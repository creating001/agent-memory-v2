"""Clean-setting guards for prediction-time inputs."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass


class CleanProtocolViolation(ValueError):
    """Raised when prediction-time data contains forbidden fields."""


FORBIDDEN_PREDICTION_KEYS = {
    "answer",
    "answers",
    "benchmark_label",
    "category",
    "gold",
    "gold_answer",
    "gold_answers",
    "judge",
    "judge_label",
    "judge_output",
    "judge_rationale",
    "label",
    "labels",
    "qid",
    "question_type",
    "reference",
    "reference_answer",
    "reference_answers",
    "row_index",
    "sample_id",
    "target",
    "targets",
}


TOP_LEVEL_FORBIDDEN_KEYS = {
    "id",
    "index",
}


@dataclass(frozen=True)
class CleanCheckResult:
    checked: bool
    forbidden_keys: tuple[str, ...]


def assert_clean_prediction_payload(payload: Mapping[str, object]) -> CleanCheckResult:
    """Reject fields that may leak benchmark answers, labels, or ids.

    The prediction pipeline may use question text, question time, raw dialogue,
    dialogue metadata, and locally built memory. It must not receive gold
    answers, judge results, benchmark labels, sample ids, or row indices.
    """

    violations: list[str] = []
    _collect_forbidden_keys(payload, path="$", violations=violations)
    if violations:
        keys = ", ".join(sorted(set(violations)))
        raise CleanProtocolViolation(
            f"Prediction payload contains clean-protocol forbidden fields: {keys}"
        )
    return CleanCheckResult(checked=True, forbidden_keys=())


def _collect_forbidden_keys(value: object, path: str, violations: list[str]) -> None:
    if isinstance(value, Mapping):
        for raw_key, child in value.items():
            key = str(raw_key)
            normalized = key.lower()
            child_path = f"{path}.{key}"
            if normalized in FORBIDDEN_PREDICTION_KEYS:
                violations.append(child_path)
            if path == "$" and normalized in TOP_LEVEL_FORBIDDEN_KEYS:
                violations.append(child_path)
            _collect_forbidden_keys(child, child_path, violations)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            _collect_forbidden_keys(child, f"{path}[{index}]", violations)
