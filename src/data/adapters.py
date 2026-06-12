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

    benchmark_key = benchmark.lower()
    if benchmark_key == "longmemeval":
        return tuple(_prepare_longmemeval_records(rows, benchmark, subset))
    if benchmark_key == "locomo":
        return tuple(_prepare_locomo_records(rows, benchmark, subset))

    prepared: list[PreparedRecord] = []
    seen_record_keys: dict[str, int] = {}
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
        record_key = _unique_record_key(clean_core, seen_record_keys)
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


def _prepare_longmemeval_records(
    rows: Iterable[Mapping[str, Any]],
    benchmark: str,
    subset: str,
) -> Iterable[PreparedRecord]:
    seen_record_keys: dict[str, int] = {}
    for row_number, row in enumerate(rows, start=1):
        question = _required_first_text(row, ("question",), row_number)
        question_time = _first_text(row, ("question_date", "question_time"))
        sessions = _extract_longmemeval_sessions(row, row_number)
        clean_core = {
            "question": question,
            "question_time": question_time,
            "sessions": sessions,
        }
        record_key = _unique_record_key(clean_core, seen_record_keys)
        prediction = {
            "record_key": record_key,
            "question": question,
            "sessions": sessions,
        }
        if question_time is not None:
            prediction["question_time"] = question_time

        yield PreparedRecord(
            prediction=prediction,
            label={
                "record_key": record_key,
                "question": question,
                "gold_answer": _first_value(row, ("answer",)),
                "question_type": _first_value(row, ("question_type",)),
                "category": None,
                "benchmark": benchmark,
                "subset": subset,
                "source_question_id": _first_value(row, ("question_id",)),
                "answer_session_ids": _first_value(row, ("answer_session_ids",)),
            },
        )


def _prepare_locomo_records(
    rows: Iterable[Mapping[str, Any]],
    benchmark: str,
    subset: str,
) -> Iterable[PreparedRecord]:
    seen_record_keys: dict[str, int] = {}
    for row_number, row in enumerate(rows, start=1):
        sessions = _extract_locomo_sessions(row, row_number)
        qa_items = _first_value(row, ("qa",))
        if not isinstance(qa_items, list):
            raise ValueError(f"Row {row_number}: LoCoMo row has no qa list")
        for qa_index, qa in enumerate(qa_items):
            if not isinstance(qa, Mapping):
                raise ValueError(f"Row {row_number}: qa {qa_index} must be an object")
            if not _include_row(qa, benchmark=benchmark, subset=subset):
                continue
            question = _required_first_text(qa, ("question",), row_number)
            clean_core = {
                "question": question,
                "question_time": None,
                "sessions": sessions,
            }
            record_key = _unique_record_key(clean_core, seen_record_keys)
            prediction = {
                "record_key": record_key,
                "question": question,
                "sessions": sessions,
            }
            yield PreparedRecord(
                prediction=prediction,
                label={
                    "record_key": record_key,
                    "question": question,
                    "gold_answer": _first_value(qa, ("answer",)),
                    "question_type": None,
                    "category": _first_value(qa, ("category",)),
                    "benchmark": benchmark,
                    "subset": subset,
                    "source_sample_id": _first_value(row, ("sample_id",)),
                    "evidence": _first_value(qa, ("evidence",)),
                },
            )


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


def _extract_longmemeval_sessions(
    row: Mapping[str, Any], row_number: int
) -> list[dict[str, Any]]:
    raw_sessions = _first_value(row, ("haystack_sessions",))
    if not isinstance(raw_sessions, list):
        raise ValueError(f"Row {row_number}: LongMemEval row has no haystack_sessions")
    session_ids = _first_value(row, ("haystack_session_ids",))
    dates = _first_value(row, ("haystack_dates",))
    if session_ids is not None and not isinstance(session_ids, list):
        raise ValueError(f"Row {row_number}: haystack_session_ids must be a list")
    if dates is not None and not isinstance(dates, list):
        raise ValueError(f"Row {row_number}: haystack_dates must be a list")

    sessions: list[dict[str, Any]] = []
    seen_session_ids: dict[str, int] = {}
    for session_index, raw_session in enumerate(raw_sessions):
        if not isinstance(raw_session, list):
            raise ValueError(
                f"Row {row_number}: haystack session {session_index} must be a turn list"
            )
        raw_session_id = (
            str(session_ids[session_index])
            if isinstance(session_ids, list) and session_index < len(session_ids)
            else f"session_{session_index:04d}"
        )
        occurrence = seen_session_ids.get(raw_session_id, 0)
        seen_session_ids[raw_session_id] = occurrence + 1
        session_id = (
            raw_session_id
            if occurrence == 0
            else f"{raw_session_id}:occ_{occurrence:04d}"
        )
        session: dict[str, Any] = {
            "session_id": session_id,
            "turns": [],
        }
        if isinstance(dates, list) and session_index < len(dates):
            session["date"] = str(dates[session_index])
        for turn_index, raw_turn in enumerate(raw_session):
            if not isinstance(raw_turn, Mapping):
                raise ValueError(
                    f"Row {row_number}: haystack session {session_index} turn {turn_index} must be object"
                )
            text = _first_text(raw_turn, TEXT_KEYS)
            if text is None:
                continue
            turn = {
                "source_id": f"{session_id}:turn_{turn_index:04d}",
                "role": _first_text(raw_turn, ROLE_KEYS) or "unknown",
                "text": text,
            }
            session["turns"].append(turn)
        sessions.append(session)
    return sessions


def _extract_locomo_sessions(
    row: Mapping[str, Any], row_number: int
) -> list[dict[str, Any]]:
    conversation = _first_value(row, ("conversation",))
    if not isinstance(conversation, Mapping):
        raise ValueError(f"Row {row_number}: LoCoMo row has no conversation object")
    session_names = sorted(
        (
            key
            for key, value in conversation.items()
            if key.startswith("session_")
            and key.count("_") == 1
            and isinstance(value, list)
        ),
        key=lambda item: int(item.split("_")[1]),
    )
    sessions = []
    for session_name in session_names:
        raw_turns = conversation[session_name]
        session: dict[str, Any] = {
            "session_id": session_name,
            "turns": [],
        }
        session_time = _first_text(conversation, (f"{session_name}_date_time",))
        if session_time is not None:
            session["date"] = session_time
        for turn_index, raw_turn in enumerate(raw_turns):
            if not isinstance(raw_turn, Mapping):
                raise ValueError(
                    f"Row {row_number}: {session_name} turn {turn_index} must be object"
                )
            source_id = _first_text(raw_turn, ("dia_id", "source_id"))
            if source_id is None:
                source_id = f"{session_name}:turn_{turn_index:04d}"
            session["turns"].append(
                {
                    "source_id": source_id,
                    "role": _first_text(raw_turn, ("speaker", "role")) or "unknown",
                    "text": _required_first_text(raw_turn, TEXT_KEYS, row_number),
                }
            )
        sessions.append(session)
    if not sessions:
        raise ValueError(f"Row {row_number}: LoCoMo conversation has no sessions")
    return sessions


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


def _unique_record_key(
    clean_core: Mapping[str, Any], seen_record_keys: dict[str, int]
) -> str:
    """Create a unique runner-only key without exposing benchmark ids."""

    base_key = _stable_record_key(clean_core)
    occurrence = seen_record_keys.get(base_key, 0)
    seen_record_keys[base_key] = occurrence + 1
    if occurrence == 0:
        return base_key
    return _stable_record_key({"base_record_key": base_key, "occurrence": occurrence})


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
