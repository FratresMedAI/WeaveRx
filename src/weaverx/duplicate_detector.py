"""Lightweight duplicate issue detection without heavy ML dependencies."""

from __future__ import annotations

import re
from difflib import SequenceMatcher

from weaverx.categories import MED_AI_KEYWORDS
from weaverx.github import GitHubIssue
from weaverx.llm import DuplicateMatch


def normalize_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"```.*?```", " ", text, flags=re.DOTALL)
    text = re.sub(r"`[^`]+`", " ", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"[^a-z0-9\s\-_/]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _keyword_overlap(a: str, b: str) -> float:
    words_a = {w for w in normalize_text(a).split() if w in MED_AI_KEYWORDS}
    words_b = {w for w in normalize_text(b).split() if w in MED_AI_KEYWORDS}
    if not words_a or not words_b:
        return 0.0
    overlap = len(words_a & words_b)
    return overlap / max(len(words_a | words_b), 1)


def similarity_score(source: GitHubIssue, candidate: GitHubIssue) -> float:
    if source.number == candidate.number:
        return 0.0

    title_a = normalize_text(source.title)
    title_b = normalize_text(candidate.title)
    body_a = normalize_text(source.body)[:500]
    body_b = normalize_text(candidate.body)[:500]

    title_ratio = SequenceMatcher(None, title_a, title_b).ratio()
    body_ratio = SequenceMatcher(None, body_a, body_b).ratio() if body_a and body_b else 0.0
    keyword_boost = _keyword_overlap(
        f"{source.title} {source.body}",
        f"{candidate.title} {candidate.body}",
    )

    combined = (0.55 * title_ratio) + (0.30 * body_ratio) + (0.15 * keyword_boost)
    return min(1.0, combined)


def find_duplicates(
    issue: GitHubIssue,
    candidates: list[GitHubIssue],
    *,
    top_k: int = 3,
    min_score: float = 0.25,
) -> list[DuplicateMatch]:
    scored: list[DuplicateMatch] = []
    for candidate in candidates:
        score = similarity_score(issue, candidate)
        if score >= min_score:
            scored.append(
                DuplicateMatch(
                    issue_number=candidate.number,
                    title=candidate.title,
                    score=score,
                    url=candidate.html_url,
                )
            )
    scored.sort(key=lambda m: m.score, reverse=True)
    return scored[:top_k]


def best_duplicate_score(matches: list[DuplicateMatch]) -> float:
    if not matches:
        return 0.0
    return matches[0].score
