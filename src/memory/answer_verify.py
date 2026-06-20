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
    risks: tuple[str, ...]

    @property
    def risk_count(self) -> int:
        return len(self.risks)

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["risk_count"] = self.risk_count
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


def _answer_is_insufficient(answer: str) -> bool:
    lowered = " ".join(answer.lower().split())
    return any(pattern in lowered for pattern in _INSUFFICIENT_PATTERNS)
