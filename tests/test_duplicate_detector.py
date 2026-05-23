"""Tests for duplicate detection."""

from weaverx.duplicate_detector import find_duplicates, normalize_text, similarity_score
from weaverx.github import GitHubIssue, mock_issue, mock_recent_issues


def test_normalize_text_strips_markdown() -> None:
    text = "Hello **world** `code` [link](http://x.com)"
    normalized = normalize_text(text)
    assert "**" not in normalized
    assert "link" in normalized


def test_similarity_same_issue_is_zero() -> None:
    issue = mock_issue(1)
    assert similarity_score(issue, issue) == 0.0


def test_find_duplicates_returns_scored_matches() -> None:
    source = mock_issue(42)
    candidates = mock_recent_issues()
    matches = find_duplicates(source, candidates, min_score=0.1)
    assert isinstance(matches, list)
    for match in matches:
        assert 0.0 <= match.score <= 1.0
        assert match.issue_number != source.number


def test_similarity_boosts_shared_keywords() -> None:
    a = GitHubIssue(
        number=1,
        title="MONAI nnU-Net BraTS reproduction issue",
        body="CUDA pytorch reproducibility",
        state="open",
        html_url="https://example.com/1",
        labels=(),
        user="a",
    )
    b = GitHubIssue(
        number=2,
        title="nnU-Net MONAI BraTS training variance",
        body="pytorch cuda reproducibility environment",
        state="open",
        html_url="https://example.com/2",
        labels=(),
        user="b",
    )
    score = similarity_score(a, b)
    assert score > 0.3
