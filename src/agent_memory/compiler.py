"""Evidence table compiler."""

from __future__ import annotations

import calendar
import re
from datetime import date, timedelta

from agent_memory.schemas import CompiledContext, EvidenceRow, RetrievalHit, RouteResult, Turn


WEEKDAY_BY_NAME = {name.lower(): index for index, name in enumerate(calendar.day_name)}


class EvidenceCompiler:
    """Compiles retrieved raw evidence into an answer-model prompt."""

    def __init__(
        self,
        max_evidence_items: int,
        max_evidence_chars: int,
        answer_style: str = "grounded",
        temporal_grounding: bool = False,
        temporal_hints: bool = False,
    ):
        self._max_evidence_items = max_evidence_items
        self._max_evidence_chars = max_evidence_chars
        self._answer_style = answer_style
        self._temporal_grounding = temporal_grounding
        self._temporal_hints = temporal_hints

    def compile(
        self,
        question: str,
        question_time: str | None,
        route: RouteResult,
        hits: tuple[RetrievalHit, ...],
        evidence_turns: tuple[Turn, ...],
    ) -> CompiledContext:
        hit_by_source_id = {hit.source_id: hit for hit in hits}
        rows: list[EvidenceRow] = []
        used_chars = 0

        for turn in evidence_turns:
            if len(rows) >= self._max_evidence_items:
                break
            hit = hit_by_source_id.get(turn.source_id)
            row = EvidenceRow(
                source_id=turn.source_id,
                session_id=turn.session_id,
                turn_index=turn.turn_index,
                role=turn.role,
                text=turn.text,
                timestamp=turn.timestamp,
                retrieval_rank=hit.rank if hit is not None else None,
                retrieval_score=hit.score if hit is not None else None,
            )
            row_chars = len(_format_row(row))
            if rows and used_chars + row_chars > self._max_evidence_chars:
                break
            rows.append(row)
            used_chars += row_chars

        prompt = _build_prompt(
            question,
            question_time,
            route,
            tuple(rows),
            answer_style=self._answer_style,
            temporal_grounding=self._temporal_grounding,
            temporal_hints=self._temporal_hints,
        )
        return CompiledContext(
            question=question,
            question_time=question_time,
            route=route,
            evidence_rows=tuple(rows),
            prompt=prompt,
            context_chars=len(prompt),
        )


def _build_prompt(
    question: str,
    question_time: str | None,
    route: RouteResult,
    rows: tuple[EvidenceRow, ...],
    answer_style: str,
    temporal_grounding: bool,
    temporal_hints: bool,
) -> str:
    lines = [
        "Answer the question using only the raw evidence table.",
        "If the evidence is insufficient, answer that the information is not available.",
        "Do not use benchmark labels, gold answers, judge output, sample ids, or row indices.",
        "",
        f"Question: {question}",
        f"Question time: {question_time or 'not provided'}",
        f"Information need: {route.information_need}",
        "",
        "Raw evidence table:",
    ]
    if answer_style == "concise":
        lines.insert(
            2,
            "Use the shortest direct answer that is fully supported; avoid explanations unless needed.",
        )
    if temporal_grounding:
        lines.insert(
            3,
            "Resolve relative time expressions against the evidence row time; for example, yesterday means the calendar day before that row time.",
        )
        lines.insert(
            4,
            "For when questions, answer with only the supported absolute date, month, or year when possible; avoid relative phrases like last year, next month, or this month and avoid explaining the calculation.",
        )
    if not rows:
        lines.append("(no evidence retrieved)")
    for row in rows:
        lines.append(_format_row(row))
    if temporal_grounding and temporal_hints:
        hints = _temporal_normalization_hints(rows)
        if hints:
            lines.extend(("", "Temporal normalization hints derived from row timestamps:"))
            lines.extend(hints)
    return "\n".join(lines)


def _format_row(row: EvidenceRow) -> str:
    rank = row.retrieval_rank if row.retrieval_rank is not None else "neighbor"
    score = f"{row.retrieval_score:.4f}" if row.retrieval_score is not None else "n/a"
    timestamp = row.timestamp or "unknown_time"
    return (
        f"- source_id={row.source_id} session={row.session_id} "
        f"turn={row.turn_index} role={row.role} time={timestamp} "
        f"rank={rank} score={score}: {row.text}"
    )


def _temporal_normalization_hints(rows: tuple[EvidenceRow, ...]) -> list[str]:
    hints: list[str] = []
    seen: set[tuple[str, str, str]] = set()
    for row in rows:
        row_date = _parse_date(row.timestamp)
        if row_date is None:
            continue
        for phrase, normalized in _relative_time_values(row.text, row_date):
            key = (row.source_id, phrase, normalized)
            if key in seen:
                continue
            seen.add(key)
            hints.append(
                f"- source_id={row.source_id} row_time={row_date.isoformat()} "
                f'phrase="{phrase}" normalized="{normalized}"'
            )
    return hints


def _relative_time_values(text: str, row_date: date) -> list[tuple[str, str]]:
    lowered = text.lower()
    values: list[tuple[str, str]] = []
    fixed_phrases = (
        ("last year", str(row_date.year - 1)),
        ("this year", str(row_date.year)),
        ("next year", str(row_date.year + 1)),
        ("last month", _shift_month(row_date, -1).strftime("%B %Y")),
        ("this month", row_date.strftime("%B %Y")),
        ("next month", _shift_month(row_date, 1).strftime("%B %Y")),
        ("yesterday", (row_date - timedelta(days=1)).isoformat()),
        ("today", row_date.isoformat()),
        ("tomorrow", (row_date + timedelta(days=1)).isoformat()),
        (
            "last week",
            f"{(row_date - timedelta(days=7)).isoformat()} to "
            f"{(row_date - timedelta(days=1)).isoformat()}",
        ),
        (
            "next week",
            f"{(row_date + timedelta(days=1)).isoformat()} to "
            f"{(row_date + timedelta(days=7)).isoformat()}",
        ),
    )
    for phrase, normalized in fixed_phrases:
        if re.search(rf"\b{re.escape(phrase)}\b", lowered):
            values.append((phrase, normalized))

    for match in re.finditer(
        r"\b(?P<direction>last|next)\s+"
        r"(?P<weekday>monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b",
        lowered,
    ):
        direction = match.group("direction")
        weekday = match.group("weekday")
        values.append(
            (
                f"{direction} {weekday}",
                _relative_weekday(row_date, WEEKDAY_BY_NAME[weekday], direction).isoformat(),
            )
        )
    return values


def _parse_date(value: str | None) -> date | None:
    if value is None:
        return None
    normalized = value.strip()[:10].replace("/", "-")
    try:
        return date.fromisoformat(normalized)
    except ValueError:
        return None


def _shift_month(value: date, delta: int) -> date:
    month_index = value.year * 12 + value.month - 1 + delta
    year = month_index // 12
    month = month_index % 12 + 1
    day = min(value.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def _relative_weekday(value: date, weekday: int, direction: str) -> date:
    if direction == "last":
        days = (value.weekday() - weekday) % 7
        return value - timedelta(days=days or 7)
    days = (weekday - value.weekday()) % 7
    return value + timedelta(days=days or 7)
