"""Evidence table compiler."""

from __future__ import annotations

import calendar
import re
from collections.abc import Mapping
from datetime import date, timedelta
from typing import Any

from memory.build import MemoryRecord
from common.schemas import CompiledContext, EvidenceRow, RetrievalHit, RouteResult, Turn


WEEKDAY_BY_NAME = {name.lower(): index for index, name in enumerate(calendar.day_name)}
NUMBER_WORDS = {
    "a": 1,
    "an": 1,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
}
MAX_RELATIVE_TIME_SPANS = {
    "day": 36500,
    "week": 5200,
    "month": 1200,
    "year": 100,
}
TOKEN_PATTERN = re.compile(r"[\w]+", re.UNICODE)
SUPPORTED_INFORMATION_NEEDS = {
    "current_state",
    "fact_lookup",
    "list_count",
    "profile_preference",
    "temporal_lookup",
}
ROUTE_OVERRIDE_KEYS = {
    "evidence_row_labels",
    "final_answer_checklist",
    "max_memory_records",
    "max_evidence_chars",
    "max_evidence_items",
    "max_row_text_chars",
    "row_text_mode",
    "structured_guide_include_memory",
    "structured_guide_include_rows",
    "structured_guide_max_rows",
}
SUPPORTED_PROMPT_MODES = {"default", "external_naive", "raw_context_only"}
DEFAULT_STRUCTURED_ANSWER_CONTRACT_NEEDS = ("list_count", "temporal_lookup")
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
        temporal_workpad: bool = False,
        temporal_text_normalization: bool = False,
        temporal_workpad_scope: str = "route",
        temporal_workpad_max_rows: int = 10,
        temporal_workpad_max_pairs: int = 12,
        structured_guide: bool = False,
        structured_guide_max_rows: int = 12,
        structured_guide_include_rows: bool = True,
        structured_guide_include_memory: bool = True,
        structured_guide_disabled_signals: tuple[str, ...] = (),
        structured_answer_contract: bool = False,
        structured_answer_contract_information_needs: tuple[str, ...] = (
            DEFAULT_STRUCTURED_ANSWER_CONTRACT_NEEDS
        ),
        structured_answer_contract_max_items: int = 10,
        evidence_order: str = "retrieval",
        memory_order: str = "retrieval",
        memory_layout: str = "flat",
        row_text_mode: str = "full",
        max_row_text_chars: int = 0,
        route_guidance: bool = False,
        evidence_row_labels: bool = False,
        final_answer_checklist: bool = False,
        max_memory_records: int = 12,
        prompt_mode: str = "default",
        route_overrides: Mapping[str, Mapping[str, Any]] | None = None,
    ):
        self._max_evidence_items = max_evidence_items
        self._max_evidence_chars = max_evidence_chars
        self._answer_style = answer_style
        self._temporal_grounding = temporal_grounding
        self._temporal_hints = temporal_hints
        self._temporal_workpad = temporal_workpad
        self._temporal_text_normalization = temporal_text_normalization
        if temporal_workpad_scope not in {"route", "calculation_route"}:
            raise ValueError(
                f"Unsupported temporal_workpad_scope: {temporal_workpad_scope}"
            )
        self._temporal_workpad_scope = temporal_workpad_scope
        self._temporal_workpad_max_rows = max(1, temporal_workpad_max_rows)
        self._temporal_workpad_max_pairs = max(0, temporal_workpad_max_pairs)
        self._structured_guide = structured_guide
        self._structured_guide_max_rows = max(1, structured_guide_max_rows)
        self._structured_guide_include_rows = structured_guide_include_rows
        self._structured_guide_include_memory = structured_guide_include_memory
        self._structured_guide_disabled_signals = tuple(
            str(signal) for signal in structured_guide_disabled_signals
        )
        self._structured_answer_contract = structured_answer_contract
        self._structured_answer_contract_information_needs = _validate_information_needs(
            structured_answer_contract_information_needs,
            field_name="structured_answer_contract_information_needs",
        )
        self._structured_answer_contract_max_items = max(
            1, int(structured_answer_contract_max_items)
        )
        if evidence_order not in {"retrieval", "question_overlap"}:
            raise ValueError(f"Unsupported evidence_order: {evidence_order}")
        self._evidence_order = evidence_order
        if memory_order not in {"retrieval", "question_overlap"}:
            raise ValueError(f"Unsupported memory_order: {memory_order}")
        self._memory_order = memory_order
        if memory_layout not in {"flat", "typed_sections"}:
            raise ValueError(f"Unsupported memory_layout: {memory_layout}")
        self._memory_layout = memory_layout
        if row_text_mode not in {"full", "query_snippet", "role_query_snippet"}:
            raise ValueError(f"Unsupported row_text_mode: {row_text_mode}")
        self._row_text_mode = row_text_mode
        self._max_row_text_chars = max_row_text_chars or 800
        self._route_guidance = route_guidance
        self._evidence_row_labels = evidence_row_labels
        self._final_answer_checklist = final_answer_checklist
        self._max_memory_records = max(0, max_memory_records)
        if prompt_mode not in SUPPORTED_PROMPT_MODES:
            raise ValueError(f"Unsupported prompt_mode: {prompt_mode}")
        self._prompt_mode = prompt_mode
        self._route_overrides = _validate_route_overrides(route_overrides or {})

    def compile(
        self,
        question: str,
        question_time: str | None,
        route: RouteResult,
        hits: tuple[RetrievalHit, ...],
        evidence_turns: tuple[Turn, ...],
        memory_records: tuple[MemoryRecord, ...] = (),
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

        route_settings = self._settings_for_route(route)

        ordered_candidates = _order_rows(
            tuple(candidates),
            question=question,
            route=route,
            evidence_order=self._evidence_order,
        )
        rows: list[EvidenceRow] = []
        used_chars = 0

        for row in ordered_candidates:
            if len(rows) >= route_settings["max_evidence_items"]:
                break
            row_chars = len(
                _format_row(
                    row,
                    question=question,
                    row_text_mode=route_settings["row_text_mode"],
                    max_row_text_chars=route_settings["max_row_text_chars"],
                )
            )
            if rows and used_chars + row_chars > route_settings["max_evidence_chars"]:
                break
            rows.append(row)
            used_chars += row_chars

        ordered_memory_records = _order_memory_records(
            tuple(memory_records),
            question=question,
            route=route,
            memory_order=self._memory_order,
        )
        selected_memory_records = ordered_memory_records[
            : route_settings["max_memory_records"]
        ]

        prompt = _build_prompt(
            question,
            question_time,
            route,
            tuple(selected_memory_records),
            tuple(rows),
            answer_style=self._answer_style,
            temporal_grounding=self._temporal_grounding,
            temporal_hints=self._temporal_hints,
            temporal_workpad=self._temporal_workpad,
            temporal_text_normalization=self._temporal_text_normalization,
            temporal_workpad_scope=self._temporal_workpad_scope,
            temporal_workpad_max_rows=self._temporal_workpad_max_rows,
            temporal_workpad_max_pairs=self._temporal_workpad_max_pairs,
            structured_guide=(
                self._structured_guide
                and not set(route.signals).intersection(
                    self._structured_guide_disabled_signals
                )
            ),
            structured_guide_max_rows=route_settings["structured_guide_max_rows"],
            structured_guide_include_rows=route_settings[
                "structured_guide_include_rows"
            ],
            structured_guide_include_memory=route_settings[
                "structured_guide_include_memory"
            ],
            structured_answer_contract=(
                self._structured_answer_contract
                and route.information_need
                in self._structured_answer_contract_information_needs
            ),
            structured_answer_contract_max_items=(
                self._structured_answer_contract_max_items
            ),
            memory_layout=self._memory_layout,
            row_text_mode=route_settings["row_text_mode"],
            max_row_text_chars=route_settings["max_row_text_chars"],
            route_guidance=self._route_guidance,
            evidence_row_labels=route_settings["evidence_row_labels"],
            final_answer_checklist=route_settings["final_answer_checklist"],
            prompt_mode=self._prompt_mode,
        )
        return CompiledContext(
            question=question,
            question_time=question_time,
            route=route,
            evidence_rows=tuple(rows),
            prompt=prompt,
            context_chars=len(prompt),
            memory_records=tuple(selected_memory_records),
        )

    def _settings_for_route(self, route: RouteResult) -> dict[str, Any]:
        settings: dict[str, Any] = {
            "evidence_row_labels": self._evidence_row_labels,
            "final_answer_checklist": self._final_answer_checklist,
            "max_evidence_chars": self._max_evidence_chars,
            "max_evidence_items": self._max_evidence_items,
            "max_memory_records": self._max_memory_records,
            "max_row_text_chars": self._max_row_text_chars,
            "row_text_mode": self._row_text_mode,
            "structured_guide_include_memory": self._structured_guide_include_memory,
            "structured_guide_include_rows": self._structured_guide_include_rows,
            "structured_guide_max_rows": self._structured_guide_max_rows,
        }
        settings.update(self._route_overrides.get(route.information_need, {}))
        return settings


def _validate_route_overrides(
    route_overrides: Mapping[str, Mapping[str, Any]],
) -> dict[str, dict[str, Any]]:
    normalized: dict[str, dict[str, Any]] = {}
    for information_need, raw_overrides in route_overrides.items():
        if information_need not in SUPPORTED_INFORMATION_NEEDS:
            raise ValueError(f"Unsupported compiler route override: {information_need}")
        if not isinstance(raw_overrides, Mapping):
            raise ValueError(
                f"compiler.route_overrides.{information_need} must be an object"
            )
        unknown_keys = set(raw_overrides).difference(ROUTE_OVERRIDE_KEYS)
        if unknown_keys:
            keys = ", ".join(sorted(unknown_keys))
            raise ValueError(
                f"Unsupported compiler.route_overrides.{information_need} keys: {keys}"
            )
        overrides: dict[str, Any] = {}
        if "max_evidence_items" in raw_overrides:
            overrides["max_evidence_items"] = max(
                0, int(raw_overrides["max_evidence_items"])
            )
        if "max_evidence_chars" in raw_overrides:
            overrides["max_evidence_chars"] = max(
                0, int(raw_overrides["max_evidence_chars"])
            )
        if "max_memory_records" in raw_overrides:
            overrides["max_memory_records"] = max(
                0, int(raw_overrides["max_memory_records"])
            )
        if "max_row_text_chars" in raw_overrides:
            overrides["max_row_text_chars"] = (
                int(raw_overrides["max_row_text_chars"]) or 800
            )
        if "structured_guide_max_rows" in raw_overrides:
            overrides["structured_guide_max_rows"] = max(
                1, int(raw_overrides["structured_guide_max_rows"])
            )
        if "structured_guide_include_rows" in raw_overrides:
            overrides["structured_guide_include_rows"] = bool(
                raw_overrides["structured_guide_include_rows"]
            )
        if "structured_guide_include_memory" in raw_overrides:
            overrides["structured_guide_include_memory"] = bool(
                raw_overrides["structured_guide_include_memory"]
            )
        if "row_text_mode" in raw_overrides:
            row_text_mode = str(raw_overrides["row_text_mode"])
            if row_text_mode not in {"full", "query_snippet", "role_query_snippet"}:
                raise ValueError(f"Unsupported row_text_mode: {row_text_mode}")
            overrides["row_text_mode"] = row_text_mode
        if "evidence_row_labels" in raw_overrides:
            overrides["evidence_row_labels"] = bool(
                raw_overrides["evidence_row_labels"]
            )
        if "final_answer_checklist" in raw_overrides:
            overrides["final_answer_checklist"] = bool(
                raw_overrides["final_answer_checklist"]
            )
        normalized[information_need] = overrides
    return normalized


def _validate_information_needs(
    information_needs: tuple[str, ...],
    *,
    field_name: str,
) -> tuple[str, ...]:
    normalized = tuple(str(value) for value in information_needs)
    unknown = set(normalized).difference(SUPPORTED_INFORMATION_NEEDS)
    if unknown:
        keys = ", ".join(sorted(unknown))
        raise ValueError(f"Unsupported compiler.{field_name}: {keys}")
    return normalized


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


def _order_memory_records(
    records: tuple[MemoryRecord, ...],
    question: str,
    route: RouteResult,
    memory_order: str,
) -> tuple[MemoryRecord, ...]:
    if memory_order == "retrieval":
        return records
    if memory_order != "question_overlap":
        raise ValueError(f"Unsupported memory_order: {memory_order}")

    question_terms = _content_terms(question)
    return tuple(
        record
        for _, record in sorted(
            enumerate(records),
            key=lambda item: _memory_record_key(
                index=item[0],
                record=item[1],
                question_terms=question_terms,
                route=route,
            ),
        )
    )


def _memory_record_key(
    index: int,
    record: MemoryRecord,
    question_terms: frozenset[str],
    route: RouteResult,
) -> tuple[float, int, str, int]:
    record_terms = _content_terms(record.search_text)
    overlap = len(question_terms.intersection(record_terms))
    type_bonus = _memory_type_bonus(record, route)
    temporal_bonus = (
        0.25
        if (
            route.information_need in {"current_state", "temporal_lookup"}
            and record.timestamp
        )
        else 0.0
    )
    confidence_bonus = min(max(record.confidence, 0.0), 1.0) * 0.1
    score = overlap + type_bonus + temporal_bonus + confidence_bonus
    missing_time = 1 if not record.timestamp else 0
    time_key = _memory_timestamp_sort_key(record.timestamp, route)
    return (-score, missing_time, time_key, index)


def _memory_type_bonus(record: MemoryRecord, route: RouteResult) -> float:
    memory_type = record.memory_type
    if route.information_need == "profile_preference":
        if memory_type in {"preference", "profile", "state"}:
            return 1.0
        if memory_type in {"fact", "event"}:
            return 0.2
        return 0.0
    if route.information_need == "current_state":
        if memory_type in {"state", "profile", "preference"}:
            return 0.8
        if memory_type in {"fact", "event"}:
            return 0.3
        return 0.0
    if route.information_need == "temporal_lookup":
        if memory_type in {"event", "state", "fact", "relationship"}:
            return 0.5
        return 0.0
    if route.information_need == "list_count":
        if memory_type in {"event", "fact", "relationship", "plan"}:
            return 0.4
        return 0.0
    if route.information_need == "fact_lookup":
        if memory_type in {"fact", "state", "relationship", "profile", "preference"}:
            return 0.2
        return 0.0
    return 0.0


def _memory_timestamp_sort_key(timestamp: str | None, route: RouteResult) -> str:
    normalized = timestamp or ""
    if route.information_need in {"current_state", "profile_preference"}:
        return _invert_sortable_text(normalized)
    return normalized


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
    memory_records: tuple[MemoryRecord, ...],
    rows: tuple[EvidenceRow, ...],
    answer_style: str,
    temporal_grounding: bool,
    temporal_hints: bool,
    temporal_workpad: bool,
    temporal_text_normalization: bool,
    temporal_workpad_scope: str,
    temporal_workpad_max_rows: int,
    temporal_workpad_max_pairs: int,
    structured_guide: bool,
    structured_guide_max_rows: int,
    structured_guide_include_rows: bool,
    structured_guide_include_memory: bool,
    structured_answer_contract: bool,
    structured_answer_contract_max_items: int,
    memory_layout: str,
    row_text_mode: str,
    max_row_text_chars: int,
    route_guidance: bool,
    evidence_row_labels: bool,
    final_answer_checklist: bool,
    prompt_mode: str,
) -> str:
    if prompt_mode == "raw_context_only":
        return _build_raw_context_only_prompt(
            question=question,
            question_time=question_time,
            rows=rows,
            answer_style=answer_style,
            row_text_mode=row_text_mode,
            max_row_text_chars=max_row_text_chars,
            evidence_row_labels=evidence_row_labels,
        )
    if prompt_mode == "external_naive":
        return _build_external_naive_prompt(
            question=question,
            question_time=question_time,
            route=route,
            memory_records=memory_records,
            rows=rows,
            row_text_mode=row_text_mode,
            max_row_text_chars=max_row_text_chars,
            temporal_workpad=temporal_workpad,
            temporal_text_normalization=temporal_text_normalization,
            temporal_workpad_scope=temporal_workpad_scope,
            temporal_workpad_max_rows=temporal_workpad_max_rows,
            temporal_workpad_max_pairs=temporal_workpad_max_pairs,
            structured_guide=structured_guide,
            structured_guide_max_rows=structured_guide_max_rows,
            structured_guide_include_rows=structured_guide_include_rows,
            structured_guide_include_memory=structured_guide_include_memory,
            structured_answer_contract=structured_answer_contract,
            structured_answer_contract_max_items=structured_answer_contract_max_items,
        )

    lines = [
        "Answer the question using the build-stage memory view and raw context.",
        "If the evidence is insufficient, answer that the information is not available.",
        "Do not use benchmark labels, gold answers, judge output, sample ids, or row indices.",
        "Build-stage memory is generated before seeing the question; use it as structured long-term memory, and use raw context to resolve ambiguity or conflicts.",
        "",
        f"Question: {question}",
        f"Question time: {question_time or 'not provided'}",
        f"Information need: {route.information_need}",
        "",
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
    if route_guidance:
        guidance_lines = _route_guidance_lines(route)
        if guidance_lines:
            lines[-1:-1] = ["", "Information-need guidance:", *guidance_lines, ""]

    lines.append("Build-stage typed memory view:")
    lines.extend(_format_memory_records(memory_records, memory_layout=memory_layout))

    if temporal_workpad and _should_add_temporal_workpad(
        question, route, temporal_workpad_scope
    ):
        workpad_lines = _temporal_workpad_lines(
            question,
            question_time,
            rows,
            max_rows=temporal_workpad_max_rows,
            max_pairs=temporal_workpad_max_pairs,
            include_relative_text=temporal_text_normalization,
        )
        if workpad_lines:
            lines.extend(("", "Temporal calculation workpad:"))
            lines.extend(workpad_lines)

    lines.extend(["", "Raw context table:"])
    if not rows:
        lines.append("(no evidence retrieved)")
    for row_index, row in enumerate(rows, start=1):
        lines.append(
            _format_row(
                row,
                question=question,
                row_text_mode=row_text_mode,
                max_row_text_chars=max_row_text_chars,
                row_label=f"E{row_index}" if evidence_row_labels else None,
            )
        )
    if temporal_grounding and temporal_hints:
        hints = _temporal_normalization_hints(rows)
        if hints:
            lines.extend(("", "Temporal normalization hints derived from row timestamps:"))
            lines.extend(hints)
    if final_answer_checklist:
        checklist = _final_answer_checklist_lines(route)
        if checklist:
            lines.extend(("", "Final answer checklist:"))
            lines.extend(checklist)
    return "\n".join(lines)


def _build_raw_context_only_prompt(
    *,
    question: str,
    question_time: str | None,
    rows: tuple[EvidenceRow, ...],
    answer_style: str,
    row_text_mode: str,
    max_row_text_chars: int,
    evidence_row_labels: bool,
) -> str:
    lines = [
        "Answer the user's question using only the provided memory context.",
        "Keep the answer concise and specific.",
        "Return only the final answer; do not include reasoning, row ids, citations, or JSON.",
        "If the memory context is insufficient, answer that the information is not available.",
        "Do not use benchmark labels, gold answers, judge output, sample ids, or row indices.",
    ]
    if answer_style == "concise":
        lines.insert(
            3,
            "Use the shortest direct answer that is fully supported; avoid explanations unless needed.",
        )
    lines.extend(
        [
            "",
            f"Question: {question}",
            f"Question time: {question_time or 'not provided'}",
            "",
            "Memory context:",
        ]
    )
    if not rows:
        lines.append("(no evidence retrieved)")
    for row_index, row in enumerate(rows, start=1):
        lines.append(
            _format_row(
                row,
                question=question,
                row_text_mode=row_text_mode,
                max_row_text_chars=max_row_text_chars,
                row_label=f"E{row_index}" if evidence_row_labels else None,
            )
        )
    return "\n".join(lines)


def _build_external_naive_prompt(
    *,
    question: str,
    question_time: str | None,
    route: RouteResult,
    memory_records: tuple[MemoryRecord, ...],
    rows: tuple[EvidenceRow, ...],
    row_text_mode: str,
    max_row_text_chars: int,
    temporal_workpad: bool,
    temporal_text_normalization: bool,
    temporal_workpad_scope: str,
    temporal_workpad_max_rows: int,
    temporal_workpad_max_pairs: int,
    structured_guide: bool,
    structured_guide_max_rows: int,
    structured_guide_include_rows: bool,
    structured_guide_include_memory: bool,
    structured_answer_contract: bool,
    structured_answer_contract_max_items: int,
) -> str:
    user_question = (
        f"Current Date: {question_time}\nQuestion: {question}"
        if question_time
        else question
    )
    temporal_aid = ""
    if temporal_workpad and _should_add_temporal_workpad(
        question, route, temporal_workpad_scope
    ):
        temporal_aid_lines = _external_temporal_aid_lines(
            question=question,
            question_time=question_time,
            rows=rows,
            max_rows=temporal_workpad_max_rows,
            max_pairs=temporal_workpad_max_pairs,
            include_relative_text=temporal_text_normalization,
        )
        if temporal_aid_lines:
            temporal_aid = "\n".join(["", "Temporal Aid:", *temporal_aid_lines, ""])
    structured_guide_block = ""
    if structured_guide:
        guide_lines = _external_structured_guide_lines(
            question=question,
            rows=rows,
            memory_records=memory_records,
            max_rows=structured_guide_max_rows,
            include_relative_text=temporal_text_normalization,
            include_rows=structured_guide_include_rows,
            include_memory=structured_guide_include_memory,
        )
        if guide_lines:
            structured_guide_block = "\n".join(
                ["", "Structured Evidence Guide:", *guide_lines, ""]
            )
    rules = ["Use only the memory context."]
    if structured_guide_block:
        rules.append(
            "Use Structured Evidence Guide only as an index into Memory Context; it is not independent evidence."
        )
    if temporal_aid:
        rules.append(
            "Use Temporal Aid only to interpret row dates and relative time phrases in the memory context; it is not independent evidence."
        )
    if structured_answer_contract:
        rules.extend(
            [
                "Before the final answer, identify the in-scope evidence items needed for count, list, sum, duration, order, or date questions.",
                "For count/list/sum questions, mark each candidate as included or excluded, merge duplicates under one canonical_item, and show compact arithmetic when needed.",
                "For temporal questions, prefer an event date or time phrase stated in the content over the Memory row Date; resolve relative phrases from that row Date and preserve the original phrase when useful.",
                "Keep evidence_items compact; include excluded candidates only when they explain a duplicate or out-of-scope decision.",
            ]
        )
    rules.extend(
        [
            "If the context is insufficient, say the provided information is not enough.",
            "Keep the answer concise and specific.",
            "Return only valid JSON.",
        ]
    )
    rule_lines = [f"{index}. {rule}" for index, rule in enumerate(rules, start=1)]
    if structured_answer_contract:
        output_json_lines = [
            "{",
            '  "reasoning": "one short sentence",',
            '  "sufficient": true,',
            '  "answer_type": "fact|count|list|sum|duration|date|order|preference|unknown",',
            '  "evidence_items": [',
            '    {"memory": "Memory 1", "canonical_item": "item/event/operand", "date": "date or empty", "value": "number/name/date/unit or empty", "include": true, "reason": "why it counts or is excluded"}',
            "  ],",
            '  "calculation": "short arithmetic or selection rule; empty if none",',
            '  "answer": "concise answer"',
            "}",
            f"Use at most {structured_answer_contract_max_items} evidence_items.",
        ]
    else:
        output_json_lines = [
            "{",
            '  "reasoning": "one short sentence",',
            '  "answer": "concise answer"',
            "}",
        ]
    return "\n".join(
        [
            "Answer the user's question using only the provided memory context.",
            "",
            "User Question:",
            user_question,
            structured_guide_block,
            "",
            "Memory Context:",
            _external_naive_context(
                rows,
                question=question,
                row_text_mode=row_text_mode,
                max_row_text_chars=max_row_text_chars,
            ),
            temporal_aid,
            "",
            "Rules:",
            *rule_lines,
            "",
            "Output JSON:",
            *output_json_lines,
        ]
    )

def _external_structured_guide_lines(
    *,
    question: str,
    rows: tuple[EvidenceRow, ...],
    memory_records: tuple[MemoryRecord, ...],
    max_rows: int,
    include_relative_text: bool,
    include_rows: bool,
    include_memory: bool,
) -> list[str]:
    if (not include_rows and not include_memory) or (not rows and not memory_records):
        return []

    lines = [
        "Use this compact guide to locate relevant raw Memory Context rows; verify final facts in those rows."
    ]
    question_terms = _content_terms(question)
    source_to_memory_index = {
        row.source_id: index for index, row in enumerate(rows, start=1)
    }

    if include_rows and rows:
        lines.append("- row_index:")
        for index, row in enumerate(rows[:max_rows], start=1):
            row_date = _parse_date(row.timestamp)
            row_date_text = row_date.isoformat() if row_date is not None else "unknown"
            matched_terms = tuple(
                sorted(question_terms.intersection(_content_terms(row.text)))
            )[:8]
            matched_text = ", ".join(matched_terms) or "none"
            relative_text = ""
            if include_relative_text and row_date is not None:
                relative_times = tuple(_relative_time_values(row.text, row_date))
                if relative_times:
                    relative_text = " | relative_time_mentions=" + "; ".join(
                        f'"{phrase}"=>"{normalized}"'
                        for phrase, normalized in relative_times[:4]
                    )
            lines.append(
                f"  - Memory {index}: row_date={row_date_text} role={row.role} "
                f"matched_terms={matched_text}{relative_text}"
            )

    if include_memory:
        memory_lines = _external_memory_guide_lines(
            memory_records=memory_records,
            source_to_memory_index=source_to_memory_index,
        )
        if memory_lines:
            lines.append("- activated_build_memory:")
            lines.extend(memory_lines)
    if len(lines) == 1:
        return []
    return lines


def _external_memory_guide_lines(
    *,
    memory_records: tuple[MemoryRecord, ...],
    source_to_memory_index: dict[str, int],
) -> list[str]:
    lines: list[str] = []
    seen_memory_ids: set[str] = set()
    for record in memory_records:
        if record.memory_id in seen_memory_ids:
            continue
        seen_memory_ids.add(record.memory_id)
        source_labels = []
        for source_id in record.source_ids:
            memory_index = source_to_memory_index.get(source_id)
            if memory_index is not None:
                source_labels.append(f"Memory {memory_index}")
        source_labels = list(dict.fromkeys(source_labels))
        if not source_labels:
            continue
        text = _truncate_text(_single_line(record.text), 220)
        fields = [
            f"type={record.memory_type}",
            f"status={record.status}",
            f"valid_from={record.valid_from or record.timestamp or 'unknown'}",
            f"valid_to={record.valid_to or 'open'}",
            f"sources={', '.join(source_labels[:6])}",
        ]
        if record.subject:
            fields.append(f"subject={_truncate_text(_single_line(record.subject), 80)}")
        if record.predicate:
            fields.append(
                f"predicate={_truncate_text(_single_line(record.predicate), 80)}"
            )
        if record.value:
            fields.append(f"value={_truncate_text(_single_line(record.value), 120)}")
        lines.append(f"  - {' | '.join(fields)}: {text}")
    return lines


def _single_line(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _external_temporal_aid_lines(
    *,
    question: str,
    question_time: str | None,
    rows: tuple[EvidenceRow, ...],
    max_rows: int,
    max_pairs: int,
    include_relative_text: bool,
) -> list[str]:
    candidates = _external_dated_candidate_rows(
        question,
        rows,
        include_relative_text=include_relative_text,
    )
    if not candidates:
        return []

    lines = [
        "Use this only as a date arithmetic aid derived from Memory Context row timestamps; final facts must still come from Memory Context."
    ]
    question_date = _parse_date(question_time)
    if question_date is not None:
        lines.append(f"- question_date={question_date.isoformat()}")

    selected = candidates[:max(1, max_rows)]
    lines.append("- memory_dates:")
    for candidate in selected:
        matched = ", ".join(candidate["matched_terms"]) or "none"
        relative = ""
        relative_times = candidate.get("relative_times", ())
        if include_relative_text and relative_times:
            relative = " | relative_time_mentions=" + "; ".join(
                f'phrase="{phrase}" normalized="{normalized}"'
                for phrase, normalized in relative_times
            )
        lines.append(
            f"  - Memory {candidate['memory_index']}: row_date={candidate['date']} "
            f"role={candidate['role']} matched_terms={matched}{relative}"
        )

    chronological = sorted(
        selected,
        key=lambda item: (str(item["date"]), int(item["memory_index"])),
    )
    if _asks_order(question) and len(chronological) >= 2:
        order = " -> ".join(
            f"Memory {item['memory_index']}({item['date']})" for item in chronological
        )
        lines.append(f"- chronological_order_by_row_date: {order}")

    if max_pairs > 0 and _asks_pairwise_duration(question) and len(selected) >= 2:
        lines.append("- pairwise_date_gaps:")
        for left, right in _external_pairwise_temporal_gaps(selected)[:max_pairs]:
            start = _parse_date(str(left["date"]))
            end = _parse_date(str(right["date"]))
            if start is None or end is None:
                continue
            days = abs((end - start).days)
            inclusive_days = days + 1
            lines.append(
                f"  - Memory {left['memory_index']}({start.isoformat()}) <-> "
                f"Memory {right['memory_index']}({end.isoformat()}): {days} days "
                f"({inclusive_days} inclusive), {days / 7:.2f} weeks, "
                f"{days / 30.44:.2f} approx months, {days / 365.25:.2f} approx years"
            )
    return lines


def _external_dated_candidate_rows(
    question: str,
    rows: tuple[EvidenceRow, ...],
    include_relative_text: bool,
) -> list[dict[str, object]]:
    question_terms = _content_terms(question)
    candidates: list[dict[str, object]] = []
    for index, row in enumerate(rows, start=1):
        row_date = _parse_date(row.timestamp)
        if row_date is None:
            continue
        matched_terms = tuple(sorted(question_terms.intersection(_content_terms(row.text))))
        relative_times = (
            tuple(_relative_time_values(row.text, row_date))
            if include_relative_text
            else ()
        )
        retrieval_bonus = 1 if row.retrieval_rank is not None else 0
        candidates.append(
            {
                "date": row_date.isoformat(),
                "index": index,
                "matched_terms": matched_terms[:8],
                "memory_index": index,
                "relative_times": relative_times,
                "role": row.role,
                "score": len(matched_terms) + retrieval_bonus + len(relative_times),
            }
        )
    candidates.sort(
        key=lambda item: (
            -int(item["score"]),
            int(item["index"]),
        )
    )
    return candidates


def _external_pairwise_temporal_gaps(
    dated_rows: list[dict[str, object]],
) -> list[tuple[dict[str, object], dict[str, object]]]:
    pairs: list[tuple[int, int, int, dict[str, object], dict[str, object]]] = []
    for left_index, left in enumerate(dated_rows):
        left_date = _parse_date(str(left["date"]))
        if left_date is None:
            continue
        for right_index, right in enumerate(dated_rows[left_index + 1 :], start=left_index + 1):
            right_date = _parse_date(str(right["date"]))
            if right_date is None or left_date == right_date:
                continue
            combined_score = int(left["score"]) + int(right["score"])
            index_distance = abs(int(left["index"]) - int(right["index"]))
            pairs.append((combined_score, -index_distance, -right_index, left, right))
    pairs.sort(key=lambda item: (item[0], item[1], item[2]), reverse=True)
    return [(left, right) for _, _, _, left, right in pairs]


def _external_naive_context(
    rows: tuple[EvidenceRow, ...],
    *,
    question: str,
    row_text_mode: str,
    max_row_text_chars: int,
) -> str:
    if not rows:
        return "None"
    blocks = []
    for index, row in enumerate(rows, start=1):
        header = f"### Memory {index}"
        if row.timestamp:
            header += f"\nDate: {row.timestamp}"
        if row.session_id:
            header += f"\nSession: {row.session_id}"
        text = _row_prompt_text(
            row.text,
            question=question,
            role=row.role,
            row_text_mode=row_text_mode,
            max_row_text_chars=max_row_text_chars,
        )
        blocks.append(f"{header}\n{row.role}: {text}")
    return "\n\n".join(blocks)


def _format_memory_records(
    records: tuple[MemoryRecord, ...],
    memory_layout: str,
) -> list[str]:
    if not records:
        return ["(no build-stage memory records activated)"]
    if memory_layout == "flat":
        return [_format_memory_record(record) for record in records]
    if memory_layout != "typed_sections":
        raise ValueError(f"Unsupported memory_layout: {memory_layout}")

    sections = [
        (
            "Profile/preference/state memory:",
            {"profile", "preference", "state"},
        ),
        (
            "Event/fact/relation memory:",
            {"event", "fact", "relationship", "plan", "unknown"},
        ),
    ]
    lines: list[str] = []
    seen_ids: set[str] = set()
    for title, memory_types in sections:
        section_records = [
            record for record in records if record.memory_type in memory_types
        ]
        if not section_records:
            continue
        lines.append(title)
        for record in section_records:
            seen_ids.add(record.memory_id)
            lines.append(_format_memory_record(record))

    leftovers = [record for record in records if record.memory_id not in seen_ids]
    if leftovers:
        lines.append("Other memory:")
        lines.extend(_format_memory_record(record) for record in leftovers)
    return lines


def _format_memory_record(record: MemoryRecord) -> str:
    entities = ", ".join(record.entities) if record.entities else "none"
    source_ids = ", ".join(record.source_ids)
    value_part = f" | value={record.value}" if record.value else ""
    subject_part = f" | subject={record.subject}" if record.subject else ""
    predicate_part = f" | predicate={record.predicate}" if record.predicate else ""
    validity_part = (
        f" | valid_from={record.valid_from or record.timestamp or 'unknown'}"
        f" | valid_to={record.valid_to or 'open'}"
    )
    status_part = (
        f" | status={record.status}"
        + (f" superseded_by={record.superseded_by}" if record.superseded_by else "")
    )
    return (
        f"- memory_id={record.memory_id} | type={record.memory_type}"
        f"{subject_part}{predicate_part}{value_part}"
        f" | time={record.timestamp or 'unknown'}{validity_part} | entities={entities}"
        f" | sources=[{source_ids}]{status_part}: {record.text}"
    )


def _format_row(
    row: EvidenceRow,
    question: str,
    row_text_mode: str,
    max_row_text_chars: int,
    row_label: str | None = None,
) -> str:
    rank = row.retrieval_rank if row.retrieval_rank is not None else "neighbor"
    score = f"{row.retrieval_score:.4f}" if row.retrieval_score is not None else "n/a"
    timestamp = row.timestamp or "unknown_time"
    text = _row_prompt_text(
        row.text,
        question=question,
        role=row.role,
        row_text_mode=row_text_mode,
        max_row_text_chars=max_row_text_chars,
    )
    label_prefix = f"{row_label} " if row_label else ""
    return (
        f"- {label_prefix}source_id={row.source_id} session={row.session_id} "
        f"turn={row.turn_index} role={row.role} time={timestamp} "
        f"rank={rank} score={score}: {text}"
    )


def _row_prompt_text(
    text: str,
    question: str,
    role: str,
    row_text_mode: str,
    max_row_text_chars: int,
) -> str:
    if row_text_mode == "full":
        return text
    if row_text_mode == "role_query_snippet":
        normalized_role = role.lower()
        if normalized_role == "assistant":
            return _query_snippet(text, question, max_row_text_chars)
        user_budget = max_row_text_chars * 2
        if len(text) > user_budget:
            return _query_snippet(text, question, user_budget)
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


def _route_guidance_lines(route: RouteResult) -> list[str]:
    if route.information_need == "current_state":
        return [
            "- Prefer the most recent directly supported evidence when older rows conflict.",
            "- If no row establishes the current state, answer that the information is not available.",
        ]
    if route.information_need == "temporal_lookup":
        return [
            "- Identify the event row first, then convert relative dates using that row time.",
            "- Return only the supported date, time span, or duration when the question asks when or how long.",
            "- If the question asks for elapsed days, weeks, months, or years, compute the difference before answering; do not return only a source date.",
            "- If the question asks which events happened in order, answer with event descriptions in chronological order, not only dates.",
        ]
    if route.information_need == "list_count":
        return [
            "- Gather all distinct supported items before answering.",
            "- If the question asks how many, count only items explicitly supported by the evidence.",
        ]
    if route.information_need == "profile_preference":
        return [
            "- Use stable stated preferences or profile facts; do not turn a one-time event into a preference.",
            "- If evidence conflicts, prefer the most recent explicit preference.",
        ]
    if route.information_need == "fact_lookup":
        return [
            "- Answer only the requested entity, value, or fact.",
            "- Ignore unrelated rows even if they share generic question words.",
        ]
    return []


def _final_answer_checklist_lines(route: RouteResult) -> list[str]:
    lines = [
        "- Privately identify the raw evidence row ids that directly support the final answer.",
        "- If no raw row supports the exact asked entity, object, relation, or time constraint, answer that the information is not available.",
        "- Do not answer from a related but different entity, object, activity, person, or collection.",
        "- If build-stage memory conflicts with raw rows, trust the raw rows.",
    ]
    if route.information_need == "current_state":
        lines.extend(
            [
                "- For current/latest questions, prefer the latest explicit raw row that matches the asked entity and relation.",
                "- If the question asks both previous and current values, provide both and do not collapse them to the latest value.",
            ]
        )
    if route.information_need == "temporal_lookup":
        lines.extend(
            [
                "- For how-long/how-many-days-ago questions, compute the requested duration; do not answer with only the event date.",
                "- For order/which-happened-first questions, answer with event descriptions in chronological order, not only dates.",
                "- Use row timestamps only to ground events described in that row; do not treat unrelated rows on the same date as the target event.",
            ]
        )
    if route.information_need == "list_count":
        lines.extend(
            [
                "- For list/count questions, gather all distinct supported items before answering; do not stop at the first matching row.",
                "- Do not count assistant suggestions unless the question asks for suggestions or assistant-provided items.",
            ]
        )
    if route.information_need == "profile_preference":
        lines.append(
            "- For preference/profile questions, require an explicit user preference or stable self-description."
        )
    lines.append("- Final response should contain only the answer, not the row ids or reasoning.")
    return lines


def _should_add_temporal_workpad(
    question: str,
    route: RouteResult,
    scope: str,
) -> bool:
    if scope == "calculation_route":
        return (
            route.information_need in {"temporal_lookup", "current_state"}
            and _asks_temporal_calculation(question)
        )
    if scope != "route":
        raise ValueError(f"Unsupported temporal_workpad_scope: {scope}")
    if route.information_need in {"temporal_lookup", "current_state"}:
        return True
    return _asks_temporal_route_hint(question)


def _temporal_workpad_lines(
    question: str,
    question_time: str | None,
    rows: tuple[EvidenceRow, ...],
    max_rows: int,
    max_pairs: int,
    include_relative_text: bool,
) -> list[str]:
    dated_rows = _dated_candidate_rows(
        question,
        rows,
        include_relative_text=include_relative_text,
    )
    if not dated_rows:
        return []

    lines = [
        "Use this only as an arithmetic aid derived from raw row timestamps; final facts must still come from the raw rows."
    ]
    if include_relative_text:
        lines.append(
            "- If row text contains a relative time mention, treat its normalized value as an event-time candidate; do not default to the row timestamp for that event."
        )
    question_date = _parse_date(question_time)
    if question_date is not None:
        lines.append(f"- question_date={question_date.isoformat()}")

    lines.append("- candidate_event_dates:")
    selected_rows = dated_rows[:max_rows]
    for candidate in selected_rows:
        matched = ", ".join(candidate["matched_terms"]) or "none"
        relative = ""
        row_date = candidate["date"]
        if question_date is not None and _asks_relative_to_question(question):
            days_ago = (question_date - row_date).days
            if days_ago >= 0:
                relative = (
                    f" | relative_to_question={days_ago} days ago, "
                    f"{days_ago // 7} full weeks ago, {days_ago / 7:.2f} weeks ago"
                )
        relative_times = candidate.get("relative_times", ())
        relative_mentions = ""
        if include_relative_text and relative_times:
            relative_mentions = " | relative_time_mentions=" + "; ".join(
                f'phrase="{phrase}" normalized="{normalized}"'
                for phrase, normalized in relative_times
            )
        lines.append(
            f"  - source_id={candidate['source_id']} date={row_date.isoformat()} "
            f"role={candidate['role']} matched_terms={matched}"
            f"{relative}{relative_mentions}"
        )

    chronological = sorted(
        selected_rows,
        key=lambda item: (item["date"], item["source_id"]),
    )
    if _asks_order(question) and len(chronological) >= 2:
        order = " -> ".join(
            f"{item['source_id']}({item['date'].isoformat()})" for item in chronological
        )
        lines.append(f"- chronological_order_by_date: {order}")

    if max_pairs > 0 and _asks_pairwise_duration(question) and len(selected_rows) >= 2:
        lines.append("- pairwise_date_gaps:")
        for left, right in _pairwise_temporal_gaps(selected_rows)[:max_pairs]:
            start = left["date"]
            end = right["date"]
            days = abs((end - start).days)
            inclusive_days = days + 1
            lines.append(
                f"  - {left['source_id']}({start.isoformat()}) <-> "
                f"{right['source_id']}({end.isoformat()}): {days} days "
                f"({inclusive_days} inclusive), {days / 7:.2f} weeks, "
                f"{days / 30.44:.2f} approx months, {days / 365.25:.2f} approx years"
            )
    return lines


def _dated_candidate_rows(
    question: str,
    rows: tuple[EvidenceRow, ...],
    include_relative_text: bool = False,
) -> list[dict[str, object]]:
    question_terms = _content_terms(question)
    candidates: list[dict[str, object]] = []
    seen_source_ids: set[str] = set()
    for index, row in enumerate(rows):
        if row.source_id in seen_source_ids:
            continue
        row_date = _parse_date(row.timestamp)
        if row_date is None:
            continue
        seen_source_ids.add(row.source_id)
        matched_terms = tuple(sorted(question_terms.intersection(_content_terms(row.text))))
        retrieval_bonus = 1 if row.retrieval_rank is not None else 0
        relative_times = (
            tuple(_relative_time_values(row.text, row_date))
            if include_relative_text
            else ()
        )
        candidates.append(
            {
                "date": row_date,
                "index": index,
                "matched_terms": matched_terms[:8],
                "relative_times": relative_times,
                "role": row.role,
                "score": len(matched_terms) + retrieval_bonus + len(relative_times),
                "source_id": row.source_id,
            }
        )
    candidates.sort(
        key=lambda item: (
            -int(item["score"]),
            int(item["index"]),
            str(item["source_id"]),
        )
    )
    return candidates


def _asks_temporal_calculation(question: str) -> bool:
    return bool(
        re.search(
            r"\b(?:how many\s+(?:days?|weeks?|months?|years?)|how long|between|elapsed|passed|duration|ago|since|before now|from now|order|chronological|first to last|last to first|before|after)\b",
            question.lower(),
        )
    )


def _asks_temporal_route_hint(question: str) -> bool:
    return bool(
        re.search(
            r"\b(?:ago|before|after|between|duration|elapsed|passed|days?|weeks?|months?|years?|chronological|first to last)\b",
            question.lower(),
        )
    )


def _asks_relative_to_question(question: str) -> bool:
    return bool(re.search(r"\b(?:ago|since|before now|from now)\b", question.lower()))


def _asks_pairwise_duration(question: str) -> bool:
    return bool(
        re.search(
            r"\b(?:how many\s+(?:days?|weeks?|months?|years?)|how long|between|elapsed|passed|duration)\b",
            question.lower(),
        )
    )


def _asks_order(question: str) -> bool:
    return bool(
        re.search(
            r"\b(?:order|chronological|first to last|last to first|before|after)\b",
            question.lower(),
        )
    )


def _pairwise_temporal_gaps(
    dated_rows: list[dict[str, object]],
) -> list[tuple[dict[str, object], dict[str, object]]]:
    pairs: list[tuple[int, int, int, dict[str, object], dict[str, object]]] = []
    for left_index, left in enumerate(dated_rows):
        for right_index, right in enumerate(dated_rows[left_index + 1 :], start=left_index + 1):
            if left["date"] == right["date"]:
                continue
            combined_score = int(left["score"]) + int(right["score"])
            index_distance = abs(int(left["index"]) - int(right["index"]))
            pairs.append((combined_score, -index_distance, -right_index, left, right))
    pairs.sort(key=lambda item: (item[0], item[1], item[2]), reverse=True)
    return [(left, right) for _, _, _, left, right in pairs]


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
        r"\b(?P<count>\d+|a|an|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s+"
        r"(?P<unit>days?|weeks?|months?|years?)\s+ago\b",
        lowered,
    ):
        count = _parse_count(match.group("count"))
        unit = match.group("unit")
        if count is None or not _is_reasonable_relative_span(count, unit):
            continue
        normalized = _ago_value(row_date, count=count, unit=unit)
        if normalized is None:
            continue
        values.append(
            (
                match.group(0),
                normalized,
            )
        )

    for match in re.finditer(
        r"\b(?P<direction>last|next|previous|coming)\s+"
        r"(?P<weekday>monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b",
        lowered,
    ):
        direction = _normalize_direction(match.group("direction"))
        weekday = match.group("weekday")
        values.append(
            (
                match.group(0),
                _relative_weekday(row_date, WEEKDAY_BY_NAME[weekday], direction).isoformat(),
            )
        )
    return values


def _parse_date(value: str | None) -> date | None:
    if value is None:
        return None
    text = value.strip()
    normalized = text[:10].replace("/", "-")
    try:
        return date.fromisoformat(normalized)
    except ValueError:
        pass

    numeric_match = re.search(
        r"\b(?P<year>\d{4})[-/](?P<month>\d{1,2})[-/](?P<day>\d{1,2})\b",
        text,
    )
    if numeric_match:
        parsed = _date_from_parts(
            int(numeric_match.group("year")),
            int(numeric_match.group("month")),
            int(numeric_match.group("day")),
        )
        if parsed is not None:
            return parsed

    day_month_match = re.search(
        r"\b(?P<day>\d{1,2})(?:st|nd|rd|th)?\s+"
        r"(?P<month>[A-Za-z]+),?\s+(?P<year>\d{4})\b",
        text,
    )
    if day_month_match:
        month = _month_number(day_month_match.group("month"))
        if month is not None:
            parsed = _date_from_parts(
                int(day_month_match.group("year")),
                month,
                int(day_month_match.group("day")),
            )
            if parsed is not None:
                return parsed

    month_day_match = re.search(
        r"\b(?P<month>[A-Za-z]+)\s+"
        r"(?P<day>\d{1,2})(?:st|nd|rd|th)?,?\s+(?P<year>\d{4})\b",
        text,
    )
    if month_day_match:
        month = _month_number(month_day_match.group("month"))
        if month is not None:
            parsed = _date_from_parts(
                int(month_day_match.group("year")),
                month,
                int(month_day_match.group("day")),
            )
            if parsed is not None:
                return parsed
    return None


def _date_from_parts(year: int, month: int, day: int) -> date | None:
    try:
        return date(year, month, day)
    except ValueError:
        return None


def _month_number(value: str) -> int | None:
    normalized = value.strip().lower()
    for index, name in enumerate(calendar.month_name):
        if index and normalized == name.lower():
            return index
    for index, name in enumerate(calendar.month_abbr):
        if index and normalized == name.lower():
            return index
    return None


def _shift_month(value: date, delta: int) -> date:
    month_index = value.year * 12 + value.month - 1 + delta
    year = month_index // 12
    month = month_index % 12 + 1
    day = min(value.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def _shift_year(value: date, delta: int) -> date:
    year = value.year + delta
    day = min(value.day, calendar.monthrange(year, value.month)[1])
    return date(year, value.month, day)


def _parse_count(value: str) -> int | None:
    if value.isdigit():
        return int(value)
    return NUMBER_WORDS.get(value)


def _is_reasonable_relative_span(count: int, unit: str) -> bool:
    if count < 0:
        return False
    for prefix, limit in MAX_RELATIVE_TIME_SPANS.items():
        if unit.startswith(prefix):
            return count <= limit
    return False


def _ago_value(value: date, count: int, unit: str) -> str | None:
    try:
        if unit.startswith("day"):
            return (value - timedelta(days=count)).isoformat()
        if unit.startswith("week"):
            return (value - timedelta(days=7 * count)).isoformat()
        if unit.startswith("month"):
            return _shift_month(value, -count).isoformat()
        if unit.startswith("year"):
            return _shift_year(value, -count).isoformat()
    except (OverflowError, ValueError):
        return None
    return None


def _normalize_direction(value: str) -> str:
    if value == "previous":
        return "last"
    if value == "coming":
        return "next"
    return value


def _relative_weekday(value: date, weekday: int, direction: str) -> date:
    if direction == "last":
        days = (value.weekday() - weekday) % 7
        return value - timedelta(days=days or 7)
    days = (weekday - value.weekday()) % 7
    return value + timedelta(days=days or 7)
