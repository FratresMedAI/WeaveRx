"""Tests for GitHub client error handling and resilience."""

from __future__ import annotations

import pytest

from weaverx.github import (
    GitHubClient,
    GitHubNotFoundError,
    GitHubPermissionError,
    validate_github_token,
)


def test_validate_github_token_accepts_none() -> None:
    assert validate_github_token(None) is None
    assert validate_github_token("   ") is None


def test_validate_github_token_rejects_short_values() -> None:
    with pytest.raises(ValueError, match="too short"):
        validate_github_token("ghp_short")


def test_validate_github_token_normalizes() -> None:
    token = "ghp_" + "a" * 36
    assert validate_github_token(f"  {token}  ") == token


@pytest.mark.httpx_mock(can_send_already_matched_responses=True)
def test_github_retries_after_rate_limit(httpx_mock: pytest.HttpXMock) -> None:
    httpx_mock.add_response(
        url="https://api.github.com/repos/org/repo/issues/1",
        status_code=429,
        headers={"Retry-After": "0"},
    )
    httpx_mock.add_response(
        url="https://api.github.com/repos/org/repo/issues/1",
        json={
            "number": 1,
            "title": "Test",
            "body": "Body",
            "state": "open",
            "html_url": "https://github.com/org/repo/issues/1",
            "labels": [],
            "user": {"login": "dev"},
        },
    )
    with GitHubClient(None) as client:
        issue = client.fetch_issue("org/repo", 1)
    assert issue.number == 1


@pytest.mark.httpx_mock(can_send_already_matched_responses=True)
def test_github_403_raises_permission_error(httpx_mock: pytest.HttpXMock) -> None:
    httpx_mock.add_response(
        url="https://api.github.com/repos/private/repo/issues/1",
        status_code=403,
        json={"message": "Resource not accessible by integration"},
    )
    with (
        GitHubClient("ghp_" + "x" * 36) as client,
        pytest.raises(GitHubPermissionError, match="permission denied"),
    ):
        client.fetch_issue("private/repo", 1)


@pytest.mark.httpx_mock(can_send_already_matched_responses=True)
def test_github_404_raises_not_found(httpx_mock: pytest.HttpXMock) -> None:
    httpx_mock.add_response(
        url="https://api.github.com/repos/org/repo/issues/99999",
        status_code=404,
        json={"message": "Not Found"},
    )
    with GitHubClient(None) as client, pytest.raises(GitHubNotFoundError, match="not found"):
        client.fetch_issue("org/repo", 99999)


@pytest.mark.httpx_mock(can_send_already_matched_responses=True)
def test_github_paginates_comments(httpx_mock: pytest.HttpXMock) -> None:
    first_page = [
        {
            "body": f"Comment {i}",
            "user": {"login": "user"},
            "created_at": "2026-01-01T00:00:00Z",
        }
        for i in range(100)
    ]
    httpx_mock.add_response(
        url="https://api.github.com/repos/org/repo/issues/5/comments?sort=created&direction=desc&per_page=100&page=1",
        json=first_page,
    )
    httpx_mock.add_response(
        url="https://api.github.com/repos/org/repo/issues/5/comments?sort=created&direction=desc&per_page=100&page=2",
        json=[
            {
                "body": "Comment overflow",
                "user": {"login": "user"},
                "created_at": "2026-01-02T00:00:00Z",
            }
        ],
    )
    with GitHubClient(None) as client:
        comments = client.fetch_issue_comments("org/repo", 5, limit=101)
    assert len(comments) == 101
    assert comments[-1].body == "Comment overflow"
