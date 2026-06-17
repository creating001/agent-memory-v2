"""Scoped evidence extraction prompts for two-stage memory QA."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from typing import Any

from common.schemas import AnswerResult, CompiledContext, EvidenceRow


@dataclass(frozen=True)
class ScopedEvidenceRun:
    """Trace for an optional scoped-evidence answer path."""

    enabled: bool
    applied: bool
    information_needs: tuple[str, ...]
    max_rows: int
    max_row_chars: int
    extraction_prompt_chars: int = 0
    answer_prompt_chars: int = 0
    evidence_json_chars: int = 0
    extraction: dict[str, Any] | None = None
    answer: dict[str, Any] | None = None
    extraction_cache: dict[str, int] | None = None
    answer_cache: dict[str, int] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def disabled_scoped_evidence_run(
    *,
    enabled: bool,
    information_needs: tuple[str, ...],
    max_rows: int,
    max_row_chars: int,
) -> ScopedEvidenceRun:
    return ScopedEvidenceRun(
        enabled=enabled,
        applied=False,
        information_needs=information_needs,
        max_rows=max_rows,
        max_row_chars=max_row_chars,
    )


def should_apply_scoped_evidence(
    context: CompiledContext,
    information_needs: tuple[str, ...],
) -> bool:
    return context.route.information_need in set(information_needs)


def build_scoped_evidence_extraction_prompt(
    context: CompiledContext,
    *,
    max_rows: int,
    max_row_chars: int,
) -> str:
    """Build a compact evidence extraction prompt from visible context rows."""

    lines = [
        "Extract scoped evidence for a long-term memory question.",
        "Use only the Memory Context rows below. Do not answer from outside knowledge.",
        "Treat every information source not shown in the question or Memory Context as unavailable.",
        "",
        "User Question:",
        _question_block(context),
        "",
        f"Information need: {context.route.information_need}",
        "",
        "Memory Context:",
    ]
    selected_rows = context.evidence_rows[: max(0, max_rows)]
    if not selected_rows:
        lines.append("(no memory rows)")
    for index, row in enumerate(selected_rows, start=1):
        lines.extend(_format_extraction_row(index, row, max_row_chars=max_row_chars))
    lines.extend(
        [
            "",
            "Extraction rules:",
            "1. Identify the exact target entity, action, object, owner/person, time range, and requested answer slot before extracting evidence.",
            "2. Include every row that may affect the answer; mark close but wrong rows as excluded instead of silently dropping them.",
            "3. Preserve exact names, dates, numbers, units, places, titles, and short quotes from the rows.",
            "4. For count, list, sum, difference, duration, comparison, or order questions, extract distinct operands or events before calculating.",
            "5. Split multiple in-scope operands in one row into separate included_items when needed, such as two purchases with two prices.",
            "6. Merge duplicate mentions under the same canonical_item; do not count a repeated mention twice.",
            "7. Do not count assistant suggestions, hypotheticals, plans, or examples unless the question asks about suggestions/plans or the user later confirms them.",
            "8. For temporal questions, distinguish mention_date from event_time; prefer a specific event date or relative phrase in the row text over the row date.",
            "9. If one row gives a broad time and another row gives a more specific time for the same event, keep both but make the more specific time the included value.",
            "10. If required evidence is missing, set sufficient=false and name the missing target or operand.",
            "",
            "Return ONLY valid JSON with this schema:",
            "{",
            '  "sufficient": true,',
            '  "answer_type": "fact|count|list|sum|duration|date|order|preference|unknown",',
            '  "target_scope": "short description of the requested scope",',
            '  "included_items": [',
            '    {"memory": "Memory 1", "canonical_item": "distinct item/event/operand", "mention_date": "row date or empty", "event_time": "event date/time/duration or empty", "value": "answer value or operand", "quote": "short row quote", "reason": "why it is in scope"}',
            "  ],",
            '  "excluded_items": [',
            '    {"memory": "Memory 2", "canonical_item": "excluded item", "reason": "duplicate|out_of_scope|wrong_time_range|assistant_suggestion|not_confirmed|less_specific|irrelevant"}',
            "  ],",
            '  "calculation": "arithmetic, ordering rule, or selection rule; empty if none",',
            '  "missing_info": "missing required evidence, or empty"',
            "}",
        ]
    )
    return "\n".join(lines)


def build_scoped_evidence_answer_prompt(
    context: CompiledContext,
    evidence_json: str,
) -> str:
    """Build a second-stage answer prompt that consumes only extracted evidence."""

    return "\n".join(
        [
            "Answer the user's question using only the extracted evidence JSON.",
            "Do not use outside knowledge or any memory row that is not represented in the JSON.",
            "",
            "User Question:",
            _question_block(context),
            "",
            f"Information need: {context.route.information_need}",
            "",
            "Extracted Evidence JSON:",
            evidence_json.strip() or "{}",
            "",
            "Answer rules:",
            "1. If sufficient is false, answer that the provided information is not enough and name the missing item only if useful.",
            "2. Use included_items only; excluded_items can explain why something is not counted but must not appear as support.",
            "3. Count each distinct canonical_item once unless the item value explicitly names multiple distinct in-scope items.",
            "4. For sums, differences, durations, or counts, verify the calculation and preserve the requested unit.",
            "5. For date/order questions, use event_time when present; use mention_date only when the event happened on that date or no more specific event_time is available.",
            "6. For list questions, preserve all distinct included item names rather than collapsing them into a broad category.",
            "7. If the question asks what, which, who, where, or name, answer with the requested names/items/places, not just the number of included_items.",
            "8. Only answer with a bare count when the question explicitly asks how many, number of, or count.",
            "9. Match the requested answer slot exactly: place, person, count, date, duration, list, state, or fact.",
            "10. Keep the final answer concise but complete enough to avoid a partial answer.",
            "",
            "Return ONLY valid JSON:",
            "{",
            '  "reasoning": "one short sentence",',
            '  "answer": "concise answer"',
            "}",
        ]
    )


def scoped_evidence_answer_result(
    *,
    extraction_result: AnswerResult,
    final_result: AnswerResult,
) -> AnswerResult:
    return AnswerResult(
        answer=final_result.answer,
        model=final_result.model,
        token_usage=extraction_result.token_usage + final_result.token_usage,
        raw_response=final_result.raw_response,
    )


def extract_evidence_json_text(text: str) -> str:
    value = _extract_json_object(text)
    if value is None:
        return text.strip()
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def parsed_evidence_json(text: str) -> dict[str, Any] | None:
    return _extract_json_object(text)


def _question_block(context: CompiledContext) -> str:
    if context.question_time:
        return f"Current Date: {context.question_time}\nQuestion: {context.question}"
    return context.question


def _format_extraction_row(
    index: int,
    row: EvidenceRow,
    *,
    max_row_chars: int,
) -> list[str]:
    return [
        f"### Memory {index}",
        f"Source: {row.source_id}",
        f"Session: {row.session_id}",
        f"Turn: {row.turn_index}",
        f"Date: {row.timestamp or ''}",
        f"Role: {row.role}",
        "Content:",
        _truncate(_single_line(row.text), max_row_chars),
    ]


def _truncate(text: str, max_chars: int) -> str:
    limit = max(80, int(max_chars))
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def _single_line(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _extract_json_object(text: str) -> dict[str, Any] | None:
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start < 0 or end <= start:
            return None
        try:
            value = json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            return None
    return value if isinstance(value, dict) else None
