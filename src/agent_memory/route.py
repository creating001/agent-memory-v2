"""Question-text-only routing."""

from __future__ import annotations

import re

from agent_memory.schemas import RouteResult


class QuestionRouter:
    """Routes by generic information need, never by benchmark labels."""

    _TEMPORAL_PATTERNS = (
        r"^\s*when\b",
        r"\bwhat\s+(?:date|time)\b",
        r"\bhow long\b",
        r"\bduration\b",
        r"\bdays?\b",
        r"\bweeks?\b",
        r"\bmonths?\b",
        r"\byears?\b",
        r"什么时候",
        r"多久",
        r"多长时间",
    )
    _RECENT_PATTERNS = (
        r"\bcurrent\b",
        r"\blatest\b",
        r"\bmost recent\b",
        r"\bnow\b",
        r"\btoday\b",
        r"最近",
        r"现在",
        r"目前",
    )
    _LIST_PATTERNS = (
        r"\blist\b",
        r"\ball\b",
        r"\bhow many\b",
        r"\bcount\b",
        r"\bwhich\b",
        r"哪些",
        r"多少",
        r"列出",
    )
    _PROFILE_PATTERNS = (
        r"\bfavorite\b",
        r"\bprefer\b",
        r"\blike\b",
        r"\bdislike\b",
        r"\bpreference\b",
        r"喜欢",
        r"偏好",
    )

    def route(self, question: str, question_time: str | None = None) -> RouteResult:
        del question_time
        normalized = question.lower()
        signals: list[str] = []

        if _matches_any(normalized, self._RECENT_PATTERNS):
            signals.append("recent_or_current")
            return RouteResult(
                information_need="current_state",
                signals=tuple(signals),
                retrieval_multiplier=2,
            )
        if _matches_any(normalized, self._TEMPORAL_PATTERNS):
            signals.append("temporal")
            return RouteResult(
                information_need="temporal_lookup",
                signals=tuple(signals),
                retrieval_multiplier=2,
            )
        if _matches_any(normalized, self._LIST_PATTERNS):
            signals.append("list_or_count")
            return RouteResult(
                information_need="list_count",
                signals=tuple(signals),
                retrieval_multiplier=3,
            )
        if _matches_any(normalized, self._PROFILE_PATTERNS):
            signals.append("profile_or_preference")
            return RouteResult(
                information_need="profile_preference",
                signals=tuple(signals),
                retrieval_multiplier=2,
            )

        return RouteResult(
            information_need="fact_lookup",
            signals=tuple(signals),
            retrieval_multiplier=1,
        )


def _matches_any(text: str, patterns: tuple[str, ...]) -> bool:
    return any(re.search(pattern, text) for pattern in patterns)
