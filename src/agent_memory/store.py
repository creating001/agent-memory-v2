"""Immutable raw evidence store."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable

from agent_memory.schemas import Turn


class RawEvidenceStore:
    """Stores raw turns as the authoritative evidence layer."""

    def __init__(self, turns: Iterable[Turn]):
        self._turns = tuple(turns)
        source_ids = [turn.source_id for turn in self._turns]
        if len(source_ids) != len(set(source_ids)):
            raise ValueError("Raw evidence source_id values must be unique")
        self._by_source_id = {turn.source_id: turn for turn in self._turns}
        self._session_turns: dict[str, tuple[Turn, ...]] = {}
        grouped: dict[str, list[Turn]] = defaultdict(list)
        for turn in self._turns:
            grouped[turn.session_id].append(turn)
        for session_id, session_turns in grouped.items():
            self._session_turns[session_id] = tuple(
                sorted(session_turns, key=lambda item: item.turn_index)
            )

    @property
    def turns(self) -> tuple[Turn, ...]:
        return self._turns

    def get(self, source_id: str) -> Turn | None:
        return self._by_source_id.get(source_id)

    def expand_neighbors(self, source_ids: Iterable[str], window: int) -> tuple[Turn, ...]:
        """Return hit turns plus same-session neighbors in chronological order."""

        selected: dict[str, Turn] = {}
        for source_id in source_ids:
            turn = self.get(source_id)
            if turn is None:
                continue
            session_turns = self._session_turns.get(turn.session_id, ())
            positions = {
                candidate.source_id: position
                for position, candidate in enumerate(session_turns)
            }
            position = positions.get(turn.source_id)
            if position is None:
                continue
            start = max(0, position - window)
            end = min(len(session_turns), position + window + 1)
            for neighbor in session_turns[start:end]:
                selected[neighbor.source_id] = neighbor

        return tuple(
            sorted(
                selected.values(),
                key=lambda item: (item.timestamp or "", item.session_id, item.turn_index),
            )
        )

    def manifest(self) -> dict[str, int]:
        return {
            "raw_turns": len(self._turns),
            "sessions": len(self._session_turns),
        }
