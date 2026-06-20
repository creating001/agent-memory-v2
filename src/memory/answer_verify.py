"""Trace-only answer support audit for clean memory QA."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any

from common.schemas import AnswerResult, CompiledContext
from memory.finalize import extract_json_object, raw_response_content


_MEMORY_REF_PATTERN = re.compile(r"\bMemory\s+(\d+)\b", re.IGNORECASE)
_INSUFFICIENT_PATTERNS = (
    "provided information is not enough",
    "information is not enough",
    "not enough information",
    "not enough evidence",
    "not available",
    "cannot determine",
    "can't determine",
    "do not have enough",
    "don't have enough",
    "insufficient information",
    "insufficient evidence",
)
_NUMBER_PATTERN = re.compile(
    r"(?<![A-Za-z0-9])[$]?\d[\d,]*(?:\.\d+)?%?(?![A-Za-z0-9])"
)
_YEAR_PATTERN = re.compile(r"\b(?:19|20)\d{2}\b")
_DATE_PATTERN = re.compile(r"\b\d{1,4}[-/]\d{1,2}(?:[-/]\d{1,4})?\b")
_MONTH_WORDS = frozenset(
    (
        "january",
        "february",
        "march",
        "april",
        "may",
        "june",
        "july",
        "august",
        "september",
        "october",
        "november",
        "december",
        "monday",
        "tuesday",
        "wednesday",
        "thursday",
        "friday",
        "saturday",
        "sunday",
        "today",
        "yesterday",
        "tomorrow",
        "tonight",
    )
)
_TEMPORAL_PHRASES = (
    "last week",
    "next week",
    "this week",
    "last month",
    "next month",
    "this month",
    "last year",
    "next year",
    "this year",
)
_ASSISTANT_ROLE_PATTERNS = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"\bwhat\s+did\s+you\s+(?:say|tell|mention|recommend|suggest|advise|ask|share|write|send|reply|respond)",
        r"\byou\s+(?:said|told|mentioned|recommended|suggested|advised|asked|shared|wrote|sent|replied|responded)",
        r"\byour\s+(?:recommendation|suggestion|advice|reply|response|message)\b",
    )
)
_USER_ROLE_PATTERNS = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"\bwhat\s+did\s+i\s+(?:say|tell|mention|ask|share|write|send)",
        r"\bi\s+(?:said|told|mentioned|asked|shared|wrote|sent)",
        r"\bmy\s+(?:message|question|request|answer|reply|response)\b",
    )
)
_ENTITY_TOKEN_PATTERN = re.compile(
    r"\b(?:[A-Z][A-Za-z0-9]*(?:[-'][A-Za-z0-9]+)*|[A-Z]{2,})\b"
)
_ENTITY_STOPWORDS = frozenset(
    (
        "A",
        "An",
        "And",
        "As",
        "At",
        "For",
        "From",
        "I",
        "In",
        "It",
        "Memory",
        "No",
        "Not",
        "Of",
        "On",
        "Or",
        "The",
        "There",
        "This",
        "To",
        "Yes",
    )
)
_CONSISTENCY_DIMENSIONS = (
    "numeric",
    "temporal",
    "speaker",
    "entity",
    "state_conflict",
    "unsupported",
)


@dataclass(frozen=True)
class AnswerSupportAudit:
    """Traceable result for source-grounded answer support checks."""

    enabled: bool
    mode: str
    trace_only: bool
    applied: bool
    reason: str
    structured_payload_present: bool
    sufficient: bool | None
    answer_is_insufficient: bool
    answer_empty: bool
    evidence_report_count: int
    support_item_count: int
    exclude_item_count: int
    final_evidence_row_count: int
    memory_reference_count: int
    unresolved_memory_references: tuple[str, ...]
    context_manifest_present: bool
    registry_backed_final_evidence_count: int
    registry_backed_support_reference_count: int
    registry_backed_support_references: tuple[int, ...]
    working_compiler_plan_available: bool
    working_compiler_plan_final_evidence_count: int
    working_compiler_plan_focus_counts: dict[str, int]
    working_compiler_plan_verifier_check_counts: dict[str, int]
    memory_system_state_available: bool
    memory_system_state_final_evidence_count: int
    memory_system_state_focus_counts: dict[str, int]
    memory_system_state_decision_counts: dict[str, int]
    memory_system_state_context_action_counts: dict[str, int]
    memory_system_state_verifier_check_counts: dict[str, int]
    memory_operation_journal_available: bool
    memory_operation_journal_final_evidence_count: int
    memory_operation_journal_operation_counts: dict[str, int]
    memory_operation_journal_family_counts: dict[str, int]
    consistency_audit_applied: bool
    consistency_valid_support_row_count: int
    consistency_dimension_counts: dict[str, int]
    consistency_risk_counts: dict[str, int]
    consistency_risks: tuple[str, ...]
    risks: tuple[str, ...]

    @property
    def risk_count(self) -> int:
        return len(self.risks)

    @property
    def consistency_risk_count(self) -> int:
        return len(self.consistency_risks)

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["risk_count"] = self.risk_count
        result["consistency_risk_count"] = self.consistency_risk_count
        return result


def audit_answer_support(
    *,
    compiled: CompiledContext,
    answer: AnswerResult,
    enabled: bool,
    mode: str = "source_grounded_audit",
    require_structured_payload: bool = True,
    require_evidence_report: bool = True,
    check_support_presence: bool = True,
    check_sufficiency_consistency: bool = True,
    check_memory_references: bool = True,
    context_manifest: dict[str, Any] | None = None,
) -> AnswerSupportAudit:
    """Audit whether the final answer is structurally backed by prompt evidence.

    The audit is intentionally trace-only: it reads only prediction-time prompt
    rows and answer JSON, never calls a model, never uses labels, and never
    changes the answer.
    """

    if not enabled:
        return _audit_noop(enabled=False, mode=mode, reason="disabled")
    if mode != "source_grounded_audit":
        raise ValueError(f"Unsupported answer verifier mode: {mode}")

    final_evidence_row_count = len(compiled.evidence_rows)
    content = raw_response_content(answer.raw_response)
    payload = extract_json_object(content) if content else None
    structured_payload_present = isinstance(payload, dict)
    payload_answer = _answer_text(payload) if payload else ""
    response_answer = payload_answer if payload_answer.strip() else answer.answer
    answer_empty = not response_answer.strip()
    answer_is_insufficient = _answer_is_insufficient(response_answer)
    sufficient = _payload_sufficient(payload)
    report = _evidence_report_items(payload)
    support_items = tuple(item for item in report if _item_status(item) == "support")
    exclude_items = tuple(item for item in report if _item_status(item) == "exclude")
    memory_references, unresolved = _memory_references(
        report,
        final_evidence_row_count=final_evidence_row_count,
    )
    registry_backed_final_source_ids = _registry_backed_final_source_ids(
        context_manifest
    )
    registry_backed_support_references = _registry_backed_support_refs(
        support_items,
        compiled=compiled,
        registry_backed_final_source_ids=registry_backed_final_source_ids,
    )
    working_plan = _working_compiler_plan_audit(context_manifest)
    system_state = _memory_system_state_audit(context_manifest)
    operation_journal = _memory_operation_journal_audit(context_manifest)
    consistency = _consistency_audit(
        compiled=compiled,
        response_answer=response_answer,
        answer_empty=answer_empty,
        answer_is_insufficient=answer_is_insufficient,
        support_items=support_items,
        system_state=system_state,
        operation_journal=operation_journal,
    )

    risks: list[str] = []
    if answer_empty:
        risks.append("empty_answer")
    if require_structured_payload and not structured_payload_present:
        risks.append("missing_structured_payload")
    if require_evidence_report and structured_payload_present and not report:
        risks.append("missing_evidence_report")
    if (
        check_support_presence
        and structured_payload_present
        and not answer_is_insufficient
        and not answer_empty
        and not support_items
    ):
        risks.append("answered_without_support_item")
    if check_sufficiency_consistency:
        if sufficient is False and not answer_is_insufficient and not answer_empty:
            risks.append("sufficiency_false_but_answered")
        if sufficient is True and answer_is_insufficient:
            risks.append("sufficiency_true_but_insufficient_answer")
    if check_memory_references:
        if unresolved:
            risks.append("unresolved_memory_reference")
        if support_items and any(
            not _memory_reference_numbers(item) for item in support_items
        ):
            risks.append("support_item_without_memory_reference")

    return AnswerSupportAudit(
        enabled=True,
        mode=mode,
        trace_only=True,
        applied=True,
        reason="audited",
        structured_payload_present=structured_payload_present,
        sufficient=sufficient,
        answer_is_insufficient=answer_is_insufficient,
        answer_empty=answer_empty,
        evidence_report_count=len(report),
        support_item_count=len(support_items),
        exclude_item_count=len(exclude_items),
        final_evidence_row_count=final_evidence_row_count,
        memory_reference_count=len(memory_references),
        unresolved_memory_references=unresolved,
        context_manifest_present=isinstance(context_manifest, dict),
        registry_backed_final_evidence_count=len(registry_backed_final_source_ids),
        registry_backed_support_reference_count=len(registry_backed_support_references),
        registry_backed_support_references=registry_backed_support_references,
        working_compiler_plan_available=working_plan["available"],
        working_compiler_plan_final_evidence_count=working_plan[
            "final_evidence_count"
        ],
        working_compiler_plan_focus_counts=working_plan["focus_counts"],
        working_compiler_plan_verifier_check_counts=working_plan[
            "verifier_check_counts"
        ],
        memory_system_state_available=system_state["available"],
        memory_system_state_final_evidence_count=system_state[
            "final_evidence_count"
        ],
        memory_system_state_focus_counts=system_state["focus_counts"],
        memory_system_state_decision_counts=system_state["decision_counts"],
        memory_system_state_context_action_counts=system_state[
            "context_action_counts"
        ],
        memory_system_state_verifier_check_counts=system_state[
            "verifier_check_counts"
        ],
        memory_operation_journal_available=operation_journal["available"],
        memory_operation_journal_final_evidence_count=operation_journal[
            "final_evidence_count"
        ],
        memory_operation_journal_operation_counts=operation_journal[
            "operation_counts"
        ],
        memory_operation_journal_family_counts=operation_journal["family_counts"],
        consistency_audit_applied=consistency["applied"],
        consistency_valid_support_row_count=consistency["valid_support_row_count"],
        consistency_dimension_counts=consistency["dimension_counts"],
        consistency_risk_counts=consistency["risk_counts"],
        consistency_risks=consistency["risks"],
        risks=tuple(dict.fromkeys(risks)),
    )


def _audit_noop(*, enabled: bool, mode: str, reason: str) -> AnswerSupportAudit:
    return AnswerSupportAudit(
        enabled=enabled,
        mode=mode,
        trace_only=True,
        applied=False,
        reason=reason,
        structured_payload_present=False,
        sufficient=None,
        answer_is_insufficient=False,
        answer_empty=False,
        evidence_report_count=0,
        support_item_count=0,
        exclude_item_count=0,
        final_evidence_row_count=0,
        memory_reference_count=0,
        unresolved_memory_references=(),
        context_manifest_present=False,
        registry_backed_final_evidence_count=0,
        registry_backed_support_reference_count=0,
        registry_backed_support_references=(),
        working_compiler_plan_available=False,
        working_compiler_plan_final_evidence_count=0,
        working_compiler_plan_focus_counts={},
        working_compiler_plan_verifier_check_counts={},
        memory_system_state_available=False,
        memory_system_state_final_evidence_count=0,
        memory_system_state_focus_counts={},
        memory_system_state_decision_counts={},
        memory_system_state_context_action_counts={},
        memory_system_state_verifier_check_counts={},
        memory_operation_journal_available=False,
        memory_operation_journal_final_evidence_count=0,
        memory_operation_journal_operation_counts={},
        memory_operation_journal_family_counts={},
        consistency_audit_applied=False,
        consistency_valid_support_row_count=0,
        consistency_dimension_counts={},
        consistency_risk_counts={},
        consistency_risks=(),
        risks=(),
    )


def _answer_text(payload: dict[str, Any] | None) -> str:
    if not isinstance(payload, dict):
        return ""
    answer = payload.get("answer")
    return str(answer) if answer is not None else ""


def _payload_sufficient(payload: dict[str, Any] | None) -> bool | None:
    if not isinstance(payload, dict) or "sufficient" not in payload:
        return None
    value = payload.get("sufficient")
    return value if isinstance(value, bool) else None


def _evidence_report_items(payload: dict[str, Any] | None) -> tuple[dict[str, Any], ...]:
    if not isinstance(payload, dict):
        return ()
    report = payload.get("evidence_report")
    if not isinstance(report, list):
        return ()
    return tuple(item for item in report if isinstance(item, dict))


def _item_status(item: dict[str, Any]) -> str:
    return str(item.get("status") or "").strip().lower()


def _memory_references(
    report: tuple[dict[str, Any], ...],
    *,
    final_evidence_row_count: int,
) -> tuple[tuple[int, ...], tuple[str, ...]]:
    refs: list[int] = []
    unresolved: list[str] = []
    for item in report:
        text = str(item.get("memory") or "")
        item_refs = _memory_reference_numbers(item)
        refs.extend(item_refs)
        if text and not item_refs:
            unresolved.append(text)
        for ref in item_refs:
            if ref < 1 or ref > final_evidence_row_count:
                unresolved.append(f"Memory {ref}")
    return tuple(refs), tuple(dict.fromkeys(unresolved))


def _memory_reference_numbers(item: dict[str, Any]) -> tuple[int, ...]:
    text = str(item.get("memory") or "")
    if "memory" in text.lower():
        return tuple(int(value) for value in re.findall(r"\b\d+\b", text))
    if re.fullmatch(r"\s*\d+(?:\s*,\s*\d+)*\s*", text):
        return tuple(int(value) for value in re.findall(r"\d+", text))
    return ()


def _registry_backed_final_source_ids(
    context_manifest: dict[str, Any] | None,
) -> frozenset[str]:
    if not isinstance(context_manifest, dict):
        return frozenset()
    memory_operations = context_manifest.get("memory_operations")
    if not isinstance(memory_operations, dict):
        return frozenset()
    registry_sources = {
        str(source_id)
        for source_id in (
            memory_operations.get("registry_projected_final_source_ids") or ()
        )
        if str(source_id).strip()
    }
    lifecycle_sources = {
        str(source_id)
        for source_id in (
            memory_operations.get("lifecycle_audit_final_source_ids") or ()
        )
        if str(source_id).strip()
    }
    layer_sources = {
        str(source_id)
        for source_id in (
            memory_operations.get("layer_manifest_final_source_ids") or ()
        )
        if str(source_id).strip()
    }
    return frozenset((*registry_sources, *lifecycle_sources, *layer_sources))


def _working_compiler_plan_audit(
    context_manifest: dict[str, Any] | None,
) -> dict[str, Any]:
    if not isinstance(context_manifest, dict):
        return {
            "available": False,
            "final_evidence_count": 0,
            "focus_counts": {},
            "verifier_check_counts": {},
        }
    memory_operations = context_manifest.get("memory_operations")
    if not isinstance(memory_operations, dict):
        return {
            "available": False,
            "final_evidence_count": 0,
            "focus_counts": {},
            "verifier_check_counts": {},
        }
    return {
        "available": bool(memory_operations.get("working_compiler_plan_available")),
        "final_evidence_count": len(
            memory_operations.get("working_compiler_plan_final_source_ids") or ()
        ),
        "focus_counts": _int_count_dict(
            memory_operations.get("working_compiler_plan_focus_counts")
        ),
        "verifier_check_counts": _int_count_dict(
            memory_operations.get("working_compiler_plan_verifier_check_counts")
        ),
    }


def _memory_system_state_audit(
    context_manifest: dict[str, Any] | None,
) -> dict[str, Any]:
    if not isinstance(context_manifest, dict):
        return _empty_memory_system_state_audit()
    memory_operations = context_manifest.get("memory_operations")
    if not isinstance(memory_operations, dict):
        return _empty_memory_system_state_audit()
    return {
        "available": bool(memory_operations.get("memory_system_state_available")),
        "final_evidence_count": len(
            memory_operations.get("memory_system_state_final_source_ids") or ()
        ),
        "focus_counts": _int_count_dict(
            memory_operations.get("memory_system_state_focus_counts")
        ),
        "decision_counts": _int_count_dict(
            memory_operations.get("memory_system_state_decision_counts")
        ),
        "context_action_counts": _int_count_dict(
            memory_operations.get("memory_system_state_context_action_counts")
        ),
        "verifier_check_counts": _int_count_dict(
            memory_operations.get("memory_system_state_verifier_check_counts")
        ),
    }


def _empty_memory_system_state_audit() -> dict[str, Any]:
    return {
        "available": False,
        "final_evidence_count": 0,
        "focus_counts": {},
        "decision_counts": {},
        "context_action_counts": {},
        "verifier_check_counts": {},
    }


def _memory_operation_journal_audit(
    context_manifest: dict[str, Any] | None,
) -> dict[str, Any]:
    if not isinstance(context_manifest, dict):
        return _empty_memory_operation_journal_audit()
    memory_operations = context_manifest.get("memory_operations")
    if not isinstance(memory_operations, dict):
        return _empty_memory_operation_journal_audit()
    return {
        "available": bool(
            memory_operations.get("memory_operation_journal_available")
        ),
        "final_evidence_count": len(
            memory_operations.get("memory_operation_journal_final_source_ids")
            or ()
        ),
        "operation_counts": _int_count_dict(
            memory_operations.get("memory_operation_journal_operation_counts")
        ),
        "family_counts": _int_count_dict(
            memory_operations.get("memory_operation_journal_family_counts")
        ),
    }


def _empty_memory_operation_journal_audit() -> dict[str, Any]:
    return {
        "available": False,
        "final_evidence_count": 0,
        "operation_counts": {},
        "family_counts": {},
    }


def _int_count_dict(value: Any) -> dict[str, int]:
    if not isinstance(value, dict):
        return {}
    counts: dict[str, int] = {}
    for key, raw_count in value.items():
        try:
            counts[str(key)] = int(raw_count)
        except (TypeError, ValueError):
            counts[str(key)] = 0
    return dict(sorted(counts.items()))


def _registry_backed_support_refs(
    support_items: tuple[dict[str, Any], ...],
    *,
    compiled: CompiledContext,
    registry_backed_final_source_ids: frozenset[str],
) -> tuple[int, ...]:
    if not support_items or not registry_backed_final_source_ids:
        return ()
    refs: list[int] = []
    for item in support_items:
        for ref in _memory_reference_numbers(item):
            index = ref - 1
            if index < 0 or index >= len(compiled.evidence_rows):
                continue
            source_id = str(getattr(compiled.evidence_rows[index], "source_id", "") or "")
            if source_id in registry_backed_final_source_ids:
                refs.append(ref)
    return tuple(dict.fromkeys(refs))


def _consistency_audit(
    *,
    compiled: CompiledContext,
    response_answer: str,
    answer_empty: bool,
    answer_is_insufficient: bool,
    support_items: tuple[dict[str, Any], ...],
    system_state: dict[str, Any],
    operation_journal: dict[str, Any],
) -> dict[str, Any]:
    """Run trace-only source consistency checks over generic answer dimensions."""

    dimension_counts = {dimension: 0 for dimension in _CONSISTENCY_DIMENSIONS}
    risk_counts = {dimension: 0 for dimension in _CONSISTENCY_DIMENSIONS}
    risks: list[str] = []

    def add_risk(dimension: str, reason: str) -> None:
        risk_counts[dimension] = risk_counts.get(dimension, 0) + 1
        risks.append(reason)

    support_rows = _support_evidence_rows(support_items, compiled=compiled)
    support_text = "\n".join(row.text for row in support_rows)
    support_norm = _normalize_grounding_text(support_text)
    answered = (
        bool(response_answer.strip())
        and not answer_empty
        and not answer_is_insufficient
    )

    if answered:
        dimension_counts["unsupported"] = 1
        if not support_rows:
            add_risk("unsupported", "unsupported_answer_without_valid_support_row")

    answer_numbers = _numeric_tokens(response_answer)
    dimension_counts["numeric"] = len(answer_numbers)
    if answer_numbers and support_rows:
        support_numbers = set(_numeric_tokens(support_text))
        missing_numbers = [
            number for number in answer_numbers if number not in support_numbers
        ]
        if missing_numbers:
            add_risk("numeric", "numeric_value_not_in_support")
    elif answer_numbers and answered:
        add_risk("numeric", "numeric_value_without_support")

    answer_temporal = _temporal_tokens(response_answer)
    dimension_counts["temporal"] = len(answer_temporal)
    if answer_temporal and support_rows:
        support_temporal = set(_temporal_tokens(support_text))
        missing_temporal = [
            token for token in answer_temporal if token not in support_temporal
        ]
        if missing_temporal:
            add_risk("temporal", "temporal_value_not_in_support")
    elif answer_temporal and answered:
        add_risk("temporal", "temporal_value_without_support")

    expected_role = _expected_source_role(compiled.question)
    if expected_role:
        dimension_counts["speaker"] = 1
        if support_rows and not any(row.role == expected_role for row in support_rows):
            add_risk("speaker", "speaker_role_mismatch")
        elif answered and not support_rows:
            add_risk("speaker", "speaker_role_without_support")

    answer_entities = _answer_entity_tokens(response_answer, question=compiled.question)
    dimension_counts["entity"] = len(answer_entities)
    if answer_entities and support_rows:
        missing_entities = [
            token
            for token in answer_entities
            if _normalize_grounding_text(token) not in support_norm
        ]
        if missing_entities:
            add_risk("entity", "entity_value_not_in_support")
    elif answer_entities and answered:
        add_risk("entity", "entity_value_without_support")

    state_conflict_signal = _state_conflict_signal(
        system_state=system_state,
        operation_journal=operation_journal,
    )
    if state_conflict_signal:
        dimension_counts["state_conflict"] = 1
        if answered and not support_rows:
            add_risk("state_conflict", "state_conflict_answer_without_support")
        if not _state_conflict_has_verify_audit(
            system_state=system_state,
            operation_journal=operation_journal,
        ):
            add_risk("state_conflict", "state_conflict_without_verify_or_audit")

    return {
        "applied": True,
        "valid_support_row_count": len(support_rows),
        "dimension_counts": {
            key: value for key, value in dimension_counts.items() if value
        },
        "risk_counts": {key: value for key, value in risk_counts.items() if value},
        "risks": tuple(dict.fromkeys(risks)),
    }


def _support_evidence_rows(
    support_items: tuple[dict[str, Any], ...],
    *,
    compiled: CompiledContext,
) -> tuple[Any, ...]:
    rows: list[Any] = []
    seen: set[int] = set()
    for item in support_items:
        for ref in _memory_reference_numbers(item):
            index = ref - 1
            if index < 0 or index >= len(compiled.evidence_rows):
                continue
            if index in seen:
                continue
            seen.add(index)
            rows.append(compiled.evidence_rows[index])
    return tuple(rows)


def _numeric_tokens(text: str) -> tuple[str, ...]:
    values = []
    for match in _NUMBER_PATTERN.findall(text or ""):
        normalized = match.strip().lstrip("$").replace(",", "")
        if normalized:
            values.append(normalized.lower())
    return tuple(dict.fromkeys(values))


def _temporal_tokens(text: str) -> tuple[str, ...]:
    lowered = " ".join((text or "").lower().split())
    values: list[str] = []
    values.extend(_normalize_date_token(token) for token in _DATE_PATTERN.findall(text))
    values.extend(_YEAR_PATTERN.findall(text or ""))
    words = re.findall(r"\b[a-zA-Z]+\b", text or "")
    values.extend(word.lower() for word in words if word.lower() in _MONTH_WORDS)
    values.extend(phrase for phrase in _TEMPORAL_PHRASES if phrase in lowered)
    return tuple(dict.fromkeys(value for value in values if value))


def _normalize_date_token(token: str) -> str:
    return token.strip().replace("/", "-").lower()


def _expected_source_role(question: str) -> str | None:
    for pattern in _ASSISTANT_ROLE_PATTERNS:
        if pattern.search(question or ""):
            return "assistant"
    for pattern in _USER_ROLE_PATTERNS:
        if pattern.search(question or ""):
            return "user"
    return None


def _answer_entity_tokens(answer: str, *, question: str) -> tuple[str, ...]:
    question_norm = _normalize_grounding_text(question)
    tokens: list[str] = []
    for match in _ENTITY_TOKEN_PATTERN.finditer(answer or ""):
        token = match.group(0).strip()
        if not token or token in _ENTITY_STOPWORDS:
            continue
        lowered = token.lower()
        if lowered in _MONTH_WORDS:
            continue
        if _normalize_grounding_text(token) in question_norm:
            continue
        tokens.append(token)
    return tuple(dict.fromkeys(tokens))


def _normalize_grounding_text(text: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", (text or "").lower()))


def _state_conflict_signal(
    *,
    system_state: dict[str, Any],
    operation_journal: dict[str, Any],
) -> bool:
    verifier_counts = system_state.get("verifier_check_counts") or {}
    focus_counts = system_state.get("focus_counts") or {}
    operation_counts = operation_journal.get("operation_counts") or {}
    return any(
        int(counts.get(key) or 0) > 0
        for counts, key in (
            (verifier_counts, "state_conflict"),
            (focus_counts, "conflict_chain"),
            (operation_counts, "supersede"),
            (operation_counts, "merge"),
            (operation_counts, "update"),
        )
    )


def _state_conflict_has_verify_audit(
    *,
    system_state: dict[str, Any],
    operation_journal: dict[str, Any],
) -> bool:
    verifier_counts = system_state.get("verifier_check_counts") or {}
    operation_counts = operation_journal.get("operation_counts") or {}
    return any(
        int(counts.get(key) or 0) > 0
        for counts, key in (
            (verifier_counts, "source_backing"),
            (verifier_counts, "raw_row_expansion"),
            (verifier_counts, "state_conflict"),
            (operation_counts, "verify"),
            (operation_counts, "audit"),
        )
    )


def _answer_is_insufficient(answer: str) -> bool:
    lowered = " ".join(answer.lower().split())
    return any(pattern in lowered for pattern in _INSUFFICIENT_PATTERNS)
