"""Build-stage LLM memory construction and management."""

from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
import urllib.error
import urllib.request
from collections import defaultdict
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any

from common.schemas import TokenUsage, Turn, llm_usage_to_token_usage


_MEMORY_TYPES = {
    "event",
    "fact",
    "preference",
    "profile",
    "state",
    "relationship",
    "plan",
    "unknown",
}
_STATEFUL_MEMORY_TYPES = frozenset({"preference", "profile", "relationship", "state"})
_DEFAULT_MANAGED_MEMORY_TYPES = frozenset((*_STATEFUL_MEMORY_TYPES, "fact"))
_MANAGEMENT_POLICIES = {
    "none": frozenset(),
    "stateful_only": _STATEFUL_MEMORY_TYPES,
    "stateful_plus_facts": _DEFAULT_MANAGED_MEMORY_TYPES,
}
_MEMORY_SCALAR_VALUE_PATTERN = re.compile(
    r"(?<![\w.:\-/])(?:\$\s*)?\d+(?:,\d{3})*(?:\.\d+)?"
    r"(?:\s?(?:k|m|b|%))?"
    r"(?:\s+[A-Za-z][A-Za-z%/-]{1,24}){0,2}(?![\w.:\-/])",
    flags=re.IGNORECASE,
)
_MEMORY_SCALAR_UNIT_STOPWORDS = frozenset(
    {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "been",
        "but",
        "by",
        "for",
        "from",
        "has",
        "have",
        "i",
        "in",
        "is",
        "it",
        "my",
        "of",
        "on",
        "or",
        "our",
        "that",
        "the",
        "their",
        "there",
        "this",
        "to",
        "was",
        "were",
        "with",
    }
)


@dataclass(frozen=True)
class MemoryRecord:
    """A managed build-stage memory item with raw source back-pointers."""

    memory_id: str
    memory_type: str
    text: str
    source_ids: tuple[str, ...]
    subject: str = ""
    predicate: str = ""
    value: str = ""
    timestamp: str | None = None
    mention_time: str | None = None
    event_time: str | None = None
    valid_from: str | None = None
    valid_to: str | None = None
    entities: tuple[str, ...] = ()
    confidence: float = 1.0
    status: str = "active"
    superseded_by: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @property
    def search_text(self) -> str:
        return " ".join(
            part
            for part in (
                self.memory_type,
                self.subject,
                self.predicate,
                self.value,
                self.mention_time or "",
                self.event_time or "",
                self.valid_from or "",
                self.valid_to or "",
                " ".join(self.entities),
                self.text,
            )
            if part
        )


@dataclass(frozen=True)
class BuildMemoryCacheStats:
    hits: int = 0
    misses: int = 0
    writes: int = 0

    def to_dict(self) -> dict[str, int]:
        return {
            "hits": self.hits,
            "misses": self.misses,
            "writes": self.writes,
        }


@dataclass(frozen=True)
class BuiltMemory:
    records: tuple[MemoryRecord, ...]
    token_usage: TokenUsage
    cache_stats: BuildMemoryCacheStats = BuildMemoryCacheStats()
    chunks: int = 0
    cache_enabled: bool = False
    builder: str = "null"
    management_policy: str = "none"
    managed_memory_types: tuple[str, ...] = ()
    management: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "records": [record.to_dict() for record in self.records],
            "token_usage": self.token_usage.to_dict(),
            "cache": self.cache_stats.to_dict(),
            "chunks": self.chunks,
            "cache_enabled": self.cache_enabled,
            "builder": self.builder,
            "management_policy": self.management_policy,
            "managed_memory_types": list(self.managed_memory_types),
            "management": dict(self.management or {}),
        }


class NullMemoryBuilder:
    """Build-stage no-op used for smoke tests and ablations."""

    def build(self, turns: tuple[Turn, ...]) -> BuiltMemory:
        del turns
        return BuiltMemory(records=(), token_usage=TokenUsage(), builder="null")


class OpenAICompatibleMemoryBuilder:
    """LLM-based build-stage typed memory extractor.

    The builder is question-independent: it receives only raw dialogue turns and
    metadata available before prediction. It creates typed memory records that
    can be searched at query time while retaining raw source back-pointers.
    """

    def __init__(
        self,
        base_url: str,
        model: str,
        temperature: float,
        max_tokens: int,
        timeout: float,
        max_turns_per_chunk: int,
        max_chars_per_turn: int,
        max_records_per_chunk: int,
        overlap_turns: int = 0,
        cache_path: str | None = None,
        cache_namespace: str | None = None,
        api_key_env: str | None = None,
        temporal_fields: bool = False,
        prompt_profile: str = "typed_compact",
        manage_facts: bool = True,
        management_policy: str | None = None,
        operation_ledger: bool = False,
        memory_system_graph: bool = False,
        chat_template_kwargs: dict[str, Any] | None = None,
    ):
        if prompt_profile not in {"typed_compact", "lossless_atomic"}:
            raise ValueError(f"Unsupported build_memory.prompt_profile: {prompt_profile}")
        if management_policy is None:
            management_policy = "stateful_plus_facts" if manage_facts else "stateful_only"
        if management_policy not in _MANAGEMENT_POLICIES:
            raise ValueError(
                "Unsupported build_memory.management_policy: "
                f"{management_policy}"
            )
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._timeout = timeout
        self._max_turns_per_chunk = max(1, max_turns_per_chunk)
        self._max_chars_per_turn = max(80, max_chars_per_turn)
        self._max_records_per_chunk = max(1, max_records_per_chunk)
        self._overlap_turns = max(
            0,
            min(overlap_turns, self._max_turns_per_chunk - 1),
        )
        self._cache_path = Path(cache_path).expanduser() if cache_path else None
        self._cache_namespace = cache_namespace or model
        self._api_key_env = api_key_env
        self._temporal_fields = temporal_fields
        self._prompt_profile = prompt_profile
        self._manage_facts = manage_facts
        self._management_policy = management_policy
        self._operation_ledger = operation_ledger
        self._memory_system_graph = memory_system_graph
        self._chat_template_kwargs = dict(chat_template_kwargs or {})
        self._connection: sqlite3.Connection | None = None
        self._cache_stats = BuildMemoryCacheStats()

    def build(self, turns: tuple[Turn, ...]) -> BuiltMemory:
        cache_stats_before = self._cache_stats
        if not turns:
            return BuiltMemory(
                records=(),
                token_usage=TokenUsage(),
                cache_stats=BuildMemoryCacheStats(),
                chunks=0,
                cache_enabled=self._cache_path is not None,
                builder=self._model,
                management_policy=self._management_policy,
                managed_memory_types=tuple(
                    sorted(_MANAGEMENT_POLICIES[self._management_policy])
                ),
                management=_management_summary(
                    (),
                    policy=self._management_policy,
                    managed_memory_types=_MANAGEMENT_POLICIES[
                        self._management_policy
                    ],
                    include_operation_ledger=self._operation_ledger,
                    include_memory_system_graph=self._memory_system_graph,
                ),
            )

        all_records: list[MemoryRecord] = []
        token_usage = TokenUsage()
        chunks = _chunk_turns(
            turns,
            self._max_turns_per_chunk,
            overlap_turns=self._overlap_turns,
        )
        valid_source_ids = {turn.source_id for turn in turns}
        timestamp_by_source_id = {turn.source_id: turn.timestamp for turn in turns}

        for chunk_index, chunk in enumerate(chunks):
            prompt = self._build_prompt(chunk)
            cache_key = _cache_key(
                self._cache_namespace,
                self._model,
                self._max_tokens,
                self._max_records_per_chunk,
                prompt,
            )
            payload = self._get(cache_key)
            if payload is None:
                response = self._chat_completion(prompt)
                message = response["choices"][0]["message"]
                content = _message_text(message).strip()
                usage = response.get("usage") or {}
                payload = {
                    "content": content,
                    "usage": usage,
                }
                self._put(cache_key, payload)
            token_usage += llm_usage_to_token_usage(payload.get("usage"), phase="build")

            raw_records = _bounded_records(
                _records_from_payload(payload.get("content", "")),
                self._max_records_per_chunk,
            )
            for ordinal, raw_record in enumerate(raw_records):
                record = _normalize_record(
                    raw_record=raw_record,
                    chunk_index=chunk_index,
                    ordinal=ordinal,
                    valid_source_ids=valid_source_ids,
                    timestamp_by_source_id=timestamp_by_source_id,
                    temporal_fields=self._temporal_fields,
                )
                if record is not None:
                    all_records.append(record)

        managed_memory_types = (
            _MANAGEMENT_POLICIES[self._management_policy]
            if self._management_policy is not None
            else (
                _STATEFUL_MEMORY_TYPES
                if self._temporal_fields
                else (
                    _DEFAULT_MANAGED_MEMORY_TYPES
                    if self._manage_facts
                    else _STATEFUL_MEMORY_TYPES
                )
            )
        )
        managed, operation_trace = _manage_records_with_trace(
            tuple(all_records),
            managed_memory_types=managed_memory_types,
        )
        return BuiltMemory(
            records=managed,
            token_usage=token_usage,
            cache_stats=_cache_stats_delta(cache_stats_before, self._cache_stats),
            chunks=len(chunks),
            cache_enabled=self._cache_path is not None,
            builder=self._model,
            management_policy=self._management_policy,
            managed_memory_types=tuple(sorted(managed_memory_types)),
            management=_management_summary(
                managed,
                policy=self._management_policy,
                managed_memory_types=managed_memory_types,
                raw_records=tuple(all_records),
                deduped_records=operation_trace["deduped_records"],
                merge_groups=operation_trace["merge_groups"],
                supersede_pairs=operation_trace["supersede_pairs"],
                include_operation_ledger=self._operation_ledger,
                include_memory_system_graph=self._memory_system_graph,
            ),
        )

    def _build_prompt(self, turns: tuple[Turn, ...]) -> str:
        if self._prompt_profile == "lossless_atomic":
            return self._build_lossless_atomic_prompt(turns)

        lines = [
            "Build a compact typed memory view from the dialogue turns.",
            "Use only the provided turns. Do not invent facts.",
            "Do not use any question, gold answer, judge output, benchmark label, sample id, qid, or row index.",
            "Create memory records that help a future agent answer long-term memory questions.",
            "Prefer durable, interaction-specific memories: concrete events, facts, preferences, profile attributes, current states, relationships, plans, and specific outcomes of the interaction.",
            "Avoid generic background knowledge, generic how-to steps, and boilerplate advice unless they are the concrete answer or recommendation produced in the interaction.",
            "When a turn contains multiple independent memory-worthy facts, create separate atomic records instead of merging them into one broad summary.",
            "Put salient names, entities, values, times, and quantities in entities/value when present.",
            "Each record must include source_ids copied exactly from the turns that support it.",
            *_temporal_field_prompt_lines(self._temporal_fields),
            f"Return at most {self._max_records_per_chunk} records.",
            "",
            "Dialogue turns:",
        ]
        for turn in turns:
            prefix = " | ".join(
                part
                for part in (
                    f"source_id={turn.source_id}",
                    f"session={turn.session_id}",
                    f"time={turn.timestamp}" if turn.timestamp else "",
                    f"role={turn.role}",
                )
                if part
            )
            text = _truncate(turn.text, self._max_chars_per_turn)
            lines.append(f"- {prefix}: {text}")
        return "\n".join(lines)

    def _build_lossless_atomic_prompt(self, turns: tuple[Turn, ...]) -> str:
        lines = [
            "Build a lossless atomic typed memory index from the dialogue turns.",
            "Use only the provided turns. Do not invent facts.",
            "Do not use any question, gold answer, judge output, benchmark label, sample id, qid, or row index.",
            "The output is an index for future retrieval, not a final answer.",
            "Create enough self-contained atomic records to preserve all user-specific and assistant-provided information that a future agent may need.",
            "Do not drop low-salience details: exact names, titles, brands, models, places, dates, durations, counts, quantities, prices, colors, relationship names, stores, organizations, and negations.",
            "Each record must be understandable without surrounding turns: replace pronouns such as it, they, he, she, this, and that with the concrete entity when the turn makes it clear.",
            "When a turn contains multiple independent facts, purchases, visits, tasks, preferences, options, list items, or numeric operands, split them into separate records.",
            "Separate stable profile/preference/state memories from one-time events, ordinary facts, assistant suggestions, and future plans.",
            "Keep assistant-provided factual answers or recommendations when they answer the user or establish a remembered item; mark them with the assistant turn source_id.",
            "If a relative time phrase is resolvable from the turn timestamp, write the resolved date or date span in the record text, value, timestamp, or event_time fields while preserving the original phrase when useful.",
            "Each record must include source_ids copied exactly from the turns that directly support it.",
            *_temporal_field_prompt_lines(self._temporal_fields),
            f"Return at most {self._max_records_per_chunk} records.",
            "",
            "Dialogue turns:",
        ]
        for turn in turns:
            prefix = " | ".join(
                part
                for part in (
                    f"source_id={turn.source_id}",
                    f"session={turn.session_id}",
                    f"time={turn.timestamp}" if turn.timestamp else "",
                    f"role={turn.role}",
                )
                if part
            )
            text = _truncate(turn.text, self._max_chars_per_turn)
            lines.append(f"- {prefix}: {text}")
        return "\n".join(lines)

    def _chat_completion(self, prompt: str) -> dict[str, Any]:
        endpoint = self._base_url + "/chat/completions"
        payload: dict[str, Any] = {
            "model": self._model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self._temperature,
            "max_tokens": self._max_tokens,
        }
        if self._chat_template_kwargs:
            payload["chat_template_kwargs"] = self._chat_template_kwargs
        request_body = json.dumps(payload).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if self._api_key_env:
            api_key = os.environ.get(self._api_key_env)
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
        request = urllib.request.Request(
            endpoint,
            data=request_body,
            headers=headers,
            method="POST",
        )
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        try:
            with opener.open(request, timeout=self._timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            body = error.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Memory build request failed: {error.code} {body}") from error

    def _get(self, key: str) -> dict[str, Any] | None:
        if self._cache_path is None:
            self._cache_stats = replace(
                self._cache_stats, misses=self._cache_stats.misses + 1
            )
            return None
        row = self._connect().execute(
            "SELECT payload_json FROM build_memory WHERE cache_key = ?",
            (key,),
        ).fetchone()
        if row is None:
            self._cache_stats = replace(
                self._cache_stats, misses=self._cache_stats.misses + 1
            )
            return None
        self._cache_stats = replace(self._cache_stats, hits=self._cache_stats.hits + 1)
        return json.loads(str(row[0]))

    def _put(self, key: str, payload: dict[str, Any]) -> None:
        if self._cache_path is None:
            return
        self._connect().execute(
            "INSERT OR REPLACE INTO build_memory(cache_key, payload_json) VALUES(?, ?)",
            (key, json.dumps(payload, ensure_ascii=False, sort_keys=True)),
        )
        self._connect().commit()
        self._cache_stats = replace(self._cache_stats, writes=self._cache_stats.writes + 1)

    def _connect(self) -> sqlite3.Connection:
        if self._connection is None:
            if self._cache_path is None:
                raise RuntimeError("cache is disabled")
            self._cache_path.parent.mkdir(parents=True, exist_ok=True)
            self._connection = sqlite3.connect(str(self._cache_path), timeout=30.0)
            self._connection.execute("PRAGMA busy_timeout = 30000")
            self._connection.execute("PRAGMA journal_mode = WAL")
            self._connection.execute(
                "CREATE TABLE IF NOT EXISTS build_memory("
                "cache_key TEXT PRIMARY KEY, "
                "payload_json TEXT NOT NULL)"
            )
            self._connection.commit()
        return self._connection


def _chunk_turns(
    turns: tuple[Turn, ...],
    max_turns_per_chunk: int,
    *,
    overlap_turns: int = 0,
) -> tuple[tuple[Turn, ...], ...]:
    chunks = []
    step = max(1, max_turns_per_chunk - max(0, overlap_turns))
    for start in range(0, len(turns), step):
        chunks.append(turns[start : start + max_turns_per_chunk])
        if start + max_turns_per_chunk >= len(turns):
            break
    return tuple(chunks)


def _records_from_payload(content: str) -> list[dict[str, Any]]:
    payload = _parse_json_object(content)
    if not isinstance(payload, dict):
        return _parse_partial_records_array(content)
    records = payload.get("records")
    if not isinstance(records, list):
        return _parse_partial_records_array(content)
    return [record for record in records if isinstance(record, dict)]


def _bounded_records(
    raw_records: list[dict[str, Any]],
    max_records: int,
) -> list[dict[str, Any]]:
    return raw_records[: max(0, max_records)]


def _parse_json_object(content: str) -> Any:
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    start = content.find("{")
    end = content.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        return json.loads(content[start : end + 1])
    except json.JSONDecodeError:
        return None


def _parse_partial_records_array(content: str) -> list[dict[str, Any]]:
    """Recover complete records from a JSON response truncated inside records[]."""

    marker = '"records"'
    marker_position = content.find(marker)
    if marker_position < 0:
        return []
    array_start = content.find("[", marker_position + len(marker))
    if array_start < 0:
        return []

    decoder = json.JSONDecoder()
    position = array_start + 1
    records: list[dict[str, Any]] = []
    while position < len(content):
        while position < len(content) and content[position] in " \n\r\t,":
            position += 1
        if position >= len(content) or content[position] == "]":
            break
        if content[position] != "{":
            break
        try:
            record, end = decoder.raw_decode(content, position)
        except json.JSONDecodeError:
            break
        if isinstance(record, dict):
            records.append(record)
        position = end
    return records


def _normalize_record(
    raw_record: dict[str, Any],
    chunk_index: int,
    ordinal: int,
    valid_source_ids: set[str],
    timestamp_by_source_id: dict[str, str | None],
    temporal_fields: bool = False,
) -> MemoryRecord | None:
    source_ids = _tuple_of_strings(raw_record.get("source_ids"))
    source_ids = tuple(source_id for source_id in source_ids if source_id in valid_source_ids)
    if not source_ids:
        return None

    text = _clean_text(raw_record.get("text"))
    subject = _clean_text(raw_record.get("subject"))
    predicate = _clean_text(raw_record.get("predicate"))
    value = _clean_text(raw_record.get("value"))
    if not text:
        text = " ".join(part for part in (subject, predicate, value) if part)
    if not text:
        return None

    memory_type = str(raw_record.get("type") or raw_record.get("memory_type") or "unknown")
    memory_type = memory_type.strip().lower().replace("-", "_")
    if memory_type not in _MEMORY_TYPES:
        memory_type = "unknown"
    timestamp = _clean_text(raw_record.get("timestamp")) or _first_timestamp(
        source_ids, timestamp_by_source_id
    )
    mention_time = _clean_text(raw_record.get("mention_time")) or _first_timestamp(
        source_ids, timestamp_by_source_id
    )
    event_time = _clean_text(raw_record.get("event_time")) or None
    raw_valid_from = _clean_text(raw_record.get("valid_from"))
    raw_valid_to = _clean_text(raw_record.get("valid_to"))
    if temporal_fields:
        if memory_type in {"profile", "preference", "relationship", "state"}:
            valid_from = raw_valid_from or event_time or timestamp
            valid_to = raw_valid_to or None
        else:
            valid_from = ""
            valid_to = None
    else:
        valid_from = raw_valid_from or timestamp
        valid_to = raw_valid_to or None
    entities = _tuple_of_strings(raw_record.get("entities"))
    confidence = _safe_float(raw_record.get("confidence"), default=1.0)
    confidence = min(1.0, max(0.0, confidence))
    memory_id = _memory_id(
        memory_type=memory_type,
        text=text,
        source_ids=source_ids,
        chunk_index=chunk_index,
        ordinal=ordinal,
    )
    return MemoryRecord(
        memory_id=memory_id,
        memory_type=memory_type,
        text=text,
        source_ids=source_ids,
        subject=subject,
        predicate=predicate,
        value=value,
        timestamp=timestamp or None,
        mention_time=mention_time or None,
        event_time=event_time,
        valid_from=valid_from or None,
        valid_to=valid_to,
        entities=entities,
        confidence=confidence,
    )


def _manage_records(
    records: tuple[MemoryRecord, ...],
    managed_memory_types: frozenset[str] = _DEFAULT_MANAGED_MEMORY_TYPES,
) -> tuple[MemoryRecord, ...]:
    managed, _trace = _manage_records_with_trace(
        records,
        managed_memory_types=managed_memory_types,
    )
    return managed


def _manage_records_with_trace(
    records: tuple[MemoryRecord, ...],
    managed_memory_types: frozenset[str] = _DEFAULT_MANAGED_MEMORY_TYPES,
) -> tuple[tuple[MemoryRecord, ...], dict[str, Any]]:
    deduped: dict[tuple[str, str, tuple[str, ...]], MemoryRecord] = {}
    duplicate_groups: dict[
        tuple[str, str, tuple[str, ...]], list[MemoryRecord]
    ] = defaultdict(list)
    for record in records:
        key = (
            record.memory_type,
            _normalize_key_text(
                " ".join(
                    part
                    for part in (
                        record.subject,
                        record.predicate,
                        record.value,
                        record.text,
                    )
                    if part
                )
            ),
            record.source_ids,
        )
        duplicate_groups[key].append(record)
        existing = deduped.get(key)
        if existing is None or record.confidence > existing.confidence:
            deduped[key] = record

    deduped_records = tuple(deduped.values())
    merge_groups = []
    for key, group in duplicate_groups.items():
        if len(group) <= 1:
            continue
        kept = deduped[key]
        merged = tuple(record for record in group if record.memory_id != kept.memory_id)
        merge_groups.append({"kept": kept, "merged": merged})

    managed = list(deduped_records)
    grouped: dict[tuple[str, str, str], list[MemoryRecord]] = defaultdict(list)
    for record in managed:
        if record.memory_type not in managed_memory_types:
            continue
        if not record.subject or not record.predicate:
            continue
        grouped[
            (
                record.memory_type,
                _normalize_key_text(record.subject),
                _normalize_key_text(record.predicate),
            )
        ].append(record)

    superseded: dict[str, str] = {}
    supersede_pairs: list[dict[str, Any]] = []
    for group in grouped.values():
        distinct_values = {
            _normalize_key_text(record.value or record.text) for record in group
        }
        if len(group) <= 1 or len(distinct_values) <= 1:
            continue
        newest = max(group, key=lambda record: (record.timestamp or "", record.memory_id))
        for record in group:
            if record.memory_id != newest.memory_id:
                superseded[record.memory_id] = newest.memory_id
                supersede_pairs.append({"old": record, "new": newest})

    managed_by_id = {record.memory_id: record for record in managed}
    result = []
    for record in managed:
        if record.memory_id in superseded:
            superseding_record = managed_by_id.get(superseded[record.memory_id])
            valid_to = (
                superseding_record.valid_from or superseding_record.timestamp
                if superseding_record is not None
                else record.valid_to
            )
            result.append(
                replace(
                    record,
                    status="superseded",
                    superseded_by=superseded[record.memory_id],
                    valid_to=valid_to,
                )
            )
        else:
            result.append(record)
    result.sort(
        key=lambda record: (
            0 if record.status == "active" else 1,
            record.memory_type,
            record.timestamp or "",
            record.memory_id,
        )
    )
    operation_trace = {
        "deduped_records": deduped_records,
        "merge_groups": tuple(merge_groups),
        "supersede_pairs": tuple(supersede_pairs),
    }
    return tuple(result), operation_trace


def _management_summary(
    records: tuple[MemoryRecord, ...],
    *,
    policy: str,
    managed_memory_types: frozenset[str],
    raw_records: tuple[MemoryRecord, ...] | None = None,
    deduped_records: tuple[MemoryRecord, ...] | None = None,
    merge_groups: tuple[dict[str, Any], ...] = (),
    supersede_pairs: tuple[dict[str, Any], ...] = (),
    include_operation_ledger: bool = False,
    include_memory_system_graph: bool = False,
) -> dict[str, Any]:
    """Summarize build-time memory operations for trace/audit.

    The summary is generated after normalization and lifecycle management. It is
    a diagnostic view only; retrieval and answering continue to use the managed
    records themselves.
    """

    status_counts: dict[str, int] = defaultdict(int)
    type_counts: dict[str, int] = defaultdict(int)
    layer_counts: dict[str, int] = defaultdict(int)
    for record in records:
        status_counts[record.status] += 1
        type_counts[record.memory_type] += 1
        layer_counts[_memory_layer(record.memory_type)] += 1

    groups: dict[tuple[str, str, str], list[MemoryRecord]] = defaultdict(list)
    for record in records:
        if not record.subject or not record.predicate:
            continue
        groups[
            (
                record.memory_type,
                _normalize_key_text(record.subject),
                _normalize_key_text(record.predicate),
            )
        ].append(record)

    managed_lifecycle_slots = 0
    nonmanaged_multi_value_slots = 0
    for (memory_type, _subject, _predicate), group in groups.items():
        values = {
            _normalize_key_text(record.value or record.text)
            for record in group
            if record.value or record.text
        }
        statuses = {record.status for record in group}
        has_lifecycle = "superseded" in statuses or len(values) > 1
        if not has_lifecycle:
            continue
        if memory_type in managed_memory_types:
            managed_lifecycle_slots += 1
        else:
            nonmanaged_multi_value_slots += 1

    object_graph = _memory_object_graph_summary(
        groups,
        managed_memory_types=managed_memory_types,
    )
    summary = {
        "policy": policy,
        "managed_memory_types": sorted(managed_memory_types),
        "total_records": len(records),
        "active_records": status_counts.get("active", 0),
        "superseded_records": status_counts.get("superseded", 0),
        "status_counts": dict(sorted(status_counts.items())),
        "type_counts": dict(sorted(type_counts.items())),
        "layer_counts": dict(sorted(layer_counts.items())),
        "operation_counts": {
            "create": len(records),
            "retain_active": status_counts.get("active", 0),
            "supersede": status_counts.get("superseded", 0),
            "retain_collection_multi_value_slot": nonmanaged_multi_value_slots,
        },
        "managed_lifecycle_slot_count": managed_lifecycle_slots,
        "nonmanaged_multi_value_slot_count": nonmanaged_multi_value_slots,
        "object_graph": object_graph,
        "clean_note": (
            "Build-time memory management is question-independent and uses only "
            "typed records derived from raw turns. Non-managed multi-value slots "
            "remain active collection facts rather than current-state updates."
        ),
    }
    if include_operation_ledger:
        summary["operation_ledger"] = _memory_operation_ledger(
            raw_records=tuple(raw_records or records),
            deduped_records=tuple(deduped_records or records),
            managed_records=records,
            managed_memory_types=managed_memory_types,
            merge_groups=merge_groups,
            supersede_pairs=supersede_pairs,
        )
    if include_memory_system_graph:
        summary["memory_system_graph"] = _memory_system_graph_summary(
            raw_records=tuple(raw_records or records),
            deduped_records=tuple(deduped_records or records),
            managed_records=records,
            managed_memory_types=managed_memory_types,
            merge_groups=merge_groups,
            supersede_pairs=supersede_pairs,
        )
    return summary


def _memory_operation_ledger(
    *,
    raw_records: tuple[MemoryRecord, ...],
    deduped_records: tuple[MemoryRecord, ...],
    managed_records: tuple[MemoryRecord, ...],
    managed_memory_types: frozenset[str],
    merge_groups: tuple[dict[str, Any], ...],
    supersede_pairs: tuple[dict[str, Any], ...],
) -> dict[str, Any]:
    """Trace-only operation ledger for build-stage memory management."""

    groups: dict[tuple[str, str, str], list[MemoryRecord]] = defaultdict(list)
    for record in managed_records:
        if not record.subject or not record.predicate:
            continue
        groups[
            (
                record.memory_type,
                _normalize_key_text(record.subject),
                _normalize_key_text(record.predicate),
            )
        ].append(record)

    collection_slots = []
    conflict_slots = []
    for key, group in sorted(groups.items()):
        values = {
            _normalize_key_text(record.value or record.text)
            for record in group
            if record.value or record.text
        }
        statuses = {record.status for record in group}
        has_lifecycle = "superseded" in statuses or len(values) > 1
        if not has_lifecycle:
            continue
        if key[0] in managed_memory_types:
            conflict_slots.append((key, tuple(group)))
        else:
            collection_slots.append((key, tuple(group)))

    operation_counts = {
        "create": len(deduped_records),
        "merge": sum(len(group.get("merged") or ()) for group in merge_groups),
        "supersede": len(supersede_pairs),
        "retain_active": sum(
            1 for record in managed_records if record.status == "active"
        ),
        "retain_superseded": sum(
            1 for record in managed_records if record.status == "superseded"
        ),
        "retain_collection_multi_value_slot": len(collection_slots),
        "verify_source_backed": sum(1 for record in managed_records if record.source_ids),
        "audit_slot": len(groups),
        "audit_conflict_slot": len(conflict_slots),
    }
    source_backed_count = operation_counts["verify_source_backed"]
    source_unbacked_count = max(0, len(managed_records) - source_backed_count)
    return {
        "enabled": True,
        "trace_only": True,
        "applied": True,
        "operation_counts": operation_counts,
        "source_backed_record_count": source_backed_count,
        "source_unbacked_record_count": source_unbacked_count,
        "layer_operation_counts": _layer_operation_counts(
            deduped_records=deduped_records,
            managed_records=managed_records,
            supersede_pairs=supersede_pairs,
        ),
        "samples": {
            "create": [
                _operation_sample("create", record)
                for record in deduped_records[:4]
            ],
            "merge": [
                _merge_operation_sample(group)
                for group in merge_groups[:4]
            ],
            "supersede": [
                _supersede_operation_sample(pair)
                for pair in supersede_pairs[:4]
            ],
            "retain_collection_multi_value_slot": [
                _slot_operation_sample("retain_collection_multi_value_slot", key, group)
                for key, group in collection_slots[:4]
            ],
            "audit_conflict_slot": [
                _slot_operation_sample("audit_conflict_slot", key, group)
                for key, group in conflict_slots[:4]
            ],
        },
        "clean_note": (
            "Trace-only build memory operation ledger. It summarizes "
            "question-independent create, merge, supersede, retain, verify, and "
            "audit operations over source-backed typed memories; it is not used "
            "by retrieval, compiler, answer, repair, finalizer, or cache keys."
        ),
    }


def _memory_system_graph_summary(
    *,
    raw_records: tuple[MemoryRecord, ...],
    deduped_records: tuple[MemoryRecord, ...],
    managed_records: tuple[MemoryRecord, ...],
    managed_memory_types: frozenset[str],
    merge_groups: tuple[dict[str, Any], ...],
    supersede_pairs: tuple[dict[str, Any], ...],
) -> dict[str, Any]:
    """Question-independent memory system graph over source-backed build memory.

    The graph is intentionally conservative: it describes memory objects,
    source spans, lifecycle slots, and operation edges. Explicit retrieval
    policies may consume governance readiness ids, but final evidence still
    resolves to raw source rows.
    """

    source_ids = _ordered_strings(
        source_id for record in managed_records for source_id in record.source_ids
    )
    groups: dict[tuple[str, str, str], list[MemoryRecord]] = defaultdict(list)
    for record in managed_records:
        if not record.subject or not record.predicate:
            continue
        groups[
            (
                record.memory_type,
                _normalize_key_text(record.subject),
                _normalize_key_text(record.predicate),
            )
        ].append(record)

    namespace_counts: dict[str, int] = defaultdict(int)
    lifecycle_counts: dict[str, int] = defaultdict(int)
    layer_counts: dict[str, int] = defaultdict(int)
    tier_counts: dict[str, int] = defaultdict(int)
    for record in managed_records:
        namespace_counts[_memory_namespace(record)] += 1
        lifecycle_counts[record.status] += 1
        layer_counts[_memory_layer(record.memory_type)] += 1
        tier_counts[
            _memory_tier(record, managed_memory_types=managed_memory_types)
        ] += 1

    slot_member_edges = sum(len(records) for records in groups.values())
    source_support_edges = sum(len(record.source_ids) for record in managed_records)
    scalar_value_manifest = _memory_scalar_value_manifest(
        groups,
        managed_memory_types=managed_memory_types,
    )
    state_conflict_manifest = _memory_state_conflict_manifest(
        groups,
        managed_memory_types=managed_memory_types,
    )
    tier_manifest = _memory_system_tier_manifest(
        managed_records,
        managed_memory_types=managed_memory_types,
    )
    source_policy = _memory_slot_source_policy_manifest(
        groups,
        managed_memory_types=managed_memory_types,
    )
    governance_manifest = _memory_system_governance_manifest(
        managed_records,
        managed_memory_types=managed_memory_types,
    )
    operation_manifest = _memory_system_operation_manifest(
        raw_records=raw_records,
        deduped_records=deduped_records,
        managed_records=managed_records,
        groups=groups,
        managed_memory_types=managed_memory_types,
        merge_groups=merge_groups,
        supersede_pairs=supersede_pairs,
    )
    memory_object_index = _memory_object_index_manifest(
        managed_records=managed_records,
        groups=groups,
        managed_memory_types=managed_memory_types,
        tier_manifest=tier_manifest,
        source_policy=source_policy,
        operation_manifest=operation_manifest,
        state_conflict_manifest=state_conflict_manifest,
        scalar_value_manifest=scalar_value_manifest,
        governance_manifest=governance_manifest,
    )
    operation_edge_counts = {
        "create": len(deduped_records),
        "merge": sum(len(group.get("merged") or ()) for group in merge_groups),
        "supersede": len(supersede_pairs),
        "source_support": source_support_edges,
        "slot_member": slot_member_edges,
        "value_object": scalar_value_manifest["value_object_count"],
        "scalar_value_object": scalar_value_manifest["scalar_value_object_count"],
        "audit_value_slot": scalar_value_manifest["value_slot_count"],
        "state_conflict_cluster": sum(
            1
            for key, records in groups.items()
            if key[0] in managed_memory_types
            and _slot_has_active_superseded_pair(records)
        ),
        "verify_source_backed": sum(
            1 for record in managed_records if record.source_ids
        ),
        "audit_slot": len(groups),
    }

    return {
        "enabled": True,
        "trace_only": False,
        "applied": True,
        "schema_version": "memory_system_graph_v3",
        "object_schema": _memory_system_object_schema(),
        "raw_record_count": len(raw_records),
        "deduped_record_count": len(deduped_records),
        "memory_object_count": len(managed_records),
        "active_object_count": lifecycle_counts.get("active", 0),
        "superseded_object_count": lifecycle_counts.get("superseded", 0),
        "source_span_count": len(source_ids),
        "slot_count": len(groups),
        "managed_lifecycle_slot_count": sum(
            1
            for key, records in groups.items()
            if key[0] in managed_memory_types and _slot_has_lifecycle(records)
        ),
        "collection_slot_count": sum(
            1
            for key, records in groups.items()
            if key[0] not in managed_memory_types and _slot_has_lifecycle(records)
        ),
        "namespace_counts": dict(sorted(namespace_counts.items())),
        "layer_counts": dict(sorted(layer_counts.items())),
        "tier_counts": dict(sorted(tier_counts.items())),
        "lifecycle_counts": dict(sorted(lifecycle_counts.items())),
        "operation_edge_counts": operation_edge_counts,
        "source_quality": _memory_system_source_quality(
            managed_records,
            managed_memory_types=managed_memory_types,
        ),
        "slot_quality": _memory_system_slot_quality(
            groups,
            managed_memory_types=managed_memory_types,
        ),
        "governance_manifest": governance_manifest,
        "source_policy": source_policy,
        "tier_manifest": tier_manifest,
        "operation_manifest": operation_manifest,
        "state_conflict_manifest": state_conflict_manifest,
        "scalar_value_manifest": scalar_value_manifest,
        "memory_object_index": memory_object_index,
        "governance": {
            "raw_evidence_policy": "immutable_final_authority",
            "derived_memory_policy": "source_backed_activation_and_audit",
            "final_evidence_policy": "raw_source_rows_only",
            "question_independent_build": True,
        },
        "memory_object_samples": [
            _memory_object_sample(
                record,
                managed_memory_types=managed_memory_types,
            )
            for record in managed_records[:10]
        ],
        "slot_samples": [
            _memory_system_slot_sample(key, tuple(records))
            for key, records in sorted(groups.items())[:10]
        ],
        "operation_edge_samples": _memory_system_operation_edge_samples(
            managed_records=managed_records,
            merge_groups=merge_groups,
            supersede_pairs=supersede_pairs,
        ),
        "source_span_samples": source_ids[:12],
        "clean_note": (
            "Question-independent build memory system graph. It organizes source-backed "
            "typed memories into namespaces, lifecycle states, object slots, "
            "source-support edges, merge edges, supersede edges, and quality "
            "signals. Explicit retrieval.memory_governance_activation may use "
            "the governance manifest to gate typed-memory activation; final "
            "answer evidence still resolves to raw source rows."
        ),
    }


def _memory_system_object_schema() -> dict[str, Any]:
    return {
        "memory_object_fields": [
            "memory_id",
            "memory_type",
            "namespace",
            "layer",
            "status",
            "subject",
            "predicate",
            "value",
            "source_ids",
            "timestamp",
            "mention_time",
            "event_time",
            "valid_from",
            "valid_to",
            "entities",
            "confidence",
            "superseded_by",
            "memory_tier",
        ],
        "edge_types": [
            "create",
            "merge",
            "supersede",
            "source_support",
            "slot_member",
            "verify_source_backed",
            "audit_slot",
            "state_conflict_cluster",
            "operation_contract",
            "value_object",
            "scalar_value_object",
        ],
        "quality_signals": [
            "source_backed",
            "complete_slot_key",
            "temporal_anchor",
            "confidence_bucket",
            "lifecycle_signal",
            "source_coverage",
            "temporal_scope_kind",
            "validity_status",
            "source_confidence_bucket",
            "activation_utility_score",
            "activation_utility_bucket",
            "slot_source_policy",
            "memory_tier",
            "state_conflict_cluster",
            "operation_contract_ready",
            "value_object",
            "scalar_value",
            "build_owned_scalar_value_manifest",
        ],
        "governance_signals": [
            "source_activation_ready",
            "activation_role",
            "activation_priority",
            "question_scope_source_order",
            "tier_counts",
            "temporal_scope_counts",
            "validity_status_counts",
            "raw_evidence_required",
            "low_confidence_blocked",
            "unbacked_blocked",
            "incomplete_slot_key_audited",
            "build_owned_conflict_cluster",
            "build_owned_operation_manifest",
            "build_owned_scalar_value_manifest",
            "build_owned_memory_object_index",
            "build_owned_operation_slot_index",
            "build_owned_operation_registry",
        ],
}


def _memory_object_index_manifest(
    *,
    managed_records: tuple[MemoryRecord, ...],
    groups: dict[tuple[str, str, str], list[MemoryRecord]],
    managed_memory_types: frozenset[str],
    tier_manifest: dict[str, Any],
    source_policy: dict[str, Any],
    operation_manifest: dict[str, Any],
    state_conflict_manifest: dict[str, Any],
    scalar_value_manifest: dict[str, Any],
    governance_manifest: dict[str, Any],
) -> dict[str, Any]:
    """Unified build-owned memory object index for query-time consumers.

    The index is a stable interface over the lower-level manifests. It does not
    create new facts: every object and slot remains source-backed and final
    answer evidence must still expand to raw source rows.
    """

    source_policy_by_slot = {
        slot.get("slot_id"): slot
        for slot in source_policy.get("slot_samples", ())
        if isinstance(slot, dict) and slot.get("slot_id")
    }
    state_conflict_slots = _memory_object_state_conflict_slot_index(
        state_conflict_manifest
    )
    conflict_slot_ids = {
        slot.get("cluster_id")
        for slot in state_conflict_slots
        if isinstance(slot, dict) and slot.get("cluster_id")
    }
    value_slots = []
    for raw_slot in scalar_value_manifest.get("slot_index", ()):
        if not isinstance(raw_slot, dict):
            continue
        slot_id = str(raw_slot.get("slot_id") or "")
        slot_policy = source_policy_by_slot.get(slot_id, {})
        value_slots.append(
            {
                **raw_slot,
                "index_source": "scalar_value_manifest",
                "memory_tier": _slot_memory_tier(
                    raw_slot,
                    managed_memory_types=managed_memory_types,
                ),
                "conflict_cluster": slot_id in conflict_slot_ids,
                "current_source_order": raw_slot.get("current_source_order")
                or slot_policy.get("current_source_order")
                or [],
                "historical_source_order": raw_slot.get("historical_source_order")
                or slot_policy.get("historical_source_order")
                or [],
                "source_policy": {
                    "source_order_policy": "memory_slot_source_policy_v1",
                    "raw_evidence_required": True,
                },
            }
        )

    operation_slots = _memory_object_operation_slot_index(
        groups,
        managed_memory_types=managed_memory_types,
    )
    operation_registry = _memory_object_operation_registry(
        managed_records=managed_records,
        managed_memory_types=managed_memory_types,
        value_slots=value_slots,
        operation_slots=operation_slots,
        state_conflict_slots=state_conflict_slots,
        operation_manifest=operation_manifest,
    )
    object_samples = [
        {
            "memory_id": record.memory_id,
            "memory_type": record.memory_type,
            "namespace": _memory_namespace(record),
            "layer": _memory_layer(record.memory_type),
            "memory_tier": _memory_tier(
                record,
                managed_memory_types=managed_memory_types,
            ),
            "status": record.status,
            "subject": _normalize_key_text(record.subject),
            "predicate": _normalize_key_text(record.predicate),
            "value": _normalize_key_text(record.value or record.text)[:160],
            "source_ids": list(record.source_ids[:8]),
            "source_backed": bool(record.source_ids),
            "activation_ready": bool(
                _memory_system_record_governance(
                    record,
                    managed_memory_types=managed_memory_types,
                )["source_activation_ready"]
            ),
            "operation_hints": _memory_object_operation_hints(record),
        }
        for record in managed_records[:24]
    ]
    activation_ready_memory_ids = [
        str(memory_id)
        for memory_id in (
            governance_manifest.get("source_activation_ready_memory_ids") or ()
        )
        if str(memory_id).strip()
    ]
    activation_priority_memory_ids = [
        str(memory_id)
        for memory_id in (
            governance_manifest.get("activation_priority_memory_ids") or ()
        )
        if str(memory_id).strip()
    ]
    layer_counts: dict[str, int] = defaultdict(int)
    for record in managed_records:
        layer_counts[_memory_layer(record.memory_type)] += 1

    return {
        "schema_version": "memory_object_index_v1",
        "trace_only": False,
        "applied": True,
        "object_count": len(managed_records),
        "slot_count": len(groups),
        "value_slot_count": len(value_slots),
        "operation_slot_count": len(operation_slots),
        "state_conflict_slot_count": len(state_conflict_slots),
        "operation_registry_entry_count": operation_registry["entry_count"],
        "operation_registry_object_entry_count": (
            operation_registry["object_entry_count"]
        ),
        "operation_registry_slot_entry_count": operation_registry["slot_entry_count"],
        "operation_registry_conflict_entry_count": (
            operation_registry["conflict_entry_count"]
        ),
        "operation_registry_source_backed_entry_count": (
            operation_registry["source_backed_entry_count"]
        ),
        "source_backed_object_count": sum(
            1 for record in managed_records if record.source_ids
        ),
        "activation_ready_object_count": len(activation_ready_memory_ids),
        "activation_ready_memory_id_count": len(activation_ready_memory_ids),
        "activation_priority_memory_id_count": len(activation_priority_memory_ids),
        "tier_counts": dict(tier_manifest.get("tier_counts") or {}),
        "layer_counts": dict(sorted(layer_counts.items())),
        "operation_counts": dict(operation_manifest.get("operation_counts") or {}),
        "index_contract": {
            "memory_layers": dict(
                operation_manifest.get("object_contract", {}).get("memory_layers")
                or {}
            ),
            "object_operations": [
                "create",
                "update",
                "merge",
                "supersede",
                "retrieve",
                "expand",
                "verify",
                "audit",
            ],
            "query_use_policy": (
                "Use as source-backed activation, state organization, conflict "
                "resolution, context packing, and audit interface only."
            ),
            "final_evidence_policy": "raw_source_rows",
            "question_independent": True,
            "activation_contract": {
                "source": "governance_manifest",
                "ready_ids_field": "activation_ready_memory_ids",
                "priority_ids_field": "activation_priority_memory_ids",
                "policy": "source_backed_activation_ready_first",
            },
            "operation_slot_contract": {
                "slot_index_field": "operation_slot_index",
                "slot_scope": "same memory_type, subject, predicate",
                "source_order_fields": [
                    "operation_current_source_order",
                    "operation_historical_source_order",
                    "validity_current_source_order",
                    "validity_historical_source_order",
                ],
                "policy": "query_consumers_choose_scope_and_expand_to_raw_sources",
            },
            "operation_registry_contract": {
                "registry_field": "operation_registry",
                "target_types": [
                    "object",
                    "value_slot",
                    "operation_slot",
                    "conflict_slot",
                ],
                "operation_scope": "source_backed_memory_management_and_context_use",
                "policy": "operations_expand_to_raw_sources_before_final_evidence",
            },
            "state_conflict_contract": {
                "slot_index_field": "state_conflict_slot_index",
                "slot_scope": "same memory_type, subject, predicate",
                "source_order_policy": "memory_slot_source_policy_v1",
                "policy": "compiler_uses_as_conflict_filter_only",
            },
        },
        "activation_ready_memory_ids": activation_ready_memory_ids,
        "activation_priority_memory_ids": activation_priority_memory_ids,
        "object_index_samples": object_samples,
        "value_slot_index": value_slots,
        "operation_slot_index": operation_slots,
        "state_conflict_slot_index": state_conflict_slots,
        "operation_registry": operation_registry,
        "state_conflict_slot_ids": sorted(str(slot_id) for slot_id in conflict_slot_ids),
        "clean_note": (
            "Question-independent build memory object index. It unifies tier, "
            "operation, state-conflict, source-policy, and value-slot manifests "
            "into one source-backed interface for retrieval, compiler, context "
            "organization, verifier, and audit. It does not use gold answers, "
            "judge outputs, benchmark labels, sample ids, test feedback, or "
            "sample-level rules; final answer evidence remains raw source rows."
        ),
    }


def _memory_object_state_conflict_slot_index(
    state_conflict_manifest: dict[str, Any],
) -> list[dict[str, Any]]:
    slots: list[dict[str, Any]] = []
    for cluster in state_conflict_manifest.get("clusters", ()) or ():
        if not isinstance(cluster, dict):
            continue
        slots.append(
            {
                **cluster,
                "index_source": "state_conflict_manifest",
                "operation_hints": [
                    "audit_state_conflict_slot",
                    "compare_active_superseded",
                    "expand_conflict_sources",
                    "verify_source_backed",
                ],
                "source_policy": {
                    "source_order_policy": "memory_slot_source_policy_v1",
                    "raw_evidence_required": True,
                },
            }
        )
    return slots


def _memory_object_operation_registry(
    *,
    managed_records: tuple[MemoryRecord, ...],
    managed_memory_types: frozenset[str],
    value_slots: list[dict[str, Any]],
    operation_slots: list[dict[str, Any]],
    state_conflict_slots: list[dict[str, Any]],
    operation_manifest: dict[str, Any],
) -> dict[str, Any]:
    """A build-owned registry for memory operations over objects and slots."""

    entries: list[dict[str, Any]] = []
    for record in managed_records:
        entries.append(
            _memory_object_operation_registry_object_entry(
                record,
                managed_memory_types=managed_memory_types,
            )
        )
    for slot in value_slots:
        entries.append(
            _memory_object_operation_registry_slot_entry(
                slot,
                target_type="value_slot",
                target_id=str(slot.get("slot_id") or ""),
                operations=tuple(str(item) for item in slot.get("operation_hints") or ()),
                source_order_fields=("current_source_order", "historical_source_order"),
            )
        )
    for slot in operation_slots:
        entries.append(
            _memory_object_operation_registry_slot_entry(
                slot,
                target_type="operation_slot",
                target_id=str(slot.get("slot_id") or ""),
                operations=tuple(
                    _memory_object_operation_slot_registry_operations(slot)
                ),
                source_order_fields=(
                    "validity_current_source_order",
                    "validity_historical_source_order",
                    "operation_current_source_order",
                    "operation_historical_source_order",
                ),
            )
        )
    for slot in state_conflict_slots:
        entries.append(
            _memory_object_operation_registry_slot_entry(
                slot,
                target_type="conflict_slot",
                target_id=str(slot.get("cluster_id") or ""),
                operations=tuple(str(item) for item in slot.get("operation_hints") or ()),
                source_order_fields=("current_source_order", "historical_source_order"),
            )
        )

    operation_counts: dict[str, int] = defaultdict(int)
    target_counts: dict[str, int] = defaultdict(int)
    source_backed_count = 0
    source_incomplete_count = 0
    for entry in entries:
        target_type = str(entry.get("target_type") or "unknown")
        target_counts[target_type] += 1
        if entry.get("source_backed"):
            source_backed_count += 1
        else:
            source_incomplete_count += 1
        for operation in entry.get("operations") or ():
            operation_counts[str(operation)] += 1

    return {
        "schema_version": "memory_operation_registry_v1",
        "trace_only": False,
        "applied": True,
        "entry_count": len(entries),
        "object_entry_count": target_counts.get("object", 0),
        "value_slot_entry_count": target_counts.get("value_slot", 0),
        "slot_entry_count": (
            target_counts.get("value_slot", 0)
            + target_counts.get("operation_slot", 0)
        ),
        "operation_slot_entry_count": target_counts.get("operation_slot", 0),
        "conflict_entry_count": target_counts.get("conflict_slot", 0),
        "source_backed_entry_count": source_backed_count,
        "source_incomplete_entry_count": source_incomplete_count,
        "target_counts": dict(sorted(target_counts.items())),
        "operation_counts": dict(sorted(operation_counts.items())),
        "manifest_operation_counts": dict(
            operation_manifest.get("operation_counts") or {}
        ),
        "operation_policy": dict(operation_manifest.get("operation_policy") or {}),
        "source_policy": {
            "raw_evidence_required": True,
            "final_evidence_policy": "raw_source_rows",
            "question_independent_build": True,
        },
        "entries": entries,
        "clean_note": (
            "Question-independent build registry for memory operations. Entries "
            "cover object lifecycle, value slots, operation slots, and conflict "
            "slots; every query-facing operation must expand to raw source rows "
            "before final evidence."
        ),
    }


def _memory_object_operation_registry_object_entry(
    record: MemoryRecord,
    *,
    managed_memory_types: frozenset[str],
) -> dict[str, Any]:
    source_ids = list(record.source_ids[:12])
    return {
        "entry_id": f"op:object:{record.memory_id}",
        "target_type": "object",
        "target_id": record.memory_id,
        "memory_id": record.memory_id,
        "memory_type": record.memory_type,
        "namespace": _memory_namespace(record),
        "layer": _memory_layer(record.memory_type),
        "memory_tier": _memory_tier(
            record,
            managed_memory_types=managed_memory_types,
        ),
        "status": record.status,
        "subject": _normalize_key_text(record.subject),
        "predicate": _normalize_key_text(record.predicate),
        "operations": _memory_object_operation_hints(record),
        "source_backed": bool(source_ids),
        "source_ids": source_ids,
        "expand_source_order": source_ids,
        "verify_policy": "source_backed_memory_object",
        "audit_policy": "source_support_confidence_slot_and_lifecycle",
        "source_policy": {
            "raw_evidence_required": True,
            "final_evidence_policy": "raw_source_rows",
        },
    }


def _memory_object_operation_registry_slot_entry(
    slot: dict[str, Any],
    *,
    target_type: str,
    target_id: str,
    operations: tuple[str, ...],
    source_order_fields: tuple[str, ...],
) -> dict[str, Any]:
    source_ids = _ordered_strings(
        source_id
        for field in source_order_fields
        for source_id in (slot.get(field) or ())
    )
    if not source_ids:
        source_ids = _ordered_strings(slot.get("source_ids") or ())
    return {
        "entry_id": f"op:{target_type}:{target_id}",
        "target_type": target_type,
        "target_id": target_id,
        "slot_id": target_id,
        "memory_type": str(slot.get("memory_type") or ""),
        "namespace": str(slot.get("namespace") or ""),
        "layer": str(
            slot.get("layer") or _memory_layer(str(slot.get("memory_type") or ""))
        ),
        "memory_tier": str(slot.get("memory_tier") or ""),
        "managed": bool(slot.get("managed")),
        "subject": _normalize_key_text(str(slot.get("subject") or "")),
        "predicate": _normalize_key_text(str(slot.get("predicate") or "")),
        "operations": _ordered_strings(operations),
        "graph_signals": _ordered_strings(slot.get("graph_signals") or ()),
        "lexical_terms": _ordered_strings(slot.get("lexical_terms") or ())[:32],
        "source_backed": bool(slot.get("source_backed") or source_ids),
        "source_ids": source_ids[:12],
        "expand_source_order": source_ids[:12],
        "operation_current_source_order": _ordered_strings(
            slot.get("operation_current_source_order") or ()
        )[:12],
        "operation_historical_source_order": _ordered_strings(
            slot.get("operation_historical_source_order") or ()
        )[:12],
        "validity_current_source_order": _ordered_strings(
            slot.get("validity_current_source_order") or ()
        )[:12],
        "validity_historical_source_order": _ordered_strings(
            slot.get("validity_historical_source_order") or ()
        )[:12],
        "active_memory_ids": _ordered_strings(slot.get("active_memory_ids") or ())[:12],
        "superseded_memory_ids": _ordered_strings(
            slot.get("superseded_memory_ids") or ()
        )[:12],
        "record_count": int(slot.get("record_count") or 0),
        "status_counts": dict(slot.get("status_counts") or {}),
        "values": _ordered_strings(slot.get("values") or ())[:12],
        "source_policy": {
            **dict(slot.get("source_policy") or {}),
            "raw_evidence_required": True,
            "final_evidence_policy": "raw_source_rows",
        },
    }


def _memory_object_operation_slot_registry_operations(
    slot: dict[str, Any],
) -> list[str]:
    operations = ["retrieve", "expand", "verify", "audit"]
    for operation in slot.get("operations") or ():
        if operation:
            operations.append(str(operation))
    for signal in slot.get("graph_signals") or ():
        if signal in {"supersede", "conflict_slot", "multi_value_slot"}:
            operations.append(f"audit_{signal}")
    return _ordered_strings(operations)


def _memory_object_operation_slot_index(
    groups: dict[tuple[str, str, str], list[MemoryRecord]],
    *,
    managed_memory_types: frozenset[str],
) -> list[dict[str, Any]]:
    slots: list[dict[str, Any]] = []
    for key, records in sorted(groups.items()):
        record_tuple = tuple(records)
        source_ids = _ordered_strings(
            source_id for record in record_tuple for source_id in record.source_ids
        )
        memory_type, subject, predicate = key
        slots.append(
            {
                "slot_id": _slot_id(key),
                "memory_type": memory_type,
                "namespace": _memory_namespace(record_tuple[0]),
                "layer": _memory_layer(memory_type),
                "managed": memory_type in managed_memory_types,
                "subject": subject,
                "predicate": predicate,
                "record_count": len(record_tuple),
                "status_counts": _memory_operation_slot_status_counts(record_tuple),
                "operations": _memory_operation_slot_types_for_index(
                    record_tuple,
                    managed_memory_types=managed_memory_types,
                ),
                "graph_signals": _memory_graph_slot_signals_for_index(
                    record_tuple,
                    managed_memory_types=managed_memory_types,
                ),
                "lexical_terms": _memory_operation_slot_lexical_terms(record_tuple)[:32],
                "source_backed": bool(source_ids),
                "source_ids": source_ids[:12],
                "operation_current_source_order": _memory_operation_slot_source_order(
                    record_tuple,
                    question_scope="current",
                    source_selection_policy="legacy",
                )[:12],
                "operation_historical_source_order": _memory_operation_slot_source_order(
                    record_tuple,
                    question_scope="historical",
                    source_selection_policy="legacy",
                )[:12],
                "validity_current_source_order": _memory_operation_slot_source_order(
                    record_tuple,
                    question_scope="current",
                    source_selection_policy="validity_aware",
                )[:12],
                "validity_historical_source_order": _memory_operation_slot_source_order(
                    record_tuple,
                    question_scope="historical",
                    source_selection_policy="validity_aware",
                )[:12],
                "memory_ids": [record.memory_id for record in record_tuple[:12]],
                "active_memory_ids": [
                    record.memory_id
                    for record in record_tuple
                    if record.status == "active"
                ][:12],
                "superseded_memory_ids": [
                    record.memory_id
                    for record in record_tuple
                    if record.status == "superseded"
                ][:12],
                "values": _ordered_normalized_values(
                    record.value or record.text for record in record_tuple
                )[:12],
                "temporal_anchors": _ordered_strings(
                    _record_time_value(record) for record in record_tuple
                )[:12],
                "source_policy": {
                    "legacy_operation_order": "active_or_historical_status_then_time",
                    "validity_aware_order": "memory_slot_source_policy_v1",
                    "raw_evidence_required": True,
                },
            }
        )
    return slots


def _memory_operation_slot_lexical_terms(
    records: tuple[MemoryRecord, ...],
) -> list[str]:
    terms: set[str] = set()
    for record in records:
        terms.update(
            _memory_operation_slot_text_terms(
                " ".join(
                    part
                    for part in (
                        record.predicate,
                        record.value,
                        record.text,
                        " ".join(record.entities),
                    )
                    if part
                )
            )
        )
    return sorted(term for term in terms if term)


def _memory_operation_slot_text_terms(value: str) -> set[str]:
    normalized = re.sub(r"[_/\\-]+", " ", value.lower())
    terms: set[str] = set()
    for token in re.findall(r"[a-z0-9]+", normalized):
        if len(token) <= 1:
            continue
        terms.add(token)
        if token.endswith("ves") and len(token) > 4:
            terms.add(token[:-1])
        if token.endswith("ies") and len(token) > 4:
            terms.add(token[:-3] + "y")
        if token.endswith("ed") and len(token) > 4:
            terms.add(token[:-1])
            terms.add(token[:-2])
        if token.endswith("ing") and len(token) > 5:
            terms.add(token[:-3])
        if token.endswith("s") and len(token) > 3:
            terms.add(token[:-1])
    return terms


def _memory_operation_slot_types_for_index(
    records: tuple[MemoryRecord, ...],
    *,
    managed_memory_types: frozenset[str],
) -> list[str]:
    if not records:
        return []
    memory_type = str(records[0].memory_type or "").lower()
    managed_slot = memory_type in managed_memory_types
    active_values: set[str] = set()
    superseded_values: set[str] = set()
    lifecycle_signal = False
    for record in records:
        value = _normalize_key_text(record.value or record.text)
        status = str(record.status or "active").lower()
        if status == "superseded":
            lifecycle_signal = True
            if value:
                superseded_values.add(value)
        else:
            if value:
                active_values.add(value)
        if record.superseded_by or record.valid_to:
            lifecycle_signal = True

    distinct_values = active_values | superseded_values
    conflict_slot = (
        managed_slot
        and len(distinct_values) > 1
        and (lifecycle_signal or len(active_values) > 1)
    )
    operations: list[str] = []
    if lifecycle_signal:
        operations.append("supersede")
    if conflict_slot:
        operations.append("conflict_slot")
    if len(distinct_values) > 1 and not lifecycle_signal and not conflict_slot:
        operations.append("collection_multi_value_slot")
    return operations


def _memory_graph_slot_signals_for_index(
    records: tuple[MemoryRecord, ...],
    *,
    managed_memory_types: frozenset[str],
) -> list[str]:
    if not records:
        return []
    signals: list[str] = []
    if any(record.source_ids for record in records):
        signals.append("source_support")
    if any(
        record.status == "superseded" or record.superseded_by or record.valid_to
        for record in records
    ):
        signals.append("supersede")
    if len(_ordered_normalized_values(record.value or record.text for record in records)) > 1:
        signals.append("multi_value_slot")
    for signal in _memory_operation_slot_types_for_index(
        records,
        managed_memory_types=managed_memory_types,
    ):
        if signal not in signals:
            signals.append(signal)
    return signals


def _memory_operation_slot_source_order(
    records: tuple[MemoryRecord, ...],
    *,
    question_scope: str,
    source_selection_policy: str,
) -> list[str]:
    if source_selection_policy == "validity_aware":
        return _memory_slot_policy_source_ids(
            records,
            question_scope=question_scope,
        )
    source_ids: list[str] = []
    for record in sorted(
        records,
        key=lambda item: _memory_operation_slot_record_sort_key_for_index(
            item,
            question_scope=question_scope,
        ),
    ):
        for source_id in record.source_ids:
            if source_id not in source_ids:
                source_ids.append(source_id)
    return source_ids


def _memory_operation_slot_record_sort_key_for_index(
    record: MemoryRecord,
    *,
    question_scope: str,
) -> tuple[int, str, str]:
    status = str(record.status or "active").lower()
    if question_scope == "historical":
        status_rank = 0 if status != "active" else 1
    else:
        status_rank = 0 if status == "active" else 1
    time_value = record.valid_from or record.timestamp or record.mention_time or ""
    return (status_rank, str(time_value), str(record.memory_id))


def _memory_operation_slot_status_counts(
    records: tuple[MemoryRecord, ...],
) -> dict[str, int]:
    counts: dict[str, int] = {}
    for record in records:
        status = str(record.status or "active")
        counts[status] = counts.get(status, 0) + 1
    return dict(sorted(counts.items()))


def _slot_memory_tier(
    slot: dict[str, Any],
    *,
    managed_memory_types: frozenset[str],
) -> str:
    memory_type = str(slot.get("memory_type") or "")
    if not bool(slot.get("source_backed", True)):
        return "quarantine_memory"
    if slot.get("superseded_memory_ids") and not slot.get("active_memory_ids"):
        return "archival_memory"
    if memory_type in managed_memory_types or memory_type == "plan":
        return "working_memory"
    return "long_term_memory"


def _memory_object_operation_hints(record: MemoryRecord) -> list[str]:
    hints = ["create", "retrieve", "verify", "audit"]
    if record.source_ids:
        hints.append("expand")
    if record.status == "superseded":
        hints.append("supersede")
    if not record.source_ids or record.confidence < 0.5:
        hints.append("quarantine")
    return hints


def _memory_system_operation_manifest(
    *,
    raw_records: tuple[MemoryRecord, ...],
    deduped_records: tuple[MemoryRecord, ...],
    managed_records: tuple[MemoryRecord, ...],
    groups: dict[tuple[str, str, str], list[MemoryRecord]],
    managed_memory_types: frozenset[str],
    merge_groups: tuple[dict[str, Any], ...],
    supersede_pairs: tuple[dict[str, Any], ...],
) -> dict[str, Any]:
    """Build-owned operation contract for memory organization and use.

    Build does not answer questions here. It records which memory objects are
    safe to create, update, merge, supersede, retrieve as candidates, expand to
    raw rows, verify, and audit so query-time modules can consume a general
    memory system instead of re-deriving benchmark-shaped rules.
    """

    assessments = [
        _memory_system_record_governance(
            record,
            managed_memory_types=managed_memory_types,
        )
        for record in managed_records
    ]
    retrieval_ready_records = tuple(
        record
        for record, assessment in zip(managed_records, assessments)
        if assessment["source_activation_ready"]
    )
    source_backed_records = tuple(
        record for record in managed_records if record.source_ids
    )
    quarantine_records = tuple(
        record
        for record in managed_records
        if not record.source_ids or record.confidence < 0.5
    )
    lifecycle_slots = tuple(
        (key, tuple(records))
        for key, records in sorted(groups.items())
        if _slot_has_lifecycle(records)
    )
    state_conflict_slots = tuple(
        (key, records)
        for key, records in lifecycle_slots
        if key[0] in managed_memory_types
        and _slot_has_active_superseded_pair(records)
    )
    operation_counts = {
        "create": len(deduped_records),
        "update": len(supersede_pairs),
        "merge": sum(len(group.get("merged") or ()) for group in merge_groups),
        "supersede": len(supersede_pairs),
        "retrieve": len(retrieval_ready_records),
        "expand": sum(len(record.source_ids) for record in source_backed_records),
        "verify": len(source_backed_records),
        "audit": len(groups),
        "audit_lifecycle_slot": len(lifecycle_slots),
        "audit_state_conflict_slot": len(state_conflict_slots),
        "quarantine": len(quarantine_records),
    }
    return {
        "schema_version": "memory_operation_manifest_v1",
        "trace_only": False,
        "applied": True,
        "raw_record_count": len(raw_records),
        "operation_counts": operation_counts,
        "layer_operation_counts": _memory_system_operation_layer_counts(
            deduped_records=deduped_records,
            managed_records=managed_records,
            groups=groups,
            managed_memory_types=managed_memory_types,
            supersede_pairs=supersede_pairs,
            retrieval_ready_records=retrieval_ready_records,
        ),
        "operation_policy": {
            "create": "Create typed memory objects only from raw source rows.",
            "update": (
                "Update managed state/profile slots by appending a newer active "
                "object and retaining the old object as archival context."
            ),
            "merge": (
                "Merge duplicate normalized objects without dropping source "
                "provenance from the retained object."
            ),
            "supersede": (
                "Never physically delete old state; mark it superseded and keep "
                "raw sources available for historical questions."
            ),
            "retrieve": (
                "Expose source-backed, governance-ready memory objects as "
                "candidate activation and ranking signals only."
            ),
            "expand": (
                "Expand every activated derived object back to immutable raw "
                "source rows before final answer evidence is formed."
            ),
            "verify": (
                "Check source support, confidence, slot completeness, temporal "
                "anchors, and lifecycle state before activation."
            ),
            "audit": (
                "Audit lifecycle slots, state conflicts, low-confidence objects, "
                "and source-unbacked objects in build artifacts."
            ),
        },
        "object_contract": {
            "memory_layers": {
                "short_term_memory": (
                    "Query/session local evidence rows and scratch context; not "
                    "persisted by this build manifest."
                ),
                "working_memory": (
                    "Active source-backed state/profile/preference/relationship "
                    "and plan objects that may influence current behavior."
                ),
                "long_term_memory": (
                    "Durable semantic and episodic objects used for recall and "
                    "context organization."
                ),
                "archival_memory": (
                    "Superseded or closed objects retained for historical lookup, "
                    "conflict chains, and audit."
                ),
                "quarantine_memory": (
                    "Low-confidence or source-unbacked objects blocked from "
                    "normal activation until raw evidence supports them."
                ),
            },
            "final_evidence_policy": "raw_source_rows",
            "question_independent": True,
        },
        "samples": {
            "create": [
                _operation_sample("create", record)
                for record in deduped_records[:4]
            ],
            "update": [
                _supersede_operation_sample(pair)
                for pair in supersede_pairs[:4]
            ],
            "merge": [
                _merge_operation_sample(group)
                for group in merge_groups[:4]
            ],
            "retrieve": [
                _operation_sample("retrieve", record)
                for record in retrieval_ready_records[:4]
            ],
            "expand": [
                _operation_sample("expand", record)
                for record in source_backed_records[:4]
            ],
            "audit": [
                _slot_operation_sample("audit", key, group)
                for key, group in lifecycle_slots[:4]
            ],
        },
        "clean_note": (
            "Question-independent build operation manifest. It records general "
            "memory operations and contracts without using gold answers, judge "
            "outputs, benchmark labels, sample ids, test feedback, or "
            "sample-level rules."
        ),
    }


def _memory_scalar_value_manifest(
    groups: dict[tuple[str, str, str], list[MemoryRecord]],
    *,
    managed_memory_types: frozenset[str],
) -> dict[str, Any]:
    """Build-owned value objects and scalar slots.

    This manifest turns typed memories into auditable value slots. It is
    question-independent and source-backed: query modules may later consume the
    slot organization, but any final answer must still expand to raw rows.
    """

    slot_index: list[dict[str, Any]] = []
    value_records: list[MemoryRecord] = []
    scalar_value_object_count = 0
    scalar_value_expression_count = 0
    source_backed_value_object_count = 0
    source_incomplete_value_object_count = 0
    retrieval_ready_value_object_count = 0
    quarantine_value_object_count = 0
    active_superseded_value_slot_count = 0
    lifecycle_value_slot_count = 0
    multi_value_slot_count = 0
    scalar_value_slot_count = 0
    scalar_active_superseded_value_slot_count = 0
    value_source_edge_count = 0

    for key, records in sorted(groups.items()):
        slot_records = tuple(
            record for record in records if _memory_record_value_object(record)
        )
        if not slot_records:
            continue

        memory_type, subject, predicate = key
        value_records.extend(slot_records)
        value_source_edge_count += sum(len(record.source_ids) for record in slot_records)
        slot_values = _ordered_normalized_values(
            _memory_record_value_object(record) for record in slot_records
        )
        slot_scalar_values = _ordered_normalized_values(
            scalar_value
            for record in slot_records
            for scalar_value in _memory_record_scalar_values(record)
        )
        active_records = tuple(
            record for record in slot_records if record.status == "active"
        )
        superseded_records = tuple(
            record for record in slot_records if record.status == "superseded"
        )
        has_active_superseded = bool(active_records and superseded_records)
        if has_active_superseded:
            active_superseded_value_slot_count += 1
        if _slot_has_lifecycle(list(slot_records)):
            lifecycle_value_slot_count += 1
        if len(slot_values) > 1:
            multi_value_slot_count += 1
        if slot_scalar_values:
            scalar_value_slot_count += 1
            if has_active_superseded:
                scalar_active_superseded_value_slot_count += 1

        slot_index.append(
            {
                "slot_id": _slot_id(key),
                "memory_type": memory_type,
                "namespace": _memory_namespace(slot_records[0]),
                "layer": _memory_layer(memory_type),
                "managed": memory_type in managed_memory_types,
                "subject": subject,
                "predicate": predicate,
                "record_count": len(slot_records),
                "value_count": len(slot_values),
                "scalar_value_count": len(slot_scalar_values),
                "active_memory_ids": [
                    record.memory_id for record in active_records[:8]
                ],
                "superseded_memory_ids": [
                    record.memory_id for record in superseded_records[:8]
                ],
                "active_values": _ordered_normalized_values(
                    _memory_record_value_object(record) for record in active_records
                )[:8],
                "superseded_values": _ordered_normalized_values(
                    _memory_record_value_object(record)
                    for record in superseded_records
                )[:8],
                "scalar_values": slot_scalar_values[:8],
                "active_scalar_values": _ordered_normalized_values(
                    scalar_value
                    for record in active_records
                    for scalar_value in _memory_record_scalar_values(record)
                )[:8],
                "superseded_scalar_values": _ordered_normalized_values(
                    scalar_value
                    for record in superseded_records
                    for scalar_value in _memory_record_scalar_values(record)
                )[:8],
                "value_objects": [
                    {
                        "memory_id": record.memory_id,
                        "status": record.status or "active",
                        "value": _memory_record_value_object(record),
                        "scalar_values": list(_memory_record_scalar_values(record)),
                        "source_ids": list(record.source_ids),
                        "time": _record_time_value(record),
                        "valid_from": record.valid_from,
                        "valid_to": record.valid_to,
                        "superseded_by": record.superseded_by,
                        "confidence": record.confidence,
                    }
                    for record in slot_records
                ],
                "current_source_order": _memory_slot_policy_source_ids(
                    slot_records,
                    question_scope="current",
                )[:8],
                "historical_source_order": _memory_slot_policy_source_ids(
                    slot_records,
                    question_scope="historical",
                )[:8],
                "source_backed": all(record.source_ids for record in slot_records),
                "temporal_anchors": _ordered_strings(
                    _record_time_value(record) for record in slot_records
                )[:8],
                "operation_hints": _memory_value_slot_operation_hints(
                    slot_records,
                    has_scalar_values=bool(slot_scalar_values),
                ),
            }
        )

    for record in value_records:
        scalar_values = _memory_record_scalar_values(record)
        if scalar_values:
            scalar_value_object_count += 1
            scalar_value_expression_count += len(scalar_values)
        if record.source_ids:
            source_backed_value_object_count += 1
        else:
            source_incomplete_value_object_count += 1
        governance = _memory_system_record_governance(
            record,
            managed_memory_types=managed_memory_types,
        )
        if governance["source_activation_ready"]:
            retrieval_ready_value_object_count += 1
        if not record.source_ids or record.confidence < 0.5:
            quarantine_value_object_count += 1

    duplicate_value_object_count = sum(
        max(
            0,
            len(tuple(record for record in records if _memory_record_value_object(record)))
            - len(
                _ordered_normalized_values(
                    _memory_record_value_object(record)
                    for record in records
                    if _memory_record_value_object(record)
                )
            ),
        )
        for records in groups.values()
    )
    superseded_value_object_count = sum(
        1 for record in value_records if record.status == "superseded"
    )
    operation_counts = {
        "create_value_object": len(value_records),
        "create_scalar_value": scalar_value_object_count,
        "update_value_slot": active_superseded_value_slot_count,
        "merge_value_slot": duplicate_value_object_count,
        "supersede_value": superseded_value_object_count,
        "retrieve_value": retrieval_ready_value_object_count,
        "expand_value_source": value_source_edge_count,
        "verify_value_source": source_backed_value_object_count,
        "audit_value_slot": len(slot_index),
        "audit_scalar_value_slot": scalar_value_slot_count,
        "audit_conflict_value_slot": active_superseded_value_slot_count,
        "quarantine_value": quarantine_value_object_count,
    }
    return {
        "schema_version": "memory_scalar_value_manifest_v1",
        "trace_only": False,
        "applied": True,
        "value_object_count": len(value_records),
        "source_backed_value_object_count": source_backed_value_object_count,
        "source_incomplete_value_object_count": source_incomplete_value_object_count,
        "scalar_value_object_count": scalar_value_object_count,
        "scalar_value_expression_count": scalar_value_expression_count,
        "value_slot_count": len(slot_index),
        "scalar_value_slot_count": scalar_value_slot_count,
        "multi_value_slot_count": multi_value_slot_count,
        "lifecycle_value_slot_count": lifecycle_value_slot_count,
        "active_superseded_value_slot_count": active_superseded_value_slot_count,
        "scalar_active_superseded_value_slot_count": (
            scalar_active_superseded_value_slot_count
        ),
        "operation_counts": operation_counts,
        "operation_policy": {
            "create_value_object": (
                "Create a value object from a typed memory only when subject, "
                "predicate, value/text, and source back-pointers are present."
            ),
            "update_value_slot": (
                "Represent newer active and older superseded values inside the "
                "same normalized slot rather than overwriting history."
            ),
            "merge_value_slot": (
                "Merge duplicate normalized values at the slot level while "
                "retaining all source ids for expansion and audit."
            ),
            "supersede_value": (
                "Keep superseded values as archival objects so historical and "
                "previous-state questions can recover them."
            ),
            "retrieve_value": (
                "Expose source-backed, high-confidence value objects as "
                "activation candidates, not as standalone final evidence."
            ),
            "expand_value_source": (
                "Resolve activated value objects back to immutable raw source "
                "rows before answer formation."
            ),
            "verify_value_source": (
                "Check source support, confidence, lifecycle state, and temporal "
                "anchors before a value slot can guide retrieval or compiler "
                "organization."
            ),
            "audit_value_slot": (
                "Audit multi-value, scalar-bearing, active/superseded, and "
                "source-incomplete slots in build artifacts."
            ),
        },
        "object_contract": {
            "value_object_fields": [
                "memory_id",
                "memory_type",
                "subject",
                "predicate",
                "value",
                "scalar_values",
                "status",
                "source_ids",
                "valid_from",
                "valid_to",
                "timestamp",
                "confidence",
                "superseded_by",
            ],
            "slot_scope": "same memory_type, subject, predicate",
            "memory_layers": [
                "short_term_memory",
                "working_memory",
                "long_term_memory",
                "archival_memory",
                "quarantine_memory",
            ],
            "final_evidence_policy": "raw_source_rows",
            "question_independent": True,
        },
        "slot_policy": {
            "source_order_policy": "memory_slot_source_policy_v1",
            "scalar_parser_scope": "record_value_first_then_text",
            "managed_memory_types": sorted(managed_memory_types),
            "raw_evidence_required": True,
        },
        "slot_index": slot_index,
        "slot_samples": slot_index[:24],
        "clean_note": (
            "Question-independent build scalar/value manifest. It organizes "
            "source-backed typed memories into value objects and value slots "
            "with lifecycle, scalar, source-order, and audit signals. It does "
            "not use gold answers, judge outputs, benchmark labels, sample ids, "
            "test feedback, or sample-level rules; final answer evidence still "
            "resolves to raw source rows."
        ),
    }


def _memory_value_slot_keys(
    groups: dict[tuple[str, str, str], list[MemoryRecord]],
) -> tuple[tuple[str, str, str], ...]:
    return tuple(
        key
        for key, records in sorted(groups.items())
        if any(_memory_record_value_object(record) for record in records)
    )


def _memory_record_value_object(record: MemoryRecord) -> str:
    return _clean_text(record.value) or _clean_text(record.text)


def _memory_record_scalar_values(record: MemoryRecord) -> tuple[str, ...]:
    basis = _clean_text(record.value) or _clean_text(record.text)
    if not basis:
        return ()
    values: list[str] = []
    spans: list[tuple[int, int]] = []
    for match in _MEMORY_SCALAR_VALUE_PATTERN.finditer(basis):
        if any(match.start() < end and match.end() > start for start, end in spans):
            continue
        value = _clean_memory_scalar_value_candidate(match.group(0))
        if not value or _looks_like_standalone_year_value(value):
            continue
        spans.append((match.start(), match.end()))
        values.append(value)
        if len(values) >= 6:
            break
    return tuple(dict.fromkeys(values))


def _clean_memory_scalar_value_candidate(value: str) -> str:
    compact = re.sub(r"\s+", " ", str(value or "")).strip(" ,.;:!?")
    if not compact:
        return ""
    if re.fullmatch(
        r"(?:\$\s*)?\d+(?:,\d{3})*(?:\.\d+)?\s*(?:k|m|b|%)?",
        compact,
        flags=re.IGNORECASE,
    ):
        return compact

    parts = compact.split()
    if not parts:
        return ""
    kept = [parts[0]]
    for token in parts[1:]:
        normalized = re.sub(r"^[^\w%$]+|[^\w%$/-]+$", "", token).lower()
        if not normalized or normalized in _MEMORY_SCALAR_UNIT_STOPWORDS:
            break
        if re.fullmatch(r"\d{1,4}", normalized):
            break
        kept.append(token.strip(" ,.;:!?"))
        if len(kept) >= 3:
            break
    return " ".join(part for part in kept if part)


def _looks_like_standalone_year_value(value: str) -> bool:
    normalized = value.strip().replace(",", "")
    if not normalized.isdigit():
        return False
    year = int(normalized)
    return 1900 <= year <= 2099


def _memory_value_slot_operation_hints(
    records: tuple[MemoryRecord, ...],
    *,
    has_scalar_values: bool,
) -> list[str]:
    hints = ["create_value_object", "verify_value_source", "audit_value_slot"]
    if has_scalar_values:
        hints.append("create_scalar_value")
    if any(record.source_ids for record in records):
        hints.append("expand_value_source")
    if any(record.status == "superseded" for record in records):
        hints.extend(["update_value_slot", "supersede_value"])
    if len(
        _ordered_normalized_values(_memory_record_value_object(record) for record in records)
    ) < len(records):
        hints.append("merge_value_slot")
    if any(not record.source_ids or record.confidence < 0.5 for record in records):
        hints.append("quarantine_value")
    return hints


def _memory_state_conflict_manifest(
    groups: dict[tuple[str, str, str], list[MemoryRecord]],
    *,
    managed_memory_types: frozenset[str],
) -> dict[str, Any]:
    """Build-owned state/profile conflict clusters for current-state activation.

    The manifest is deliberately question-independent. It identifies managed
    slots where active and superseded records coexist, keeps source-backed raw
    row orderings for current/historical scopes, and leaves final evidence
    authority to raw source rows.
    """

    clusters: list[dict[str, Any]] = []
    missing_active_source_count = 0
    missing_superseded_source_count = 0
    for key, records in sorted(groups.items()):
        memory_type, subject, predicate = key
        if memory_type not in managed_memory_types:
            continue
        active_records = tuple(record for record in records if record.status == "active")
        superseded_records = tuple(
            record for record in records if record.status == "superseded"
        )
        if not active_records or not superseded_records:
            continue
        active_source_ids = _ordered_strings(
            source_id for record in active_records for source_id in record.source_ids
        )
        superseded_source_ids = _ordered_strings(
            source_id for record in superseded_records for source_id in record.source_ids
        )
        if not active_source_ids:
            missing_active_source_count += 1
        if not superseded_source_ids:
            missing_superseded_source_count += 1
        clusters.append(
            {
                "cluster_id": _slot_id(key),
                "memory_type": memory_type,
                "namespace": _memory_namespace(records[0]) if records else "unknown",
                "subject": subject,
                "predicate": predicate,
                "record_count": len(records),
                "active_memory_ids": [record.memory_id for record in active_records[:8]],
                "superseded_memory_ids": [
                    record.memory_id for record in superseded_records[:8]
                ],
                "active_values": _ordered_normalized_values(
                    record.value or record.text for record in active_records
                )[:8],
                "superseded_values": _ordered_normalized_values(
                    record.value or record.text for record in superseded_records
                )[:8],
                "active_source_order": active_source_ids[:8],
                "superseded_source_order": superseded_source_ids[:8],
                "current_source_order": _memory_slot_policy_source_ids(
                    tuple(records),
                    question_scope="current",
                )[:8],
                "historical_source_order": _memory_slot_policy_source_ids(
                    tuple(records),
                    question_scope="historical",
                )[:8],
                "source_backed": bool(active_source_ids and superseded_source_ids),
                "temporal_anchors": {
                    "active": _ordered_strings(
                        _record_time_value(record) for record in active_records
                    )[:8],
                    "superseded": _ordered_strings(
                        _record_time_value(record) for record in superseded_records
                    )[:8],
                },
            }
        )

    source_backed_clusters = sum(1 for cluster in clusters if cluster["source_backed"])
    return {
        "schema_version": "memory_state_conflict_manifest_v1",
        "trace_only": False,
        "applied": True,
        "cluster_count": len(clusters),
        "source_backed_cluster_count": source_backed_clusters,
        "source_incomplete_cluster_count": max(
            0,
            len(clusters) - source_backed_clusters,
        ),
        "missing_active_source_count": missing_active_source_count,
        "missing_superseded_source_count": missing_superseded_source_count,
        "managed_memory_types": sorted(managed_memory_types),
        "cluster_policy": {
            "slot_scope": "same memory_type, subject, predicate",
            "requires_active_and_superseded": True,
            "requires_managed_memory_type": True,
            "source_order_policy": "memory_slot_source_policy_v1",
            "final_evidence_policy": "raw_source_rows",
        },
        "clusters": clusters[:24],
        "clean_note": (
            "Question-independent build conflict manifest over managed memory "
            "slots. It clusters active/superseded source-backed records so "
            "query modules can consume state lifecycle organization without "
            "using gold answers, judge outputs, benchmark labels, sample ids, "
            "or sample-level rules."
        ),
    }


def _memory_system_tier_manifest(
    records: tuple[MemoryRecord, ...],
    *,
    managed_memory_types: frozenset[str],
) -> dict[str, Any]:
    tier_records: dict[str, list[MemoryRecord]] = defaultdict(list)
    for record in records:
        tier_records[
            _memory_tier(record, managed_memory_types=managed_memory_types)
        ].append(record)

    ordered_tiers = (
        "working_memory",
        "long_term_memory",
        "archival_memory",
        "quarantine_memory",
    )
    record_ids_by_tier = {
        tier: [record.memory_id for record in tier_records.get(tier, ())[:24]]
        for tier in ordered_tiers
    }
    source_counts_by_tier = {
        tier: sum(len(record.source_ids) for record in tier_records.get(tier, ()))
        for tier in ordered_tiers
    }
    return {
        "schema_version": "memory_tier_manifest_v1",
        "trace_only": False,
        "applied": True,
        "tier_order": list(ordered_tiers),
        "tier_counts": {
            tier: len(tier_records.get(tier, ())) for tier in ordered_tiers
        },
        "source_counts_by_tier": source_counts_by_tier,
        "record_ids_by_tier": record_ids_by_tier,
        "tier_policy": {
            "working_memory": (
                "Active state, profile, preference, relationship, and plan "
                "objects that may affect current behavior or unresolved future "
                "intent."
            ),
            "long_term_memory": (
                "Durable source-backed semantic, episodic, and stable profile "
                "objects retained for recall and context organization."
            ),
            "archival_memory": (
                "Closed or superseded objects retained for historical lookup, "
                "conflict chains, and audit."
            ),
            "quarantine_memory": (
                "Low-confidence or source-unbacked objects blocked from normal "
                "activation until audited."
            ),
        },
        "clean_note": (
            "Question-independent memory tier manifest inspired by working/"
            "long-term/archival memory systems. Tiers organize source-backed "
            "memory objects for future activation policies; raw source rows "
            "remain final answer authority."
        ),
    }


def _memory_tier(
    record: MemoryRecord,
    *,
    managed_memory_types: frozenset[str],
) -> str:
    if not record.source_ids or record.confidence < 0.5:
        return "quarantine_memory"
    if record.status == "superseded" or record.superseded_by or record.valid_to:
        return "archival_memory"
    if record.memory_type in managed_memory_types or record.memory_type == "plan":
        return "working_memory"
    return "long_term_memory"


def _memory_system_operation_layer_counts(
    *,
    deduped_records: tuple[MemoryRecord, ...],
    managed_records: tuple[MemoryRecord, ...],
    groups: dict[tuple[str, str, str], list[MemoryRecord]],
    managed_memory_types: frozenset[str],
    supersede_pairs: tuple[dict[str, Any], ...],
    retrieval_ready_records: tuple[MemoryRecord, ...],
) -> dict[str, dict[str, int]]:
    result: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for record in deduped_records:
        result[_memory_layer(record.memory_type)]["create"] += 1
    for pair in supersede_pairs:
        old = pair.get("old")
        new = pair.get("new")
        if isinstance(new, MemoryRecord):
            result[_memory_layer(new.memory_type)]["update"] += 1
        if isinstance(old, MemoryRecord):
            result[_memory_layer(old.memory_type)]["supersede"] += 1
    for record in retrieval_ready_records:
        result[_memory_layer(record.memory_type)]["retrieve"] += 1
    for record in managed_records:
        layer = _memory_layer(record.memory_type)
        if record.source_ids:
            result[layer]["expand"] += len(record.source_ids)
            result[layer]["verify"] += 1
        if not record.source_ids or record.confidence < 0.5:
            result[layer]["quarantine"] += 1
    for key, records in groups.items():
        layer = _memory_layer(key[0])
        result[layer]["audit"] += 1
        if _slot_has_lifecycle(records):
            result[layer]["audit_lifecycle_slot"] += 1
        if key[0] in managed_memory_types and _slot_has_active_superseded_pair(records):
            result[layer]["audit_state_conflict_slot"] += 1
    return {
        layer: dict(sorted(counts.items()))
        for layer, counts in sorted(result.items())
    }


def _memory_slot_source_policy_manifest(
    groups: dict[tuple[str, str, str], list[MemoryRecord]],
    *,
    managed_memory_types: frozenset[str],
) -> dict[str, Any]:
    """Build-side source policy for graph utility slot activation.

    The policy is question-independent: build records current/open and
    historical/closed source preferences for each slot. Query-time graph utility
    only chooses the broad question scope, while final evidence remains raw rows.
    """

    current_ordered_slots = 0
    historical_ordered_slots = 0
    lifecycle_slots = 0
    multi_source_slots = 0
    slot_samples: list[dict[str, Any]] = []
    for key, records in sorted(groups.items()):
        record_tuple = tuple(records)
        current_order = _memory_slot_policy_source_ids(
            record_tuple,
            question_scope="current",
        )
        historical_order = _memory_slot_policy_source_ids(
            record_tuple,
            question_scope="historical",
        )
        if current_order:
            current_ordered_slots += 1
        if historical_order:
            historical_ordered_slots += 1
        if _slot_has_lifecycle(records):
            lifecycle_slots += 1
        source_ids = _ordered_strings(
            source_id for record in records for source_id in record.source_ids
        )
        if len(source_ids) > 1:
            multi_source_slots += 1
        if len(slot_samples) >= 12:
            continue
        memory_type, subject, predicate = key
        slot_samples.append(
            {
                "slot_id": _slot_id(key),
                "memory_type": memory_type,
                "layer": _memory_layer(memory_type),
                "managed": memory_type in managed_memory_types,
                "subject": subject,
                "predicate": predicate,
                "record_count": len(records),
                "current_source_order": current_order[:8],
                "historical_source_order": historical_order[:8],
                "current_memory_order": [
                    record.memory_id
                    for record in sorted(
                        record_tuple,
                        key=lambda item: memory_slot_record_source_policy_sort_key(
                            item,
                            question_scope="current",
                        ),
                    )
                ][:8],
                "historical_memory_order": [
                    record.memory_id
                    for record in sorted(
                        record_tuple,
                        key=lambda item: memory_slot_record_source_policy_sort_key(
                            item,
                            question_scope="historical",
                        ),
                    )
                ][:8],
            }
        )
    return {
        "schema_version": "memory_slot_source_policy_v1",
        "trace_only": False,
        "applied": True,
        "slot_count": len(groups),
        "current_scope_ordered_slot_count": current_ordered_slots,
        "historical_scope_ordered_slot_count": historical_ordered_slots,
        "lifecycle_slot_count": lifecycle_slots,
        "multi_source_slot_count": multi_source_slots,
        "question_scopes": ["current", "historical"],
        "policy": {
            "current_scope": [
                "open_state",
                "event_scoped",
                "active_or_open",
                "closed",
            ],
            "historical_scope": [
                "closed",
                "event_scoped",
                "open_state",
                "active_or_open",
            ],
            "tie_breakers": [
                "source_confidence",
                "temporal_anchor",
                "time_rank",
                "memory_id",
            ],
            "final_evidence_policy": "raw_source_rows",
        },
        "slot_samples": slot_samples,
        "clean_note": (
            "Build-side source policy over source-backed memory slots. It "
            "precomputes current and historical source orderings from validity, "
            "confidence, temporal anchors, lifecycle status, and source ids; "
            "query modules may use only the ordering, while final answer "
            "evidence still resolves to raw source rows."
        ),
    }


def _memory_slot_policy_source_ids(
    records: tuple[MemoryRecord, ...],
    *,
    question_scope: str,
) -> list[str]:
    source_ids: list[str] = []
    for record in sorted(
        records,
        key=lambda item: memory_slot_record_source_policy_sort_key(
            item,
            question_scope=question_scope,
        ),
    ):
        for source_id in record.source_ids:
            if source_id not in source_ids:
                source_ids.append(source_id)
    return source_ids


def memory_slot_record_source_policy_sort_key(
    record: Any,
    *,
    question_scope: str,
) -> tuple[Any, ...]:
    """Sort a source-backed memory record for slot source activation."""

    return (
        _memory_record_validity_rank(record, question_scope=question_scope),
        _memory_record_source_confidence_rank(record),
        _memory_record_temporal_anchor_rank(record),
        *_memory_record_time_rank(record, question_scope=question_scope),
        str(getattr(record, "memory_id", "")),
    )


def _memory_record_validity_rank(record: Any, *, question_scope: str) -> int:
    status = str(getattr(record, "status", "active") or "active").lower()
    memory_type = str(getattr(record, "memory_type", "") or "").lower()
    closed = bool(
        status == "superseded"
        or getattr(record, "superseded_by", None)
        or getattr(record, "valid_to", None)
    )
    event_scoped = bool(getattr(record, "event_time", None))
    open_state = memory_type in _STATEFUL_MEMORY_TYPES and not closed
    if question_scope == "historical":
        if closed:
            return 0
        if event_scoped:
            return 1
        if open_state:
            return 2
        return 3
    if open_state:
        return 0
    if event_scoped:
        return 1
    if not closed:
        return 2
    return 3


def _memory_record_source_confidence_rank(record: Any) -> int:
    if not tuple(getattr(record, "source_ids", ()) or ()):
        return 3
    confidence = float(getattr(record, "confidence", 1.0) or 0.0)
    if confidence >= 0.8:
        return 0
    if confidence >= 0.5:
        return 1
    return 2


def _memory_record_temporal_anchor_rank(record: Any) -> int:
    if (
        getattr(record, "valid_from", None)
        or getattr(record, "valid_to", None)
        or getattr(record, "event_time", None)
        or getattr(record, "mention_time", None)
        or getattr(record, "timestamp", None)
    ):
        return 0
    return 1


def _memory_record_time_rank(record: Any, *, question_scope: str) -> tuple[int, str]:
    time_value = str(
        getattr(record, "valid_from", None)
        or getattr(record, "event_time", None)
        or getattr(record, "timestamp", None)
        or getattr(record, "mention_time", None)
        or ""
    )
    if question_scope == "historical":
        return (0, time_value)
    return (-_sortable_time_digits(time_value), time_value)


def _sortable_time_digits(value: str) -> int:
    digits = "".join(ch for ch in value if ch.isdigit())
    if not digits:
        return 0
    return int(digits[:12])


def _memory_system_governance_manifest(
    records: tuple[MemoryRecord, ...],
    *,
    managed_memory_types: frozenset[str],
) -> dict[str, Any]:
    assessments = [
        _memory_system_record_governance(
            record,
            managed_memory_types=managed_memory_types,
        )
        for record in records
    ]
    risk_counts: dict[str, int] = defaultdict(int)
    activation_role_counts: dict[str, int] = defaultdict(int)
    activation_utility_bucket_counts: dict[str, int] = defaultdict(int)
    temporal_scope_counts: dict[str, int] = defaultdict(int)
    validity_status_counts: dict[str, int] = defaultdict(int)
    source_confidence_bucket_counts: dict[str, int] = defaultdict(int)
    tier_counts: dict[str, int] = defaultdict(int)
    for assessment in assessments:
        activation_role_counts[str(assessment["activation_role"])] += 1
        activation_utility_bucket_counts[
            str(assessment["activation_utility_bucket"])
        ] += 1
        temporal_scope_counts[str(assessment["temporal_scope_kind"])] += 1
        validity_status_counts[str(assessment["validity_status"])] += 1
        source_confidence_bucket_counts[
            str(assessment["source_confidence_bucket"])
        ] += 1
        tier_counts[str(assessment["memory_tier"])] += 1
        for risk in assessment["risk_flags"]:
            risk_counts[str(risk)] += 1
    activation_ready_count = sum(
        1 for assessment in assessments if assessment["source_activation_ready"]
    )
    source_activation_ready_memory_ids = [
        str(assessment["memory_id"])
        for assessment in assessments
        if assessment["source_activation_ready"]
    ]
    activation_blocked_memory_ids = [
        str(assessment["memory_id"])
        for assessment in assessments
        if not assessment["source_activation_ready"]
    ]
    risk_memory_ids = [
        str(assessment["memory_id"])
        for assessment in assessments
        if assessment["risk_flags"]
    ]
    risk_memory_ids_by_flag: dict[str, list[str]] = defaultdict(list)
    for assessment in assessments:
        for risk in assessment["risk_flags"]:
            risk_memory_ids_by_flag[str(risk)].append(str(assessment["memory_id"]))
    activation_priority_memory_ids = [
        str(assessment["memory_id"])
        for assessment in sorted(
            assessments,
            key=_memory_activation_priority_sort_key,
        )
        if assessment["source_activation_ready"]
    ]
    return {
        "schema_version": "memory_system_governance_v2",
        "trace_only": False,
        "applied": True,
        "record_count": len(records),
        "source_activation_ready_record_count": activation_ready_count,
        "raw_evidence_required_record_count": len(records),
        "risk_record_count": sum(
            1 for assessment in assessments if assessment["risk_flags"]
        ),
        "risk_counts": dict(sorted(risk_counts.items())),
        "source_activation_ready_memory_ids": source_activation_ready_memory_ids,
        "activation_blocked_memory_ids": activation_blocked_memory_ids,
        "risk_memory_ids": risk_memory_ids,
        "risk_memory_ids_by_flag": {
            key: value for key, value in sorted(risk_memory_ids_by_flag.items())
        },
        "activation_role_counts": dict(sorted(activation_role_counts.items())),
        "activation_utility_bucket_counts": dict(
            sorted(activation_utility_bucket_counts.items())
        ),
        "temporal_scope_counts": dict(sorted(temporal_scope_counts.items())),
        "validity_status_counts": dict(sorted(validity_status_counts.items())),
        "source_confidence_bucket_counts": dict(
            sorted(source_confidence_bucket_counts.items())
        ),
        "tier_counts": dict(sorted(tier_counts.items())),
        "activation_priority_memory_ids": activation_priority_memory_ids,
        "high_utility_memory_ids": [
            str(assessment["memory_id"])
            for assessment in assessments
            if assessment["source_activation_ready"]
            and assessment["activation_utility_bucket"] == "high"
        ],
        "activation_utility_policy": _memory_activation_utility_policy(),
        "activation_policy": {
            "typed_memory_role": "source_backed_activation_hint",
            "final_answer_evidence": "raw_source_rows",
            "requires_source_ids": True,
            "blocks_unbacked_activation": True,
            "blocks_low_confidence_activation": True,
            "audits_incomplete_slot_keys": True,
            "rank_manifest_available": True,
        },
        "record_samples": assessments[:10],
        "clean_note": (
            "Question-independent governance manifest. Typed memory can be "
            "treated as an activation hint only when it is source-backed and "
            "not low confidence. The manifest also exposes activation role and "
            "utility signals for future retrieval policies, while final answer "
            "evidence must still resolve to raw source rows."
        ),
    }


def _memory_system_record_governance(
    record: MemoryRecord,
    *,
    managed_memory_types: frozenset[str],
) -> dict[str, Any]:
    source_backed = bool(record.source_ids)
    complete_slot_key = bool(record.memory_type and record.subject and record.predicate)
    temporal_anchor = bool(
        record.timestamp
        or record.mention_time
        or record.event_time
        or record.valid_from
        or record.valid_to
    )
    lifecycle_signal = bool(
        record.status == "superseded" or record.superseded_by or record.valid_to
    )
    confidence_bucket = _confidence_bucket(record.confidence)
    temporal_scope_kind = _temporal_scope_kind(record)
    validity_status = _validity_status(record, managed_memory_types=managed_memory_types)
    source_confidence_bucket = _source_confidence_bucket(record)
    memory_tier = _memory_tier(record, managed_memory_types=managed_memory_types)
    risk_flags: list[str] = []
    if not source_backed:
        risk_flags.append("unbacked")
    if record.confidence < 0.5:
        risk_flags.append("low_confidence")
    if not complete_slot_key:
        risk_flags.append("incomplete_slot_key")
    if (
        record.memory_type in managed_memory_types
        and record.status == "active"
        and not temporal_anchor
    ):
        risk_flags.append("managed_active_without_temporal_anchor")
    source_activation_ready = source_backed and record.confidence >= 0.5
    activation_utility = _memory_activation_utility(
        record,
        source_backed=source_backed,
        complete_slot_key=complete_slot_key,
        temporal_anchor=temporal_anchor,
        lifecycle_signal=lifecycle_signal,
        source_activation_ready=source_activation_ready,
        managed_memory_types=managed_memory_types,
    )
    return {
        "memory_id": record.memory_id,
        "memory_type": record.memory_type,
        "namespace": _memory_namespace(record),
        "layer": _memory_layer(record.memory_type),
        "status": record.status,
        "memory_tier": memory_tier,
        "source_activation_ready": source_activation_ready,
        "raw_evidence_required": True,
        "source_backed": source_backed,
        "complete_slot_key": complete_slot_key,
        "temporal_anchor": temporal_anchor,
        "temporal_scope_kind": temporal_scope_kind,
        "validity_status": validity_status,
        "source_confidence_bucket": source_confidence_bucket,
        "lifecycle_signal": lifecycle_signal,
        "confidence_bucket": confidence_bucket,
        "activation_role": activation_utility["role"],
        "activation_utility_score": activation_utility["score"],
        "activation_utility_bucket": activation_utility["bucket"],
        "activation_utility_reasons": activation_utility["reasons"],
        "risk_flags": tuple(risk_flags),
        "source_ids": list(record.source_ids[:6]),
        "valid_from": record.valid_from,
        "valid_to": record.valid_to,
        "slot_key": {
            "subject": _normalize_key_text(record.subject),
            "predicate": _normalize_key_text(record.predicate),
        },
    }


def _temporal_scope_kind(record: MemoryRecord) -> str:
    if record.valid_from or record.valid_to:
        return "validity_interval"
    if record.event_time:
        return "event_time"
    if record.mention_time:
        return "mention_time"
    if record.timestamp:
        return "record_timestamp"
    return "unanchored"


def _validity_status(
    record: MemoryRecord,
    *,
    managed_memory_types: frozenset[str],
) -> str:
    if record.status == "superseded" or record.superseded_by or record.valid_to:
        return "closed"
    if record.memory_type in managed_memory_types:
        if record.valid_from or record.timestamp or record.mention_time:
            return "open"
        return "open_unanchored"
    if record.event_time:
        return "event_scoped"
    return "not_applicable"


def _source_confidence_bucket(record: MemoryRecord) -> str:
    if not record.source_ids:
        return "unbacked"
    return _confidence_bucket(record.confidence)


def _memory_activation_utility_policy() -> dict[str, Any]:
    return {
        "schema_version": "memory_activation_utility_v1",
        "score_weights": {
            "source_backed": 3,
            "high_confidence": 2,
            "medium_confidence": 1,
            "low_confidence": -4,
            "complete_slot_key": 1,
            "value_or_text": 1,
            "temporal_anchor": 1,
            "multi_source": 1,
            "active": 1,
            "lifecycle_signal": 1,
            "managed_memory_type": 1,
        },
        "bucket_thresholds": {
            "high": 9,
            "medium": 6,
            "low": 0,
        },
        "role_order": [
            "stateful_candidate",
            "semantic_candidate",
            "episodic_candidate",
            "prospective_candidate",
            "lifecycle_context",
            "general_candidate",
            "blocked",
        ],
        "tier_order": [
            "working_memory",
            "long_term_memory",
            "archival_memory",
            "quarantine_memory",
        ],
        "clean_note": (
            "Question-independent activation utility over typed memory metadata. "
            "It uses source support, confidence, slot completeness, temporal "
            "anchors, lifecycle state, memory type, and memory tier only."
        ),
    }


def _memory_activation_utility(
    record: MemoryRecord,
    *,
    source_backed: bool,
    complete_slot_key: bool,
    temporal_anchor: bool,
    lifecycle_signal: bool,
    source_activation_ready: bool,
    managed_memory_types: frozenset[str],
) -> dict[str, Any]:
    weights = _memory_activation_utility_policy()["score_weights"]
    score = 0
    reasons: list[str] = []

    def add(reason: str) -> None:
        nonlocal score
        score += int(weights[reason])
        reasons.append(reason)

    if source_backed:
        add("source_backed")
    if record.confidence >= 0.8:
        add("high_confidence")
    elif record.confidence >= 0.5:
        add("medium_confidence")
    else:
        add("low_confidence")
    if complete_slot_key:
        add("complete_slot_key")
    if record.value or record.text:
        add("value_or_text")
    if temporal_anchor:
        add("temporal_anchor")
    if len(record.source_ids) > 1:
        add("multi_source")
    if record.status == "active":
        add("active")
    if lifecycle_signal:
        add("lifecycle_signal")
    if record.memory_type in managed_memory_types:
        add("managed_memory_type")

    role = _memory_activation_role(
        record,
        source_activation_ready=source_activation_ready,
        lifecycle_signal=lifecycle_signal,
    )
    bucket = _memory_activation_utility_bucket(
        score,
        source_activation_ready=source_activation_ready,
    )
    return {
        "role": role,
        "score": score,
        "bucket": bucket,
        "reasons": tuple(reasons),
    }


def _memory_activation_role(
    record: MemoryRecord,
    *,
    source_activation_ready: bool,
    lifecycle_signal: bool,
) -> str:
    if not source_activation_ready:
        return "blocked"
    if lifecycle_signal or record.status == "superseded":
        return "lifecycle_context"
    if record.memory_type in _STATEFUL_MEMORY_TYPES:
        return "stateful_candidate"
    if record.memory_type == "fact":
        return "semantic_candidate"
    if record.memory_type == "event":
        return "episodic_candidate"
    if record.memory_type == "plan":
        return "prospective_candidate"
    return "general_candidate"


def _memory_activation_utility_bucket(
    score: int,
    *,
    source_activation_ready: bool,
) -> str:
    if not source_activation_ready:
        return "blocked"
    thresholds = _memory_activation_utility_policy()["bucket_thresholds"]
    if score >= int(thresholds["high"]):
        return "high"
    if score >= int(thresholds["medium"]):
        return "medium"
    return "low"


def _memory_activation_priority_sort_key(assessment: dict[str, Any]) -> tuple[Any, ...]:
    policy = _memory_activation_utility_policy()
    role_order = {
        role: index
        for index, role in enumerate(policy["role_order"])
    }
    tier_order = {
        tier: index
        for index, tier in enumerate(policy.get("tier_order") or ())
    }
    role = str(assessment.get("activation_role") or "")
    tier = str(assessment.get("memory_tier") or "")
    status = str(assessment.get("status") or "")
    return (
        -int(assessment.get("activation_utility_score") or 0),
        tier_order.get(tier, 99),
        role_order.get(role, 99),
        0 if status == "active" else 1,
        str(assessment.get("memory_type") or ""),
        str(assessment.get("memory_id") or ""),
    )


def _confidence_bucket(confidence: float) -> str:
    if confidence >= 0.8:
        return "high"
    if confidence >= 0.5:
        return "medium"
    return "low"


def _memory_system_source_quality(
    records: tuple[MemoryRecord, ...],
    *,
    managed_memory_types: frozenset[str],
) -> dict[str, Any]:
    source_counts = [len(record.source_ids) for record in records]
    confidence_buckets = {"high": 0, "medium": 0, "low": 0}
    temporal_scope_counts: dict[str, int] = defaultdict(int)
    validity_status_counts: dict[str, int] = defaultdict(int)
    source_confidence_bucket_counts: dict[str, int] = defaultdict(int)
    for record in records:
        if record.confidence >= 0.8:
            confidence_buckets["high"] += 1
        elif record.confidence >= 0.5:
            confidence_buckets["medium"] += 1
        else:
            confidence_buckets["low"] += 1
        temporal_scope_counts[_temporal_scope_kind(record)] += 1
        validity_status_counts[
            _validity_status(
                record,
                managed_memory_types=managed_memory_types,
            )
        ] += 1
        source_confidence_bucket_counts[_source_confidence_bucket(record)] += 1

    source_backed_count = sum(1 for count in source_counts if count > 0)
    complete_slot_key_count = sum(
        1
        for record in records
        if record.memory_type and record.subject and record.predicate
    )
    value_backed_count = sum(1 for record in records if record.value or record.text)
    temporal_anchor_count = sum(
        1
        for record in records
        if record.timestamp
        or record.mention_time
        or record.event_time
        or record.valid_from
        or record.valid_to
    )
    lifecycle_signal_count = sum(
        1
        for record in records
        if record.status == "superseded" or record.superseded_by or record.valid_to
    )
    return {
        "record_count": len(records),
        "source_backed_record_count": source_backed_count,
        "source_unbacked_record_count": max(0, len(records) - source_backed_count),
        "single_source_record_count": sum(1 for count in source_counts if count == 1),
        "multi_source_record_count": sum(1 for count in source_counts if count > 1),
        "complete_slot_key_record_count": complete_slot_key_count,
        "value_backed_record_count": value_backed_count,
        "temporal_anchor_record_count": temporal_anchor_count,
        "lifecycle_signal_record_count": lifecycle_signal_count,
        "low_confidence_record_count": confidence_buckets["low"],
        "confidence_buckets": confidence_buckets,
        "temporal_scope_counts": dict(sorted(temporal_scope_counts.items())),
        "validity_status_counts": dict(sorted(validity_status_counts.items())),
        "source_confidence_bucket_counts": dict(
            sorted(source_confidence_bucket_counts.items())
        ),
        "avg_sources_per_record": (
            sum(source_counts) / len(source_counts) if source_counts else 0.0
        ),
    }


def _memory_system_slot_quality(
    groups: dict[tuple[str, str, str], list[MemoryRecord]],
    *,
    managed_memory_types: frozenset[str],
) -> dict[str, Any]:
    source_backed_slot_count = 0
    complete_value_slot_count = 0
    active_superseded_pair_count = 0
    managed_lifecycle_slot_count = 0
    collection_slot_count = 0
    multi_source_slot_count = 0
    for key, records in groups.items():
        active_values = _ordered_normalized_values(
            record.value or record.text
            for record in records
            if record.status == "active"
        )
        superseded_values = _ordered_normalized_values(
            record.value or record.text
            for record in records
            if record.status == "superseded"
        )
        source_ids = _ordered_strings(
            source_id for record in records for source_id in record.source_ids
        )
        if source_ids:
            source_backed_slot_count += 1
        if any(record.value or record.text for record in records):
            complete_value_slot_count += 1
        if active_values and superseded_values:
            active_superseded_pair_count += 1
        if _slot_has_lifecycle(records):
            if key[0] in managed_memory_types:
                managed_lifecycle_slot_count += 1
            else:
                collection_slot_count += 1
        if len(source_ids) > 1:
            multi_source_slot_count += 1
    return {
        "slot_count": len(groups),
        "source_backed_slot_count": source_backed_slot_count,
        "source_unbacked_slot_count": max(0, len(groups) - source_backed_slot_count),
        "complete_value_slot_count": complete_value_slot_count,
        "managed_lifecycle_slot_count": managed_lifecycle_slot_count,
        "collection_slot_count": collection_slot_count,
        "active_superseded_pair_slot_count": active_superseded_pair_count,
        "multi_source_slot_count": multi_source_slot_count,
    }


def _memory_namespace(record: MemoryRecord) -> str:
    layer = _memory_layer(record.memory_type)
    if layer == "profile_state":
        return "long_term_profile_state"
    if layer == "semantic":
        return "long_term_semantic"
    if layer == "episodic":
        return "long_term_episodic"
    if layer == "prospective":
        return "prospective"
    return "unknown"


def _slot_has_lifecycle(records: list[MemoryRecord]) -> bool:
    values = {
        _normalize_key_text(record.value or record.text)
        for record in records
        if record.value or record.text
    }
    statuses = {record.status for record in records}
    return "superseded" in statuses or len(values) > 1


def _slot_has_active_superseded_pair(
    records: tuple[MemoryRecord, ...] | list[MemoryRecord],
) -> bool:
    statuses = {record.status for record in records}
    return "active" in statuses and "superseded" in statuses


def _record_time_value(record: MemoryRecord) -> str:
    return str(
        record.valid_from
        or record.event_time
        or record.timestamp
        or record.mention_time
        or record.valid_to
        or ""
    )


def _memory_object_sample(
    record: MemoryRecord,
    *,
    managed_memory_types: frozenset[str],
) -> dict[str, Any]:
    return {
        "memory_id": record.memory_id,
        "memory_type": record.memory_type,
        "namespace": _memory_namespace(record),
        "layer": _memory_layer(record.memory_type),
        "memory_tier": _memory_tier(
            record,
            managed_memory_types=managed_memory_types,
        ),
        "status": record.status,
        "subject": _normalize_key_text(record.subject),
        "predicate": _normalize_key_text(record.predicate),
        "value": _normalize_key_text(record.value or record.text)[:160],
        "source_ids": list(record.source_ids[:6]),
        "valid_from": record.valid_from,
        "valid_to": record.valid_to,
        "temporal_scope_kind": _temporal_scope_kind(record),
        "validity_status": _validity_status(
            record,
            managed_memory_types=managed_memory_types,
        ),
        "source_confidence_bucket": _source_confidence_bucket(record),
        "superseded_by": record.superseded_by,
    }


def _memory_system_slot_sample(
    key: tuple[str, str, str],
    records: tuple[MemoryRecord, ...],
) -> dict[str, Any]:
    memory_type, subject, predicate = key
    active_values = _ordered_normalized_values(
        record.value or record.text
        for record in records
        if record.status == "active"
    )
    superseded_values = _ordered_normalized_values(
        record.value or record.text
        for record in records
        if record.status == "superseded"
    )
    return {
        "slot_id": _slot_id(key),
        "memory_type": memory_type,
        "namespace": _memory_namespace(records[0]) if records else "unknown",
        "layer": _memory_layer(memory_type),
        "subject": subject,
        "predicate": predicate,
        "record_count": len(records),
        "active_value_count": len(active_values),
        "superseded_value_count": len(superseded_values),
        "active_values": active_values[:4],
        "superseded_values": superseded_values[:4],
        "memory_ids": [record.memory_id for record in records[:8]],
        "source_ids": _ordered_strings(
            source_id for record in records for source_id in record.source_ids
        )[:8],
    }


def _memory_system_operation_edge_samples(
    *,
    managed_records: tuple[MemoryRecord, ...],
    merge_groups: tuple[dict[str, Any], ...],
    supersede_pairs: tuple[dict[str, Any], ...],
) -> dict[str, list[dict[str, Any]]]:
    return {
        "source_support": [
            {
                "operation": "source_support",
                "memory_id": record.memory_id,
                "source_ids": list(record.source_ids[:6]),
            }
            for record in managed_records[:6]
            if record.source_ids
        ],
        "merge": [
            _memory_system_merge_edge_sample(group) for group in merge_groups[:6]
        ],
        "supersede": [
            _memory_system_supersede_edge_sample(pair)
            for pair in supersede_pairs[:6]
        ],
    }


def _memory_system_merge_edge_sample(group: dict[str, Any]) -> dict[str, Any]:
    kept = group.get("kept")
    merged = tuple(group.get("merged") or ())
    if not isinstance(kept, MemoryRecord):
        return {"operation": "merge", "reason": "invalid_sample"}
    return {
        "operation": "merge",
        "kept_memory_id": kept.memory_id,
        "merged_memory_ids": [
            record.memory_id for record in merged if isinstance(record, MemoryRecord)
        ][:8],
        "reason": "duplicate_normalized_text_and_sources",
    }


def _memory_system_supersede_edge_sample(pair: dict[str, Any]) -> dict[str, Any]:
    old = pair.get("old")
    new = pair.get("new")
    if not isinstance(old, MemoryRecord) or not isinstance(new, MemoryRecord):
        return {"operation": "supersede", "reason": "invalid_sample"}
    return {
        "operation": "supersede",
        "old_memory_id": old.memory_id,
        "new_memory_id": new.memory_id,
        "old_value": _normalize_key_text(old.value or old.text)[:160],
        "new_value": _normalize_key_text(new.value or new.text)[:160],
        "valid_to": new.valid_from or new.timestamp,
        "reason": "newer_managed_slot_value",
    }


def _slot_id(key: tuple[str, str, str]) -> str:
    digest = hashlib.sha256()
    digest.update("|".join(key).encode("utf-8"))
    return f"slot_{digest.hexdigest()[:12]}"


def _layer_operation_counts(
    *,
    deduped_records: tuple[MemoryRecord, ...],
    managed_records: tuple[MemoryRecord, ...],
    supersede_pairs: tuple[dict[str, Any], ...],
) -> dict[str, dict[str, int]]:
    result: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for record in deduped_records:
        result[_memory_layer(record.memory_type)]["create"] += 1
    for record in managed_records:
        operation = (
            "retain_superseded"
            if record.status == "superseded"
            else "retain_active"
        )
        result[_memory_layer(record.memory_type)][operation] += 1
    for pair in supersede_pairs:
        old = pair.get("old")
        if isinstance(old, MemoryRecord):
            result[_memory_layer(old.memory_type)]["supersede"] += 1
    return {
        layer: dict(sorted(counts.items()))
        for layer, counts in sorted(result.items())
    }


def _operation_sample(operation: str, record: MemoryRecord) -> dict[str, Any]:
    return {
        "operation": operation,
        "memory_id": record.memory_id,
        "memory_type": record.memory_type,
        "layer": _memory_layer(record.memory_type),
        "status": record.status,
        "subject": _normalize_key_text(record.subject),
        "predicate": _normalize_key_text(record.predicate),
        "value": _normalize_key_text(record.value or record.text)[:160],
        "source_ids": list(record.source_ids[:6]),
    }


def _merge_operation_sample(group: dict[str, Any]) -> dict[str, Any]:
    kept = group.get("kept")
    merged = tuple(group.get("merged") or ())
    if not isinstance(kept, MemoryRecord):
        return {"operation": "merge", "reason": "invalid_sample"}
    sample = _operation_sample("merge", kept)
    sample["merged_memory_ids"] = [
        record.memory_id for record in merged if isinstance(record, MemoryRecord)
    ][:6]
    sample["reason"] = "duplicate_normalized_text_and_sources"
    return sample


def _supersede_operation_sample(pair: dict[str, Any]) -> dict[str, Any]:
    old = pair.get("old")
    new = pair.get("new")
    if not isinstance(old, MemoryRecord) or not isinstance(new, MemoryRecord):
        return {"operation": "supersede", "reason": "invalid_sample"}
    sample = _operation_sample("supersede", old)
    sample["superseded_by"] = new.memory_id
    sample["new_value"] = _normalize_key_text(new.value or new.text)[:160]
    sample["valid_to"] = new.valid_from or new.timestamp
    sample["reason"] = "newer_managed_slot_value"
    return sample


def _slot_operation_sample(
    operation: str,
    key: tuple[str, str, str],
    group: tuple[MemoryRecord, ...],
) -> dict[str, Any]:
    memory_type, subject, predicate = key
    return {
        "operation": operation,
        "memory_type": memory_type,
        "layer": _memory_layer(memory_type),
        "subject": subject,
        "predicate": predicate,
        "record_count": len(group),
        "active_value_count": len(
            {
                _normalize_key_text(record.value or record.text)
                for record in group
                if record.status == "active" and (record.value or record.text)
            }
        ),
        "superseded_value_count": len(
            {
                _normalize_key_text(record.value or record.text)
                for record in group
                if record.status == "superseded" and (record.value or record.text)
            }
        ),
        "source_ids": _ordered_strings(
            source_id for record in group for source_id in record.source_ids
        )[:8],
    }


def _memory_object_graph_summary(
    groups: dict[tuple[str, str, str], list[MemoryRecord]],
    *,
    managed_memory_types: frozenset[str],
) -> dict[str, Any]:
    """Trace-only source-backed object/slot view over managed memories."""

    slot_count = 0
    lifecycle_slot_count = 0
    collection_slot_count = 0
    conflict_slot_count = 0
    multi_value_active_slot_count = 0
    source_backed_slot_count = 0
    layer_counts: dict[str, int] = defaultdict(int)
    slot_samples: list[dict[str, Any]] = []

    for key, records in sorted(groups.items()):
        memory_type, subject, predicate = key
        active_values = _ordered_normalized_values(
            record.value or record.text
            for record in records
            if record.status == "active"
        )
        superseded_values = _ordered_normalized_values(
            record.value or record.text
            for record in records
            if record.status == "superseded"
        )
        all_values = _ordered_normalized_values(
            record.value or record.text for record in records
        )
        active_source_ids = _ordered_strings(
            source_id
            for record in records
            if record.status == "active"
            for source_id in record.source_ids
        )
        superseded_source_ids = _ordered_strings(
            source_id
            for record in records
            if record.status == "superseded"
            for source_id in record.source_ids
        )
        source_ids = _ordered_strings(
            source_id for record in records for source_id in record.source_ids
        )
        has_lifecycle = bool(superseded_values) or len(all_values) > 1
        is_managed = memory_type in managed_memory_types
        if has_lifecycle and is_managed:
            slot_kind = "managed_lifecycle"
            lifecycle_slot_count += 1
        elif has_lifecycle:
            slot_kind = "collection_multi_value"
            collection_slot_count += 1
        else:
            slot_kind = "single_value"
        if active_values and superseded_values:
            conflict_slot_count += 1
        if len(active_values) > 1:
            multi_value_active_slot_count += 1
        if source_ids:
            source_backed_slot_count += 1
        layer = _memory_layer(memory_type)
        layer_counts[layer] += 1
        slot_count += 1
        if len(slot_samples) < 12:
            slot_samples.append(
                {
                    "memory_type": memory_type,
                    "layer": layer,
                    "slot_kind": slot_kind,
                    "subject": subject,
                    "predicate": predicate,
                    "record_count": len(records),
                    "active_value_count": len(active_values),
                    "superseded_value_count": len(superseded_values),
                    "source_count": len(source_ids),
                    "active_values": active_values[:4],
                    "superseded_values": superseded_values[:4],
                    "active_source_ids": active_source_ids[:6],
                    "superseded_source_ids": superseded_source_ids[:6],
                }
            )

    return {
        "trace_only": True,
        "slot_count": slot_count,
        "managed_lifecycle_slot_count": lifecycle_slot_count,
        "collection_multi_value_slot_count": collection_slot_count,
        "conflict_slot_count": conflict_slot_count,
        "multi_value_active_slot_count": multi_value_active_slot_count,
        "source_backed_slot_count": source_backed_slot_count,
        "layer_counts": dict(sorted(layer_counts.items())),
        "slots": slot_samples,
        "clean_note": (
            "Trace-only build-stage object graph. Slots are grouped from "
            "source-backed typed memory records by memory_type, subject, and "
            "predicate; the graph is not used by retrieval, compiler, answer, "
            "repair, finalizer, or cache keys."
        ),
    }


def _ordered_normalized_values(values: Any) -> list[str]:
    return _ordered_strings(
        _normalize_key_text(value) for value in values if _normalize_key_text(value)
    )


def _ordered_strings(values: Any) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = str(value or "").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


def _memory_layer(memory_type: str) -> str:
    if memory_type in {"event"}:
        return "episodic"
    if memory_type in {"preference", "profile", "relationship", "state"}:
        return "profile_state"
    if memory_type in {"plan"}:
        return "prospective"
    if memory_type in {"fact"}:
        return "semantic"
    return "unknown"


def _message_text(message: dict[str, Any]) -> str:
    for key in ("content", "reasoning", "reasoning_content"):
        value = message.get(key)
        if value is not None:
            return str(value)
    return ""


def _temporal_field_prompt_lines(enabled: bool) -> list[str]:
    if not enabled:
        return [
            "Return ONLY valid JSON with this schema:",
            '{"records":[{"type":"event|fact|preference|profile|state|relationship|plan","text":"short memory","subject":"","predicate":"","value":"","source_ids":["..."],"timestamp":"YYYY-MM-DD or null","entities":["..."],"confidence":0.0}]}',
        ]
    return [
        "Track time with separate fields when possible:",
        "- mention_time: when the supporting turn was said or recorded; usually the turn time.",
        "- event_time: when the described event/action happened, or the explicit/resolved time span in the turn text.",
        "- valid_from / valid_to: when a state, preference, profile fact, or relationship became true and stopped being true; leave valid_to null if still open.",
        "- For one-time events, use event_time and leave valid_from/valid_to null unless the text describes an ongoing state created by that event.",
        "- For event, fact, or plan records, do not use valid_from/valid_to to restate event_time; if the memory is ongoing, classify it as state, profile, preference, or relationship.",
        "- For generic background facts, public schedules, seasonal advice, or examples not tied to the speaker's own memory, do not create a validity interval; keep valid_from/valid_to null.",
        "- timestamp: the best primary time for sorting this record; use event_time when it is known, otherwise mention_time.",
        "Resolve common relative phrases such as yesterday, last week, last Friday, next month, a few years ago, and two weeks ago against the supporting turn time.",
        "Do not infer a time from unrelated turns; leave event_time null when the event time is not stated or resolvable.",
        "Return ONLY valid JSON with this schema:",
        '{"records":[{"type":"event|fact|preference|profile|state|relationship|plan","text":"short memory","subject":"","predicate":"","value":"","source_ids":["..."],"timestamp":"YYYY-MM-DD or null","mention_time":"YYYY-MM-DD or null","event_time":"YYYY-MM-DD, time span, duration, or null","valid_from":"YYYY-MM-DD, time span, or null","valid_to":"YYYY-MM-DD, time span, or null","entities":["..."],"confidence":0.0}]}',
    ]


def _tuple_of_strings(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value.strip(),) if value.strip() else ()
    if not isinstance(value, list):
        return ()
    result = []
    for item in value:
        text = str(item).strip()
        if text:
            result.append(text)
    return tuple(dict.fromkeys(result))


def _clean_text(value: Any) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def _safe_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _first_timestamp(
    source_ids: tuple[str, ...],
    timestamp_by_source_id: dict[str, str | None],
) -> str:
    for source_id in source_ids:
        timestamp = timestamp_by_source_id.get(source_id)
        if timestamp:
            return timestamp
    return ""


def _normalize_key_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


def _memory_id(
    memory_type: str,
    text: str,
    source_ids: tuple[str, ...],
    chunk_index: int,
    ordinal: int,
) -> str:
    digest = hashlib.sha256()
    digest.update(memory_type.encode("utf-8"))
    digest.update(b"\0")
    digest.update(text.encode("utf-8"))
    digest.update(b"\0")
    digest.update("|".join(source_ids).encode("utf-8"))
    return f"mem_{chunk_index:04d}_{ordinal:04d}_{digest.hexdigest()[:12]}"


def _cache_key(
    namespace: str,
    model: str,
    max_tokens: int,
    max_records_per_chunk: int,
    prompt: str,
) -> str:
    digest = hashlib.sha256()
    digest.update(namespace.encode("utf-8"))
    digest.update(b"\0")
    digest.update(model.encode("utf-8"))
    digest.update(b"\0")
    digest.update(str(max_tokens).encode("utf-8"))
    digest.update(b"\0")
    digest.update(str(max_records_per_chunk).encode("utf-8"))
    digest.update(b"\0")
    digest.update(prompt.encode("utf-8"))
    return digest.hexdigest()


def _cache_stats_delta(
    before: BuildMemoryCacheStats,
    after: BuildMemoryCacheStats,
) -> BuildMemoryCacheStats:
    return BuildMemoryCacheStats(
        hits=after.hits - before.hits,
        misses=after.misses - before.misses,
        writes=after.writes - before.writes,
    )


def _truncate(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[: max(0, max_chars - 3)].rstrip() + "..."
