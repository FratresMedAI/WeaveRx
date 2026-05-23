"""Tests for triage orchestrator."""

from weaverx.triage import TriageOptions, TriageOrchestrator


def test_mock_triage_single_issue() -> None:
    orchestrator = TriageOrchestrator(github_token=None, mock=True)
    options = TriageOptions(
        repo="Project-MONAI/MONAI",
        issue_number=42,
        mock=True,
        dry_run=True,
        privacy_insight=True,
    )
    result = orchestrator.triage_one(options)
    assert result.issue.number == 42
    assert result.analysis.category
    assert result.draft_response
    payload = result.to_dict()
    assert payload["repo"] == "Project-MONAI/MONAI"
    assert payload["status"] == "ready_for_review"
    assert "analysis" in payload
    assert payload["sources"]
    assert payload["llm"]["provider"] == "mock"
    assert payload["safeguard"] is not None
    assert "score" in payload["safeguard"]
    assert "status" in payload["safeguard"]
    assert "triggered" in payload["safeguard"]


def test_mock_triage_recent_batch() -> None:
    orchestrator = TriageOrchestrator(github_token=None, mock=True)
    options = TriageOptions(
        repo="MIC-DKFZ/nnUNet",
        recent=2,
        mock=True,
        dry_run=True,
    )
    results = orchestrator.triage_recent(options)
    assert len(results) == 2
    assert all(r.analysis.draft_response for r in results)
