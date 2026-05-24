"""Tests for LLM prompt construction."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from weaverx.github import GitHubIssue
from weaverx.llm import LiteLLMProvider, _few_shot_messages


def test_few_shot_messages_include_examples() -> None:
    messages = _few_shot_messages()
    assert len(messages) == 4
    assert messages[0]["role"] == "user"
    assert "reproducibility-environment" in messages[1]["content"]
    assert "dataset-access-licensing" in messages[3]["content"]


def test_litellm_provider_includes_few_shot_turns() -> None:
    issue = GitHubIssue(
        number=1,
        title="Dataset issue",
        body="Need access",
        state="open",
        html_url="https://example.com/1",
        labels=(),
        user="u",
    )
    payload = {
        "category": "dataset-access-licensing",
        "priority": "medium",
        "impact_summary": "Blocked.",
        "duplicate_likelihood": 0.0,
        "suggested_labels": ["dataset"],
        "draft_response": "Hi @u — thanks.",
        "privacy_flags": [],
        "reasoning": "Dataset issue.",
        "sources": [],
    }
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content=json.dumps(payload)))]
    captured: dict[str, object] = {}

    def _capture(**kwargs: object) -> MagicMock:
        captured.update(kwargs)
        return mock_response

    with patch("weaverx.llm.litellm.completion", side_effect=_capture):
        provider = LiteLLMProvider(provider="grok", model="xai/grok-2-latest", api_key="test-key")
        provider.analyze(issue, duplicate_candidates=[], heuristic_duplicate_score=0.0)

    messages = captured["messages"]
    assert isinstance(messages, list)
    assert len(messages) >= 6
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    assert messages[-1]["role"] == "user"
    assert "Triage this GitHub issue" in messages[-1]["content"]
