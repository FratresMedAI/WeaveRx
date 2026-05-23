"""Tests for draft safeguard heuristics."""

from __future__ import annotations

from weaverx.safeguards import (
    SafeguardConfig,
    SafeguardFinding,
    aggregate_score,
    check_entropy,
    check_length_repetition,
    check_patterns,
    check_relevance,
    run_safeguards,
    shannon_entropy,
    status_from_score,
)
from weaverx.triage import TriageOptions, TriageOrchestrator

NORMAL_DRAFT = (
    "Hi @researcher-dev — thank you for taking the time to write this up.\n\n"
    "Reproducibility questions like this are valuable for the medical AI community. "
    "Could you share your MONAI and nnU-Net versions, CUDA/PyTorch stack, and the "
    "exact BraTS preprocessing steps you used?"
)


def test_shannon_entropy_normal_prose() -> None:
    entropy = shannon_entropy(NORMAL_DRAFT)
    assert 3.5 <= entropy <= 5.5
    assert check_entropy(NORMAL_DRAFT, SafeguardConfig()) is None


def test_high_entropy_base64_blob() -> None:
    blob = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/" * 3
    config = SafeguardConfig(min_entropy_chars=10, entropy_max=5.0)
    finding = check_entropy(blob, config)
    assert finding is not None
    assert finding.id == "high_entropy"


def test_excessive_length() -> None:
    config = SafeguardConfig(max_chars=100)
    findings = check_length_repetition("x" * 150, config)
    assert any(finding.id == "excessive_length" for finding in findings)


def test_heavy_repetition() -> None:
    repeated = " ".join(["reproduce monai nnunet brats"] * 20)
    config = SafeguardConfig(repetition_ratio_max=0.2, ngram_repeat_min=3)
    findings = check_length_repetition(repeated, config)
    assert any(finding.id == "heavy_repetition" for finding in findings)


def test_credential_pattern() -> None:
    draft = "Please set api_key=abcd1234efgh5678 in your environment."
    findings = check_patterns(draft, SafeguardConfig())
    assert any(finding.id == "credential_like_pattern" for finding in findings)


def test_low_relevance() -> None:
    issue_title = "Unable to reproduce nnU-Net training results on BraTS subset"
    issue_body = "MONAI transforms and nnU-Net benchmark reproduction on BraTS dataset."
    unrelated_draft = (
        "Thanks for reporting. Here is a generic answer about documentation formatting "
        "and unrelated repository housekeeping tasks."
    )
    finding, ratio = check_relevance(
        unrelated_draft,
        issue_title=issue_title,
        issue_body=issue_body,
        config=SafeguardConfig(relevance_ratio_min=0.5),
    )
    assert finding is not None
    assert finding.id == "low_relevance"
    assert ratio is not None
    assert ratio < 0.5


def test_clean_draft_score() -> None:
    report = run_safeguards(
        NORMAL_DRAFT,
        issue_title="nnU-Net BraTS reproduction issue",
        issue_body="MONAI pipeline and nnU-Net benchmark on BraTS subset.",
    )
    assert report.status == "clean"
    assert report.score < 3.0
    assert report.triggered == []


def test_aggregate_score_caps_at_10() -> None:
    findings = [
        SafeguardFinding(id="credential_like_pattern", severity="high", message="a"),
        SafeguardFinding(id="private_key_pattern", severity="high", message="b"),
        SafeguardFinding(id="base64_like_blob", severity="medium", message="c"),
    ]
    assert aggregate_score(findings) == 10.0


def test_status_from_score_thresholds() -> None:
    assert status_from_score(0.0) == "clean"
    assert status_from_score(2.9) == "clean"
    assert status_from_score(3.0) == "review_recommended"
    assert status_from_score(6.9) == "review_recommended"
    assert status_from_score(7.0) == "high_risk"


def test_run_safeguards_includes_metrics_and_checks() -> None:
    report = run_safeguards(NORMAL_DRAFT, issue_title="BraTS", issue_body="nnU-Net MONAI")
    payload = report.to_dict()
    assert "entropy" in payload["metrics"]
    assert payload["checks_run"] == ["entropy", "length_repetition", "patterns", "relevance"]


def test_disabled_safeguards_in_orchestrator() -> None:
    orchestrator = TriageOrchestrator(github_token=None, mock=True)
    options = TriageOptions(
        repo="Project-MONAI/MONAI",
        issue_number=42,
        mock=True,
        dry_run=True,
        safeguards=False,
    )
    result = orchestrator.triage_one(options)
    assert result.safeguard is None
    assert result.to_dict()["safeguard"] is None
