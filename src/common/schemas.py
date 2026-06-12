"""Core data structures for the clean Agent-Memory skeleton."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class Turn:
    source_id: str
    session_id: str
    turn_index: int
    role: str
    text: str
    timestamp: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PredictionRequest:
    question: str
    turns: tuple[Turn, ...]
    question_time: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PredictionEnvelope:
    request: PredictionRequest
    record_key: str | None = None


@dataclass(frozen=True)
class RouteResult:
    information_need: str
    signals: tuple[str, ...]
    retrieval_multiplier: int = 1

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RetrievalHit:
    source_id: str
    score: float
    rank: int
    retriever: str
    matched_terms: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class EvidenceRow:
    source_id: str
    session_id: str
    turn_index: int
    role: str
    text: str
    timestamp: str | None
    retrieval_rank: int | None
    retrieval_score: float | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CompiledContext:
    question: str
    question_time: str | None
    route: RouteResult
    evidence_rows: tuple[EvidenceRow, ...]
    prompt: str
    context_chars: int
    memory_records: tuple[Any, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["route"] = self.route.to_dict()
        result["evidence_rows"] = [row.to_dict() for row in self.evidence_rows]
        result["memory_records"] = [
            record.to_dict() if hasattr(record, "to_dict") else record
            for record in self.memory_records
        ]
        return result


@dataclass(frozen=True)
class TokenUsage:
    build_tokens: int = 0
    query_tokens: int = 0

    def to_dict(self) -> dict[str, int]:
        return asdict(self)


@dataclass(frozen=True)
class AnswerResult:
    answer: str
    model: str
    token_usage: TokenUsage
    raw_response: str | None = None

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["token_usage"] = self.token_usage.to_dict()
        return result
