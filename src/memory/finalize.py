"""Conservative answer finalization from structured evidence."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation
from typing import Any


@dataclass(frozen=True)
class AnswerFinalization:
    """Traceable result for a mechanical answer finalizer."""

    answer: str
    before: str
    applied: bool
    reason: str
    evidence_item_count: int = 0
    expected_value: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


_COUNT_QUESTION = re.compile(
    r"\b(how many|number of|count of|count|total number of)\b",
    re.IGNORECASE,
)
_DURATION_COUNT_QUESTION = re.compile(
    r"\bhow many\s+(?:days?|weeks?|months?|years?|hours?|minutes?)\b|\bhow long\b",
    re.IGNORECASE,
)
_SUM_QUESTION = re.compile(
    r"\b(total|sum|combined|altogether|in all|how much)\b",
    re.IGNORECASE,
)
_MONEY_QUESTION = re.compile(
    r"(\$|\bdollars?\b|\bcost\b|\bcosts\b|\bspend\b|\bspent\b|\bpaid\b|"
    r"\bprice\b|\bprices\b|\bexpense\b|\bexpenses\b|\bcharge\b|\bcharges\b)",
    re.IGNORECASE,
)
_INSUFFICIENT_ANSWER = re.compile(
    r"\b(not enough|insufficient|cannot determine|can't determine|not available|"
    r"unknown|do not know|don't know)\b",
    re.IGNORECASE,
)
_NUMBER = re.compile(r"(?<![A-Za-z])([0-9][0-9,]*(?:\.[0-9]+)?)(?![A-Za-z])")
_MONEY = re.compile(
    r"(?:\$\s*([0-9][0-9,]*(?:\.[0-9]+)?)|"
    r"([0-9][0-9,]*(?:\.[0-9]+)?)\s*(?:dollars?|usd)\b)",
    re.IGNORECASE,
)
_DATE_LIKE = re.compile(
    r"\b(?:19|20)\d{2}[-/]\d{1,2}[-/]\d{1,2}\b|"
    r"\b(?:19|20)\d{2}\b|"
    r"\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b"
)
_FILTER_REASON = re.compile(
    r"\b(duplicate|out[-_ ]of[-_ ]scope|irrelevant|wrong[_ -]?time|"
    r"not[_ -]?confirmed|assistant[_ -]?suggestion|hypothetical|planned)\b",
    re.IGNORECASE,
)


def finalize_structured_answer(
    *,
    question: str,
    draft_answer: str,
    raw_response: str | None,
    enable_count_correction: bool = False,
    enable_money_sum_correction: bool = True,
) -> AnswerFinalization:
    """Repair only narrow count/sum mismatches exposed by model evidence JSON.

    The function uses only prediction-time artifacts: the question, the answer
    model response, and its structured evidence fields. It never reads labels,
    judge output, benchmark metadata, or sample identifiers.
    """

    content = raw_response_content(raw_response)
    if not content:
        return _noop(draft_answer, "no_raw_response_content")
    payload = extract_json_object(content)
    if not payload:
        return _noop(draft_answer, "no_structured_answer_json")
    if payload.get("sufficient") is False:
        return _noop(draft_answer, "model_marked_insufficient")

    items = _extract_items(payload)
    if not items:
        return _noop(draft_answer, "no_structured_evidence_items")

    lowered_question = question.lower()
    if enable_money_sum_correction and _is_sum_question(lowered_question):
        summed = _finalize_money_sum(
            lowered_question=lowered_question,
            draft_answer=draft_answer,
            items=items,
        )
        if summed is not None:
            return summed

    if enable_count_correction and _is_count_question(lowered_question):
        counted = _finalize_count(
            lowered_question=lowered_question,
            draft_answer=draft_answer,
            items=items,
        )
        if counted is not None:
            return counted

    return _noop(draft_answer, "unsupported_or_consistent")


def raw_response_content(raw_response: str | None) -> str:
    if not raw_response:
        return ""
    try:
        payload = json.loads(raw_response)
    except json.JSONDecodeError:
        return ""
    if isinstance(payload, dict) and payload.get("content") is not None:
        return str(payload["content"])
    return ""


def extract_json_object(text: str) -> dict[str, Any] | None:
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


def _noop(answer: str, reason: str) -> AnswerFinalization:
    return AnswerFinalization(
        answer=answer,
        before=answer,
        applied=False,
        reason=reason,
    )


def _is_count_question(lowered_question: str) -> bool:
    return bool(_COUNT_QUESTION.search(lowered_question)) and not bool(
        _DURATION_COUNT_QUESTION.search(lowered_question)
    )


def _is_sum_question(lowered_question: str) -> bool:
    return bool(_SUM_QUESTION.search(lowered_question)) and bool(
        _MONEY_QUESTION.search(lowered_question)
    )


def _answer_is_insufficient(answer: str) -> bool:
    return bool(_INSUFFICIENT_ANSWER.search(answer))


def _extract_items(payload: dict[str, Any]) -> list[dict[str, Any]]:
    for key in ("evidence_items", "items", "counted_items"):
        value = payload.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
    return []


def _item_included(item: dict[str, Any]) -> bool:
    include = item.get("include")
    if include is not None:
        return bool(include)
    return True


def _normalize_item(item: dict[str, Any]) -> dict[str, str]:
    return {
        "canonical_item": str(
            item.get("canonical_item")
            or item.get("item")
            or item.get("name")
            or item.get("event")
            or item.get("memory")
            or ""
        ).strip(),
        "date": str(item.get("date") or "").strip(),
        "evidence": str(
            item.get("evidence")
            or item.get("quote")
            or item.get("text")
            or item.get("reason")
            or ""
        ).strip(),
        "value": str(item.get("value") or "").strip(),
        "reason": str(item.get("reason") or "").strip(),
    }


def _included_items(
    items: list[dict[str, Any]],
    *,
    lowered_question: str,
) -> list[dict[str, str]]:
    allow_suggestions = bool(
        re.search(r"\b(plan|plans|planned|suggest|suggestion|recommend)\b", lowered_question)
    )
    included = []
    for item in items:
        normalized = _normalize_item(item)
        if not _item_included(item):
            continue
        if _FILTER_REASON.search(normalized["reason"]) and not allow_suggestions:
            continue
        included.append(normalized)
    return included


def _dedupe_items(items: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[str] = set()
    output = []
    for item in items:
        key = _item_key(item)
        if not key or key in seen:
            continue
        seen.add(key)
        output.append(item)
    return output


def _item_key(item: dict[str, str]) -> str:
    for field in ("canonical_item", "value", "evidence"):
        value = item.get(field, "")
        key = _clean_key(value)
        if key:
            return key
    return ""


def _clean_key(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def _finalize_count(
    *,
    lowered_question: str,
    draft_answer: str,
    items: list[dict[str, Any]],
) -> AnswerFinalization | None:
    if _answer_is_insufficient(draft_answer):
        return None
    included = _dedupe_items(
        _included_items(items, lowered_question=lowered_question)
    )
    if len(included) < 2:
        return None
    expected = Decimal(len(included))
    if not _numeric_answer_disagrees(draft_answer, expected):
        return None
    answer = _format_count_answer(included)
    return AnswerFinalization(
        answer=answer,
        before=draft_answer,
        applied=True,
        reason="structured_evidence_count_consistency",
        evidence_item_count=len(included),
        expected_value=str(len(included)),
    )


def _finalize_money_sum(
    *,
    lowered_question: str,
    draft_answer: str,
    items: list[dict[str, Any]],
) -> AnswerFinalization | None:
    if _answer_is_insufficient(draft_answer):
        return None
    included = _dedupe_items(
        _included_items(items, lowered_question=lowered_question)
    )
    numeric_items = _numeric_money_items(included)
    if len(numeric_items) < 2:
        return None
    total = sum(value for _, value in numeric_items)
    if not _numeric_answer_disagrees(draft_answer, total):
        return None
    answer = _format_sum_answer(total, numeric_items)
    return AnswerFinalization(
        answer=answer,
        before=draft_answer,
        applied=True,
        reason="structured_evidence_money_sum_consistency",
        evidence_item_count=len(numeric_items),
        expected_value=_format_decimal(total),
    )


def _numeric_money_items(items: list[dict[str, str]]) -> list[tuple[str, Decimal]]:
    output: list[tuple[str, Decimal]] = []
    seen: set[tuple[str, str]] = set()
    for item in items:
        value = _extract_money_value(item.get("value", ""))
        if value is None:
            value = _extract_money_value(item.get("evidence", ""))
        if value is None:
            value = _extract_plain_value(item.get("value", ""))
        if value is None:
            continue
        label = item.get("canonical_item") or item.get("evidence") or "item"
        key = (_clean_key(label), str(value))
        if key in seen:
            continue
        seen.add(key)
        output.append((label, value))
    return output


def _extract_money_value(text: str) -> Decimal | None:
    for match in _MONEY.finditer(text):
        raw = match.group(1) or match.group(2)
        value = _decimal(raw)
        if value is not None:
            return value
    return None


def _extract_plain_value(text: str) -> Decimal | None:
    if not text or _DATE_LIKE.search(text):
        return None
    matches = list(_NUMBER.finditer(text))
    if len(matches) != 1:
        return None
    return _decimal(matches[0].group(1))


def _decimal(value: str | None) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(value.replace(",", ""))
    except (InvalidOperation, AttributeError):
        return None


def _numeric_answer_disagrees(answer: str, expected: Decimal) -> bool:
    numbers = [
        value
        for value in (_decimal(match.group(1)) for match in _NUMBER.finditer(answer))
        if value is not None
    ]
    if not numbers:
        return True
    return all(value != expected for value in numbers)


def _format_count_answer(items: list[dict[str, str]]) -> str:
    labels = [
        _compact_label(item.get("canonical_item") or item.get("value") or item["evidence"])
        for item in items
    ]
    labels = [label for label in labels if label]
    if labels:
        return f"{len(items)}: {', '.join(labels[:8])}"
    return str(len(items))


def _format_sum_answer(total: Decimal, items: list[tuple[str, Decimal]]) -> str:
    operands = ", ".join(
        f"{_compact_label(label)} ${_format_decimal(value)}"
        for label, value in items[:8]
    )
    if operands:
        return f"${_format_decimal(total)} total ({operands})"
    return f"${_format_decimal(total)} total"


def _format_decimal(value: Decimal) -> str:
    if value == value.to_integral_value():
        return str(int(value))
    return format(value.normalize(), "f")


def _compact_label(value: str) -> str:
    value = re.sub(r"\s+", " ", value).strip()
    value = value.strip(" -:;,.")
    if len(value) <= 80:
        return value
    return value[:77].rstrip() + "..."
