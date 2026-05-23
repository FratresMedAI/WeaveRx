"""Supportive draft response refinement for medical AI issues."""

from __future__ import annotations

from weaverx.categories import CATEGORY_BY_SLUG
from weaverx.github import GitHubIssue
from weaverx.llm import TriageAnalysis


def _opening_line(issue: GitHubIssue) -> str:
    author = issue.user or "there"
    return f"Hi @{author} - thank you for sharing this with the community."


def _category_guidance(slug: str) -> str:
    cat = CATEGORY_BY_SLUG.get(slug)
    if not cat:
        return ""
    return cat.healer_framing


def _privacy_addendum(flags: list[str]) -> str:
    if not flags:
        return ""
    return (
        "\n\n---\n"
        "**Privacy note:** Please avoid sharing patient identifiers, DICOM UIDs tied to "
        "individuals, or other PHI in public issues. De-identified logs, synthetic data, "
        "or private maintainer channels are safer ways to share sensitive details."
    )


def _repro_checklist() -> str:
    return (
        "\n\n**Repro checklist (helps us help you faster):**\n"
        "- Package versions (PyTorch, MONAI, nnU-Net, CUDA)\n"
        "- Config files or trainer/plan identifiers\n"
        "- Random seed and data split/fold\n"
        "- Minimal command or notebook snippet"
    )


def refine_draft(issue: GitHubIssue, analysis: TriageAnalysis) -> str:
    """
    Ensure the draft feels supportive and includes practical next steps.
    If the LLM draft is already strong, lightly augment rather than replace.
    """
    draft = analysis.draft_response.strip()
    if len(draft) < 80:
        draft = (
            f"{_opening_line(issue)}\n\n"
            f"{analysis.impact_summary}\n\n"
            f"{_category_guidance(analysis.category)}"
        )

    if analysis.category == "reproducibility-environment" and "version" not in draft.lower():
        draft += _repro_checklist()

    needs_privacy = analysis.category == "privacy-compliance-dicom" or analysis.privacy_flags
    if needs_privacy and "phi" not in draft.lower() and "patient" not in draft.lower():
        draft += _privacy_addendum(analysis.privacy_flags)

    if not draft.startswith("Hi"):
        draft = f"{_opening_line(issue)}\n\n{draft}"

    return draft.strip()
