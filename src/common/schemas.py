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
    diagnostics: dict[str, Any] = field(default_factory=dict)

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
    build_think_tokens: int = 0
    query_think_tokens: int = 0
    build_total_tokens: int | None = None
    query_total_tokens: int | None = None

    def __post_init__(self) -> None:
        if self.build_total_tokens is None:
            object.__setattr__(
                self,
                "build_total_tokens",
                self.build_tokens + self.build_think_tokens,
            )
        if self.query_total_tokens is None:
            object.__setattr__(
                self,
                "query_total_tokens",
                self.query_tokens + self.query_think_tokens,
            )

    def to_dict(self) -> dict[str, int]:
        return {
            "build_tokens": int(self.build_tokens),
            "query_tokens": int(self.query_tokens),
            "build_think_tokens": int(self.build_think_tokens),
            "query_think_tokens": int(self.query_think_tokens),
            "build_total_tokens": int(self.build_total_tokens or 0),
            "query_total_tokens": int(self.query_total_tokens or 0),
        }

    def __add__(self, other: "TokenUsage") -> "TokenUsage":
        return TokenUsage(
            build_tokens=self.build_tokens + other.build_tokens,
            query_tokens=self.query_tokens + other.query_tokens,
            build_think_tokens=self.build_think_tokens + other.build_think_tokens,
            query_think_tokens=self.query_think_tokens + other.query_think_tokens,
            build_total_tokens=int(self.build_total_tokens or 0)
            + int(other.build_total_tokens or 0),
            query_total_tokens=int(self.query_total_tokens or 0)
            + int(other.query_total_tokens or 0),
        )

    @classmethod
    def from_mapping(cls, value: Any) -> "TokenUsage":
        if not isinstance(value, dict):
            return cls()
        return cls(
            build_tokens=int(value.get("build_tokens") or 0),
            query_tokens=int(value.get("query_tokens") or 0),
            build_think_tokens=int(value.get("build_think_tokens") or 0),
            query_think_tokens=int(value.get("query_think_tokens") or 0),
            build_total_tokens=_optional_int(value.get("build_total_tokens")),
            query_total_tokens=_optional_int(value.get("query_total_tokens")),
        )


def llm_usage_to_token_usage(usage: Any, *, phase: str) -> TokenUsage:
    if phase not in {"build", "query"}:
        raise ValueError(f"Unsupported token usage phase: {phase}")
    if not isinstance(usage, dict):
        return TokenUsage()
    total_tokens = _usage_total_tokens(usage)
    think_tokens = min(_usage_think_tokens(usage), total_tokens)
    visible_tokens = max(0, total_tokens - think_tokens)
    if phase == "build":
        return TokenUsage(
            build_tokens=visible_tokens,
            build_think_tokens=think_tokens,
            build_total_tokens=total_tokens,
        )
    return TokenUsage(
        query_tokens=visible_tokens,
        query_think_tokens=think_tokens,
        query_total_tokens=total_tokens,
    )


def _usage_total_tokens(usage: dict[str, Any]) -> int:
    total = _optional_int(usage.get("total_tokens"))
    if total is not None:
        return total
    return int(usage.get("prompt_tokens") or 0) + int(usage.get("completion_tokens") or 0)


def _usage_think_tokens(usage: dict[str, Any]) -> int:
    direct = _optional_int(usage.get("reasoning_tokens"))
    if direct is not None:
        return direct
    for key in ("completion_tokens_details", "output_tokens_details"):
        details = usage.get(key)
        if isinstance(details, dict):
            nested = _optional_int(details.get("reasoning_tokens"))
            if nested is not None:
                return nested
    return 0


def _optional_int(value: Any) -> int | None:
    if value is None:
        return None
    return int(value)


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
