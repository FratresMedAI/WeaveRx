"""Integration tests for GitHub client and end-to-end flows."""

from __future__ import annotations

import json
import re

import pytest
from typer.testing import CliRunner

from weaverx.cli import app
from weaverx.github import GitHubClient, GitHubIssue
from weaverx.llm import GrokLLMProvider, MockLLMProvider
from weaverx.triage import TriageOptions, TriageOrchestrator

runner = CliRunner()

ISSUES_LIST_RE = re.compile(r".*/repos/[^/]+/[^/]+/issues(\?.*)?$")

SAMPLE_ISSUE = {
    "number": 99,
    "title": "Cannot download BraTS dataset - license form unclear",
    "body": "The dataset access page returns 403 after submitting the license form.",
    "state": "open",
    "html_url": "https://github.com/example/repo/issues/99",
    "labels": [{"name": "dataset"}],
    "user": {"login": "researcher"},
}

SAMPLE_LIST = [
    SAMPLE_ISSUE,
    {
        "number": 98,
        "title": "Older dataset question",
        "body": "Similar download issue",
        "state": "open",
        "html_url": "https://github.com/example/repo/issues/98",
        "labels": [],
        "user": {"login": "other"},
    },
]

GROK_RESPONSE = {
    "choices": [
        {
            "message": {
                "content": json.dumps(
                    {
                        "category": "dataset-access-licensing",
                        "priority": "medium",
                        "impact_summary": "Dataset access blocked.",
                        "duplicate_likelihood": 0.2,
                        "suggested_labels": ["dataset"],
                        "draft_response": "Hi @researcher - thanks for reporting this.",
                        "privacy_flags": [],
                        "reasoning": "Dataset licensing issue.",
                    }
                )
            }
        }
    ]
}


@pytest.mark.httpx_mock(can_send_already_matched_responses=True)
def test_github_fetch_issue(httpx_mock: pytest.HttpXMock) -> None:
    httpx_mock.add_response(
        url="https://api.github.com/repos/org/repo/issues/99",
        json=SAMPLE_ISSUE,
    )
    with GitHubClient(None) as client:
        issue = client.fetch_issue("org/repo", 99)
    assert issue.number == 99
    assert issue.title.startswith("Cannot download")


@pytest.mark.httpx_mock(can_send_already_matched_responses=True)
def test_github_fetch_recent_skips_prs(httpx_mock: pytest.HttpXMock) -> None:
    httpx_mock.add_response(
        url=ISSUES_LIST_RE,
        json=[
            *SAMPLE_LIST,
            {"number": 97, "title": "PR item", "pull_request": {}, "labels": [], "user": {}},
        ],
    )
    with GitHubClient(None) as client:
        issues = client.fetch_recent_issues("org/repo", limit=5)
    assert len(issues) == 2
    assert all(isinstance(i, GitHubIssue) for i in issues)


@pytest.mark.httpx_mock(can_send_already_matched_responses=True)
def test_grok_provider_parses_json(httpx_mock: pytest.HttpXMock) -> None:
    httpx_mock.add_response(
        url="https://api.x.ai/v1/chat/completions",
        json=GROK_RESPONSE,
    )
    issue = GitHubIssue(
        number=1,
        title="Dataset issue",
        body="Need access",
        state="open",
        html_url="https://example.com/1",
        labels=(),
        user="u",
    )
    provider = GrokLLMProvider("test-key")
    analysis = provider.analyze(issue, duplicate_candidates=[], heuristic_duplicate_score=0.0)
    assert analysis.category == "dataset-access-licensing"
    assert analysis.draft_response.startswith("Hi @researcher")


def test_mock_llm_categorizes_by_content() -> None:
    provider = MockLLMProvider()
    dataset_issue = GitHubIssue(
        number=1,
        title="CheXpert download returns 403",
        body="Need license clarification for dataset access.",
        state="open",
        html_url="https://example.com/1",
        labels=(),
        user="doc",
    )
    analysis = provider.analyze(
        dataset_issue,
        duplicate_candidates=[],
        heuristic_duplicate_score=0.0,
    )
    assert analysis.category == "dataset-access-licensing"

    privacy_issue = GitHubIssue(
        number=2,
        title="DICOM series upload",
        body="Patient MRN accidentally included in sample DICOM headers.",
        state="open",
        html_url="https://example.com/2",
        labels=(),
        user="rad",
    )
    privacy = provider.analyze(
        privacy_issue,
        duplicate_candidates=[],
        heuristic_duplicate_score=0.0,
    )
    assert privacy.category == "privacy-compliance-dicom"
    assert privacy.privacy_flags


@pytest.mark.httpx_mock(can_send_already_matched_responses=True)
def test_triage_with_mock_llm_and_mocked_github(httpx_mock: pytest.HttpXMock) -> None:
    httpx_mock.add_response(
        url="https://api.github.com/repos/Project-MONAI/MONAI/issues/99",
        json=SAMPLE_ISSUE,
    )
    httpx_mock.add_response(
        url=ISSUES_LIST_RE,
        json=SAMPLE_LIST,
        is_reusable=True,
    )
    orchestrator = TriageOrchestrator(github_token=None, mock=False, mock_llm=True)
    result = orchestrator.triage_one(
        TriageOptions(
            repo="Project-MONAI/MONAI",
            issue_number=99,
            mock_llm=True,
            dry_run=True,
        )
    )
    assert result.analysis.category == "dataset-access-licensing"
    assert result.draft_response
    assert result.dry_run is True


def test_post_comment_without_confirm_does_not_post() -> None:
    orchestrator = TriageOrchestrator(github_token="fake-token", mock=True)
    result = orchestrator.triage_one(
        TriageOptions(
            repo="org/repo",
            issue_number=42,
            mock=True,
            dry_run=False,
            post_comment=True,
            confirm=False,
        )
    )
    assert result.posted_comment is False


def test_cli_mock_and_mock_llm_mutually_exclusive() -> None:
    result = runner.invoke(
        app,
        [
            "triage",
            "--repo",
            "Project-MONAI/MONAI",
            "--issue",
            "1",
            "--mock",
            "--mock-llm",
        ],
    )
    assert result.exit_code == 1


@pytest.mark.network
def test_live_public_github_fetch() -> None:
    """Optional live test against public GitHub API (no token)."""
    with GitHubClient(None) as client:
        issue = client.fetch_issue("Project-MONAI/MONAI", 1)
    assert issue.number == 1
    assert issue.title
