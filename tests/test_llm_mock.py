"""Tests for mock LLM provider."""

from weaverx.github import mock_issue
from weaverx.llm import MockLLMProvider, TriageAnalysis, scan_privacy_keywords


def test_mock_llm_returns_valid_analysis() -> None:
    issue = mock_issue(42)
    provider = MockLLMProvider()
    analysis = provider.analyze(
        issue,
        duplicate_candidates=[],
        heuristic_duplicate_score=0.0,
        privacy_insight=True,
    )
    assert isinstance(analysis, TriageAnalysis)
    assert analysis.category == "reproducibility-environment"
    assert analysis.priority in {"low", "medium", "high", "critical"}
    assert 0.0 <= analysis.duplicate_likelihood <= 1.0
    assert analysis.draft_response
    assert analysis.sources
    assert analysis.sources[0].type in {"issue_title", "issue_body"}


def test_privacy_keyword_scan() -> None:
    flags = scan_privacy_keywords("Patient MRN and DICOM headers with PHI")
    assert any("dicom" in f or "phi" in f or "mrn" in f for f in flags)


def test_triage_analysis_validates_category() -> None:
    analysis = TriageAnalysis(
        category="not-a-real-slug",
        priority="medium",
        impact_summary="test",
        duplicate_likelihood=0.5,
        suggested_labels=["bug"],
        draft_response="Thanks!",
        reasoning="test",
    )
    assert analysis.category == "bug"
