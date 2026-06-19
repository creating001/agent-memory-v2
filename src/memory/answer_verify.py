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


def _answer_is_insufficient(answer: str) -> bool:
    lowered = " ".join(answer.lower().split())
    return any(pattern in lowered for pattern in _INSUFFICIENT_PATTERNS)
