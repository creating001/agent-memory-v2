"""Evidence table compiler."""

from __future__ import annotations

import calendar
import re
from collections.abc import Iterable, Mapping
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
MEMORY_STATE_GUIDE_VALUE_CONFLICT_TYPES = {"fact", "preference", "profile", "state"}
MEMORY_STATE_GUIDE_CONFLICT_SOURCES = {"records", "build_manifest"}
MEMORY_STATE_GUIDE_ALIGNMENT_WEAK_TERMS = {
    "a",
    "about",
    "after",
    "an",
    "and",
    "are",
    "at",
    "been",
    "before",
    "current",
    "did",
    "does",
    "for",
    "from",
    "got",
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
    "latest",
    "me",
    "my",
    "now",
    "of",
    "on",
    "or",
    "our",
    "previous",
    "recent",
    "recently",
    "the",
    "their",
    "today",
    "was",
    "were",
    "what",
    "when",
    "where",
    "which",
    "with",
    "you",
    "your",
}
MEMORY_STATE_GUIDE_STATEFUL_SLOT_PATTERN = re.compile(
    r"\b("
    r"address|current|feel|feels|frequent|goal|job|live|lives|living|"
    r"located|location|membership|moved|position|record|role|status|work|works"
    r")\b",
    re.IGNORECASE,
)
MEMORY_OPERATION_PLAN_REQUIRED_READINESS_MODES = (
    "additive_index",
    "source_expansion",
    "context_organization",
)
UPDATE_CONFLICT_VALUE_UNIT_STOPWORDS = {
    "a",
    "about",
    "after",
    "an",
    "ago",
    "and",
    "around",
    "at",
    "before",
    "by",
    "for",
    "from",
    "in",
    "is",
    "later",
    "last",
    "next",
    "now",
    "of",
    "on",
    "or",
    "per",
    "the",
    "this",
    "to",
    "today",
    "tomorrow",
    "was",
    "were",
    "with",
    "yesterday",
}
UPDATE_CONFLICT_VALUE_PATTERNS = (
    r"\b\d{1,2}:\d{2}\b",
    r"(?:[$€£]\s*)?\b\d{1,3}(?:,\d{3})+(?:\.\d+)?(?:\s+(?:[A-Za-z][A-Za-z0-9%/-]*|%)){0,2}\b",
    r"(?:[$€£]\s*)?\b\d+(?:\.\d+)?\s*k\b",
    r"(?:[$€£]\s*)?\b\d+(?:\.\d+)?\s*(?:percent|%)\b",
    r"\b(?:every other week|every week|weekly|monthly|yearly|once a week|twice a week|once a month|twice a month)\b",
)
UPDATE_CONFLICT_SCALAR_VALUE_PATTERNS = (
    r"\b\d{1,2}:\d{2}\b",
    r"(?:[$€£]\s*)?\b\d{1,3}(?:,\d{3})+(?:\.\d+)?\b",
    r"(?:[$€£]\s*)?\b\d+(?:\.\d+)?\s*k\b",
    r"(?:[$€£]\s*)?\b\d+(?:\.\d+)?\s*(?:percent|%)\b",
    r"\b(?:every other week|every week|weekly|monthly|yearly|once a week|twice a week|once a month|twice a month)\b",
    r"(?:[$€£]\s*)?\b\d+(?:\.\d+)?\b",
)
UPDATE_CONFLICT_GENERIC_VALUE_PATTERN = (
    r"(?:[$€£]\s*)?\b\d+(?:,\d{3})*(?:\.\d+)?"
    r"(?:\s+(?:[A-Za-z][A-Za-z0-9%/-]*|%)){0,2}\b"
)
TOKEN_PATTERN = re.compile(r"[\w]+", re.UNICODE)
PERSONALIZED_ADVICE_PATTERN = re.compile(
    r"\b("
    r"recommend(?:ation|ations|ed|ing)?|suggest(?:ion|ions|ed|ing)?|"
    r"advice|advise|tips?|ideas?|should\s+i|should\s+we|"
    r"what\s+should\s+i|what\s+do\s+you\s+think|do\s+you\s+think|"
    r"help\s+me\s+choose|best\s+way"
    r")\b",
    re.IGNORECASE,
)
ASSISTANT_RECALL_PATTERN = re.compile(
    r"\b("
    r"remind\s+me|remember|earlier|previously|last\s+time|"
    r"you\s+(?:told|recommended|suggested|said|mentioned)|"
    r"what\s+did\s+you|what\s+was\s+the"
    r")\b",
    re.IGNORECASE,
)
GROUNDED_INFERENCE_PATTERN = re.compile(
    r"\b("
    r"would|might|could|likely|unlikely|probably|seem(?:s)?|"
    r"considered|do\s+you\s+think|what\s+might|how\s+would|"
    r"still\s+want|be\s+considered"
    r")\b",
    re.IGNORECASE,
)
MODAL_GROUNDED_INFERENCE_PATTERN = re.compile(
    r"\b("
    r"would|might|could|likely|unlikely|probably|seem(?:s)?|"
    r"considered|what\s+might|how\s+would|still\s+want|be\s+considered"
    r")\b",
    re.IGNORECASE,
)
SUPPORTED_INFORMATION_NEEDS = {
    "current_state",
    "fact_lookup",
    "list_count",
    "profile_preference",
    "temporal_lookup",
}
SUPPORTED_CONTEXT_LAYOUTS = {"flat", "session_thread", "chronological_session_thread"}
ROUTE_OVERRIDE_KEYS = {
    "candidate_guide",
    "candidate_guide_include_memory_hints",
    "candidate_guide_max_memory_hints",
    "candidate_guide_max_rows",
    "candidate_guide_memory_hint_chars",
    "candidate_guide_snippet_chars",
    "context_layout",
    "current_state_update_contract",
    "dialogue_inference_contract",
    "event_time_candidate_map",
    "event_time_candidate_map_audit",
    "event_time_candidate_map_allow_time_of_day_questions",
    "event_time_candidate_map_allowed_time_kinds",
    "event_time_candidate_map_include_mention_time",
    "event_time_candidate_map_mention_time_fallback",
    "event_time_candidate_map_mention_time_fallback_min_coverage",
    "event_time_candidate_map_mention_time_fallback_trigger_max_coverage",
    "event_time_candidate_map_max_groups",
    "event_time_candidate_map_min_coverage",
    "event_time_candidate_map_min_terms",
    "event_time_candidate_map_snippet_chars",
    "event_time_candidate_map_strip_context_wrappers",
    "enable_weekend_relative_time",
    "evidence_order",
    "evidence_report_detail",
    "grounded_inference_contract",
    "grounded_inference_gate",
    "max_memory_records",
    "max_evidence_chars",
    "max_evidence_items",
    "max_row_text_chars",
    "memory_state_guide",
    "memory_state_guide_candidate_records",
    "memory_state_guide_require_active_superseded_pair",
    "memory_state_guide_require_slot_overlap",
    "memory_state_guide_require_conflict",
    "memory_state_guide_conflict_source",
    "memory_state_guide_require_stateful_slot",
    "memory_state_guide_include_superseded",
    "memory_state_guide_max_records",
    "memory_state_guide_value_chars",
    "memory_value_slot_guide",
    "memory_value_slot_guide_max_slots",
    "memory_value_slot_guide_max_values",
    "memory_value_slot_guide_memory_types",
    "memory_operation_plan_guide",
    "memory_operation_plan_guide_max_plans",
    "memory_operation_plan_guide_max_values",
    "memory_operation_plan_guide_value_chars",
    "memory_operation_plan_guide_render_values",
    "memory_operation_plan_guide_require_readiness",
    "memory_operation_plan_guide_required_readiness_modes",
    "memory_operation_context_organizer",
    "memory_operation_context_organizer_max_plans",
    "memory_operation_readiness_audit",
    "memory_operation_readiness_audit_max_plans",
    "memory_workspace_plan",
    "memory_workspace_plan_max_groups",
    "memory_workspace_plan_max_values",
    "memory_workspace_plan_value_chars",
    "profile_activation_guide",
    "profile_activation_guide_max_records",
    "profile_activation_guide_value_chars",
    "row_text_mode",
    "tail_max_row_text_chars",
    "tail_row_text_after_rank",
    "tail_row_text_mode",
    "source_anchor_keep",
    "source_anchor_memory_rows",
    "source_anchor_per_session",
    "source_anchor_session_rows",
    "structured_guide_include_memory",
    "structured_guide_include_rows",
    "structured_guide_max_memory_hints_per_row",
    "structured_guide_memory_hint_chars",
    "structured_guide_memory_hints",
    "structured_guide_max_rows",
    "temporal_order_contract",
    "update_conflict_guide",
    "update_conflict_guide_max_rows",
    "update_conflict_guide_snippet_chars",
}
EVIDENCE_ORDER_MODES = {
    "retrieval",
    "question_overlap",
    "memory_aware",
    "source_anchor_coverage",
    "memory_source_interleave",
    "memory_version_chain_interleave",
    "scoped_memory_version_chain_interleave",
    "memory_tail_filter_preserve_order",
    "fixed_set_memory_source_interleave",
}
FIXED_SET_EVIDENCE_ORDER_MODES = {"fixed_set_memory_source_interleave"}
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
        temporal_workpad: bool = False,
        temporal_text_normalization: bool = False,
        temporal_event_contract: bool = False,
        temporal_workpad_scope: str = "route",
        temporal_workpad_max_rows: int = 10,
        temporal_workpad_max_pairs: int = 12,
        event_timeline: bool = False,
        event_timeline_information_needs: tuple[str, ...] = (
            "current_state",
            "list_count",
            "temporal_lookup",
        ),
        event_timeline_max_rows: int = 12,
        event_timeline_snippet_chars: int = 180,
        event_time_candidate_manifest: bool = False,
        event_time_candidate_manifest_information_needs: tuple[str, ...] = (
            "current_state",
            "list_count",
            "temporal_lookup",
        ),
        event_time_candidate_manifest_max_rows: int = 12,
        event_time_candidate_manifest_snippet_chars: int = 160,
        event_time_candidate_manifest_question_gate: bool = True,
        event_time_candidate_manifest_grouped_view: bool = False,
        event_time_candidate_manifest_max_groups: int = 8,
        event_time_candidate_map: bool = False,
        event_time_candidate_map_information_needs: tuple[str, ...] = (
            "temporal_lookup",
        ),
        event_time_candidate_map_max_groups: int = 1,
        event_time_candidate_map_snippet_chars: int = 140,
        event_time_candidate_map_min_terms: int = 2,
        event_time_candidate_map_min_coverage: float = 0.6,
        event_time_candidate_map_allowed_time_kinds: tuple[str, ...] = (
            "exact_today",
            "explicit_date",
            "relative_phrase",
        ),
        event_time_candidate_map_strip_context_wrappers: bool = False,
        event_time_candidate_map_segment_local_context: bool = False,
        event_time_candidate_map_rank_by_coverage: bool = False,
        event_time_candidate_map_normalize_terms: bool = False,
        event_time_candidate_map_exact_today_min_coverage: float | None = None,
        event_time_candidate_map_require_role_match: bool = False,
        event_time_candidate_map_allow_time_of_day_questions: bool = True,
        event_time_candidate_map_audit: bool = False,
        event_time_candidate_map_temporal_ambiguity_contract: bool = False,
        event_time_candidate_map_include_mention_time: bool = False,
        event_time_candidate_map_mention_time_fallback: bool = False,
        event_time_candidate_map_mention_time_fallback_min_coverage: float = 0.8,
        event_time_candidate_map_mention_time_fallback_trigger_max_coverage: float = 0.8,
        enable_weekend_relative_time: bool = False,
        structured_guide: bool = False,
        structured_guide_max_rows: int = 12,
        structured_guide_include_rows: bool = True,
        structured_guide_include_memory: bool = True,
        structured_guide_memory_hints: bool = False,
        structured_guide_max_memory_hints_per_row: int = 1,
        structured_guide_memory_hint_chars: int = 70,
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
        candidate_guide_include_memory_hints: bool = False,
        candidate_guide_max_memory_hints: int = 2,
        candidate_guide_memory_hint_chars: int = 120,
        update_conflict_guide: bool = False,
        update_conflict_guide_information_needs: tuple[str, ...] = (
            "current_state",
            "fact_lookup",
            "list_count",
            "temporal_lookup",
        ),
        update_conflict_guide_max_rows: int = 6,
        update_conflict_guide_snippet_chars: int = 180,
        memory_state_guide: bool = False,
        memory_state_guide_information_needs: tuple[str, ...] = (
            "current_state",
            "fact_lookup",
            "profile_preference",
        ),
        memory_state_guide_max_records: int = 8,
        memory_state_guide_candidate_records: int = 12,
        memory_state_guide_value_chars: int = 120,
        memory_state_guide_include_superseded: bool = True,
        memory_state_guide_require_conflict: bool = False,
        memory_state_guide_conflict_source: str = "records",
        memory_state_guide_require_active_superseded_pair: bool = False,
        memory_state_guide_require_slot_overlap: bool = False,
        memory_state_guide_require_stateful_slot: bool = False,
        memory_value_slot_guide: bool = False,
        memory_value_slot_guide_information_needs: tuple[str, ...] = (
            "current_state",
            "fact_lookup",
            "profile_preference",
        ),
        memory_value_slot_guide_max_slots: int = 4,
        memory_value_slot_guide_max_values: int = 6,
        memory_value_slot_guide_memory_types: tuple[str, ...] = (),
        memory_operation_plan_guide: bool = False,
        memory_operation_plan_guide_information_needs: tuple[str, ...] = (
            "current_state",
            "profile_preference",
        ),
        memory_operation_plan_guide_max_plans: int = 3,
        memory_operation_plan_guide_max_values: int = 4,
        memory_operation_plan_guide_value_chars: int = 90,
        memory_operation_plan_guide_render_values: bool = True,
        memory_operation_plan_guide_require_readiness: bool = False,
        memory_operation_plan_guide_required_readiness_modes: tuple[str, ...] = (
            MEMORY_OPERATION_PLAN_REQUIRED_READINESS_MODES
        ),
        memory_operation_context_organizer: bool = False,
        memory_operation_context_organizer_information_needs: tuple[str, ...] = (
            "current_state",
        ),
        memory_operation_context_organizer_max_plans: int = 4,
        memory_operation_readiness_audit: bool = False,
        memory_operation_readiness_audit_information_needs: tuple[str, ...] = (
            "current_state",
        ),
        memory_operation_readiness_audit_max_plans: int = 4,
        memory_workspace_plan: bool = False,
        memory_workspace_plan_information_needs: tuple[str, ...] = (
            "current_state",
            "fact_lookup",
            "list_count",
            "profile_preference",
            "temporal_lookup",
        ),
        memory_workspace_plan_max_groups: int = 4,
        memory_workspace_plan_max_values: int = 3,
        memory_workspace_plan_value_chars: int = 100,
        profile_activation_guide: bool = False,
        profile_activation_guide_information_needs: tuple[str, ...] = (
            "profile_preference",
        ),
        profile_activation_guide_max_records: int = 4,
        profile_activation_guide_value_chars: int = 160,
        operation_workpad: bool = False,
        operation_workpad_information_needs: tuple[str, ...] = (
            DEFAULT_STRUCTURED_ANSWER_CONTRACT_NEEDS
        ),
        operation_workpad_question_gate: bool = False,
        personalized_advice_contract: bool = False,
        current_state_update_contract: bool = False,
        dialogue_inference_contract: bool = False,
        grounded_inference_contract: bool = False,
        grounded_inference_gate: str = "broad",
        temporal_order_contract: bool = False,
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
        tail_row_text_mode: str = "full",
        tail_row_text_after_rank: int = 0,
        tail_max_row_text_chars: int = 0,
        max_memory_records: int = 12,
        memory_context_newlines_after_blocks: int = 3,
        prompt_mode: str = "default",
        route_overrides: Mapping[str, Mapping[str, Any]] | None = None,
    ):
        self._max_evidence_items = max_evidence_items
        self._max_evidence_chars = max_evidence_chars
        self._answer_style = answer_style
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
        self._event_timeline = bool(event_timeline)
        self._event_timeline_information_needs = _validate_information_needs(
            event_timeline_information_needs,
            field_name="event_timeline_information_needs",
        )
        self._event_timeline_max_rows = max(2, int(event_timeline_max_rows))
        self._event_timeline_snippet_chars = max(80, int(event_timeline_snippet_chars))
        self._event_time_candidate_manifest = bool(event_time_candidate_manifest)
        self._event_time_candidate_manifest_information_needs = (
            _validate_information_needs(
                event_time_candidate_manifest_information_needs,
                field_name="event_time_candidate_manifest_information_needs",
            )
        )
        self._event_time_candidate_manifest_max_rows = max(
            2, int(event_time_candidate_manifest_max_rows)
        )
        self._event_time_candidate_manifest_snippet_chars = max(
            80, int(event_time_candidate_manifest_snippet_chars)
        )
        self._event_time_candidate_manifest_question_gate = bool(
            event_time_candidate_manifest_question_gate
        )
        self._event_time_candidate_manifest_grouped_view = bool(
            event_time_candidate_manifest_grouped_view
        )
        self._event_time_candidate_manifest_max_groups = max(
            1, int(event_time_candidate_manifest_max_groups)
        )
        self._event_time_candidate_map = bool(event_time_candidate_map)
        self._event_time_candidate_map_information_needs = _validate_information_needs(
            event_time_candidate_map_information_needs,
            field_name="event_time_candidate_map_information_needs",
        )
        self._event_time_candidate_map_max_groups = max(
            1, int(event_time_candidate_map_max_groups)
        )
        self._event_time_candidate_map_snippet_chars = max(
            80, int(event_time_candidate_map_snippet_chars)
        )
        self._event_time_candidate_map_min_terms = max(
            1, int(event_time_candidate_map_min_terms)
        )
        self._event_time_candidate_map_min_coverage = min(
            1.0, max(0.0, float(event_time_candidate_map_min_coverage))
        )
        self._event_time_candidate_map_allowed_time_kinds = tuple(
            str(kind) for kind in event_time_candidate_map_allowed_time_kinds
        ) or ("exact_today", "explicit_date", "relative_phrase")
        self._event_time_candidate_map_strip_context_wrappers = bool(
            event_time_candidate_map_strip_context_wrappers
        )
        self._event_time_candidate_map_segment_local_context = bool(
            event_time_candidate_map_segment_local_context
        )
        self._event_time_candidate_map_rank_by_coverage = bool(
            event_time_candidate_map_rank_by_coverage
        )
        self._event_time_candidate_map_normalize_terms = bool(
            event_time_candidate_map_normalize_terms
        )
        self._event_time_candidate_map_exact_today_min_coverage = (
            None
            if event_time_candidate_map_exact_today_min_coverage is None
            else min(
                1.0,
                max(0.0, float(event_time_candidate_map_exact_today_min_coverage)),
            )
        )
        self._event_time_candidate_map_require_role_match = bool(
            event_time_candidate_map_require_role_match
        )
        self._event_time_candidate_map_allow_time_of_day_questions = bool(
            event_time_candidate_map_allow_time_of_day_questions
        )
        self._event_time_candidate_map_audit = bool(event_time_candidate_map_audit)
        self._event_time_candidate_map_temporal_ambiguity_contract = bool(
            event_time_candidate_map_temporal_ambiguity_contract
        )
        self._event_time_candidate_map_include_mention_time = bool(
            event_time_candidate_map_include_mention_time
        )
        self._event_time_candidate_map_mention_time_fallback = bool(
            event_time_candidate_map_mention_time_fallback
        )
        self._event_time_candidate_map_mention_time_fallback_min_coverage = min(
            1.0,
            max(0.0, float(event_time_candidate_map_mention_time_fallback_min_coverage)),
        )
        self._event_time_candidate_map_mention_time_fallback_trigger_max_coverage = (
            min(
                1.0,
                max(
                    0.0,
                    float(
                        event_time_candidate_map_mention_time_fallback_trigger_max_coverage
                    ),
                ),
            )
        )
        self._enable_weekend_relative_time = bool(enable_weekend_relative_time)
        self._structured_guide = structured_guide
        self._structured_guide_max_rows = max(1, structured_guide_max_rows)
        self._structured_guide_include_rows = structured_guide_include_rows
        self._structured_guide_include_memory = structured_guide_include_memory
        self._structured_guide_memory_hints = bool(structured_guide_memory_hints)
        self._structured_guide_max_memory_hints_per_row = max(
            0, int(structured_guide_max_memory_hints_per_row)
        )
        self._structured_guide_memory_hint_chars = max(
            30, int(structured_guide_memory_hint_chars)
        )
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
        self._candidate_guide_include_memory_hints = bool(
            candidate_guide_include_memory_hints
        )
        self._candidate_guide_max_memory_hints = max(
            0, int(candidate_guide_max_memory_hints)
        )
        self._candidate_guide_memory_hint_chars = max(
            40, int(candidate_guide_memory_hint_chars)
        )
        self._update_conflict_guide = update_conflict_guide
        self._update_conflict_guide_information_needs = _validate_information_needs(
            update_conflict_guide_information_needs,
            field_name="update_conflict_guide_information_needs",
        )
        self._update_conflict_guide_max_rows = max(
            2, int(update_conflict_guide_max_rows)
        )
        self._update_conflict_guide_snippet_chars = max(
            80, int(update_conflict_guide_snippet_chars)
        )
        self._memory_state_guide = bool(memory_state_guide)
        self._memory_state_guide_information_needs = _validate_information_needs(
            memory_state_guide_information_needs,
            field_name="memory_state_guide_information_needs",
        )
        self._memory_state_guide_max_records = max(
            1, int(memory_state_guide_max_records)
        )
        self._memory_state_guide_candidate_records = max(
            1, int(memory_state_guide_candidate_records)
        )
        self._memory_state_guide_value_chars = max(
            40, int(memory_state_guide_value_chars)
        )
        self._memory_state_guide_include_superseded = bool(
            memory_state_guide_include_superseded
        )
        self._memory_state_guide_require_conflict = bool(
            memory_state_guide_require_conflict
        )
        self._memory_state_guide_conflict_source = (
            _validate_memory_state_guide_conflict_source(
                memory_state_guide_conflict_source
            )
        )
        self._memory_state_guide_require_active_superseded_pair = bool(
            memory_state_guide_require_active_superseded_pair
        )
        self._memory_state_guide_require_slot_overlap = bool(
            memory_state_guide_require_slot_overlap
        )
        self._memory_state_guide_require_stateful_slot = bool(
            memory_state_guide_require_stateful_slot
        )
        self._memory_value_slot_guide = bool(memory_value_slot_guide)
        self._memory_value_slot_guide_information_needs = _validate_information_needs(
            memory_value_slot_guide_information_needs,
            field_name="memory_value_slot_guide_information_needs",
        )
        self._memory_value_slot_guide_max_slots = max(
            1, int(memory_value_slot_guide_max_slots)
        )
        self._memory_value_slot_guide_max_values = max(
            1, int(memory_value_slot_guide_max_values)
        )
        self._memory_value_slot_guide_memory_types = tuple(
            str(value).strip().lower()
            for value in memory_value_slot_guide_memory_types
            if str(value).strip()
        )
        self._memory_operation_plan_guide = bool(memory_operation_plan_guide)
        self._memory_operation_plan_guide_information_needs = (
            _validate_information_needs(
                memory_operation_plan_guide_information_needs,
                field_name="memory_operation_plan_guide_information_needs",
            )
        )
        self._memory_operation_plan_guide_max_plans = max(
            1, int(memory_operation_plan_guide_max_plans)
        )
        self._memory_operation_plan_guide_max_values = max(
            1, int(memory_operation_plan_guide_max_values)
        )
        self._memory_operation_plan_guide_value_chars = max(
            40, int(memory_operation_plan_guide_value_chars)
        )
        self._memory_operation_plan_guide_render_values = bool(
            memory_operation_plan_guide_render_values
        )
        self._memory_operation_plan_guide_require_readiness = bool(
            memory_operation_plan_guide_require_readiness
        )
        self._memory_operation_plan_guide_required_readiness_modes = (
            _validate_operation_plan_readiness_modes(
                memory_operation_plan_guide_required_readiness_modes
            )
        )
        self._memory_operation_context_organizer = bool(
            memory_operation_context_organizer
        )
        self._memory_operation_context_organizer_information_needs = (
            _validate_information_needs(
                memory_operation_context_organizer_information_needs,
                field_name="memory_operation_context_organizer_information_needs",
            )
        )
        self._memory_operation_context_organizer_max_plans = max(
            1, int(memory_operation_context_organizer_max_plans)
        )
        self._memory_operation_readiness_audit = bool(
            memory_operation_readiness_audit
        )
        self._memory_operation_readiness_audit_information_needs = (
            _validate_information_needs(
                memory_operation_readiness_audit_information_needs,
                field_name="memory_operation_readiness_audit_information_needs",
            )
        )
        self._memory_operation_readiness_audit_max_plans = max(
            1, int(memory_operation_readiness_audit_max_plans)
        )
        self._memory_workspace_plan = bool(memory_workspace_plan)
        self._memory_workspace_plan_information_needs = _validate_information_needs(
            memory_workspace_plan_information_needs,
            field_name="memory_workspace_plan_information_needs",
        )
        self._memory_workspace_plan_max_groups = max(
            1, int(memory_workspace_plan_max_groups)
        )
        self._memory_workspace_plan_max_values = max(
            1, int(memory_workspace_plan_max_values)
        )
        self._memory_workspace_plan_value_chars = max(
            40, int(memory_workspace_plan_value_chars)
        )
        self._profile_activation_guide = bool(profile_activation_guide)
        self._profile_activation_guide_information_needs = _validate_information_needs(
            profile_activation_guide_information_needs,
            field_name="profile_activation_guide_information_needs",
        )
        self._profile_activation_guide_max_records = max(
            1, int(profile_activation_guide_max_records)
        )
        self._profile_activation_guide_value_chars = max(
            60, int(profile_activation_guide_value_chars)
        )
        self._operation_workpad = operation_workpad
        self._operation_workpad_information_needs = _validate_information_needs(
            operation_workpad_information_needs,
            field_name="operation_workpad_information_needs",
        )
        self._operation_workpad_question_gate = operation_workpad_question_gate
        self._personalized_advice_contract = personalized_advice_contract
        self._current_state_update_contract = current_state_update_contract
        self._dialogue_inference_contract = dialogue_inference_contract
        self._grounded_inference_contract = grounded_inference_contract
        if grounded_inference_gate not in {"broad", "modal_only"}:
            raise ValueError(
                f"Unsupported grounded_inference_gate: {grounded_inference_gate}"
            )
        self._grounded_inference_gate = grounded_inference_gate
        self._temporal_order_contract = temporal_order_contract
        if context_layout not in SUPPORTED_CONTEXT_LAYOUTS:
            raise ValueError(f"Unsupported context_layout: {context_layout}")
        self._context_layout = context_layout
        if evidence_order not in EVIDENCE_ORDER_MODES:
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
        if tail_row_text_mode not in {"full", "query_snippet", "role_query_snippet"}:
            raise ValueError(f"Unsupported tail_row_text_mode: {tail_row_text_mode}")
        self._tail_row_text_mode = tail_row_text_mode
        self._tail_row_text_after_rank = max(0, int(tail_row_text_after_rank))
        self._tail_max_row_text_chars = tail_max_row_text_chars or self._max_row_text_chars
        self._max_memory_records = max(0, max_memory_records)
        self._memory_context_newlines_after_blocks = max(
            2, int(memory_context_newlines_after_blocks)
        )
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
        memory_state_guide_records: tuple[MemoryRecord, ...] | None = None,
        memory_state_conflict_manifest: Mapping[str, Any] | None = None,
        memory_scalar_value_manifest: Mapping[str, Any] | None = None,
        memory_object_index: Mapping[str, Any] | None = None,
        memory_workspace_manifest: Mapping[str, Any] | None = None,
        memory_operation_plan: Mapping[str, Any] | None = None,
        memory_query_readiness_manifest: Mapping[str, Any] | None = None,
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

        evidence_order = route_settings["evidence_order"]
        selection_evidence_order = (
            "retrieval"
            if evidence_order in FIXED_SET_EVIDENCE_ORDER_MODES
            else evidence_order
        )
        ordered_candidates = _order_rows(
            tuple(candidates),
            question=question,
            route=route,
            evidence_order=selection_evidence_order,
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

        if evidence_order == "fixed_set_memory_source_interleave":
            rows = list(
                _order_rows(
                    tuple(rows),
                    question=question,
                    route=route,
                    evidence_order="memory_source_interleave",
                    memory_records=tuple(memory_records),
                    source_anchor_keep=route_settings["source_anchor_keep"],
                    source_anchor_memory_rows=route_settings[
                        "source_anchor_memory_rows"
                    ],
                    source_anchor_per_session=route_settings[
                        "source_anchor_per_session"
                    ],
                    source_anchor_session_rows=route_settings[
                        "source_anchor_session_rows"
                    ],
                )
            )

        ordered_memory_records = _order_memory_records(
            tuple(memory_records),
            question=question,
            route=route,
            memory_order=self._memory_order,
        )
        selected_memory_records = ordered_memory_records[
            : route_settings["max_memory_records"]
        ]
        memory_state_guide_source_records = (
            tuple(memory_state_guide_records)
            if memory_state_guide_records is not None
            else tuple(memory_records)
        )
        ordered_memory_state_guide_records = _order_memory_records(
            memory_state_guide_source_records,
            question=question,
            route=route,
            memory_order=self._memory_order,
        )
        selected_memory_state_guide_records = ordered_memory_state_guide_records[
            : route_settings["memory_state_guide_candidate_records"]
        ]
        laid_out_rows = _layout_rows(
            tuple(rows),
            context_layout=route_settings["context_layout"],
        )
        context_organizer_trace: dict[str, Any] | None = None
        if (
            route_settings["memory_operation_context_organizer"]
            and route.information_need
            in self._memory_operation_context_organizer_information_needs
        ):
            laid_out_rows, context_organizer_trace = (
                _memory_operation_context_organizer(
                    question=question,
                    route=route,
                    rows=laid_out_rows,
                    memory_operation_plan=memory_operation_plan,
                    memory_query_readiness_manifest=memory_query_readiness_manifest,
                    max_plans=route_settings[
                        "memory_operation_context_organizer_max_plans"
                    ],
                    required_readiness_modes=route_settings[
                        "memory_operation_plan_guide_required_readiness_modes"
                    ],
                )
            )

        prompt = _build_prompt(
            question,
            question_time,
            route,
            tuple(selected_memory_records),
            laid_out_rows,
            answer_style=self._answer_style,
            temporal_workpad=self._temporal_workpad,
            temporal_text_normalization=self._temporal_text_normalization,
            temporal_event_contract=self._temporal_event_contract,
            temporal_workpad_scope=self._temporal_workpad_scope,
            temporal_workpad_max_rows=self._temporal_workpad_max_rows,
            temporal_workpad_max_pairs=self._temporal_workpad_max_pairs,
            event_timeline=(
                self._event_timeline
                and route.information_need in self._event_timeline_information_needs
                and _asks_chronological_order(question)
            ),
            event_timeline_max_rows=self._event_timeline_max_rows,
            event_timeline_snippet_chars=self._event_timeline_snippet_chars,
            event_time_candidate_map=(
                route_settings["event_time_candidate_map"]
                and route.information_need
                in self._event_time_candidate_map_information_needs
                and _asks_event_time_candidate_map(
                    question,
                    route,
                    allow_time_of_day_questions=route_settings[
                        "event_time_candidate_map_allow_time_of_day_questions"
                    ],
                )
            ),
            event_time_candidate_map_max_groups=route_settings[
                "event_time_candidate_map_max_groups"
            ],
            event_time_candidate_map_snippet_chars=route_settings[
                "event_time_candidate_map_snippet_chars"
            ],
            event_time_candidate_map_min_terms=route_settings[
                "event_time_candidate_map_min_terms"
            ],
            event_time_candidate_map_min_coverage=route_settings[
                "event_time_candidate_map_min_coverage"
            ],
            event_time_candidate_map_allowed_time_kinds=route_settings[
                "event_time_candidate_map_allowed_time_kinds"
            ],
            event_time_candidate_map_strip_context_wrappers=route_settings[
                "event_time_candidate_map_strip_context_wrappers"
            ],
            event_time_candidate_map_segment_local_context=route_settings[
                "event_time_candidate_map_segment_local_context"
            ],
            event_time_candidate_map_rank_by_coverage=route_settings[
                "event_time_candidate_map_rank_by_coverage"
            ],
            event_time_candidate_map_normalize_terms=route_settings[
                "event_time_candidate_map_normalize_terms"
            ],
            event_time_candidate_map_exact_today_min_coverage=route_settings[
                "event_time_candidate_map_exact_today_min_coverage"
            ],
            event_time_candidate_map_require_role_match=route_settings[
                "event_time_candidate_map_require_role_match"
            ],
            event_time_candidate_map_temporal_ambiguity_contract=route_settings[
                "event_time_candidate_map_temporal_ambiguity_contract"
            ],
            event_time_candidate_map_include_mention_time=route_settings[
                "event_time_candidate_map_include_mention_time"
            ],
            event_time_candidate_map_mention_time_fallback=route_settings[
                "event_time_candidate_map_mention_time_fallback"
            ],
            event_time_candidate_map_mention_time_fallback_min_coverage=(
                route_settings[
                    "event_time_candidate_map_mention_time_fallback_min_coverage"
                ]
            ),
            event_time_candidate_map_mention_time_fallback_trigger_max_coverage=(
                route_settings[
                    "event_time_candidate_map_mention_time_fallback_trigger_max_coverage"
                ]
            ),
            enable_weekend_relative_time=route_settings[
                "enable_weekend_relative_time"
            ],
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
            structured_guide_memory_hints=route_settings[
                "structured_guide_memory_hints"
            ],
            structured_guide_max_memory_hints_per_row=route_settings[
                "structured_guide_max_memory_hints_per_row"
            ],
            structured_guide_memory_hint_chars=route_settings[
                "structured_guide_memory_hint_chars"
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
            candidate_guide_include_memory_hints=route_settings[
                "candidate_guide_include_memory_hints"
            ],
            candidate_guide_max_memory_hints=route_settings[
                "candidate_guide_max_memory_hints"
            ],
            candidate_guide_memory_hint_chars=route_settings[
                "candidate_guide_memory_hint_chars"
            ],
            update_conflict_guide=(
                route_settings["update_conflict_guide"]
                and route.information_need
                in self._update_conflict_guide_information_needs
            ),
            update_conflict_guide_max_rows=route_settings[
                "update_conflict_guide_max_rows"
            ],
            update_conflict_guide_snippet_chars=route_settings[
                "update_conflict_guide_snippet_chars"
            ],
            memory_state_guide=(
                route_settings["memory_state_guide"]
                and route.information_need in self._memory_state_guide_information_needs
            ),
            memory_state_guide_max_records=route_settings[
                "memory_state_guide_max_records"
            ],
            memory_state_guide_records=selected_memory_state_guide_records,
            memory_state_conflict_manifest=memory_state_conflict_manifest,
            memory_scalar_value_manifest=memory_scalar_value_manifest,
            memory_object_index=memory_object_index,
            memory_workspace_manifest=memory_workspace_manifest,
            memory_operation_plan=memory_operation_plan,
            memory_query_readiness_manifest=memory_query_readiness_manifest,
            memory_operation_plan_guide=(
                route_settings["memory_operation_plan_guide"]
                and route.information_need
                in self._memory_operation_plan_guide_information_needs
            ),
            memory_operation_plan_guide_max_plans=route_settings[
                "memory_operation_plan_guide_max_plans"
            ],
            memory_operation_plan_guide_max_values=route_settings[
                "memory_operation_plan_guide_max_values"
            ],
            memory_operation_plan_guide_value_chars=route_settings[
                "memory_operation_plan_guide_value_chars"
            ],
            memory_operation_plan_guide_render_values=route_settings[
                "memory_operation_plan_guide_render_values"
            ],
            memory_operation_plan_guide_require_readiness=route_settings[
                "memory_operation_plan_guide_require_readiness"
            ],
            memory_operation_plan_guide_required_readiness_modes=route_settings[
                "memory_operation_plan_guide_required_readiness_modes"
            ],
            memory_workspace_plan=(
                route_settings["memory_workspace_plan"]
                and route.information_need
                in self._memory_workspace_plan_information_needs
            ),
            memory_workspace_plan_max_groups=route_settings[
                "memory_workspace_plan_max_groups"
            ],
            memory_workspace_plan_max_values=route_settings[
                "memory_workspace_plan_max_values"
            ],
            memory_workspace_plan_value_chars=route_settings[
                "memory_workspace_plan_value_chars"
            ],
            memory_state_guide_candidate_records=route_settings[
                "memory_state_guide_candidate_records"
            ],
            memory_state_guide_value_chars=route_settings[
                "memory_state_guide_value_chars"
            ],
            memory_state_guide_include_superseded=route_settings[
                "memory_state_guide_include_superseded"
            ],
            memory_state_guide_require_conflict=route_settings[
                "memory_state_guide_require_conflict"
            ],
            memory_state_guide_conflict_source=route_settings[
                "memory_state_guide_conflict_source"
            ],
            memory_state_guide_require_active_superseded_pair=route_settings[
                "memory_state_guide_require_active_superseded_pair"
            ],
            memory_state_guide_require_slot_overlap=route_settings[
                "memory_state_guide_require_slot_overlap"
            ],
            memory_state_guide_require_stateful_slot=route_settings[
                "memory_state_guide_require_stateful_slot"
            ],
            memory_value_slot_guide=(
                route_settings["memory_value_slot_guide"]
                and route.information_need
                in self._memory_value_slot_guide_information_needs
            ),
            memory_value_slot_guide_max_slots=route_settings[
                "memory_value_slot_guide_max_slots"
            ],
            memory_value_slot_guide_max_values=route_settings[
                "memory_value_slot_guide_max_values"
            ],
            memory_value_slot_guide_memory_types=route_settings[
                "memory_value_slot_guide_memory_types"
            ],
            profile_activation_guide=(
                route_settings["profile_activation_guide"]
                and route.information_need
                in self._profile_activation_guide_information_needs
            ),
            profile_activation_guide_max_records=route_settings[
                "profile_activation_guide_max_records"
            ],
            profile_activation_guide_value_chars=route_settings[
                "profile_activation_guide_value_chars"
            ],
            evidence_report_max_items=self._evidence_report_max_items,
            evidence_report_detail=route_settings["evidence_report_detail"],
            operation_workpad=(
                self._operation_workpad
                and route.information_need in self._operation_workpad_information_needs
                and _should_apply_operation_workpad(
                    question,
                    route,
                    question_gate=self._operation_workpad_question_gate,
                )
            ),
            personalized_advice_contract=(
                self._personalized_advice_contract
                and _is_personalized_advice_question(question)
            ),
            current_state_update_contract=route_settings[
                "current_state_update_contract"
            ],
            dialogue_inference_contract=route_settings["dialogue_inference_contract"],
            grounded_inference_contract=(
                route_settings["grounded_inference_contract"]
                and _is_grounded_inference_question(
                    question,
                    gate=route_settings["grounded_inference_gate"],
                )
            ),
            temporal_order_contract=route_settings["temporal_order_contract"],
            context_layout=route_settings["context_layout"],
            memory_layout=self._memory_layout,
            row_text_mode=route_settings["row_text_mode"],
            max_row_text_chars=route_settings["max_row_text_chars"],
            tail_row_text_mode=route_settings["tail_row_text_mode"],
            tail_row_text_after_rank=route_settings["tail_row_text_after_rank"],
            tail_max_row_text_chars=route_settings["tail_max_row_text_chars"],
            memory_context_newlines_after_blocks=(
                self._memory_context_newlines_after_blocks
            ),
            prompt_mode=self._prompt_mode,
        )
        diagnostics: dict[str, Any] = {}
        if context_organizer_trace is not None:
            diagnostics["memory_operation_context_organizer"] = (
                context_organizer_trace
            )
        if (
            route_settings["memory_state_guide"]
            and route.information_need in self._memory_state_guide_information_needs
        ):
            memory_state_ledger = _source_backed_memory_state_ledger(
                question=question,
                route=route,
                rows=laid_out_rows,
                memory_records=selected_memory_state_guide_records,
                max_records=route_settings["memory_state_guide_candidate_records"],
                max_value_chars=route_settings["memory_state_guide_value_chars"],
            )
            if memory_state_ledger["applied"]:
                diagnostics["source_backed_memory_state_ledger"] = memory_state_ledger
        if (
            route_settings["memory_operation_readiness_audit"]
            and route.information_need
            in self._memory_operation_readiness_audit_information_needs
        ):
            diagnostics["memory_operation_readiness_audit"] = (
                _memory_operation_readiness_audit(
                    question=question,
                    route=route,
                    rows=laid_out_rows,
                    memory_operation_plan=memory_operation_plan,
                    memory_query_readiness_manifest=memory_query_readiness_manifest,
                    max_plans=route_settings[
                        "memory_operation_readiness_audit_max_plans"
                    ],
                    required_readiness_modes=route_settings[
                        "memory_operation_plan_guide_required_readiness_modes"
                    ],
                )
            )
        if self._event_time_candidate_manifest:
            diagnostics["event_time_candidate_manifest"] = (
                _event_time_candidate_manifest(
                    question=question,
                    route=route,
                    rows=laid_out_rows,
                    information_needs=(
                        self._event_time_candidate_manifest_information_needs
                    ),
                    max_rows=self._event_time_candidate_manifest_max_rows,
                    snippet_chars=self._event_time_candidate_manifest_snippet_chars,
                    question_gate=self._event_time_candidate_manifest_question_gate,
                    grouped_view=self._event_time_candidate_manifest_grouped_view,
                    max_groups=self._event_time_candidate_manifest_max_groups,
                    enable_weekend_relative_time=route_settings[
                        "enable_weekend_relative_time"
                    ],
                )
            )
        if route_settings["event_time_candidate_map_audit"]:
            diagnostics["event_time_candidate_map_audit"] = (
                _event_time_candidate_map_audit(
                    question=question,
                    route=route,
                    rows=laid_out_rows,
                    max_groups=route_settings["event_time_candidate_map_max_groups"],
                    snippet_chars=route_settings[
                        "event_time_candidate_map_snippet_chars"
                    ],
                    min_terms=route_settings["event_time_candidate_map_min_terms"],
                    min_coverage=route_settings[
                        "event_time_candidate_map_min_coverage"
                    ],
                    allowed_time_kinds=route_settings[
                        "event_time_candidate_map_allowed_time_kinds"
                    ],
                    strip_context_wrappers=route_settings[
                        "event_time_candidate_map_strip_context_wrappers"
                    ],
                    segment_local_context=route_settings[
                        "event_time_candidate_map_segment_local_context"
                    ],
                    rank_by_coverage=route_settings[
                        "event_time_candidate_map_rank_by_coverage"
                    ],
                    normalize_terms=route_settings[
                        "event_time_candidate_map_normalize_terms"
                    ],
                    exact_today_min_coverage=route_settings[
                        "event_time_candidate_map_exact_today_min_coverage"
                    ],
                    require_role_match=route_settings[
                        "event_time_candidate_map_require_role_match"
                    ],
                    allow_time_of_day_questions=route_settings[
                        "event_time_candidate_map_allow_time_of_day_questions"
                    ],
                    enable_weekend_relative_time=route_settings[
                        "enable_weekend_relative_time"
                    ],
                )
            )
        return CompiledContext(
            question=question,
            question_time=question_time,
            route=route,
            evidence_rows=laid_out_rows,
            prompt=prompt,
            context_chars=len(prompt),
            memory_records=tuple(selected_memory_records),
            diagnostics=diagnostics,
        )

    def _settings_for_route(self, route: RouteResult) -> dict[str, Any]:
        settings: dict[str, Any] = {
            "candidate_guide": self._candidate_guide,
            "candidate_guide_include_memory_hints": (
                self._candidate_guide_include_memory_hints
            ),
            "candidate_guide_max_memory_hints": (
                self._candidate_guide_max_memory_hints
            ),
            "candidate_guide_max_rows": self._candidate_guide_max_rows,
            "candidate_guide_memory_hint_chars": (
                self._candidate_guide_memory_hint_chars
            ),
            "candidate_guide_snippet_chars": self._candidate_guide_snippet_chars,
            "update_conflict_guide": self._update_conflict_guide,
            "update_conflict_guide_max_rows": self._update_conflict_guide_max_rows,
            "update_conflict_guide_snippet_chars": (
                self._update_conflict_guide_snippet_chars
            ),
            "memory_state_guide": self._memory_state_guide,
            "memory_state_guide_max_records": self._memory_state_guide_max_records,
            "memory_state_guide_candidate_records": (
                self._memory_state_guide_candidate_records
            ),
            "memory_state_guide_value_chars": self._memory_state_guide_value_chars,
            "memory_state_guide_include_superseded": (
                self._memory_state_guide_include_superseded
            ),
            "memory_state_guide_require_conflict": (
                self._memory_state_guide_require_conflict
            ),
            "memory_state_guide_conflict_source": (
                self._memory_state_guide_conflict_source
            ),
            "memory_state_guide_require_active_superseded_pair": (
                self._memory_state_guide_require_active_superseded_pair
            ),
            "memory_state_guide_require_slot_overlap": (
                self._memory_state_guide_require_slot_overlap
            ),
            "memory_state_guide_require_stateful_slot": (
                self._memory_state_guide_require_stateful_slot
            ),
            "memory_value_slot_guide": self._memory_value_slot_guide,
            "memory_value_slot_guide_max_slots": (
                self._memory_value_slot_guide_max_slots
            ),
            "memory_value_slot_guide_max_values": (
                self._memory_value_slot_guide_max_values
            ),
            "memory_value_slot_guide_memory_types": (
                self._memory_value_slot_guide_memory_types
            ),
            "memory_operation_plan_guide": self._memory_operation_plan_guide,
            "memory_operation_plan_guide_max_plans": (
                self._memory_operation_plan_guide_max_plans
            ),
            "memory_operation_plan_guide_max_values": (
                self._memory_operation_plan_guide_max_values
            ),
            "memory_operation_plan_guide_value_chars": (
                self._memory_operation_plan_guide_value_chars
            ),
            "memory_operation_plan_guide_render_values": (
                self._memory_operation_plan_guide_render_values
            ),
            "memory_operation_plan_guide_require_readiness": (
                self._memory_operation_plan_guide_require_readiness
            ),
            "memory_operation_plan_guide_required_readiness_modes": (
                self._memory_operation_plan_guide_required_readiness_modes
            ),
            "memory_operation_context_organizer": (
                self._memory_operation_context_organizer
            ),
            "memory_operation_context_organizer_max_plans": (
                self._memory_operation_context_organizer_max_plans
            ),
            "memory_operation_readiness_audit": (
                self._memory_operation_readiness_audit
            ),
            "memory_operation_readiness_audit_max_plans": (
                self._memory_operation_readiness_audit_max_plans
            ),
            "memory_workspace_plan": self._memory_workspace_plan,
            "memory_workspace_plan_max_groups": (
                self._memory_workspace_plan_max_groups
            ),
            "memory_workspace_plan_max_values": (
                self._memory_workspace_plan_max_values
            ),
            "memory_workspace_plan_value_chars": (
                self._memory_workspace_plan_value_chars
            ),
            "profile_activation_guide": self._profile_activation_guide,
            "profile_activation_guide_max_records": (
                self._profile_activation_guide_max_records
            ),
            "profile_activation_guide_value_chars": (
                self._profile_activation_guide_value_chars
            ),
            "context_layout": self._context_layout,
            "current_state_update_contract": self._current_state_update_contract,
            "dialogue_inference_contract": self._dialogue_inference_contract,
            "evidence_order": self._evidence_order,
            "evidence_report_detail": self._evidence_report_detail,
            "event_time_candidate_map": self._event_time_candidate_map,
            "event_time_candidate_map_max_groups": (
                self._event_time_candidate_map_max_groups
            ),
            "event_time_candidate_map_snippet_chars": (
                self._event_time_candidate_map_snippet_chars
            ),
            "event_time_candidate_map_min_terms": (
                self._event_time_candidate_map_min_terms
            ),
            "event_time_candidate_map_min_coverage": (
                self._event_time_candidate_map_min_coverage
            ),
            "event_time_candidate_map_allowed_time_kinds": (
                self._event_time_candidate_map_allowed_time_kinds
            ),
            "event_time_candidate_map_strip_context_wrappers": (
                self._event_time_candidate_map_strip_context_wrappers
            ),
            "event_time_candidate_map_segment_local_context": (
                self._event_time_candidate_map_segment_local_context
            ),
            "event_time_candidate_map_rank_by_coverage": (
                self._event_time_candidate_map_rank_by_coverage
            ),
            "event_time_candidate_map_normalize_terms": (
                self._event_time_candidate_map_normalize_terms
            ),
            "event_time_candidate_map_exact_today_min_coverage": (
                self._event_time_candidate_map_exact_today_min_coverage
            ),
            "event_time_candidate_map_require_role_match": (
                self._event_time_candidate_map_require_role_match
            ),
            "event_time_candidate_map_allow_time_of_day_questions": (
                self._event_time_candidate_map_allow_time_of_day_questions
            ),
            "event_time_candidate_map_audit": self._event_time_candidate_map_audit,
            "event_time_candidate_map_temporal_ambiguity_contract": (
                self._event_time_candidate_map_temporal_ambiguity_contract
            ),
            "event_time_candidate_map_include_mention_time": (
                self._event_time_candidate_map_include_mention_time
            ),
            "event_time_candidate_map_mention_time_fallback": (
                self._event_time_candidate_map_mention_time_fallback
            ),
            "event_time_candidate_map_mention_time_fallback_min_coverage": (
                self._event_time_candidate_map_mention_time_fallback_min_coverage
            ),
            "event_time_candidate_map_mention_time_fallback_trigger_max_coverage": (
                self._event_time_candidate_map_mention_time_fallback_trigger_max_coverage
            ),
            "enable_weekend_relative_time": self._enable_weekend_relative_time,
            "grounded_inference_contract": self._grounded_inference_contract,
            "grounded_inference_gate": self._grounded_inference_gate,
            "max_evidence_chars": self._max_evidence_chars,
            "max_evidence_items": self._max_evidence_items,
            "max_memory_records": self._max_memory_records,
            "max_row_text_chars": self._max_row_text_chars,
            "operation_workpad_question_gate": self._operation_workpad_question_gate,
            "row_text_mode": self._row_text_mode,
            "tail_max_row_text_chars": self._tail_max_row_text_chars,
            "tail_row_text_after_rank": self._tail_row_text_after_rank,
            "tail_row_text_mode": self._tail_row_text_mode,
            "source_anchor_keep": self._source_anchor_keep,
            "source_anchor_memory_rows": self._source_anchor_memory_rows,
            "source_anchor_per_session": self._source_anchor_per_session,
            "source_anchor_session_rows": self._source_anchor_session_rows,
            "structured_guide_include_memory": self._structured_guide_include_memory,
            "structured_guide_include_rows": self._structured_guide_include_rows,
            "structured_guide_max_memory_hints_per_row": (
                self._structured_guide_max_memory_hints_per_row
            ),
            "structured_guide_memory_hint_chars": (
                self._structured_guide_memory_hint_chars
            ),
            "structured_guide_memory_hints": self._structured_guide_memory_hints,
            "structured_guide_max_rows": self._structured_guide_max_rows,
            "temporal_order_contract": self._temporal_order_contract,
            "event_timeline": self._event_timeline,
            "event_timeline_information_needs": self._event_timeline_information_needs,
            "event_timeline_max_rows": self._event_timeline_max_rows,
            "event_timeline_snippet_chars": self._event_timeline_snippet_chars,
            "event_time_candidate_manifest": self._event_time_candidate_manifest,
            "event_time_candidate_manifest_information_needs": (
                self._event_time_candidate_manifest_information_needs
            ),
            "event_time_candidate_manifest_max_rows": (
                self._event_time_candidate_manifest_max_rows
            ),
            "event_time_candidate_manifest_question_gate": (
                self._event_time_candidate_manifest_question_gate
            ),
            "event_time_candidate_manifest_snippet_chars": (
                self._event_time_candidate_manifest_snippet_chars
            ),
            "event_time_candidate_manifest_grouped_view": (
                self._event_time_candidate_manifest_grouped_view
            ),
            "event_time_candidate_manifest_max_groups": (
                self._event_time_candidate_manifest_max_groups
            ),
        }
        settings.update(self._route_overrides.get(route.information_need, {}))
        return settings


def _validate_memory_state_guide_conflict_source(value: str) -> str:
    if value not in MEMORY_STATE_GUIDE_CONFLICT_SOURCES:
        raise ValueError(
            "Unsupported memory_state_guide_conflict_source: "
            f"{value}. Expected one of {sorted(MEMORY_STATE_GUIDE_CONFLICT_SOURCES)}"
        )
    return value


def _validate_operation_plan_readiness_modes(value: object) -> tuple[str, ...]:
    if value is None:
        return MEMORY_OPERATION_PLAN_REQUIRED_READINESS_MODES
    if isinstance(value, str):
        raw_modes = (value,)
    elif isinstance(value, Iterable):
        raw_modes = tuple(value)
    else:
        raw_modes = (value,)
    modes = tuple(
        str(mode).strip()
        for mode in raw_modes
        if str(mode).strip()
    )
    return modes or MEMORY_OPERATION_PLAN_REQUIRED_READINESS_MODES


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
        if "structured_guide_memory_hints" in raw_overrides:
            overrides["structured_guide_memory_hints"] = bool(
                raw_overrides["structured_guide_memory_hints"]
            )
        if "structured_guide_max_memory_hints_per_row" in raw_overrides:
            overrides["structured_guide_max_memory_hints_per_row"] = max(
                0, int(raw_overrides["structured_guide_max_memory_hints_per_row"])
            )
        if "structured_guide_memory_hint_chars" in raw_overrides:
            overrides["structured_guide_memory_hint_chars"] = max(
                30, int(raw_overrides["structured_guide_memory_hint_chars"])
            )
        if "row_text_mode" in raw_overrides:
            row_text_mode = str(raw_overrides["row_text_mode"])
            if row_text_mode not in {"full", "query_snippet", "role_query_snippet"}:
                raise ValueError(f"Unsupported row_text_mode: {row_text_mode}")
            overrides["row_text_mode"] = row_text_mode
        if "tail_row_text_mode" in raw_overrides:
            tail_row_text_mode = str(raw_overrides["tail_row_text_mode"])
            if tail_row_text_mode not in {
                "full",
                "query_snippet",
                "role_query_snippet",
            }:
                raise ValueError(
                    f"Unsupported tail_row_text_mode: {tail_row_text_mode}"
                )
            overrides["tail_row_text_mode"] = tail_row_text_mode
        if "tail_row_text_after_rank" in raw_overrides:
            overrides["tail_row_text_after_rank"] = max(
                0, int(raw_overrides["tail_row_text_after_rank"])
            )
        if "tail_max_row_text_chars" in raw_overrides:
            overrides["tail_max_row_text_chars"] = (
                int(raw_overrides["tail_max_row_text_chars"]) or 800
            )
        if "evidence_order" in raw_overrides:
            evidence_order = str(raw_overrides["evidence_order"])
            if evidence_order not in EVIDENCE_ORDER_MODES:
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
        if "event_time_candidate_map" in raw_overrides:
            overrides["event_time_candidate_map"] = bool(
                raw_overrides["event_time_candidate_map"]
            )
        if "event_time_candidate_map_max_groups" in raw_overrides:
            overrides["event_time_candidate_map_max_groups"] = max(
                1, int(raw_overrides["event_time_candidate_map_max_groups"])
            )
        if "event_time_candidate_map_snippet_chars" in raw_overrides:
            overrides["event_time_candidate_map_snippet_chars"] = max(
                80, int(raw_overrides["event_time_candidate_map_snippet_chars"])
            )
        if "event_time_candidate_map_min_terms" in raw_overrides:
            overrides["event_time_candidate_map_min_terms"] = max(
                1, int(raw_overrides["event_time_candidate_map_min_terms"])
            )
        if "event_time_candidate_map_min_coverage" in raw_overrides:
            overrides["event_time_candidate_map_min_coverage"] = min(
                1.0,
                max(0.0, float(raw_overrides["event_time_candidate_map_min_coverage"])),
            )
        if "event_time_candidate_map_allowed_time_kinds" in raw_overrides:
            raw_kinds = raw_overrides["event_time_candidate_map_allowed_time_kinds"]
            if not isinstance(raw_kinds, (list, tuple)):
                raise ValueError(
                    "route_overrides.event_time_candidate_map_allowed_time_kinds "
                    "must be a list or tuple"
                )
            overrides["event_time_candidate_map_allowed_time_kinds"] = tuple(
                str(kind) for kind in raw_kinds
            )
        if "event_time_candidate_map_strip_context_wrappers" in raw_overrides:
            overrides["event_time_candidate_map_strip_context_wrappers"] = bool(
                raw_overrides["event_time_candidate_map_strip_context_wrappers"]
            )
        if "event_time_candidate_map_segment_local_context" in raw_overrides:
            overrides["event_time_candidate_map_segment_local_context"] = bool(
                raw_overrides["event_time_candidate_map_segment_local_context"]
            )
        if "event_time_candidate_map_rank_by_coverage" in raw_overrides:
            overrides["event_time_candidate_map_rank_by_coverage"] = bool(
                raw_overrides["event_time_candidate_map_rank_by_coverage"]
            )
        if "event_time_candidate_map_normalize_terms" in raw_overrides:
            overrides["event_time_candidate_map_normalize_terms"] = bool(
                raw_overrides["event_time_candidate_map_normalize_terms"]
            )
        if "event_time_candidate_map_exact_today_min_coverage" in raw_overrides:
            raw_value = raw_overrides[
                "event_time_candidate_map_exact_today_min_coverage"
            ]
            overrides["event_time_candidate_map_exact_today_min_coverage"] = (
                None if raw_value is None else min(1.0, max(0.0, float(raw_value)))
            )
        if "event_time_candidate_map_require_role_match" in raw_overrides:
            overrides["event_time_candidate_map_require_role_match"] = bool(
                raw_overrides["event_time_candidate_map_require_role_match"]
            )
        if "event_time_candidate_map_allow_time_of_day_questions" in raw_overrides:
            overrides["event_time_candidate_map_allow_time_of_day_questions"] = bool(
                raw_overrides["event_time_candidate_map_allow_time_of_day_questions"]
            )
        if "event_time_candidate_map_audit" in raw_overrides:
            overrides["event_time_candidate_map_audit"] = bool(
                raw_overrides["event_time_candidate_map_audit"]
            )
        if "enable_weekend_relative_time" in raw_overrides:
            overrides["enable_weekend_relative_time"] = bool(
                raw_overrides["enable_weekend_relative_time"]
            )
        if "event_time_candidate_map_include_mention_time" in raw_overrides:
            overrides["event_time_candidate_map_include_mention_time"] = bool(
                raw_overrides["event_time_candidate_map_include_mention_time"]
            )
        if "event_time_candidate_map_mention_time_fallback" in raw_overrides:
            overrides["event_time_candidate_map_mention_time_fallback"] = bool(
                raw_overrides["event_time_candidate_map_mention_time_fallback"]
            )
        if (
            "event_time_candidate_map_mention_time_fallback_min_coverage"
            in raw_overrides
        ):
            overrides[
                "event_time_candidate_map_mention_time_fallback_min_coverage"
            ] = min(
                1.0,
                max(
                    0.0,
                    float(
                        raw_overrides[
                            "event_time_candidate_map_mention_time_fallback_min_coverage"
                        ]
                    ),
                ),
            )
        if (
            "event_time_candidate_map_mention_time_fallback_trigger_max_coverage"
            in raw_overrides
        ):
            overrides[
                "event_time_candidate_map_mention_time_fallback_trigger_max_coverage"
            ] = min(
                1.0,
                max(
                    0.0,
                    float(
                        raw_overrides[
                            "event_time_candidate_map_mention_time_fallback_trigger_max_coverage"
                        ]
                    ),
                ),
            )
        if "candidate_guide" in raw_overrides:
            overrides["candidate_guide"] = bool(raw_overrides["candidate_guide"])
        if "candidate_guide_include_memory_hints" in raw_overrides:
            overrides["candidate_guide_include_memory_hints"] = bool(
                raw_overrides["candidate_guide_include_memory_hints"]
            )
        if "candidate_guide_max_memory_hints" in raw_overrides:
            overrides["candidate_guide_max_memory_hints"] = max(
                0, int(raw_overrides["candidate_guide_max_memory_hints"])
            )
        if "candidate_guide_max_rows" in raw_overrides:
            overrides["candidate_guide_max_rows"] = max(
                1, int(raw_overrides["candidate_guide_max_rows"])
            )
        if "candidate_guide_memory_hint_chars" in raw_overrides:
            overrides["candidate_guide_memory_hint_chars"] = max(
                40, int(raw_overrides["candidate_guide_memory_hint_chars"])
            )
        if "candidate_guide_snippet_chars" in raw_overrides:
            overrides["candidate_guide_snippet_chars"] = max(
                80, int(raw_overrides["candidate_guide_snippet_chars"])
            )
        if "update_conflict_guide" in raw_overrides:
            overrides["update_conflict_guide"] = bool(
                raw_overrides["update_conflict_guide"]
            )
        if "update_conflict_guide_max_rows" in raw_overrides:
            overrides["update_conflict_guide_max_rows"] = max(
                2, int(raw_overrides["update_conflict_guide_max_rows"])
            )
        if "update_conflict_guide_snippet_chars" in raw_overrides:
            overrides["update_conflict_guide_snippet_chars"] = max(
                80, int(raw_overrides["update_conflict_guide_snippet_chars"])
            )
        if "memory_state_guide" in raw_overrides:
            overrides["memory_state_guide"] = bool(
                raw_overrides["memory_state_guide"]
            )
        if "memory_state_guide_max_records" in raw_overrides:
            overrides["memory_state_guide_max_records"] = max(
                1, int(raw_overrides["memory_state_guide_max_records"])
            )
        if "memory_state_guide_candidate_records" in raw_overrides:
            overrides["memory_state_guide_candidate_records"] = max(
                1, int(raw_overrides["memory_state_guide_candidate_records"])
            )
        if "memory_state_guide_value_chars" in raw_overrides:
            overrides["memory_state_guide_value_chars"] = max(
                40, int(raw_overrides["memory_state_guide_value_chars"])
            )
        if "memory_state_guide_include_superseded" in raw_overrides:
            overrides["memory_state_guide_include_superseded"] = bool(
                raw_overrides["memory_state_guide_include_superseded"]
            )
        if "memory_state_guide_require_conflict" in raw_overrides:
            overrides["memory_state_guide_require_conflict"] = bool(
                raw_overrides["memory_state_guide_require_conflict"]
            )
        if "memory_state_guide_conflict_source" in raw_overrides:
            overrides["memory_state_guide_conflict_source"] = (
                _validate_memory_state_guide_conflict_source(
                    str(raw_overrides["memory_state_guide_conflict_source"])
                )
            )
        if "memory_state_guide_require_active_superseded_pair" in raw_overrides:
            overrides["memory_state_guide_require_active_superseded_pair"] = bool(
                raw_overrides["memory_state_guide_require_active_superseded_pair"]
            )
        if "memory_state_guide_require_slot_overlap" in raw_overrides:
            overrides["memory_state_guide_require_slot_overlap"] = bool(
                raw_overrides["memory_state_guide_require_slot_overlap"]
            )
        if "memory_state_guide_require_stateful_slot" in raw_overrides:
            overrides["memory_state_guide_require_stateful_slot"] = bool(
                raw_overrides["memory_state_guide_require_stateful_slot"]
            )
        if "memory_value_slot_guide" in raw_overrides:
            overrides["memory_value_slot_guide"] = bool(
                raw_overrides["memory_value_slot_guide"]
            )
        if "memory_value_slot_guide_max_slots" in raw_overrides:
            overrides["memory_value_slot_guide_max_slots"] = max(
                1, int(raw_overrides["memory_value_slot_guide_max_slots"])
            )
        if "memory_value_slot_guide_max_values" in raw_overrides:
            overrides["memory_value_slot_guide_max_values"] = max(
                1, int(raw_overrides["memory_value_slot_guide_max_values"])
            )
        if "memory_value_slot_guide_memory_types" in raw_overrides:
            raw_types = raw_overrides["memory_value_slot_guide_memory_types"]
            if not isinstance(raw_types, (list, tuple)):
                raise ValueError(
                    "route_overrides.memory_value_slot_guide_memory_types must "
                    "be a list or tuple"
                )
            overrides["memory_value_slot_guide_memory_types"] = tuple(
                str(value).strip().lower()
                for value in raw_types
                if str(value).strip()
            )
        if "memory_operation_plan_guide" in raw_overrides:
            overrides["memory_operation_plan_guide"] = bool(
                raw_overrides["memory_operation_plan_guide"]
            )
        if "memory_operation_plan_guide_max_plans" in raw_overrides:
            overrides["memory_operation_plan_guide_max_plans"] = max(
                1, int(raw_overrides["memory_operation_plan_guide_max_plans"])
            )
        if "memory_operation_plan_guide_max_values" in raw_overrides:
            overrides["memory_operation_plan_guide_max_values"] = max(
                1, int(raw_overrides["memory_operation_plan_guide_max_values"])
            )
        if "memory_operation_plan_guide_value_chars" in raw_overrides:
            overrides["memory_operation_plan_guide_value_chars"] = max(
                40, int(raw_overrides["memory_operation_plan_guide_value_chars"])
            )
        if "memory_operation_plan_guide_render_values" in raw_overrides:
            overrides["memory_operation_plan_guide_render_values"] = bool(
                raw_overrides["memory_operation_plan_guide_render_values"]
            )
        if "memory_operation_plan_guide_require_readiness" in raw_overrides:
            overrides["memory_operation_plan_guide_require_readiness"] = bool(
                raw_overrides["memory_operation_plan_guide_require_readiness"]
            )
        if "memory_operation_plan_guide_required_readiness_modes" in raw_overrides:
            overrides["memory_operation_plan_guide_required_readiness_modes"] = (
                _validate_operation_plan_readiness_modes(
                    raw_overrides[
                        "memory_operation_plan_guide_required_readiness_modes"
                    ]
                )
            )
        if "memory_operation_context_organizer" in raw_overrides:
            overrides["memory_operation_context_organizer"] = bool(
                raw_overrides["memory_operation_context_organizer"]
            )
        if "memory_operation_context_organizer_max_plans" in raw_overrides:
            overrides["memory_operation_context_organizer_max_plans"] = max(
                1, int(raw_overrides["memory_operation_context_organizer_max_plans"])
            )
        if "memory_operation_readiness_audit" in raw_overrides:
            overrides["memory_operation_readiness_audit"] = bool(
                raw_overrides["memory_operation_readiness_audit"]
            )
        if "memory_operation_readiness_audit_max_plans" in raw_overrides:
            overrides["memory_operation_readiness_audit_max_plans"] = max(
                1, int(raw_overrides["memory_operation_readiness_audit_max_plans"])
            )
        if "memory_workspace_plan" in raw_overrides:
            overrides["memory_workspace_plan"] = bool(
                raw_overrides["memory_workspace_plan"]
            )
        if "memory_workspace_plan_max_groups" in raw_overrides:
            overrides["memory_workspace_plan_max_groups"] = max(
                1, int(raw_overrides["memory_workspace_plan_max_groups"])
            )
        if "memory_workspace_plan_max_values" in raw_overrides:
            overrides["memory_workspace_plan_max_values"] = max(
                1, int(raw_overrides["memory_workspace_plan_max_values"])
            )
        if "memory_workspace_plan_value_chars" in raw_overrides:
            overrides["memory_workspace_plan_value_chars"] = max(
                40, int(raw_overrides["memory_workspace_plan_value_chars"])
            )
        if "profile_activation_guide" in raw_overrides:
            overrides["profile_activation_guide"] = bool(
                raw_overrides["profile_activation_guide"]
            )
        if "profile_activation_guide_max_records" in raw_overrides:
            overrides["profile_activation_guide_max_records"] = max(
                1, int(raw_overrides["profile_activation_guide_max_records"])
            )
        if "profile_activation_guide_value_chars" in raw_overrides:
            overrides["profile_activation_guide_value_chars"] = max(
                60, int(raw_overrides["profile_activation_guide_value_chars"])
            )
        if "context_layout" in raw_overrides:
            context_layout = str(raw_overrides["context_layout"])
            if context_layout not in SUPPORTED_CONTEXT_LAYOUTS:
                raise ValueError(f"Unsupported context_layout: {context_layout}")
            overrides["context_layout"] = context_layout
        if "current_state_update_contract" in raw_overrides:
            overrides["current_state_update_contract"] = bool(
                raw_overrides["current_state_update_contract"]
            )
        if "dialogue_inference_contract" in raw_overrides:
            overrides["dialogue_inference_contract"] = bool(
                raw_overrides["dialogue_inference_contract"]
            )
        if "grounded_inference_contract" in raw_overrides:
            overrides["grounded_inference_contract"] = bool(
                raw_overrides["grounded_inference_contract"]
            )
        if "grounded_inference_gate" in raw_overrides:
            gate = str(raw_overrides["grounded_inference_gate"])
            if gate not in {"broad", "modal_only"}:
                raise ValueError(f"Unsupported grounded_inference_gate: {gate}")
            overrides["grounded_inference_gate"] = gate
        if "temporal_order_contract" in raw_overrides:
            overrides["temporal_order_contract"] = bool(
                raw_overrides["temporal_order_contract"]
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
    if evidence_order not in EVIDENCE_ORDER_MODES:
        raise ValueError(f"Unsupported evidence_order: {evidence_order}")

    question_terms = _content_terms(question)
    if evidence_order == "memory_tail_filter_preserve_order":
        return _memory_tail_filter_preserve_order(
            rows,
            question_terms=question_terms,
            route=route,
            memory_records=memory_records,
            anchor_keep=source_anchor_keep,
            memory_rows=source_anchor_memory_rows,
            per_session=source_anchor_per_session,
            session_rows=source_anchor_session_rows,
        )
    if evidence_order in {
        "memory_source_interleave",
        "fixed_set_memory_source_interleave",
    }:
        return _memory_source_interleave_order(
            rows,
            question_terms=question_terms,
            route=route,
            memory_records=memory_records,
            anchor_keep=source_anchor_keep,
            memory_rows=source_anchor_memory_rows,
            per_session=source_anchor_per_session,
            session_rows=source_anchor_session_rows,
        )
    if evidence_order == "memory_version_chain_interleave":
        return _memory_version_chain_interleave_order(
            rows,
            question_terms=question_terms,
            route=route,
            memory_records=memory_records,
            anchor_keep=source_anchor_keep,
            memory_rows=source_anchor_memory_rows,
            per_session=source_anchor_per_session,
            session_rows=source_anchor_session_rows,
        )
    if evidence_order == "scoped_memory_version_chain_interleave":
        return _scoped_memory_version_chain_interleave_order(
            rows,
            question=question,
            question_terms=question_terms,
            route=route,
            memory_records=memory_records,
            anchor_keep=source_anchor_keep,
            memory_rows=source_anchor_memory_rows,
            per_session=source_anchor_per_session,
            session_rows=source_anchor_session_rows,
        )
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


def _memory_source_interleave_order(
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
    for row in rows[anchor_keep:]:
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


def _memory_version_chain_interleave_order(
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
    if not rows or not memory_records:
        return rows

    row_by_source = {row.source_id: row for row in rows}
    chains = _visible_version_chains(
        memory_records,
        row_by_source=row_by_source,
        question_terms=question_terms,
        route=route,
    )
    if not chains:
        return _memory_source_interleave_order(
            rows,
            question_terms=question_terms,
            route=route,
            memory_records=memory_records,
            anchor_keep=anchor_keep,
            memory_rows=memory_rows,
            per_session=per_session,
            session_rows=session_rows,
        )

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
    for chain in chains:
        for source_id in chain["source_ids"]:
            row = row_by_source.get(source_id)
            if row is None:
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


def _scoped_memory_version_chain_interleave_order(
    rows: tuple[EvidenceRow, ...],
    *,
    question: str,
    question_terms: frozenset[str],
    route: RouteResult,
    memory_records: tuple[MemoryRecord, ...],
    anchor_keep: int,
    memory_rows: int,
    per_session: int,
    session_rows: int,
) -> tuple[EvidenceRow, ...]:
    if not rows or not memory_records:
        return rows

    row_by_source = {row.source_id: row for row in rows}
    chains = _visible_scoped_version_chains(
        memory_records,
        row_by_source=row_by_source,
        question=question,
        question_terms=question_terms,
        route=route,
    )
    if not chains:
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
    for chain in chains:
        for source_id in chain["source_ids"]:
            row = row_by_source.get(source_id)
            if row is None:
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


def _visible_version_chains(
    memory_records: tuple[MemoryRecord, ...],
    *,
    row_by_source: Mapping[str, EvidenceRow],
    question_terms: frozenset[str],
    route: RouteResult,
) -> tuple[dict[str, Any], ...]:
    groups: dict[tuple[str, str, str], list[tuple[int, MemoryRecord]]] = {}
    for index, record in enumerate(memory_records):
        key = _version_chain_key(record, route)
        if key is None:
            continue
        if not any(source_id in row_by_source for source_id in record.source_ids):
            continue
        groups.setdefault(key, []).append((index, record))

    chains: list[dict[str, Any]] = []
    for records_with_index in groups.values():
        if len(records_with_index) <= 1:
            continue
        values = {
            _normalize_memory_value(record)
            for _index, record in records_with_index
            if _normalize_memory_value(record)
        }
        statuses = {record.status for _index, record in records_with_index}
        if len(values) <= 1 and "superseded" not in statuses:
            continue

        ordered_records = sorted(
            records_with_index,
            key=lambda item: _version_record_sort_key(item[0], item[1], route),
        )
        source_ids: list[str] = []
        for _index, record in ordered_records:
            for source_id in record.source_ids:
                if source_id not in row_by_source or source_id in source_ids:
                    continue
                source_ids.append(source_id)
        if not source_ids:
            continue

        score = max(
            _version_record_score(record, question_terms=question_terms, route=route)
            for _index, record in records_with_index
        )
        first_rank = min(
            (
                row_by_source[source_id].retrieval_rank
                for source_id in source_ids
                if row_by_source[source_id].retrieval_rank is not None
            ),
            default=1_000_000,
        )
        chains.append(
            {
                "score": score,
                "first_rank": first_rank,
                "source_ids": tuple(source_ids),
            }
        )

    return tuple(
        sorted(
            chains,
            key=lambda chain: (
                -chain["score"],
                chain["first_rank"],
                chain["source_ids"],
            ),
        )
    )


def _visible_scoped_version_chains(
    memory_records: tuple[MemoryRecord, ...],
    *,
    row_by_source: Mapping[str, EvidenceRow],
    question: str,
    question_terms: frozenset[str],
    route: RouteResult,
) -> tuple[dict[str, Any], ...]:
    question_scope = _scoped_version_question_scope(question)
    if question_scope == "unspecified":
        return ()
    scoped_question_terms = _scoped_version_question_terms(question)
    if not scoped_question_terms:
        return ()

    groups: dict[tuple[str, str, str], list[tuple[int, MemoryRecord]]] = {}
    for index, record in enumerate(memory_records):
        key = _version_chain_key(record, route)
        if key is None:
            continue
        if not any(source_id in row_by_source for source_id in record.source_ids):
            continue
        groups.setdefault(key, []).append((index, record))

    chains: list[dict[str, Any]] = []
    for records_with_index in groups.values():
        if not _has_version_change(records_with_index):
            continue
        matching_records = tuple(
            (index, record)
            for index, record in records_with_index
            if _version_record_matches_question(record, scoped_question_terms)
        )
        if not matching_records:
            continue

        scoped_records = tuple(
            (index, record)
            for index, record in records_with_index
            if _version_record_in_question_scope(record, question_scope)
        )
        if not scoped_records:
            continue

        ordered_records = sorted(
            scoped_records,
            key=lambda item: _scoped_version_record_sort_key(
                item[0],
                item[1],
                question_scope=question_scope,
                route=route,
            ),
        )
        source_ids: list[str] = []
        for _index, record in ordered_records:
            for source_id in record.source_ids:
                if source_id not in row_by_source or source_id in source_ids:
                    continue
                source_ids.append(source_id)
        if not source_ids:
            continue

        score = max(
            _version_record_score(
                record,
                question_terms=question_terms,
                route=route,
            )
            for _index, record in matching_records
        )
        first_rank = min(
            (
                row_by_source[source_id].retrieval_rank
                for source_id in source_ids
                if row_by_source[source_id].retrieval_rank is not None
            ),
            default=1_000_000,
        )
        chains.append(
            {
                "score": score,
                "first_rank": first_rank,
                "source_ids": tuple(source_ids),
            }
        )

    return tuple(
        sorted(
            chains,
            key=lambda chain: (
                -chain["score"],
                chain["first_rank"],
                chain["source_ids"],
            ),
        )
    )


def _has_version_change(
    records_with_index: tuple[tuple[int, MemoryRecord], ...] | list[tuple[int, MemoryRecord]],
) -> bool:
    if len(records_with_index) <= 1:
        return False
    values = {
        _normalize_memory_value(record)
        for _index, record in records_with_index
        if _normalize_memory_value(record)
    }
    statuses = {record.status for _index, record in records_with_index}
    return len(values) > 1 or "superseded" in statuses


def _version_chain_key(
    record: MemoryRecord,
    route: RouteResult,
) -> tuple[str, str, str] | None:
    if route.information_need not in {"current_state", "profile_preference"}:
        return None
    if record.memory_type not in {"state", "profile", "preference", "relationship"}:
        return None
    subject = _normalize_version_text(record.subject)
    predicate = _normalize_version_text(record.predicate)
    if not subject or not predicate:
        return None
    return (record.memory_type, subject, predicate)


def _version_record_sort_key(
    index: int,
    record: MemoryRecord,
    route: RouteResult,
) -> tuple[int, str, int]:
    status_rank = 0 if record.status == "active" else 1
    time_key = _memory_timestamp_sort_key(record.valid_from or record.timestamp, route)
    return (status_rank, time_key, index)


def _scoped_version_record_sort_key(
    index: int,
    record: MemoryRecord,
    *,
    question_scope: str,
    route: RouteResult,
) -> tuple[int, str, int]:
    status = str(record.status or "active")
    if question_scope == "historical":
        status_rank = 0 if status != "active" else 1
    else:
        status_rank = 0 if status == "active" else 1
    time_key = _memory_timestamp_sort_key(record.valid_from or record.timestamp, route)
    return (status_rank, time_key, index)


def _version_record_score(
    record: MemoryRecord,
    *,
    question_terms: frozenset[str],
    route: RouteResult,
) -> float:
    record_terms = _content_terms(record.search_text)
    overlap = len(question_terms.intersection(record_terms))
    status_bonus = 0.4 if record.status == "active" else 0.15
    return overlap + _memory_type_bonus(record, route) + status_bonus


def _normalize_memory_value(record: MemoryRecord) -> str:
    return _normalize_version_text(record.value or record.text)


def _normalize_version_text(value: str) -> str:
    return " ".join(str(value).lower().strip().split())


def _scoped_version_question_scope(question: str) -> str:
    lowered = question.lower()
    current = bool(
        re.search(
            r"\b(current|currently|latest|most recent|recently|recent|now|"
            r"today|still|as of|these days|at present|present)\b",
            lowered,
        )
        or re.search(r"(当前|现在|目前|最新|最近|今天|仍然)", question)
    )
    historical = bool(
        re.search(
            r"\b(previous|previously|former|formerly|original|originally|"
            r"initial|initially|earlier|prior|before|used to|old)\b",
            lowered,
        )
        or re.search(r"(之前|以前|原来|原本|最初|过去|曾经|上次)", question)
    )
    change = bool(
        re.search(
            r"\b(changed|updated|switched|moved|became|no longer|instead|"
            r"correction|corrected|actually)\b",
            lowered,
        )
        or re.search(r"(更新|改变|变化|换成|搬到|变成|不再|纠正|其实)", question)
    )
    if change or (current and historical):
        return "change"
    if current:
        return "current"
    if historical:
        return "historical"
    return "unspecified"


def _scoped_version_question_terms(question: str) -> frozenset[str]:
    weak_terms = {
        "after",
        "ago",
        "before",
        "current",
        "currently",
        "day",
        "days",
        "duration",
        "earlier",
        "earliest",
        "former",
        "latest",
        "long",
        "month",
        "months",
        "most",
        "now",
        "old",
        "order",
        "original",
        "past",
        "present",
        "previous",
        "previously",
        "prior",
        "recent",
        "recently",
        "started",
        "still",
        "today",
        "used",
        "week",
        "weeks",
        "year",
        "years",
    }
    return frozenset(_content_terms(question).difference(weak_terms))


def _version_record_matches_question(
    record: MemoryRecord,
    question_terms: frozenset[str],
) -> bool:
    if not question_terms:
        return False
    subject_terms = _content_terms(record.subject)
    scoped_question_terms = question_terms.difference(subject_terms)
    if not scoped_question_terms:
        return False
    record_text = " ".join(
        part
        for part in (
            record.predicate,
            record.value,
            record.text,
            " ".join(record.entities),
        )
        if part
    )
    record_terms = _content_terms(record_text).difference(subject_terms)
    return bool(scoped_question_terms.intersection(record_terms))


def _version_record_in_question_scope(
    record: MemoryRecord,
    question_scope: str,
) -> bool:
    status = str(record.status or "active")
    if question_scope == "current":
        return status == "active"
    if question_scope == "historical":
        return status != "active"
    return question_scope == "change"


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


def _memory_tail_filter_preserve_order(
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
    if not rows or anchor_keep <= 0:
        return rows

    memory_source_scores = _memory_source_scores(
        memory_records,
        question_terms=question_terms,
        route=route,
    )
    selected_ids = {row.source_id for row in rows[:anchor_keep]}
    memory_anchor_sessions: list[str] = []
    memory_session_counts: dict[str, int] = {}

    if memory_rows > 0 and memory_source_scores:
        added_memory_rows = 0
        tail_rows = rows[anchor_keep:]
        for row in sorted(
            tail_rows,
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
            selected_ids.add(row.source_id)
            if row.session_id not in memory_anchor_sessions:
                memory_anchor_sessions.append(row.session_id)
            memory_session_counts[row.session_id] = (
                memory_session_counts.get(row.session_id, 0) + 1
            )
            added_memory_rows += 1
            if added_memory_rows >= memory_rows:
                break

    if session_rows > 0 and memory_anchor_sessions:
        session_counts: dict[str, int] = {}
        for row in rows[anchor_keep:]:
            if row.session_id not in memory_anchor_sessions:
                continue
            if session_counts.get(row.session_id, 0) >= session_rows:
                continue
            selected_ids.add(row.source_id)
            session_counts[row.session_id] = session_counts.get(row.session_id, 0) + 1

    return tuple(row for row in rows if row.source_id in selected_ids)


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
    if context_layout not in {"session_thread", "chronological_session_thread"}:
        raise ValueError(f"Unsupported context_layout: {context_layout}")

    grouped: dict[str, list[EvidenceRow]] = {}
    session_order: list[str] = []
    for row in rows:
        if row.session_id not in grouped:
            grouped[row.session_id] = []
            session_order.append(row.session_id)
        grouped[row.session_id].append(row)

    laid_out: list[EvidenceRow] = []
    if context_layout == "chronological_session_thread":
        session_order = sorted(
            session_order,
            key=lambda session_id: _session_chronology_key(grouped[session_id]),
        )

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


def _session_chronology_key(rows: list[EvidenceRow]) -> tuple[int, str, int, str]:
    timestamps = [row.timestamp for row in rows if row.timestamp]
    earliest = min(timestamps) if timestamps else ""
    first_rank = min(
        (
            row.retrieval_rank
            for row in rows
            if row.retrieval_rank is not None
        ),
        default=1_000_000,
    )
    session_id = rows[0].session_id if rows else ""
    return (0 if earliest else 1, earliest, first_rank, session_id)


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
    temporal_workpad: bool,
    temporal_text_normalization: bool,
    temporal_event_contract: bool,
    temporal_workpad_scope: str,
    temporal_workpad_max_rows: int,
    temporal_workpad_max_pairs: int,
    event_timeline: bool,
    event_timeline_max_rows: int,
    event_timeline_snippet_chars: int,
    event_time_candidate_map: bool,
    event_time_candidate_map_max_groups: int,
    event_time_candidate_map_snippet_chars: int,
    event_time_candidate_map_min_terms: int,
    event_time_candidate_map_min_coverage: float,
    event_time_candidate_map_allowed_time_kinds: tuple[str, ...],
    event_time_candidate_map_strip_context_wrappers: bool,
    event_time_candidate_map_segment_local_context: bool,
    event_time_candidate_map_rank_by_coverage: bool,
    event_time_candidate_map_normalize_terms: bool,
    event_time_candidate_map_exact_today_min_coverage: float | None,
    event_time_candidate_map_require_role_match: bool,
    event_time_candidate_map_temporal_ambiguity_contract: bool,
    event_time_candidate_map_include_mention_time: bool,
    event_time_candidate_map_mention_time_fallback: bool,
    event_time_candidate_map_mention_time_fallback_min_coverage: float,
    event_time_candidate_map_mention_time_fallback_trigger_max_coverage: float,
    enable_weekend_relative_time: bool,
    structured_guide: bool,
    structured_guide_max_rows: int,
    structured_guide_include_rows: bool,
    structured_guide_include_memory: bool,
    structured_guide_memory_hints: bool,
    structured_guide_max_memory_hints_per_row: int,
    structured_guide_memory_hint_chars: int,
    structured_answer_contract: bool,
    structured_answer_contract_max_items: int,
    evidence_report_contract: bool,
    aggregation_report_contract: bool,
    candidate_guide: bool,
    candidate_guide_max_rows: int,
    candidate_guide_snippet_chars: int,
    candidate_guide_include_memory_hints: bool,
    candidate_guide_max_memory_hints: int,
    candidate_guide_memory_hint_chars: int,
    update_conflict_guide: bool,
    update_conflict_guide_max_rows: int,
    update_conflict_guide_snippet_chars: int,
    memory_state_guide: bool,
    memory_state_guide_records: tuple[MemoryRecord, ...],
    memory_state_conflict_manifest: Mapping[str, Any] | None,
    memory_scalar_value_manifest: Mapping[str, Any] | None,
    memory_object_index: Mapping[str, Any] | None,
    memory_workspace_manifest: Mapping[str, Any] | None,
    memory_operation_plan: Mapping[str, Any] | None,
    memory_query_readiness_manifest: Mapping[str, Any] | None,
    memory_operation_plan_guide: bool,
    memory_operation_plan_guide_max_plans: int,
    memory_operation_plan_guide_max_values: int,
    memory_operation_plan_guide_value_chars: int,
    memory_operation_plan_guide_render_values: bool,
    memory_operation_plan_guide_require_readiness: bool,
    memory_operation_plan_guide_required_readiness_modes: tuple[str, ...],
    memory_workspace_plan: bool,
    memory_workspace_plan_max_groups: int,
    memory_workspace_plan_max_values: int,
    memory_workspace_plan_value_chars: int,
    memory_state_guide_max_records: int,
    memory_state_guide_candidate_records: int,
    memory_state_guide_value_chars: int,
    memory_state_guide_include_superseded: bool,
    memory_state_guide_require_conflict: bool,
    memory_state_guide_conflict_source: str,
    memory_state_guide_require_active_superseded_pair: bool,
    memory_state_guide_require_slot_overlap: bool,
    memory_state_guide_require_stateful_slot: bool,
    memory_value_slot_guide: bool,
    memory_value_slot_guide_max_slots: int,
    memory_value_slot_guide_max_values: int,
    memory_value_slot_guide_memory_types: tuple[str, ...],
    profile_activation_guide: bool,
    profile_activation_guide_max_records: int,
    profile_activation_guide_value_chars: int,
    evidence_report_max_items: int,
    evidence_report_detail: bool,
    operation_workpad: bool,
    personalized_advice_contract: bool,
    current_state_update_contract: bool,
    dialogue_inference_contract: bool,
    grounded_inference_contract: bool,
    temporal_order_contract: bool,
    context_layout: str,
    memory_layout: str,
    row_text_mode: str,
    max_row_text_chars: int,
    tail_row_text_mode: str,
    tail_row_text_after_rank: int,
    tail_max_row_text_chars: int,
    memory_context_newlines_after_blocks: int,
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
            tail_row_text_mode=tail_row_text_mode,
            tail_row_text_after_rank=tail_row_text_after_rank,
            tail_max_row_text_chars=tail_max_row_text_chars,
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
            tail_row_text_mode=tail_row_text_mode,
            tail_row_text_after_rank=tail_row_text_after_rank,
            tail_max_row_text_chars=tail_max_row_text_chars,
            temporal_workpad=temporal_workpad,
            temporal_text_normalization=temporal_text_normalization,
            temporal_event_contract=temporal_event_contract,
            temporal_workpad_scope=temporal_workpad_scope,
            temporal_workpad_max_rows=temporal_workpad_max_rows,
            temporal_workpad_max_pairs=temporal_workpad_max_pairs,
            event_timeline=event_timeline,
            event_timeline_max_rows=event_timeline_max_rows,
            event_timeline_snippet_chars=event_timeline_snippet_chars,
            event_time_candidate_map=event_time_candidate_map,
            event_time_candidate_map_max_groups=event_time_candidate_map_max_groups,
            event_time_candidate_map_snippet_chars=(
                event_time_candidate_map_snippet_chars
            ),
            event_time_candidate_map_min_terms=event_time_candidate_map_min_terms,
            event_time_candidate_map_min_coverage=(
                event_time_candidate_map_min_coverage
            ),
            event_time_candidate_map_allowed_time_kinds=(
                event_time_candidate_map_allowed_time_kinds
            ),
            event_time_candidate_map_strip_context_wrappers=(
                event_time_candidate_map_strip_context_wrappers
            ),
            event_time_candidate_map_segment_local_context=(
                event_time_candidate_map_segment_local_context
            ),
            event_time_candidate_map_rank_by_coverage=(
                event_time_candidate_map_rank_by_coverage
            ),
            event_time_candidate_map_normalize_terms=(
                event_time_candidate_map_normalize_terms
            ),
            event_time_candidate_map_exact_today_min_coverage=(
                event_time_candidate_map_exact_today_min_coverage
            ),
            event_time_candidate_map_require_role_match=(
                event_time_candidate_map_require_role_match
            ),
            event_time_candidate_map_temporal_ambiguity_contract=(
                event_time_candidate_map_temporal_ambiguity_contract
            ),
            event_time_candidate_map_include_mention_time=(
                event_time_candidate_map_include_mention_time
            ),
            event_time_candidate_map_mention_time_fallback=(
                event_time_candidate_map_mention_time_fallback
            ),
            event_time_candidate_map_mention_time_fallback_min_coverage=(
                event_time_candidate_map_mention_time_fallback_min_coverage
            ),
            event_time_candidate_map_mention_time_fallback_trigger_max_coverage=(
                event_time_candidate_map_mention_time_fallback_trigger_max_coverage
            ),
            enable_weekend_relative_time=enable_weekend_relative_time,
            structured_guide=structured_guide,
            structured_guide_max_rows=structured_guide_max_rows,
            structured_guide_include_rows=structured_guide_include_rows,
            structured_guide_include_memory=structured_guide_include_memory,
            structured_guide_memory_hints=structured_guide_memory_hints,
            structured_guide_max_memory_hints_per_row=(
                structured_guide_max_memory_hints_per_row
            ),
            structured_guide_memory_hint_chars=structured_guide_memory_hint_chars,
            structured_answer_contract=structured_answer_contract,
            structured_answer_contract_max_items=structured_answer_contract_max_items,
            evidence_report_contract=evidence_report_contract,
            aggregation_report_contract=aggregation_report_contract,
            candidate_guide=candidate_guide,
            candidate_guide_max_rows=candidate_guide_max_rows,
            candidate_guide_snippet_chars=candidate_guide_snippet_chars,
            candidate_guide_include_memory_hints=(
                candidate_guide_include_memory_hints
            ),
            candidate_guide_max_memory_hints=candidate_guide_max_memory_hints,
            candidate_guide_memory_hint_chars=candidate_guide_memory_hint_chars,
            update_conflict_guide=update_conflict_guide,
            update_conflict_guide_max_rows=update_conflict_guide_max_rows,
            update_conflict_guide_snippet_chars=(
                update_conflict_guide_snippet_chars
            ),
            memory_state_guide=memory_state_guide,
            memory_state_guide_records=memory_state_guide_records,
            memory_state_conflict_manifest=memory_state_conflict_manifest,
            memory_scalar_value_manifest=memory_scalar_value_manifest,
            memory_object_index=memory_object_index,
            memory_workspace_manifest=memory_workspace_manifest,
            memory_operation_plan=memory_operation_plan,
            memory_query_readiness_manifest=memory_query_readiness_manifest,
            memory_operation_plan_guide=memory_operation_plan_guide,
            memory_operation_plan_guide_max_plans=memory_operation_plan_guide_max_plans,
            memory_operation_plan_guide_max_values=(
                memory_operation_plan_guide_max_values
            ),
            memory_operation_plan_guide_value_chars=(
                memory_operation_plan_guide_value_chars
            ),
            memory_operation_plan_guide_render_values=(
                memory_operation_plan_guide_render_values
            ),
            memory_operation_plan_guide_require_readiness=(
                memory_operation_plan_guide_require_readiness
            ),
            memory_operation_plan_guide_required_readiness_modes=(
                memory_operation_plan_guide_required_readiness_modes
            ),
            memory_workspace_plan=memory_workspace_plan,
            memory_workspace_plan_max_groups=memory_workspace_plan_max_groups,
            memory_workspace_plan_max_values=memory_workspace_plan_max_values,
            memory_workspace_plan_value_chars=memory_workspace_plan_value_chars,
            memory_state_guide_max_records=memory_state_guide_max_records,
            memory_state_guide_candidate_records=(
                memory_state_guide_candidate_records
            ),
            memory_state_guide_value_chars=memory_state_guide_value_chars,
            memory_state_guide_include_superseded=(
                memory_state_guide_include_superseded
            ),
            memory_state_guide_require_conflict=(
                memory_state_guide_require_conflict
            ),
            memory_state_guide_conflict_source=memory_state_guide_conflict_source,
            memory_state_guide_require_active_superseded_pair=(
                memory_state_guide_require_active_superseded_pair
            ),
            memory_state_guide_require_slot_overlap=(
                memory_state_guide_require_slot_overlap
            ),
            memory_state_guide_require_stateful_slot=(
                memory_state_guide_require_stateful_slot
            ),
            memory_value_slot_guide=memory_value_slot_guide,
            memory_value_slot_guide_max_slots=memory_value_slot_guide_max_slots,
            memory_value_slot_guide_max_values=memory_value_slot_guide_max_values,
            memory_value_slot_guide_memory_types=memory_value_slot_guide_memory_types,
            profile_activation_guide=profile_activation_guide,
            profile_activation_guide_max_records=profile_activation_guide_max_records,
            profile_activation_guide_value_chars=profile_activation_guide_value_chars,
            evidence_report_max_items=evidence_report_max_items,
            evidence_report_detail=evidence_report_detail,
            operation_workpad=operation_workpad,
            personalized_advice_contract=personalized_advice_contract,
            current_state_update_contract=current_state_update_contract,
            dialogue_inference_contract=dialogue_inference_contract,
            grounded_inference_contract=grounded_inference_contract,
            temporal_order_contract=temporal_order_contract,
            memory_context_newlines_after_blocks=(
                memory_context_newlines_after_blocks
            ),
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
            enable_weekend_relative_time=enable_weekend_relative_time,
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
                tail_row_text_mode=tail_row_text_mode,
                tail_row_text_after_rank=tail_row_text_after_rank,
                tail_max_row_text_chars=tail_max_row_text_chars,
            )
        )
    return "\n".join(lines)


def _build_raw_context_only_prompt(
    *,
    question: str,
    question_time: str | None,
    rows: tuple[EvidenceRow, ...],
    answer_style: str,
    row_text_mode: str,
    max_row_text_chars: int,
    tail_row_text_mode: str,
    tail_row_text_after_rank: int,
    tail_max_row_text_chars: int,
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
                tail_row_text_mode=tail_row_text_mode,
                tail_row_text_after_rank=tail_row_text_after_rank,
                tail_max_row_text_chars=tail_max_row_text_chars,
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
    tail_row_text_mode: str,
    tail_row_text_after_rank: int,
    tail_max_row_text_chars: int,
    temporal_workpad: bool,
    temporal_text_normalization: bool,
    temporal_event_contract: bool,
    temporal_workpad_scope: str,
    temporal_workpad_max_rows: int,
    temporal_workpad_max_pairs: int,
    event_timeline: bool,
    event_timeline_max_rows: int,
    event_timeline_snippet_chars: int,
    event_time_candidate_map: bool,
    event_time_candidate_map_max_groups: int,
    event_time_candidate_map_snippet_chars: int,
    event_time_candidate_map_min_terms: int,
    event_time_candidate_map_min_coverage: float,
    event_time_candidate_map_allowed_time_kinds: tuple[str, ...],
    event_time_candidate_map_strip_context_wrappers: bool,
    event_time_candidate_map_segment_local_context: bool,
    event_time_candidate_map_rank_by_coverage: bool,
    event_time_candidate_map_normalize_terms: bool,
    event_time_candidate_map_exact_today_min_coverage: float | None,
    event_time_candidate_map_require_role_match: bool,
    event_time_candidate_map_temporal_ambiguity_contract: bool,
    event_time_candidate_map_include_mention_time: bool,
    event_time_candidate_map_mention_time_fallback: bool,
    event_time_candidate_map_mention_time_fallback_min_coverage: float,
    event_time_candidate_map_mention_time_fallback_trigger_max_coverage: float,
    enable_weekend_relative_time: bool,
    structured_guide: bool,
    structured_guide_max_rows: int,
    structured_guide_include_rows: bool,
    structured_guide_include_memory: bool,
    structured_guide_memory_hints: bool,
    structured_guide_max_memory_hints_per_row: int,
    structured_guide_memory_hint_chars: int,
    structured_answer_contract: bool,
    structured_answer_contract_max_items: int,
    evidence_report_contract: bool,
    aggregation_report_contract: bool,
    candidate_guide: bool,
    candidate_guide_max_rows: int,
    candidate_guide_snippet_chars: int,
    candidate_guide_include_memory_hints: bool,
    candidate_guide_max_memory_hints: int,
    candidate_guide_memory_hint_chars: int,
    update_conflict_guide: bool,
    update_conflict_guide_max_rows: int,
    update_conflict_guide_snippet_chars: int,
    memory_state_guide: bool,
    memory_state_guide_records: tuple[MemoryRecord, ...],
    memory_state_conflict_manifest: Mapping[str, Any] | None,
    memory_scalar_value_manifest: Mapping[str, Any] | None,
    memory_object_index: Mapping[str, Any] | None,
    memory_workspace_manifest: Mapping[str, Any] | None,
    memory_operation_plan: Mapping[str, Any] | None,
    memory_query_readiness_manifest: Mapping[str, Any] | None,
    memory_operation_plan_guide: bool,
    memory_operation_plan_guide_max_plans: int,
    memory_operation_plan_guide_max_values: int,
    memory_operation_plan_guide_value_chars: int,
    memory_operation_plan_guide_render_values: bool,
    memory_operation_plan_guide_require_readiness: bool,
    memory_operation_plan_guide_required_readiness_modes: tuple[str, ...],
    memory_workspace_plan: bool,
    memory_workspace_plan_max_groups: int,
    memory_workspace_plan_max_values: int,
    memory_workspace_plan_value_chars: int,
    memory_state_guide_max_records: int,
    memory_state_guide_candidate_records: int,
    memory_state_guide_value_chars: int,
    memory_state_guide_include_superseded: bool,
    memory_state_guide_require_conflict: bool,
    memory_state_guide_conflict_source: str,
    memory_state_guide_require_active_superseded_pair: bool,
    memory_state_guide_require_slot_overlap: bool,
    memory_state_guide_require_stateful_slot: bool,
    memory_value_slot_guide: bool,
    memory_value_slot_guide_max_slots: int,
    memory_value_slot_guide_max_values: int,
    memory_value_slot_guide_memory_types: tuple[str, ...],
    profile_activation_guide: bool,
    profile_activation_guide_max_records: int,
    profile_activation_guide_value_chars: int,
    evidence_report_max_items: int,
    evidence_report_detail: bool,
    operation_workpad: bool,
    personalized_advice_contract: bool,
    current_state_update_contract: bool,
    dialogue_inference_contract: bool,
    grounded_inference_contract: bool,
    temporal_order_contract: bool,
    memory_context_newlines_after_blocks: int,
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
            enable_weekend_relative_time=enable_weekend_relative_time,
        )
        if temporal_aid_lines:
            temporal_aid = "\n".join(["", "Temporal Aid:", *temporal_aid_lines, ""])
    event_timeline_block = ""
    if event_timeline:
        event_timeline_lines = _external_event_timeline_lines(
            question=question,
            rows=rows,
            max_rows=event_timeline_max_rows,
            snippet_chars=event_timeline_snippet_chars,
        )
        if event_timeline_lines:
            event_timeline_block = "\n".join(
                ["", "Source Event Timeline:", *event_timeline_lines, ""]
            )
    event_time_candidate_map_block = ""
    if event_time_candidate_map:
        event_time_candidate_map_lines = _external_event_time_candidate_map_lines(
            question=question,
            rows=rows,
            max_groups=event_time_candidate_map_max_groups,
            snippet_chars=event_time_candidate_map_snippet_chars,
            min_terms=event_time_candidate_map_min_terms,
            min_coverage=event_time_candidate_map_min_coverage,
            allowed_time_kinds=event_time_candidate_map_allowed_time_kinds,
            strip_context_wrappers=event_time_candidate_map_strip_context_wrappers,
            segment_local_context=event_time_candidate_map_segment_local_context,
            rank_by_coverage=event_time_candidate_map_rank_by_coverage,
            normalize_terms=event_time_candidate_map_normalize_terms,
            exact_today_min_coverage=(
                event_time_candidate_map_exact_today_min_coverage
            ),
            require_role_match=event_time_candidate_map_require_role_match,
            temporal_ambiguity_contract=(
                event_time_candidate_map_temporal_ambiguity_contract
            ),
            include_mention_time=event_time_candidate_map_include_mention_time,
            mention_time_fallback=event_time_candidate_map_mention_time_fallback,
            mention_time_fallback_min_coverage=(
                event_time_candidate_map_mention_time_fallback_min_coverage
            ),
            mention_time_fallback_trigger_max_coverage=(
                event_time_candidate_map_mention_time_fallback_trigger_max_coverage
            ),
            enable_weekend_relative_time=enable_weekend_relative_time,
        )
        if event_time_candidate_map_lines:
            event_time_candidate_map_block = "\n".join(
                [
                    "",
                    "Event-Time Candidate Map:",
                    *event_time_candidate_map_lines,
                    "",
                ]
            )
    structured_guide_block = ""
    if structured_guide:
        guide_lines = _external_structured_guide_lines(
            question=question,
            route=route,
            rows=rows,
            memory_records=memory_records,
            max_rows=structured_guide_max_rows,
            include_relative_text=temporal_text_normalization,
            event_contract=use_temporal_event_contract,
            enable_weekend_relative_time=enable_weekend_relative_time,
            include_rows=structured_guide_include_rows,
            include_memory=structured_guide_include_memory,
            include_inline_memory_hints=structured_guide_memory_hints,
            max_memory_hints_per_row=structured_guide_max_memory_hints_per_row,
            memory_hint_chars=structured_guide_memory_hint_chars,
        )
        if guide_lines:
            structured_guide_block = "\n".join(
                ["", "Structured Evidence Guide:", *guide_lines, ""]
            )
    memory_workspace_plan_block = ""
    if memory_workspace_plan:
        memory_workspace_lines = _external_memory_workspace_plan_lines(
            question=question,
            route=route,
            rows=rows,
            memory_workspace_manifest=memory_workspace_manifest,
            max_groups=memory_workspace_plan_max_groups,
            max_values=memory_workspace_plan_max_values,
            max_value_chars=memory_workspace_plan_value_chars,
        )
        if memory_workspace_lines:
            memory_workspace_plan_block = "\n".join(
                ["", "Memory Workspace Plan:", *memory_workspace_lines, ""]
            )
    memory_operation_plan_guide_block = ""
    if memory_operation_plan_guide:
        memory_operation_plan_lines = _external_memory_operation_plan_guide_lines(
            question=question,
            route=route,
            rows=rows,
            memory_operation_plan=memory_operation_plan,
            memory_query_readiness_manifest=memory_query_readiness_manifest,
            max_plans=memory_operation_plan_guide_max_plans,
            max_values=memory_operation_plan_guide_max_values,
            max_value_chars=memory_operation_plan_guide_value_chars,
            render_values=memory_operation_plan_guide_render_values,
            require_readiness=memory_operation_plan_guide_require_readiness,
            required_readiness_modes=(
                memory_operation_plan_guide_required_readiness_modes
            ),
        )
        if memory_operation_plan_lines:
            memory_operation_plan_guide_block = "\n".join(
                ["", "Memory Operation Plan Guide:", *memory_operation_plan_lines, ""]
            )
    candidate_guide_block = ""
    if candidate_guide:
        candidate_lines = _external_candidate_guide_lines(
            question=question,
            route=route,
            rows=rows,
            memory_records=memory_records,
            max_rows=candidate_guide_max_rows,
            snippet_chars=candidate_guide_snippet_chars,
            include_memory_hints=candidate_guide_include_memory_hints,
            max_memory_hints=candidate_guide_max_memory_hints,
            memory_hint_chars=candidate_guide_memory_hint_chars,
        )
        if candidate_lines:
            candidate_guide_block = "\n".join(
                ["", "Candidate Evidence Map:", *candidate_lines, ""]
            )
    profile_activation_guide_block = ""
    if profile_activation_guide:
        profile_activation_lines = _external_profile_activation_guide_lines(
            question=question,
            route=route,
            rows=rows,
            memory_records=memory_records,
            max_records=profile_activation_guide_max_records,
            max_value_chars=profile_activation_guide_value_chars,
        )
        if profile_activation_lines:
            profile_activation_guide_block = "\n".join(
                ["", "Profile Memory Activation Guide:", *profile_activation_lines, ""]
            )
    memory_state_guide_block = ""
    if memory_state_guide:
        memory_state_lines = _external_memory_state_guide_lines(
            question=question,
            route=route,
            rows=rows,
            memory_records=memory_state_guide_records,
            state_conflict_manifest=memory_state_conflict_manifest,
            max_records=memory_state_guide_max_records,
            max_value_chars=memory_state_guide_value_chars,
            include_superseded=memory_state_guide_include_superseded,
            require_conflict=memory_state_guide_require_conflict,
            conflict_source=memory_state_guide_conflict_source,
            require_active_superseded_pair=(
                memory_state_guide_require_active_superseded_pair
            ),
            require_slot_overlap=memory_state_guide_require_slot_overlap,
            require_stateful_slot=memory_state_guide_require_stateful_slot,
        )
        if memory_state_lines:
            memory_state_guide_block = "\n".join(
                ["", "Managed Memory State Guide:", *memory_state_lines, ""]
            )
    memory_value_slot_guide_block = ""
    if memory_value_slot_guide:
        memory_value_slot_lines = _external_memory_value_slot_guide_lines(
            question=question,
            route=route,
            rows=rows,
            scalar_value_manifest=memory_scalar_value_manifest,
            memory_object_index=memory_object_index,
            max_slots=memory_value_slot_guide_max_slots,
            max_values=memory_value_slot_guide_max_values,
            memory_types=memory_value_slot_guide_memory_types,
        )
        if memory_value_slot_lines:
            memory_value_slot_guide_block = "\n".join(
                ["", "Memory Value Slot Guide:", *memory_value_slot_lines, ""]
            )
    update_conflict_guide_block = ""
    if update_conflict_guide:
        update_conflict_lines = _external_update_conflict_guide_lines(
            question=question,
            route=route,
            rows=rows,
            max_rows=update_conflict_guide_max_rows,
            snippet_chars=update_conflict_guide_snippet_chars,
        )
        if update_conflict_lines:
            update_conflict_guide_block = "\n".join(
                ["", "Update/Conflict Candidate Chain:", *update_conflict_lines, ""]
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
    if memory_workspace_plan_block:
        rules.append(
            "Use Memory Workspace Plan only as a source-backed memory-system index into cited Memory Context rows; it is not independent evidence."
        )
    if memory_operation_plan_guide_block:
        rules.append(
            "Use Memory Operation Plan Guide only as a source-backed state/context operation contract over cited Memory Context rows; it is not independent evidence."
        )
    if profile_activation_guide_block:
        rules.append(
            "Use Profile Memory Activation Guide only as a source-backed preference/profile index into cited Memory Context rows; it is not independent evidence."
        )
    if memory_state_guide_block:
        rules.append(
            "Use Managed Memory State Guide only as a state/conflict index into cited Memory Context rows; it is not independent evidence."
        )
    if memory_value_slot_guide_block:
        rules.append(
            "Use Memory Value Slot Guide only as a build-owned value/state index into cited Memory Context rows; it is not independent evidence."
        )
    if update_conflict_guide_block:
        rules.append(
            "Use Update/Conflict Candidate Chain only as a compact index into Memory Context; it is not independent evidence."
        )
    if temporal_aid:
        rules.append(
            "Use Temporal Aid only to interpret row dates and relative time phrases in the memory context; it is not independent evidence."
        )
    if event_timeline_block:
        rules.append(
            "Use Source Event Timeline only as a source-backed index into cited Memory Context rows; it is not independent evidence."
        )
    if event_time_candidate_map_block:
        rules.append(
            "Use Event-Time Candidate Map only as a high-confidence source-backed index into cited Memory Context rows; it is not independent evidence."
        )
    personalized_advice_block = ""
    if personalized_advice_contract:
        personalized_advice_block = "\n".join(
            ["", "Personalized Advice Discipline:", *_personalized_advice_lines(), ""]
        )
        rules.append(
            "Use Personalized Advice Discipline only to interpret relevant Memory Context rows; it is not independent evidence."
        )
    grounded_inference_block = ""
    if grounded_inference_contract:
        grounded_inference_block = "\n".join(
            ["", "Grounded Inference Discipline:", *_grounded_inference_lines(), ""]
        )
        rules.append(
            "Use Grounded Inference Discipline only to interpret Memory Context rows; it is not independent evidence."
        )
    if context_layout in {"session_thread", "chronological_session_thread"}:
        if context_layout == "chronological_session_thread":
            rules.append(
                "Memory Context is grouped by session; sessions and turns are shown in chronological order. Use nearby turns in the same session to resolve implicit references, but do not merge unrelated sessions."
            )
        else:
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
                dialogue_inference_contract=dialogue_inference_contract,
                temporal_order_contract=temporal_order_contract,
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
            '  "missing": "missing required target/operand/endpoint or empty",',
            '  "answer": "concise answer"',
            "}",
            f"Use at most {evidence_report_max_items} evidence_report items.",
        ]
        if use_aggregation_report_contract:
            output_json_lines.insert(
                -4,
                '  "calculation": "count/sum/difference/duration/order calculation or empty",',
            )
    else:
        output_json_lines = [
            "{",
            '  "reasoning": "one short sentence",',
            '  "answer": "concise answer"',
            "}",
        ]
    prompt_parts = [
        "Answer the user's question using only the provided memory context.",
        "",
        "User Question:",
        user_question,
    ]
    prompt_blocks = [
        block
        for block in (
            structured_guide_block,
            memory_workspace_plan_block,
            memory_operation_plan_guide_block,
            event_time_candidate_map_block,
            candidate_guide_block,
            profile_activation_guide_block,
            memory_state_guide_block,
            memory_value_slot_guide_block,
            update_conflict_guide_block,
            event_timeline_block,
            operation_workpad_block,
            personalized_advice_block,
            grounded_inference_block,
        )
        if block
    ]
    prompt_parts.extend(prompt_blocks)
    if prompt_blocks:
        memory_context_separator = [""] * max(
            0, int(memory_context_newlines_after_blocks) - 2
        )
    else:
        memory_context_separator = ["", ""]
    prompt_parts.extend(
        [
            *memory_context_separator,
            "Memory Context:",
            _external_naive_context(
                rows,
                question=question,
                row_text_mode=row_text_mode,
                max_row_text_chars=max_row_text_chars,
                tail_row_text_mode=tail_row_text_mode,
                tail_row_text_after_rank=tail_row_text_after_rank,
                tail_max_row_text_chars=tail_max_row_text_chars,
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
    return "\n".join(prompt_parts)


def _external_evidence_report_rules(
    question: str,
    route: RouteResult,
    *,
    temporal_event_contract: bool = False,
    detailed: bool = False,
    current_state_update_contract: bool = False,
    dialogue_inference_contract: bool = False,
    temporal_order_contract: bool = False,
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
    if dialogue_inference_contract:
        rules.extend(
            [
                "Same-session neighboring turns may jointly resolve an omitted slot only when they are part of the same ongoing exchange and the later row explicitly names the missing entity, value, place, or constraint.",
                "An assistant row can support an answer when it directly answers, acknowledges, repeats, or clarifies the user's stated event or request; do not treat assistant suggestions or examples as support unless the user confirms them or the question asks about suggestions.",
                "Do not combine partial clues across different sessions or unrelated topics to invent a target event, object, place, or preference.",
            ]
        )
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
        if temporal_order_contract:
            rules.extend(
                [
                    "For order/comparison questions, normalize each candidate event or state time before comparing; the earlier normalized event time happened first.",
                    "Phrases such as for the past N days/weeks/months/years, since N ago, or started N ago indicate a start time N units before the row Date, not the row Date itself.",
                    "If the reasoning dates imply the opposite of the drafted answer, correct the answer to match the normalized date comparison.",
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
    route: RouteResult,
    rows: tuple[EvidenceRow, ...],
    memory_records: tuple[MemoryRecord, ...],
    max_rows: int,
    include_relative_text: bool,
    event_contract: bool,
    enable_weekend_relative_time: bool,
    include_rows: bool,
    include_memory: bool,
    include_inline_memory_hints: bool,
    max_memory_hints_per_row: int,
    memory_hint_chars: int,
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
    memory_records_by_source = (
        _memory_records_by_source_id(memory_records)
        if include_inline_memory_hints and max_memory_hints_per_row > 0
        else {}
    )

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
                relative_times = tuple(
                    _relative_time_values(
                        row.text,
                        row_date,
                        enable_weekend=enable_weekend_relative_time,
                    )
                )
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
            memory_hint_text = ""
            memory_hint = _structured_row_memory_hint_text(
                memory_records_by_source.get(row.source_id, ()),
                route=route,
                max_hints=max_memory_hints_per_row,
                max_chars=memory_hint_chars,
            )
            if memory_hint:
                memory_hint_text = f" | memory_hint={memory_hint}"
            lines.append(
                f"  - Memory {index}: row_date={row_date_text} role={row.role} "
                f"matched_terms={matched_text}{relative_text}{memory_hint_text}"
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


def _structured_row_memory_hint_text(
    memory_records: tuple[MemoryRecord, ...],
    *,
    route: RouteResult,
    max_hints: int,
    max_chars: int,
) -> str:
    if not memory_records or max_hints <= 0:
        return ""
    hints = []
    for record in memory_records:
        if not _memory_type_matches_route(record.memory_type, route):
            continue
        hint = _compact_inline_memory_hint(record, max_chars=max_chars)
        if hint:
            hints.append(hint)
        if len(hints) >= max_hints:
            break
    return "; ".join(hints)


def _compact_inline_memory_hint(record: MemoryRecord, *, max_chars: int) -> str:
    memory_type = record.memory_type or "memory"
    status = f"({record.status})" if record.status and record.status != "active" else ""
    value = record.value or record.text
    if not value:
        return f"{memory_type}{status}"
    return f"{memory_type}{status}:{_truncate_text(_single_line(value), max_chars)}"


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


def _external_memory_workspace_plan_lines(
    *,
    question: str,
    route: RouteResult,
    rows: tuple[EvidenceRow, ...],
    memory_workspace_manifest: Mapping[str, Any] | None,
    max_groups: int,
    max_values: int,
    max_value_chars: int,
) -> list[str]:
    """Compact source-backed memory workspace plan grounded in visible rows."""

    if (
        not rows
        or not memory_workspace_manifest
        or not memory_workspace_manifest.get("applied")
        or max_groups <= 0
    ):
        return []

    activation_groups = memory_workspace_manifest.get("activation_groups") or ()
    if (
        not isinstance(activation_groups, Iterable)
        or isinstance(activation_groups, (str, bytes))
    ):
        return []

    source_to_memory_index = {
        row.source_id: index for index, row in enumerate(rows, start=1)
    }
    question_terms = _content_terms(question).difference(
        MEMORY_STATE_GUIDE_ALIGNMENT_WEAK_TERMS
    )
    question_scope = _workspace_question_scope(question, route)
    candidates: list[tuple[float, int, Mapping[str, Any], tuple[dict[str, Any], ...], tuple[str, ...]]] = []
    for ordinal, raw_group in enumerate(activation_groups):
        if not isinstance(raw_group, Mapping):
            continue
        if raw_group.get("source_backed") is False:
            continue
        if str(raw_group.get("memory_tier") or "") == "quarantine_memory":
            continue
        visible_values = _workspace_visible_values(
            raw_group,
            source_to_memory_index=source_to_memory_index,
            max_values=max_values,
            question_scope=question_scope,
        )
        source_labels = _workspace_group_source_labels(
            raw_group,
            source_to_memory_index=source_to_memory_index,
            question_scope=question_scope,
        )
        if not visible_values and not source_labels:
            continue
        score = _workspace_group_score(
            raw_group,
            visible_values=visible_values,
            question_terms=question_terms,
            route=route,
            question_scope=question_scope,
        )
        if score <= 0:
            continue
        candidates.append((score, -ordinal, raw_group, visible_values, source_labels))

    if not candidates:
        return []

    candidates.sort(reverse=True)
    selected = sorted(
        candidates[:max_groups],
        key=lambda item: (
            str(item[2].get("memory_tier") or ""),
            str(item[2].get("memory_type") or ""),
            str(item[2].get("subject") or ""),
            str(item[2].get("predicate") or ""),
            item[1],
        ),
    )
    lines = [
        "Use this build-owned workspace to activate memory slots, expand them to raw rows, verify lifecycle/source support, and audit conflicts before answering.",
        "- Every listed group is backed by visible Memory Context rows; final facts must still come from those rows.",
        "- operations: retrieve -> expand -> verify -> context_pack -> answer_from_raw_rows; use audit for conflicts or stale values.",
        "- groups:",
    ]
    for _, _, group, visible_values, source_labels in selected:
        fields = [
            f"group={_single_line(str(group.get('group_type') or 'memory_workspace'))}",
            f"tier={_single_line(str(group.get('memory_tier') or 'memory'))}",
            f"type={_single_line(str(group.get('memory_type') or 'memory'))}",
        ]
        subject = _single_line(str(group.get("subject") or ""))
        predicate = _single_line(str(group.get("predicate") or ""))
        if subject:
            fields.append(f"subject={_truncate_text(subject, 52)}")
        if predicate:
            fields.append(f"predicate={_truncate_text(predicate, 52)}")
        lifecycle = _single_line(str(group.get("lifecycle_state") or ""))
        if lifecycle:
            fields.append(f"lifecycle={lifecycle}")
        active_values = _workspace_values_text(
            visible_values,
            status="active",
            max_values=max_values,
            max_chars=max_value_chars,
        )
        if active_values:
            fields.append(f"active={active_values}")
        historical_values = _workspace_historical_values_text(
            visible_values,
            max_values=max_values,
            max_chars=max_value_chars,
        )
        if historical_values:
            fields.append(f"historical={historical_values}")
        scalar_values = _workspace_scalar_values_text(
            visible_values,
            max_values=max_values,
        )
        if scalar_values:
            fields.append(f"scalars={scalar_values}")
        source_text = ", ".join(source_labels[:8])
        if source_text:
            fields.append(f"sources={source_text}")
        operations = [
            str(operation)
            for operation in group.get("operation_hints") or ()
            if str(operation).strip()
        ][:5]
        if operations:
            fields.append(f"ops={', '.join(operations)}")
        lines.append(f"  - {' | '.join(fields)}")
    return lines


def _external_memory_operation_plan_guide_lines(
    *,
    question: str,
    route: RouteResult,
    rows: tuple[EvidenceRow, ...],
    memory_operation_plan: Mapping[str, Any] | None,
    memory_query_readiness_manifest: Mapping[str, Any] | None,
    max_plans: int,
    max_values: int,
    max_value_chars: int,
    render_values: bool,
    require_readiness: bool,
    required_readiness_modes: tuple[str, ...],
) -> list[str]:
    """Compact operation-plan guide grounded in visible raw rows."""

    if (
        not rows
        or not memory_operation_plan
        or not memory_operation_plan.get("applied")
        or max_plans <= 0
    ):
        return []

    raw_plans = memory_operation_plan.get("workspace_operation_plans") or ()
    if not isinstance(raw_plans, Iterable) or isinstance(raw_plans, (str, bytes)):
        return []

    source_to_memory_index = {
        row.source_id: index for index, row in enumerate(rows, start=1)
    }
    readiness_by_slot = _memory_query_readiness_by_slot(
        memory_query_readiness_manifest
    )
    question_terms = _content_terms(question).difference(
        MEMORY_STATE_GUIDE_ALIGNMENT_WEAK_TERMS
    )
    question_scope = _workspace_question_scope(question, route)
    candidates: list[
        tuple[float, int, Mapping[str, Any], tuple[str, ...], Mapping[str, Any] | None]
    ] = []
    for ordinal, raw_plan in enumerate(raw_plans):
        if not isinstance(raw_plan, Mapping):
            continue
        if raw_plan.get("source_backed") is False:
            continue
        if str(raw_plan.get("memory_tier") or "") == "quarantine_memory":
            continue
        readiness = _operation_plan_query_readiness(
            raw_plan,
            readiness_by_slot=readiness_by_slot,
            require_readiness=require_readiness,
            required_readiness_modes=required_readiness_modes,
        )
        if require_readiness and readiness is None:
            continue
        source_labels = _operation_plan_source_labels(
            raw_plan,
            source_to_memory_index=source_to_memory_index,
            question_scope=question_scope,
        )
        if not source_labels:
            continue
        score = _operation_plan_score(
            raw_plan,
            question_terms=question_terms,
            route=route,
            question_scope=question_scope,
        )
        if score <= 0:
            continue
        candidates.append((score, -ordinal, raw_plan, source_labels, readiness))

    if not candidates:
        return []

    candidates.sort(reverse=True)
    selected = sorted(
        candidates[:max_plans],
        key=lambda item: (
            str(item[2].get("memory_tier") or ""),
            str(item[2].get("memory_type") or ""),
            str(item[2].get("subject") or ""),
            str(item[2].get("predicate") or ""),
            item[1],
        ),
    )

    lines = [
        "Use this build-owned operation plan to activate state slots, expand raw rows, verify lifecycle/source support, audit stale values, and pack context before answering.",
        "- Every listed plan is backed by visible Memory Context rows; final facts must still come from those rows.",
        "- operation order: retrieve -> expand -> verify -> audit_if_needed -> context_pack -> answer_from_raw_rows.",
        "- plans:",
    ]
    if require_readiness:
        lines.insert(
            1,
            "- Readiness gate: rendered plans are guarded_ready and only safe for additive source-backed organization; they do not replace the state/value guide.",
        )
    if not render_values:
        lines.insert(
            2 if require_readiness else 1,
            "- Values are intentionally not rendered here; use visible Memory Context rows and the state/value guide for final values.",
        )
    for _, _, plan, source_labels, readiness in selected:
        fields = [
            f"tier={_single_line(str(plan.get('memory_tier') or 'memory'))}",
            f"type={_single_line(str(plan.get('memory_type') or 'memory'))}",
        ]
        readiness_fields = _operation_plan_readiness_fields(readiness)
        fields.extend(readiness_fields)
        subject = _single_line(str(plan.get("subject") or ""))
        predicate = _single_line(str(plan.get("predicate") or ""))
        if subject:
            fields.append(f"subject={_truncate_text(subject, 52)}")
        if predicate:
            fields.append(f"predicate={_truncate_text(predicate, 52)}")
        lifecycle = _single_line(str(plan.get("lifecycle_state") or ""))
        if lifecycle:
            fields.append(f"lifecycle={lifecycle}")
        view_modes = _operation_plan_view_modes_text(plan)
        if view_modes:
            fields.append(f"views={view_modes}")
        if render_values:
            active_text = _operation_plan_values_text(
                plan,
                field_name="active_values",
                max_values=max_values,
                max_chars=max_value_chars,
            )
            if active_text:
                fields.append(f"active={active_text}")
            historical_text = _operation_plan_values_text(
                plan,
                field_name="superseded_values",
                max_values=max_values,
                max_chars=max_value_chars,
            )
            if historical_text:
                fields.append(f"historical={historical_text}")
            scalar_text = _operation_plan_values_text(
                plan,
                field_name="scalar_values",
                max_values=max_values,
                max_chars=max_value_chars,
            )
            if scalar_text:
                fields.append(f"scalars={scalar_text}")
        else:
            fields.append("values=raw_rows_only")
        fields.append(f"sources={', '.join(source_labels[:8])}")
        operations = _operation_plan_sequence_text(plan)
        if operations:
            fields.append(f"ops={operations}")
        audit = _operation_plan_audit_text(plan)
        if audit:
            fields.append(f"audit={audit}")
        lines.append(f"  - {' | '.join(fields)}")
    return lines


def _memory_query_readiness_by_slot(
    memory_query_readiness_manifest: Mapping[str, Any] | None,
) -> dict[str, Mapping[str, Any]]:
    if (
        not isinstance(memory_query_readiness_manifest, Mapping)
        or not memory_query_readiness_manifest.get("applied")
    ):
        return {}
    raw_readiness = memory_query_readiness_manifest.get("readiness_index") or ()
    if not isinstance(raw_readiness, Iterable) or isinstance(
        raw_readiness, (str, bytes)
    ):
        return {}
    readiness_by_slot: dict[str, Mapping[str, Any]] = {}
    for readiness in raw_readiness:
        if not isinstance(readiness, Mapping):
            continue
        slot_id = str(readiness.get("slot_id") or "")
        if not slot_id:
            continue
        readiness_by_slot[slot_id] = readiness
    return readiness_by_slot


def _operation_plan_query_readiness(
    plan: Mapping[str, Any],
    *,
    readiness_by_slot: Mapping[str, Mapping[str, Any]],
    require_readiness: bool,
    required_readiness_modes: tuple[str, ...],
) -> Mapping[str, Any] | None:
    slot_id = str(plan.get("slot_id") or "")
    if not slot_id:
        return None
    readiness = readiness_by_slot.get(slot_id)
    if not isinstance(readiness, Mapping):
        return None
    if str(readiness.get("readiness_state") or "") != "guarded_ready":
        return None
    raw_safe_modes = readiness.get("safe_consumption_modes") or ()
    if not isinstance(raw_safe_modes, Iterable) or isinstance(
        raw_safe_modes, (str, bytes)
    ):
        return None
    safe_modes = {str(mode) for mode in raw_safe_modes}
    if not set(required_readiness_modes).issubset(safe_modes):
        return None
    query_gate = readiness.get("query_gate") or {}
    if not isinstance(query_gate, Mapping):
        return None
    if query_gate.get("requires_visible_raw_rows") is False:
        return None
    if not require_readiness:
        return readiness
    return readiness


def _operation_plan_readiness_fields(
    readiness: Mapping[str, Any] | None,
) -> tuple[str, ...]:
    if not isinstance(readiness, Mapping):
        return ()
    fields = ["ready=guarded_additive"]
    query_gate = readiness.get("query_gate") or {}
    if isinstance(query_gate, Mapping) and not bool(
        query_gate.get("replace_state_value_guide_allowed", False)
    ):
        fields.append("replace=blocked")
    verification = readiness.get("verification_readiness") or {}
    if isinstance(verification, Mapping):
        answer_gate = _single_line(str(verification.get("answer_gate") or ""))
        if answer_gate:
            fields.append(f"answer_gate={_truncate_text(answer_gate, 42)}")
    return tuple(fields)


def _operation_plan_visible_source_ids(
    plan: Mapping[str, Any],
    *,
    visible_source_ids: frozenset[str],
    question_scope: str,
) -> tuple[str, ...]:
    source_expansion = plan.get("source_expansion_plan") or {}
    if not isinstance(source_expansion, Mapping):
        source_expansion = {}
    source_fields = (
        ("current_source_order", "historical_source_order", "all_source_ids")
        if question_scope == "current"
        else ("historical_source_order", "current_source_order", "all_source_ids")
    )
    source_ids: list[str] = []
    for field_name in source_fields:
        raw_source_ids = source_expansion.get(field_name) or ()
        if not isinstance(raw_source_ids, Iterable) or isinstance(
            raw_source_ids, (str, bytes)
        ):
            continue
        for raw_source_id in raw_source_ids:
            source_id = str(raw_source_id)
            if source_id not in visible_source_ids or source_id in source_ids:
                continue
            source_ids.append(source_id)
    return tuple(source_ids)


def _memory_operation_context_organizer(
    *,
    question: str,
    route: RouteResult,
    rows: tuple[EvidenceRow, ...],
    memory_operation_plan: Mapping[str, Any] | None,
    memory_query_readiness_manifest: Mapping[str, Any] | None,
    max_plans: int,
    required_readiness_modes: tuple[str, ...],
) -> tuple[tuple[EvidenceRow, ...], dict[str, Any]]:
    trace: dict[str, Any] = {
        "enabled": True,
        "applied": False,
        "trace_only": False,
        "information_need": route.information_need,
        "required_readiness_modes": list(required_readiness_modes),
        "candidate_count": 0,
        "ready_visible_plan_count": 0,
        "selected_plan_count": 0,
        "boosted_source_ids": [],
        "changed_order": False,
        "values_rendered_to_prompt": False,
        "clean_note": (
            "Readiness-gated context organization over already selected raw rows. "
            "It uses build-owned operation plans only to order visible source rows; "
            "derived values are not rendered and final answer evidence remains raw rows."
        ),
    }
    if (
        not rows
        or not memory_operation_plan
        or not memory_operation_plan.get("applied")
        or max_plans <= 0
    ):
        trace["reason"] = "missing_rows_or_operation_plan"
        return rows, trace
    raw_plans = memory_operation_plan.get("workspace_operation_plans") or ()
    if not isinstance(raw_plans, Iterable) or isinstance(raw_plans, (str, bytes)):
        trace["reason"] = "invalid_operation_plan"
        return rows, trace

    visible_source_ids = frozenset(row.source_id for row in rows)
    readiness_by_slot = _memory_query_readiness_by_slot(
        memory_query_readiness_manifest
    )
    question_terms = _content_terms(question).difference(
        MEMORY_STATE_GUIDE_ALIGNMENT_WEAK_TERMS
    )
    question_scope = _workspace_question_scope(question, route)
    candidates: list[
        tuple[float, int, Mapping[str, Any], tuple[str, ...], Mapping[str, Any]]
    ] = []
    raw_candidate_count = 0
    for ordinal, raw_plan in enumerate(raw_plans):
        if not isinstance(raw_plan, Mapping):
            continue
        if raw_plan.get("source_backed") is False:
            continue
        if str(raw_plan.get("memory_tier") or "") == "quarantine_memory":
            continue
        raw_candidate_count += 1
        readiness = _operation_plan_query_readiness(
            raw_plan,
            readiness_by_slot=readiness_by_slot,
            require_readiness=True,
            required_readiness_modes=required_readiness_modes,
        )
        if readiness is None:
            continue
        source_ids = _operation_plan_visible_source_ids(
            raw_plan,
            visible_source_ids=visible_source_ids,
            question_scope=question_scope,
        )
        if not source_ids:
            continue
        score = _operation_plan_score(
            raw_plan,
            question_terms=question_terms,
            route=route,
            question_scope=question_scope,
        )
        if score <= 0:
            continue
        candidates.append((score, -ordinal, raw_plan, source_ids, readiness))

    trace["candidate_count"] = raw_candidate_count
    trace["ready_visible_plan_count"] = len(candidates)
    if not candidates:
        trace["reason"] = "no_ready_visible_plan"
        return rows, trace

    candidates.sort(reverse=True)
    selected = candidates[:max_plans]
    source_scores: dict[str, float] = {}
    selected_plans: list[dict[str, Any]] = []
    for score, _, plan, source_ids, readiness in selected:
        selected_plans.append(
            {
                "slot_id": str(plan.get("slot_id") or ""),
                "score": score,
                "memory_tier": str(plan.get("memory_tier") or ""),
                "memory_type": str(plan.get("memory_type") or ""),
                "subject": _single_line(str(plan.get("subject") or "")),
                "predicate": _single_line(str(plan.get("predicate") or "")),
                "lifecycle_state": str(plan.get("lifecycle_state") or ""),
                "readiness_state": str(readiness.get("readiness_state") or ""),
                "source_ids": list(source_ids[:8]),
                "operation_sequence": list(plan.get("operation_sequence") or ())[:8],
            }
        )
        for source_rank, source_id in enumerate(source_ids):
            source_score = score + max(0.0, 1.0 - (source_rank * 0.1))
            source_scores[source_id] = max(
                source_scores.get(source_id, 0.0), source_score
            )

    if not source_scores:
        trace["reason"] = "no_visible_sources_selected"
        return rows, trace

    original_source_order = [row.source_id for row in rows]
    original_index = {row.source_id: index for index, row in enumerate(rows)}
    organized_rows = tuple(
        sorted(
            rows,
            key=lambda row: (
                0 if row.source_id in source_scores else 1,
                -source_scores.get(row.source_id, 0.0),
                original_index.get(row.source_id, 1_000_000),
            ),
        )
    )
    new_source_order = [row.source_id for row in organized_rows]
    boosted_source_ids = [
        source_id for source_id in new_source_order if source_id in source_scores
    ]
    trace.update(
        {
            "applied": True,
            "reason": "ready_visible_sources_prioritized",
            "selected_plan_count": len(selected_plans),
            "selected_plans": selected_plans,
            "boosted_source_ids": boosted_source_ids[:16],
            "changed_order": original_source_order != new_source_order,
        }
    )
    return organized_rows, trace


def _memory_operation_readiness_audit(
    *,
    question: str,
    route: RouteResult,
    rows: tuple[EvidenceRow, ...],
    memory_operation_plan: Mapping[str, Any] | None,
    memory_query_readiness_manifest: Mapping[str, Any] | None,
    max_plans: int,
    required_readiness_modes: tuple[str, ...],
) -> dict[str, Any]:
    audit: dict[str, Any] = {
        "enabled": True,
        "applied": False,
        "trace_only": True,
        "information_need": route.information_need,
        "required_readiness_modes": list(required_readiness_modes),
        "candidate_count": 0,
        "ready_visible_plan_count": 0,
        "selected_plans": [],
        "clean_note": (
            "Trace-only readiness audit from build-owned operation plans. It is "
            "not included in the answer prompt, answer cache key, retrieval, "
            "repair, or finalizer."
        ),
    }
    if (
        not rows
        or not memory_operation_plan
        or not memory_operation_plan.get("applied")
        or max_plans <= 0
    ):
        audit["reason"] = "missing_rows_or_operation_plan"
        return audit
    raw_plans = memory_operation_plan.get("workspace_operation_plans") or ()
    if not isinstance(raw_plans, Iterable) or isinstance(raw_plans, (str, bytes)):
        audit["reason"] = "invalid_operation_plan"
        return audit
    source_to_memory_index = {
        row.source_id: index for index, row in enumerate(rows, start=1)
    }
    readiness_by_slot = _memory_query_readiness_by_slot(
        memory_query_readiness_manifest
    )
    question_terms = _content_terms(question).difference(
        MEMORY_STATE_GUIDE_ALIGNMENT_WEAK_TERMS
    )
    question_scope = _workspace_question_scope(question, route)
    candidates: list[
        tuple[float, int, Mapping[str, Any], tuple[str, ...], Mapping[str, Any]]
    ] = []
    raw_candidate_count = 0
    for ordinal, raw_plan in enumerate(raw_plans):
        if not isinstance(raw_plan, Mapping):
            continue
        raw_candidate_count += 1
        if raw_plan.get("source_backed") is False:
            continue
        if str(raw_plan.get("memory_tier") or "") == "quarantine_memory":
            continue
        readiness = _operation_plan_query_readiness(
            raw_plan,
            readiness_by_slot=readiness_by_slot,
            require_readiness=True,
            required_readiness_modes=required_readiness_modes,
        )
        if readiness is None:
            continue
        source_labels = _operation_plan_source_labels(
            raw_plan,
            source_to_memory_index=source_to_memory_index,
            question_scope=question_scope,
        )
        if not source_labels:
            continue
        score = _operation_plan_score(
            raw_plan,
            question_terms=question_terms,
            route=route,
            question_scope=question_scope,
        )
        if score <= 0:
            continue
        candidates.append((score, -ordinal, raw_plan, source_labels, readiness))
    audit["candidate_count"] = raw_candidate_count
    audit["ready_visible_plan_count"] = len(candidates)
    if not candidates:
        audit["reason"] = "no_ready_visible_plan"
        return audit
    candidates.sort(reverse=True)
    selected = sorted(
        candidates[:max_plans],
        key=lambda item: (
            str(item[2].get("memory_tier") or ""),
            str(item[2].get("memory_type") or ""),
            str(item[2].get("subject") or ""),
            str(item[2].get("predicate") or ""),
            item[1],
        ),
    )
    selected_plans: list[dict[str, Any]] = []
    for score, _, plan, source_labels, readiness in selected:
        query_gate = readiness.get("query_gate") or {}
        verification = readiness.get("verification_readiness") or {}
        selected_plans.append(
            {
                "slot_id": str(plan.get("slot_id") or ""),
                "score": score,
                "memory_tier": str(plan.get("memory_tier") or ""),
                "memory_type": str(plan.get("memory_type") or ""),
                "subject": _single_line(str(plan.get("subject") or "")),
                "predicate": _single_line(str(plan.get("predicate") or "")),
                "lifecycle_state": str(plan.get("lifecycle_state") or ""),
                "readiness_state": str(readiness.get("readiness_state") or ""),
                "safe_consumption_modes": list(
                    readiness.get("safe_consumption_modes") or ()
                )[:8],
                "replace_state_value_guide_allowed": bool(
                    isinstance(query_gate, Mapping)
                    and query_gate.get("replace_state_value_guide_allowed", False)
                ),
                "answer_gate": (
                    str(verification.get("answer_gate") or "")
                    if isinstance(verification, Mapping)
                    else ""
                ),
                "source_labels": list(source_labels[:8]),
                "operation_sequence": list(plan.get("operation_sequence") or ())[:8],
                "values_rendered_to_prompt": False,
            }
        )
    audit["applied"] = True
    audit["reason"] = "ready_visible_plans_selected"
    audit["selected_plans"] = selected_plans
    return audit


def _operation_plan_source_labels(
    plan: Mapping[str, Any],
    *,
    source_to_memory_index: Mapping[str, int],
    question_scope: str,
) -> tuple[str, ...]:
    source_expansion = plan.get("source_expansion_plan") or {}
    if not isinstance(source_expansion, Mapping):
        source_expansion = {}
    source_fields = (
        ("current_source_order", "historical_source_order", "all_source_ids")
        if question_scope == "current"
        else ("historical_source_order", "current_source_order", "all_source_ids")
    )
    labels: list[str] = []
    for field_name in source_fields:
        raw_source_ids = source_expansion.get(field_name) or ()
        if not isinstance(raw_source_ids, Iterable) or isinstance(
            raw_source_ids, (str, bytes)
        ):
            continue
        for source_id in raw_source_ids:
            index = source_to_memory_index.get(str(source_id))
            if index is None:
                continue
            label = f"Memory {index}"
            if label not in labels:
                labels.append(label)
    return tuple(labels)


def _operation_plan_score(
    plan: Mapping[str, Any],
    *,
    question_terms: frozenset[str],
    route: RouteResult,
    question_scope: str,
) -> float:
    state_management = plan.get("state_management_plan") or {}
    if not isinstance(state_management, Mapping):
        state_management = {}
    text_parts = [
        str(plan.get("memory_type") or ""),
        str(plan.get("subject") or ""),
        str(plan.get("predicate") or ""),
        *(str(value) for value in state_management.get("active_values") or ()),
        *(str(value) for value in state_management.get("superseded_values") or ()),
        *(str(value) for value in state_management.get("scalar_values") or ()),
    ]
    slot_terms = _content_terms(" ".join(text_parts)).difference(
        MEMORY_STATE_GUIDE_ALIGNMENT_WEAK_TERMS
    )
    overlap = len(question_terms.intersection(slot_terms))
    score = float(overlap)
    memory_type = str(plan.get("memory_type") or "").lower()
    if route.information_need == "current_state":
        if memory_type in {"state", "profile", "preference", "relationship"}:
            score += 2.0
        if str(plan.get("lifecycle_state") or "") == "active_with_history":
            score += 1.0
        if bool(plan.get("conflict_cluster")):
            score += 1.0
        if question_scope == "current" and state_management.get("active_values"):
            score += 1.0
    elif route.information_need == "profile_preference":
        if memory_type in {"profile", "preference", "relationship"}:
            score += 1.5
    if state_management.get("active_values") or state_management.get(
        "superseded_values"
    ):
        score += 0.5
    return score


def _operation_plan_values_text(
    plan: Mapping[str, Any],
    *,
    field_name: str,
    max_values: int,
    max_chars: int,
) -> str:
    state_management = plan.get("state_management_plan") or {}
    if not isinstance(state_management, Mapping):
        return ""
    values = [
        _truncate_text(_single_line(str(value)), max_chars)
        for value in state_management.get(field_name) or ()
        if str(value).strip()
    ][:max_values]
    return ", ".join(dict.fromkeys(values))


def _operation_plan_view_modes_text(plan: Mapping[str, Any]) -> str:
    view_policy = plan.get("view_policy") or {}
    if not isinstance(view_policy, Mapping):
        return ""
    modes = [
        _single_line(str(mode))
        for mode in view_policy.get("supported_views") or ()
        if str(mode).strip()
    ][:4]
    return ", ".join(dict.fromkeys(modes))


def _operation_plan_sequence_text(plan: Mapping[str, Any]) -> str:
    operations = [
        _single_line(str(operation))
        for operation in plan.get("operation_sequence") or ()
        if str(operation).strip()
    ][:6]
    return ", ".join(dict.fromkeys(operations))


def _operation_plan_audit_text(plan: Mapping[str, Any]) -> str:
    audit_plan = plan.get("audit_plan") or {}
    if not isinstance(audit_plan, Mapping):
        return ""
    obligations = [
        _single_line(str(obligation))
        for obligation in audit_plan.get("obligations") or ()
        if str(obligation).strip()
    ]
    interesting = [
        obligation
        for obligation in obligations
        if obligation
        not in {"verify_raw_source_support", "audit_slot_scope"}
    ][:4]
    return ", ".join(dict.fromkeys(interesting))


def _workspace_question_scope(question: str, route: RouteResult) -> str:
    lowered = question.lower()
    if route.information_need == "current_state" or re.search(
        r"\b(current|currently|latest|now|recent|recently|newest|today)\b",
        lowered,
    ):
        return "current"
    if re.search(
        r"\b(previous|previously|before|earlier|original|initial|old|past|used to|history)\b",
        lowered,
    ):
        return "historical"
    return "general"


def _workspace_group_source_labels(
    group: Mapping[str, Any],
    *,
    source_to_memory_index: Mapping[str, int],
    question_scope: str,
) -> tuple[str, ...]:
    source_ids: list[str] = []
    if question_scope == "current":
        source_ids.extend(str(value) for value in group.get("current_source_order") or ())
        source_ids.extend(str(value) for value in group.get("historical_source_order") or ())
    elif question_scope == "historical":
        source_ids.extend(str(value) for value in group.get("historical_source_order") or ())
        source_ids.extend(str(value) for value in group.get("current_source_order") or ())
    else:
        source_ids.extend(str(value) for value in group.get("source_ids") or ())
    labels = []
    for source_id in source_ids:
        memory_index = source_to_memory_index.get(source_id)
        if memory_index is not None:
            labels.append(f"Memory {memory_index}")
    return tuple(dict.fromkeys(labels))


def _workspace_visible_values(
    group: Mapping[str, Any],
    *,
    source_to_memory_index: Mapping[str, int],
    max_values: int,
    question_scope: str,
) -> tuple[dict[str, Any], ...]:
    raw_values = group.get("values") or ()
    if not isinstance(raw_values, Iterable) or isinstance(raw_values, (str, bytes)):
        return ()
    values: list[dict[str, Any]] = []
    seen: set[tuple[str, str, tuple[str, ...]]] = set()
    for raw_value in raw_values:
        if not isinstance(raw_value, Mapping):
            continue
        source_labels = _workspace_value_source_labels(
            raw_value,
            source_to_memory_index=source_to_memory_index,
        )
        if not source_labels:
            continue
        status = _single_line(str(raw_value.get("status") or "active")) or "active"
        value_text = _single_line(str(raw_value.get("value") or ""))
        scalar_values = tuple(
            _single_line(str(value))
            for value in raw_value.get("scalar_values") or ()
            if str(value).strip()
        )
        if not value_text and not scalar_values:
            continue
        key = (status, value_text, source_labels)
        if key in seen:
            continue
        seen.add(key)
        values.append(
            {
                "status": status,
                "value": value_text,
                "scalar_values": scalar_values,
                "source_labels": source_labels,
                "time": _single_line(str(raw_value.get("time") or "")),
            }
        )
    values.sort(key=lambda value: _workspace_value_sort_key(value, question_scope))
    return tuple(values[: max(1, max_values * 2)])


def _workspace_value_source_labels(
    value: Mapping[str, Any],
    *,
    source_to_memory_index: Mapping[str, int],
) -> tuple[str, ...]:
    labels = []
    for source_id in value.get("source_ids") or ():
        memory_index = source_to_memory_index.get(str(source_id))
        if memory_index is not None:
            labels.append(f"Memory {memory_index}")
    return tuple(dict.fromkeys(labels))


def _workspace_value_sort_key(value: Mapping[str, Any], question_scope: str) -> tuple[int, str]:
    status = str(value.get("status") or "active")
    if question_scope == "current":
        status_rank = 0 if status == "active" else 1
    elif question_scope == "historical":
        status_rank = 0 if status != "active" else 1
    else:
        status_rank = 0 if status == "active" else 1
    return (status_rank, str(value.get("time") or ""))


def _workspace_group_score(
    group: Mapping[str, Any],
    *,
    visible_values: tuple[dict[str, Any], ...],
    question_terms: frozenset[str],
    route: RouteResult,
    question_scope: str,
) -> float:
    basis_parts = [
        str(group.get("group_type") or ""),
        str(group.get("memory_type") or ""),
        str(group.get("subject") or ""),
        str(group.get("predicate") or ""),
        str(group.get("lifecycle_state") or ""),
    ]
    for value in visible_values:
        basis_parts.append(str(value.get("value") or ""))
        basis_parts.extend(str(item) for item in value.get("scalar_values") or ())
    basis = " ".join(basis_parts).replace("_", " ").replace("-", " ")
    overlap = len(question_terms.intersection(_content_terms(basis)))
    memory_type = str(group.get("memory_type") or "")
    type_match = _memory_type_name_matches_route(memory_type, route)
    if overlap <= 0 and not type_match:
        return 0.0
    if overlap <= 0 and route.information_need != "profile_preference":
        return 0.0
    score = overlap * 2.0
    if type_match:
        score += 0.7
    if bool(group.get("conflict_cluster")) and route.information_need == "current_state":
        score += 0.8
    lifecycle = str(group.get("lifecycle_state") or "")
    if lifecycle in {"active_with_history", "has_superseded_context"}:
        score += 0.4
    if question_scope == "historical" and any(
        value.get("status") != "active" for value in visible_values
    ):
        score += 0.5
    if any(value.get("scalar_values") for value in visible_values):
        score += 0.2
    return score


def _workspace_values_text(
    visible_values: tuple[dict[str, Any], ...],
    *,
    status: str,
    max_values: int,
    max_chars: int,
) -> str:
    parts = []
    for value in visible_values:
        if value.get("status") != status:
            continue
        text = _truncate_text(_single_line(str(value.get("value") or "")), max_chars)
        if not text and value.get("scalar_values"):
            text = _truncate_text(str(value["scalar_values"][0]), max_chars)
        if not text:
            continue
        source_text = ", ".join(value.get("source_labels") or ())
        time_text = str(value.get("time") or "unknown")
        parts.append(f"{text} [{source_text}; time={time_text}]")
        if len(parts) >= max_values:
            break
    return "; ".join(parts)


def _workspace_historical_values_text(
    visible_values: tuple[dict[str, Any], ...],
    *,
    max_values: int,
    max_chars: int,
) -> str:
    parts = []
    for value in visible_values:
        if value.get("status") == "active":
            continue
        text = _truncate_text(_single_line(str(value.get("value") or "")), max_chars)
        if not text:
            continue
        source_text = ", ".join(value.get("source_labels") or ())
        time_text = str(value.get("time") or "unknown")
        parts.append(f"{text} [{source_text}; time={time_text}]")
        if len(parts) >= max_values:
            break
    return "; ".join(parts)


def _workspace_scalar_values_text(
    visible_values: tuple[dict[str, Any], ...],
    *,
    max_values: int,
) -> str:
    scalars = []
    seen: set[str] = set()
    for value in visible_values:
        source_text = ", ".join(value.get("source_labels") or ())
        for scalar_value in value.get("scalar_values") or ():
            scalar_text = _truncate_text(_single_line(str(scalar_value)), 60)
            key = f"{scalar_text}|{source_text}"
            if not scalar_text or key in seen:
                continue
            seen.add(key)
            scalars.append(f"{scalar_text} [{source_text}]")
            if len(scalars) >= max_values:
                return "; ".join(scalars)
    return "; ".join(scalars)


def _external_profile_activation_guide_lines(
    *,
    question: str,
    route: RouteResult,
    rows: tuple[EvidenceRow, ...],
    memory_records: tuple[MemoryRecord, ...],
    max_records: int,
    max_value_chars: int,
) -> list[str]:
    """Preference/profile activation map grounded in visible raw rows."""

    if (
        route.information_need != "profile_preference"
        or not rows
        or not memory_records
        or max_records <= 0
    ):
        return []

    source_to_memory_index = {
        row.source_id: index for index, row in enumerate(rows, start=1)
    }
    question_terms = _content_terms(question)
    candidates: list[tuple[float, int, MemoryRecord, tuple[str, ...]]] = []
    for ordinal, record in enumerate(memory_records):
        source_labels = _memory_record_source_labels(record, source_to_memory_index)
        if not source_labels:
            continue
        score = _profile_activation_record_score(
            record,
            question_terms=question_terms,
        )
        if score <= 0:
            continue
        candidates.append((score, -ordinal, record, source_labels))

    if not candidates:
        return []

    candidates.sort(reverse=True)
    selected = candidates[:max_records]
    lines = [
        "Use this source-backed profile view to activate durable preferences, constraints, prior choices, and successful examples relevant to advice/profile questions.",
        "- Each record is linked to visible raw Memory Context rows; verify final claims against those rows.",
        "- Do not turn a one-time event into a stable preference, but it can guide a compatible suggestion when the user asks for advice.",
        "- records:",
    ]
    for _, _, record, source_labels in selected:
        fields = [
            f"type={record.memory_type}",
            f"status={record.status or 'active'}",
        ]
        if record.subject:
            fields.append(
                f"subject={_truncate_text(_single_line(record.subject), 60)}"
            )
        if record.predicate:
            fields.append(
                f"predicate={_truncate_text(_single_line(record.predicate), 60)}"
            )
        value = record.value or record.text
        if value:
            fields.append(
                f"value={_truncate_text(_single_line(value), max_value_chars)}"
            )
        time_value = (
            record.event_time
            or record.valid_from
            or record.mention_time
            or record.timestamp
            or "unknown"
        )
        fields.append(f"time={_single_line(time_value)}")
        fields.append(f"sources={', '.join(source_labels[:6])}")
        lines.append(f"  - {' | '.join(fields)}")
    return lines


def _profile_activation_record_score(
    record: MemoryRecord,
    *,
    question_terms: frozenset[str],
) -> float:
    memory_type = (record.memory_type or "").lower()
    type_weights = {
        "preference": 3.0,
        "profile": 2.5,
        "state": 1.8,
        "fact": 1.2,
        "event": 0.8,
    }
    type_score = type_weights.get(memory_type, 0.0)
    if type_score <= 0:
        return 0.0

    basis_terms = _content_terms(_memory_record_hint_basis(record))
    overlap = len(question_terms.intersection(basis_terms))
    if overlap <= 0 and memory_type not in {"preference", "profile"}:
        return 0.0

    score = type_score + overlap * 2.0
    if record.status == "active":
        score += 0.4
    elif record.status == "superseded":
        score -= 0.5
    if record.subject or record.predicate or record.value:
        score += 0.4
    return score


def _external_memory_state_guide_lines(
    *,
    question: str,
    route: RouteResult,
    rows: tuple[EvidenceRow, ...],
    memory_records: tuple[MemoryRecord, ...],
    state_conflict_manifest: Mapping[str, Any] | None,
    max_records: int,
    max_value_chars: int,
    include_superseded: bool,
    require_conflict: bool = False,
    conflict_source: str = "records",
    require_active_superseded_pair: bool = False,
    require_slot_overlap: bool = False,
    require_stateful_slot: bool = False,
) -> list[str]:
    """Compact managed-memory state view grounded in visible raw rows."""

    if not rows or not memory_records or max_records <= 0:
        return []

    source_to_memory_index = {
        row.source_id: index for index, row in enumerate(rows, start=1)
    }
    question_terms = _content_terms(question)
    candidates: list[tuple[float, int, MemoryRecord, tuple[str, ...]]] = []
    for ordinal, record in enumerate(memory_records):
        if record.status != "active" and not include_superseded:
            continue
        source_labels = _memory_record_source_labels(record, source_to_memory_index)
        if not source_labels:
            continue
        score = _memory_state_record_score(
            record,
            question_terms=question_terms,
            route=route,
        )
        if score <= 0:
            continue
        candidates.append((score, -ordinal, record, source_labels))

    if not candidates:
        return []
    if require_conflict:
        candidate_records_by_slot: dict[tuple[str, str, str], list[MemoryRecord]] = {}
        for _, _, record, _ in candidates:
            candidate_records_by_slot.setdefault(
                _memory_state_slot_key(record),
                [],
            ).append(record)
        if conflict_source == "build_manifest":
            conflict_slot_keys = _memory_state_manifest_conflict_slot_keys(
                state_conflict_manifest,
                candidate_records_by_slot=candidate_records_by_slot,
                question_terms=question_terms,
                require_active_superseded_pair=require_active_superseded_pair,
                require_slot_overlap=require_slot_overlap,
                require_stateful_slot=require_stateful_slot,
            )
        else:
            conflict_slot_keys = _memory_state_conflict_slot_keys(
                (record for _, _, record, _ in candidates),
                question_terms=question_terms,
                require_active_superseded_pair=require_active_superseded_pair,
                require_slot_overlap=require_slot_overlap,
                require_stateful_slot=require_stateful_slot,
            )
        if not conflict_slot_keys:
            return []
        candidates = [
            item
            for item in candidates
            if _memory_state_slot_key(item[2]) in conflict_slot_keys
        ]
        if not candidates:
            return []

    candidates.sort(reverse=True)
    selected = candidates[:max_records]
    selected.sort(
        key=lambda item: (
            _memory_state_slot_key(item[2]),
            0 if item[2].status == "active" else 1,
            item[2].timestamp or "",
            item[1],
        )
    )
    has_superseded = any(record.status == "superseded" for _, _, record, _ in selected)

    lines = [
        "Use this managed-memory view to locate current, historical, and conflicting state candidates; verify every final fact in the cited raw Memory Context rows.",
        "- active means the build-stage manager kept this record as the latest candidate for its subject/predicate; superseded means an older conflicting candidate.",
    ]
    if has_superseded:
        lines.append(
            "- For current/latest questions, compare active and superseded candidates against the cited rows; for previous/original/before questions, the superseded row may be the requested historical value."
        )
    lines.append("- records:")
    for _, _, record, source_labels in selected:
        fields = [
            f"type={record.memory_type}",
            f"status={record.status or 'active'}",
        ]
        if record.subject:
            fields.append(
                f"subject={_truncate_text(_single_line(record.subject), 60)}"
            )
        if record.predicate:
            fields.append(
                f"predicate={_truncate_text(_single_line(record.predicate), 60)}"
            )
        value = record.value or record.text
        if value:
            fields.append(
                f"value={_truncate_text(_single_line(value), max_value_chars)}"
            )
        time_value = (
            record.event_time
            or record.valid_from
            or record.mention_time
            or record.timestamp
            or "unknown"
        )
        fields.append(f"time={_single_line(time_value)}")
        fields.append(f"valid_to={record.valid_to or 'open'}")
        if record.superseded_by:
            fields.append(f"superseded_by={record.superseded_by}")
        fields.append(f"sources={', '.join(source_labels[:6])}")
        lines.append(f"  - {' | '.join(fields)}")
    return lines


def _external_memory_value_slot_guide_lines(
    *,
    question: str,
    route: RouteResult,
    rows: tuple[EvidenceRow, ...],
    scalar_value_manifest: Mapping[str, Any] | None,
    memory_object_index: Mapping[str, Any] | None = None,
    max_slots: int,
    max_values: int,
    memory_types: tuple[str, ...] = (),
) -> list[str]:
    """Compact build-owned value slot view grounded in visible raw rows."""

    value_slot_index: Any = ()
    if memory_object_index and memory_object_index.get("applied"):
        value_slot_index = memory_object_index.get("value_slot_index") or ()
    elif scalar_value_manifest and scalar_value_manifest.get("applied"):
        value_slot_index = (
            scalar_value_manifest.get("slot_index")
            or scalar_value_manifest.get("slot_samples")
            or ()
        )

    if (
        not rows
        or not value_slot_index
        or max_slots <= 0
        or max_values <= 0
    ):
        return []

    source_to_memory_index = {
        row.source_id: index for index, row in enumerate(rows, start=1)
    }
    question_terms = _content_terms(question).difference(
        MEMORY_STATE_GUIDE_ALIGNMENT_WEAK_TERMS
    )
    allowed_memory_types = frozenset(
        str(value).strip().lower() for value in memory_types if str(value).strip()
    )
    candidates: list[tuple[float, int, Mapping[str, Any], tuple[dict[str, Any], ...]]] = []
    for ordinal, raw_slot in enumerate(value_slot_index):
        if not isinstance(raw_slot, Mapping):
            continue
        memory_type = str(raw_slot.get("memory_type") or "").strip().lower()
        if allowed_memory_types and memory_type not in allowed_memory_types:
            continue
        if raw_slot.get("source_backed") is False:
            continue
        visible_values = _memory_value_slot_visible_values(
            raw_slot,
            source_to_memory_index=source_to_memory_index,
            max_values=max_values,
        )
        if not visible_values:
            continue
        score = _memory_value_slot_score(
            raw_slot,
            visible_values=visible_values,
            question_terms=question_terms,
            route=route,
        )
        if score <= 0:
            continue
        candidates.append((score, -ordinal, raw_slot, visible_values))

    if not candidates:
        return []

    candidates.sort(reverse=True)
    selected = sorted(
        candidates[:max_slots],
        key=lambda item: (
            str(item[2].get("memory_type") or ""),
            str(item[2].get("subject") or ""),
            str(item[2].get("predicate") or ""),
            item[1],
        ),
    )
    has_superseded = any(
        value.get("status") == "superseded"
        for _, _, _, visible_values in selected
        for value in visible_values
    )

    lines = [
        "Use this build-owned value slot view to organize current, historical, scalar, and conflicting values; verify every final fact in the cited raw Memory Context rows.",
    ]
    if has_superseded:
        lines.append(
            "- active values are current candidates for a slot; superseded values are retained for historical, previous, or before-scope questions."
        )
    lines.append("- slots:")
    for _, _, slot, visible_values in selected:
        fields = [
            f"type={_single_line(str(slot.get('memory_type') or 'memory'))}",
        ]
        subject = _single_line(str(slot.get("subject") or ""))
        predicate = _single_line(str(slot.get("predicate") or ""))
        if subject:
            fields.append(f"subject={_truncate_text(subject, 60)}")
        if predicate:
            fields.append(f"predicate={_truncate_text(predicate, 60)}")
        active_text = _memory_value_slot_values_text(
            visible_values,
            status="active",
            max_values=max_values,
        )
        if active_text:
            fields.append(f"active_values={active_text}")
        superseded_text = _memory_value_slot_values_text(
            visible_values,
            status="superseded",
            max_values=max_values,
        )
        if superseded_text:
            fields.append(f"superseded_values={superseded_text}")
        scalar_text = _memory_value_slot_scalar_text(
            visible_values,
            max_values=max_values,
        )
        if scalar_text:
            fields.append(f"scalar_values={scalar_text}")
        source_labels = _memory_value_slot_source_label_text(visible_values)
        if source_labels:
            fields.append(f"sources={source_labels}")
        operation_hints = [
            str(hint)
            for hint in (slot.get("operation_hints") or ())
            if str(hint).strip()
        ][:4]
        if operation_hints:
            fields.append(f"operations={', '.join(operation_hints)}")
        lines.append(f"  - {' | '.join(fields)}")
    return lines


def _memory_value_slot_visible_values(
    slot: Mapping[str, Any],
    *,
    source_to_memory_index: Mapping[str, int],
    max_values: int,
) -> tuple[dict[str, Any], ...]:
    values: list[dict[str, Any]] = []
    seen: set[tuple[str, str, tuple[str, ...]]] = set()
    raw_values = slot.get("value_objects") or ()
    if not isinstance(raw_values, Iterable) or isinstance(raw_values, (str, bytes)):
        return ()
    for raw_value in raw_values:
        if not isinstance(raw_value, Mapping):
            continue
        source_labels = _memory_value_object_source_labels(
            raw_value,
            source_to_memory_index=source_to_memory_index,
        )
        if not source_labels:
            continue
        value_text = _single_line(str(raw_value.get("value") or ""))
        scalar_values = tuple(
            _single_line(str(value))
            for value in (raw_value.get("scalar_values") or ())
            if str(value).strip()
        )
        if not value_text and not scalar_values:
            continue
        status = _single_line(str(raw_value.get("status") or "active")) or "active"
        key = (status, value_text, source_labels)
        if key in seen:
            continue
        seen.add(key)
        values.append(
            {
                "status": status,
                "value": value_text,
                "scalar_values": scalar_values,
                "source_labels": source_labels,
                "time": _single_line(str(raw_value.get("time") or "")),
            }
        )
        if len(values) >= max(1, max_values * 2):
            break
    return tuple(values)


def _memory_value_object_source_labels(
    value_object: Mapping[str, Any],
    *,
    source_to_memory_index: Mapping[str, int],
) -> tuple[str, ...]:
    labels = []
    for source_id in value_object.get("source_ids") or ():
        memory_index = source_to_memory_index.get(str(source_id))
        if memory_index is not None:
            labels.append(f"Memory {memory_index}")
    return tuple(dict.fromkeys(labels))


def _memory_value_slot_score(
    slot: Mapping[str, Any],
    *,
    visible_values: tuple[dict[str, Any], ...],
    question_terms: frozenset[str],
    route: RouteResult,
) -> float:
    basis_parts = [
        str(slot.get("memory_type") or ""),
        str(slot.get("subject") or ""),
        str(slot.get("predicate") or ""),
    ]
    for value in visible_values:
        basis_parts.append(str(value.get("value") or ""))
        basis_parts.extend(str(item) for item in value.get("scalar_values") or ())
    basis = " ".join(basis_parts).replace("_", " ").replace("-", " ")
    overlap = len(question_terms.intersection(_content_terms(basis)))
    if overlap <= 0:
        return 0.0
    score = float(overlap * 2)
    memory_type = str(slot.get("memory_type") or "")
    if _memory_type_name_matches_route(memory_type, route):
        score += 0.6
    if any(value.get("status") == "active" for value in visible_values):
        score += 0.25
    if any(value.get("status") == "superseded" for value in visible_values):
        score += 0.5
    if any(value.get("scalar_values") for value in visible_values):
        score += 0.4
    if bool(slot.get("managed")):
        score += 0.2
    return score


def _memory_type_name_matches_route(memory_type: str, route: RouteResult) -> bool:
    normalized = memory_type.lower()
    if route.information_need == "current_state":
        return normalized in {"state", "profile", "preference", "relationship"}
    if route.information_need == "profile_preference":
        return normalized in {"preference", "profile", "state"}
    if route.information_need == "fact_lookup":
        return normalized in {"fact", "event", "relationship", "state", "profile"}
    return _memory_type_matches_route(memory_type, route)


def _memory_value_slot_values_text(
    visible_values: tuple[dict[str, Any], ...],
    *,
    status: str,
    max_values: int,
) -> str:
    parts = []
    for value in visible_values:
        if value.get("status") != status:
            continue
        value_text = _truncate_text(_single_line(str(value.get("value") or "")), 90)
        if not value_text and value.get("scalar_values"):
            value_text = _truncate_text(str(value["scalar_values"][0]), 90)
        if not value_text:
            continue
        source_text = ", ".join(value.get("source_labels") or ())
        time_text = str(value.get("time") or "unknown")
        parts.append(f"{value_text} [{source_text}; time={time_text}]")
        if len(parts) >= max_values:
            break
    return "; ".join(parts)


def _memory_value_slot_scalar_text(
    visible_values: tuple[dict[str, Any], ...],
    *,
    max_values: int,
) -> str:
    scalars = []
    seen: set[str] = set()
    for value in visible_values:
        source_text = ", ".join(value.get("source_labels") or ())
        for scalar_value in value.get("scalar_values") or ():
            scalar_text = _truncate_text(_single_line(str(scalar_value)), 60)
            key = f"{scalar_text}|{source_text}"
            if not scalar_text or key in seen:
                continue
            seen.add(key)
            scalars.append(f"{scalar_text} [{source_text}]")
            if len(scalars) >= max_values:
                return "; ".join(scalars)
    return "; ".join(scalars)


def _memory_value_slot_source_label_text(
    visible_values: tuple[dict[str, Any], ...],
) -> str:
    labels = []
    for value in visible_values:
        labels.extend(value.get("source_labels") or ())
    return ", ".join(dict.fromkeys(labels))


def _memory_record_source_labels(
    record: MemoryRecord,
    source_to_memory_index: Mapping[str, int],
) -> tuple[str, ...]:
    labels = []
    for source_id in record.source_ids:
        memory_index = source_to_memory_index.get(source_id)
        if memory_index is not None:
            labels.append(f"Memory {memory_index}")
    return tuple(dict.fromkeys(labels))


def _source_backed_memory_state_ledger(
    *,
    question: str,
    route: RouteResult,
    rows: tuple[EvidenceRow, ...],
    memory_records: tuple[MemoryRecord, ...],
    max_records: int,
    max_value_chars: int,
) -> dict[str, Any]:
    """Structured source-backed memory state index for repair-time review."""

    if not rows or not memory_records or max_records <= 0:
        return {
            "applied": False,
            "entries": [],
            "entry_count": 0,
            "reason": "no_rows_or_records",
        }

    source_to_memory_index = {
        row.source_id: index for index, row in enumerate(rows, start=1)
    }
    question_terms = _content_terms(question)
    focused_question_terms = set(question_terms).difference(
        MEMORY_STATE_GUIDE_ALIGNMENT_WEAK_TERMS
    )
    candidates: list[tuple[float, int, dict[str, Any]]] = []
    for ordinal, record in enumerate(memory_records):
        source_labels = _memory_record_source_labels(record, source_to_memory_index)
        if not source_labels:
            continue
        slot_terms = _memory_state_slot_alignment_terms(record)
        overlap_terms = tuple(sorted(focused_question_terms.intersection(slot_terms)))
        if not overlap_terms:
            continue
        stateful_slot = _memory_state_slot_is_stateful(
            record.memory_type,
            [record],
        )
        if len(overlap_terms) < 2 and not stateful_slot:
            continue
        score = _memory_state_record_score(
            record,
            question_terms=question_terms,
            route=route,
        ) + float(len(overlap_terms))
        if score <= 0:
            continue
        value = record.value or record.text
        time_value = (
            record.event_time
            or record.valid_from
            or record.mention_time
            or record.timestamp
            or "unknown"
        )
        candidates.append(
            (
                score,
                -ordinal,
                {
                    "memory_type": record.memory_type,
                    "status": record.status or "active",
                    "subject": _single_line(record.subject),
                    "predicate": _single_line(record.predicate),
                    "value": _truncate_text(_single_line(value), max_value_chars),
                    "time": _single_line(time_value),
                    "valid_to": record.valid_to or "open",
                    "source_labels": source_labels,
                    "overlap_terms": overlap_terms,
                    "stateful_slot": stateful_slot,
                },
            )
        )

    if not candidates:
        return {
            "applied": False,
            "entries": [],
            "entry_count": 0,
            "reason": "no_question_aligned_source_backed_state",
        }

    candidates.sort(reverse=True)
    entries = [entry for _score, _ordinal, entry in candidates[:max_records]]
    return {
        "applied": True,
        "entries": entries,
        "entry_count": len(entries),
        "clean_note": (
            "Source-backed typed memory ledger. Entries are only an index into "
            "cited raw Memory Context rows and are not independent evidence."
        ),
    }


def _memory_state_record_score(
    record: MemoryRecord,
    *,
    question_terms: frozenset[str],
    route: RouteResult,
) -> float:
    basis_terms = _content_terms(_memory_record_hint_basis(record))
    overlap = len(question_terms.intersection(basis_terms))
    type_match = _memory_type_matches_route(record.memory_type, route)
    score = float(overlap * 2)
    if type_match:
        score += 2.0
    if record.status == "active":
        score += 0.5
    elif record.status == "superseded" and route.information_need in {
        "current_state",
        "fact_lookup",
        "profile_preference",
    }:
        score += 0.25
    if record.subject or record.predicate or record.value:
        score += 0.5
    if overlap == 0 and not type_match:
        return 0.0
    return score


def _memory_state_conflict_slot_keys(
    records: Iterable[MemoryRecord],
    *,
    question_terms: frozenset[str] = frozenset(),
    require_active_superseded_pair: bool = False,
    require_slot_overlap: bool = False,
    require_stateful_slot: bool = False,
) -> set[tuple[str, str, str]]:
    slots: dict[tuple[str, str, str], list[MemoryRecord]] = {}
    for record in records:
        slots.setdefault(_memory_state_slot_key(record), []).append(record)

    conflict_keys: set[tuple[str, str, str]] = set()
    for key, slot_records in slots.items():
        if require_slot_overlap and not _memory_state_slot_matches_question(
            slot_records,
            question_terms=question_terms,
        ):
            continue
        if require_stateful_slot and not _memory_state_slot_is_stateful(
            key[0],
            slot_records,
        ):
            continue
        if require_active_superseded_pair and not _memory_state_slot_has_update_pair(
            slot_records
        ):
            continue
        values = set()
        for record in slot_records:
            value = _normalize_memory_value(record)
            if value:
                values.add(value)
        has_lifecycle_marker = any(
            (record.status or "active") == "superseded"
            or bool(record.superseded_by)
            or bool(record.valid_to)
            for record in slot_records
        )
        memory_type = key[0]
        has_value_conflict = (
            memory_type in MEMORY_STATE_GUIDE_VALUE_CONFLICT_TYPES
            and len(values) >= 2
        )
        if has_value_conflict or has_lifecycle_marker:
            conflict_keys.add(key)
    return conflict_keys


def _memory_state_slot_has_update_pair(records: list[MemoryRecord]) -> bool:
    active_values = set()
    superseded_values = set()
    for record in records:
        value = _normalize_memory_value(record)
        if not value:
            continue
        status = record.status or "active"
        if status == "superseded" or record.valid_to or record.superseded_by:
            superseded_values.add(value)
        else:
            active_values.add(value)
    return bool(active_values and superseded_values.difference(active_values))


def _memory_state_slot_matches_question(
    records: list[MemoryRecord],
    *,
    question_terms: frozenset[str],
) -> bool:
    if not question_terms:
        return False
    slot_terms: set[str] = set()
    for record in records:
        slot_terms.update(_memory_state_slot_alignment_terms(record))
    focused_question_terms = set(question_terms).difference(
        MEMORY_STATE_GUIDE_ALIGNMENT_WEAK_TERMS
    )
    return bool(slot_terms.intersection(focused_question_terms))


def _memory_state_slot_alignment_terms(record: MemoryRecord) -> frozenset[str]:
    text = " ".join((record.subject, record.predicate, record.value))
    text = text.replace("_", " ").replace("-", " ")
    return _content_terms(text)


def _memory_state_slot_is_stateful(
    memory_type: str,
    records: list[MemoryRecord],
) -> bool:
    if memory_type == "state":
        return True
    text = " ".join(
        " ".join((record.predicate, record.subject, record.value))
        for record in records
    )
    text = text.replace("_", " ").replace("-", " ")
    return bool(MEMORY_STATE_GUIDE_STATEFUL_SLOT_PATTERN.search(text))


def _memory_state_slot_key(record: MemoryRecord) -> tuple[str, str, str]:
    return (
        (record.memory_type or "").lower(),
        _single_line(record.subject).lower(),
        _single_line(record.predicate).lower(),
    )


def _memory_state_manifest_conflict_slot_keys(
    state_conflict_manifest: Mapping[str, Any] | None,
    *,
    candidate_records_by_slot: Mapping[tuple[str, str, str], list[MemoryRecord]],
    question_terms: frozenset[str],
    require_active_superseded_pair: bool,
    require_slot_overlap: bool,
    require_stateful_slot: bool,
) -> set[tuple[str, str, str]]:
    if not state_conflict_manifest or not state_conflict_manifest.get("applied"):
        return set()
    keys: set[tuple[str, str, str]] = set()
    for cluster in state_conflict_manifest.get("clusters") or ():
        if not isinstance(cluster, Mapping):
            continue
        if not cluster.get("source_backed"):
            continue
        key = (
            _single_line(str(cluster.get("memory_type") or "")).lower(),
            _single_line(str(cluster.get("subject") or "")).lower(),
            _single_line(str(cluster.get("predicate") or "")).lower(),
        )
        slot_records = candidate_records_by_slot.get(key) or []
        if not slot_records:
            continue
        if require_slot_overlap and not _memory_state_slot_matches_question(
            slot_records,
            question_terms=question_terms,
        ):
            continue
        if require_stateful_slot and not _memory_state_slot_is_stateful(
            key[0],
            slot_records,
        ):
            continue
        if require_active_superseded_pair and not _memory_state_slot_has_update_pair(
            slot_records
        ):
            continue
        keys.add(key)
    return keys


def _external_candidate_guide_lines(
    *,
    question: str,
    route: RouteResult,
    rows: tuple[EvidenceRow, ...],
    memory_records: tuple[MemoryRecord, ...],
    max_rows: int,
    snippet_chars: int,
    include_memory_hints: bool,
    max_memory_hints: int,
    memory_hint_chars: int,
) -> list[str]:
    """Compact source-preserving row map for candidate-heavy questions."""

    if not rows:
        return []

    memory_records_by_source = (
        _memory_records_by_source_id(memory_records)
        if include_memory_hints and max_memory_hints > 0
        else {}
    )
    selected = _candidate_guide_rows(
        question=question,
        route=route,
        rows=rows,
        memory_records_by_source=memory_records_by_source,
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
        memory_hints = _candidate_memory_hint_text(
            memory_records_by_source.get(row.source_id, ()),
            max_hints=max_memory_hints,
            max_chars=memory_hint_chars,
        )
        memory_hint_text = (
            f" | source_memory_hints={memory_hints}" if memory_hints else ""
        )
        snippet = _single_line(_query_snippet(row.text, question, snippet_chars))
        lines.append(
            f"  - Memory {memory_index}: date={row.timestamp or 'unknown'} "
            f"role={row.role} matched_terms={matched_text}{quantity_text}"
            f"{time_text}{memory_hint_text} | text=\"{snippet}\""
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
    if route.information_need == "fact_lookup":
        return (
            "- focus: match the requested answer slot exactly, compare close "
            "candidates, and avoid substituting related-topic rows for the asked "
            "person, object, place, action, or event."
        )
    return ""


def _candidate_guide_rows(
    *,
    question: str,
    route: RouteResult,
    rows: tuple[EvidenceRow, ...],
    memory_records_by_source: Mapping[str, tuple[MemoryRecord, ...]],
    max_rows: int,
) -> tuple[tuple[int, EvidenceRow], ...]:
    question_terms = _content_terms(question)
    scored: list[tuple[float, int, int, EvidenceRow]] = []
    for index, row in enumerate(rows, start=1):
        score = _candidate_guide_row_score(
            row,
            question_terms=question_terms,
            route=route,
            memory_records=memory_records_by_source.get(row.source_id, ()),
        )
        if row.retrieval_rank is not None:
            score += 1.0 / (row.retrieval_rank + 4.0)
        if row.role.lower() == "user":
            score += 0.15
        scored.append((score, -index, index, row))

    scored.sort(reverse=True)
    selected = sorted(
        _diverse_candidate_rows(scored, max_rows=max_rows),
        key=lambda item: item[2],
    )
    return tuple((index, row) for _, _, index, row in selected)


def _diverse_candidate_rows(
    scored: list[tuple[float, int, int, EvidenceRow]],
    *,
    max_rows: int,
) -> list[tuple[float, int, int, EvidenceRow]]:
    """Keep high-scoring candidate rows while reducing near-duplicate guide lines."""

    selected: list[tuple[float, int, int, EvidenceRow]] = []
    selected_signatures: list[frozenset[str]] = []
    selected_sessions: set[str] = set()

    def add(item: tuple[float, int, int, EvidenceRow]) -> None:
        selected.append(item)
        selected_signatures.append(_content_signature(item[3].text))
        selected_sessions.add(item[3].session_id)

    for item in scored:
        if len(selected) >= max_rows:
            break
        signature = _content_signature(item[3].text)
        same_session = item[3].session_id in selected_sessions
        near_duplicate = any(
            _signature_overlap(signature, existing) >= 0.7
            for existing in selected_signatures
        )
        if selected and same_session and near_duplicate:
            continue
        add(item)

    if len(selected) >= max_rows:
        return selected

    selected_ids = {item[3].source_id for item in selected}
    for item in scored:
        if len(selected) >= max_rows:
            break
        if item[3].source_id not in selected_ids:
            add(item)
            selected_ids.add(item[3].source_id)
    return selected


def _content_signature(text: str) -> frozenset[str]:
    return frozenset(term for term in _content_terms(text) if len(term) >= 4)


def _signature_overlap(left: frozenset[str], right: frozenset[str]) -> float:
    if not left or not right:
        return 0.0
    return len(left.intersection(right)) / len(left.union(right))


def _candidate_guide_row_score(
    row: EvidenceRow,
    *,
    question_terms: frozenset[str],
    route: RouteResult,
    memory_records: tuple[MemoryRecord, ...],
) -> float:
    row_terms = _content_terms(row.text)
    score = len(question_terms.intersection(row_terms)) * 2.0
    if memory_records:
        score += _source_memory_candidate_bonus(
            question_terms=question_terms,
            memory_records=memory_records,
            route=route,
        )
    if route.information_need in {"list_count", "temporal_lookup"} and _has_quantity_expression(row.text):
        score += 0.8
    if route.information_need in {"temporal_lookup", "current_state"} and (
        row.timestamp or _has_time_expression(row.text)
    ):
        score += 0.6
    if route.information_need in {"profile_preference", "current_state"} and _has_profile_or_state_signal(row.text):
        score += 0.7
    return score


def _memory_records_by_source_id(
    memory_records: tuple[MemoryRecord, ...],
) -> dict[str, tuple[MemoryRecord, ...]]:
    records_by_source: dict[str, list[MemoryRecord]] = {}
    seen_by_source: dict[str, set[str]] = {}
    for record in memory_records:
        memory_id = record.memory_id or id(record)
        for source_id in record.source_ids:
            seen = seen_by_source.setdefault(source_id, set())
            memory_key = str(memory_id)
            if memory_key in seen:
                continue
            seen.add(memory_key)
            records_by_source.setdefault(source_id, []).append(record)
    return {source_id: tuple(records) for source_id, records in records_by_source.items()}


def _source_memory_candidate_bonus(
    *,
    question_terms: frozenset[str],
    memory_records: tuple[MemoryRecord, ...],
    route: RouteResult,
) -> float:
    best_overlap = 0
    type_bonus = 0.0
    for record in memory_records:
        record_terms = _content_terms(_memory_record_hint_basis(record))
        best_overlap = max(best_overlap, len(question_terms.intersection(record_terms)))
        if _memory_type_matches_route(record.memory_type, route):
            type_bonus = max(type_bonus, 0.4)
    return min(2.5, best_overlap * 0.8) + type_bonus


def _memory_type_matches_route(memory_type: str, route: RouteResult) -> bool:
    normalized = memory_type.lower()
    if route.information_need == "profile_preference":
        return normalized in {"preference", "profile", "state"}
    if route.information_need == "current_state":
        return normalized in {"state", "profile", "preference", "relationship"}
    if route.information_need == "temporal_lookup":
        return normalized in {"event", "plan", "fact", "state"}
    if route.information_need == "list_count":
        return normalized in {"event", "fact", "relationship", "plan", "state"}
    if route.information_need == "fact_lookup":
        return normalized in {"fact", "event", "relationship", "state", "profile"}
    return False


def _candidate_memory_hint_text(
    memory_records: tuple[MemoryRecord, ...],
    *,
    max_hints: int,
    max_chars: int,
) -> str:
    if not memory_records or max_hints <= 0:
        return ""
    hints = [
        _compact_memory_hint(record, max_chars=max_chars)
        for record in memory_records[:max_hints]
    ]
    return "; ".join(hint for hint in hints if hint)


def _compact_memory_hint(record: MemoryRecord, *, max_chars: int) -> str:
    fields = [record.memory_type or "memory"]
    if record.status and record.status != "active":
        fields.append(f"status={record.status}")
    time_value = (
        record.event_time
        or record.valid_from
        or record.mention_time
        or record.timestamp
    )
    if time_value:
        fields.append(f"time={_single_line(time_value)}")
    basis = _memory_record_hint_basis(record)
    if basis:
        fields.append(_truncate_text(_single_line(basis), max_chars))
    return ": ".join(fields[:1]) + (" | " + " | ".join(fields[1:]) if len(fields) > 1 else "")


def _memory_record_hint_basis(record: MemoryRecord) -> str:
    return " ".join(
        part
        for part in (
            record.subject,
            record.predicate,
            record.value,
            record.text,
        )
        if part
    )


def _external_update_conflict_guide_lines(
    *,
    question: str,
    route: RouteResult,
    rows: tuple[EvidenceRow, ...],
    max_rows: int,
    snippet_chars: int,
) -> list[str]:
    selected = _update_conflict_guide_rows(
        question=question,
        route=route,
        rows=rows,
        max_rows=max_rows,
    )
    if not selected:
        return []

    lines = [
        "Use this compact chain to compare directly relevant raw rows that may describe an older state, newer state, correction, or scoped historical value; verify final facts in Memory Context.",
    ]
    if _is_aggregation_question(question):
        lines.append(
            "- For total, sum, difference, cost, or combined-value questions, collect each requested operand from matching rows; an older operand is still valid unless a newer row explicitly replaces the same operand."
        )
    else:
        lines.append(
            "- Match the question scope first: current/latest/now should use the newest direct update, while previous/original/first/before/in-period questions should use the matching historical scope."
        )
    lines.extend(
        [
            "- Explicit corrections, updates, added items, changed values, or approximate current values can override retrieval rank when the Memory Context supports them.",
            "- Preserve unit and answer-slot wording attached to a selected value, such as dollars, stars, followers, minutes, years, level, or count.",
            "- rows:",
        ]
    )
    for candidate in selected:
        row = candidate["row"]
        snippet = _single_line(
            _query_snippet(row.text, question, snippet_chars)  # type: ignore[union-attr]
        )
        signals = ", ".join(candidate["signals"]) or "none"
        values = "; ".join(candidate["values"])
        lines.append(
            f"  - Memory {candidate['memory_index']}: date={row.timestamp or 'unknown'} "
            f"role={row.role} signals={signals} values={values} | text=\"{snippet}\""
        )
    return lines


def _update_conflict_guide_rows(
    *,
    question: str,
    route: RouteResult,
    rows: tuple[EvidenceRow, ...],
    max_rows: int,
) -> tuple[dict[str, Any], ...]:
    if len(rows) < 2:
        return ()
    if _asks_advice_or_recommendation(question):
        return ()
    if not _asks_update_conflict_value_slot(question):
        return ()

    question_terms = _update_conflict_question_terms(question)
    question_scope = _has_update_conflict_question_scope(question)
    include_domain_units = not _asks_event_order_or_sequence(question)
    candidates: list[dict[str, Any]] = []
    distinct_values: set[str] = set()
    value_rows = 0
    signaled_rows = 0

    for memory_index, row in enumerate(rows, start=1):
        if row.role.lower() != "user":
            continue
        values = _update_conflict_values(
            row.text,
            include_domain_units=include_domain_units,
        )
        if not values:
            continue
        overlap = len(question_terms.intersection(_content_terms(row.text)))
        signals = _update_conflict_signals(row.text)
        if overlap < 1:
            continue
        if overlap == 1 and not (
            route.information_need == "current_state"
            and (signals or question_scope)
        ):
            continue
        normalized_values = tuple(_normalize_update_value(value) for value in values)
        distinct_values.update(normalized_values)
        value_rows += 1
        if signals:
            signaled_rows += 1
        score = (
            overlap * 2.0
            + len(values) * 0.25
            + (2.0 if signals else 0.0)
            + (1.0 if row.role.lower() == "user" else 0.0)
        )
        candidates.append(
            {
                "memory_index": memory_index,
                "row": row,
                "values": values,
                "signals": signals,
                "score": score,
            }
        )

    if value_rows < 2 or len(distinct_values) < 2:
        return ()
    if not (
        question_scope
        or signaled_rows > 0
        or route.information_need == "current_state"
    ):
        return ()

    best = sorted(
        candidates,
        key=lambda item: (
            -float(item["score"]),
            str(item["row"].timestamp or ""),
            int(item["memory_index"]),
        ),
    )[:max_rows]
    return tuple(
        sorted(
            best,
            key=lambda item: (
                str(item["row"].timestamp or ""),
                int(item["memory_index"]),
            ),
        )
    )


def _has_update_conflict_question_scope(question: str) -> bool:
    lowered = question.lower()
    return bool(
        re.search(
            r"\b(current|currently|latest|recent|recently|now|still|today|"
            r"previous|previously|before|initial|initially|original|originally|"
            r"first|last|new|added|updated|changed|total|in the past|so far)\b",
            lowered,
        )
    )


def _asks_advice_or_recommendation(question: str) -> bool:
    return bool(
        re.search(
            r"\b(any tips|suggest|suggestions|recommend|recommendations|"
            r"what do you think|ideas on|helpful tips|what should i|should i)\b",
            question.lower(),
        )
    )


def _asks_update_conflict_value_slot(question: str) -> bool:
    lowered = question.lower()
    if _asks_event_order_or_sequence(question):
        return bool(re.search(r"\b(days?|weeks?|months?|years?)\b", lowered))
    scalar_intent = bool(
        re.search(
            r"\b(how many|how much|how long|how often|total|sum|combined|"
            r"difference|cost|price|amount|number|count|percentage|discount|"
            r"duration|spent|spend|save|saved|raise|raised)\b",
            lowered,
        )
    )
    if scalar_intent:
        return True
    return bool(
        re.search(
            r"\b(followers?|views?|comments?|stars?|level|score|goal|time|"
            r"distance|pre-approved)\b",
            lowered,
        )
    )


def _asks_event_order_or_sequence(question: str) -> bool:
    lowered = question.lower()
    if not re.search(
        r"\b(order|sequence|chronological|earliest|latest|timeline|from earliest to latest|from oldest to newest|from first to last)\b",
        lowered,
    ):
        return False
    return bool(
        re.search(
            r"\b(trips?|travels?|visits?|vacations?|events?|activities?|"
            r"meetings?|appointments?|places?|restaurants?|concerts?|"
            r"movies?|books?|projects?|tasks?)\b",
            lowered,
        )
    )


def _update_conflict_question_terms(question: str) -> frozenset[str]:
    weak_scope_terms = {
        "after",
        "before",
        "current",
        "currently",
        "daily",
        "day",
        "days",
        "first",
        "last",
        "latest",
        "long",
        "many",
        "month",
        "months",
        "much",
        "new",
        "now",
        "past",
        "previous",
        "recent",
        "recently",
        "still",
        "time",
        "times",
        "today",
        "total",
        "week",
        "weeks",
        "work",
        "year",
        "years",
    }
    strong_terms = _content_terms(question).difference(weak_scope_terms)
    return strong_terms or _content_terms(question)


def _update_conflict_signals(text: str) -> tuple[str, ...]:
    lowered = text.lower()
    signal_patterns = (
        ("correction", r"\b(actually|correction|corrected|instead)\b"),
        ("current", r"\b(now|currently|current|still|as of|these days)\b"),
        ("change", r"\b(changed|updated|switched|moved|became|no longer|used to)\b"),
        ("addition", r"\b(added|another|bringing my|bringing the|total to)\b"),
        ("reached", r"\b(reached|close to|nearing)\b"),
        ("history", r"\b(previously|before|originally|initially|first)\b"),
        ("memory", r"\b(remember when|last time)\b"),
        ("personal_best", r"\b(personal best|beat my|beat the)\b"),
    )
    signals = [
        label for label, pattern in signal_patterns if re.search(pattern, lowered)
    ]
    return tuple(dict.fromkeys(signals))


def _update_conflict_values(
    text: str,
    *,
    include_domain_units: bool = True,
) -> tuple[str, ...]:
    values: list[str] = []
    spans: list[tuple[int, int]] = []
    patterns = (
        UPDATE_CONFLICT_VALUE_PATTERNS + (UPDATE_CONFLICT_GENERIC_VALUE_PATTERN,)
        if include_domain_units
        else UPDATE_CONFLICT_SCALAR_VALUE_PATTERNS
    )
    for pattern in patterns:
        for match in re.finditer(pattern, text, flags=re.IGNORECASE):
            if any(match.start() < end and match.end() > start for start, end in spans):
                continue
            value = _clean_update_conflict_value_candidate(match.group(0))
            if not value:
                continue
            if _looks_like_standalone_year(value):
                continue
            spans.append((match.start(), match.end()))
            values.append(value)
            if len(values) >= 6:
                return tuple(dict.fromkeys(values))
    return tuple(dict.fromkeys(values))


def _clean_update_conflict_value_candidate(value: str) -> str:
    compact = _single_line(value).strip(" ,.;:!?")
    if not compact:
        return ""
    if re.fullmatch(
        r"(?:[$€£]\s*)?\d+(?:,\d{3})*(?:\.\d+)?\s*(?:k|%)?",
        compact,
        flags=re.IGNORECASE,
    ):
        return compact

    parts = compact.split()
    if len(parts) <= 1:
        return compact

    kept = [parts[0]]
    for token in parts[1:]:
        normalized = re.sub(r"^[^\w%]+|[^\w%/-]+$", "", token).lower()
        if not normalized:
            break
        if normalized in UPDATE_CONFLICT_VALUE_UNIT_STOPWORDS:
            break
        if re.fullmatch(r"\d{1,4}", normalized):
            break
        kept.append(token.strip(" ,.;:!?"))
        if len(kept) >= 3:
            break
    return " ".join(part for part in kept if part)


def _looks_like_standalone_year(value: str) -> bool:
    normalized = value.strip().replace(",", "")
    if not normalized.isdigit():
        return False
    year = int(normalized)
    return 1900 <= year <= 2099


def _normalize_update_value(value: str) -> str:
    return re.sub(r"\s+", " ", value.lower().replace(",", "")).strip()


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


def _should_apply_operation_workpad(
    question: str,
    route: RouteResult,
    *,
    question_gate: bool,
) -> bool:
    if not question_gate:
        return True
    if route.information_need in {"list_count", "temporal_lookup"}:
        return True
    return _asks_collection_operation(question) or _asks_temporal_calculation(question)


def _is_personalized_advice_question(question: str) -> bool:
    text = question.strip().lower()
    if not text:
        return False
    return bool(PERSONALIZED_ADVICE_PATTERN.search(text)) and not bool(
        ASSISTANT_RECALL_PATTERN.search(text)
    )


def _personalized_advice_lines() -> list[str]:
    return [
        "- Treat remembered preferences, dislikes, goals, constraints, owned resources, and prior successes as usable personalization evidence.",
        "- If the context gives personalization anchors but no exact named option, answer with suitable option types, criteria, or next-step choices instead of refusing.",
        "- Do not introduce a specific named place, product, show, person, brand, or event unless that name appears in Memory Context.",
        "- Include one or two brief personalization anchors from Memory Context; if no anchor exists, say the information is not enough.",
    ]


def _is_grounded_inference_question(question: str, *, gate: str = "broad") -> bool:
    text = question.strip().lower()
    if not text:
        return False
    if ASSISTANT_RECALL_PATTERN.search(text):
        return False
    if gate == "modal_only":
        return bool(MODAL_GROUNDED_INFERENCE_PATTERN.search(text))
    if gate == "broad":
        return bool(GROUNDED_INFERENCE_PATTERN.search(text))
    raise ValueError(f"Unsupported grounded_inference_gate: {gate}")


def _grounded_inference_lines() -> list[str]:
    return [
        "- For questions asking would, might, likely, probably, or considered, the user is asking for a memory-grounded inference, not necessarily a verbatim quote.",
        "- Use directly relevant anchors from Memory Context such as stated preferences, actions, constraints, experiences, self-descriptions, outcomes, and repeated behavior.",
        "- If the anchors point clearly one way, answer with a calibrated conclusion such as yes, no, likely, unlikely, or somewhat; do not refuse only because the exact final wording is absent.",
        "- Do not infer sensitive identity, religion, health, finances, or other personal status from stereotypes or demographics; use only explicit self-statements, concrete behavior, and conversation context.",
        "- If there are no relevant anchors or the anchors conflict without a clear direction, say the provided information is not enough.",
        "- Keep the final answer concise and include the key uncertainty qualifier when the evidence is indirect.",
    ]


def _single_line(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _external_event_timeline_lines(
    *,
    question: str,
    rows: tuple[EvidenceRow, ...],
    max_rows: int,
    snippet_chars: int,
) -> list[str]:
    candidates = _event_timeline_candidate_rows(
        question=question,
        rows=rows,
        snippet_chars=snippet_chars,
    )
    if len(candidates) < 2:
        return []

    selected = sorted(
        candidates,
        key=lambda item: (-int(item["score"]), int(item["memory_index"])),
    )[: max(2, max_rows)]
    timeline = sorted(selected, key=_event_timeline_sort_key)

    lines = [
        "Use this as a compact index into Memory Context rows for order/timeline questions; verify final facts in the cited rows.",
        "- time_kind exact_today/explicit_date is stronger than vague_relative_recent. A vague 'recently' near a row date is not a strict before/after fact for another same-date event unless the row text says so.",
        "- mention_time_only means the row date is only when the memory was written; do not treat it as the event time without row-text support.",
        "- timeline_candidates:",
    ]
    for item in timeline:
        matched = ", ".join(item["matched_terms"]) or "none"
        markers = "; ".join(item["markers"]) or "none"
        lines.append(
            f"  - Memory {item['memory_index']}: mention_time={item['mention_time']} "
            f"time_kind={item['time_kind']} event_time={item['event_time']} "
            f"matched_terms={matched} markers={markers} text={item['snippet']}"
        )
    order = " -> ".join(
        f"Memory {item['memory_index']}({item['event_time']}, {item['time_kind']})"
        for item in timeline
    )
    lines.append(f"- tentative_order_by_best_available_event_time: {order}")
    return lines


def _external_event_time_candidate_map_lines(
    *,
    question: str,
    rows: tuple[EvidenceRow, ...],
    max_groups: int,
    snippet_chars: int,
    min_terms: int,
    min_coverage: float,
    allowed_time_kinds: tuple[str, ...],
    strip_context_wrappers: bool,
    segment_local_context: bool,
    rank_by_coverage: bool,
    normalize_terms: bool,
    exact_today_min_coverage: float | None,
    require_role_match: bool,
    temporal_ambiguity_contract: bool,
    include_mention_time: bool,
    mention_time_fallback: bool,
    mention_time_fallback_min_coverage: float,
    mention_time_fallback_trigger_max_coverage: float,
    enable_weekend_relative_time: bool,
) -> list[str]:
    target_terms = _event_time_candidate_map_target_terms(
        question,
        normalize_terms=normalize_terms,
    )
    if not target_terms:
        return []

    candidates = _event_timeline_candidate_rows(
        question=question,
        rows=rows,
        snippet_chars=snippet_chars,
        strip_context_wrappers=strip_context_wrappers,
        segment_local_context=segment_local_context,
        normalize_slot_terms=normalize_terms,
        enable_weekend_relative_time=enable_weekend_relative_time,
    )
    if len(candidates) < 1:
        return []

    if rank_by_coverage:
        selected = sorted(
            candidates,
            key=lambda item: _event_time_candidate_map_pool_sort_key(
                item,
                target_terms,
            ),
        )[: max(2, max_groups * 16)]
    else:
        selected = sorted(
            candidates,
            key=lambda item: (-int(item["score"]), int(item["memory_index"])),
        )[: max(2, max_groups * 8)]
    conflict_groups = _event_time_candidate_conflict_groups(selected)
    groups = _event_time_candidate_groups(
        selected,
        conflict_groups=conflict_groups,
        max_groups=max(1, max_groups * 8),
    )

    high_confidence_resolutions = {
        "high_confidence_single",
        "high_confidence_duplicate_same_time",
    }
    allowed_time_kind_set = {str(kind) for kind in allowed_time_kinds}
    item_by_source_id = {str(item["source_id"]): item for item in selected}
    target_role_terms = (
        _event_time_candidate_map_target_role_terms(selected, target_terms)
        if require_role_match
        else frozenset()
    )
    candidates_for_prompt: list[dict[str, object]] = []
    mention_time_fallbacks: list[dict[str, object]] = []
    for group in groups:
        if group.get("conflict_type"):
            continue
        dedup_key = str(group.get("dedup_key") or "")
        if not dedup_key.startswith("q:"):
            continue
        key_terms = frozenset(dedup_key[2:].split("|")).difference(
            _EVENT_SLOT_WEAK_TERMS
        )
        matched_terms = tuple(sorted(key_terms.intersection(target_terms)))
        if len(matched_terms) < min_terms:
            continue
        coverage = len(matched_terms) / max(1, len(target_terms))
        if coverage < min_coverage:
            continue
        if (
            str(group.get("best_time_kind")) == "exact_today"
            and exact_today_min_coverage is not None
            and coverage < exact_today_min_coverage
        ):
            continue
        best = item_by_source_id.get(str(group.get("best_source_id") or ""))
        if best is None:
            continue
        if target_role_terms and not _event_time_candidate_role_matches(
            str(best.get("role") or ""),
            target_role_terms,
        ):
            continue
        if (
            mention_time_fallback
            and str(group.get("best_time_kind")) == "mention_time_only"
            and str(group.get("resolution")) == "low_precision_single"
            and coverage >= mention_time_fallback_min_coverage
        ):
            mention_time_fallbacks.append(
                {
                    "coverage": coverage,
                    "matched_terms": matched_terms,
                    "group": group,
                    "item": best,
                }
            )
            continue
        if str(group.get("resolution")) not in high_confidence_resolutions:
            continue
        if (
            allowed_time_kind_set
            and str(group.get("best_time_kind")) not in allowed_time_kind_set
        ):
            continue
        candidates_for_prompt.append(
            {
                "coverage": coverage,
                "matched_terms": matched_terms,
                "group": group,
                "item": best,
            }
        )

    if not candidates_for_prompt:
        return []

    candidates_for_prompt.sort(
        key=lambda item: (
            -float(item["coverage"]),
            -len(item["matched_terms"]),
            int(item["item"]["memory_index"]),
        )
    )
    best_coverage = float(candidates_for_prompt[0]["coverage"])
    top = [
        item
        for item in candidates_for_prompt
        if abs(float(item["coverage"]) - best_coverage) < 1e-9
    ]
    top_times = {str(item["group"]["best_event_time"]) for item in top}
    if len(top_times) > 1:
        return []
    selected_for_prompt = top[:max_groups]
    fallback_for_prompt: dict[str, object] | None = None
    if mention_time_fallback and selected_for_prompt:
        primary = selected_for_prompt[0]
        primary_group = primary["group"]
        if (
            str(primary_group.get("best_time_kind")) == "exact_today"
            and float(primary["coverage"])
            < mention_time_fallback_trigger_max_coverage
        ):
            stronger_fallbacks = [
                item
                for item in mention_time_fallbacks
                if float(item["coverage"]) > float(primary["coverage"])
            ]
            if stronger_fallbacks:
                fallback_for_prompt = sorted(
                    stronger_fallbacks,
                    key=lambda item: (
                        -float(item["coverage"]),
                        -len(item["matched_terms"]),
                        int(item["item"]["memory_index"]),
                    ),
                )[0]

    lines = [
        "Use this narrow map only to locate the likely target event-time row; verify the final answer in Memory Context.",
        "- Only high-confidence q-slot groups with no event-time conflict and strong question-term coverage are shown.",
        "- Omitted rows may be low precision, conflicted, or less specific to the question.",
    ]
    if fallback_for_prompt is not None:
        lines.append(
            "- mention_time_fallback rows appear only when a row strongly matches the target but has no explicit event date; use the row Date only if the question asks when it was stated/planned or no stronger event-time row applies."
        )
    if temporal_ambiguity_contract:
        lines.extend(
            [
                "- For planned, intended, scheduled, or future relative phrases, keep mention_time and event_time separate; do not collapse one into the other.",
                "- If the question could be asking when the plan or statement was made rather than only when the future event was scheduled, include both mention_time and planned event_time in the final answer.",
            ]
        )
    lines.append("- target_event_time_candidates:")
    for entry in [
        *selected_for_prompt,
        *([fallback_for_prompt] if fallback_for_prompt is not None else []),
    ]:
        item = entry["item"]
        group = entry["group"]
        matched = ", ".join(entry["matched_terms"]) or "none"
        source_labels = []
        for source_id in group.get("high_confidence_source_ids") or ():
            source_item = item_by_source_id.get(str(source_id))
            if source_item is None:
                continue
            source_labels.append(f"Memory {source_item['memory_index']}")
        source_text = ", ".join(dict.fromkeys(source_labels)) or (
            f"Memory {item['memory_index']}"
        )
        markers = "; ".join(str(marker) for marker in item.get("markers") or ())
        time_kind = str(group["best_time_kind"])
        if entry is fallback_for_prompt:
            markers = markers or "mention_time_only"
            time_kind = "mention_time_fallback"
        time_prefix = (
            f"mention_time={item['mention_time']} "
            if include_mention_time
            else ""
        )
        lines.append(
            f"  - {source_text}: {time_prefix}"
            f"event_time={group['best_event_time']} time_kind={time_kind} "
            f"matched_terms={matched} "
            f"coverage={float(entry['coverage']):.3f} markers={markers or 'none'} "
            f"text=\"{item['snippet']}\""
        )
    return lines


def _event_time_candidate_map_audit(
    *,
    question: str,
    route: RouteResult,
    rows: tuple[EvidenceRow, ...],
    max_groups: int,
    snippet_chars: int,
    min_terms: int,
    min_coverage: float,
    allowed_time_kinds: tuple[str, ...],
    strip_context_wrappers: bool,
    segment_local_context: bool,
    rank_by_coverage: bool,
    normalize_terms: bool,
    exact_today_min_coverage: float | None,
    require_role_match: bool,
    allow_time_of_day_questions: bool,
    enable_weekend_relative_time: bool,
) -> dict[str, object]:
    """Trace-only mirror of prompt-side event-time map gating."""

    base: dict[str, object] = {
        "enabled": True,
        "trace_only": True,
        "applied": False,
        "information_need": route.information_need,
        "prompt_eligible_count": 0,
        "prompt_candidates": [],
        "rejected_groups": [],
        "risk_flags": [],
        "clean_note": (
            "Trace-only audit of Event-Time Candidate Map gating. It is not "
            "included in the answer prompt, retrieval, repair, finalizer, or cache key."
        ),
    }
    if not _asks_event_time_candidate_map(
        question,
        route,
        allow_time_of_day_questions=allow_time_of_day_questions,
    ):
        return {**base, "reason": "question_gate_not_matched"}

    target_terms = _event_time_candidate_map_target_terms(
        question,
        normalize_terms=normalize_terms,
    )
    if not target_terms:
        return {**base, "reason": "no_target_terms"}

    candidates = _event_timeline_candidate_rows(
        question=question,
        rows=rows,
        snippet_chars=snippet_chars,
        strip_context_wrappers=strip_context_wrappers,
        segment_local_context=segment_local_context,
        normalize_slot_terms=normalize_terms,
        enable_weekend_relative_time=enable_weekend_relative_time,
    )
    if not candidates:
        return {**base, "reason": "no_source_backed_time_candidates"}

    if rank_by_coverage:
        selected = sorted(
            candidates,
            key=lambda item: _event_time_candidate_map_pool_sort_key(
                item,
                target_terms,
            ),
        )[: max(2, max_groups * 16)]
    else:
        selected = sorted(
            candidates,
            key=lambda item: (-int(item["score"]), int(item["memory_index"])),
        )[: max(2, max_groups * 8)]
    conflict_groups = _event_time_candidate_conflict_groups(selected)
    groups = _event_time_candidate_groups(
        selected,
        conflict_groups=conflict_groups,
        max_groups=max(1, max_groups * 8),
    )

    high_confidence_resolutions = {
        "high_confidence_single",
        "high_confidence_duplicate_same_time",
    }
    allowed_time_kind_set = {str(kind) for kind in allowed_time_kinds}
    item_by_source_id = {str(item["source_id"]): item for item in selected}
    target_role_terms = (
        _event_time_candidate_map_target_role_terms(selected, target_terms)
        if require_role_match
        else frozenset()
    )
    prompt_candidates: list[dict[str, object]] = []
    rejected_groups: list[dict[str, object]] = []

    for group in groups:
        dedup_key = str(group.get("dedup_key") or "")
        key_terms = frozenset(dedup_key[2:].split("|")).difference(
            _EVENT_SLOT_WEAK_TERMS
        )
        matched_terms = tuple(sorted(key_terms.intersection(target_terms)))
        coverage = len(matched_terms) / max(1, len(target_terms))
        best = item_by_source_id.get(str(group.get("best_source_id") or ""))
        rejected_reason = ""
        if group.get("conflict_type"):
            rejected_reason = str(group.get("conflict_type"))
        elif str(group.get("resolution")) not in high_confidence_resolutions:
            rejected_reason = str(group.get("resolution") or "low_confidence")
        elif (
            allowed_time_kind_set
            and str(group.get("best_time_kind")) not in allowed_time_kind_set
        ):
            rejected_reason = "time_kind_not_allowed"
        elif not dedup_key.startswith("q:"):
            rejected_reason = "non_question_slot"
        elif len(matched_terms) < min_terms:
            rejected_reason = "too_few_question_terms"
        elif coverage < min_coverage:
            rejected_reason = "low_question_coverage"
        elif (
            str(group.get("best_time_kind")) == "exact_today"
            and exact_today_min_coverage is not None
            and coverage < exact_today_min_coverage
        ):
            rejected_reason = "exact_today_low_question_coverage"
        elif best is None:
            rejected_reason = "missing_best_source"
        elif target_role_terms and not _event_time_candidate_role_matches(
            str(best.get("role") or ""),
            target_role_terms,
        ):
            rejected_reason = "role_mismatch"

        if rejected_reason:
            if len(rejected_groups) < max(4, max_groups * 2):
                rejected_groups.append(
                    {
                        "dedup_key": dedup_key,
                        "reason": rejected_reason,
                        "best_time_kind": str(group.get("best_time_kind") or ""),
                        "best_event_time": str(group.get("best_event_time") or ""),
                        "coverage": round(coverage, 3),
                        "matched_terms": matched_terms,
                        "source_ids": tuple(
                            str(source_id)
                            for source_id in group.get("source_ids") or ()
                        ),
                    }
                )
            continue

        assert best is not None
        flags = _event_time_candidate_map_audit_flags(
            group=group,
            item=best,
            coverage=coverage,
            exact_today_min_coverage=exact_today_min_coverage,
        )
        prompt_candidates.append(
            {
                "source_id": str(best.get("source_id") or ""),
                "memory_index": int(best.get("memory_index") or 0),
                "dedup_key": dedup_key,
                "mention_time": str(best.get("mention_time") or ""),
                "event_time": str(group.get("best_event_time") or ""),
                "time_kind": str(group.get("best_time_kind") or ""),
                "matched_terms": matched_terms,
                "coverage": round(coverage, 3),
                "markers": tuple(str(marker) for marker in best.get("markers") or ()),
                "risk_flags": flags,
                "snippet": str(best.get("snippet") or ""),
            }
        )

    top_flags = sorted(
        {
            flag
            for candidate in prompt_candidates
            for flag in tuple(candidate.get("risk_flags") or ())
        }
    )
    return {
        **base,
        "applied": True,
        "reason": "event_time_candidate_map_gate_audited",
        "n_candidates": len(candidates),
        "n_selected": len(selected),
        "target_terms": tuple(sorted(target_terms)),
        "prompt_eligible_count": len(prompt_candidates),
        "prompt_candidates": prompt_candidates[:max_groups],
        "rejected_groups": rejected_groups,
        "risk_flags": tuple(top_flags),
        "conflict_groups": conflict_groups,
    }


def _event_time_candidate_map_audit_flags(
    *,
    group: dict[str, object],
    item: dict[str, object],
    coverage: float,
    exact_today_min_coverage: float | None,
) -> tuple[str, ...]:
    flags: list[str] = []
    time_kind = str(group.get("best_time_kind") or "")
    if time_kind == "exact_today":
        flags.append("exact_today_prompt_candidate")
        threshold = 0.8 if exact_today_min_coverage is None else exact_today_min_coverage
        if coverage < threshold:
            flags.append("exact_today_low_question_coverage")
    if time_kind == "relative_phrase":
        flags.append("relative_phrase_prompt_candidate")
    if str(item.get("mention_time") or "") == str(group.get("best_event_time") or ""):
        flags.append("event_time_equals_mention_time")
    markers = tuple(str(marker) for marker in item.get("markers") or ())
    if not markers:
        flags.append("mention_time_only_candidate")
    return tuple(flags)


def _asks_event_time_candidate_map(
    question: str,
    route: RouteResult,
    *,
    allow_time_of_day_questions: bool,
) -> bool:
    if route.information_need != "temporal_lookup":
        return False
    lowered = question.lower()
    if re.search(
        r"\b(how\s+long|duration|order|ordered|sequence|first|last|"
        r"earliest|latest|before|after|since|until)\b",
        lowered,
    ):
        return False
    english_gate = r"\b(when|what\s+date|which\s+date|which\s+day|what\s+day"
    chinese_gate = r"(什么时候|哪天|日期"
    if allow_time_of_day_questions:
        english_gate += r"|what\s+time"
        chinese_gate += r"|几点|什么时间"
    english_gate += r")\b"
    chinese_gate += r")"
    return bool(
        re.search(english_gate, lowered)
        or re.search(chinese_gate, question)
    )


def _event_time_candidate_map_pool_sort_key(
    item: dict[str, object],
    target_terms: frozenset[str],
) -> tuple[float, int, int, int, int]:
    key_terms = _event_time_candidate_map_key_terms(str(item.get("slot_key") or ""))
    matched_terms = key_terms.intersection(target_terms)
    coverage = len(matched_terms) / max(1, len(target_terms))
    return (
        -coverage,
        -len(matched_terms),
        int(item.get("precision_rank") or 99),
        -int(item.get("score") or 0),
        int(item["memory_index"]),
    )


def _event_time_candidate_map_key_terms(slot_key: str) -> frozenset[str]:
    if slot_key.startswith("q:"):
        return frozenset(slot_key[2:].split("|")).difference(_EVENT_SLOT_WEAK_TERMS)
    return frozenset()


def _event_time_candidate_map_target_role_terms(
    items: list[dict[str, object]],
    target_terms: frozenset[str],
) -> frozenset[str]:
    candidate_role_terms: set[str] = set()
    for item in items:
        candidate_role_terms.update(
            _event_time_candidate_role_terms(str(item.get("role") or ""))
        )
    return frozenset(candidate_role_terms).intersection(target_terms)


def _event_time_candidate_role_matches(
    role: str,
    target_role_terms: frozenset[str],
) -> bool:
    role_terms = _event_time_candidate_role_terms(role)
    if not role_terms:
        return True
    return bool(role_terms.intersection(target_role_terms))


def _event_time_candidate_role_terms(role: str) -> frozenset[str]:
    terms = _content_terms(role).difference({"assistant", "system", "user"})
    return frozenset(term for term in terms if term not in _EVENT_SLOT_WEAK_TERMS)


def _event_time_candidate_map_target_terms(
    question: str,
    *,
    normalize_terms: bool = False,
) -> frozenset[str]:
    extra_weak_terms = {
        "date",
        "day",
        "did",
        "does",
        "event",
        "happen",
        "happened",
        "is",
        "time",
        "was",
        "were",
    }
    return frozenset(
        term
        for term in _event_candidate_content_terms(
            question,
            normalize_terms=normalize_terms,
        ).difference(_EVENT_SLOT_WEAK_TERMS)
        if term not in extra_weak_terms and len(term) > 1
    )


def _event_time_candidate_manifest(
    *,
    question: str,
    route: RouteResult,
    rows: tuple[EvidenceRow, ...],
    information_needs: tuple[str, ...],
    max_rows: int,
    snippet_chars: int,
    question_gate: bool,
    grouped_view: bool,
    max_groups: int,
    enable_weekend_relative_time: bool,
) -> dict[str, object]:
    base: dict[str, object] = {
        "enabled": True,
        "trace_only": True,
        "applied": False,
        "information_need": route.information_need,
        "question_gate": question_gate,
        "items": [],
        "candidate_groups": [],
        "grouped_view": grouped_view,
        "conflict_groups": [],
        "safe_order_available": False,
        "safe_order_source_ids": [],
        "safe_order_blocked_reason": "not_applied",
        "clean_note": (
            "Trace-only source-backed event-time candidate manifest. It is not "
            "included in the answer prompt, retrieval, repair, finalizer, or cache key."
        ),
    }
    if route.information_need not in information_needs:
        return {**base, "reason": "information_need_not_enabled"}
    if question_gate and not _asks_event_time_candidate_manifest(question, route):
        return {**base, "reason": "question_gate_not_matched"}

    candidates = _event_timeline_candidate_rows(
        question=question,
        rows=rows,
        snippet_chars=snippet_chars,
        enable_weekend_relative_time=enable_weekend_relative_time,
    )
    if len(candidates) < 2:
        return {
            **base,
            "reason": "fewer_than_two_source_backed_time_candidates",
            "n_candidates": len(candidates),
        }

    selected = sorted(
        candidates,
        key=lambda item: (-int(item["score"]), int(item["memory_index"])),
    )[: max(2, max_rows)]
    ordered = sorted(selected, key=lambda item: int(item["memory_index"]))
    conflict_groups = _event_time_candidate_conflict_groups(selected)
    safe_order = _event_time_candidate_safe_order(selected, conflict_groups)
    candidate_groups = (
        _event_time_candidate_groups(
            selected,
            conflict_groups=conflict_groups,
            max_groups=max_groups,
        )
        if grouped_view
        else []
    )

    items: list[dict[str, object]] = []
    for item in ordered:
        markers = tuple(str(marker) for marker in item.get("markers", ()))
        matched_terms = tuple(str(term) for term in item.get("matched_terms", ()))
        inclusion_reasons = []
        if markers:
            inclusion_reasons.append("event_time_marker")
        if matched_terms:
            inclusion_reasons.append("question_overlap")
        items.append(
            {
                "source_id": str(item["source_id"]),
                "memory_index": int(item["memory_index"]),
                "dedup_key": str(item["slot_key"]),
                "mention_time": str(item["mention_time"]),
                "event_time": str(item["event_time"]),
                "time_kind": str(item["time_kind"]),
                "time_precision_rank": int(item["precision_rank"]),
                "role": str(item["role"]),
                "matched_terms": matched_terms,
                "markers": markers,
                "snippet": str(item["snippet"]),
                "included": True,
                "inclusion_reason": "+".join(inclusion_reasons) or "source_row",
            }
        )

    return {
        **base,
        "applied": True,
        "reason": "source_backed_event_time_candidates",
        "n_candidates": len(candidates),
        "n_selected": len(selected),
        "dedup_key_count": len({str(item["slot_key"]) for item in selected}),
        "items": items,
        "candidate_groups": candidate_groups,
        "candidate_group_count": len(candidate_groups),
        "conflict_groups": conflict_groups,
        "safe_order_available": bool(safe_order["available"]),
        "safe_order_source_ids": safe_order["source_ids"],
        "safe_order_blocked_reason": safe_order["blocked_reason"],
    }


def _asks_event_time_candidate_manifest(question: str, route: RouteResult) -> bool:
    text = question or ""
    lowered = text.lower()
    if re.search(
        r"\b("
        r"when|date|time|timeline|chronological|chronologically|sequence|"
        r"order|first|last|earliest|latest|before|after|since|until|"
        r"current|currently|now|still|recent|recently|most\s+recent|"
        r"how\s+long|duration"
        r")\b",
        lowered,
    ):
        return True
    if route.information_need == "temporal_lookup":
        return True
    return bool(
        re.search(
            r"(什么时候|哪天|日期|顺序|先后|最早|最晚|之前|之后|最新|现在|目前)",
            text,
        )
    )


def _event_time_candidate_conflict_groups(
    items: list[dict[str, object]],
) -> list[dict[str, object]]:
    groups: dict[str, list[dict[str, object]]] = {}
    for item in items:
        groups.setdefault(str(item["slot_key"]), []).append(item)

    conflicts: list[dict[str, object]] = []
    high_confidence = {"exact_today", "explicit_date", "relative_phrase"}
    for slot_key, group in sorted(groups.items()):
        if len(group) <= 1:
            continue
        high_times = sorted(
            {
                str(item["event_time"])
                for item in group
                if str(item["time_kind"]) in high_confidence
            }
        )
        kinds = sorted({str(item["time_kind"]) for item in group})
        if len(high_times) > 1:
            conflict_type = "event_time_conflict"
        elif any(
            kind in {"vague_relative_recent", "mention_time_only"} for kind in kinds
        ):
            conflict_type = "duplicate_with_low_precision_time"
        else:
            continue
        conflicts.append(
            {
                "dedup_key": slot_key,
                "type": conflict_type,
                "source_ids": tuple(str(item["source_id"]) for item in group),
                "event_times": tuple(
                    sorted({str(item["event_time"]) for item in group})
                ),
                "time_kinds": tuple(kinds),
            }
        )
    return conflicts


def _event_time_candidate_safe_order(
    items: list[dict[str, object]],
    conflict_groups: list[dict[str, object]],
) -> dict[str, object]:
    high_confidence = {"exact_today", "explicit_date", "relative_phrase"}
    if conflict_groups:
        return {
            "available": False,
            "source_ids": [],
            "blocked_reason": "dedup_or_time_conflict",
        }
    if len(items) < 2:
        return {
            "available": False,
            "source_ids": [],
            "blocked_reason": "fewer_than_two_candidates",
        }
    if any(str(item["time_kind"]) not in high_confidence for item in items):
        return {
            "available": False,
            "source_ids": [],
            "blocked_reason": "low_precision_event_time_present",
        }
    slot_keys = [str(item["slot_key"]) for item in items]
    if len(set(slot_keys)) != len(slot_keys):
        return {
            "available": False,
            "source_ids": [],
            "blocked_reason": "duplicate_answer_slot",
        }
    ordered = sorted(items, key=_event_timeline_sort_key)
    return {
        "available": True,
        "source_ids": [str(item["source_id"]) for item in ordered],
        "blocked_reason": "",
    }


def _event_time_candidate_groups(
    items: list[dict[str, object]],
    *,
    conflict_groups: list[dict[str, object]],
    max_groups: int,
) -> list[dict[str, object]]:
    """Group event-time candidates by source-backed answer slot."""

    conflict_by_key = {
        str(group["dedup_key"]): str(group["type"]) for group in conflict_groups
    }
    grouped: dict[str, list[dict[str, object]]] = {}
    for item in items:
        grouped.setdefault(str(item["slot_key"]), []).append(item)

    high_confidence = {"exact_today", "explicit_date", "relative_phrase"}
    rows: list[dict[str, object]] = []
    for slot_key, group in grouped.items():
        ordered = sorted(group, key=lambda item: int(item["memory_index"]))
        high_items = [
            item for item in ordered if str(item["time_kind"]) in high_confidence
        ]
        best_pool = high_items or ordered
        best = sorted(
            best_pool,
            key=lambda item: (
                int(item["precision_rank"]),
                -int(item["score"]),
                int(item["memory_index"]),
            ),
        )[0]
        conflict_type = conflict_by_key.get(slot_key, "")
        if conflict_type:
            resolution = conflict_type
        elif len(ordered) == 1 and high_items:
            resolution = "high_confidence_single"
        elif len(ordered) == 1:
            resolution = "low_precision_single"
        elif len(high_items) == len(ordered):
            resolution = "high_confidence_duplicate_same_time"
        else:
            resolution = "low_precision_duplicate"

        rows.append(
            {
                "dedup_key": slot_key,
                "source_ids": tuple(str(item["source_id"]) for item in ordered),
                "high_confidence_source_ids": tuple(
                    str(item["source_id"]) for item in high_items
                ),
                "event_times": tuple(
                    dict.fromkeys(str(item["event_time"]) for item in ordered)
                ),
                "time_kinds": tuple(
                    sorted({str(item["time_kind"]) for item in ordered})
                ),
                "best_source_id": str(best["source_id"]),
                "best_event_time": str(best["event_time"]),
                "best_time_kind": str(best["time_kind"]),
                "conflict_type": conflict_type,
                "resolution": resolution,
                "candidate_count": len(ordered),
            }
        )

    rows.sort(
        key=lambda item: (
            1 if item["conflict_type"] else 0,
            -int(item["candidate_count"]),
            str(item["dedup_key"]),
        )
    )
    return rows[:max_groups]


_EVENT_SLOT_WEAK_TERMS = frozenset(
    {
        "after",
        "ago",
        "before",
        "chronological",
        "chronologically",
        "current",
        "currently",
        "date",
        "did",
        "during",
        "earlier",
        "earliest",
        "event",
        "events",
        "first",
        "happened",
        "latest",
        "last",
        "later",
        "mention",
        "month",
        "months",
        "most",
        "now",
        "order",
        "recent",
        "recently",
        "sequence",
        "since",
        "still",
        "then",
        "time",
        "timeline",
        "today",
        "visited",
        "week",
        "weeks",
        "when",
        "year",
        "years",
    }
)


def _event_candidate_slot_key(
    *,
    question_terms: frozenset[str],
    row_text: str,
    source_id: str,
    normalize_terms: bool = False,
) -> str:
    row_terms = _event_candidate_content_terms(
        row_text,
        normalize_terms=normalize_terms,
    ).difference(_EVENT_SLOT_WEAK_TERMS)
    matched_terms = tuple(
        sorted(
            question_terms.intersection(row_terms).difference(_EVENT_SLOT_WEAK_TERMS)
        )
    )[:6]
    if matched_terms:
        return "q:" + "|".join(matched_terms)

    proper_phrases = _proper_phrase_signatures(row_text)
    if proper_phrases:
        return "phrase:" + proper_phrases[0]

    fallback_terms = tuple(sorted(row_terms))[:6]
    if fallback_terms:
        return "terms:" + "|".join(fallback_terms)
    return f"source:{source_id}"


def _event_candidate_content_terms(
    text: str,
    *,
    normalize_terms: bool,
) -> frozenset[str]:
    terms = _content_terms(text)
    if not normalize_terms:
        return terms
    expanded: set[str] = set()
    for term in terms:
        expanded.update(_event_candidate_term_variants(term))
    return frozenset(expanded)


def _event_candidate_term_variants(term: str) -> tuple[str, ...]:
    variants = [term]
    if len(term) > 4 and term.endswith("ing"):
        base = term[:-3]
        if len(base) > 2 and base[-1] == base[-2]:
            base = base[:-1]
        variants.append(base)
        variants.append(base + "e")
    if len(term) > 3 and term.endswith("ed"):
        base = term[:-2]
        if len(base) > 2 and base[-1] == base[-2]:
            base = base[:-1]
        variants.append(base)
        variants.append(base + "e")
    if len(term) > 3 and term.endswith("s"):
        variants.append(term[:-1])
    return tuple(dict.fromkeys(value for value in variants if len(value) > 1))


def _proper_phrase_signatures(text: str) -> tuple[str, ...]:
    phrases: list[str] = []
    seen: set[str] = set()
    pattern = re.compile(
        r"\b[A-Z][A-Za-z0-9'&.-]+(?:\s+(?:of|the|and|for|at|in|"
        r"[A-Z][A-Za-z0-9'&.-]+)){1,6}"
    )
    for match in pattern.finditer(text):
        phrase = _normalize_version_text(match.group(0))
        if phrase in {"i remember", "i recently"}:
            continue
        if phrase and phrase not in seen:
            seen.add(phrase)
            phrases.append(phrase)
    return tuple(phrases)


def _event_timeline_candidate_rows(
    *,
    question: str,
    rows: tuple[EvidenceRow, ...],
    snippet_chars: int,
    strip_context_wrappers: bool = False,
    segment_local_context: bool = False,
    normalize_slot_terms: bool = False,
    enable_weekend_relative_time: bool = False,
) -> list[dict[str, object]]:
    question_terms = _event_candidate_content_terms(
        question,
        normalize_terms=normalize_slot_terms,
    )
    candidates: list[dict[str, object]] = []
    for index, row in enumerate(rows, start=1):
        row_date = _parse_date(row.timestamp)
        if row_date is None:
            continue
        row_candidates: list[dict[str, object]] = []
        for segment_index, (candidate_text, segment_role) in enumerate(
            _event_time_candidate_text_segments(
                row.text,
                strip_context_wrappers=strip_context_wrappers,
                segment_local_context=segment_local_context,
            )
        ):
            markers = _event_time_markers(
                candidate_text,
                row_date,
                enable_weekend=enable_weekend_relative_time,
            )
            row_terms = _event_candidate_content_terms(
                candidate_text,
                normalize_terms=normalize_slot_terms,
            )
            matched_terms = tuple(sorted(question_terms.intersection(row_terms)))[:8]
            if not markers and not matched_terms:
                continue
            primary = markers[0] if markers else _mention_time_marker(row_date)
            snippet = _single_line(candidate_text)
            if len(snippet) > snippet_chars:
                snippet = (snippet[: max(0, snippet_chars - 3)].rstrip() + "...")[
                    :snippet_chars
                ]
            marker_text = tuple(
                f'{marker["kind"]}: phrase="{marker["phrase"]}" event_time="{marker["value"]}"'
                for marker in markers
            )
            retrieval_bonus = 1 if row.retrieval_rank is not None else 0
            row_candidates.append(
                {
                    "event_sort_date": primary["sort_date"],
                    "event_time": primary["value"],
                    "index": index,
                    "markers": marker_text,
                    "matched_terms": matched_terms,
                    "memory_index": index,
                    "mention_time": row_date.isoformat(),
                    "precision_rank": primary["precision_rank"],
                    "role": segment_role or row.role,
                    "score": (
                        len(matched_terms) + retrieval_bonus + (2 * len(markers))
                    ),
                    "segment_index": segment_index,
                    "slot_key": _event_candidate_slot_key(
                        question_terms=question_terms,
                        row_text=candidate_text,
                        source_id=row.source_id,
                        normalize_terms=normalize_slot_terms,
                    ),
                    "source_id": row.source_id,
                    "snippet": snippet,
                    "time_kind": primary["kind"],
                }
            )
        if not row_candidates:
            continue
        if segment_local_context and len(row_candidates) > 1:
            row_candidates = [
                sorted(
                    row_candidates,
                    key=lambda item: _event_time_candidate_segment_sort_key(
                        item,
                        question_terms,
                    ),
                )[0]
            ]
        candidates.extend(row_candidates)
    return candidates


def _event_time_candidate_segment_sort_key(
    item: dict[str, object],
    question_terms: frozenset[str],
) -> tuple[int, int, int, int]:
    key_terms = _event_time_candidate_map_key_terms(str(item.get("slot_key") or ""))
    matched_terms = key_terms.intersection(question_terms)
    return (
        -len(matched_terms),
        -len(tuple(item.get("markers") or ())),
        -int(item.get("score") or 0),
        int(item.get("segment_index") or 0),
    )


def _event_time_candidate_text_segments(
    text: str,
    *,
    strip_context_wrappers: bool,
    segment_local_context: bool,
) -> tuple[tuple[str, str | None], ...]:
    if not segment_local_context:
        candidate_text = (
            _strip_local_context_timestamp_wrappers(text)
            if strip_context_wrappers
            else text
        )
        return ((candidate_text, None),)
    if not _has_local_context_wrapper(text):
        return ((text, None),)

    segments: list[tuple[str, str | None]] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or _is_local_context_header(line):
            continue
        match = re.match(
            r"^-\s+(?:(?:nearby|selected) turn|near|center)"
            r"(?: \([^)]+\))?\s*\|\s*(?P<body>.*)$",
            line,
        )
        body = match.group("body") if match else line
        role = None
        role_match = re.match(r"^(?P<role>[^:]{1,40}):\s*(?P<rest>.*)$", body)
        if role_match:
            role = role_match.group("role").strip()
        segments.append((body, role))
    return tuple(segments) if segments else ((text, None),)


def _strip_local_context_timestamp_wrappers(text: str) -> str:
    if not _has_local_context_wrapper(text):
        return text
    lines: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if _is_local_context_header(line):
            continue
        match = re.match(
            r"^-\s+(?:(?:nearby|selected) turn|near|center)"
            r"(?: \([^)]+\))?\s*\|\s*(?P<body>.*)$",
            line,
        )
        if match:
            lines.append(match.group("body"))
        else:
            lines.append(line)
    return "\n".join(lines) if lines else text


def _has_local_context_wrapper(text: str) -> bool:
    return (
        "Local dialogue context from the same session:" in text
        or "Same-session context:" in text
    )


def _is_local_context_header(line: str) -> bool:
    return line in {
        "Local dialogue context from the same session:",
        "Same-session context:",
    }


def _event_time_markers(
    text: str,
    row_date: date,
    *,
    enable_weekend: bool = False,
) -> tuple[dict[str, object], ...]:
    markers: list[dict[str, object]] = []
    seen: set[tuple[str, str]] = set()

    def add_marker(
        *,
        phrase: str,
        value: str,
        kind: str,
        sort_date: date | None,
        precision_rank: int,
    ) -> None:
        key = (phrase.lower(), value)
        if key in seen:
            return
        seen.add(key)
        markers.append(
            {
                "kind": kind,
                "phrase": phrase,
                "precision_rank": precision_rank,
                "sort_date": sort_date or row_date,
                "value": value,
            }
        )

    for phrase, normalized in _explicit_date_mentions(text, row_date):
        add_marker(
            phrase=phrase,
            value=normalized,
            kind="explicit_date",
            sort_date=_parse_date(normalized),
            precision_rank=0,
        )
    for phrase, normalized in _relative_time_values(
        text,
        row_date,
        enable_weekend=enable_weekend,
    ):
        kind = "exact_today" if phrase.lower() == "today" else "relative_phrase"
        add_marker(
            phrase=phrase,
            value=normalized,
            kind=kind,
            sort_date=_parse_date(normalized),
            precision_rank=0 if kind == "exact_today" else 1,
        )
    for phrase in _vague_recent_phrases(text):
        add_marker(
            phrase=phrase,
            value=f"near_or_before {row_date.isoformat()}",
            kind="vague_relative_recent",
            sort_date=row_date,
            precision_rank=2,
        )
    markers.sort(
        key=lambda marker: (
            marker["sort_date"],
            int(marker["precision_rank"]),
            str(marker["phrase"]),
        )
    )
    return tuple(markers)


def _mention_time_marker(row_date: date) -> dict[str, object]:
    return {
        "kind": "mention_time_only",
        "phrase": "row date",
        "precision_rank": 3,
        "sort_date": row_date,
        "value": row_date.isoformat(),
    }


def _event_timeline_sort_key(item: dict[str, object]) -> tuple[date, int, int]:
    sort_date = item["event_sort_date"]
    if not isinstance(sort_date, date):
        sort_date = _parse_date(str(sort_date)) or date.max
    return (
        sort_date,
        int(item["precision_rank"]),
        int(item["memory_index"]),
    )


def _explicit_date_mentions(text: str, row_date: date) -> tuple[tuple[str, str], ...]:
    mentions: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()

    def add(phrase: str, parsed: date | None) -> None:
        if parsed is None:
            return
        value = parsed.isoformat()
        key = (phrase.lower(), value)
        if key in seen:
            return
        seen.add(key)
        mentions.append((phrase, value))

    for match in re.finditer(
        r"\b(?P<year>\d{4})[-/](?P<month>\d{1,2})[-/](?P<day>\d{1,2})\b",
        text,
    ):
        add(
            match.group(0),
            _date_from_parts(
                int(match.group("year")),
                int(match.group("month")),
                int(match.group("day")),
            ),
        )
    month_names = (
        "January|February|March|April|May|June|July|August|September|"
        "October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sept|Sep|"
        "Oct|Nov|Dec"
    )
    for match in re.finditer(
        rf"\b(?P<month>{month_names})\s+"
        r"(?P<day>\d{1,2})(?:st|nd|rd|th)?(?:,\s*(?P<year>\d{4}))?\b",
        text,
        re.IGNORECASE,
    ):
        month = _month_number(match.group("month"))
        if month is None:
            continue
        year = int(match.group("year") or row_date.year)
        add(match.group(0), _date_from_parts(year, month, int(match.group("day"))))
    for match in re.finditer(
        rf"\b(?P<day>\d{{1,2}})(?:st|nd|rd|th)?\s+"
        rf"(?P<month>{month_names})(?:,\s*(?P<year>\d{{4}}))?\b",
        text,
        re.IGNORECASE,
    ):
        month = _month_number(match.group("month"))
        if month is None:
            continue
        year = int(match.group("year") or row_date.year)
        add(match.group(0), _date_from_parts(year, month, int(match.group("day"))))
    return tuple(mentions)


def _vague_recent_phrases(text: str) -> tuple[str, ...]:
    phrases: list[str] = []
    for match in re.finditer(
        r"\b(?:recently|not long ago|a while ago|the other day)\b",
        text,
        re.IGNORECASE,
    ):
        phrases.append(match.group(0))
    return tuple(phrases)


def _external_temporal_aid_lines(
    *,
    question: str,
    question_time: str | None,
    rows: tuple[EvidenceRow, ...],
    max_rows: int,
    max_pairs: int,
    include_relative_text: bool,
    event_contract: bool = False,
    enable_weekend_relative_time: bool = False,
) -> list[str]:
    candidates = _external_dated_candidate_rows(
        question,
        rows,
        include_relative_text=include_relative_text,
        enable_weekend_relative_time=enable_weekend_relative_time,
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
    enable_weekend_relative_time: bool,
) -> list[dict[str, object]]:
    question_terms = _content_terms(question)
    candidates: list[dict[str, object]] = []
    for index, row in enumerate(rows, start=1):
        row_date = _parse_date(row.timestamp)
        if row_date is None:
            continue
        matched_terms = tuple(sorted(question_terms.intersection(_content_terms(row.text))))
        relative_times = (
            tuple(
                _relative_time_values(
                    row.text,
                    row_date,
                    enable_weekend=enable_weekend_relative_time,
                )
            )
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
    tail_row_text_mode: str,
    tail_row_text_after_rank: int,
    tail_max_row_text_chars: int,
    context_layout: str = "flat",
) -> str:
    if not rows:
        return "None"
    if context_layout in {"session_thread", "chronological_session_thread"}:
        return _external_session_thread_context(
            rows,
            question=question,
            row_text_mode=row_text_mode,
            max_row_text_chars=max_row_text_chars,
            tail_row_text_mode=tail_row_text_mode,
            tail_row_text_after_rank=tail_row_text_after_rank,
            tail_max_row_text_chars=tail_max_row_text_chars,
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
        text = _row_prompt_text_for_row(
            row,
            question=question,
            row_text_mode=row_text_mode,
            max_row_text_chars=max_row_text_chars,
            tail_row_text_mode=tail_row_text_mode,
            tail_row_text_after_rank=tail_row_text_after_rank,
            tail_max_row_text_chars=tail_max_row_text_chars,
        )
        blocks.append(f"{header}\n{row.role}: {text}")
    return "\n\n".join(blocks)


def _external_session_thread_context(
    rows: tuple[EvidenceRow, ...],
    *,
    question: str,
    row_text_mode: str,
    max_row_text_chars: int,
    tail_row_text_mode: str,
    tail_row_text_after_rank: int,
    tail_max_row_text_chars: int,
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
        text = _row_prompt_text_for_row(
            row,
            question=question,
            row_text_mode=row_text_mode,
            max_row_text_chars=max_row_text_chars,
            tail_row_text_mode=tail_row_text_mode,
            tail_row_text_after_rank=tail_row_text_after_rank,
            tail_max_row_text_chars=tail_max_row_text_chars,
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
    tail_row_text_mode: str = "full",
    tail_row_text_after_rank: int = 0,
    tail_max_row_text_chars: int = 0,
    row_label: str | None = None,
) -> str:
    rank = row.retrieval_rank if row.retrieval_rank is not None else "neighbor"
    score = f"{row.retrieval_score:.4f}" if row.retrieval_score is not None else "n/a"
    timestamp = row.timestamp or "unknown_time"
    text = _row_prompt_text_for_row(
        row,
        question=question,
        row_text_mode=row_text_mode,
        max_row_text_chars=max_row_text_chars,
        tail_row_text_mode=tail_row_text_mode,
        tail_row_text_after_rank=tail_row_text_after_rank,
        tail_max_row_text_chars=tail_max_row_text_chars,
    )
    label_prefix = f"{row_label} " if row_label else ""
    return (
        f"- {label_prefix}source_id={row.source_id} session={row.session_id} "
        f"turn={row.turn_index} role={row.role} time={timestamp} "
        f"rank={rank} score={score}: {text}"
    )


def _row_prompt_text_for_row(
    row: EvidenceRow,
    *,
    question: str,
    row_text_mode: str,
    max_row_text_chars: int,
    tail_row_text_mode: str,
    tail_row_text_after_rank: int,
    tail_max_row_text_chars: int,
) -> str:
    effective_mode = row_text_mode
    effective_max_chars = max_row_text_chars
    if (
        tail_row_text_after_rank > 0
        and row.retrieval_rank is not None
        and row.retrieval_rank > tail_row_text_after_rank
    ):
        effective_mode = tail_row_text_mode
        effective_max_chars = tail_max_row_text_chars or max_row_text_chars
    return _row_prompt_text(
        row.text,
        question=question,
        role=row.role,
        row_text_mode=effective_mode,
        max_row_text_chars=effective_max_chars,
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
    enable_weekend_relative_time: bool = False,
) -> list[str]:
    dated_rows = _dated_candidate_rows(
        question,
        rows,
        include_relative_text=include_relative_text,
        enable_weekend_relative_time=enable_weekend_relative_time,
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
    enable_weekend_relative_time: bool = False,
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
            tuple(
                _relative_time_values(
                    row.text,
                    row_date,
                    enable_weekend=enable_weekend_relative_time,
                )
            )
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


def _asks_chronological_order(question: str) -> bool:
    lowered = question.lower()
    has_order_phrase = bool(
        re.search(
            r"\b(?:what(?:'s|\s+is)\s+the\s+order|in\s+what\s+order|"
            r"order\s+of|chronological(?:ly| order)?|timeline|sequence|"
            r"first\s+to\s+last|last\s+to\s+first|earliest\s+to\s+latest|"
            r"latest\s+to\s+earliest|starting\s+from\s+the\s+earliest)\b",
            lowered,
        )
    )
    has_time_direction = bool(
        re.search(
            r"\b(?:earliest|latest|oldest|newest|first|last|chronological|"
            r"before|after)\b",
            lowered,
        )
    )
    return has_order_phrase and has_time_direction


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


def _temporal_normalization_hints(
    rows: tuple[EvidenceRow, ...],
    *,
    enable_weekend_relative_time: bool = False,
) -> list[str]:
    hints: list[str] = []
    seen: set[tuple[str, str, str]] = set()
    for row in rows:
        row_date = _parse_date(row.timestamp)
        if row_date is None:
            continue
        for phrase, normalized in _relative_time_values(
            row.text,
            row_date,
            enable_weekend=enable_weekend_relative_time,
        ):
            key = (row.source_id, phrase, normalized)
            if key in seen:
                continue
            seen.add(key)
            hints.append(
                f"- source_id={row.source_id} row_time={row_date.isoformat()} "
                f'phrase="{phrase}" normalized="{normalized}"'
            )
    return hints


def _relative_time_values(
    text: str,
    row_date: date,
    *,
    enable_weekend: bool = False,
) -> list[tuple[str, str]]:
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
    )
    for phrase, normalized in fixed_phrases:
        if re.search(rf"\b{re.escape(phrase)}\b", lowered):
            append_value(phrase, normalized)
    legacy_weekend_phrases = (
        ("last weekend", _weekend_before(row_date, weekends_back=1)),
    )
    for phrase, normalized in legacy_weekend_phrases:
        if re.search(rf"\b{re.escape(phrase)}\b", lowered):
            append_value(phrase, normalized)
    if enable_weekend:
        weekend_phrases = (
            ("this weekend", _weekend_containing_or_after(row_date)),
            ("coming weekend", _weekend_containing_or_after(row_date)),
            ("upcoming weekend", _weekend_containing_or_after(row_date)),
            ("previous weekend", _weekend_before(row_date, weekends_back=1)),
            ("the weekend before", _weekend_before(row_date, weekends_back=1)),
            ("weekend before", _weekend_before(row_date, weekends_back=1)),
        )
        for phrase, normalized in weekend_phrases:
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

    weekend_count_pattern = (
        r"\b(?P<count>\d+|a|an|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s+"
        r"weekends?\s+"
        + (r"(?:ago|before)\b" if enable_weekend else r"ago\b")
    )
    for match in re.finditer(weekend_count_pattern, lowered):
        count = _parse_count(match.group("count"))
        if count is None or not _is_reasonable_relative_span(count, "week"):
            continue
        append_value(
            match.group(0),
            _weekend_before(row_date, weekends_back=count),
        )

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


def _weekend_containing_or_after(value: date) -> str:
    days_until_saturday = (5 - value.weekday()) % 7
    target_saturday = value + timedelta(days=days_until_saturday)
    target_sunday = target_saturday + timedelta(days=1)
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
