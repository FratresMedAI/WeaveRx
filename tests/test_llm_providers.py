"""Tests for LiteLLM provider factory and parsing."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from weaverx.github import GitHubIssue
from weaverx.llm import (
    LiteLLMProvider,
    MockLLMProvider,
    create_llm_provider,
    resolve_model,
)


def test_create_llm_provider_mock() -> None:
    provider = create_llm_provider(mock=True)
    assert isinstance(provider, MockLLMProvider)
    assert provider.metadata.provider == "mock"


def test_create_llm_provider_requires_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("XAI_API_KEY", raising=False)
    with pytest.raises(ValueError, match="XAI_API_KEY"):
        create_llm_provider(mock=False, provider="grok")


def test_resolve_model_defaults() -> None:
    assert resolve_model("anthropic") == "anthropic/claude-3-5-sonnet-20241022"
    assert resolve_model("openai") == "openai/gpt-4o"


def test_litellm_provider_parses_json_with_sources() -> None:
    issue = GitHubIssue(
        number=1,
        title="Dataset issue",
        body="Need BraTS dataset access",
        state="open",
        html_url="https://example.com/1",
        labels=(),
        user="u",
    )
    payload = {
        "category": "dataset-access-licensing",
        "priority": "medium",
        "impact_summary": "Dataset access blocked.",
        "duplicate_likelihood": 0.2,
        "suggested_labels": ["dataset"],
        "draft_response": "Hi @u — thanks for reporting this.",
        "privacy_flags": [],
        "reasoning": "Dataset licensing issue.",
        "sources": [
            {
                "type": "issue_body",
                "snippet": "Need BraTS dataset access",
                "reason": "Dataset access concern.",
            }
        ],
    }
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content=json.dumps(payload)))]

    with patch("weaverx.llm.litellm.completion", return_value=mock_response) as mock_completion:
        provider = LiteLLMProvider(provider="grok", model="xai/grok-2-latest", api_key="test-key")
        analysis = provider.analyze(issue, duplicate_candidates=[], heuristic_duplicate_score=0.0)

    assert analysis.category == "dataset-access-licensing"
    assert len(analysis.sources) == 1
    assert analysis.sources[0].type == "issue_body"
    mock_completion.assert_called_once()


def test_litellm_openai_uses_api_base(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_BASE", "https://example.com/v1")
    issue = GitHubIssue(
        number=1,
        title="t",
        body="b",
        state="open",
        html_url="https://example.com/1",
        labels=(),
        user="u",
    )
    payload = {
        "category": "bug",
        "priority": "low",
        "impact_summary": "x",
        "duplicate_likelihood": 0.0,
        "suggested_labels": ["bug"],
        "draft_response": "Hi",
        "privacy_flags": [],
        "reasoning": "r",
        "sources": [],
    }
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content=json.dumps(payload)))]

    with patch("weaverx.llm.litellm.completion", return_value=mock_response) as mock_completion:
        provider = LiteLLMProvider(provider="openai", model="openai/gpt-4o", api_key="sk-test")
        provider.analyze(issue, duplicate_candidates=[], heuristic_duplicate_score=0.0)

    call_kwargs = mock_completion.call_args.kwargs
    assert call_kwargs["api_base"] == "https://example.com/v1"
