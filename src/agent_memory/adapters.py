"""Dataset adapters that separate clean prediction inputs from labels."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass
from typing import Any


QUESTION_KEYS = ("question", "query", "question_text")
QUESTION_TIME_KEYS = ("question_time", "question_date", "query_time", "time")
ANSWER_KEYS = (
    "gold_answer",
    "gold_answers",
    "answer",
    "answers",
    "reference_answer",
    "reference_answers",
    "target",
    "targets",
)
TYPE_KEYS = ("question_type", "category", "type")
SESSION_KEYS = ("sessions", "haystack_sessions", "conversation", "conversations", "dialogue")
TURN_KEYS = ("turns", "messages", "conversation", "dialogue")
TEXT_KEYS = ("text", "content", "message", "utterance")
ROLE_KEYS = ("role", "speaker", "from")
TIME_KEYS = ("timestamp", "time", "date", "created_at")


@dataclass(frozen=True)
class PreparedRecord:
    prediction: dict[str, Any]
    label: dict[str, Any]


def prepare_records(
    rows: Iterable[Mapping[str, Any]],
    benchmark: str,
    subset: str,
) -> tuple[PreparedRecord, ...]:
    """Prepare clean prediction records and offline-only labels."""

    prepared: list[PreparedRecord] = []
    for row_number, row in enumerate(rows, start=1):
        if not _include_row(row, benchmark=benchmark, subset=subset):
            continue
        question = _required_first_text(row, QUESTION_KEYS, row_number)
        question_time = _first_text(row, QUESTION_TIME_KEYS)
        sessions = _extract_sessions(row, row_number)
        clean_core = {
            "question": question,
            "question_time": question_time,
            "sessions": sessions,
        }
        record_key = _stable_record_key(clean_core)
        prediction = {
            "record_key": record_key,
            "question": question,
            "sessions": sessions,
        }
        if question_time is not None:
            prediction["question_time"] = question_time

        label = {
            "record_key": record_key,
            "question": question,
            "gold_answer": _first_value(row, ANSWER_KEYS),
            "question_type": _first_value(row, ("question_type", "type")),
            "category": _first_value(row, ("category",)),
            "benchmark": benchmark,
            "subset": subset,
        }
        prepared.append(PreparedRecord(prediction=prediction, label=label))
    return tuple(prepared)


def read_json_or_jsonl(path: str) -> list[Mapping[str, Any]]:
    with open(path, "r", encoding="utf-8") as handle:
        text = handle.read().strip()
    if not text:
        return []
    if text[0] == "[":
        payload = json.loads(text)
        if not isinstance(payload, list):
            raise ValueError("JSON input must be a list of objects")
        return [_ensure_mapping(item) for item in payload]
    return [_ensure_mapping(json.loads(line)) for line in text.splitlines() if line.strip()]


def to_plain_records(records: Iterable[PreparedRecord]) -> list[dict[str, Any]]:
    return [asdict(record) for record in records]


def _include_row(row: Mapping[str, Any], benchmark: str, subset: str) -> bool:
    benchmark_key = benchmark.lower()
    subset_key = subset.lower()
    if benchmark_key == "locomo" and subset_key in {"non-adversarial", "non_adversarial"}:
        category = _first_value(row, ("category", "question_type", "type"))
        if category is None:
            return True
        category_text = str(category).strip().lower()
        return category_text not in {"5", "category 5", "adversarial", "adv"}
    return True


def _extract_sessions(row: Mapping[str, Any], row_number: int) -> list[dict[str, Any]]:
    raw_sessions = _first_value(row, SESSION_KEYS)
    if raw_sessions is None:
        raw_sessions = _first_value(row, TURN_KEYS)
    if raw_sessions is None:
        raise ValueError(f"Row {row_number}: no dialogue/session field found")

    if isinstance(raw_sessions, list) and raw_sessions and all(
        isinstance(item, Mapping) and _looks_like_turn(item) for item in raw_sessions
    ):
        return [_normalize_session({"turns": raw_sessions}, 0, row_number)]

    if isinstance(raw_sessions, list):
        sessions = []
        for session_index, raw_session in enumerate(raw_sessions):
            if isinstance(raw_session, Mapping):
                sessions.append(_normalize_session(raw_session, session_index, row_number))
            elif isinstance(raw_session, list):
                sessions.append(
                    _normalize_session({"turns": raw_session}, session_index, row_number)
                )
            else:
                raise ValueError(
                    f"Row {row_number}: session {session_index} must be object or list"
                )
        if not sessions:
            raise ValueError(f"Row {row_number}: no sessions found")
        return sessions

    if isinstance(raw_sessions, Mapping):
        return [_normalize_session(raw_sessions, 0, row_number)]

    raise ValueError(f"Row {row_number}: unsupported session container")


def _normalize_session(
    raw_session: Mapping[str, Any], session_index: int, row_number: int
) -> dict[str, Any]:
    raw_turns = _first_value(raw_session, TURN_KEYS)
    if raw_turns is None and _looks_like_turn(raw_session):
        raw_turns = [raw_session]
    if not isinstance(raw_turns, list):
        raise ValueError(f"Row {row_number}: session {session_index} has no turn list")

    session: dict[str, Any] = {
        "session_id": _first_text(raw_session, ("session_id", "session", "id"))
        or f"session_{session_index:04d}",
        "turns": [],
    }
    session_time = _first_text(raw_session, ("date", "timestamp", "time"))
    if session_time is not None:
        session["date"] = session_time

    for turn_index, raw_turn in enumerate(raw_turns):
        if not isinstance(raw_turn, Mapping):
            raise ValueError(
                f"Row {row_number}: session {session_index} turn {turn_index} must be object"
            )
        text = _required_first_text(raw_turn, TEXT_KEYS, row_number)
        turn: dict[str, Any] = {
            "role": _first_text(raw_turn, ROLE_KEYS) or "unknown",
            "text": text,
        }
        timestamp = _first_text(raw_turn, TIME_KEYS)
        if timestamp is not None:
            turn["timestamp"] = timestamp
        source_id = _first_text(raw_turn, ("source_id",))
        if source_id is not None:
            turn["source_id"] = source_id
        session["turns"].append(turn)
    return session


def _stable_record_key(clean_core: Mapping[str, Any]) -> str:
    encoded = json.dumps(clean_core, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:24]


def _looks_like_turn(value: Mapping[str, Any]) -> bool:
    return _first_value(value, TEXT_KEYS) is not None


def _required_first_text(
    row: Mapping[str, Any], keys: tuple[str, ...], row_number: int
) -> str:
    value = _first_text(row, keys)
    if value is None:
        raise ValueError(f"Row {row_number}: missing one of {keys}")
    return value


def _first_text(row: Mapping[str, Any], keys: tuple[str, ...]) -> str | None:
    value = _first_value(row, keys)
    if value is None:
        return None
    text = str(value).strip()
    return text if text else None


def _first_value(row: Mapping[str, Any], keys: tuple[str, ...]) -> Any:
    for key in keys:
        if key in row and row[key] is not None:
            return row[key]
    return None


def _ensure_mapping(value: Any) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError("Expected each dataset row to be a JSON object")
    return value
