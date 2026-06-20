"""Question-text-only routing."""

from __future__ import annotations

import re

from common.schemas import RouteResult


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
    _MONTH_NAME_PATTERN = (
        r"(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|"
        r"jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:t(?:ember)?)?|"
        r"oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)"
    )
    _EXPLICIT_DATE_PATTERNS = (
        rf"\b{_MONTH_NAME_PATTERN}\s+\d{{1,2}}(?:st|nd|rd|th)?(?:,\s*\d{{4}})?\b",
        rf"\b\d{{1,2}}(?:st|nd|rd|th)?\s+{_MONTH_NAME_PATTERN}(?:\s+\d{{4}})?\b",
        rf"\b{_MONTH_NAME_PATTERN}\s+\d{{4}}\b",
        r"\b\d{4}-\d{1,2}-\d{1,2}\b",
        r"\b\d{1,2}/\d{1,2}/(?:\d{2}|\d{4})\b",
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
    _BROAD_LIST_PATTERNS = (
        r"^\s*what\s+(?:[a-z][a-z/-]*\s+){0,4}(?:[a-z][a-z/-]*s|people)\s+(?:has|have|had)\b",
        r"^\s*what\s+(?:activities|events|types|kinds?|symbols|songs?|artists?|bands?)\b",
        r"^\s*where\s+has\b",
        r"\bboth\b",
        r"\bin common\b",
        r"\bdone\s+with\b",
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
    _RECOMMENDATION_PROFILE_PATTERNS = (
        r"^\s*(?:can|could|would)\s+you\s+(?:recommend|suggest)\b",
        r"^\s*(?:please\s+)?(?:recommend|suggest)\b",
        r"\b(?:recommendations?|suggestions?)\s+(?:for|to)\s+me\b",
        r"\bwhat\s+(?:should|would|could)\s+i\s+(?:watch|read|listen to|eat|cook|visit|try|buy|wear|do)\b",
    )
    _ADVICE_PROFILE_PATTERNS = (
        r"\b(?:any|some)\s+(?:tips|advice|ideas|suggestions)\b",
        r"\b(?:tips|advice|ideas|suggestions)\s+(?:for|on|about)\b",
        r"\bcan\s+you\s+(?:give|provide|offer|share)\s+.*\b(?:tips|advice|ideas|suggestions)\b",
        r"\bwhat\s+do\s+you\s+think\b",
        r"\bdo\s+you\s+think\s+(?:i|it|that)\b",
        r"\bshould\s+i\b",
    )

    def __init__(
        self,
        enable_broad_list_patterns: bool = False,
        enable_recommendation_profile_patterns: bool = False,
        enable_advice_profile_patterns: bool = False,
        temporal_priority_over_recent: bool = False,
    ):
        self._enable_broad_list_patterns = enable_broad_list_patterns
        self._enable_recommendation_profile_patterns = (
            enable_recommendation_profile_patterns
        )
        self._enable_advice_profile_patterns = enable_advice_profile_patterns
        self._temporal_priority_over_recent = temporal_priority_over_recent

    def route(self, question: str, question_time: str | None = None) -> RouteResult:
        del question_time
        normalized = question.lower()
        signals: list[str] = []
        temporal_signals = _temporal_route_signals(
            normalized,
            temporal_patterns=self._TEMPORAL_PATTERNS,
            explicit_date_patterns=self._EXPLICIT_DATE_PATTERNS,
        )

        if self._temporal_priority_over_recent and temporal_signals:
            return RouteResult(
                information_need="temporal_lookup",
                signals=temporal_signals,
                retrieval_multiplier=2,
            )
        if _matches_any(normalized, self._RECENT_PATTERNS):
            signals.append("recent_or_current")
            return RouteResult(
                information_need="current_state",
                signals=tuple(signals),
                retrieval_multiplier=2,
            )
        if temporal_signals:
            return RouteResult(
                information_need="temporal_lookup",
                signals=temporal_signals,
                retrieval_multiplier=2,
            )
        if (
            self._enable_recommendation_profile_patterns
            and _matches_any(normalized, self._RECOMMENDATION_PROFILE_PATTERNS)
        ):
            signals.append("profile_or_preference")
            signals.append("personalized_recommendation")
            return RouteResult(
                information_need="profile_preference",
                signals=tuple(signals),
                retrieval_multiplier=2,
            )
        if (
            self._enable_advice_profile_patterns
            and _matches_any(normalized, self._ADVICE_PROFILE_PATTERNS)
        ):
            signals.append("profile_or_preference")
            signals.append("personalized_recommendation")
            signals.append("advice_request")
            return RouteResult(
                information_need="profile_preference",
                signals=tuple(signals),
                retrieval_multiplier=2,
            )
        list_patterns = self._LIST_PATTERNS
        if self._enable_broad_list_patterns:
            list_patterns = (*list_patterns, *self._BROAD_LIST_PATTERNS)
        if _matches_any(normalized, list_patterns):
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


def _temporal_route_signals(
    text: str,
    *,
    temporal_patterns: tuple[str, ...],
    explicit_date_patterns: tuple[str, ...],
) -> tuple[str, ...]:
    signals: list[str] = []
    if _matches_any(text, temporal_patterns):
        signals.append("temporal")
    if _matches_any(text, explicit_date_patterns):
        if "temporal" not in signals:
            signals.append("temporal")
        signals.append("explicit_date")
    return tuple(signals)
