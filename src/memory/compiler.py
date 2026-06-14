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
    "candidate_guide",
    "candidate_guide_max_rows",
    "candidate_guide_snippet_chars",
    "context_layout",
    "current_state_update_contract",
    "evidence_order",
    "evidence_report_detail",
    "evidence_row_labels",
    "final_answer_checklist",
    "max_memory_records",
    "max_evidence_chars",
    "max_evidence_items",
    "max_row_text_chars",
    "row_text_mode",
    "source_anchor_keep",
    "source_anchor_memory_rows",
    "source_anchor_per_session",
    "source_anchor_session_rows",
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
        temporal_event_contract: bool = False,
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
        evidence_report_contract: bool = False,
        evidence_report_information_needs: tuple[str, ...] = tuple(
            sorted(SUPPORTED_INFORMATION_NEEDS)
        ),
        evidence_report_max_items: int = 8,
        evidence_report_detail: bool = False,
        aggregation_report_contract: bool = False,
        aggregation_report_information_needs: tuple[str, ...] = (
            DEFAULT_STRUCTURED_ANSWER_CONTRACT_NEEDS
        ),
        candidate_guide: bool = False,
        candidate_guide_information_needs: tuple[str, ...] = (
            DEFAULT_STRUCTURED_ANSWER_CONTRACT_NEEDS
        ),
        candidate_guide_max_rows: int = 6,
        candidate_guide_snippet_chars: int = 160,
        operation_workpad: bool = False,
        operation_workpad_information_needs: tuple[str, ...] = (
            DEFAULT_STRUCTURED_ANSWER_CONTRACT_NEEDS
        ),
        current_state_update_contract: bool = False,
        source_anchor_keep: int = 0,
        source_anchor_memory_rows: int = 0,
        source_anchor_per_session: int = 0,
        source_anchor_session_rows: int = 0,
        context_layout: str = "flat",
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
        self._temporal_event_contract = temporal_event_contract
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
        self._evidence_report_contract = evidence_report_contract
        self._evidence_report_information_needs = _validate_information_needs(
            evidence_report_information_needs,
            field_name="evidence_report_information_needs",
        )
        self._evidence_report_max_items = max(1, int(evidence_report_max_items))
        self._evidence_report_detail = evidence_report_detail
        self._aggregation_report_contract = aggregation_report_contract
        self._aggregation_report_information_needs = _validate_information_needs(
            aggregation_report_information_needs,
            field_name="aggregation_report_information_needs",
        )
        self._candidate_guide = candidate_guide
        self._candidate_guide_information_needs = _validate_information_needs(
            candidate_guide_information_needs,
            field_name="candidate_guide_information_needs",
        )
        self._candidate_guide_max_rows = max(1, int(candidate_guide_max_rows))
        self._candidate_guide_snippet_chars = max(
            80, int(candidate_guide_snippet_chars)
        )
        self._operation_workpad = operation_workpad
        self._operation_workpad_information_needs = _validate_information_needs(
            operation_workpad_information_needs,
            field_name="operation_workpad_information_needs",
        )
        self._current_state_update_contract = current_state_update_contract
        if context_layout not in {"flat", "session_thread"}:
            raise ValueError(f"Unsupported context_layout: {context_layout}")
        self._context_layout = context_layout
        if evidence_order not in {
            "retrieval",
            "question_overlap",
            "memory_aware",
            "source_anchor_coverage",
        }:
            raise ValueError(f"Unsupported evidence_order: {evidence_order}")
        self._evidence_order = evidence_order
        self._source_anchor_keep = max(0, int(source_anchor_keep))
        self._source_anchor_memory_rows = max(0, int(source_anchor_memory_rows))
        self._source_anchor_per_session = max(0, int(source_anchor_per_session))
        self._source_anchor_session_rows = max(0, int(source_anchor_session_rows))
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
            evidence_order=route_settings["evidence_order"],
            memory_records=tuple(memory_records),
            source_anchor_keep=route_settings["source_anchor_keep"],
            source_anchor_memory_rows=route_settings["source_anchor_memory_rows"],
            source_anchor_per_session=route_settings["source_anchor_per_session"],
            source_anchor_session_rows=route_settings["source_anchor_session_rows"],
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
        laid_out_rows = _layout_rows(
            tuple(rows),
            context_layout=route_settings["context_layout"],
        )

        prompt = _build_prompt(
            question,
            question_time,
            route,
            tuple(selected_memory_records),
            laid_out_rows,
            answer_style=self._answer_style,
            temporal_grounding=self._temporal_grounding,
            temporal_hints=self._temporal_hints,
            temporal_workpad=self._temporal_workpad,
            temporal_text_normalization=self._temporal_text_normalization,
            temporal_event_contract=self._temporal_event_contract,
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
            evidence_report_contract=(
                self._evidence_report_contract
                and route.information_need in self._evidence_report_information_needs
            ),
            aggregation_report_contract=(
                self._aggregation_report_contract
                and route.information_need in self._aggregation_report_information_needs
                and _is_aggregation_question(question)
            ),
            candidate_guide=(
                route_settings["candidate_guide"]
                and route.information_need in self._candidate_guide_information_needs
            ),
            candidate_guide_max_rows=route_settings["candidate_guide_max_rows"],
            candidate_guide_snippet_chars=route_settings[
                "candidate_guide_snippet_chars"
            ],
            evidence_report_max_items=self._evidence_report_max_items,
            evidence_report_detail=route_settings["evidence_report_detail"],
            operation_workpad=(
                self._operation_workpad
                and route.information_need in self._operation_workpad_information_needs
            ),
            current_state_update_contract=route_settings[
                "current_state_update_contract"
            ],
            context_layout=route_settings["context_layout"],
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
            evidence_rows=laid_out_rows,
            prompt=prompt,
            context_chars=len(prompt),
            memory_records=tuple(selected_memory_records),
        )

    def _settings_for_route(self, route: RouteResult) -> dict[str, Any]:
        settings: dict[str, Any] = {
            "candidate_guide": self._candidate_guide,
            "candidate_guide_max_rows": self._candidate_guide_max_rows,
            "candidate_guide_snippet_chars": self._candidate_guide_snippet_chars,
            "evidence_row_labels": self._evidence_row_labels,
            "context_layout": self._context_layout,
            "current_state_update_contract": self._current_state_update_contract,
            "evidence_order": self._evidence_order,
            "evidence_report_detail": self._evidence_report_detail,
            "final_answer_checklist": self._final_answer_checklist,
            "max_evidence_chars": self._max_evidence_chars,
            "max_evidence_items": self._max_evidence_items,
            "max_memory_records": self._max_memory_records,
            "max_row_text_chars": self._max_row_text_chars,
            "row_text_mode": self._row_text_mode,
            "source_anchor_keep": self._source_anchor_keep,
            "source_anchor_memory_rows": self._source_anchor_memory_rows,
            "source_anchor_per_session": self._source_anchor_per_session,
            "source_anchor_session_rows": self._source_anchor_session_rows,
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
        if "evidence_order" in raw_overrides:
            evidence_order = str(raw_overrides["evidence_order"])
            if evidence_order not in {
                "retrieval",
                "question_overlap",
                "memory_aware",
                "source_anchor_coverage",
            }:
                raise ValueError(f"Unsupported evidence_order: {evidence_order}")
            overrides["evidence_order"] = evidence_order
        for key in (
            "source_anchor_keep",
            "source_anchor_memory_rows",
            "source_anchor_per_session",
            "source_anchor_session_rows",
        ):
            if key in raw_overrides:
                overrides[key] = max(0, int(raw_overrides[key]))
        if "evidence_report_detail" in raw_overrides:
            overrides["evidence_report_detail"] = bool(
                raw_overrides["evidence_report_detail"]
            )
        if "candidate_guide" in raw_overrides:
            overrides["candidate_guide"] = bool(raw_overrides["candidate_guide"])
        if "candidate_guide_max_rows" in raw_overrides:
            overrides["candidate_guide_max_rows"] = max(
                1, int(raw_overrides["candidate_guide_max_rows"])
            )
        if "candidate_guide_snippet_chars" in raw_overrides:
            overrides["candidate_guide_snippet_chars"] = max(
                80, int(raw_overrides["candidate_guide_snippet_chars"])
            )
        if "evidence_row_labels" in raw_overrides:
            overrides["evidence_row_labels"] = bool(
                raw_overrides["evidence_row_labels"]
            )
        if "context_layout" in raw_overrides:
            context_layout = str(raw_overrides["context_layout"])
            if context_layout not in {"flat", "session_thread"}:
                raise ValueError(f"Unsupported context_layout: {context_layout}")
            overrides["context_layout"] = context_layout
        if "current_state_update_contract" in raw_overrides:
            overrides["current_state_update_contract"] = bool(
                raw_overrides["current_state_update_contract"]
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
    memory_records: tuple[MemoryRecord, ...] = (),
    source_anchor_keep: int = 0,
    source_anchor_memory_rows: int = 0,
    source_anchor_per_session: int = 0,
    source_anchor_session_rows: int = 0,
) -> tuple[EvidenceRow, ...]:
    if evidence_order == "retrieval":
        return rows
    if evidence_order not in {
        "question_overlap",
        "memory_aware",
        "source_anchor_coverage",
    }:
        raise ValueError(f"Unsupported evidence_order: {evidence_order}")

    question_terms = _content_terms(question)
    if evidence_order == "source_anchor_coverage":
        return _source_anchor_coverage_order(
            rows,
            question_terms=question_terms,
            route=route,
            memory_records=memory_records,
            anchor_keep=source_anchor_keep,
            memory_rows=source_anchor_memory_rows,
            per_session=source_anchor_per_session,
            session_rows=source_anchor_session_rows,
        )
    if evidence_order == "memory_aware":
        memory_source_scores = _memory_source_scores(
            memory_records,
            question_terms=question_terms,
            route=route,
        )
        return tuple(
            row
            for _, row in sorted(
                enumerate(rows),
                key=lambda item: _memory_aware_row_key(
                    index=item[0],
                    row=item[1],
                    question_terms=question_terms,
                    route=route,
                    memory_source_scores=memory_source_scores,
                ),
            )
        )

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


def _source_anchor_coverage_order(
    rows: tuple[EvidenceRow, ...],
    *,
    question_terms: frozenset[str],
    route: RouteResult,
    memory_records: tuple[MemoryRecord, ...],
    anchor_keep: int,
    memory_rows: int,
    per_session: int,
    session_rows: int,
) -> tuple[EvidenceRow, ...]:
    memory_source_scores = _memory_source_scores(
        memory_records,
        question_terms=question_terms,
        route=route,
    )
    if not rows or not memory_source_scores:
        return rows

    selected: list[EvidenceRow] = []
    seen: set[str] = set()
    memory_anchor_sessions: list[str] = []
    memory_session_counts: dict[str, int] = {}

    def add(row: EvidenceRow, *, memory_anchor: bool = False) -> bool:
        if row.source_id in seen:
            return False
        seen.add(row.source_id)
        selected.append(row)
        if memory_anchor and row.session_id not in memory_anchor_sessions:
            memory_anchor_sessions.append(row.session_id)
        return True

    for row in rows[:anchor_keep]:
        add(row)

    added_memory_rows = 0
    for row in sorted(
        rows,
        key=lambda item: _source_anchor_row_key(
            item,
            question_terms=question_terms,
            route=route,
            memory_source_scores=memory_source_scores,
        ),
    ):
        if memory_source_scores.get(row.source_id, 0.0) <= 0:
            continue
        if (
            per_session > 0
            and memory_session_counts.get(row.session_id, 0) >= per_session
        ):
            continue
        if add(row, memory_anchor=True):
            memory_session_counts[row.session_id] = (
                memory_session_counts.get(row.session_id, 0) + 1
            )
            added_memory_rows += 1
            if memory_rows > 0 and added_memory_rows >= memory_rows:
                break

    if session_rows > 0:
        session_counts: dict[str, int] = {}
        for session_id in memory_anchor_sessions:
            for row in rows:
                if row.session_id != session_id:
                    continue
                if session_counts.get(session_id, 0) >= session_rows:
                    break
                if add(row):
                    session_counts[session_id] = session_counts.get(session_id, 0) + 1

    for row in rows:
        add(row)
    return tuple(selected)


def _source_anchor_row_key(
    row: EvidenceRow,
    *,
    question_terms: frozenset[str],
    route: RouteResult,
    memory_source_scores: dict[str, float],
) -> tuple[float, float, float, int, int, str, str, int]:
    row_terms = _content_terms(row.text)
    memory_score = min(memory_source_scores.get(row.source_id, 0.0), 8.0)
    overlap = len(question_terms.intersection(row_terms))
    feature_bonus = _source_anchor_feature_bonus(row, route)
    missing_rank = 1 if row.retrieval_rank is None else 0
    rank = row.retrieval_rank if row.retrieval_rank is not None else 1_000_000
    time_key = _source_anchor_timestamp_key(row.timestamp, route)
    return (
        -memory_score,
        -overlap,
        -feature_bonus,
        missing_rank,
        rank,
        time_key,
        row.session_id,
        row.turn_index,
    )


def _source_anchor_feature_bonus(row: EvidenceRow, route: RouteResult) -> float:
    score = 0.0
    if route.information_need in {"list_count", "temporal_lookup"}:
        if _has_quantity_expression(row.text):
            score += 0.4
        if row.timestamp or _has_time_expression(row.text):
            score += 0.3
    if route.information_need in {"profile_preference", "current_state"}:
        if _has_profile_or_state_signal(row.text):
            score += 0.5
        if row.timestamp:
            score += 0.2
    if row.role.lower() == "user":
        score += 0.1
    return score


def _source_anchor_timestamp_key(timestamp: str | None, route: RouteResult) -> str:
    normalized = timestamp or ""
    if route.information_need in {"current_state", "profile_preference"}:
        return _invert_sortable_text(normalized)
    return normalized


def _layout_rows(
    rows: tuple[EvidenceRow, ...],
    *,
    context_layout: str,
) -> tuple[EvidenceRow, ...]:
    if context_layout == "flat":
        return rows
    if context_layout != "session_thread":
        raise ValueError(f"Unsupported context_layout: {context_layout}")

    grouped: dict[str, list[EvidenceRow]] = {}
    session_order: list[str] = []
    for row in rows:
        if row.session_id not in grouped:
            grouped[row.session_id] = []
            session_order.append(row.session_id)
        grouped[row.session_id].append(row)

    laid_out: list[EvidenceRow] = []
    for session_id in session_order:
        laid_out.extend(
            sorted(
                grouped[session_id],
                key=lambda row: (
                    row.turn_index,
                    row.retrieval_rank if row.retrieval_rank is not None else 1_000_000,
                    row.source_id,
                ),
            )
        )
    return tuple(laid_out)


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


def _memory_source_scores(
    records: tuple[MemoryRecord, ...],
    *,
    question_terms: frozenset[str],
    route: RouteResult,
) -> dict[str, float]:
    """Score raw source turns through source-linked build memory records."""

    scores: dict[str, float] = {}
    for index, record in enumerate(records):
        record_terms = _content_terms(record.search_text)
        overlap = len(question_terms.intersection(record_terms))
        if overlap <= 0 and _memory_type_bonus(record, route) <= 0:
            continue
        rank_bonus = 1.0 / (index + 1)
        confidence_bonus = min(max(record.confidence, 0.0), 1.0) * 0.1
        score = (
            overlap
            + _memory_type_bonus(record, route)
            + rank_bonus
            + confidence_bonus
        )
        for source_id in record.source_ids:
            scores[source_id] = max(scores.get(source_id, 0.0), score)
    return scores


def _memory_aware_row_key(
    index: int,
    row: EvidenceRow,
    question_terms: frozenset[str],
    route: RouteResult,
    memory_source_scores: dict[str, float],
) -> tuple[float, int, int, str, str, int, int]:
    row_terms = _content_terms(row.text)
    overlap = len(question_terms.intersection(row_terms))
    rank = row.retrieval_rank if row.retrieval_rank is not None else 1_000_000
    rank_bonus = 1.0 / (rank + 4.0) if row.retrieval_rank is not None else 0.0
    memory_bonus = min(memory_source_scores.get(row.source_id, 0.0), 4.0) * 0.35
    direct_hit_bonus = 1.0 if row.retrieval_rank is not None else 0.0
    temporal_bonus = (
        0.25
        if (
            route.information_need in {"current_state", "temporal_lookup"}
            and (row.timestamp or _has_time_expression(row.text))
        )
        else 0.0
    )
    quantity_bonus = (
        0.2
        if route.information_need == "list_count" and _has_quantity_expression(row.text)
        else 0.0
    )
    score = (
        overlap
        + direct_hit_bonus
        + rank_bonus
        + memory_bonus
        + temporal_bonus
        + quantity_bonus
    )
    missing_rank = 1 if row.retrieval_rank is None else 0
    time_key = _timestamp_sort_key(row.timestamp, route)
    return (-score, missing_rank, rank, time_key, row.session_id, row.turn_index, index)


def _content_terms(text: str) -> frozenset[str]:
    terms = [
        match.group(0).lower()
        for match in TOKEN_PATTERN.finditer(text)
        if match.group(0).lower() not in QUESTION_STOPWORDS
    ]
    return frozenset(terms)


def _has_quantity_expression(text: str) -> bool:
    lowered = text.lower()
    if re.search(r"\b\d+(?:[.,]\d+)?\b", lowered):
        return True
    return any(word in lowered for word in NUMBER_WORDS)


def _has_time_expression(text: str) -> bool:
    lowered = text.lower()
    return bool(
        re.search(r"\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b", lowered)
        or re.search(
            r"\b(?:yesterday|today|tomorrow|last|next|ago|week|month|year)\b",
            lowered,
        )
        or re.search(
            r"\b(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b",
            lowered,
        )
    )


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
    temporal_event_contract: bool,
    temporal_workpad_scope: str,
    temporal_workpad_max_rows: int,
    temporal_workpad_max_pairs: int,
    structured_guide: bool,
    structured_guide_max_rows: int,
    structured_guide_include_rows: bool,
    structured_guide_include_memory: bool,
    structured_answer_contract: bool,
    structured_answer_contract_max_items: int,
    evidence_report_contract: bool,
    aggregation_report_contract: bool,
    candidate_guide: bool,
    candidate_guide_max_rows: int,
    candidate_guide_snippet_chars: int,
    evidence_report_max_items: int,
    evidence_report_detail: bool,
    operation_workpad: bool,
    current_state_update_contract: bool,
    context_layout: str,
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
            context_layout=context_layout,
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
            temporal_event_contract=temporal_event_contract,
            temporal_workpad_scope=temporal_workpad_scope,
            temporal_workpad_max_rows=temporal_workpad_max_rows,
            temporal_workpad_max_pairs=temporal_workpad_max_pairs,
            structured_guide=structured_guide,
            structured_guide_max_rows=structured_guide_max_rows,
            structured_guide_include_rows=structured_guide_include_rows,
            structured_guide_include_memory=structured_guide_include_memory,
            structured_answer_contract=structured_answer_contract,
            structured_answer_contract_max_items=structured_answer_contract_max_items,
            evidence_report_contract=evidence_report_contract,
            aggregation_report_contract=aggregation_report_contract,
            candidate_guide=candidate_guide,
            candidate_guide_max_rows=candidate_guide_max_rows,
            candidate_guide_snippet_chars=candidate_guide_snippet_chars,
            evidence_report_max_items=evidence_report_max_items,
            evidence_report_detail=evidence_report_detail,
            operation_workpad=operation_workpad,
            current_state_update_contract=current_state_update_contract,
            final_answer_checklist=final_answer_checklist,
            context_layout=context_layout,
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
    context_layout: str,
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
    temporal_event_contract: bool,
    temporal_workpad_scope: str,
    temporal_workpad_max_rows: int,
    temporal_workpad_max_pairs: int,
    structured_guide: bool,
    structured_guide_max_rows: int,
    structured_guide_include_rows: bool,
    structured_guide_include_memory: bool,
    structured_answer_contract: bool,
    structured_answer_contract_max_items: int,
    evidence_report_contract: bool,
    aggregation_report_contract: bool,
    candidate_guide: bool,
    candidate_guide_max_rows: int,
    candidate_guide_snippet_chars: int,
    evidence_report_max_items: int,
    evidence_report_detail: bool,
    operation_workpad: bool,
    current_state_update_contract: bool,
    final_answer_checklist: bool,
    context_layout: str,
) -> str:
    use_temporal_event_contract = (
        temporal_event_contract and route.information_need == "temporal_lookup"
    )
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
            event_contract=use_temporal_event_contract,
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
            event_contract=use_temporal_event_contract,
            include_rows=structured_guide_include_rows,
            include_memory=structured_guide_include_memory,
        )
        if guide_lines:
            structured_guide_block = "\n".join(
                ["", "Structured Evidence Guide:", *guide_lines, ""]
            )
    candidate_guide_block = ""
    if candidate_guide:
        candidate_lines = _external_candidate_guide_lines(
            question=question,
            route=route,
            rows=rows,
            max_rows=candidate_guide_max_rows,
            snippet_chars=candidate_guide_snippet_chars,
        )
        if candidate_lines:
            candidate_guide_block = "\n".join(
                ["", "Candidate Evidence Map:", *candidate_lines, ""]
            )
    rules = ["Use only the memory context."]
    if structured_guide_block:
        rules.append(
            "Use Structured Evidence Guide only as an index into Memory Context; it is not independent evidence."
        )
    if candidate_guide_block:
        rules.append(
            "Use Candidate Evidence Map only as a compact index into Memory Context; it is not independent evidence."
        )
    if temporal_aid:
        rules.append(
            "Use Temporal Aid only to interpret row dates and relative time phrases in the memory context; it is not independent evidence."
        )
    if context_layout == "session_thread":
        rules.append(
            "Memory Context is grouped by session in chronological turn order within each session; use nearby turns in the same session to resolve implicit references, but do not merge unrelated sessions."
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
    use_aggregation_report_contract = (
        evidence_report_contract
        and aggregation_report_contract
        and not structured_answer_contract
    )
    if evidence_report_contract and not structured_answer_contract:
        rules.extend(
            _external_evidence_report_rules(
                question,
                route,
                temporal_event_contract=use_temporal_event_contract,
                detailed=evidence_report_detail,
                current_state_update_contract=current_state_update_contract,
            )
        )
    if use_aggregation_report_contract:
        rules.extend(_external_aggregation_report_rules())
    operation_workpad_block = ""
    if operation_workpad and not structured_answer_contract:
        operation_lines = _external_operation_workpad_lines(question, route)
        if operation_lines:
            operation_workpad_block = "\n".join(
                ["", "Private Operation Discipline:", *operation_lines, ""]
            )
            rules.append(
                "Use Private Operation Discipline as an internal checklist only; do not add checklist fields to the output JSON."
            )
    final_answer_checklist_block = ""
    if final_answer_checklist:
        checklist_lines = _final_answer_checklist_lines(route)
        if checklist_lines:
            final_answer_checklist_block = "\n".join(
                ["", "Final Answer Checklist:", *checklist_lines, ""]
            )
            rules.append(
                "Use Final Answer Checklist as an internal validation step only; do not add checklist fields to the output JSON."
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
    elif evidence_report_contract:
        if use_temporal_event_contract:
            evidence_item_schema = (
                '    {"memory": "Memory 1", "status": "support|exclude", '
                '"slot": "requested answer slot", "mention_time": "Memory Date or empty", '
                '"time_phrase": "explicit or relative time phrase in content or empty", '
                '"event_time": "date/time/span/duration of the target event or empty", '
                '"value": "answer value or empty", "reason": "why it supports or is excluded"}'
            )
        elif use_aggregation_report_contract:
            evidence_item_schema = (
                '    {"memory": "Memory 1", "status": "support|exclude", '
                '"canonical_item": "distinct item/event/operand or empty", '
                '"slot": "counted_item|operand|date|duration|order|exclude", '
                '"count_increment": "integer count contribution or empty", '
                '"operand_value": "number/unit for sum/difference/duration or empty", '
                '"value": "final value/date/name if not a count increment", '
                '"reason": "why it supports or is excluded"}'
            )
        else:
            evidence_item_schema = (
                '    {"memory": "Memory 1", "status": "support|exclude", '
                '"slot": "requested answer slot", "value": "number/name/date/unit or empty", '
                '"reason": "why it supports or is excluded"}'
            )
        output_json_lines = [
            "{",
            '  "reasoning": "compact evidence decision",',
            '  "sufficient": true,',
            '  "answer_type": "fact|count|list|sum|duration|date|order|preference|unknown",',
            '  "evidence_report": [',
            evidence_item_schema,
            "  ],",
            '  "calculation": "count/sum/difference/duration/order calculation or empty",',
            '  "missing": "missing required target/operand/endpoint or empty",',
            '  "answer": "concise answer"',
            "}",
            f"Use at most {evidence_report_max_items} evidence_report items.",
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
            candidate_guide_block,
            operation_workpad_block,
            final_answer_checklist_block,
            "",
            "Memory Context:",
            _external_naive_context(
                rows,
                question=question,
                row_text_mode=row_text_mode,
                max_row_text_chars=max_row_text_chars,
                context_layout=context_layout,
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


def _external_evidence_report_rules(
    question: str,
    route: RouteResult,
    *,
    temporal_event_contract: bool = False,
    detailed: bool = False,
    current_state_update_contract: bool = False,
) -> list[str]:
    """General visible evidence report instructions for clean reader discipline."""

    rules = [
        "Before the final answer, build a compact evidence_report from Memory Context.",
        "Every support item must match the requested entity, object, action, relation, speaker, time scope, and answer slot.",
        "Include close-but-wrong candidates as exclude items only when they could otherwise be confused with the answer.",
        "If a required target, operand, endpoint, or speaker source is missing, set sufficient=false and explain the missing part.",
        "Do not use Structured Evidence Guide or Temporal Aid as independent evidence; they only point to Memory Context rows.",
    ]
    if detailed:
        rules.extend(_detailed_evidence_report_rules(question))
    if route.information_need == "list_count":
        rules.extend(
            [
                "For count/list/sum/comparison questions, list distinct in-scope items or operands before answering.",
                "Merge duplicate mentions of the same real-world item, event, purchase, trip, process, person, or role.",
                "Do not count assistant suggestions or hypothetical examples unless the question asks about suggestions or the user confirms them.",
                "Answer with the count plus compact item names when names are available.",
            ]
        )
    elif route.information_need == "temporal_lookup":
        rules.extend(
            [
                "For date/duration/order questions, identify the exact event or state before selecting a date.",
                "Treat row Date as mention time; prefer event dates or relative time phrases stated in the row text.",
                "Resolve relative time phrases from the row Date and preserve explicit duration phrases when they directly answer.",
            ]
        )
        if temporal_event_contract:
            rules.extend(
                [
                    "In evidence_report, keep mention_time separate from event_time: mention_time is the Memory Date, while event_time is when the target event/state happened or held.",
                    "For when/date/duration answers, use event_time or a directly stated duration when available; use mention_time only if the content says the target event happened or was observed then, or the question asks when it was mentioned.",
                ]
            )
    elif route.information_need == "current_state":
        rules.extend(
            [
                "For current/latest/recent questions, include older and newer directly relevant candidates when present, then answer with the newest supported state.",
                "Do not let an old profile or old event override a newer directly relevant update.",
            ]
        )
        if current_state_update_contract:
            rules.extend(
                [
                    "A newer approximate or self-reported state is usable support when it directly matches the requested slot; keep qualifiers such as about, close to, almost, or nearing instead of reverting to an older exact value.",
                    "An assistant row can support a current state when it directly acknowledges, repeats, or summarizes the user's stated value or state.",
                ]
            )
    elif route.information_need == "profile_preference":
        rules.extend(
            [
                "For preference or recommendation questions, use stated preferences, dislikes, constraints, habits, owned resources, and prior experiences.",
                "Do not invent a named recommendation unless that name appears in Memory Context or the question asks for a type rather than a specific remembered item.",
            ]
        )
    else:
        rules.extend(
            [
                "For fact lookup questions, match the requested slot exactly: place, person, date, object, service, organization, or event.",
                "Do not answer with a related source, method, discussion topic, or explanation when the question asks for a different slot.",
            ]
        )
    return rules


def _external_aggregation_report_rules() -> list[str]:
    """Schema discipline for question-derived aggregation, without labels."""

    return [
        "For aggregation questions, first identify the exact owner/person, target entity, action, time range, and requested operation.",
        "Use canonical_item for the real-world item/event/operand being counted or calculated; merge duplicate mentions under one canonical_item.",
        "For count questions, use count_increment only as the item's contribution to the final count: usually 1 per distinct item/event, or a larger integer only when one memory explicitly names multiple distinct in-scope items.",
        "Do not put unrelated numeric facts such as tank size, page count, stars, mileage, dates, or already-read amounts into count_increment; put those in value or operand_value instead.",
        "For sum, difference, remaining, percentage, or duration questions, use operand_value for each operand and show the arithmetic in calculation.",
        "Exclude assistant suggestions, examples, hypotheticals, duplicates, wrong-time-range items, and merely related discussions unless the user confirmed the event or the question asks about suggestions.",
        "The final answer must match calculation: count=sum(count_increment), sum/difference from operand_value, order from dated included items.",
    ]


def _is_aggregation_question(question: str) -> bool:
    lowered = question.lower()
    return bool(
        re.search(
            r"\b(how many|how much|total|sum|combined|altogether|in all|count|"
            r"number of|difference|percentage|order of|ordered|earliest|latest)\b",
            lowered,
        )
    )


def _detailed_evidence_report_rules(question: str) -> list[str]:
    """Additional generic evidence discipline adapted from external memory QA systems."""

    rules = [
        "Include every candidate row that may change the final answer; preserve exact numbers, dates, names, places, titles, units, and event descriptions.",
        "Set status=support only when the row explicitly satisfies the requested action, object, relation, time range, and scope; mark related but mismatched candidates as exclude instead of silently ignoring them.",
        "Do not treat owning, discussing, planning, liking, asking about, recommending, or considering something as buying, attending, completing, using, reading, moving, or doing it unless the row says so explicitly.",
        "Assistant suggestions, estimates, recommendations, or hypothetical plans are support only when the question asks about assistant suggestions/plans or the user later confirms them.",
        "Do not treat missing evidence as zero, false, or none; if only a lower bound is supported, answer with that lower bound instead of inventing an exact value.",
        "For current/latest/recent/now questions, compare older and newer directly relevant candidates; for previous/initial/original questions, answer the requested historical state rather than the newest state.",
        "Preserve the evidence unit and wording when it directly answers the question; do not convert '45 minutes each way' into a different total unless the question asks for that total.",
    ]
    lowered = question.lower()
    if _asks_collection_operation(lowered) or _looks_like_plural_slot_question(lowered):
        rules.extend(
            [
                "For list-style what/which questions, preserve all distinct in-scope item names or values, not just one example or a broad class.",
                "Merge repeated mentions of the same real-world item, event, process, person, trip, purchase, or role under one canonical value.",
                "If a row is ambiguous between a duplicate and a separate new item, mark it exclude as ambiguous_duplicate unless the answer can be a supported lower bound.",
            ]
        )
    return rules


def _external_structured_guide_lines(
    *,
    question: str,
    rows: tuple[EvidenceRow, ...],
    memory_records: tuple[MemoryRecord, ...],
    max_rows: int,
    include_relative_text: bool,
    event_contract: bool,
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
                    if event_contract:
                        relative_text = " | event_time_candidates=" + "; ".join(
                            f'phrase="{phrase}" event_time="{normalized}"'
                            for phrase, normalized in relative_times[:4]
                        )
                    else:
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
            f"mention_time={record.mention_time or record.timestamp or 'unknown'}",
            f"event_time={record.event_time or 'unknown'}",
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


def _external_candidate_guide_lines(
    *,
    question: str,
    route: RouteResult,
    rows: tuple[EvidenceRow, ...],
    max_rows: int,
    snippet_chars: int,
) -> list[str]:
    """Compact source-preserving row map for candidate-heavy questions."""

    if not rows:
        return []

    selected = _candidate_guide_rows(
        question=question,
        route=route,
        rows=rows,
        max_rows=max_rows,
    )
    if not selected:
        return []

    lines = [
        "Use this compact map to compare candidate raw rows; verify final facts in Memory Context."
    ]
    focus = _candidate_guide_focus_line(question, route)
    if focus:
        lines.append(focus)
    lines.append("- candidates:")
    for memory_index, row in selected:
        matched_terms = sorted(_content_terms(question).intersection(_content_terms(row.text)))[:6]
        matched_text = ", ".join(matched_terms) or "none"
        quantities = _candidate_quantity_mentions(row.text)
        quantity_text = f" | quantities={'; '.join(quantities)}" if quantities else ""
        times = _candidate_time_mentions(row.text)
        time_text = f" | time_phrases={'; '.join(times)}" if times else ""
        snippet = _single_line(_query_snippet(row.text, question, snippet_chars))
        lines.append(
            f"  - Memory {memory_index}: date={row.timestamp or 'unknown'} "
            f"role={row.role} matched_terms={matched_text}{quantity_text}"
            f"{time_text} | text=\"{snippet}\""
        )
    return lines


def _candidate_guide_focus_line(question: str, route: RouteResult) -> str:
    lowered = question.lower()
    if route.information_need == "profile_preference":
        return (
            "- focus: extract user-stated preferences, constraints, dislikes, owned setup, "
            "and prior experiences; avoid generic advice unsupported by rows."
        )
    if route.information_need == "current_state":
        return (
            "- focus: compare newer and older directly relevant rows; answer the current "
            "state only when a row supports it."
        )
    if route.information_need == "list_count" or _asks_collection_operation(lowered):
        return (
            "- focus: collect distinct in-scope items/events, merge repeated mentions, "
            "and keep out-of-scope or hypothetical rows separate."
        )
    if route.information_need == "temporal_lookup":
        return (
            "- focus: identify the target event/action row before using row dates, "
            "relative time phrases, quantities, or durations."
        )
    return ""


def _candidate_guide_rows(
    *,
    question: str,
    route: RouteResult,
    rows: tuple[EvidenceRow, ...],
    max_rows: int,
) -> tuple[tuple[int, EvidenceRow], ...]:
    question_terms = _content_terms(question)
    scored: list[tuple[float, int, int, EvidenceRow]] = []
    for index, row in enumerate(rows, start=1):
        score = _candidate_guide_row_score(
            row,
            question_terms=question_terms,
            route=route,
        )
        if row.retrieval_rank is not None:
            score += 1.0 / (row.retrieval_rank + 4.0)
        if row.role.lower() == "user":
            score += 0.15
        scored.append((score, -index, index, row))

    scored.sort(reverse=True)
    selected = sorted(scored[:max_rows], key=lambda item: item[2])
    return tuple((index, row) for _, _, index, row in selected)


def _candidate_guide_row_score(
    row: EvidenceRow,
    *,
    question_terms: frozenset[str],
    route: RouteResult,
) -> float:
    row_terms = _content_terms(row.text)
    score = len(question_terms.intersection(row_terms)) * 2.0
    if route.information_need in {"list_count", "temporal_lookup"} and _has_quantity_expression(row.text):
        score += 0.8
    if route.information_need in {"temporal_lookup", "current_state"} and (
        row.timestamp or _has_time_expression(row.text)
    ):
        score += 0.6
    if route.information_need in {"profile_preference", "current_state"} and _has_profile_or_state_signal(row.text):
        score += 0.7
    return score


def _has_profile_or_state_signal(text: str) -> bool:
    lowered = text.lower()
    return bool(
        re.search(
            r"\b(prefer|preference|like|love|dislike|hate|need|want|looking for|"
            r"interested in|currently|now|still|own|have|my setup|my current)\b",
            lowered,
        )
    )


def _candidate_quantity_mentions(text: str) -> tuple[str, ...]:
    mentions: list[str] = []
    for match in re.finditer(
        r"(?:\$\s*)?\b\d+(?:[.,]\d+)?(?:\s*(?:days?|weeks?|months?|years?|hours?|minutes?|times?|items?|pieces?|videos?|films?|classes?))?",
        text,
        flags=re.IGNORECASE,
    ):
        mentions.append(_single_line(match.group(0)))
        if len(mentions) >= 4:
            break
    return tuple(dict.fromkeys(mentions))


def _candidate_time_mentions(text: str) -> tuple[str, ...]:
    patterns = (
        r"\b(?:yesterday|today|tomorrow)\b",
        r"\b(?:last|next|this)\s+(?:day|week|month|year|monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b",
        r"\b\d+\s+(?:days?|weeks?|months?|years?)\s+ago\b",
        r"\b20\d{2}[-/]\d{1,2}[-/]\d{1,2}\b",
        r"\b(?:january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2}(?:st|nd|rd|th)?(?:,\s*20\d{2})?\b",
    )
    mentions: list[str] = []
    for pattern in patterns:
        for match in re.finditer(pattern, text, flags=re.IGNORECASE):
            mentions.append(_single_line(match.group(0)))
            if len(mentions) >= 4:
                return tuple(dict.fromkeys(mentions))
    return tuple(dict.fromkeys(mentions))


def _external_operation_workpad_lines(question: str, route: RouteResult) -> list[str]:
    """Short generic reader discipline for operation-heavy questions.

    This deliberately does not request a richer output schema. The goal is to
    preserve v18's concise answer surface while asking the model to privately
    verify operands, scope, and dates before producing the final JSON.
    """

    lines = [
        "- Privately identify the exact answer slot requested: person, place, date, duration, count, list, order, or fact.",
        "- A candidate row is usable only if it matches the asked entity, object, action, relation, and time scope; related-topic evidence is not enough.",
        "- If a required target, compared item, endpoint, or operand is missing, answer that the provided information is not enough.",
    ]
    if route.information_need == "list_count" or _asks_collection_operation(question):
        lines.extend(
            [
                "- For count, list, sum, difference, average, or comparison questions, gather all distinct in-scope items before answering.",
                "- If the question uses inclusive alternatives such as 'or', 'have done or currently doing', or 'past or current', include candidates satisfying any requested alternative rather than excluding past items only because they are not current.",
                "- Merge duplicate mentions of the same real-world item, event, process, subscription, trip, purchase, or role.",
                "- Do not count assistant suggestions, hypothetical examples, or paraphrases unless the question asks about suggestions or the user confirms them.",
                "- Verify arithmetic and preserve the requested unit; include enough item detail to avoid a partial answer.",
            ]
        )
    if route.information_need in {"temporal_lookup", "current_state"} or _asks_temporal_calculation(question):
        lines.extend(
            [
                "- For date, duration, and order questions, first identify the event/action row, then derive the answer from that row.",
                "- Treat the row Date as the mention time; prefer event dates or relative time phrases stated in the row text when they differ.",
                "- Resolve phrases such as yesterday, last Friday, last week, last month, and years ago from the row Date; do not answer with the row Date unless the event happened on that date.",
                "- Preserve an explicit duration phrase when it directly answers a how-long question instead of replacing it with a rough date gap.",
            ]
        )
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
    event_contract: bool = False,
) -> list[str]:
    candidates = _external_dated_candidate_rows(
        question,
        rows,
        include_relative_text=include_relative_text,
    )
    if not candidates:
        return []

    if event_contract:
        lines = [
            "Use this only as a date arithmetic aid derived from Memory Context row timestamps and relative phrases; final facts must still come from Memory Context.",
            "- mention_time is the Memory Date. event_time_candidates come from relative or explicit time phrases in the row text and should answer the target event time when they match the question.",
        ]
    else:
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
            if event_contract:
                relative = " | event_time_candidates=" + "; ".join(
                    f'phrase="{phrase}" event_time="{normalized}"'
                    for phrase, normalized in relative_times
                )
            else:
                relative = " | relative_time_mentions=" + "; ".join(
                    f'phrase="{phrase}" normalized="{normalized}"'
                    for phrase, normalized in relative_times
                )
        date_label = "mention_time" if event_contract else "row_date"
        lines.append(
            f"  - Memory {candidate['memory_index']}: {date_label}={candidate['date']} "
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
    context_layout: str = "flat",
) -> str:
    if not rows:
        return "None"
    if context_layout == "session_thread":
        return _external_session_thread_context(
            rows,
            question=question,
            row_text_mode=row_text_mode,
            max_row_text_chars=max_row_text_chars,
        )
    if context_layout != "flat":
        raise ValueError(f"Unsupported context_layout: {context_layout}")
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


def _external_session_thread_context(
    rows: tuple[EvidenceRow, ...],
    *,
    question: str,
    row_text_mode: str,
    max_row_text_chars: int,
) -> str:
    blocks: list[str] = []
    current_session: str | None = None
    episode_index = 0
    for index, row in enumerate(rows, start=1):
        if row.session_id != current_session:
            episode_index += 1
            current_session = row.session_id
            blocks.append(f"### Episode {episode_index}\nSession: {row.session_id}")
        header = f"#### Memory {index}"
        if row.timestamp:
            header += f"\nDate: {row.timestamp}"
        header += f"\nTurn: {row.turn_index}"
        if row.retrieval_rank is not None:
            header += f"\nRetrieval rank: {row.retrieval_rank}"
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
        f" | mention_time={record.mention_time or record.timestamp or 'unknown'}"
        f" | event_time={record.event_time or 'unknown'}"
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
        "- Privately identify the Memory Context rows that directly support the final answer.",
        "- If no raw row supports the exact asked entity, object, relation, or time constraint, answer that the information is not available.",
        "- Do not answer from a related but different entity, object, activity, person, or collection.",
        "- If the question mentions multiple compared alternatives, required target actions, or scoped entities, each required part must be directly supported; partial support is not enough.",
        "- Do not infer that an alternative happened, was purchased, attended, completed, or preferred merely because another alternative is supported.",
        "- Preserve full names, titles, locations, dates, item names, and qualifiers from supporting rows when they are part of the requested answer.",
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


def _asks_collection_operation(question: str) -> bool:
    return bool(
        re.search(
            r"\b(?:how many|count|total|sum|average|difference|both|shared|common|all|list|which|first|earlier|later|more|less)\b",
            question.lower(),
        )
    )


def _looks_like_plural_slot_question(question: str) -> bool:
    lowered = question.lower()
    return bool(
        re.search(
            r"\b(?:what|which)\s+(?:types?|kinds?|events?|books?|movies?|shows?|places?|cities?|schools?|organizations?|items?|things?|activities?|hobbies?|[a-z]+s)\b",
            lowered,
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
    seen: set[tuple[str, str]] = set()
    seen_normalized: set[str] = set()

    def append_value(phrase: str, normalized: str) -> None:
        key = (phrase, normalized)
        if key in seen or normalized in seen_normalized:
            return
        seen.add(key)
        seen_normalized.add(normalized)
        values.append(key)

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
            "previous week",
            f"{(row_date - timedelta(days=7)).isoformat()} to "
            f"{(row_date - timedelta(days=1)).isoformat()}",
        ),
        (
            "the week before",
            f"{(row_date - timedelta(days=7)).isoformat()} to "
            f"{(row_date - timedelta(days=1)).isoformat()}",
        ),
        (
            "week before",
            f"{(row_date - timedelta(days=7)).isoformat()} to "
            f"{(row_date - timedelta(days=1)).isoformat()}",
        ),
        (
            "next week",
            f"{(row_date + timedelta(days=1)).isoformat()} to "
            f"{(row_date + timedelta(days=7)).isoformat()}",
        ),
        ("last weekend", _weekend_before(row_date, weekends_back=1)),
        ("previous weekend", _weekend_before(row_date, weekends_back=1)),
        ("the weekend before", _weekend_before(row_date, weekends_back=1)),
        ("weekend before", _weekend_before(row_date, weekends_back=1)),
    )
    for phrase, normalized in fixed_phrases:
        if re.search(rf"\b{re.escape(phrase)}\b", lowered):
            append_value(phrase, normalized)

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
        append_value(match.group(0), normalized)

    for match in re.finditer(
        r"\b(?P<count>\d+|a|an|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s+"
        r"weekends?\s+(?:ago|before)\b",
        lowered,
    ):
        count = _parse_count(match.group("count"))
        if count is None or not _is_reasonable_relative_span(count, "week"):
            continue
        append_value(match.group(0), _weekend_before(row_date, weekends_back=count))

    for match in re.finditer(
        r"\b(?P<direction>last|next|previous|coming)\s+"
        r"(?P<weekday>monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b",
        lowered,
    ):
        direction = _normalize_direction(match.group("direction"))
        weekday = match.group("weekday")
        append_value(
            match.group(0),
            _relative_weekday(row_date, WEEKDAY_BY_NAME[weekday], direction).isoformat(),
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


def _weekend_before(value: date, *, weekends_back: int) -> str:
    days_since_sunday = (value.weekday() - 6) % 7
    latest_prior_sunday = value - timedelta(days=days_since_sunday or 7)
    target_sunday = latest_prior_sunday - timedelta(days=7 * max(0, weekends_back - 1))
    target_saturday = target_sunday - timedelta(days=1)
    return f"{target_saturday.isoformat()} to {target_sunday.isoformat()}"


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
