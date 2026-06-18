"""Conservative answer finalization from structured evidence."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any


@dataclass(frozen=True)
class AnswerFinalization:
    """Traceable result for an answer finalizer or guardrail."""

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
_HOW_MANY_TARGET = re.compile(
    r"\bhow many\s+(.+?)(?:\s+"
    r"(?:do|does|did|have|has|had|am|is|are|was|were|will|would|"
    r"could|should|can|that)\b|\?)",
    re.IGNORECASE,
)
_DURATION_COUNT_QUESTION = re.compile(
    r"\bhow many\s+(?:days?|weeks?|months?|years?|hours?|minutes?)\b|\bhow long\b",
    re.IGNORECASE,
)
_DURATION_UNIT_QUESTION = re.compile(
    r"\bhow many\s+(days?|weeks?|months?|years?)\b",
    re.IGNORECASE,
)
_DECIMAL_DURATION_ANSWER = re.compile(
    r"^\s*(?:about\s+|approximately\s+)?([0-9]+(?:\.[0-9]+)?)\s+"
    r"(days?|weeks?|months?|years?)\s*$",
    re.IGNORECASE,
)
_SUM_QUESTION = re.compile(
    r"\b(total|sum|combined|altogether|in all|how much)\b",
    re.IGNORECASE,
)
_AVERAGE_QUESTION = re.compile(
    r"\b(?:what(?:\s+is|'s)?\s+the\s+average|average\s+[^?]*\bof\b|"
    r"mean\s+[^?]*\bof\b)\b",
    re.IGNORECASE,
)
_AVERAGE_COMPARISON = re.compile(
    r"\b(older|younger|more|less|than|difference|above|below)\b",
    re.IGNORECASE,
)
_MONEY_QUESTION = re.compile(
    r"(\$|\bdollars?\b|\bcost\b|\bcosts\b|\bspend\b|\bspent\b|\bpaid\b|"
    r"\bprice\b|\bprices\b|\bexpense\b|\bexpenses\b|\bcharge\b|\bcharges\b)",
    re.IGNORECASE,
)
_MONEY_DIFFERENCE_QUESTION = re.compile(
    r"\b(how much more|how much less|difference|compared to|compare|versus|vs\.?)\b",
    re.IGNORECASE,
)
_DATE_ENDPOINT_DURATION_QUESTION = re.compile(
    r"\bhow many\s+days?\b|\bhow long\b",
    re.IGNORECASE,
)
_RELATIVE_DATE_QUESTION = re.compile(
    r"^\s*when\b|\bwhat\s+(?:date|day|time)\b",
    re.IGNORECASE,
)
_INSUFFICIENT_ANSWER = re.compile(
    r"\b(not enough|insufficient|cannot determine|can't determine|not available|"
    r"unknown|do not know|don't know)\b",
    re.IGNORECASE,
)
_BARE_NUMERIC_ANSWER = re.compile(
    r"^\s*[0-9][0-9,]*(?:\.[0-9]+)?\s*$",
    re.IGNORECASE,
)
_LEVEL_SLOT = re.compile(r"\blevel\b", re.IGNORECASE)
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
_DATE_RANGE_ANSWER = re.compile(
    r"\b(?:19|20)\d{2}[-/]\d{1,2}[-/]\d{1,2}\s+to\s+"
    r"(?:19|20)\d{2}[-/]\d{1,2}[-/]\d{1,2}\b",
    re.IGNORECASE,
)
_ISO_DATE = re.compile(r"\b((?:19|20)\d{2})-(\d{1,2})-(\d{1,2})\b")
_SLASH_DATE = re.compile(r"\b((?:19|20)\d{2})/(\d{1,2})/(\d{1,2})\b")
_FILTER_REASON = re.compile(
    r"\b(duplicate|out[-_ ]of[-_ ]scope|irrelevant|wrong[_ -]?time|"
    r"not[_ -]?confirmed|assistant[_ -]?suggestion|hypothetical|planned)\b",
    re.IGNORECASE,
)
_WEEKDAY_INDEX = {
    "mon": 0,
    "monday": 0,
    "tue": 1,
    "tues": 1,
    "tuesday": 1,
    "wed": 2,
    "wednesday": 2,
    "thu": 3,
    "thur": 3,
    "thurs": 3,
    "thursday": 3,
    "fri": 4,
    "friday": 4,
    "sat": 5,
    "saturday": 5,
    "sun": 6,
    "sunday": 6,
}


def finalize_structured_answer(
    *,
    question: str,
    draft_answer: str,
    raw_response: str | None,
    enable_count_correction: bool = False,
    enable_evidence_report_count_correction: bool = False,
    enable_money_sum_correction: bool = True,
    enable_duration_rounding_correction: bool = False,
    enable_missing_detail: bool = False,
    enable_count_answer_detail: bool = False,
    enable_average_calculation: bool = False,
    enable_money_difference_calculation: bool = False,
    enable_date_endpoint_duration_calculation: bool = False,
    enable_relative_time_calculation: bool = False,
) -> AnswerFinalization:
    """Repair only narrow count/sum mismatches exposed by model evidence JSON.

    The function uses only prediction-time artifacts: the question, the answer
    model response, and its structured evidence fields. It never reads labels,
    judge output, benchmark metadata, or sample identifiers.
    """

    if enable_duration_rounding_correction:
        rounded = _finalize_duration_rounding(
            question=question,
            draft_answer=draft_answer,
        )
        if rounded is not None:
            return rounded

    content = raw_response_content(raw_response)
    if not content:
        return _noop(draft_answer, "no_raw_response_content")
    payload = extract_json_object(content)
    if not payload:
        return _noop(draft_answer, "no_structured_answer_json")
    if payload.get("sufficient") is False:
        if enable_money_difference_calculation:
            money_difference = _finalize_money_difference(
                question=question,
                draft_answer=draft_answer,
                payload=payload,
            )
            if money_difference is not None:
                return money_difference
        if enable_missing_detail:
            detailed = _finalize_missing_detail(
                draft_answer=draft_answer,
                payload=payload,
            )
            if detailed is not None:
                return detailed
        return _noop(draft_answer, "model_marked_insufficient")

    lowered_question = question.lower()
    if enable_relative_time_calculation:
        relative_time = _finalize_relative_time_calculation(
            question=question,
            lowered_question=lowered_question,
            draft_answer=draft_answer,
            payload=payload,
        )
        if relative_time is not None:
            return relative_time

    if enable_evidence_report_count_correction and _is_count_question(
        lowered_question
    ):
        report_counted = _finalize_evidence_report_count_increment(
            draft_answer=draft_answer,
            payload=payload,
        )
        if report_counted is not None:
            return report_counted

    if enable_count_answer_detail and _is_count_question(lowered_question):
        detailed_count = _finalize_evidence_report_count_detail(
            question=question,
            lowered_question=lowered_question,
            draft_answer=draft_answer,
            payload=payload,
        )
        if detailed_count is not None:
            return detailed_count

    if enable_average_calculation and _is_average_question(question):
        averaged = _finalize_average_calculation(
            draft_answer=draft_answer,
            payload=payload,
        )
        if averaged is not None:
            return averaged

    if enable_money_difference_calculation:
        money_difference = _finalize_money_difference(
            question=question,
            draft_answer=draft_answer,
            payload=payload,
        )
        if money_difference is not None:
            return money_difference

    if enable_date_endpoint_duration_calculation:
        date_duration = _finalize_date_endpoint_duration(
            question=question,
            draft_answer=draft_answer,
            payload=payload,
        )
        if date_duration is not None:
            return date_duration

    items = _extract_items(payload)
    if not items:
        return _noop(draft_answer, "no_structured_evidence_items")

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


def guard_source_grounded_answer(
    *,
    question: str = "",
    draft_answer: str,
    raw_response: str | None,
    enable_missing_detail: bool = False,
    enable_numeric_slot_label_preservation: bool = False,
) -> AnswerFinalization:
    """Generic source-grounded guardrail that never computes a new answer.

    This mode only uses the answer model's structured response as a consistency
    trace. It may expand a short insufficient answer with the model's own
    missing-evidence field, but it does not count, sum, calculate dates, resolve
    relative time, or otherwise rewrite a supported answer.
    """

    content = raw_response_content(raw_response)
    if not content:
        return _noop(draft_answer, "no_raw_response_content")
    payload = extract_json_object(content)
    if not payload:
        return _noop(draft_answer, "no_structured_answer_json")
    if payload.get("sufficient") is False:
        if enable_missing_detail:
            detailed = _finalize_missing_detail(
                draft_answer=draft_answer,
                payload=payload,
            )
            if detailed is not None:
                return AnswerFinalization(
                    answer=detailed.answer,
                    before=detailed.before,
                    applied=True,
                    reason="source_grounded_missing_detail",
                    evidence_item_count=detailed.evidence_item_count,
                    expected_value=detailed.expected_value,
                )
        return _noop(draft_answer, "model_marked_insufficient")
    if enable_numeric_slot_label_preservation:
        labeled = _finalize_numeric_slot_label_preservation(
            question=question,
            draft_answer=draft_answer,
            payload=payload,
        )
        if labeled is not None:
            return labeled
    return _noop(draft_answer, "source_grounded_guard_consistent")


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


def _is_average_question(question: str) -> bool:
    return bool(_AVERAGE_QUESTION.search(question)) and not bool(
        _AVERAGE_COMPARISON.search(question)
    )


def _answer_is_insufficient(answer: str) -> bool:
    return bool(_INSUFFICIENT_ANSWER.search(answer))


def _finalize_missing_detail(
    *,
    draft_answer: str,
    payload: dict[str, Any],
) -> AnswerFinalization | None:
    if not _answer_is_insufficient(draft_answer):
        return None
    if len(draft_answer.split()) > 10:
        return None
    missing = _compact_missing_detail(
        str(payload.get("missing") or payload.get("missing_info") or "")
    )
    if not missing:
        return None
    return AnswerFinalization(
        answer=f"The provided information is not enough to answer the question: {missing}",
        before=draft_answer,
        applied=True,
        reason="missing_detail_from_structured_answer",
        expected_value=missing,
    )


def _finalize_numeric_slot_label_preservation(
    *,
    question: str,
    draft_answer: str,
    payload: dict[str, Any],
) -> AnswerFinalization | None:
    """Preserve a source-backed numeric slot label without changing the value."""

    if _answer_is_insufficient(draft_answer):
        return None
    if not _BARE_NUMERIC_ANSWER.fullmatch(draft_answer):
        return None
    if not _LEVEL_SLOT.search(question):
        return None

    lowered_question = question.lower()
    if (
        _COUNT_QUESTION.search(lowered_question)
        or _DURATION_COUNT_QUESTION.search(lowered_question)
        or _SUM_QUESTION.search(lowered_question)
        or _MONEY_QUESTION.search(lowered_question)
        or _is_average_question(question)
    ):
        return None

    expected = _extract_plain_value(draft_answer)
    if expected is None:
        return None
    report = payload.get("evidence_report")
    if not isinstance(report, list):
        return None

    matches = []
    for item in report:
        if not isinstance(item, dict):
            continue
        if str(item.get("status") or "").strip().lower() != "support":
            continue
        value = str(item.get("value") or "")
        item_value = _extract_plain_value(value)
        if item_value is None or item_value != expected:
            continue
        basis = " ".join(
            str(item.get(field) or "") for field in ("slot", "value", "reason")
        )
        if _LEVEL_SLOT.search(basis):
            matches.append(item)

    if not matches:
        return None
    answer = f"level {draft_answer.strip()}"
    return AnswerFinalization(
        answer=answer,
        before=draft_answer,
        applied=True,
        reason="numeric_slot_label_preservation",
        evidence_item_count=len(matches),
        expected_value=answer,
    )


def _compact_missing_detail(text: str) -> str:
    detail = re.sub(r"\s+", " ", text).strip(" .")
    if not detail:
        return ""
    if len(detail) > 220:
        detail = detail[:217].rstrip() + "..."
    return detail


def _finalize_duration_rounding(
    *,
    question: str,
    draft_answer: str,
) -> AnswerFinalization | None:
    if _answer_is_insufficient(draft_answer):
        return None
    question_match = _DURATION_UNIT_QUESTION.search(question)
    if not question_match:
        return None
    answer_match = _DECIMAL_DURATION_ANSWER.match(draft_answer)
    if not answer_match:
        return None
    value = _decimal(answer_match.group(1))
    if value is None or value == value.to_integral_value():
        return None
    question_unit = _singular_unit(question_match.group(1))
    answer_unit = _singular_unit(answer_match.group(2))
    if question_unit != answer_unit:
        return None
    rounded = int(value.to_integral_value(rounding=ROUND_HALF_UP))
    unit = question_unit if rounded == 1 else f"{question_unit}s"
    return AnswerFinalization(
        answer=f"{rounded} {unit}",
        before=draft_answer,
        applied=True,
        reason="duration_decimal_rounding",
        expected_value=str(rounded),
    )


def _singular_unit(unit: str) -> str:
    return unit.lower().rstrip("s")


def _extract_items(payload: dict[str, Any]) -> list[dict[str, Any]]:
    for key in ("evidence_items", "items", "counted_items"):
        value = payload.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
    return []


def _finalize_evidence_report_count_increment(
    *,
    draft_answer: str,
    payload: dict[str, Any],
) -> AnswerFinalization | None:
    if _answer_is_insufficient(draft_answer):
        return None
    if str(payload.get("answer_type") or "").lower() != "count":
        return None
    report = payload.get("evidence_report")
    if not isinstance(report, list):
        return None
    supports = [
        item
        for item in report
        if isinstance(item, dict)
        and str(item.get("status") or "").strip().lower() == "support"
    ]
    if len(supports) < 2:
        return None
    increments: list[tuple[dict[str, Any], Decimal]] = []
    for item in supports:
        if str(item.get("operand_value") or "").strip():
            return None
        increment = _extract_plain_value(str(item.get("count_increment") or ""))
        if increment is None:
            return None
        if (
            increment <= 0
            or increment != increment.to_integral_value()
            or increment > 1000
        ):
            return None
        increments.append((item, increment))
    total = sum(value for _, value in increments)
    if not _numeric_answer_disagrees(draft_answer, total):
        return None
    labels = [
        _compact_label(
            str(
                item.get("canonical_item")
                or item.get("value")
                or item.get("reason")
                or "item"
            )
        )
        for item, _ in increments
    ]
    labels = [label for label in labels if label]
    answer = str(int(total))
    if labels:
        answer = f"{answer}: {', '.join(labels[:8])}"
    return AnswerFinalization(
        answer=answer,
        before=draft_answer,
        applied=True,
        reason="evidence_report_count_increment_consistency",
        evidence_item_count=len(increments),
        expected_value=str(int(total)),
    )


def _finalize_evidence_report_count_detail(
    *,
    question: str,
    lowered_question: str,
    draft_answer: str,
    payload: dict[str, Any],
) -> AnswerFinalization | None:
    if _answer_is_insufficient(draft_answer):
        return None
    if _DURATION_COUNT_QUESTION.search(lowered_question):
        return None
    if len(draft_answer.split()) > 4:
        return None
    if str(payload.get("answer_type") or "").lower() not in {"count", "list"}:
        return None
    report = payload.get("evidence_report")
    if not isinstance(report, list):
        return None
    labels = _evidence_report_support_labels(report)
    if len(labels) < 2:
        return None
    expected = Decimal(len(labels))
    if not _numeric_answer_contains(draft_answer, expected):
        return None
    answer_terms = set(_clean_key(draft_answer).split())
    for label in labels:
        label_terms = _clean_key(label).split()
        if label_terms and label_terms[0] in answer_terms:
            return None
    return AnswerFinalization(
        answer=_format_count_detail_answer(int(expected), labels, question),
        before=draft_answer,
        applied=True,
        reason="evidence_report_count_answer_detail",
        evidence_item_count=len(labels),
        expected_value=str(int(expected)),
    )


def _evidence_report_support_labels(report: list[Any]) -> list[str]:
    labels = []
    seen: set[str] = set()
    for item in report:
        if not isinstance(item, dict):
            continue
        if str(item.get("status") or "").strip().lower() != "support":
            continue
        label = _evidence_report_label(item)
        key = _clean_key(label)
        if not key or key in seen:
            continue
        seen.add(key)
        labels.append(label)
    return labels


def _evidence_report_label(item: dict[str, Any]) -> str:
    label = _compact_label(
        str(
            item.get("canonical_item")
            or item.get("value")
            or item.get("slot")
            or item.get("reason")
            or ""
        )
    )
    if not label:
        return ""
    terms = _clean_key(label).split()
    if _extract_plain_value(label) is not None and len(terms) <= 3:
        return ""
    return label


def _format_count_detail_answer(count: int, labels: list[str], question: str) -> str:
    target = _count_target_phrase(question)
    prefix = f"{count} {target}" if target else str(count)
    return f"{prefix}: {', '.join(labels[:8])}"


def _count_target_phrase(question: str) -> str:
    match = _HOW_MANY_TARGET.search(question)
    if not match:
        return ""
    phrase = re.sub(r"\s+", " ", match.group(1)).strip(" ?:;,.")
    if not phrase:
        return ""
    if len(phrase) > 70:
        phrase = phrase[:67].rstrip() + "..."
    return phrase


def _finalize_average_calculation(
    *,
    draft_answer: str,
    payload: dict[str, Any],
) -> AnswerFinalization | None:
    if _answer_is_insufficient(draft_answer):
        return None
    report = payload.get("evidence_report")
    if not isinstance(report, list):
        return None
    values = _evidence_report_numeric_support_values(report)
    if not 2 <= len(values) <= 6:
        return None
    average = (sum(values) / Decimal(len(values))).quantize(Decimal("0.01"))
    if _numeric_answer_contains(draft_answer, average):
        return None
    if not any(_numeric_answer_contains(draft_answer, value) for value in values):
        return None
    operands = " + ".join(_format_decimal(value) for value in values[:6])
    answer = f"{_format_decimal(average)} average (({operands}) / {len(values)})"
    return AnswerFinalization(
        answer=answer,
        before=draft_answer,
        applied=True,
        reason="evidence_report_average_calculation",
        evidence_item_count=len(values),
        expected_value=_format_decimal(average),
    )


def _evidence_report_numeric_support_values(report: list[Any]) -> list[Decimal]:
    values = []
    for item in report:
        if not isinstance(item, dict):
            continue
        if str(item.get("status") or "").strip().lower() != "support":
            continue
        raw_value = str(item.get("value") or "").strip()
        if not raw_value or _DATE_LIKE.search(raw_value):
            continue
        value = _extract_plain_value(raw_value)
        if value is None:
            continue
        values.append(value)
    return values


def _finalize_money_difference(
    *,
    question: str,
    draft_answer: str,
    payload: dict[str, Any],
) -> AnswerFinalization | None:
    if not _MONEY_DIFFERENCE_QUESTION.search(question):
        return None
    report = payload.get("evidence_report")
    if not isinstance(report, list):
        return None
    values = _evidence_report_money_support_values(report)
    if len(values) != 2:
        return None
    difference = abs(values[0][1] - values[1][1])
    if difference <= 0:
        return None
    if _numeric_answer_contains(draft_answer, difference):
        return None
    return AnswerFinalization(
        answer=f"${_format_decimal(difference)}",
        before=draft_answer,
        applied=True,
        reason="evidence_report_money_difference",
        evidence_item_count=len(values),
        expected_value=_format_decimal(difference),
    )


def _evidence_report_money_support_values(
    report: list[Any],
) -> list[tuple[str, Decimal]]:
    values = []
    seen: set[Decimal] = set()
    for item in report:
        if not isinstance(item, dict):
            continue
        if str(item.get("status") or "").strip().lower() != "support":
            continue
        raw_value = str(item.get("value") or "").strip()
        value = _extract_money_value(raw_value)
        if value is None or value in seen:
            continue
        seen.add(value)
        values.append((raw_value, value))
    return values


def _finalize_date_endpoint_duration(
    *,
    question: str,
    draft_answer: str,
    payload: dict[str, Any],
) -> AnswerFinalization | None:
    if _answer_is_insufficient(draft_answer):
        return None
    if not _DATE_ENDPOINT_DURATION_QUESTION.search(question):
        return None
    if re.search(r"\bhow many\s+(?:weeks?|months?|years?)\b", question, re.IGNORECASE):
        return None
    report = payload.get("evidence_report")
    if not isinstance(report, list):
        return None
    dates = _evidence_report_support_dates(report)
    if len(dates) != 2:
        return None
    days = abs((dates[0] - dates[1]).days)
    if days <= 0 or days > 90:
        return None
    expected = Decimal(days)
    if _numeric_answer_contains(draft_answer, expected):
        return None
    return AnswerFinalization(
        answer=f"{days} days",
        before=draft_answer,
        applied=True,
        reason="evidence_report_date_endpoint_duration",
        evidence_item_count=len(dates),
        expected_value=str(days),
    )


def _evidence_report_support_dates(report: list[Any]) -> list[date]:
    dates = []
    seen: set[date] = set()
    for item in report:
        if not isinstance(item, dict):
            continue
        if str(item.get("status") or "").strip().lower() != "support":
            continue
        raw_value = str(item.get("value") or "")
        for match in _ISO_DATE.finditer(raw_value):
            parsed = _parse_iso_date(match)
            if parsed is None or parsed in seen:
                continue
            seen.add(parsed)
            dates.append(parsed)
    return dates


def _parse_iso_date(match: re.Match[str]) -> date | None:
    try:
        return date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
    except ValueError:
        return None


def _finalize_relative_time_calculation(
    *,
    question: str,
    lowered_question: str,
    draft_answer: str,
    payload: dict[str, Any],
) -> AnswerFinalization | None:
    if _answer_is_insufficient(draft_answer):
        return None
    if _DURATION_COUNT_QUESTION.search(lowered_question):
        return None
    if not _RELATIVE_DATE_QUESTION.search(question):
        return None
    answer_type = str(payload.get("answer_type") or "").strip().lower()
    if answer_type and answer_type not in {"date", "time"}:
        return None
    report = payload.get("evidence_report")
    if not isinstance(report, list):
        return None

    candidates: list[tuple[int, str]] = []
    for item in report:
        if not isinstance(item, dict):
            continue
        if str(item.get("status") or "").strip().lower() != "support":
            continue
        phrase = str(item.get("time_phrase") or "").strip()
        if not phrase or phrase.lower() in {"none", "n/a", "na", "empty"}:
            continue
        anchor = _parse_date_text(
            str(
                item.get("mention_time")
                or item.get("mention_date")
                or item.get("date")
                or ""
            )
        )
        if anchor is None:
            continue
        resolved = _resolve_relative_time_phrase(phrase, anchor)
        if resolved is None:
            continue
        specificity, answer = resolved
        answer_is_range = _is_iso_date_range_answer(answer)
        if not _is_iso_date_answer(answer) and not answer_is_range:
            continue
        if answer_is_range and _is_iso_date_answer(draft_answer):
            continue
        candidates.append((specificity, answer))

    if not candidates:
        return None
    candidate_answers = {_normalize_answer_date_text(answer) for _, answer in candidates}
    if len(candidate_answers) != 1:
        return None
    max_specificity = max(score for score, _answer in candidates)
    best_answers = {
        _normalize_answer_date_text(answer)
        for score, answer in candidates
        if score == max_specificity
    }
    if len(best_answers) != 1:
        return None
    answer = next(iter(best_answers))
    if _normalize_answer_date_text(draft_answer) == answer:
        return None
    return AnswerFinalization(
        answer=answer,
        before=draft_answer,
        applied=True,
        reason="evidence_report_relative_time_calculation",
        expected_value=answer,
    )


def _parse_date_text(text: str) -> date | None:
    for pattern in (_ISO_DATE, _SLASH_DATE):
        match = pattern.search(text)
        if not match:
            continue
        try:
            return date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
        except ValueError:
            return None
    return None


def _resolve_relative_time_phrase(
    phrase: str,
    anchor: date,
) -> tuple[int, str] | None:
    lowered = phrase.lower()
    if re.search(r"\blast night\b|\byesterday\b", lowered):
        return 4, _iso_date(anchor - timedelta(days=1))
    if re.search(r"\bday after tomorrow\b", lowered):
        return 4, _iso_date(anchor + timedelta(days=2))
    if re.search(r"\btomorrow\b", lowered):
        return 4, _iso_date(anchor + timedelta(days=1))

    weekday_match = re.search(
        r"\blast\s+"
        r"(mon(?:day)?|tue(?:s|sday)?|wed(?:nesday)?|thu(?:r|rs|rsday|rday)?|"
        r"fri(?:day)?|sat(?:urday)?|sun(?:day)?)\b",
        lowered,
    )
    if weekday_match:
        weekday = _WEEKDAY_INDEX.get(weekday_match.group(1))
        if weekday is None:
            return None
        days_back = (anchor.weekday() - weekday) % 7
        if days_back == 0:
            days_back = 7
        return 3, _iso_date(anchor - timedelta(days=days_back))

    if re.search(r"\b(two weekends ago|two weekends before)\b", lowered):
        start, end = _weekend_before(anchor)
        start -= timedelta(days=7)
        end -= timedelta(days=7)
        return 2, _iso_date_range(start, end)
    if re.search(r"\b(last weekend|this past weekend|past weekend)\b", lowered):
        start, end = _weekend_before(anchor)
        return 2, _iso_date_range(start, end)
    if re.search(r"\b(two weekends later|two weekends after)\b", lowered):
        start, end = _weekend_after(anchor)
        start += timedelta(days=7)
        end += timedelta(days=7)
        return 2, _iso_date_range(start, end)
    if re.search(r"\b(next weekend|coming weekend|weekend after)\b", lowered):
        start, end = _weekend_after(anchor)
        return 2, _iso_date_range(start, end)

    if re.search(r"\b(last week|the week before)\b", lowered):
        return 1, _iso_date_range(anchor - timedelta(days=7), anchor - timedelta(days=1))
    if re.search(r"\b(next week|the following week|week after)\b", lowered):
        return 1, _iso_date_range(anchor + timedelta(days=1), anchor + timedelta(days=7))
    return None


def _iso_date(value: date) -> str:
    return value.isoformat()


def _iso_date_range(start: date, end: date) -> str:
    return f"{_iso_date(start)} to {_iso_date(end)}"


def _weekend_before(anchor: date) -> tuple[date, date]:
    days_since_saturday = (anchor.weekday() - 5) % 7
    if days_since_saturday == 0:
        days_since_saturday = 7
    saturday = anchor - timedelta(days=days_since_saturday)
    sunday = saturday + timedelta(days=1)
    if sunday >= anchor:
        saturday -= timedelta(days=7)
        sunday -= timedelta(days=7)
    return saturday, sunday


def _weekend_after(anchor: date) -> tuple[date, date]:
    days_until_saturday = (5 - anchor.weekday()) % 7
    if days_until_saturday == 0:
        days_until_saturday = 7
    saturday = anchor + timedelta(days=days_until_saturday)
    return saturday, saturday + timedelta(days=1)


def _is_iso_date_answer(value: str) -> bool:
    return bool(_ISO_DATE.fullmatch(value.strip()))


def _is_iso_date_range_answer(value: str) -> bool:
    return bool(_DATE_RANGE_ANSWER.fullmatch(value.strip()))


def _normalize_answer_date_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip(" .")


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


def _numeric_answer_contains(answer: str, expected: Decimal) -> bool:
    return not _numeric_answer_disagrees(answer, expected)


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
