"""Evidence table compiler."""

from __future__ import annotations

from agent_memory.schemas import CompiledContext, EvidenceRow, RetrievalHit, RouteResult, Turn


class EvidenceCompiler:
    """Compiles retrieved raw evidence into an answer-model prompt."""

    def __init__(
        self,
        max_evidence_items: int,
        max_evidence_chars: int,
        answer_style: str = "grounded",
        temporal_grounding: bool = False,
    ):
        self._max_evidence_items = max_evidence_items
        self._max_evidence_chars = max_evidence_chars
        self._answer_style = answer_style
        self._temporal_grounding = temporal_grounding

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
            "For time questions, prefer the supported absolute date, month, or year instead of relative phrases like last year, next month, or this month.",
        )
    if not rows:
        lines.append("(no evidence retrieved)")
    for row in rows:
        lines.append(_format_row(row))
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
