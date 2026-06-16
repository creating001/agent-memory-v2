"""Selective answer repair for clean memory QA.

This module uses only prediction-time artifacts: the question, route, retrieved
memory context, and the draft answer/JSON. It must never read labels, judge
outputs, benchmark metadata, sample ids, or test feedback.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any

from common.schemas import AnswerResult, CompiledContext
from memory.finalize import extract_json_object, raw_response_content


_INSUFFICIENT_ANSWER = re.compile(
    r"\b(not enough|insufficient|cannot determine|can't determine|not available|"
    r"unknown|do not know|don't know|not provided|not mentioned|not specified|"
    r"no information)\b",
    re.IGNORECASE,
)
_COLLECTION_QUESTION = re.compile(
    r"\b(?:what|which)\s+(?:items?|events?|activities|places?|people|persons|"
    r"books?|songs?|movies?|artists?|bands?|exercises?|causes?|foods?|meals?|"
    r"classes?|workshops?|projects?|purchases?|hobbies|sports?|games?|"
    r"restaurants?|stores?|services?|organizations?|groups?|symbols?|topics?|"
    r"subjects?|courses?|awards?|trips?|visits?|tools?|apps?|devices?)\b|"
    r"\bwhat\s+kind(?:s)?\s+of\b|"
    r"\bwhat\s+.+\b(?:has|have|had)\s+.+\b(?:done|bought|painted|visited|"
    r"attended|participated|read|seen|watched|tried|used|owned|made|created|"
    r"ordered|eaten|played|joined|taken)\b",
    re.IGNORECASE,
)
_COUNT_QUESTION = re.compile(r"\b(?:how many|number of|count of)\b", re.IGNORECASE)
_NUMERIC_ANSWER = re.compile(r"\b\d+(?:\.\d+)?\b")
_ITEM_SEPARATOR = re.compile(r"\s*(?:,|;|\band\b|\n|\|)\s*", re.IGNORECASE)


@dataclass(frozen=True)
class AnswerRepair:
    """Traceable result for optional LLM answer repair."""

    answer: AnswerResult
    enabled: bool
    triggered: bool
    applied: bool
    reasons: tuple[str, ...]
    before: str
    after: str
    decision: str
    reason: str
    prompt_context_chars: int = 0
    response: AnswerResult | None = None

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["answer"] = self.answer.to_dict()
        result["response"] = self.response.to_dict() if self.response else None
        return result


def maybe_repair_answer(
    *,
    answerer: Any | None,
    compiled: CompiledContext,
    draft: AnswerResult,
    enabled: bool,
    information_needs: tuple[str, ...],
    enable_uncertain_trigger: bool,
    enable_short_list_trigger: bool,
    enable_temporal_conflict_trigger: bool,
    enable_profile_preference_trigger: bool,
    uncertain_min_support_items: int,
    max_context_chars: int,
    max_row_text_chars: int,
) -> AnswerRepair:
    """Run a second LLM pass only when generic runtime signals show risk."""

    if not enabled:
        return _noop(draft, enabled=False, reason="disabled")
    if answerer is None:
        return _noop(draft, enabled=True, reason="no_repair_answerer")
    if information_needs and compiled.route.information_need not in information_needs:
        return _noop(draft, enabled=True, reason="information_need_not_enabled")

    reasons = repair_trigger_reasons(
        question=compiled.question,
        route_information_need=compiled.route.information_need,
        draft_answer=draft.answer,
        raw_response=draft.raw_response,
        enable_uncertain_trigger=enable_uncertain_trigger,
        enable_short_list_trigger=enable_short_list_trigger,
        enable_temporal_conflict_trigger=enable_temporal_conflict_trigger,
        enable_profile_preference_trigger=enable_profile_preference_trigger,
        uncertain_min_support_items=uncertain_min_support_items,
    )
    if not reasons:
        return _noop(draft, enabled=True, reason="no_trigger")

    prompt, prompt_context_chars = build_repair_prompt(
        compiled=compiled,
        draft=draft,
        reasons=reasons,
        max_context_chars=max_context_chars,
        max_row_text_chars=max_row_text_chars,
    )
    repair_context = CompiledContext(
        question=compiled.question,
        question_time=compiled.question_time,
        route=compiled.route,
        evidence_rows=compiled.evidence_rows,
        prompt=prompt,
        context_chars=prompt_context_chars,
        memory_records=compiled.memory_records,
    )
    response = answerer.answer(repair_context)
    decision = _repair_decision(response.raw_response)
    revised_answer = response.answer.strip()

    applied = False
    after = draft.answer
    if decision == "revise" and revised_answer:
        after = revised_answer
        applied = after != draft.answer
    elif decision not in {"keep", "revise"} and revised_answer:
        after = revised_answer
        applied = after != draft.answer

    final_token_usage = draft.token_usage + response.token_usage
    final = AnswerResult(
        answer=after,
        model=response.model if applied else draft.model,
        token_usage=final_token_usage,
        raw_response=response.raw_response if applied else draft.raw_response,
    )
    return AnswerRepair(
        answer=final,
        enabled=True,
        triggered=True,
        applied=applied,
        reasons=reasons,
        before=draft.answer,
        after=after,
        decision=decision or "unknown",
        reason="repair_called",
        prompt_context_chars=prompt_context_chars,
        response=response,
    )


def repair_trigger_reasons(
    *,
    question: str,
    route_information_need: str,
    draft_answer: str,
    raw_response: str | None,
    enable_uncertain_trigger: bool,
    enable_short_list_trigger: bool,
    enable_temporal_conflict_trigger: bool,
    enable_profile_preference_trigger: bool = False,
    uncertain_min_support_items: int = 0,
) -> tuple[str, ...]:
    payload = _draft_payload(raw_response)
    reasons: list[str] = []

    if (
        enable_profile_preference_trigger
        and route_information_need == "profile_preference"
    ):
        reasons.append("profile_preference_review")

    if enable_uncertain_trigger:
        answer_type = str(payload.get("answer_type") or "").strip().lower()
        missing = str(payload.get("missing") or "").strip()
        has_uncertain_signal = (
            _INSUFFICIENT_ANSWER.search(draft_answer or "")
            or payload.get("sufficient") is False
            or answer_type == "unknown"
            or bool(missing)
        )
        if has_uncertain_signal and _support_item_count(payload) >= max(
            0, int(uncertain_min_support_items)
        ):
            reasons.append("uncertain_or_missing")

    if enable_short_list_trigger and _looks_like_short_collection_answer(
        question=question,
        route_information_need=route_information_need,
        draft_answer=draft_answer,
        payload=payload,
    ):
        reasons.append("short_collection_answer")

    if enable_temporal_conflict_trigger and route_information_need == "temporal_lookup":
        answer_type = str(payload.get("answer_type") or "").strip().lower()
        if answer_type in {"fact", "unknown", "list", "count", "preference"}:
            reasons.append("temporal_answer_type_mismatch")
        values = _support_values(payload)
        if len(values) > 1:
            reasons.append("temporal_multiple_support_values")

    return tuple(dict.fromkeys(reasons))


def build_repair_prompt(
    *,
    compiled: CompiledContext,
    draft: AnswerResult,
    reasons: tuple[str, ...],
    max_context_chars: int,
    max_row_text_chars: int,
) -> tuple[str, int]:
    draft_json = raw_response_content(draft.raw_response) or draft.answer
    memory_context, context_chars = _repair_memory_context(
        compiled,
        max_context_chars=max_context_chars,
        max_row_text_chars=max_row_text_chars,
    )
    question_time = compiled.question_time or ""
    reason_text = ", ".join(reasons)

    prompt = "\n".join(
        [
            "You are a clean memory-QA answer verifier and repairer.",
            "Use only the provided Memory Context and Draft Answer artifacts.",
            "",
            "Question:",
            compiled.question,
            "",
            "Question Time:",
            question_time,
            "",
            "Information Need:",
            compiled.route.information_need,
            "",
            "Repair Trigger Reasons:",
            reason_text,
            "",
            "Draft Answer:",
            draft.answer,
            "",
            "Draft Answer JSON:",
            draft_json,
            "",
            "Memory Context:",
            memory_context,
            "",
            "Rules:",
            "1. Prefer decision=keep when the draft answer is directly supported and complete enough for the question.",
            "2. Use decision=revise only when Memory Context clearly supports a better answer or the draft refusal is contradicted by available evidence.",
            "3. Do not use labels, reference answers, judge feedback, benchmark categories, sample ids, or assumptions outside Memory Context.",
            "4. For list or count questions, include all distinct in-scope values supported by Memory Context; merge duplicates and do not narrow a supported broad answer unless evidence clearly excludes it.",
            "5. For temporal questions, separate Memory Date from event time; answer the event/state time requested by the question.",
            "6. For current/latest questions, compare older and newer directly relevant evidence before revising.",
            "7. If evidence remains insufficient, keep or revise to a concise insufficient-information answer.",
            *_profile_preference_repair_rules(compiled),
            "Return only valid JSON.",
            "",
            "Output JSON:",
            "{",
            '  "decision": "keep|revise",',
            '  "reason": "one short evidence-based sentence",',
            '  "answer": "final concise answer"',
            "}",
        ]
    )
    return prompt, context_chars


def _profile_preference_repair_rules(compiled: CompiledContext) -> list[str]:
    if compiled.route.information_need != "profile_preference":
        return []
    return [
        "8. For preference, advice, or recommendation questions, extract user-specific anchors from Memory Context: preferences, dislikes, constraints, owned tools/resources, current setup, prior successful experiences, current problems, and stated goals.",
        "9. If the draft refused but Memory Context has relevant anchors, revise to a tailored answer using those anchors instead of generic advice.",
        "10. If the exact requested named option is not in Memory Context, answer with the type, criteria, or constraints the user would likely prefer; do not invent unsupported specific names.",
        "11. This no-new-names rule applies even when you know plausible real-world shows, conferences, hotels, products, publications, venues, or events; use only names present in Memory Context.",
        "12. The final answer must not contain a proper noun, title, organization, venue, platform, publication, conference, hotel, product, show, movie, restaurant, or event name unless that exact name appears verbatim in Memory Context.",
        "13. If no exact named option is present, answer with preference type, selection criteria, or constraints only.",
        "14. Include the key personalized constraint or reason in the final answer when needed for the answer to satisfy the request.",
    ]


def _noop(draft: AnswerResult, *, enabled: bool, reason: str) -> AnswerRepair:
    return AnswerRepair(
        answer=draft,
        enabled=enabled,
        triggered=False,
        applied=False,
        reasons=(),
        before=draft.answer,
        after=draft.answer,
        decision="keep",
        reason=reason,
    )


def _draft_payload(raw_response: str | None) -> dict[str, Any]:
    content = raw_response_content(raw_response)
    if not content:
        return {}
    return extract_json_object(content) or {}


def _repair_decision(raw_response: str | None) -> str:
    payload = _draft_payload(raw_response)
    return str(payload.get("decision") or "").strip().lower()


def _looks_like_short_collection_answer(
    *,
    question: str,
    route_information_need: str,
    draft_answer: str,
    payload: dict[str, Any],
) -> bool:
    if route_information_need not in {"fact_lookup", "list_count"}:
        return False
    lowered_question = question.lower()
    answer_type = str(payload.get("answer_type") or "").strip().lower()
    if answer_type not in {"", "list", "count", "fact"}:
        return False
    if not _COLLECTION_QUESTION.search(lowered_question):
        return False
    if _INSUFFICIENT_ANSWER.search(draft_answer or ""):
        return False
    answer = (draft_answer or "").strip()
    if not answer:
        return False
    if _COUNT_QUESTION.search(lowered_question) and _NUMERIC_ANSWER.search(answer):
        return False
    if len(answer.split()) > 10:
        return False
    return len(_answer_items(answer)) <= 2


def _answer_items(answer: str) -> tuple[str, ...]:
    normalized = answer.strip().strip("[](){}")
    if not normalized:
        return ()
    parts = [
        part.strip().strip("\"'")
        for part in _ITEM_SEPARATOR.split(normalized)
        if part.strip().strip("\"'")
    ]
    return tuple(parts or (normalized,))


def _support_values(payload: dict[str, Any]) -> set[str]:
    values: set[str] = set()
    report = payload.get("evidence_report")
    if not isinstance(report, list):
        return values
    for item in report:
        if not isinstance(item, dict):
            continue
        if str(item.get("status") or "").strip().lower() != "support":
            continue
        value = str(item.get("event_time") or item.get("value") or "").strip()
        if value:
            values.add(value)
    return values


def _support_item_count(payload: dict[str, Any]) -> int:
    report = payload.get("evidence_report")
    if not isinstance(report, list):
        return 0
    return sum(
        1
        for item in report
        if isinstance(item, dict)
        and str(item.get("status") or "").strip().lower() == "support"
    )


def _repair_memory_context(
    compiled: CompiledContext,
    *,
    max_context_chars: int,
    max_row_text_chars: int,
) -> tuple[str, int]:
    limit = max(0, int(max_context_chars))
    row_limit = max(0, int(max_row_text_chars))
    lines: list[str] = []
    total = 0
    for index, row in enumerate(compiled.evidence_rows, start=1):
        text = row.text
        if row_limit and len(text) > row_limit:
            text = (text[: max(0, row_limit - 3)].rstrip() + "...")[:row_limit]
        parts = [
            f"Memory {index}:",
            f"Date: {row.timestamp or ''}",
            f"Speaker: {row.role}",
            f"Text: {text}",
        ]
        row_text = "\n".join(parts)
        projected = total + len(row_text) + (2 if lines else 0)
        if limit and lines and projected > limit:
            break
        if limit and not lines and len(row_text) > limit:
            row_text = (row_text[: max(0, limit - 3)].rstrip() + "...")[:limit]
            projected = len(row_text)
        lines.append(row_text)
        total = projected
    return "\n\n".join(lines), total
