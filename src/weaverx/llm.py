"""LLM providers for medical AI issue triage (Grok-first)."""

from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from typing import Any, Literal

import httpx
from pydantic import BaseModel, Field, field_validator

from weaverx.categories import (
    CATEGORY_BY_SLUG,
    MED_AI_CATEGORIES,
    PRIVACY_KEYWORDS,
    Priority,
    category_prompt_block,
    validate_category_slug,
)
from weaverx.github import GitHubIssue

PriorityLevel = Literal["low", "medium", "high", "critical"]


class TriageAnalysis(BaseModel):
    category: str
    priority: PriorityLevel
    impact_summary: str
    duplicate_likelihood: float = Field(ge=0.0, le=1.0)
    suggested_labels: list[str]
    draft_response: str
    privacy_flags: list[str] = Field(default_factory=list)
    reasoning: str

    @field_validator("category")
    @classmethod
    def normalize_category(cls, value: str) -> str:
        return validate_category_slug(value)

    @field_validator("priority", mode="before")
    @classmethod
    def normalize_priority(cls, value: str) -> str:
        normalized = str(value).lower().strip()
        if normalized in {p.value for p in Priority}:
            return normalized
        return Priority.MEDIUM.value

    @field_validator("duplicate_likelihood", mode="before")
    @classmethod
    def clamp_duplicate(cls, value: float | int | str) -> float:
        try:
            score = float(value)
        except (TypeError, ValueError):
            return 0.0
        return max(0.0, min(1.0, score))


class DuplicateMatch(BaseModel):
    issue_number: int
    title: str
    score: float
    url: str


def _build_system_prompt(*, privacy_insight: bool) -> str:
    privacy_note = (
        "\n\nAlso flag privacy/containment concerns in `privacy_flags` "
        "(e.g. possible_phi, dicom_handling, credential_exposure) when the issue "
        "may involve sensitive clinical data. Never encourage sharing identifiers."
        if privacy_insight
        else ""
    )
    return f"""You are WeaveRx, a supportive triage assistant for open-source medical AI projects.

Your tone is warm, practical, and community-oriented—never stern or dismissive.
Researchers and clinicians often juggle IRB constraints, dataset licenses, and reproducibility
challenges. Illuminate the issue clearly and offer restorative guidance.

Classify issues into exactly ONE of these medical AI categories:
{category_prompt_block()}

Priority guidance for medical AI:
- critical: data safety/PHI exposure, blocking clinical deployment, widespread breakage
- high: reproducibility blockers, benchmark integrity, major clinical validation gaps
- medium: subgroup performance concerns, integration friction, unclear docs
- low: minor docs typos, nice-to-have features, general questions

Respond with ONLY valid JSON matching this schema:
{{
  "category": "<category-slug>",
  "priority": "low|medium|high|critical",
  "impact_summary": "<1-2 sentences>",
  "duplicate_likelihood": <0.0-1.0>,
  "suggested_labels": ["label1", "label2"],
  "draft_response": "<supportive GitHub comment, markdown ok>",
  "privacy_flags": ["flag1"],
  "reasoning": "<brief maintainer note>"
}}

Few-shot tone examples:
- Reproducibility: "Thanks for documenting your setup so carefully—reproducibility is everything
  in medical AI. Could you share your nnU-Net plans identifier and preprocessing JSON?"
- Dataset access: "Dataset access friction is something many of us hit. The current process is
  documented in …; if you're blocked on licensing, we're happy to clarify what's needed."
- Privacy: "We appreciate you raising this. Please avoid posting patient identifiers in issues;
  de-identified screenshots or synthetic examples help us help you safely."
{privacy_note}
"""


def _build_user_prompt(
    issue: GitHubIssue,
    *,
    duplicate_candidates: list[DuplicateMatch],
    heuristic_duplicate_score: float,
) -> str:
    dupes_text = "None found."
    if duplicate_candidates:
        lines = [
            f"- #{d.issue_number} (score {d.score:.2f}): {d.title} ({d.url})"
            for d in duplicate_candidates
        ]
        dupes_text = "\n".join(lines)

    return f"""Triage this GitHub issue:

**Repository issue:** #{issue.number}
**Title:** {issue.title}
**Author:** {issue.user or "unknown"}
**Labels:** {", ".join(issue.labels) or "none"}
**Body:**
{issue.body or "(empty)"}

Heuristic duplicate score from recent issues: {heuristic_duplicate_score:.2f}
Candidate duplicates:
{dupes_text}

Produce JSON triage analysis with a helpful draft_response ready to post.
"""


def scan_privacy_keywords(text: str) -> list[str]:
    lowered = text.lower()
    flags: list[str] = []
    for keyword in PRIVACY_KEYWORDS:
        if keyword in lowered:
            flags.append(f"keyword:{keyword.replace(' ', '_')}")
    if "dicom" in lowered:
        flags.append("dicom_handling")
    if any(k in lowered for k in ("patient", "phi", "hipaa", "gdpr")):
        flags.append("possible_phi")
    return sorted(set(flags))


def _extract_json(content: str) -> dict[str, Any]:
    content = content.strip()
    try:
        parsed = json.loads(content)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{.*\}", content, re.DOTALL)
    if match:
        parsed = json.loads(match.group())
        if isinstance(parsed, dict):
            return parsed
    raise ValueError(f"LLM response did not contain valid JSON: {content[:200]}...")


class LLMProvider(ABC):
    @abstractmethod
    def analyze(
        self,
        issue: GitHubIssue,
        *,
        duplicate_candidates: list[DuplicateMatch],
        heuristic_duplicate_score: float,
        privacy_insight: bool = True,
    ) -> TriageAnalysis:
        raise NotImplementedError


class MockLLMProvider(LLMProvider):
    """Deterministic offline provider for tests and demos."""

    def analyze(
        self,
        issue: GitHubIssue,
        *,
        duplicate_candidates: list[DuplicateMatch],
        heuristic_duplicate_score: float,
        privacy_insight: bool = True,
    ) -> TriageAnalysis:
        text = f"{issue.title}\n{issue.body}"
        lowered = text.lower()
        privacy_flags = scan_privacy_keywords(text) if privacy_insight else []
        dup_score = max(heuristic_duplicate_score, 0.15 if duplicate_candidates else 0.05)

        category, priority, labels, impact = _infer_mock_analysis(lowered, privacy_flags)
        cat = CATEGORY_BY_SLUG[category]
        draft = _build_mock_draft(issue, category, cat.healer_framing, impact)

        return TriageAnalysis(
            category=category,
            priority=priority,
            impact_summary=impact,
            duplicate_likelihood=dup_score,
            suggested_labels=labels,
            draft_response=draft,
            privacy_flags=privacy_flags,
            reasoning=(
                f"Heuristic mock triage classified as {cat.display_name}. "
                f"Use XAI_API_KEY for full Grok analysis."
            ),
        )


def _infer_mock_analysis(
    lowered: str,
    privacy_flags: list[str],
) -> tuple[str, PriorityLevel, list[str], str]:
    if privacy_flags or any(
        k in lowered for k in ("hipaa", "gdpr", "phi", "patient id", "mrn", "identifiable")
    ):
        return (
            "privacy-compliance-dicom",
            "critical",
            ["privacy", "compliance", "dicom"],
            "Issue may involve sensitive clinical data handling that needs careful containment.",
        )
    if any(
        k in lowered
        for k in ("dataset", "download", "licens", "chexpert", "403", "data access")
    ):
        return (
            "dataset-access-licensing",
            "medium",
            ["dataset", "data-access"],
            "Dataset access or licensing appears to be the main blocker for this contributor.",
        )
    if any(
        k in lowered
        for k in ("clinical validation", "reader study", "prospective", "fda", "clinical trial")
    ):
        return (
            "clinical-validation",
            "high",
            ["clinical-validation", "evaluation"],
            "Contributor is seeking guidance on clinical or external validation pathways.",
        )
    if "[bug]" in lowered or any(
        k in lowered for k in ("crash", "error", "exception", "fail", " broken", "bug:")
    ):
        return (
            "bug",
            "medium",
            ["bug"],
            "Unexpected behavior or failure reported that may affect users.",
        )
    if any(k in lowered for k in ("documentation", "docs", "tutorial", "readme", "example")):
        return (
            "documentation",
            "low",
            ["documentation"],
            "Documentation clarity would help the next researcher move faster.",
        )
    if any(k in lowered for k in ("feature", "integration", "enhancement", "support for")):
        return (
            "feature-integration",
            "medium",
            ["enhancement", "integration"],
            "Contributor is proposing a new capability or integration point.",
        )
    if any(
        k in lowered
        for k in (
            "reproduc",
            "cuda",
            "pytorch",
            "environment",
            "nnunet",
            "nn u-net",
            "cannot reproduce",
        )
    ):
        return (
            "reproducibility-environment",
            "high",
            ["reproducibility", "environment"],
            "Environment or reproduction mismatch may be blocking benchmark trust.",
        )
    if any(
        k in lowered
        for k in ("accuracy", "dice", "auc", "sensitivity", "pathology", "subgroup")
    ):
        return (
            "model-performance-pathology",
            "high",
            ["performance", "pathology"],
            "Model performance on a specific pathology or subgroup needs investigation.",
        )
    return (
        "documentation",
        "low",
        ["question"],
        "General question that may benefit from clearer docs or a pointer to examples.",
    )


def _build_mock_draft(
    issue: GitHubIssue,
    category: str,
    healer_framing: str,
    impact: str,
) -> str:
    author = issue.user or "there"
    lines = [
        f"Hi @{author} - thank you for taking the time to write this up.",
        "",
        impact,
        "",
        healer_framing,
    ]
    if category == "reproducibility-environment":
        lines.extend(
            [
                "",
                "A few things that often help us untangle medical AI reproduction issues:",
                "",
                "1. **Environment snapshot** - PyTorch, CUDA, MONAI/nnU-Net versions",
                "2. **Preprocessing** - config files or exported dataset plans",
                "3. **Seed & fold** - confirm split and random seed",
            ]
        )
    if category == "dataset-access-licensing":
        lines.extend(
            [
                "",
                "If you're blocked on access, sharing which step failed (form, mirror, "
                "credentials) helps us improve the path for the next researcher.",
            ]
        )
    lines.append("")
    lines.append("Happy to dig in once you share a bit more detail (no patient data, please!).")
    return "\n".join(lines)


class GrokLLMProvider(LLMProvider):
    API_URL = "https://api.x.ai/v1/chat/completions"
    DEFAULT_MODEL = "grok-2-latest"

    def __init__(
        self,
        api_key: str,
        *,
        model: str | None = None,
        timeout: float = 60.0,
    ) -> None:
        self._api_key = api_key
        self._model = model or self.DEFAULT_MODEL
        self._client = httpx.Client(timeout=timeout)

    def close(self) -> None:
        self._client.close()

    def analyze(
        self,
        issue: GitHubIssue,
        *,
        duplicate_candidates: list[DuplicateMatch],
        heuristic_duplicate_score: float,
        privacy_insight: bool = True,
    ) -> TriageAnalysis:
        messages = [
            {"role": "system", "content": _build_system_prompt(privacy_insight=privacy_insight)},
            {
                "role": "user",
                "content": _build_user_prompt(
                    issue,
                    duplicate_candidates=duplicate_candidates,
                    heuristic_duplicate_score=heuristic_duplicate_score,
                ),
            },
        ]
        response = self._client.post(
            self.API_URL,
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self._model,
                "messages": messages,
                "temperature": 0.2,
                "response_format": {"type": "json_object"},
            },
        )
        response.raise_for_status()
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        parsed = _extract_json(content)
        analysis = TriageAnalysis.model_validate(parsed)

        if privacy_insight:
            keyword_flags = scan_privacy_keywords(f"{issue.title}\n{issue.body}")
            merged = sorted(set(analysis.privacy_flags) | set(keyword_flags))
            analysis = analysis.model_copy(update={"privacy_flags": merged})

        return analysis


def create_llm_provider(*, mock: bool, api_key: str | None) -> LLMProvider:
    if mock:
        return MockLLMProvider()
    if not api_key:
        raise ValueError(
            "XAI_API_KEY is required for LLM analysis. Set the env var or pass --mock."
        )
    return GrokLLMProvider(api_key)


def default_labels_for_category(slug: str) -> list[str]:
    for cat in MED_AI_CATEGORIES:
        if cat.slug == slug:
            return list(cat.suggested_labels)
    return ["bug"]
