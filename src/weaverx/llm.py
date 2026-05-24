"""LLM providers for medical AI issue triage (multi-provider via LiteLLM)."""

from __future__ import annotations

import json
import os
import re
from abc import ABC, abstractmethod
from typing import Any, Literal

import litellm
from pydantic import BaseModel, Field, field_validator

from weaverx.categories import (
    CATEGORY_BY_SLUG,
    MED_AI_CATEGORIES,
    PRIVACY_KEYWORDS,
    Priority,
    category_prompt_block,
    validate_category_slug,
)
from weaverx.github import GitHubComment, GitHubIssue

PriorityLevel = Literal["low", "medium", "high", "critical"]
LLMProviderName = Literal["grok", "anthropic", "openai", "mock"]
SourceType = Literal["issue_title", "issue_body", "issue_comment", "duplicate_issue"]

DEFAULT_MODELS: dict[str, str] = {
    "grok": "xai/grok-2-latest",
    "anthropic": "anthropic/claude-3-5-sonnet-20241022",
    "openai": "openai/gpt-4o",
}

PROVIDER_API_KEY_ENV: dict[str, str] = {
    "grok": "XAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
}


class TriageSource(BaseModel):
    type: SourceType
    snippet: str
    reason: str

    @field_validator("snippet")
    @classmethod
    def trim_snippet(cls, value: str) -> str:
        return value.strip()[:500]


class TriageAnalysis(BaseModel):
    category: str
    priority: PriorityLevel
    impact_summary: str
    duplicate_likelihood: float = Field(ge=0.0, le=1.0)
    suggested_labels: list[str]
    draft_response: str
    privacy_flags: list[str] = Field(default_factory=list)
    reasoning: str
    sources: list[TriageSource] = Field(default_factory=list)

    @field_validator("category")
    @classmethod
    def normalize_category(cls, value: str) -> str:
        return validate_category_slug(value)

    @field_validator("priority", mode="before")
    @classmethod
    def normalize_priority(cls, value: str) -> str:
        normalized = str(value).lower().strip()
        if normalized in {p.value for p in Priority}:
            return normalized
        return Priority.MEDIUM.value

    @field_validator("duplicate_likelihood", mode="before")
    @classmethod
    def clamp_duplicate(cls, value: float | int | str) -> float:
        try:
            score = float(value)
        except (TypeError, ValueError):
            return 0.0
        return max(0.0, min(1.0, score))


class DuplicateMatch(BaseModel):
    issue_number: int
    title: str
    score: float
    url: str


class LLMMetadata(BaseModel):
    provider: LLMProviderName
    model: str


def _build_system_prompt(*, privacy_insight: bool) -> str:
    privacy_note = (
        "\n\nAlso flag privacy/containment concerns in `privacy_flags` "
        "(e.g. possible_phi, dicom_handling, credential_exposure) when the issue "
        "may involve sensitive clinical data. Never encourage sharing identifiers."
        if privacy_insight
        else ""
    )
    return f"""You are WeaveRx, a supportive triage assistant for open-source medical AI projects.

Your tone is warm, practical, and community-oriented—never stern or dismissive.
Researchers and clinicians often juggle IRB constraints, dataset licenses, and reproducibility
challenges. Illuminate the issue clearly and offer restorative guidance.

Classify issues into exactly ONE of these medical AI categories:
{category_prompt_block()}

Priority guidance for medical AI:
- critical: data safety/PHI exposure, blocking clinical deployment, widespread breakage
- high: reproducibility blockers, benchmark integrity, major clinical validation gaps
- medium: subgroup performance concerns, integration friction, unclear docs
- low: minor docs typos, nice-to-have features, general questions

Respond with ONLY valid JSON matching this schema:
{{
  "category": "<category-slug>",
  "priority": "low|medium|high|critical",
  "impact_summary": "<1-2 sentences>",
  "duplicate_likelihood": <0.0-1.0>,
  "suggested_labels": ["label1", "label2"],
  "draft_response": "<supportive GitHub comment, markdown ok>",
  "privacy_flags": ["flag1"],
  "reasoning": "<brief maintainer note>",
  "sources": [
    {{
      "type": "issue_title|issue_body|issue_comment|duplicate_issue",
      "snippet": "<short excerpt from the issue or comment>",
      "reason": "<why this excerpt grounded your triage decision>"
    }}
  ]
}}

Include 1-4 sources citing the specific issue text (title, body, or comments) that informed
your category, priority, and draft. Keep snippets short and verbatim where possible.

Draft responses should:
- Open with a warm greeting to the issue author (@username when known)
- Acknowledge the specific blocker before suggesting next steps
- Offer concrete, category-appropriate asks (versions, configs, access steps)
- Never request PHI, patient identifiers, or raw DICOM with identifiers in public threads
{privacy_note}
"""


def _few_shot_messages() -> list[dict[str, str]]:
    """Compact examples to stabilize JSON structure and tone."""
    return [
        {
            "role": "user",
            "content": (
                "Triage this GitHub issue:\n\n"
                "**Repository issue:** #1204\n"
                "**Title:** Cannot reproduce nnU-Net BraTS Dice scores\n"
                "**Author:** ml-researcher\n"
                "**Labels:** question\n"
                "**Body:**\n"
                "Using PyTorch 2.2, CUDA 12.1, MONAI 1.3, default nnUNetTrainer fold 0. "
                "Dice ~5% below paper.\n\n"
                "**Recent comments:**\nNone.\n\n"
                "Heuristic duplicate score from recent issues: 0.12\n"
                "Candidate duplicates:\nNone found.\n\n"
                "Produce JSON triage analysis with a helpful draft_response ready to post."
            ),
        },
        {
            "role": "assistant",
            "content": json.dumps(
                {
                    "category": "reproducibility-environment",
                    "priority": "high",
                    "impact_summary": (
                        "Benchmark reproduction mismatch may block trust in reported BraTS scores."
                    ),
                    "duplicate_likelihood": 0.12,
                    "suggested_labels": ["reproducibility", "environment", "nnunet"],
                    "draft_response": (
                        "Hi @ml-researcher — thank you for documenting your setup carefully.\n\n"
                        "A ~5% Dice gap often traces to preprocessing plans, fold/seed, or "
                        "package versions. Could you share PyTorch/CUDA/MONAI/nnU-Net versions, "
                        "the trainer/plan ID, and a minimal command? No patient data needed."
                    ),
                    "privacy_flags": [],
                    "reasoning": "Reproduction/environment mismatch on a standard benchmark.",
                    "sources": [
                        {
                            "type": "issue_body",
                            "snippet": "Dice ~5% below paper",
                            "reason": "Quantified reproduction gap drives high priority.",
                        }
                    ],
                }
            ),
        },
        {
            "role": "user",
            "content": (
                "Triage this GitHub issue:\n\n"
                "**Repository issue:** #88\n"
                "**Title:** CheXpert subset download returns 403\n"
                "**Author:** clinician-dev\n"
                "**Labels:** dataset\n"
                "**Body:**\n"
                "Submitted the license form but the mirror link still returns 403.\n\n"
                "**Recent comments:**\nNone.\n\n"
                "Heuristic duplicate score from recent issues: 0.05\n"
                "Candidate duplicates:\nNone found.\n\n"
                "Produce JSON triage analysis with a helpful draft_response ready to post."
            ),
        },
        {
            "role": "assistant",
            "content": json.dumps(
                {
                    "category": "dataset-access-licensing",
                    "priority": "medium",
                    "impact_summary": (
                        "Dataset access blocked after licensing step; slows downstream experiments."
                    ),
                    "duplicate_likelihood": 0.05,
                    "suggested_labels": ["dataset", "data-access"],
                    "draft_response": (
                        "Hi @clinician-dev — sorry the mirror is blocking you after the form.\n\n"
                        "Could you note which URL returns 403 and whether you received a "
                        "confirmation email? We can point you to the current access docs or "
                        "a community mirror if available."
                    ),
                    "privacy_flags": [],
                    "reasoning": "Classic dataset licensing/access friction.",
                    "sources": [
                        {
                            "type": "issue_body",
                            "snippet": "mirror link still returns 403",
                            "reason": "Access failure described in issue body.",
                        }
                    ],
                }
            ),
        },
    ]


def _build_user_prompt(
    issue: GitHubIssue,
    *,
    duplicate_candidates: list[DuplicateMatch],
    heuristic_duplicate_score: float,
    issue_comments: list[GitHubComment] | None = None,
) -> str:
    dupes_text = "None found."
    if duplicate_candidates:
        lines = [
            f"- #{d.issue_number} (score {d.score:.2f}): {d.title} ({d.url})"
            for d in duplicate_candidates
        ]
        dupes_text = "\n".join(lines)

    comments_text = "None."
    if issue_comments:
        comment_lines = [
            f"- @{c.user or 'unknown'}: {c.body[:400]}{'...' if len(c.body) > 400 else ''}"
            for c in issue_comments[:5]
        ]
        comments_text = "\n".join(comment_lines)

    return f"""Triage this GitHub issue:

**Repository issue:** #{issue.number}
**Title:** {issue.title}
**Author:** {issue.user or "unknown"}
**Labels:** {", ".join(issue.labels) or "none"}
**Body:**
{issue.body or "(empty)"}

**Recent comments:**
{comments_text}

Heuristic duplicate score from recent issues: {heuristic_duplicate_score:.2f}
Candidate duplicates:
{dupes_text}

Produce JSON triage analysis with a helpful draft_response ready to post.
"""


def scan_privacy_keywords(text: str) -> list[str]:
    lowered = text.lower()
    flags: list[str] = []
    for keyword in PRIVACY_KEYWORDS:
        if keyword in lowered:
            flags.append(f"keyword:{keyword.replace(' ', '_')}")
    if "dicom" in lowered:
        flags.append("dicom_handling")
    if any(k in lowered for k in ("patient", "phi", "hipaa", "gdpr")):
        flags.append("possible_phi")
    return sorted(set(flags))


def _extract_json(content: str) -> dict[str, Any]:
    content = content.strip()
    try:
        parsed = json.loads(content)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{.*\}", content, re.DOTALL)
    if match:
        parsed = json.loads(match.group())
        if isinstance(parsed, dict):
            return parsed
    raise ValueError(f"LLM response did not contain valid JSON: {content[:200]}...")


def _normalize_provider(value: str | None) -> LLMProviderName:
    normalized = (value or os.environ.get("WEAVERX_LLM_PROVIDER", "grok")).lower().strip()
    if normalized in {"grok", "anthropic", "openai", "mock"}:
        return normalized  # type: ignore[return-value]
    raise ValueError(
        f"Unsupported LLM provider: {normalized!r}. "
        "Use grok, anthropic, or openai (or --mock for offline)."
    )


def resolve_model(provider: LLMProviderName, model: str | None = None) -> str:
    if model:
        return model
    env_model = os.environ.get("WEAVERX_LLM_MODEL")
    if env_model:
        return env_model
    if provider == "mock":
        return "mock"
    return DEFAULT_MODELS[provider]


def resolve_api_key(provider: LLMProviderName) -> str | None:
    if provider == "mock":
        return None
    env_name = PROVIDER_API_KEY_ENV[provider]
    return os.environ.get(env_name)


def _build_mock_sources(issue: GitHubIssue, category: str) -> list[TriageSource]:
    sources = [
        TriageSource(
            type="issue_title",
            snippet=issue.title,
            reason=f"Confirmed triage category: {category}.",
        )
    ]
    if issue.body:
        first_line = next((line.strip() for line in issue.body.splitlines() if line.strip()), "")
        if first_line:
            sources.append(
                TriageSource(
                    type="issue_body",
                    snippet=first_line[:300],
                    reason="Key issue details used for classification and draft.",
                )
            )
    return sources


class LLMProvider(ABC):
    @property
    @abstractmethod
    def metadata(self) -> LLMMetadata:
        raise NotImplementedError

    @abstractmethod
    def analyze(
        self,
        issue: GitHubIssue,
        *,
        duplicate_candidates: list[DuplicateMatch],
        heuristic_duplicate_score: float,
        privacy_insight: bool = True,
        issue_comments: list[GitHubComment] | None = None,
    ) -> TriageAnalysis:
        raise NotImplementedError


class MockLLMProvider(LLMProvider):
    """Deterministic offline provider for tests and demos."""

    @property
    def metadata(self) -> LLMMetadata:
        return LLMMetadata(provider="mock", model="mock")

    def analyze(
        self,
        issue: GitHubIssue,
        *,
        duplicate_candidates: list[DuplicateMatch],
        heuristic_duplicate_score: float,
        privacy_insight: bool = True,
        issue_comments: list[GitHubComment] | None = None,
    ) -> TriageAnalysis:
        del issue_comments
        text = f"{issue.title}\n{issue.body}"
        lowered = text.lower()
        privacy_flags = scan_privacy_keywords(text) if privacy_insight else []
        dup_score = max(heuristic_duplicate_score, 0.15 if duplicate_candidates else 0.05)

        category, priority, labels, impact = _infer_mock_analysis(lowered, privacy_flags)
        cat = CATEGORY_BY_SLUG[category]
        draft = _build_mock_draft(issue, category, cat.healer_framing, impact)
        sources = _build_mock_sources(issue, category)

        if duplicate_candidates:
            top = duplicate_candidates[0]
            sources.append(
                TriageSource(
                    type="duplicate_issue",
                    snippet=top.title,
                    reason=f"Heuristic duplicate score {top.score:.2f} from recent issues.",
                )
            )

        return TriageAnalysis(
            category=category,
            priority=priority,
            impact_summary=impact,
            duplicate_likelihood=dup_score,
            suggested_labels=labels,
            draft_response=draft,
            privacy_flags=privacy_flags,
            reasoning=(
                f"Heuristic mock triage classified as {cat.display_name}. "
                f"Set an LLM API key for full provider analysis."
            ),
            sources=sources,
        )


def _infer_mock_analysis(
    lowered: str,
    privacy_flags: list[str],
) -> tuple[str, PriorityLevel, list[str], str]:
    if privacy_flags or any(
        k in lowered for k in ("hipaa", "gdpr", "phi", "patient id", "mrn", "identifiable")
    ):
        return (
            "privacy-compliance-dicom",
            "critical",
            ["privacy", "compliance", "dicom"],
            "Issue may involve sensitive clinical data handling that needs careful containment.",
        )
    if any(
        k in lowered for k in ("dataset", "download", "licens", "chexpert", "403", "data access")
    ):
        return (
            "dataset-access-licensing",
            "medium",
            ["dataset", "data-access"],
            "Dataset access or licensing appears to be the main blocker for this contributor.",
        )
    if any(
        k in lowered
        for k in ("clinical validation", "reader study", "prospective", "fda", "clinical trial")
    ):
        return (
            "clinical-validation",
            "high",
            ["clinical-validation", "evaluation"],
            "Contributor is seeking guidance on clinical or external validation pathways.",
        )
    if "[bug]" in lowered or any(
        k in lowered for k in ("crash", "error", "exception", "fail", " broken", "bug:")
    ):
        return (
            "bug",
            "medium",
            ["bug"],
            "Unexpected behavior or failure reported that may affect users.",
        )
    if any(k in lowered for k in ("documentation", "docs", "tutorial", "readme", "example")):
        return (
            "documentation",
            "low",
            ["documentation"],
            "Documentation clarity would help the next researcher move faster.",
        )
    if any(k in lowered for k in ("feature", "integration", "enhancement", "support for")):
        return (
            "feature-integration",
            "medium",
            ["enhancement", "integration"],
            "Contributor is proposing a new capability or integration point.",
        )
    if any(
        k in lowered
        for k in (
            "reproduc",
            "cuda",
            "pytorch",
            "environment",
            "nnunet",
            "nn u-net",
            "cannot reproduce",
        )
    ):
        return (
            "reproducibility-environment",
            "high",
            ["reproducibility", "environment"],
            "Environment or reproduction mismatch may be blocking benchmark trust.",
        )
    if any(
        k in lowered for k in ("accuracy", "dice", "auc", "sensitivity", "pathology", "subgroup")
    ):
        return (
            "model-performance-pathology",
            "high",
            ["performance", "pathology"],
            "Model performance on a specific pathology or subgroup needs investigation.",
        )
    return (
        "documentation",
        "low",
        ["question"],
        "General question that may benefit from clearer docs or a pointer to examples.",
    )


def _build_mock_draft(
    issue: GitHubIssue,
    category: str,
    healer_framing: str,
    impact: str,
) -> str:
    author = issue.user or "there"
    lines = [
        f"Hi @{author} - thank you for taking the time to write this up.",
        "",
        impact,
        "",
        healer_framing,
    ]
    if category == "reproducibility-environment":
        lines.extend(
            [
                "",
                "A few things that often help us untangle medical AI reproduction issues:",
                "",
                "1. **Environment snapshot** - PyTorch, CUDA, MONAI/nnU-Net versions",
                "2. **Preprocessing** - config files or exported dataset plans",
                "3. **Seed & fold** - confirm split and random seed",
            ]
        )
    if category == "dataset-access-licensing":
        lines.extend(
            [
                "",
                "If you're blocked on access, sharing which step failed (form, mirror, "
                "credentials) helps us improve the path for the next researcher.",
            ]
        )
    lines.append("")
    lines.append("Happy to dig in once you share a bit more detail (no patient data, please!).")
    return "\n".join(lines)


class LiteLLMProvider(LLMProvider):
    """Unified provider backed by LiteLLM (Grok, Anthropic, OpenAI-compatible)."""

    def __init__(
        self,
        *,
        provider: LLMProviderName,
        model: str,
        api_key: str,
    ) -> None:
        if provider == "mock":
            raise ValueError("Use MockLLMProvider for mock mode.")
        self._provider = provider
        self._model = model
        self._api_key = api_key

    @property
    def metadata(self) -> LLMMetadata:
        return LLMMetadata(provider=self._provider, model=self._model)

    def analyze(
        self,
        issue: GitHubIssue,
        *,
        duplicate_candidates: list[DuplicateMatch],
        heuristic_duplicate_score: float,
        privacy_insight: bool = True,
        issue_comments: list[GitHubComment] | None = None,
    ) -> TriageAnalysis:
        messages: list[dict[str, str]] = [
            {"role": "system", "content": _build_system_prompt(privacy_insight=privacy_insight)},
            *_few_shot_messages(),
            {
                "role": "user",
                "content": _build_user_prompt(
                    issue,
                    duplicate_candidates=duplicate_candidates,
                    heuristic_duplicate_score=heuristic_duplicate_score,
                    issue_comments=issue_comments,
                ),
            },
        ]
        kwargs: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
            "api_key": self._api_key,
        }
        if self._provider == "openai" and os.environ.get("OPENAI_API_BASE"):
            kwargs["api_base"] = os.environ["OPENAI_API_BASE"]

        response = litellm.completion(**kwargs)
        content = response.choices[0].message.content
        if not content:
            raise ValueError("LLM returned empty content.")
        parsed = _extract_json(content)
        if "sources" not in parsed:
            parsed["sources"] = []
        analysis = TriageAnalysis.model_validate(parsed)
        if not analysis.sources:
            analysis = analysis.model_copy(
                update={"sources": _build_mock_sources(issue, analysis.category)}
            )

        if privacy_insight:
            keyword_flags = scan_privacy_keywords(f"{issue.title}\n{issue.body}")
            merged = sorted(set(analysis.privacy_flags) | set(keyword_flags))
            analysis = analysis.model_copy(update={"privacy_flags": merged})

        return analysis


def create_llm_provider(
    *,
    mock: bool,
    provider: str | None = None,
    model: str | None = None,
) -> LLMProvider:
    if mock:
        return MockLLMProvider()

    provider_name = _normalize_provider(provider)
    resolved_model = resolve_model(provider_name, model)
    api_key = resolve_api_key(provider_name)
    if not api_key:
        env_name = PROVIDER_API_KEY_ENV[provider_name]
        raise ValueError(
            f"{env_name} is required for LLM analysis with provider {provider_name!r}. "
            "Set the env var or pass --mock."
        )
    return LiteLLMProvider(provider=provider_name, model=resolved_model, api_key=api_key)


def default_labels_for_category(slug: str) -> list[str]:
    for cat in MED_AI_CATEGORIES:
        if cat.slug == slug:
            return list(cat.suggested_labels)
    return ["bug"]
