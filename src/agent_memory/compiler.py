"""Evidence table compiler."""

from __future__ import annotations

import calendar
import re
from datetime import date, timedelta

from agent_memory.schemas import CompiledContext, EvidenceRow, RetrievalHit, RouteResult, Turn


WEEKDAY_BY_NAME = {name.lower(): index for index, name in enumerate(calendar.day_name)}
TOKEN_PATTERN = re.compile(r"[\w]+", re.UNICODE)
QUESTION_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "at",
    "be",
    "been",
    "being",
    "could",
    "did",
    "do",
    "does",
    "for",
    "from",
    "had",
    "has",
    "have",
    "her",
    "his",
    "how",
    "i",
    "in",
    "is",
    "it",
    "me",
    "my",
    "of",
    "on",
    "or",
    "our",
    "she",
    "should",
    "the",
    "their",
    "they",
    "to",
    "was",
    "were",
    "what",
    "when",
    "where",
    "which",
    "who",
    "whom",
    "why",
    "would",
    "you",
    "your",
}


class EvidenceCompiler:
    """Compiles retrieved raw evidence into an answer-model prompt."""

    def __init__(
        self,
        max_evidence_items: int,
        max_evidence_chars: int,
        answer_style: str = "grounded",
        temporal_grounding: bool = False,
        temporal_hints: bool = False,
        evidence_order: str = "retrieval",
        row_text_mode: str = "full",
        max_row_text_chars: int = 0,
    ):
        self._max_evidence_items = max_evidence_items
        self._max_evidence_chars = max_evidence_chars
        self._answer_style = answer_style
        self._temporal_grounding = temporal_grounding
        self._temporal_hints = temporal_hints
        if evidence_order not in {"retrieval", "question_overlap"}:
            raise ValueError(f"Unsupported evidence_order: {evidence_order}")
        self._evidence_order = evidence_order
        if row_text_mode not in {"full", "query_snippet"}:
            raise ValueError(f"Unsupported row_text_mode: {row_text_mode}")
        self._row_text_mode = row_text_mode
        self._max_row_text_chars = max_row_text_chars or 800

    def compile(
        self,
        question: str,
        question_time: str | None,
        route: RouteResult,
        hits: tuple[RetrievalHit, ...],
        evidence_turns: tuple[Turn, ...],
    ) -> CompiledContext:
        hit_by_source_id = {hit.source_id: hit for hit in hits}
        candidates: list[EvidenceRow] = []
        for turn in evidence_turns:
            hit = hit_by_source_id.get(turn.source_id)
            candidates.append(
                EvidenceRow(
                    source_id=turn.source_id,
                    session_id=turn.session_id,
                    turn_index=turn.turn_index,
                    role=turn.role,
                    text=turn.text,
                    timestamp=turn.timestamp,
                    retrieval_rank=hit.rank if hit is not None else None,
                    retrieval_score=hit.score if hit is not None else None,
                )
            )

        ordered_candidates = _order_rows(
            tuple(candidates),
            question=question,
            route=route,
            evidence_order=self._evidence_order,
        )
        rows: list[EvidenceRow] = []
        used_chars = 0

        for row in ordered_candidates:
            if len(rows) >= self._max_evidence_items:
                break
            row_chars = len(
                _format_row(
                    row,
                    question=question,
                    row_text_mode=self._row_text_mode,
                    max_row_text_chars=self._max_row_text_chars,
                )
            )
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
            row_text_mode=self._row_text_mode,
            max_row_text_chars=self._max_row_text_chars,
        )
        return CompiledContext(
            question=question,
            question_time=question_time,
            route=route,
            evidence_rows=tuple(rows),
            prompt=prompt,
            context_chars=len(prompt),
        )


def _order_rows(
    rows: tuple[EvidenceRow, ...],
    question: str,
    route: RouteResult,
    evidence_order: str,
) -> tuple[EvidenceRow, ...]:
    if evidence_order == "retrieval":
        return rows
    if evidence_order != "question_overlap":
        raise ValueError(f"Unsupported evidence_order: {evidence_order}")

    question_terms = _content_terms(question)
    return tuple(
        row
        for _, row in sorted(
            enumerate(rows),
            key=lambda item: _question_overlap_key(
                index=item[0],
                row=item[1],
                question_terms=question_terms,
                route=route,
            ),
        )
    )


def _question_overlap_key(
    index: int,
    row: EvidenceRow,
    question_terms: frozenset[str],
    route: RouteResult,
) -> tuple[float, int, int, str, str, int, int]:
    row_terms = _content_terms(row.text)
    overlap = len(question_terms.intersection(row_terms))
    direct_hit_bonus = 1.0 if row.retrieval_rank is not None else 0.0
    temporal_bonus = (
        0.25
        if (
            route.information_need in {"current_state", "temporal_lookup"}
            and row.timestamp
        )
        else 0.0
    )
    score = overlap + direct_hit_bonus + temporal_bonus
    missing_rank = 1 if row.retrieval_rank is None else 0
    rank = row.retrieval_rank if row.retrieval_rank is not None else 1_000_000
    time_key = _timestamp_sort_key(row.timestamp, route)
    return (-score, missing_rank, rank, time_key, row.session_id, row.turn_index, index)


def _content_terms(text: str) -> frozenset[str]:
    terms = [
        match.group(0).lower()
        for match in TOKEN_PATTERN.finditer(text)
        if match.group(0).lower() not in QUESTION_STOPWORDS
    ]
    return frozenset(terms)


def _timestamp_sort_key(timestamp: str | None, route: RouteResult) -> str:
    normalized = timestamp or ""
    if route.information_need == "current_state":
        return _invert_sortable_text(normalized)
    return normalized


def _invert_sortable_text(value: str) -> str:
    return "".join(chr(0x10FFFF - ord(char)) for char in value)


def _build_prompt(
    question: str,
    question_time: str | None,
    route: RouteResult,
    rows: tuple[EvidenceRow, ...],
    answer_style: str,
    temporal_grounding: bool,
    temporal_hints: bool,
    row_text_mode: str,
    max_row_text_chars: int,
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
        lines.append(
            _format_row(
                row,
                question=question,
                row_text_mode=row_text_mode,
                max_row_text_chars=max_row_text_chars,
            )
        )
    if temporal_grounding and temporal_hints:
        hints = _temporal_normalization_hints(rows)
        if hints:
            lines.extend(("", "Temporal normalization hints derived from row timestamps:"))
            lines.extend(hints)
    return "\n".join(lines)


def _format_row(
    row: EvidenceRow,
    question: str,
    row_text_mode: str,
    max_row_text_chars: int,
) -> str:
    rank = row.retrieval_rank if row.retrieval_rank is not None else "neighbor"
    score = f"{row.retrieval_score:.4f}" if row.retrieval_score is not None else "n/a"
    timestamp = row.timestamp or "unknown_time"
    text = _row_prompt_text(
        row.text,
        question=question,
        row_text_mode=row_text_mode,
        max_row_text_chars=max_row_text_chars,
    )
    return (
        f"- source_id={row.source_id} session={row.session_id} "
        f"turn={row.turn_index} role={row.role} time={timestamp} "
        f"rank={rank} score={score}: {text}"
    )


def _row_prompt_text(
    text: str,
    question: str,
    row_text_mode: str,
    max_row_text_chars: int,
) -> str:
    if row_text_mode == "full":
        return text
    if row_text_mode != "query_snippet":
        raise ValueError(f"Unsupported row_text_mode: {row_text_mode}")
    return _query_snippet(text, question, max_row_text_chars)


def _query_snippet(text: str, question: str, max_chars: int) -> str:
    if max_chars <= 0 or len(text) <= max_chars:
        return text

    terms = _content_terms(question)
    if not terms:
        return _truncate_text(text, max_chars)

    lower_text = text.lower()
    positions: list[int] = []
    for term in terms:
        pattern = re.compile(rf"\b{re.escape(term)}\b")
        positions.extend(match.start() for match in pattern.finditer(lower_text))
    if not positions:
        return _truncate_text(text, max_chars)

    max_start = max(0, len(text) - max_chars)
    candidate_starts = {
        min(max(0, position - max_chars // 3), max_start) for position in positions
    }
    best_start = min(
        candidate_starts,
        key=lambda start: (
            -sum(1 for position in positions if start <= position < start + max_chars),
            start,
        ),
    )
    snippet = text[best_start : best_start + max_chars].strip()
    prefix = "... " if best_start > 0 else ""
    suffix = " ..." if best_start + max_chars < len(text) else ""
    return f"{prefix}{snippet}{suffix}"


def _truncate_text(text: str, max_chars: int) -> str:
    if max_chars <= 0 or len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + " ..."


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
