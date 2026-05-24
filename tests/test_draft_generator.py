"""Tests for draft refinement."""

from __future__ import annotations

from weaverx.draft_generator import refine_draft
from weaverx.github import GitHubIssue
from weaverx.llm import DuplicateMatch, TriageAnalysis


def _issue(**kwargs: object) -> GitHubIssue:
    defaults = {
        "number": 1,
        "title": "Test issue",
        "body": "Body",
        "state": "open",
        "html_url": "https://example.com/1",
        "labels": (),
        "user": "researcher",
    }
    defaults.update(kwargs)
    return GitHubIssue(**defaults)  # type: ignore[arg-type]


def _analysis(**kwargs: object) -> TriageAnalysis:
    defaults = {
        "category": "documentation",
        "priority": "low",
        "impact_summary": "Needs clearer docs.",
        "duplicate_likelihood": 0.0,
        "suggested_labels": ["documentation"],
        "draft_response": "Short.",
        "privacy_flags": [],
        "reasoning": "test",
        "sources": [],
    }
    defaults.update(kwargs)
    return TriageAnalysis(**defaults)  # type: ignore[arg-type]


def test_refine_adds_repro_checklist() -> None:
    draft = refine_draft(
        _issue(),
        _analysis(category="reproducibility-environment", draft_response="Thanks for reporting."),
    )
    assert "Repro checklist" in draft
    assert draft.startswith("Hi @")


def test_refine_adds_privacy_note_for_flags() -> None:
    draft = refine_draft(
        _issue(body="DICOM headers"),
        _analysis(
            category="privacy-compliance-dicom",
            draft_response="Thanks for flagging this.",
            privacy_flags=["possible_phi"],
        ),
    )
    assert "Privacy note" in draft
    assert "PHI" in draft


def test_refine_adds_duplicate_crosslink() -> None:
    matches = [
        DuplicateMatch(
            issue_number=38,
            title="Similar dataset issue",
            score=0.62,
            url="https://github.com/x/y/issues/38",
        )
    ]
    draft = refine_draft(
        _issue(),
        _analysis(
            category="dataset-access-licensing",
            duplicate_likelihood=0.5,
            draft_response="Thanks — we'll look into dataset access.",
        ),
        duplicate_matches=matches,
    )
    assert "#38" in draft
    assert "Access checklist" in draft
