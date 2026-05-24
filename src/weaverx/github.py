"""GitHub REST API client for issue triage."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

import httpx

from weaverx.utils import parse_repo

_GITHUB_TOKEN_PREFIXES = ("ghp_", "gho_", "ghu_", "ghs_", "ghr_", "github_pat_")
_RETRYABLE_STATUS = frozenset({429, 502, 503, 504})
_MAX_RETRIES = 3
_MAX_BACKOFF_SECONDS = 60.0


class GitHubAPIError(Exception):
    """Base error for GitHub API failures."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int,
        response_body: str = "",
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body


class GitHubRateLimitError(GitHubAPIError):
    """Rate limit exceeded (HTTP 429)."""


class GitHubPermissionError(GitHubAPIError):
    """Insufficient permissions or forbidden (HTTP 403)."""


class GitHubNotFoundError(GitHubAPIError):
    """Resource not found (HTTP 404)."""


def validate_github_token(token: str | None) -> str | None:
    """
    Normalize and lightly validate a GitHub token.

    Unauthenticated requests (None/empty) are allowed for public API use.
    """
    if token is None:
        return None
    normalized = token.strip()
    if not normalized:
        return None
    if len(normalized) < 20:
        raise ValueError(
            "GitHub token appears invalid (too short). "
            "Use a personal access token or fine-grained token from GitHub settings."
        )
    if not normalized.startswith(_GITHUB_TOKEN_PREFIXES):
        # Legacy tokens and some CI tokens omit known prefixes — warn via debug only.
        pass
    return normalized


def _parse_retry_after(response: httpx.Response, attempt: int) -> float:
    raw = response.headers.get("Retry-After")
    if raw:
        try:
            return min(float(raw), _MAX_BACKOFF_SECONDS)
        except ValueError:
            pass
    return min(2.0**attempt, _MAX_BACKOFF_SECONDS)


def _error_message(response: httpx.Response) -> str:
    try:
        payload = response.json()
        if isinstance(payload, dict):
            message = payload.get("message")
            if isinstance(message, str) and message.strip():
                doc_url = payload.get("documentation_url")
                if doc_url:
                    return f"{message} (see {doc_url})"
                return message
    except Exception:
        pass
    text = response.text.strip()
    if text:
        return text[:500]
    return f"GitHub API request failed with HTTP {response.status_code}"


def _raise_for_response(response: httpx.Response) -> None:
    message = _error_message(response)
    status = response.status_code
    body = response.text[:500]
    if status == 429:
        raise GitHubRateLimitError(
            f"GitHub rate limit exceeded: {message}",
            status_code=status,
            response_body=body,
        )
    if status == 403:
        raise GitHubPermissionError(
            f"GitHub permission denied: {message}",
            status_code=status,
            response_body=body,
        )
    if status == 404:
        raise GitHubNotFoundError(
            f"GitHub resource not found: {message}",
            status_code=status,
            response_body=body,
        )
    raise GitHubAPIError(
        message,
        status_code=status,
        response_body=body,
    )


@dataclass(frozen=True, slots=True)
class GitHubIssue:
    number: int
    title: str
    body: str
    state: str
    html_url: str
    labels: tuple[str, ...]
    user: str | None


@dataclass(frozen=True, slots=True)
class GitHubComment:
    user: str | None
    body: str
    created_at: str | None = None


class GitHubClient:
    API_BASE = "https://api.github.com"

    def __init__(self, token: str | None, *, timeout: float = 30.0) -> None:
        validated = validate_github_token(token)
        headers: dict[str, str] = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if validated:
            headers["Authorization"] = f"Bearer {validated}"
        self._client = httpx.Client(base_url=self.API_BASE, headers=headers, timeout=timeout)

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> GitHubClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def _request(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, str | int] | None = None,
        json: dict[str, Any] | None = None,
    ) -> httpx.Response:
        last_response: httpx.Response | None = None
        for attempt in range(_MAX_RETRIES):
            response = self._client.request(method, url, params=params, json=json)
            last_response = response
            if response.status_code < 400:
                return response
            if response.status_code in _RETRYABLE_STATUS and attempt < _MAX_RETRIES - 1:
                delay = _parse_retry_after(response, attempt)
                time.sleep(delay)
                continue
            _raise_for_response(response)
        assert last_response is not None
        _raise_for_response(last_response)
        raise GitHubAPIError("Unexpected GitHub request failure", status_code=500)

    def _get_paginated(
        self,
        url: str,
        *,
        params: dict[str, str | int],
        limit: int,
        item_filter: Any | None = None,
    ) -> list[dict[str, Any]]:
        collected: list[dict[str, Any]] = []
        page = 1
        per_page = min(max(limit, 1), 100)
        while len(collected) < limit:
            page_params = {**params, "per_page": per_page, "page": page}
            response = self._request("GET", url, params=page_params)
            batch = response.json()
            if not isinstance(batch, list) or not batch:
                break
            for item in batch:
                if not isinstance(item, dict):
                    continue
                if item_filter is not None and not item_filter(item):
                    continue
                collected.append(item)
                if len(collected) >= limit:
                    break
            if len(batch) < per_page:
                break
            page += 1
        return collected[:limit]

    def _parse_issue(self, data: dict[str, Any]) -> GitHubIssue:
        labels = tuple(label["name"] for label in data.get("labels", []) if isinstance(label, dict))
        user = None
        if isinstance(data.get("user"), dict):
            user = data["user"].get("login")
        return GitHubIssue(
            number=int(data["number"]),
            title=str(data.get("title") or ""),
            body=str(data.get("body") or ""),
            state=str(data.get("state") or "open"),
            html_url=str(data.get("html_url") or ""),
            labels=labels,
            user=user,
        )

    def fetch_issue(self, repo: str, issue_number: int) -> GitHubIssue:
        owner, name = parse_repo(repo)
        response = self._request("GET", f"/repos/{owner}/{name}/issues/{issue_number}")
        return self._parse_issue(response.json())

    def fetch_issue_comments(
        self,
        repo: str,
        issue_number: int,
        *,
        limit: int = 5,
    ) -> list[GitHubComment]:
        owner, name = parse_repo(repo)
        items = self._get_paginated(
            f"/repos/{owner}/{name}/issues/{issue_number}/comments",
            params={"sort": "created", "direction": "desc"},
            limit=max(limit, 1),
        )
        comments: list[GitHubComment] = []
        for item in items[:limit]:
            user = None
            if isinstance(item.get("user"), dict):
                user = item["user"].get("login")
            comments.append(
                GitHubComment(
                    user=user,
                    body=str(item.get("body") or ""),
                    created_at=str(item.get("created_at") or "") or None,
                )
            )
        return comments

    def fetch_recent_issues(
        self,
        repo: str,
        *,
        limit: int = 30,
        state: str = "open",
    ) -> list[GitHubIssue]:
        owner, name = parse_repo(repo)

        def _is_issue(item: dict[str, Any]) -> bool:
            return "pull_request" not in item

        # Fetch extra pages when many items are pull requests.
        fetch_limit = min(max(limit * 2, limit), 100)
        items = self._get_paginated(
            f"/repos/{owner}/{name}/issues",
            params={"state": state, "sort": "created", "direction": "desc"},
            limit=fetch_limit,
            item_filter=_is_issue,
        )
        return [self._parse_issue(item) for item in items[:limit]]

    def post_comment(self, repo: str, issue_number: int, body: str) -> None:
        owner, name = parse_repo(repo)
        self._request(
            "POST",
            f"/repos/{owner}/{name}/issues/{issue_number}/comments",
            json={"body": body},
        )

    def add_labels(self, repo: str, issue_number: int, labels: list[str]) -> None:
        if not labels:
            return
        owner, name = parse_repo(repo)
        self._request(
            "POST",
            f"/repos/{owner}/{name}/issues/{issue_number}/labels",
            json={"labels": labels},
        )


def mock_issue(number: int = 42) -> GitHubIssue:
    """Deterministic issue for mock/offline runs."""
    return GitHubIssue(
        number=number,
        title="Unable to reproduce nnU-Net training results on BraTS subset",
        body=(
            "Hi maintainers,\n\n"
            "I'm trying to reproduce the BraTS segmentation benchmark using nnU-Net v2 "
            "with CUDA 12.1 and PyTorch 2.2. My Dice scores are ~5% lower than reported.\n\n"
            "**Environment:** Ubuntu 22.04, MONAI 1.3, single A100\n"
            "**Config:** default nnUNetTrainer, fold 0\n\n"
            "Has anyone seen similar variance? Happy to share my preprocessing logs."
        ),
        state="open",
        html_url="https://github.com/example/med-ai/issues/42",
        labels=("question",),
        user="researcher-dev",
    )


def mock_recent_issues() -> list[GitHubIssue]:
    return [
        mock_issue(42),
        GitHubIssue(
            number=38,
            title="Dataset download link for CheXpert subset returns 403",
            body="The linked CheXpert mirror seems to require updated credentials.",
            state="open",
            html_url="https://github.com/example/med-ai/issues/38",
            labels=("dataset",),
            user="clinician-ml",
        ),
        GitHubIssue(
            number=35,
            title="MONAI transform fails on DICOM series with missing SliceThickness",
            body="Running LoadImageD on a de-identified chest CT series raises KeyError.",
            state="open",
            html_url="https://github.com/example/med-ai/issues/35",
            labels=("bug", "monai"),
            user="rad-ai",
        ),
    ]
