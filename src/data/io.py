"""Prediction JSONL loading for the clean skeleton."""

from __future__ import annotations

import json
from collections.abc import Iterator, Mapping
from pathlib import Path
from typing import Any

from common.clean import assert_clean_prediction_payload
from common.schemas import PredictionEnvelope, PredictionRequest, Turn


def load_prediction_jsonl(path: str | Path) -> Iterator[PredictionEnvelope]:
    """Load clean prediction requests from JSONL.

    `record_key` is an optional runner-only alignment key. It is not passed to
    route, retrieval, compiler, or answer modules.
    """

    input_path = Path(path)
    with input_path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            payload = json.loads(stripped)
            if not isinstance(payload, Mapping):
                raise ValueError(f"Line {line_number}: expected a JSON object")

            record_key = payload.get("record_key")
            prediction_payload = {
                key: value for key, value in payload.items() if key != "record_key"
            }
            assert_clean_prediction_payload(prediction_payload)
            yield PredictionEnvelope(
                request=_build_prediction_request(prediction_payload, line_number),
                record_key=str(record_key) if record_key is not None else None,
            )


def _build_prediction_request(
    payload: Mapping[str, Any], line_number: int
) -> PredictionRequest:
    question = _required_text(payload, "question", line_number)
    question_time = _optional_text(payload.get("question_time"))
    turns = tuple(_iter_turns(payload, line_number))
    if not turns:
        raise ValueError(f"Line {line_number}: prediction request has no turns")
    return PredictionRequest(
        question=question,
        question_time=question_time,
        turns=turns,
        metadata={},
    )


def _iter_turns(payload: Mapping[str, Any], line_number: int) -> Iterator[Turn]:
    if "sessions" in payload:
        sessions = payload["sessions"]
        if not isinstance(sessions, list):
            raise ValueError(f"Line {line_number}: sessions must be a list")
        for session_position, session in enumerate(sessions):
            if not isinstance(session, Mapping):
                raise ValueError(
                    f"Line {line_number}: session {session_position} must be an object"
                )
            yield from _iter_session_turns(session, session_position, line_number)
        return

    if "turns" in payload or "messages" in payload:
        session = {
            "session_id": payload.get("session_id", "session_0000"),
            "date": payload.get("date"),
            "turns": payload.get("turns", payload.get("messages")),
        }
        yield from _iter_session_turns(session, 0, line_number)
        return

    raise ValueError(
        f"Line {line_number}: expected either sessions, turns, or messages"
    )


def _iter_session_turns(
    session: Mapping[str, Any], session_position: int, line_number: int
) -> Iterator[Turn]:
    raw_turns = session.get("turns", session.get("messages"))
    if not isinstance(raw_turns, list):
        raise ValueError(
            f"Line {line_number}: session {session_position} turns must be a list"
        )

    session_id = _optional_text(session.get("session_id")) or f"session_{session_position:04d}"
    session_date = _optional_text(session.get("date"))
    for turn_position, raw_turn in enumerate(raw_turns):
        if not isinstance(raw_turn, Mapping):
            raise ValueError(
                f"Line {line_number}: turn {turn_position} must be an object"
            )
        role = _optional_text(raw_turn.get("role")) or "unknown"
        text = _optional_text(raw_turn.get("text"))
        if text is None:
            text = _optional_text(raw_turn.get("content"))
        if text is None:
            raise ValueError(
                f"Line {line_number}: turn {turn_position} is missing text/content"
            )
        timestamp = _optional_text(raw_turn.get("timestamp"))
        if timestamp is None:
            timestamp = _optional_text(raw_turn.get("time"))
        if timestamp is None:
            timestamp = session_date
        source_id = _optional_text(raw_turn.get("source_id"))
        if source_id is None:
            source_id = f"{session_id}:turn_{turn_position:04d}"
        yield Turn(
            source_id=source_id,
            session_id=session_id,
            turn_index=turn_position,
            role=role,
            text=text,
            timestamp=timestamp,
            metadata={},
        )


def _required_text(payload: Mapping[str, Any], key: str, line_number: int) -> str:
    value = _optional_text(payload.get(key))
    if value is None:
        raise ValueError(f"Line {line_number}: missing required text field {key}")
    return value


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text if text else None
