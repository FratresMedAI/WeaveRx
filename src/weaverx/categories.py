"""Medical AI issue categories with restorative, community-oriented framing."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class Priority(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True, slots=True)
class MedAICategory:
    slug: str
    display_name: str
    description: str
    suggested_labels: tuple[str, ...]
    healer_framing: str


MED_AI_CATEGORIES: tuple[MedAICategory, ...] = (
    MedAICategory(
        slug="dataset-access-licensing",
        display_name="Dataset Access & Licensing",
        description=(
            "Questions about obtaining datasets, usage terms, attribution, "
            "or redistribution constraints for medical imaging or clinical data."
        ),
        suggested_labels=("dataset", "data-access", "licensing"),
        healer_framing=(
            "Acknowledge how dataset friction slows research; offer clear paths "
            "to documentation, access forms, or community-maintained mirrors."
        ),
    ),
    MedAICategory(
        slug="model-performance-pathology",
        display_name="Model Performance (Pathology/Subgroup)",
        description=(
            "Reports or questions about model accuracy on specific pathologies, "
            "anatomical sites, patient subgroups, or edge cases."
        ),
        suggested_labels=("performance", "pathology", "subgroup"),
        healer_framing=(
            "Validate the concern—subgroup performance matters clinically. "
            "Invite reproducible eval details and point to benchmark scripts."
        ),
    ),
    MedAICategory(
        slug="reproducibility-environment",
        display_name="Reproducibility & Environment",
        description=(
            "Setup issues, dependency conflicts, MONAI/nnU-Net version mismatches, "
            "CUDA/PyTorch environments, or inability to reproduce published results."
        ),
        suggested_labels=("reproducibility", "environment", "monai", "nnunet"),
        healer_framing=(
            "Reproducibility is the bedrock of medical AI trust. Offer a gentle "
            "checklist: versions, seeds, config files, and minimal repro steps."
        ),
    ),
    MedAICategory(
        slug="clinical-validation",
        display_name="Clinical Validation Request",
        description=(
            "Requests for external validation, reader studies, prospective evaluation, "
            "or guidance on moving from research code to clinical assessment."
        ),
        suggested_labels=("clinical-validation", "evaluation"),
        healer_framing=(
            "Honor the clinical lens. Clarify scope (research vs. regulated use) "
            "and suggest validation frameworks without overpromising."
        ),
    ),
    MedAICategory(
        slug="privacy-compliance-dicom",
        display_name="Privacy/Compliance/DICOM Considerations",
        description=(
            "PHI handling, de-identification, HIPAA/GDPR questions, DICOM metadata, "
            "or concerns about sensitive data in issues or workflows."
        ),
        suggested_labels=("privacy", "compliance", "dicom", "phi"),
        healer_framing=(
            "Respond with care and containment. Never ask for patient identifiers; "
            "redirect to safe, de-identified sharing practices."
        ),
    ),
    MedAICategory(
        slug="bug",
        display_name="Bug",
        description="Unexpected crashes, incorrect outputs, or broken functionality.",
        suggested_labels=("bug",),
        healer_framing=(
            "Thank them for the report. Ask for minimal repro steps and environment "
            "details in a supportive, non-blaming tone."
        ),
    ),
    MedAICategory(
        slug="feature-integration",
        display_name="Feature/Integration Request",
        description=(
            "New capabilities, framework integrations (MONAI, nnU-Net, ITK), "
            "or workflow improvements."
        ),
        suggested_labels=("enhancement", "integration"),
        healer_framing=(
            "Welcome the idea; explain fit with project scope and invite a design "
            "sketch or use case from their clinical/research context."
        ),
    ),
    MedAICategory(
        slug="documentation",
        display_name="Documentation",
        description="Missing, unclear, or outdated docs, tutorials, or API references.",
        suggested_labels=("documentation",),
        healer_framing=(
            "Documentation gaps are community gifts—each question helps the next "
            "researcher. Point to existing docs and offer to clarify."
        ),
    ),
)

CATEGORY_BY_SLUG: dict[str, MedAICategory] = {c.slug: c for c in MED_AI_CATEGORIES}

# Keywords used to boost duplicate detection and privacy scanning.
MED_AI_KEYWORDS: frozenset[str] = frozenset(
    {
        "monai",
        "nnunet",
        "nn-u-net",
        "dicom",
        "nifti",
        "chestxray",
        "chexpert",
        "mimic",
        "brats",
        "isic",
        "pathology",
        "segmentation",
        "radiology",
        "hipaa",
        "gdpr",
        "phi",
        "de-identification",
        "deidentification",
        "clinical",
        "validation",
        "reproducibility",
        "cuda",
        "pytorch",
    }
)

PRIVACY_KEYWORDS: frozenset[str] = frozenset(
    {
        "phi",
        "hipaa",
        "gdpr",
        "patient id",
        "patient name",
        "mrn",
        "medical record",
        "dicom",
        "identifiable",
        "de-ident",
        "deident",
        "ssn",
        "date of birth",
        "dob",
    }
)


def category_prompt_block() -> str:
    """Format categories for LLM system prompts."""
    lines: list[str] = []
    for cat in MED_AI_CATEGORIES:
        labels = ", ".join(cat.suggested_labels)
        lines.append(
            f"- **{cat.display_name}** (`{cat.slug}`): {cat.description} "
            f"[labels: {labels}]"
        )
    return "\n".join(lines)


def validate_category_slug(slug: str) -> str:
    """Return slug if valid, otherwise the closest match or 'bug'."""
    if slug in CATEGORY_BY_SLUG:
        return slug
    normalized = slug.lower().replace("_", "-").replace(" ", "-")
    if normalized in CATEGORY_BY_SLUG:
        return normalized
    for cat in MED_AI_CATEGORIES:
        if cat.slug in normalized or normalized in cat.slug:
            return cat.slug
    return "bug"
