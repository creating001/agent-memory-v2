"""Offline diagnostics for retrieval and evidence use."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping
from typing import Any


def evidence_recall(
    traces: Iterable[Mapping[str, Any]],
    labels: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    label_by_key = {str(label.get("record_key")): label for label in labels}
    rows = []
    by_group: dict[str, list[bool]] = defaultdict(list)

    for trace_record in traces:
        record_key = str(trace_record.get("record_key"))
        label = label_by_key.get(record_key)
        if label is None:
            continue
        evidence_ids = _evidence_ids(label)
        if not evidence_ids:
            continue
        source_ids = _compiled_source_ids(trace_record)
        hit = _has_evidence_hit(source_ids, evidence_ids)
        rows.append(hit)
        by_group[_group_name(label)].append(hit)

    return {
        "n_with_evidence_labels": len(rows),
        "evidence_recall": _rate(rows),
        "by_type": {
            group: {"n": len(values), "evidence_recall": _rate(values)}
            for group, values in sorted(by_group.items())
        },
        "diagnostic_note": (
            "Offline-only retrieval diagnostic. Evidence labels must not feed "
            "prediction, route, retrieval, compiler, answer, or verifier modules."
        ),
    }


def _compiled_source_ids(trace_record: Mapping[str, Any]) -> list[str]:
    trace = trace_record.get("trace")
    if not isinstance(trace, Mapping):
        return []
    compiled_context = trace.get("compiled_context")
    if not isinstance(compiled_context, Mapping):
        return []
    evidence_rows = compiled_context.get("evidence_rows")
    if not isinstance(evidence_rows, list):
        return []
    source_ids = []
    for row in evidence_rows:
        if isinstance(row, Mapping) and row.get("source_id") is not None:
            source_ids.append(str(row["source_id"]))
    return source_ids


def _evidence_ids(label: Mapping[str, Any]) -> list[str]:
    locomo_evidence = label.get("evidence")
    if isinstance(locomo_evidence, list):
        return [str(item) for item in locomo_evidence if item is not None]
    longmemeval_sessions = label.get("answer_session_ids")
    if isinstance(longmemeval_sessions, list):
        return [str(item) for item in longmemeval_sessions if item is not None]
    return []


def _has_evidence_hit(source_ids: list[str], evidence_ids: list[str]) -> bool:
    for source_id in source_ids:
        session_id = source_id.split(":turn_", 1)[0]
        for evidence_id in evidence_ids:
            if (
                source_id == evidence_id
                or session_id == evidence_id
                or source_id.startswith(evidence_id + ":")
            ):
                return True
    return False


def _group_name(label: Mapping[str, Any]) -> str:
    group = label.get("question_type") or label.get("category") or "unknown"
    return str(group)


def _rate(values: list[bool]) -> float | None:
    if not values:
        return None
    return sum(1 for value in values if value) / len(values)
