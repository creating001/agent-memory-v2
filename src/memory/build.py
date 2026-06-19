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
    """Trace-only memory system graph over source-backed build memory.

    The graph is intentionally conservative: it describes memory objects,
    source spans, lifecycle slots, and operation edges, but it does not feed
    retrieval, compiler, answer, repair, finalizer, or cache construction.
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
    for record in managed_records:
        namespace_counts[_memory_namespace(record)] += 1
        lifecycle_counts[record.status] += 1
        layer_counts[_memory_layer(record.memory_type)] += 1

    slot_member_edges = sum(len(records) for records in groups.values())
    source_support_edges = sum(len(record.source_ids) for record in managed_records)
    operation_edge_counts = {
        "create": len(deduped_records),
        "merge": sum(len(group.get("merged") or ()) for group in merge_groups),
        "supersede": len(supersede_pairs),
        "source_support": source_support_edges,
        "slot_member": slot_member_edges,
        "verify_source_backed": sum(
            1 for record in managed_records if record.source_ids
        ),
        "audit_slot": len(groups),
    }

    return {
        "enabled": True,
        "trace_only": True,
        "applied": True,
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
        "lifecycle_counts": dict(sorted(lifecycle_counts.items())),
        "operation_edge_counts": operation_edge_counts,
        "memory_object_samples": [
            _memory_object_sample(record) for record in managed_records[:10]
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
            "Trace-only build memory system graph. It organizes source-backed "
            "typed memories into namespaces, lifecycle states, object slots, "
            "source-support edges, merge edges, and supersede edges. It is not "
            "used by retrieval, compiler, answer, repair, finalizer, or cache "
            "keys."
        ),
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


def _memory_object_sample(record: MemoryRecord) -> dict[str, Any]:
    return {
        "memory_id": record.memory_id,
        "memory_type": record.memory_type,
        "namespace": _memory_namespace(record),
        "layer": _memory_layer(record.memory_type),
        "status": record.status,
        "subject": _normalize_key_text(record.subject),
        "predicate": _normalize_key_text(record.predicate),
        "value": _normalize_key_text(record.value or record.text)[:160],
        "source_ids": list(record.source_ids[:6]),
        "valid_from": record.valid_from,
        "valid_to": record.valid_to,
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
