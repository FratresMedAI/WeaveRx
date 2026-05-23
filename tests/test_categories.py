"""Tests for medical AI categories."""

from weaverx.categories import (
    CATEGORY_BY_SLUG,
    MED_AI_CATEGORIES,
    category_prompt_block,
    validate_category_slug,
)


def test_eight_categories_defined() -> None:
    assert len(MED_AI_CATEGORIES) == 8


def test_category_slugs_unique() -> None:
    slugs = [c.slug for c in MED_AI_CATEGORIES]
    assert len(slugs) == len(set(slugs))


def test_validate_category_slug_normalizes() -> None:
    assert validate_category_slug("reproducibility-environment") == "reproducibility-environment"
    assert validate_category_slug("bug") == "bug"
    assert validate_category_slug("unknown-thing") == "bug"


def test_category_prompt_block_includes_all() -> None:
    block = category_prompt_block()
    for cat in MED_AI_CATEGORIES:
        assert cat.display_name in block
        assert cat.slug in block


def test_category_lookup() -> None:
    assert "dataset-access-licensing" in CATEGORY_BY_SLUG
    assert CATEGORY_BY_SLUG["dataset-access-licensing"].suggested_labels
