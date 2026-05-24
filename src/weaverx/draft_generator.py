"""Supportive draft response refinement for medical AI issues."""

from __future__ import annotations

from weaverx.categories import CATEGORY_BY_SLUG
from weaverx.github import GitHubIssue
from weaverx.llm import DuplicateMatch, TriageAnalysis


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


def _dataset_access_checklist() -> str:
    return (
        "\n\n**Access checklist:**\n"
        "- Which URL or form step failed (HTTP status if known)\n"
        "- Whether you received a license confirmation email\n"
        "- Dataset version/subset name and intended use (research vs. clinical)"
    )


def _clinical_validation_note() -> str:
    return (
        "\n\n**Validation scope:** WeaveRx drafts are maintainer support, not regulatory advice. "
        "For clinical deployment, clarify whether you need research benchmarking, reader studies, "
        "or formal validation—and consult your IRB/compliance team for regulated workflows."
    )


def _bug_repro_prompt() -> str:
    return (
        "\n\n**To reproduce:**\n"
        "- Steps to trigger the issue (minimal script or CLI command)\n"
        "- Expected vs. actual behavior\n"
        "- Stack trace or log excerpt (redact identifiers)"
    )


def _duplicate_crosslink(matches: list[DuplicateMatch]) -> str:
    if not matches:
        return ""
    top = matches[0]
    return (
        f"\n\n**Possible related issue:** #{top.issue_number} "
        f"({top.title}) — {top.url}\n"
        "If this is the same topic, we can consolidate discussion there."
    )


def refine_draft(
    issue: GitHubIssue,
    analysis: TriageAnalysis,
    *,
    duplicate_matches: list[DuplicateMatch] | None = None,
) -> str:
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

    category = analysis.category
    lowered = draft.lower()

    if category == "reproducibility-environment" and "repro checklist" not in lowered:
        draft += _repro_checklist()

    if category == "dataset-access-licensing" and "access checklist" not in lowered:
        draft += _dataset_access_checklist()

    if category == "clinical-validation" and "validation scope" not in lowered:
        draft += _clinical_validation_note()

    if category == "bug" and "to reproduce" not in lowered:
        draft += _bug_repro_prompt()

    needs_privacy = category == "privacy-compliance-dicom" or analysis.privacy_flags
    if needs_privacy and "privacy note" not in lowered:
        draft += _privacy_addendum(analysis.privacy_flags)

    if (
        duplicate_matches
        and analysis.duplicate_likelihood >= 0.35
        and f"#{duplicate_matches[0].issue_number}" not in draft
    ):
        draft += _duplicate_crosslink(duplicate_matches)

    if not draft.startswith("Hi"):
        draft = f"{_opening_line(issue)}\n\n{draft}"

    return draft.strip()
