"""Lightweight local safeguard checks for generated draft responses."""

from __future__ import annotations

import math
import os
import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Literal

from weaverx.categories import MED_AI_KEYWORDS
from weaverx.duplicate_detector import normalize_text

SafeguardStatus = Literal["clean", "review_recommended", "high_risk"]

FINDING_WEIGHTS: dict[str, float] = {
    "high_entropy": 2.5,
    "excessive_length": 1.5,
    "heavy_repetition": 2.0,
    "credential_like_pattern": 4.0,
    "excessive_markdown_links": 1.5,
    "base64_like_blob": 3.0,
    "private_key_pattern": 4.0,
    "low_relevance": 2.0,
}

_CREDENTIAL_PATTERN = re.compile(
    r"(?i)(api[_-]?key|secret|password|token)\s*[:=]\s*\S{8,}",
)
_AWS_KEY_PATTERN = re.compile(r"AKIA[0-9A-Z]{16}")
_BASE64_BLOB_PATTERN = re.compile(r"[A-Za-z0-9+/]{80,}={0,2}")
_MARKDOWN_LINK_PATTERN = re.compile(r"\[[^\]]*\]\([^)]+\)")
_PRIVATE_KEY_MARKERS = ("BEGIN PRIVATE KEY", "ssh-rsa")


@dataclass(frozen=True, slots=True)
class SafeguardConfig:
    enabled: bool = True
    entropy_max: float = 5.5
    min_entropy_chars: int = 80
    max_chars: int = 6000
    repetition_ratio_max: float = 0.35
    ngram_repeat_min: int = 5
    relevance_ratio_min: float = 0.08
    min_issue_keywords: int = 3
    max_markdown_links: int = 15
    check_entropy: bool = True
    check_length_repetition: bool = True
    check_patterns: bool = True
    check_relevance: bool = True


@dataclass(slots=True)
class SafeguardFinding:
    id: str
    severity: str
    message: str
    metric: float | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "id": self.id,
            "severity": self.severity,
            "message": self.message,
        }
        if self.metric is not None:
            payload["metric"] = self.metric
        return payload


@dataclass(slots=True)
class SafeguardMetrics:
    entropy: float = 0.0
    char_count: int = 0
    word_count: int = 0
    repetition_ratio: float = 0.0
    relevance_ratio: float | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "entropy": round(self.entropy, 2),
            "char_count": self.char_count,
            "word_count": self.word_count,
            "repetition_ratio": round(self.repetition_ratio, 2),
        }
        if self.relevance_ratio is not None:
            payload["relevance_ratio"] = round(self.relevance_ratio, 2)
        return payload


@dataclass(slots=True)
class SafeguardReport:
    score: float
    status: SafeguardStatus
    triggered: list[SafeguardFinding] = field(default_factory=list)
    metrics: SafeguardMetrics = field(default_factory=SafeguardMetrics)
    checks_run: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "score": round(self.score, 1),
            "status": self.status,
            "triggered": [finding.to_dict() for finding in self.triggered],
            "metrics": self.metrics.to_dict(),
            "checks_run": self.checks_run,
        }


def load_safeguard_config_from_env() -> SafeguardConfig:
    """Build safeguard config from optional environment overrides."""
    enabled = os.environ.get("WEAVERX_SAFEGUARDS", "1").lower() not in {"0", "false", "no"}

    def _float(name: str, default: float) -> float:
        raw = os.environ.get(name)
        return float(raw) if raw else default

    def _int(name: str, default: int) -> int:
        raw = os.environ.get(name)
        return int(raw) if raw else default

    return SafeguardConfig(
        enabled=enabled,
        entropy_max=_float("WEAVERX_SAFEGUARD_ENTROPY_MAX", 5.5),
        max_chars=_int("WEAVERX_SAFEGUARD_MAX_CHARS", 6000),
    )


def shannon_entropy(text: str) -> float:
    if not text:
        return 0.0
    counts = Counter(text)
    length = len(text)
    entropy = 0.0
    for count in counts.values():
        probability = count / length
        entropy -= probability * math.log2(probability)
    return entropy


def repetition_ratio(text: str) -> float:
    words = normalize_text(text).split()
    if len(words) < 2:
        return 0.0
    unique = len(set(words))
    return 1.0 - (unique / len(words))


def _has_repeated_ngram(text: str, *, n: int = 4, min_count: int = 5) -> bool:
    words = normalize_text(text).split()
    if len(words) < n:
        return False
    ngrams = [" ".join(words[i : i + n]) for i in range(len(words) - n + 1)]
    counts = Counter(ngrams)
    return any(count >= min_count for count in counts.values())


def _content_keywords(text: str) -> set[str]:
    normalized = normalize_text(text)
    words = {word for word in normalized.split() if len(word) > 4}
    med_words = {word for word in normalized.split() if word in MED_AI_KEYWORDS}
    return words | med_words


def check_entropy(text: str, config: SafeguardConfig) -> SafeguardFinding | None:
    if len(text) < config.min_entropy_chars:
        return None
    entropy = shannon_entropy(text)
    if entropy > config.entropy_max:
        return SafeguardFinding(
            id="high_entropy",
            severity="medium",
            message=(
                f"Shannon entropy {entropy:.2f} exceeds threshold {config.entropy_max:.1f} "
                "(possible encoded/obfuscated content)."
            ),
            metric=round(entropy, 2),
        )
    return None


def check_length_repetition(text: str, config: SafeguardConfig) -> list[SafeguardFinding]:
    findings: list[SafeguardFinding] = []

    if len(text) > config.max_chars:
        findings.append(
            SafeguardFinding(
                id="excessive_length",
                severity="medium",
                message=(
                    f"Draft length {len(text)} exceeds threshold {config.max_chars} characters."
                ),
                metric=float(len(text)),
            )
        )

    ratio = repetition_ratio(text)
    if ratio > config.repetition_ratio_max or _has_repeated_ngram(
        text,
        min_count=config.ngram_repeat_min,
    ):
        findings.append(
            SafeguardFinding(
                id="heavy_repetition",
                severity="medium",
                message=(
                    f"Draft shows heavy repetition (ratio {ratio:.2f}, "
                    f"threshold {config.repetition_ratio_max:.2f})."
                ),
                metric=round(ratio, 2),
            )
        )

    return findings


def check_patterns(text: str, config: SafeguardConfig) -> list[SafeguardFinding]:
    findings: list[SafeguardFinding] = []
    seen: set[str] = set()

    def _add(finding: SafeguardFinding) -> None:
        if finding.id not in seen:
            seen.add(finding.id)
            findings.append(finding)

    if _CREDENTIAL_PATTERN.search(text):
        _add(
            SafeguardFinding(
                id="credential_like_pattern",
                severity="high",
                message="Draft contains a credential-like token pattern (e.g. API key shape).",
            )
        )

    if _AWS_KEY_PATTERN.search(text):
        _add(
            SafeguardFinding(
                id="credential_like_pattern",
                severity="high",
                message="Draft contains a credential-like token pattern (e.g. API key shape).",
            )
        )

    if _BASE64_BLOB_PATTERN.search(text):
        _add(
            SafeguardFinding(
                id="base64_like_blob",
                severity="medium",
                message="Draft contains a long base64-like encoded blob.",
            )
        )

    link_count = len(_MARKDOWN_LINK_PATTERN.findall(text))
    if link_count > config.max_markdown_links:
        _add(
            SafeguardFinding(
                id="excessive_markdown_links",
                severity="low",
                message=(
                    f"Draft contains {link_count} markdown links "
                    f"(threshold {config.max_markdown_links})."
                ),
                metric=float(link_count),
            )
        )

    text_lower = text.lower()
    for marker in _PRIVATE_KEY_MARKERS:
        if marker.lower() in text_lower:
            _add(
                SafeguardFinding(
                    id="private_key_pattern",
                    severity="high",
                    message=f"Draft contains a private key marker ({marker!r}).",
                )
            )
            break

    return findings


def check_relevance(
    draft: str,
    *,
    issue_title: str,
    issue_body: str,
    config: SafeguardConfig,
) -> tuple[SafeguardFinding | None, float | None]:
    issue_text = f"{issue_title} {issue_body}"
    issue_keywords = _content_keywords(issue_text)
    draft_keywords = _content_keywords(draft)

    if len(issue_keywords) < config.min_issue_keywords:
        return None, None

    overlap = issue_keywords & draft_keywords
    ratio = len(overlap) / max(len(issue_keywords), 1)

    if ratio < config.relevance_ratio_min:
        return (
            SafeguardFinding(
                id="low_relevance",
                severity="medium",
                message=(
                    f"Draft keyword overlap with issue is low ({ratio:.2f}, "
                    f"threshold {config.relevance_ratio_min:.2f})."
                ),
                metric=round(ratio, 2),
            ),
            ratio,
        )

    return None, ratio


def aggregate_score(findings: list[SafeguardFinding]) -> float:
    total = sum(FINDING_WEIGHTS.get(finding.id, 1.0) for finding in findings)
    return min(10.0, total)


def status_from_score(score: float) -> SafeguardStatus:
    if score >= 7.0:
        return "high_risk"
    if score >= 3.0:
        return "review_recommended"
    return "clean"


def run_safeguards(
    draft: str,
    *,
    issue_title: str = "",
    issue_body: str = "",
    config: SafeguardConfig | None = None,
) -> SafeguardReport:
    cfg = config or load_safeguard_config_from_env()
    findings: list[SafeguardFinding] = []
    checks_run: list[str] = []

    metrics = SafeguardMetrics(
        entropy=shannon_entropy(draft),
        char_count=len(draft),
        word_count=len(normalize_text(draft).split()),
        repetition_ratio=repetition_ratio(draft),
    )

    if cfg.check_entropy:
        checks_run.append("entropy")
        if finding := check_entropy(draft, cfg):
            findings.append(finding)

    if cfg.check_length_repetition:
        checks_run.append("length_repetition")
        findings.extend(check_length_repetition(draft, cfg))

    if cfg.check_patterns:
        checks_run.append("patterns")
        findings.extend(check_patterns(draft, cfg))

    if cfg.check_relevance:
        checks_run.append("relevance")
        relevance_finding, relevance_ratio = check_relevance(
            draft,
            issue_title=issue_title,
            issue_body=issue_body,
            config=cfg,
        )
        metrics.relevance_ratio = relevance_ratio
        if relevance_finding is not None:
            findings.append(relevance_finding)

    score = aggregate_score(findings)
    status = status_from_score(score)

    return SafeguardReport(
        score=score,
        status=status,
        triggered=findings,
        metrics=metrics,
        checks_run=checks_run,
    )
