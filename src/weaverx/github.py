"""GitHub REST API client for issue triage."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

from weaverx.utils import parse_repo


@dataclass(frozen=True, slots=True)
class GitHubIssue:
    number: int
    title: str
    body: str
    state: str
    html_url: str
    labels: tuple[str, ...]
    user: str | None


class GitHubClient:
    API_BASE = "https://api.github.com"

    def __init__(self, token: str | None, *, timeout: float = 30.0) -> None:
        headers: dict[str, str] = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"
        self._client = httpx.Client(base_url=self.API_BASE, headers=headers, timeout=timeout)

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> GitHubClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

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
        response = self._client.get(f"/repos/{owner}/{name}/issues/{issue_number}")
        response.raise_for_status()
        return self._parse_issue(response.json())

    def fetch_recent_issues(
        self,
        repo: str,
        *,
        limit: int = 30,
        state: str = "open",
    ) -> list[GitHubIssue]:
        owner, name = parse_repo(repo)
        params: dict[str, str | int] = {
            "state": state,
            "per_page": min(limit, 100),
            "sort": "created",
            "direction": "desc",
        }
        response = self._client.get(f"/repos/{owner}/{name}/issues", params=params)
        response.raise_for_status()
        items = response.json()
        issues: list[GitHubIssue] = []
        for item in items:
            if "pull_request" in item:
                continue
            issues.append(self._parse_issue(item))
            if len(issues) >= limit:
                break
        return issues

    def post_comment(self, repo: str, issue_number: int, body: str) -> None:
        owner, name = parse_repo(repo)
        response = self._client.post(
            f"/repos/{owner}/{name}/issues/{issue_number}/comments",
            json={"body": body},
        )
        response.raise_for_status()

    def add_labels(self, repo: str, issue_number: int, labels: list[str]) -> None:
        if not labels:
            return
        owner, name = parse_repo(repo)
        response = self._client.post(
            f"/repos/{owner}/{name}/issues/{issue_number}/labels",
            json={"labels": labels},
        )
        response.raise_for_status()


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
