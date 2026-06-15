"""Immutable raw evidence store."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable

from common.schemas import Turn


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

    @property
    def average_turn_chars(self) -> float:
        if not self._turns:
            return 0.0
        return sum(len(turn.text) for turn in self._turns) / len(self._turns)

    def sessions(self) -> tuple[tuple[str, tuple[Turn, ...]], ...]:
        return tuple(self._session_turns.items())

    def session_turns(self, session_id: str) -> tuple[Turn, ...]:
        return self._session_turns.get(session_id, ())

    def get(self, source_id: str) -> Turn | None:
        return self._by_source_id.get(source_id)

    def expand_neighbors(
        self,
        source_ids: Iterable[str],
        window: int,
        order: str = "hit_priority",
    ) -> tuple[Turn, ...]:
        """Return hit turns plus same-session neighbors.

        `hit_priority` keeps each retrieved nucleus before its neighbors so the
        compiler cannot drop direct retrieval hits before lower-priority context.
        `chronological` preserves the earlier baseline for ablation.
        """

        if window < 0:
            raise ValueError("neighbor expansion window must be non-negative")
        if order not in {"hit_priority", "chronological"}:
            raise ValueError(f"Unsupported neighbor expansion order: {order}")

        selected: dict[str, Turn] = {}
        ordered_source_ids: list[str] = []
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
            if order == "hit_priority":
                candidates = (turn, *session_turns[start:position], *session_turns[position + 1 : end])
            else:
                candidates = session_turns[start:end]
            for neighbor in candidates:
                if neighbor.source_id in selected:
                    continue
                selected[neighbor.source_id] = neighbor
                ordered_source_ids.append(neighbor.source_id)

        if order == "hit_priority":
            return tuple(selected[source_id] for source_id in ordered_source_ids)

        return tuple(
            sorted(
                selected.values(),
                key=lambda item: (item.timestamp or "", item.session_id, item.turn_index),
            )
        )

    def manifest(self) -> dict[str, int | float]:
        return {
            "raw_turns": len(self._turns),
            "sessions": len(self._session_turns),
            "avg_turn_chars": self.average_turn_chars,
        }
