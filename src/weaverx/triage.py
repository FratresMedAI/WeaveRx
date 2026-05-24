"""Core triage orchestration for WeaveRx."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from weaverx.categories import CATEGORY_BY_SLUG
from weaverx.draft_generator import refine_draft
from weaverx.duplicate_detector import best_duplicate_score, find_duplicates
from weaverx.github import (
    GitHubClient,
    GitHubComment,
    GitHubIssue,
    mock_issue,
    mock_recent_issues,
)
from weaverx.llm import (
    DuplicateMatch,
    LLMMetadata,
    LLMProvider,
    TriageAnalysis,
    create_llm_provider,
)
from weaverx.safeguards import SafeguardReport, run_safeguards
from weaverx.utils import LOG, get_env, is_mock_mode, require_confirmation

TriageStatus = Literal["ready_for_review", "posted"]


@dataclass(slots=True)
class TriageResult:
    repo: str
    issue: GitHubIssue
    analysis: TriageAnalysis
    duplicate_matches: list[DuplicateMatch] = field(default_factory=list)
    heuristic_duplicate_score: float = 0.0
    draft_response: str = ""
    dry_run: bool = False
    posted_comment: bool = False
    applied_labels: list[str] = field(default_factory=list)
    safeguard: SafeguardReport | None = None
    llm: LLMMetadata | None = None

    def result_status(self) -> TriageStatus:
        if self.posted_comment or self.applied_labels:
            return "posted"
        return "ready_for_review"

    def to_dict(self) -> dict[str, Any]:
        cat = CATEGORY_BY_SLUG.get(self.analysis.category)
        return {
            "repo": self.repo,
            "status": self.result_status(),
            "issue": {
                "number": self.issue.number,
                "title": self.issue.title,
                "url": self.issue.html_url,
                "author": self.issue.user,
                "labels": list(self.issue.labels),
            },
            "analysis": self.analysis.model_dump(),
            "category_display": cat.display_name if cat else self.analysis.category,
            "sources": [source.model_dump() for source in self.analysis.sources],
            "duplicate_matches": [m.model_dump() for m in self.duplicate_matches],
            "heuristic_duplicate_score": self.heuristic_duplicate_score,
            "draft_response": self.draft_response,
            "safeguard": self.safeguard.to_dict() if self.safeguard else None,
            "llm": self.llm.model_dump() if self.llm else None,
            "dry_run": self.dry_run,
            "posted_comment": self.posted_comment,
            "applied_labels": self.applied_labels,
        }


@dataclass(slots=True)
class TriageOptions:
    repo: str
    issue_number: int | None = None
    recent: int | None = None
    mock: bool = False
    mock_llm: bool = False
    dry_run: bool = False
    confirm: bool = False
    privacy_insight: bool = True
    safeguards: bool = True
    llm_provider: str | None = None
    llm_model: str | None = None
    post_comment: bool = False
    apply_labels: bool = False


class TriageOrchestrator:
    def __init__(
        self,
        *,
        github_token: str | None,
        llm: LLMProvider | None = None,
        mock: bool = False,
        mock_llm: bool = False,
        llm_provider: str | None = None,
        llm_model: str | None = None,
    ) -> None:
        self._mock = mock
        self._mock_llm = mock_llm
        self._github_token = github_token
        self._llm = llm
        self._llm_provider = llm_provider
        self._llm_model = llm_model

    def _get_llm(self) -> LLMProvider:
        if self._llm is not None:
            return self._llm
        use_mock_llm = self._mock or self._mock_llm
        provider = None if use_mock_llm else (self._llm_provider or get_env("WEAVERX_LLM_PROVIDER"))
        model = self._llm_model or get_env("WEAVERX_LLM_MODEL")
        self._llm = create_llm_provider(
            mock=use_mock_llm,
            provider=provider,
            model=model,
        )
        return self._llm

    def _fetch_context(
        self,
        repo: str,
        issue_number: int,
    ) -> tuple[GitHubIssue, list[GitHubIssue], list[GitHubComment]]:
        if self._mock:
            issue = mock_issue(issue_number)
            recent = [i for i in mock_recent_issues() if i.number != issue_number]
            return issue, recent, []

        with GitHubClient(self._github_token) as client:
            issue = client.fetch_issue(repo, issue_number)
            recent = client.fetch_recent_issues(repo, limit=30)
            comments = client.fetch_issue_comments(repo, issue_number, limit=5)
        recent = [i for i in recent if i.number != issue_number]
        return issue, recent, comments

    def triage_one(self, options: TriageOptions) -> TriageResult:
        if options.issue_number is None:
            raise ValueError("issue_number is required for single triage.")

        issue, recent, comments = self._fetch_context(options.repo, options.issue_number)
        duplicates = find_duplicates(issue, recent)
        heuristic_score = best_duplicate_score(duplicates)

        llm = self._get_llm()
        analysis = llm.analyze(
            issue,
            duplicate_candidates=duplicates,
            heuristic_duplicate_score=heuristic_score,
            privacy_insight=options.privacy_insight,
            issue_comments=comments,
        )
        draft = refine_draft(issue, analysis, duplicate_matches=duplicates)

        safeguard = None
        if options.safeguards:
            safeguard = run_safeguards(
                draft,
                issue_title=issue.title,
                issue_body=issue.body,
            )

        result = TriageResult(
            repo=options.repo,
            issue=issue,
            analysis=analysis,
            duplicate_matches=duplicates,
            heuristic_duplicate_score=heuristic_score,
            draft_response=draft,
            dry_run=options.dry_run,
            safeguard=safeguard,
            llm=llm.metadata,
        )

        if options.post_comment or options.apply_labels:
            self._maybe_apply(options, result)

        return result

    def triage_recent(self, options: TriageOptions) -> list[TriageResult]:
        count = options.recent or 10
        if self._mock:
            issues = mock_recent_issues()[:count]
        else:
            with GitHubClient(self._github_token) as client:
                issues = client.fetch_recent_issues(options.repo, limit=count)

        results: list[TriageResult] = []
        for issue in issues:
            single = TriageOptions(
                repo=options.repo,
                issue_number=issue.number,
                mock=options.mock,
                mock_llm=options.mock_llm,
                dry_run=options.dry_run,
                confirm=options.confirm,
                privacy_insight=options.privacy_insight,
                safeguards=options.safeguards,
                llm_provider=options.llm_provider,
                llm_model=options.llm_model,
                post_comment=False,
                apply_labels=False,
            )
            results.append(self.triage_one(single))
        return results

    def _maybe_apply(self, options: TriageOptions, result: TriageResult) -> None:
        if self._mock:
            LOG.info("Mock mode: skipping GitHub writes.")
            return

        if not self._github_token:
            raise ValueError("GITHUB_TOKEN is required to post comments or labels.")

        with GitHubClient(self._github_token) as client:
            if options.post_comment:
                allowed = require_confirmation(
                    confirm=options.confirm,
                    dry_run=options.dry_run,
                    action_description=f"posting triage comment on #{result.issue.number}",
                )
                if allowed:
                    client.post_comment(options.repo, result.issue.number, result.draft_response)
                    result.posted_comment = True

            if options.apply_labels:
                allowed = require_confirmation(
                    confirm=options.confirm,
                    dry_run=options.dry_run,
                    action_description=f"applying labels to #{result.issue.number}",
                )
                if allowed:
                    labels = result.analysis.suggested_labels
                    client.add_labels(options.repo, result.issue.number, labels)
                    result.applied_labels = labels


def build_orchestrator(
    *,
    mock: bool = False,
    mock_llm: bool = False,
    llm_provider: str | None = None,
    llm_model: str | None = None,
) -> TriageOrchestrator:
    use_mock = is_mock_mode(mock)
    token = None if use_mock else get_env("GITHUB_TOKEN")
    return TriageOrchestrator(
        github_token=token,
        mock=use_mock,
        mock_llm=mock_llm or use_mock,
        llm_provider=llm_provider,
        llm_model=llm_model,
    )
