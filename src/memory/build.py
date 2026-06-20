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
        memory_working_view: bool = True,
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
        self._memory_working_view = memory_working_view
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
                    include_memory_working_view=self._memory_working_view,
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
                include_memory_working_view=self._memory_working_view,
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
    include_memory_working_view: bool = True,
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
            include_memory_working_view=include_memory_working_view,
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
    include_memory_working_view: bool = True,
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
        include_working_memory_view=include_memory_working_view,
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
            "working_memory_view",
            "lifecycle_audit",
            "memory_layer_manifest",
            "memory_operation_api",
            "memory_operation_lifecycle",
            "memory_system_state",
            "memory_operation_journal",
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
            "build_owned_working_memory_view",
            "build_owned_lifecycle_audit",
            "build_owned_memory_layer_manifest",
            "build_owned_memory_operation_api",
            "build_owned_memory_operation_lifecycle",
            "build_owned_memory_system_state",
            "build_owned_memory_operation_journal",
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
    include_working_memory_view: bool = True,
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
    working_memory_view = (
        _memory_working_memory_view(operation_registry)
        if include_working_memory_view
        else _disabled_memory_working_memory_view()
    )
    lifecycle_audit = _memory_lifecycle_audit(
        operation_registry=operation_registry,
        working_memory_view=working_memory_view,
    )
    layer_manifest = _memory_layer_manifest(
        lifecycle_audit=lifecycle_audit,
    )
    operation_api = _memory_operation_api(
        lifecycle_audit=lifecycle_audit,
        layer_manifest=layer_manifest,
    )
    context_interface = _memory_context_interface(
        lifecycle_audit=lifecycle_audit,
        layer_manifest=layer_manifest,
        operation_api=operation_api,
    )
    operation_lifecycle = _memory_operation_lifecycle(
        operation_api=operation_api,
        context_interface=context_interface,
    )
    working_compiler_plan = _memory_working_memory_compiler_plan(
        context_interface=context_interface,
        operation_lifecycle=operation_lifecycle,
        layer_manifest=layer_manifest,
    )
    memory_system_state = _memory_system_state(
        context_interface=context_interface,
        operation_lifecycle=operation_lifecycle,
        working_compiler_plan=working_compiler_plan,
        layer_manifest=layer_manifest,
    )
    operation_journal = _memory_operation_journal(
        memory_system_state=memory_system_state,
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
        "working_memory_view_entry_count": working_memory_view["entry_count"],
        "working_memory_view_source_backed_entry_count": (
            working_memory_view["source_backed_entry_count"]
        ),
        "lifecycle_audit_entry_count": lifecycle_audit["entry_count"],
        "lifecycle_audit_source_backed_entry_count": (
            lifecycle_audit["source_backed_entry_count"]
        ),
        "lifecycle_audit_conflict_entry_count": lifecycle_audit[
            "conflict_entry_count"
        ],
        "layer_manifest_layer_count": layer_manifest["layer_count"],
        "layer_manifest_entry_count": layer_manifest["entry_count"],
        "layer_manifest_source_backed_entry_count": (
            layer_manifest["source_backed_entry_count"]
        ),
        "operation_api_entry_count": operation_api["entry_count"],
        "operation_api_source_backed_entry_count": (
            operation_api["source_backed_entry_count"]
        ),
        "operation_api_anchor_source_count": (
            operation_api["context_anchor_source_count"]
        ),
        "context_interface_role_count": context_interface["role_count"],
        "context_interface_anchor_source_count": (
            context_interface["context_anchor_source_count"]
        ),
        "context_interface_operation_slot_count": (
            context_interface["operation_slot_count"]
        ),
        "operation_lifecycle_entry_count": operation_lifecycle["entry_count"],
        "operation_lifecycle_source_backed_entry_count": (
            operation_lifecycle["source_backed_entry_count"]
        ),
        "working_compiler_plan_entry_count": working_compiler_plan["entry_count"],
        "working_compiler_plan_source_backed_entry_count": (
            working_compiler_plan["source_backed_entry_count"]
        ),
        "working_compiler_plan_context_slot_count": (
            working_compiler_plan["context_interface_slot_count"]
        ),
        "memory_system_state_entry_count": memory_system_state["entry_count"],
        "memory_system_state_source_backed_entry_count": (
            memory_system_state["source_backed_entry_count"]
        ),
        "memory_system_state_layer_count": memory_system_state["layer_count"],
        "memory_operation_journal_entry_count": operation_journal["entry_count"],
        "memory_operation_journal_source_backed_entry_count": (
            operation_journal["source_backed_entry_count"]
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
            "working_memory_view_contract": {
                "view_field": "working_memory_view",
                "schema_version": "memory_working_view_v1",
                "layers": list(_memory_working_view_layer_contract().keys()),
                "policy": (
                    "query compiler consumes source-backed workspace entries; "
                    "short-term memory is supplied by visible raw rows at query time"
                ),
            },
            "lifecycle_audit_contract": {
                "audit_field": "lifecycle_audit",
                "schema_version": "memory_lifecycle_audit_v1",
                "source": "working_memory_view_or_operation_registry",
                "operations": _memory_working_view_operation_contract(),
                "policy": (
                    "audit state, conflict, source, and operation readiness; "
                    "final evidence still expands to raw source rows"
                ),
            },
            "layer_manifest_contract": {
                "manifest_field": "memory_layer_manifest",
                "schema_version": "memory_layer_manifest_v1",
                "layers": layer_manifest["layer_order"],
                "short_term_policy": "query_supplied_raw_rows_not_persisted_by_build",
                "policy": (
                    "organize memory operations by layer before query consumers "
                    "choose retrieval, context packing, verification, or audit actions"
                ),
            },
            "operation_api_contract": {
                "api_field": "memory_operation_api",
                "schema_version": "memory_operation_api_v1",
                "operations": _memory_working_view_operation_contract(),
                "anchor_source_field": "context_anchor_source_ids",
                "source": "lifecycle_audit_and_layer_manifest",
                "policy": (
                    "query consumers call operation actions and expand returned "
                    "source ids to raw rows; memory objects are never final evidence"
                ),
            },
            "context_interface_contract": {
                "interface_field": "memory_context_interface",
                "schema_version": "memory_context_interface_v1",
                "source": "memory_layer_manifest_and_memory_operation_api",
                "anchor_source_field": "context_anchor_source_ids",
                "operation_slot_field": "operation_slots",
                "operation_lifecycle_field": "memory_operation_lifecycle",
                "working_compiler_plan_field": "memory_working_compiler_plan",
                "roles": [
                    "query_short_term",
                    "working_state",
                    "long_term_recall",
                    "archival_state",
                    "quarantine_audit",
                ],
                "policy": (
                    "query modules consume source-backed memory roles and "
                    "operation views through one stable context interface; "
                    "operation lifecycle records define build-time management "
                    "decisions, then query modules expand to raw rows before "
                    "final evidence"
                ),
            },
            "working_compiler_plan_contract": {
                "plan_field": "memory_working_compiler_plan",
                "schema_version": "memory_working_compiler_plan_v1",
                "source": "memory_context_interface_and_memory_operation_lifecycle",
                "focuses": [
                    "current_state",
                    "conflict_chain",
                    "temporal_validity",
                    "long_term_recall",
                    "audit_only",
                ],
                "operations": _memory_working_view_operation_contract(),
                "policy": (
                    "build produces source-backed context organization, source "
                    "expansion, and verifier check plans; query compiler may "
                    "consume the plan but final evidence still expands to raw "
                    "source rows"
                ),
            },
            "memory_system_state_contract": {
                "state_field": "memory_system_state",
                "schema_version": "memory_system_state_v1",
                "sources": [
                    "memory_context_interface",
                    "memory_operation_lifecycle",
                    "memory_working_compiler_plan",
                    "memory_layer_manifest",
                ],
                "layers": layer_manifest["layer_order"],
                "operations": _memory_working_view_operation_contract(),
                "policy": (
                    "build-owned state plane for memory layer organization, "
                    "operation decisions, source expansion, context packing, "
                    "verifier checks, and audit; every entry expands to raw "
                    "source rows before answer evidence"
                ),
            },
            "memory_operation_journal_contract": {
                "journal_field": "memory_operation_journal",
                "schema_version": "memory_operation_journal_v1",
                "source": "memory_system_state",
                "operations": _memory_working_view_operation_contract(),
                "policy": (
                    "normalize build manager decisions and query-time memory "
                    "operations into source-backed create/update/merge/supersede/"
                    "retrieve/expand/verify/audit records for audit and ablation; "
                    "records still expand to raw source rows before final evidence"
                ),
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
        "working_memory_view": working_memory_view,
        "lifecycle_audit": lifecycle_audit,
        "memory_layer_manifest": layer_manifest,
        "memory_operation_api": operation_api,
        "memory_context_interface": context_interface,
        "memory_operation_lifecycle": operation_lifecycle,
        "memory_working_compiler_plan": working_compiler_plan,
        "memory_system_state": memory_system_state,
        "memory_operation_journal": operation_journal,
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


def _memory_working_memory_view(
    operation_registry: dict[str, Any],
) -> dict[str, Any]:
    """Workspace view over source-backed memory operations for query consumers."""

    entries: list[dict[str, Any]] = []
    for raw_entry in operation_registry.get("entries") or ():
        if not isinstance(raw_entry, dict):
            continue
        source_ids = _ordered_strings(
            raw_entry.get("expand_source_order") or raw_entry.get("source_ids") or ()
        )[:12]
        workspace_layer = _memory_workspace_layer(raw_entry)
        workspace_role = _memory_workspace_role(raw_entry)
        entries.append(
            {
                "entry_id": f"wm:{raw_entry.get('entry_id') or len(entries)}",
                "registry_entry_id": str(raw_entry.get("entry_id") or ""),
                "target_type": str(raw_entry.get("target_type") or "object"),
                "target_id": str(raw_entry.get("target_id") or ""),
                "slot_id": str(raw_entry.get("slot_id") or ""),
                "memory_id": str(raw_entry.get("memory_id") or ""),
                "memory_type": str(raw_entry.get("memory_type") or ""),
                "namespace": str(raw_entry.get("namespace") or ""),
                "layer": str(raw_entry.get("layer") or ""),
                "memory_tier": str(raw_entry.get("memory_tier") or ""),
                "workspace_layer": workspace_layer,
                "workspace_role": workspace_role,
                "status": str(raw_entry.get("status") or ""),
                "subject": _normalize_key_text(str(raw_entry.get("subject") or "")),
                "predicate": _normalize_key_text(str(raw_entry.get("predicate") or "")),
                "values": _ordered_strings(raw_entry.get("values") or ())[:12],
                "operations": _ordered_strings(raw_entry.get("operations") or ()),
                "graph_signals": _ordered_strings(
                    raw_entry.get("graph_signals") or ()
                ),
                "lexical_terms": _ordered_strings(
                    raw_entry.get("lexical_terms") or ()
                )[:32],
                "record_count": int(raw_entry.get("record_count") or 0),
                "status_counts": dict(raw_entry.get("status_counts") or {}),
                "operation_current_source_order": _ordered_strings(
                    raw_entry.get("operation_current_source_order") or ()
                )[:12],
                "operation_historical_source_order": _ordered_strings(
                    raw_entry.get("operation_historical_source_order") or ()
                )[:12],
                "validity_current_source_order": _ordered_strings(
                    raw_entry.get("validity_current_source_order") or ()
                )[:12],
                "validity_historical_source_order": _ordered_strings(
                    raw_entry.get("validity_historical_source_order") or ()
                )[:12],
                "active_memory_ids": _ordered_strings(
                    raw_entry.get("active_memory_ids") or ()
                )[:12],
                "superseded_memory_ids": _ordered_strings(
                    raw_entry.get("superseded_memory_ids") or ()
                )[:12],
                "source_backed": bool(raw_entry.get("source_backed") or source_ids),
                "source_ids": source_ids,
                "expand_source_order": source_ids,
                "verify_policy": "expand_to_raw_source_rows",
                "audit_policy": "source_support_status_slot_and_lifecycle",
                "source_policy": {
                    "raw_evidence_required": True,
                    "final_evidence_policy": "raw_source_rows",
                },
            }
        )

    layer_counts: dict[str, int] = defaultdict(int)
    role_counts: dict[str, int] = defaultdict(int)
    target_counts: dict[str, int] = defaultdict(int)
    operation_counts: dict[str, int] = defaultdict(int)
    source_backed_count = 0
    for entry in entries:
        layer_counts[str(entry.get("workspace_layer") or "unknown")] += 1
        role_counts[str(entry.get("workspace_role") or "unknown")] += 1
        target_counts[str(entry.get("target_type") or "unknown")] += 1
        if entry.get("source_backed"):
            source_backed_count += 1
        for operation in entry.get("operations") or ():
            operation_counts[str(operation)] += 1

    return {
        "schema_version": "memory_working_view_v1",
        "trace_only": False,
        "applied": True,
        "entry_count": len(entries),
        "source_backed_entry_count": source_backed_count,
        "source_incomplete_entry_count": max(0, len(entries) - source_backed_count),
        "layer_counts": dict(sorted(layer_counts.items())),
        "role_counts": dict(sorted(role_counts.items())),
        "target_counts": dict(sorted(target_counts.items())),
        "operation_counts": dict(sorted(operation_counts.items())),
        "layer_contract": _memory_working_view_layer_contract(),
        "operation_contract": _memory_working_view_operation_contract(),
        "source_policy": {
            "raw_evidence_required": True,
            "final_evidence_policy": "raw_source_rows",
            "question_independent_build": True,
        },
        "entries": entries,
        "clean_note": (
            "Question-independent working-memory view over the operation registry. "
            "It organizes build memory into layer/role/target entries for state "
            "management, conflict handling, context organization, and answer audit; "
            "all entries must expand to raw source rows before final evidence."
        ),
    }


def _disabled_memory_working_memory_view() -> dict[str, Any]:
    return {
        "schema_version": "memory_working_view_v1",
        "trace_only": False,
        "applied": False,
        "entry_count": 0,
        "source_backed_entry_count": 0,
        "source_incomplete_entry_count": 0,
        "layer_counts": {},
        "role_counts": {},
        "target_counts": {},
        "operation_counts": {},
        "layer_contract": _memory_working_view_layer_contract(),
        "operation_contract": _memory_working_view_operation_contract(),
        "source_policy": {
            "raw_evidence_required": True,
            "final_evidence_policy": "raw_source_rows",
            "question_independent_build": True,
        },
        "entries": [],
        "disabled_reason": (
            "build_memory.memory_system_graph.working_memory_view.enabled=false"
        ),
        "clean_note": (
            "Working-memory view is disabled for ablation. Query consumers must "
            "fall back to the source-backed operation registry or raw operation "
            "slot index, and final answer evidence still resolves to raw rows."
        ),
    }


def _memory_layer_manifest(
    *,
    lifecycle_audit: dict[str, Any],
) -> dict[str, Any]:
    layer_order = tuple(_memory_working_view_layer_contract().keys())
    layers = {
        layer: {
            "layer": layer,
            "description": _memory_working_view_layer_contract()[layer],
            "query_supplied": layer == "short_term_memory",
            "persisted_by_build": layer != "short_term_memory",
            "entry_count": 0,
            "source_backed_entry_count": 0,
            "source_incomplete_entry_count": 0,
            "memory_ids": [],
            "source_ids": [],
            "target_counts": {},
            "stage_counts": {},
            "operation_counts": {},
        }
        for layer in layer_order
    }
    for entry in lifecycle_audit.get("entries") or ():
        if not isinstance(entry, dict):
            continue
        layer = _memory_layer_manifest_entry_layer(entry)
        summary = layers[layer]
        summary["entry_count"] += 1
        if entry.get("source_backed"):
            summary["source_backed_entry_count"] += 1
        else:
            summary["source_incomplete_entry_count"] += 1
        _memory_layer_manifest_extend_unique(
            summary["memory_ids"],
            (
                entry.get("memory_id"),
                *(entry.get("active_memory_ids") or ()),
                *(entry.get("superseded_memory_ids") or ()),
            ),
            max_items=64,
        )
        _memory_layer_manifest_extend_unique(
            summary["source_ids"],
            (
                *(entry.get("current_source_order") or ()),
                *(entry.get("historical_source_order") or ()),
                *(entry.get("source_ids") or ()),
            ),
            max_items=96,
        )
        _memory_layer_manifest_increment(
            summary["target_counts"],
            str(entry.get("target_type") or "unknown"),
        )
        _memory_layer_manifest_increment(
            summary["stage_counts"],
            str(entry.get("lifecycle_stage") or "unknown"),
        )
        for action in entry.get("audit_actions") or ():
            _memory_layer_manifest_increment(
                summary["operation_counts"],
                str(action or "unknown"),
            )

    for layer in layer_order:
        summary = layers[layer]
        summary["target_counts"] = dict(sorted(summary["target_counts"].items()))
        summary["stage_counts"] = dict(sorted(summary["stage_counts"].items()))
        summary["operation_counts"] = dict(sorted(summary["operation_counts"].items()))

    entry_count = sum(layers[layer]["entry_count"] for layer in layer_order)
    source_backed_count = sum(
        layers[layer]["source_backed_entry_count"] for layer in layer_order
    )
    return {
        "schema_version": "memory_layer_manifest_v1",
        "trace_only": False,
        "applied": bool(lifecycle_audit.get("applied")),
        "layer_order": list(layer_order),
        "layer_count": len(layer_order),
        "entry_count": entry_count,
        "source_backed_entry_count": source_backed_count,
        "source_incomplete_entry_count": max(0, entry_count - source_backed_count),
        "layers": layers,
        "source_policy": {
            "raw_evidence_required": True,
            "final_evidence_policy": "raw_source_rows",
            "question_independent_build": True,
            "short_term_memory_source": "query_visible_raw_rows",
        },
        "operation_contract": _memory_working_view_operation_contract(),
        "clean_note": (
            "Question-independent memory layer manifest over lifecycle audit entries. "
            "It separates short-term raw row memory, working state/conflict memory, "
            "long-term recall, archival history, and quarantine policy without "
            "using questions, labels, gold answers, judge outputs, sample ids, or "
            "test feedback."
        ),
    }


def _memory_layer_manifest_entry_layer(entry: dict[str, Any]) -> str:
    workspace_layer = str(entry.get("workspace_layer") or "")
    if workspace_layer in _memory_working_view_layer_contract():
        return workspace_layer
    memory_tier = str(entry.get("memory_tier") or "")
    if memory_tier in _memory_working_view_layer_contract():
        return memory_tier
    lifecycle_stage = str(entry.get("lifecycle_stage") or "")
    if lifecycle_stage == "quarantine":
        return "quarantine_memory"
    if lifecycle_stage == "archival_state":
        return "archival_memory"
    if lifecycle_stage in {
        "active_state",
        "conflict_resolution",
        "state_value_management",
    }:
        return "working_memory"
    return "long_term_memory"


def _memory_layer_manifest_extend_unique(
    target: list[str],
    values: Any,
    *,
    max_items: int,
) -> None:
    seen = set(target)
    for value in values:
        text = str(value or "").strip()
        if not text or text in seen:
            continue
        target.append(text)
        seen.add(text)
        if len(target) >= max_items:
            return


def _memory_layer_manifest_increment(counts: dict[str, int], key: str) -> None:
    counts[key] = int(counts.get(key) or 0) + 1


def _memory_operation_api(
    *,
    lifecycle_audit: dict[str, Any],
    layer_manifest: dict[str, Any],
) -> dict[str, Any]:
    """Stable query-facing API over build-owned memory operations."""

    operation_contract = tuple(_memory_working_view_operation_contract())
    entries: list[dict[str, Any]] = []
    for ordinal, raw_entry in enumerate(lifecycle_audit.get("entries") or ()):
        if not isinstance(raw_entry, dict):
            continue
        actions = tuple(
            action
            for action in _ordered_strings(raw_entry.get("audit_actions") or ())
            if action in operation_contract
        )
        if not actions:
            actions = tuple(
                action
                for action in ("retrieve", "expand", "verify", "audit")
                if raw_entry.get("source_backed")
            )
        graph_signals = _memory_operation_api_graph_signals(
            raw_entry,
            actions=actions,
        )
        query_operations = _ordered_strings((*actions, *graph_signals))
        current_source_order = _ordered_strings(
            raw_entry.get("current_source_order") or ()
        )[:12]
        historical_source_order = _ordered_strings(
            raw_entry.get("historical_source_order") or ()
        )[:12]
        operation_current_source_order = _ordered_strings(
            raw_entry.get("operation_current_source_order")
            or raw_entry.get("current_source_order")
            or ()
        )[:12]
        operation_historical_source_order = _ordered_strings(
            raw_entry.get("operation_historical_source_order")
            or raw_entry.get("historical_source_order")
            or ()
        )[:12]
        validity_current_source_order = _ordered_strings(
            raw_entry.get("validity_current_source_order")
            or raw_entry.get("current_source_order")
            or operation_current_source_order
        )[:12]
        validity_historical_source_order = _ordered_strings(
            raw_entry.get("validity_historical_source_order")
            or raw_entry.get("historical_source_order")
            or operation_historical_source_order
        )[:12]
        source_ids = _ordered_strings(
            (
                *current_source_order,
                *historical_source_order,
                *operation_current_source_order,
                *operation_historical_source_order,
                *validity_current_source_order,
                *validity_historical_source_order,
                *(raw_entry.get("source_ids") or ()),
            )
        )[:12]
        memory_layer = _memory_layer_manifest_entry_layer(raw_entry)
        entries.append(
            {
                "operation_id": f"api:{raw_entry.get('audit_id') or ordinal}",
                "interface_source": "memory_lifecycle_audit",
                "interface_entry_id": str(raw_entry.get("audit_id") or ""),
                "target_type": str(raw_entry.get("target_type") or "object"),
                "target_id": str(raw_entry.get("target_id") or ""),
                "slot_id": str(raw_entry.get("slot_id") or ""),
                "memory_id": str(raw_entry.get("memory_id") or ""),
                "memory_type": str(raw_entry.get("memory_type") or ""),
                "namespace": str(raw_entry.get("namespace") or ""),
                "layer": str(raw_entry.get("layer") or ""),
                "memory_layer": memory_layer,
                "memory_tier": str(raw_entry.get("memory_tier") or ""),
                "lifecycle_stage": str(raw_entry.get("lifecycle_stage") or ""),
                "status": str(raw_entry.get("status") or ""),
                "status_counts": dict(raw_entry.get("status_counts") or {}),
                "subject": _normalize_key_text(str(raw_entry.get("subject") or "")),
                "predicate": _normalize_key_text(str(raw_entry.get("predicate") or "")),
                "values": _ordered_strings(raw_entry.get("values") or ())[:12],
                "operation_actions": list(actions),
                "operations": query_operations,
                "graph_signals": graph_signals,
                "lexical_terms": _memory_operation_api_lexical_terms(raw_entry)[:32],
                "record_count": int(raw_entry.get("record_count") or 0),
                "operation_map": {
                    action: {
                        "enabled": action in actions,
                        "source_ids": source_ids if action in actions else [],
                        "policy": "expand_to_raw_source_rows",
                    }
                    for action in operation_contract
                },
                "active_memory_ids": _ordered_strings(
                    raw_entry.get("active_memory_ids") or ()
                )[:12],
                "superseded_memory_ids": _ordered_strings(
                    raw_entry.get("superseded_memory_ids") or ()
                )[:12],
                "current_source_order": current_source_order,
                "historical_source_order": historical_source_order,
                "operation_current_source_order": operation_current_source_order,
                "operation_historical_source_order": (
                    operation_historical_source_order
                ),
                "validity_current_source_order": validity_current_source_order,
                "validity_historical_source_order": validity_historical_source_order,
                "source_ids": source_ids,
                "source_backed": bool(raw_entry.get("source_backed") or source_ids),
                "activation_scope": _memory_operation_api_activation_scope(
                    memory_layer
                ),
                "source_policy": {
                    "raw_evidence_required": True,
                    "final_evidence_policy": "raw_source_rows",
                    "memory_objects_are_not_final_evidence": True,
                },
            }
        )

    layer_counts: dict[str, int] = defaultdict(int)
    stage_counts: dict[str, int] = defaultdict(int)
    target_counts: dict[str, int] = defaultdict(int)
    action_counts: dict[str, int] = defaultdict(int)
    source_backed_count = 0
    for entry in entries:
        layer_counts[str(entry.get("memory_layer") or "unknown")] += 1
        stage_counts[str(entry.get("lifecycle_stage") or "unknown")] += 1
        target_counts[str(entry.get("target_type") or "unknown")] += 1
        if entry.get("source_backed"):
            source_backed_count += 1
        for action in entry.get("operation_actions") or ():
            action_counts[str(action)] += 1

    context_anchor_source_ids = _memory_operation_api_context_anchor_source_ids(
        layer_manifest
    )
    return {
        "schema_version": "memory_operation_api_v1",
        "trace_only": False,
        "applied": bool(entries),
        "entry_count": len(entries),
        "source_backed_entry_count": source_backed_count,
        "source_incomplete_entry_count": max(0, len(entries) - source_backed_count),
        "operation_contract": list(operation_contract),
        "operation_action_counts": dict(sorted(action_counts.items())),
        "layer_counts": dict(sorted(layer_counts.items())),
        "stage_counts": dict(sorted(stage_counts.items())),
        "target_counts": dict(sorted(target_counts.items())),
        "context_anchor_policy": {
            "anchor_layers": [
                "archival_memory",
                "working_memory",
                "long_term_memory",
            ],
            "source": "memory_layer_manifest",
            "policy": "preserve source-backed lifecycle anchors before raw-row expansion",
        },
        "context_anchor_source_ids": context_anchor_source_ids,
        "context_anchor_source_count": len(context_anchor_source_ids),
        "source_policy": {
            "raw_evidence_required": True,
            "final_evidence_policy": "raw_source_rows",
            "question_independent_build": True,
            "memory_objects_are_not_final_evidence": True,
        },
        "entries": entries,
        "clean_note": (
            "Question-independent managed memory operation API. It exposes "
            "create/update/merge/supersede/retrieve/expand/verify/audit over "
            "source-backed lifecycle entries so query modules can consume one "
            "stable interface instead of registry/view/audit internals. It never "
            "uses questions, labels, gold answers, judge outputs, sample ids, "
            "or test feedback; final evidence must expand to raw source rows."
        ),
    }


def _memory_operation_api_activation_scope(memory_layer: str) -> str:
    if memory_layer == "archival_memory":
        return "historical_state"
    if memory_layer == "working_memory":
        return "working_state"
    if memory_layer == "quarantine_memory":
        return "quarantine_audit_only"
    return "long_term_recall"


def _memory_operation_api_graph_signals(
    entry: dict[str, Any],
    *,
    actions: tuple[str, ...],
) -> list[str]:
    signals = list(_ordered_strings(entry.get("graph_signals") or ()))
    if entry.get("source_backed") or entry.get("source_ids"):
        signals.append("source_support")
    status_counts = entry.get("status_counts") or {}
    audit_flags = {str(flag) for flag in entry.get("audit_flags") or ()}
    if (
        "supersede" in actions
        or status_counts.get("superseded")
        or entry.get("superseded_memory_ids")
    ):
        signals.append("supersede")
    if (
        str(entry.get("target_type") or "") == "conflict_slot"
        or "conflict_resolution" in audit_flags
    ):
        signals.append("conflict_slot")
    values = _ordered_strings(entry.get("values") or ())
    if len(values) > 1:
        signals.append("multi_value_slot")
    return _ordered_strings(signals)


def _memory_operation_api_lexical_terms(entry: dict[str, Any]) -> list[str]:
    inherited_terms = _ordered_strings(entry.get("lexical_terms") or ())
    if inherited_terms:
        return inherited_terms
    text = " ".join(
        str(part)
        for part in (
            entry.get("subject") or "",
            entry.get("predicate") or "",
            " ".join(str(value) for value in (entry.get("values") or ())),
        )
        if part
    )
    return _ordered_strings(
        token.lower()
        for token in re.findall(r"[A-Za-z0-9_]+", text)
        if len(token) >= 3
    )


def _memory_operation_api_context_anchor_source_ids(
    layer_manifest: dict[str, Any],
) -> list[str]:
    layers = layer_manifest.get("layers")
    if not isinstance(layers, dict):
        return []
    return _ordered_strings(
        source_id
        for layer in ("archival_memory", "working_memory", "long_term_memory")
        for summary in (layers.get(layer),)
        if isinstance(summary, dict)
        for source_id in (summary.get("source_ids") or ())
    )


def _memory_context_interface(
    *,
    lifecycle_audit: dict[str, Any],
    layer_manifest: dict[str, Any],
    operation_api: dict[str, Any],
) -> dict[str, Any]:
    """Build-owned context interface over memory layers and operations."""

    layer_contract = _memory_working_view_layer_contract()
    layer_order = _ordered_strings(
        layer_manifest.get("layer_order") or layer_contract.keys()
    )
    layers = layer_manifest.get("layers")
    if not isinstance(layers, dict):
        layers = {}
    operation_entries = [
        entry for entry in operation_api.get("entries") or () if isinstance(entry, dict)
    ]
    context_anchor_source_ids = _ordered_strings(
        operation_api.get("context_anchor_source_ids")
        or _memory_operation_api_context_anchor_source_ids(layer_manifest)
    )
    source_roles = {
        _memory_context_interface_role_name(layer): (
            _memory_context_interface_source_role(
                layer=layer,
                summary=(
                    layers.get(layer) if isinstance(layers.get(layer), dict) else {}
                ),
                layer_contract=layer_contract,
            )
        )
        for layer in layer_order
    }
    operation_views = {
        "conflict_resolution": _memory_context_interface_operation_view(
            operation_entries,
            operation_signals=("conflict_slot", "multi_value_slot"),
            lifecycle_stages=("conflict_resolution",),
            operations=("verify", "audit", "retrieve", "expand"),
        ),
        "supersession_chain": _memory_context_interface_operation_view(
            operation_entries,
            operation_signals=("supersede",),
            lifecycle_stages=("archival_state",),
            operations=("supersede", "verify", "audit", "retrieve", "expand"),
        ),
        "state_verification": _memory_context_interface_operation_view(
            operation_entries,
            operation_signals=(),
            lifecycle_stages=(
                "active_state",
                "state_value_management",
                "conflict_resolution",
            ),
            operations=("verify", "audit"),
        ),
    }
    operation_slots = _memory_context_interface_operation_slots(operation_entries)
    object_type_counts: dict[str, int] = defaultdict(int)
    action_counts: dict[str, int] = defaultdict(int)
    for entry in operation_entries:
        object_type_counts[str(entry.get("target_type") or "unknown")] += 1
        for action in entry.get("operation_actions") or ():
            action_counts[str(action)] += 1

    return {
        "schema_version": "memory_context_interface_v1",
        "trace_only": False,
        "applied": bool(
            layer_manifest.get("applied")
            or operation_api.get("applied")
            or lifecycle_audit.get("applied")
        ),
        "interface_sources": [
            "memory_layer_manifest",
            "memory_operation_api",
            "memory_lifecycle_audit",
        ],
        "role_count": len(source_roles),
        "entry_count": int(operation_api.get("entry_count") or 0),
        "source_backed_entry_count": int(
            operation_api.get("source_backed_entry_count") or 0
        ),
        "source_incomplete_entry_count": int(
            operation_api.get("source_incomplete_entry_count") or 0
        ),
        "operation_slot_count": len(operation_slots),
        "source_backed_operation_slot_count": sum(
            1 for slot in operation_slots if slot.get("source_backed")
        ),
        "operation_contract": list(_memory_working_view_operation_contract()),
        "operation_action_counts": dict(sorted(action_counts.items())),
        "memory_object_type_counts": dict(sorted(object_type_counts.items())),
        "layer_order": layer_order,
        "source_roles": source_roles,
        "operation_views": operation_views,
        "operation_slots": operation_slots,
        "context_anchor_source_ids": context_anchor_source_ids,
        "context_anchor_source_count": len(context_anchor_source_ids),
        "context_organization_policy": {
            "short_term_memory": "query_visible_raw_rows",
            "working_memory": "active_state_and_conflict_context",
            "long_term_memory": "stable_recall_context",
            "archival_memory": "historical_state_and_supersession_context",
            "quarantine_memory": "audit_only_not_final_evidence",
            "anchor_retention": "preserve_source_backed_lifecycle_anchors",
            "source_expansion": "expand_memory_object_source_ids_to_raw_rows",
            "verification_scope": (
                "number_time_speaker_entity_state_conflict_unsupported_answer"
            ),
        },
        "source_policy": {
            "raw_evidence_required": True,
            "final_evidence_policy": "raw_source_rows",
            "question_independent_build": True,
            "memory_objects_are_not_final_evidence": True,
        },
        "clean_note": (
            "Question-independent memory context interface that organizes "
            "short-term, working, long-term, archival, and quarantine memory "
            "roles plus conflict, supersession, and verification operation "
            "views and operation slots. It lets query modules consume one "
            "source-backed memory system boundary for state management, "
            "retrieval expansion, context organization, and audit while final "
            "evidence remains raw source rows."
        ),
    }


def _memory_context_interface_role_name(layer: str) -> str:
    if layer == "short_term_memory":
        return "query_short_term"
    if layer == "working_memory":
        return "working_state"
    if layer == "long_term_memory":
        return "long_term_recall"
    if layer == "archival_memory":
        return "archival_state"
    if layer == "quarantine_memory":
        return "quarantine_audit"
    return layer or "unknown"


def _memory_context_interface_source_role(
    *,
    layer: str,
    summary: dict[str, Any],
    layer_contract: dict[str, str],
) -> dict[str, Any]:
    source_ids = _ordered_strings(summary.get("source_ids") or ())
    return {
        "memory_layer": layer,
        "description": layer_contract.get(layer, ""),
        "query_supplied": bool(summary.get("query_supplied")),
        "persisted_by_build": bool(
            summary.get("persisted_by_build", layer != "short_term_memory")
        ),
        "entry_count": int(summary.get("entry_count") or 0),
        "source_backed_entry_count": int(
            summary.get("source_backed_entry_count") or 0
        ),
        "source_incomplete_entry_count": int(
            summary.get("source_incomplete_entry_count") or 0
        ),
        "source_ids": source_ids,
        "source_count": len(source_ids),
        "target_counts": dict(summary.get("target_counts") or {}),
        "stage_counts": dict(summary.get("stage_counts") or {}),
        "operation_counts": dict(summary.get("operation_counts") or {}),
        "allowed_operations": _memory_context_interface_role_operations(layer),
        "source_policy": {
            "raw_evidence_required": layer != "short_term_memory"
            or bool(summary.get("query_supplied")),
            "final_evidence_policy": "raw_source_rows",
        },
    }


def _memory_context_interface_operation_slots(
    entries: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    slots: list[dict[str, Any]] = []
    for entry in entries:
        if entry.get("target_type") != "operation_slot":
            continue
        slots.append(
            {
                **entry,
                "interface_source": "memory_context_interface",
                "interface_entry_id": str(entry.get("operation_id") or ""),
                "context_role": _memory_context_interface_role_name(
                    str(entry.get("memory_layer") or "")
                ),
                "source_policy": {
                    "raw_evidence_required": True,
                    "final_evidence_policy": "raw_source_rows",
                    "memory_objects_are_not_final_evidence": True,
                    "projection_source": "memory_operation_api",
                },
            }
        )
    return slots


def _memory_operation_lifecycle(
    *,
    operation_api: dict[str, Any],
    context_interface: dict[str, Any],
) -> dict[str, Any]:
    """Build-time memory manager decision plane over operation API entries."""

    entries = [
        entry for entry in operation_api.get("entries") or () if isinstance(entry, dict)
    ]
    context_operation_ids = {
        str(slot.get("interface_entry_id") or slot.get("operation_id") or "")
        for slot in context_interface.get("operation_slots") or ()
        if isinstance(slot, dict)
        and str(slot.get("interface_entry_id") or slot.get("operation_id") or "")
    }
    decisions: list[dict[str, Any]] = []
    decision_counts: dict[str, int] = defaultdict(int)
    phase_counts: dict[str, int] = defaultdict(int)
    layer_counts: dict[str, int] = defaultdict(int)
    target_counts: dict[str, int] = defaultdict(int)
    transition_counts: dict[str, int] = defaultdict(int)
    consumer_counts: dict[str, int] = defaultdict(int)
    source_backed_count = 0

    for ordinal, entry in enumerate(entries):
        decision = _memory_operation_lifecycle_decision(entry)
        phase = _memory_operation_lifecycle_phase(decision)
        transition = _memory_operation_lifecycle_transition(entry, decision)
        consumers = _memory_operation_lifecycle_consumers(entry, decision)
        source_ids = _ordered_strings(entry.get("source_ids") or ())[:12]
        memory_layer = str(entry.get("memory_layer") or "long_term_memory")
        target_type = str(entry.get("target_type") or "object")
        if entry.get("source_backed") or source_ids:
            source_backed_count += 1
        decision_counts[decision] += 1
        phase_counts[phase] += 1
        layer_counts[memory_layer] += 1
        target_counts[target_type] += 1
        transition_counts[transition] += 1
        for consumer in consumers:
            consumer_counts[consumer] += 1
        decisions.append(
            {
                "lifecycle_id": f"life:{entry.get('operation_id') or ordinal}",
                "interface_source": "memory_operation_lifecycle",
                "operation_id": str(entry.get("operation_id") or ""),
                "context_interface_slot": str(entry.get("operation_id") or "")
                in context_operation_ids,
                "target_type": target_type,
                "target_id": str(entry.get("target_id") or ""),
                "slot_id": str(entry.get("slot_id") or ""),
                "memory_id": str(entry.get("memory_id") or ""),
                "memory_type": str(entry.get("memory_type") or ""),
                "memory_layer": memory_layer,
                "lifecycle_stage": str(entry.get("lifecycle_stage") or ""),
                "status": str(entry.get("status") or ""),
                "subject": _normalize_key_text(str(entry.get("subject") or "")),
                "predicate": _normalize_key_text(str(entry.get("predicate") or "")),
                "values": _ordered_strings(entry.get("values") or ())[:8],
                "manager_decision": decision,
                "phase": phase,
                "state_transition": transition,
                "operation_actions": _ordered_strings(
                    entry.get("operation_actions") or ()
                ),
                "operations": _ordered_strings(entry.get("operations") or ()),
                "query_consumers": consumers,
                "source_backed": bool(entry.get("source_backed") or source_ids),
                "source_ids": source_ids,
                "source_policy": {
                    "raw_evidence_required": True,
                    "final_evidence_policy": "raw_source_rows",
                    "physical_delete_allowed": False,
                    "delete_maps_to": "supersede_or_quarantine",
                },
            }
        )

    return {
        "schema_version": "memory_operation_lifecycle_v1",
        "trace_only": False,
        "applied": bool(decisions),
        "interface_sources": [
            "memory_operation_api",
            "memory_context_interface",
        ],
        "entry_count": len(decisions),
        "source_backed_entry_count": source_backed_count,
        "source_incomplete_entry_count": max(0, len(decisions) - source_backed_count),
        "context_interface_slot_count": sum(
            1 for decision in decisions if decision["context_interface_slot"]
        ),
        "decision_counts": dict(sorted(decision_counts.items())),
        "phase_counts": dict(sorted(phase_counts.items())),
        "layer_counts": dict(sorted(layer_counts.items())),
        "target_counts": dict(sorted(target_counts.items())),
        "transition_counts": dict(sorted(transition_counts.items())),
        "query_consumer_counts": dict(sorted(consumer_counts.items())),
        "operation_model": {
            "add": "create",
            "update": "update_or_merge",
            "delete": "non_destructive_supersede_or_quarantine",
            "noop": "retain_source_backed_memory",
            "inspired_by": [
                "Mem0 ADD/UPDATE/DELETE/NOOP",
                "MemoryOS short/mid/long layering",
                "memory consolidation merge/rewrite/audit passes",
            ],
        },
        "operation_contract": _memory_working_view_operation_contract(),
        "source_policy": {
            "raw_evidence_required": True,
            "final_evidence_policy": "raw_source_rows",
            "question_independent_build": True,
            "physical_delete_allowed": False,
        },
        "decisions": decisions,
        "clean_note": (
            "Question-independent memory manager lifecycle over source-backed "
            "operation API entries. It turns create/update/merge/supersede/"
            "retrieve/expand/verify/audit into explicit build-time decisions, "
            "maps physical delete to non-destructive supersede or quarantine, "
            "and exposes query consumers without using questions, labels, gold "
            "answers, judge outputs, sample ids, or test feedback."
        ),
    }


def _memory_working_memory_compiler_plan(
    *,
    context_interface: dict[str, Any],
    operation_lifecycle: dict[str, Any],
    layer_manifest: dict[str, Any],
) -> dict[str, Any]:
    """Build-owned plan for state, conflict, context, and verification use."""

    decisions = [
        decision
        for decision in operation_lifecycle.get("decisions") or ()
        if isinstance(decision, dict)
    ]
    source_roles = context_interface.get("source_roles")
    if not isinstance(source_roles, dict):
        source_roles = {}
    layer_summaries = layer_manifest.get("layers")
    if not isinstance(layer_summaries, dict):
        layer_summaries = {}

    entries: list[dict[str, Any]] = []
    focus_counts: dict[str, int] = defaultdict(int)
    layer_counts: dict[str, int] = defaultdict(int)
    decision_counts: dict[str, int] = defaultdict(int)
    context_action_counts: dict[str, int] = defaultdict(int)
    verifier_check_counts: dict[str, int] = defaultdict(int)
    source_backed_count = 0
    context_slot_count = 0
    source_expansion_ids: list[str] = []

    for ordinal, decision in enumerate(decisions):
        focus = _memory_working_compiler_plan_focus(decision)
        secondary_focuses = _memory_working_compiler_plan_secondary_focuses(
            decision,
            focus,
        )
        context_actions = _memory_working_compiler_plan_context_actions(
            decision,
            focus,
        )
        verifier_checks = _memory_working_compiler_plan_verifier_checks(
            decision,
            focus,
        )
        source_ids = _ordered_strings(decision.get("source_ids") or ())[:16]
        memory_layer = str(decision.get("memory_layer") or "long_term_memory")
        context_role = _memory_context_interface_role_name(memory_layer)
        manager_decision = str(decision.get("manager_decision") or "retain")
        if source_ids or decision.get("source_backed"):
            source_backed_count += 1
        if decision.get("context_interface_slot"):
            context_slot_count += 1
        _memory_layer_manifest_extend_unique(
            source_expansion_ids,
            source_ids,
            max_items=128,
        )
        focus_counts[focus] += 1
        layer_counts[memory_layer] += 1
        decision_counts[manager_decision] += 1
        for action in context_actions:
            context_action_counts[action] += 1
        for check in verifier_checks:
            verifier_check_counts[check] += 1

        entries.append(
            {
                "plan_id": f"wmcp:{decision.get('operation_id') or ordinal}",
                "interface_source": "memory_working_compiler_plan",
                "source_lifecycle_id": str(decision.get("lifecycle_id") or ""),
                "source_operation_id": str(decision.get("operation_id") or ""),
                "context_interface_slot": bool(
                    decision.get("context_interface_slot")
                ),
                "target_type": str(decision.get("target_type") or ""),
                "target_id": str(decision.get("target_id") or ""),
                "slot_id": str(decision.get("slot_id") or ""),
                "memory_id": str(decision.get("memory_id") or ""),
                "memory_type": str(decision.get("memory_type") or ""),
                "memory_layer": memory_layer,
                "context_role": context_role,
                "focus": focus,
                "secondary_focuses": secondary_focuses,
                "manager_decision": manager_decision,
                "phase": str(decision.get("phase") or ""),
                "state_transition": str(decision.get("state_transition") or ""),
                "lifecycle_stage": str(decision.get("lifecycle_stage") or ""),
                "status": str(decision.get("status") or ""),
                "subject": _normalize_key_text(str(decision.get("subject") or "")),
                "predicate": _normalize_key_text(str(decision.get("predicate") or "")),
                "values": _ordered_strings(decision.get("values") or ())[:8],
                "context_actions": context_actions,
                "source_expansion": {
                    "policy": "expand_to_raw_source_rows",
                    "source_ids": source_ids,
                    "source_count": len(source_ids),
                    "prefer_context_interface_slot": bool(
                        decision.get("context_interface_slot")
                    ),
                },
                "verifier_checks": verifier_checks,
                "query_consumers": _ordered_strings(
                    decision.get("query_consumers") or ()
                ),
                "operation_actions": _ordered_strings(
                    decision.get("operation_actions") or ()
                ),
                "operations": _ordered_strings(decision.get("operations") or ()),
                "source_backed": bool(decision.get("source_backed") or source_ids),
                "source_ids": source_ids,
                "source_policy": {
                    "raw_evidence_required": True,
                    "final_evidence_policy": "raw_source_rows",
                    "memory_objects_are_not_final_evidence": True,
                    "question_independent_build": True,
                },
            }
        )

    return {
        "schema_version": "memory_working_compiler_plan_v1",
        "trace_only": False,
        "applied": bool(entries),
        "interface_sources": [
            "memory_context_interface",
            "memory_operation_lifecycle",
            "memory_layer_manifest",
        ],
        "entry_count": len(entries),
        "source_backed_entry_count": source_backed_count,
        "source_incomplete_entry_count": max(0, len(entries) - source_backed_count),
        "context_interface_slot_count": context_slot_count,
        "focus_counts": dict(sorted(focus_counts.items())),
        "layer_counts": dict(sorted(layer_counts.items())),
        "decision_counts": dict(sorted(decision_counts.items())),
        "context_action_counts": dict(sorted(context_action_counts.items())),
        "verifier_check_counts": dict(sorted(verifier_check_counts.items())),
        "source_expansion_source_ids": source_expansion_ids,
        "source_expansion_source_count": len(source_expansion_ids),
        "source_roles": {
            str(role): {
                "memory_layer": str(summary.get("memory_layer") or ""),
                "source_count": int(summary.get("source_count") or 0),
                "allowed_operations": _ordered_strings(
                    summary.get("allowed_operations") or ()
                ),
            }
            for role, summary in source_roles.items()
            if isinstance(summary, dict)
        },
        "layer_plan": {
            str(layer): {
                "entry_count": int(summary.get("entry_count") or 0),
                "source_backed_entry_count": int(
                    summary.get("source_backed_entry_count") or 0
                ),
                "query_supplied": bool(summary.get("query_supplied")),
                "persisted_by_build": bool(summary.get("persisted_by_build")),
            }
            for layer, summary in layer_summaries.items()
            if isinstance(summary, dict)
        },
        "operation_contract": _memory_working_view_operation_contract(),
        "context_organization_policy": {
            "short_term_memory": "query_visible_raw_rows",
            "working_memory": "pack_current_state_and_conflict_chain",
            "long_term_memory": "retrieve_stable_recall_with_source_expansion",
            "archival_memory": "separate_historical_state_for_temporal_validity",
            "quarantine_memory": "audit_only_not_final_evidence",
            "conflict_policy": "compare_active_superseded_then_expand_sources",
            "verification_policy": "attach_source_grounded_checks_before_answer",
        },
        "source_policy": {
            "raw_evidence_required": True,
            "final_evidence_policy": "raw_source_rows",
            "question_independent_build": True,
            "memory_objects_are_not_final_evidence": True,
        },
        "entries": entries,
        "clean_note": (
            "Question-independent working-memory compiler plan derived from "
            "memory lifecycle and context-interface artifacts. It turns memory "
            "objects into a source-backed plan for current state, conflict "
            "chains, temporal validity, long-term recall, source expansion, "
            "and verifier checks. It does not use question text, gold answers, "
            "judge outputs, benchmark labels, sample ids, or test feedback; "
            "final answer evidence remains raw source rows."
        ),
    }


def _memory_system_state(
    *,
    context_interface: dict[str, Any],
    operation_lifecycle: dict[str, Any],
    working_compiler_plan: dict[str, Any],
    layer_manifest: dict[str, Any],
) -> dict[str, Any]:
    """Unified build-owned memory system state for query consumers."""

    plan_entries = [
        entry
        for entry in working_compiler_plan.get("entries") or ()
        if isinstance(entry, dict)
    ]
    decisions = [
        decision
        for decision in operation_lifecycle.get("decisions") or ()
        if isinstance(decision, dict)
    ]
    source_roles = context_interface.get("source_roles")
    if not isinstance(source_roles, dict):
        source_roles = {}
    layer_summaries = layer_manifest.get("layers")
    if not isinstance(layer_summaries, dict):
        layer_summaries = {}

    layer_order = _ordered_strings(
        layer_manifest.get("layer_order") or _memory_working_view_layer_contract().keys()
    )
    layers: dict[str, dict[str, Any]] = {}
    for layer in layer_order:
        role_name = _memory_context_interface_role_name(layer)
        role_summary = source_roles.get(role_name)
        if not isinstance(role_summary, dict):
            role_summary = {}
        layer_summary = layer_summaries.get(layer)
        if not isinstance(layer_summary, dict):
            layer_summary = {}
        source_ids = _ordered_strings(
            role_summary.get("source_ids") or layer_summary.get("source_ids") or ()
        )
        layers[layer] = {
            "memory_layer": layer,
            "context_role": role_name,
            "query_supplied": bool(
                layer_summary.get("query_supplied")
                or role_summary.get("query_supplied")
            ),
            "persisted_by_build": bool(
                layer_summary.get("persisted_by_build", layer != "short_term_memory")
            ),
            "entry_count": int(
                layer_summary.get("entry_count")
                or role_summary.get("entry_count")
                or 0
            ),
            "source_backed_entry_count": int(
                layer_summary.get("source_backed_entry_count")
                or role_summary.get("source_backed_entry_count")
                or 0
            ),
            "source_ids": source_ids,
            "source_count": len(source_ids),
            "allowed_operations": _ordered_strings(
                role_summary.get("allowed_operations")
                or _memory_context_interface_role_operations(layer)
            ),
        }

    decision_by_operation_id = {
        str(decision.get("operation_id") or ""): decision
        for decision in decisions
        if str(decision.get("operation_id") or "")
    }
    entries: list[dict[str, Any]] = []
    source_expansion_ids: list[str] = []
    focus_counts: dict[str, int] = defaultdict(int)
    decision_counts: dict[str, int] = defaultdict(int)
    layer_counts: dict[str, int] = defaultdict(int)
    verifier_check_counts: dict[str, int] = defaultdict(int)
    context_action_counts: dict[str, int] = defaultdict(int)
    source_backed_count = 0

    for ordinal, plan_entry in enumerate(plan_entries):
        operation_id = str(plan_entry.get("source_operation_id") or "")
        decision = decision_by_operation_id.get(operation_id, {})
        source_expansion = plan_entry.get("source_expansion")
        if isinstance(source_expansion, dict):
            source_ids = _ordered_strings(source_expansion.get("source_ids") or ())
        else:
            source_ids = []
        if not source_ids:
            source_ids = _ordered_strings(plan_entry.get("source_ids") or ())
        source_ids = source_ids[:16]
        _memory_layer_manifest_extend_unique(
            source_expansion_ids,
            source_ids,
            max_items=128,
        )
        focus = str(plan_entry.get("focus") or "long_term_recall")
        manager_decision = str(plan_entry.get("manager_decision") or "retain")
        memory_layer = str(plan_entry.get("memory_layer") or "long_term_memory")
        context_role = str(
            plan_entry.get("context_role")
            or _memory_context_interface_role_name(memory_layer)
        )
        context_actions = _ordered_strings(plan_entry.get("context_actions") or ())
        verifier_checks = _ordered_strings(plan_entry.get("verifier_checks") or ())
        focus_counts[focus] += 1
        decision_counts[manager_decision] += 1
        layer_counts[memory_layer] += 1
        for action in context_actions:
            context_action_counts[str(action)] += 1
        for check in verifier_checks:
            verifier_check_counts[str(check)] += 1
        if plan_entry.get("source_backed") or source_ids:
            source_backed_count += 1
        entries.append(
            {
                "state_id": f"mss:{plan_entry.get('plan_id') or ordinal}",
                "interface_source": "memory_system_state",
                "plan_id": str(plan_entry.get("plan_id") or ""),
                "source_lifecycle_id": str(
                    plan_entry.get("source_lifecycle_id")
                    or decision.get("lifecycle_id")
                    or ""
                ),
                "source_operation_id": operation_id,
                "target_type": str(plan_entry.get("target_type") or ""),
                "target_id": str(plan_entry.get("target_id") or ""),
                "slot_id": str(plan_entry.get("slot_id") or ""),
                "memory_id": str(plan_entry.get("memory_id") or ""),
                "memory_type": str(plan_entry.get("memory_type") or ""),
                "memory_layer": memory_layer,
                "context_role": context_role,
                "focus": focus,
                "manager_decision": manager_decision,
                "phase": str(plan_entry.get("phase") or ""),
                "state_transition": str(plan_entry.get("state_transition") or ""),
                "lifecycle_stage": str(plan_entry.get("lifecycle_stage") or ""),
                "status": str(plan_entry.get("status") or ""),
                "subject": _normalize_key_text(str(plan_entry.get("subject") or "")),
                "predicate": _normalize_key_text(
                    str(plan_entry.get("predicate") or "")
                ),
                "values": _ordered_strings(plan_entry.get("values") or ())[:8],
                "context_actions": context_actions,
                "verifier_checks": verifier_checks,
                "operations": _ordered_strings(plan_entry.get("operations") or ()),
                "operation_actions": _ordered_strings(
                    plan_entry.get("operation_actions") or ()
                ),
                "query_consumers": _ordered_strings(
                    plan_entry.get("query_consumers") or ()
                ),
                "source_backed": bool(plan_entry.get("source_backed") or source_ids),
                "source_ids": source_ids,
                "source_expansion": {
                    "policy": "expand_to_raw_source_rows",
                    "source_ids": source_ids,
                    "source_count": len(source_ids),
                },
                "source_policy": {
                    "raw_evidence_required": True,
                    "final_evidence_policy": "raw_source_rows",
                    "memory_objects_are_not_final_evidence": True,
                    "question_independent_build": True,
                },
            }
        )

    return {
        "schema_version": "memory_system_state_v1",
        "trace_only": False,
        "applied": bool(entries or layers),
        "interface_sources": [
            "memory_context_interface",
            "memory_operation_lifecycle",
            "memory_working_compiler_plan",
            "memory_layer_manifest",
        ],
        "layer_count": len(layers),
        "entry_count": len(entries),
        "source_backed_entry_count": source_backed_count,
        "source_incomplete_entry_count": max(0, len(entries) - source_backed_count),
        "focus_counts": dict(sorted(focus_counts.items())),
        "decision_counts": dict(sorted(decision_counts.items())),
        "layer_counts": dict(sorted(layer_counts.items())),
        "context_action_counts": dict(sorted(context_action_counts.items())),
        "verifier_check_counts": dict(sorted(verifier_check_counts.items())),
        "source_expansion_source_ids": source_expansion_ids,
        "source_expansion_source_count": len(source_expansion_ids),
        "layers": layers,
        "operation_contract": _memory_working_view_operation_contract(),
        "context_organization_policy": {
            "short_term_memory": "query_visible_raw_rows",
            "working_memory": "state_conflict_workspace",
            "long_term_memory": "stable_source_backed_recall",
            "archival_memory": "non_destructive_historical_state",
            "quarantine_memory": "audit_only_not_final_evidence",
            "operation_flow": (
                "create_update_merge_supersede_then_retrieve_expand_verify_audit"
            ),
        },
        "source_policy": {
            "raw_evidence_required": True,
            "final_evidence_policy": "raw_source_rows",
            "question_independent_build": True,
            "memory_objects_are_not_final_evidence": True,
        },
        "entries": entries,
        "clean_note": (
            "Question-independent memory system state. It unifies layered memory "
            "roles, manager decisions, source expansion, context actions, verifier "
            "checks, and audit policy into one build-owned interface. It never "
            "uses question text, gold answers, judge outputs, benchmark labels, "
            "sample ids, or test feedback; final answer evidence remains raw "
            "source rows."
        ),
    }


def _memory_operation_journal(
    *,
    memory_system_state: dict[str, Any],
) -> dict[str, Any]:
    """Source-backed operation journal over the build-owned system state."""

    state_entries = [
        entry
        for entry in memory_system_state.get("entries") or ()
        if isinstance(entry, dict)
    ]
    journal_entries: list[dict[str, Any]] = []
    operation_counts: dict[str, int] = defaultdict(int)
    family_counts: dict[str, int] = defaultdict(int)
    decision_counts: dict[str, int] = defaultdict(int)
    phase_counts: dict[str, int] = defaultdict(int)
    layer_counts: dict[str, int] = defaultdict(int)
    target_counts: dict[str, int] = defaultdict(int)
    context_role_counts: dict[str, int] = defaultdict(int)
    source_backed_count = 0
    source_expansion_ids: list[str] = []

    for state_entry in state_entries:
        state_id = str(state_entry.get("state_id") or "")
        manager_decision = str(state_entry.get("manager_decision") or "")
        phase = str(state_entry.get("phase") or "")
        memory_layer = str(state_entry.get("memory_layer") or "long_term_memory")
        target_type = str(state_entry.get("target_type") or "object")
        context_role = str(state_entry.get("context_role") or "")
        source_ids = _ordered_strings(
            (
                *(state_entry.get("source_ids") or ()),
                *(
                    state_entry.get("source_expansion", {}).get("source_ids") or ()
                    if isinstance(state_entry.get("source_expansion"), dict)
                    else ()
                ),
            )
        )[:16]
        operation_types = _memory_operation_journal_operation_types(state_entry)
        for operation_index, operation_type in enumerate(operation_types):
            family = _memory_operation_journal_family(operation_type)
            operation_counts[operation_type] += 1
            family_counts[family] += 1
            decision_counts[manager_decision or "unknown"] += 1
            phase_counts[phase or "unknown"] += 1
            layer_counts[memory_layer] += 1
            target_counts[target_type] += 1
            context_role_counts[context_role or "unknown"] += 1
            if state_entry.get("source_backed") or source_ids:
                source_backed_count += 1
            _memory_layer_manifest_extend_unique(
                source_expansion_ids,
                source_ids,
                max_items=128,
            )
            journal_entries.append(
                {
                    "journal_id": (
                        f"moj:{state_id or len(journal_entries)}:"
                        f"{operation_type}:{operation_index}"
                    ),
                    "interface_source": "memory_operation_journal",
                    "source_state_id": state_id,
                    "source_plan_id": str(state_entry.get("plan_id") or ""),
                    "source_lifecycle_id": str(
                        state_entry.get("source_lifecycle_id") or ""
                    ),
                    "source_operation_id": str(
                        state_entry.get("source_operation_id") or ""
                    ),
                    "operation_type": operation_type,
                    "operation_family": family,
                    "manager_decision": manager_decision,
                    "phase": phase,
                    "state_transition": str(state_entry.get("state_transition") or ""),
                    "memory_layer": memory_layer,
                    "context_role": context_role,
                    "focus": str(state_entry.get("focus") or ""),
                    "target_type": target_type,
                    "target_id": str(state_entry.get("target_id") or ""),
                    "slot_id": str(state_entry.get("slot_id") or ""),
                    "memory_id": str(state_entry.get("memory_id") or ""),
                    "memory_type": str(state_entry.get("memory_type") or ""),
                    "lifecycle_stage": str(state_entry.get("lifecycle_stage") or ""),
                    "status": str(state_entry.get("status") or ""),
                    "subject": _normalize_key_text(
                        str(state_entry.get("subject") or "")
                    ),
                    "predicate": _normalize_key_text(
                        str(state_entry.get("predicate") or "")
                    ),
                    "values": _ordered_strings(state_entry.get("values") or ())[:8],
                    "context_actions": _ordered_strings(
                        state_entry.get("context_actions") or ()
                    ),
                    "verifier_checks": _ordered_strings(
                        state_entry.get("verifier_checks") or ()
                    ),
                    "query_consumers": _ordered_strings(
                        state_entry.get("query_consumers") or ()
                    ),
                    "source_backed": bool(state_entry.get("source_backed") or source_ids),
                    "source_ids": source_ids,
                    "source_expansion": {
                        "policy": "expand_to_raw_source_rows",
                        "source_ids": source_ids,
                        "source_count": len(source_ids),
                    },
                    "source_policy": {
                        "raw_evidence_required": True,
                        "final_evidence_policy": "raw_source_rows",
                        "memory_objects_are_not_final_evidence": True,
                        "question_independent_build": True,
                    },
                }
            )

    return {
        "schema_version": "memory_operation_journal_v1",
        "trace_only": False,
        "applied": bool(journal_entries),
        "interface_sources": ["memory_system_state"],
        "entry_count": len(journal_entries),
        "source_backed_entry_count": source_backed_count,
        "source_incomplete_entry_count": max(
            0, len(journal_entries) - source_backed_count
        ),
        "state_entry_count": len(state_entries),
        "operation_counts": dict(sorted(operation_counts.items())),
        "family_counts": dict(sorted(family_counts.items())),
        "decision_counts": dict(sorted(decision_counts.items())),
        "phase_counts": dict(sorted(phase_counts.items())),
        "layer_counts": dict(sorted(layer_counts.items())),
        "target_counts": dict(sorted(target_counts.items())),
        "context_role_counts": dict(sorted(context_role_counts.items())),
        "source_expansion_source_ids": source_expansion_ids,
        "source_expansion_source_count": len(source_expansion_ids),
        "operation_contract": _memory_working_view_operation_contract(),
        "operation_policy": {
            "create": "source_backed_memory_object_creation",
            "update": "source_backed_state_refresh",
            "merge": "source_backed_parallel_value_consolidation",
            "supersede": "non_destructive_archival_transition",
            "retrieve": "candidate_activation",
            "expand": "raw_source_row_expansion",
            "verify": "source_grounded_consistency_check",
            "audit": "traceable_risk_and_policy_check",
        },
        "source_policy": {
            "raw_evidence_required": True,
            "final_evidence_policy": "raw_source_rows",
            "question_independent_build": True,
            "memory_objects_are_not_final_evidence": True,
        },
        "entries": journal_entries,
        "clean_note": (
            "Question-independent memory operation journal over memory_system_state. "
            "It records create/update/merge/supersede/retrieve/expand/verify/audit "
            "as source-backed operations for state management, context organization, "
            "verification, and audit. It does not use question text, gold answers, "
            "judge outputs, benchmark labels, sample ids, or test feedback; final "
            "answer evidence remains raw source rows."
        ),
    }


def _memory_operation_journal_operation_types(entry: dict[str, Any]) -> list[str]:
    operations: list[str] = []
    manager_decision = str(entry.get("manager_decision") or "")
    if manager_decision in {"create", "update", "merge", "supersede"}:
        operations.append(manager_decision)
    if manager_decision in {"audit_conflict", "quarantine_audit"}:
        operations.append("audit")
    raw_operations = {
        str(operation)
        for operation in (
            *(entry.get("operations") or ()),
            *(entry.get("operation_actions") or ()),
        )
    }
    context_actions = {
        str(action) for action in entry.get("context_actions") or ()
    }
    verifier_checks = {
        str(check) for check in entry.get("verifier_checks") or ()
    }
    if raw_operations.intersection({"retrieve", "expand", "verify", "audit"}):
        operations.extend(
            operation
            for operation in ("retrieve", "expand", "verify", "audit")
            if operation in raw_operations
        )
    else:
        if context_actions or entry.get("source_ids"):
            operations.extend(["retrieve", "expand"])
        if verifier_checks:
            operations.append("verify")
        if (
            manager_decision in {"audit_conflict", "quarantine_audit"}
            or "state_conflict" in verifier_checks
            or "quarantine_not_final_evidence" in verifier_checks
        ):
            operations.append("audit")
    return [operation for operation in _ordered_strings(operations) if operation]


def _memory_operation_journal_family(operation_type: str) -> str:
    if operation_type in {"create", "update", "merge", "supersede"}:
        return "management"
    if operation_type in {"retrieve", "expand"}:
        return "context"
    if operation_type == "verify":
        return "verification"
    return "audit"


def _memory_working_compiler_plan_focus(decision: dict[str, Any]) -> str:
    manager_decision = str(decision.get("manager_decision") or "")
    target_type = str(decision.get("target_type") or "")
    memory_layer = str(decision.get("memory_layer") or "")
    lifecycle_stage = str(decision.get("lifecycle_stage") or "")
    state_transition = str(decision.get("state_transition") or "")
    if manager_decision in {"audit_conflict", "supersede"}:
        return "conflict_chain"
    if target_type == "conflict_slot":
        return "conflict_chain"
    if state_transition == "active_to_archival_non_destructive":
        return "conflict_chain"
    if manager_decision == "quarantine_audit" or memory_layer == "quarantine_memory":
        return "audit_only"
    if memory_layer == "archival_memory" or lifecycle_stage == "archival_state":
        return "temporal_validity"
    if memory_layer == "long_term_memory":
        return "long_term_recall"
    if memory_layer == "working_memory":
        return "current_state"
    return "long_term_recall"


def _memory_working_compiler_plan_secondary_focuses(
    decision: dict[str, Any],
    focus: str,
) -> list[str]:
    focuses: list[str] = []
    manager_decision = str(decision.get("manager_decision") or "")
    memory_layer = str(decision.get("memory_layer") or "")
    if focus == "conflict_chain":
        focuses.extend(["current_state", "temporal_validity"])
    if manager_decision in {"update", "merge", "retain_slot"}:
        focuses.append("current_state")
    if memory_layer == "archival_memory":
        focuses.append("temporal_validity")
    return [item for item in _ordered_strings(focuses) if item != focus]


def _memory_working_compiler_plan_context_actions(
    decision: dict[str, Any],
    focus: str,
) -> list[str]:
    actions = ["retrieve_source_rows", "expand_memory_sources"]
    manager_decision = str(decision.get("manager_decision") or "")
    target_type = str(decision.get("target_type") or "")
    if focus == "current_state":
        actions.extend(["prefer_active_state", "pack_working_state"])
    elif focus == "conflict_chain":
        actions.extend(["compare_active_superseded", "organize_supersession_chain"])
    elif focus == "temporal_validity":
        actions.extend(["order_by_source_time", "separate_current_from_historical"])
    elif focus == "long_term_recall":
        actions.append("retrieve_stable_recall")
    elif focus == "audit_only":
        actions.extend(["quarantine_from_final_evidence", "audit_source_backing"])
    if manager_decision == "create":
        actions.append("write_new_memory_object")
    elif manager_decision == "update":
        actions.append("refresh_working_state")
    elif manager_decision == "merge":
        actions.append("merge_parallel_slot_values")
    elif manager_decision == "supersede":
        actions.append("retain_superseded_as_archival_context")
    elif manager_decision == "retain_slot" or target_type.endswith("_slot"):
        actions.append("retain_slot_for_context")
    return _ordered_strings(actions)


def _memory_working_compiler_plan_verifier_checks(
    decision: dict[str, Any],
    focus: str,
) -> list[str]:
    checks = ["source_backing", "raw_row_expansion"]
    values = _ordered_strings(decision.get("values") or ())
    manager_decision = str(decision.get("manager_decision") or "")
    if focus == "current_state":
        checks.extend(["current_state_supported", "unsupported_answer"])
    elif focus == "conflict_chain":
        checks.extend(
            ["state_conflict", "active_superseded_consistency", "source_order"]
        )
    elif focus == "temporal_validity":
        checks.extend(["temporal_validity", "source_order"])
    elif focus == "long_term_recall":
        checks.extend(["profile_fact_consistency", "source_grounding"])
    elif focus == "audit_only":
        checks.extend(["quarantine_not_final_evidence", "source_completeness"])
    if len(values) > 1:
        checks.append("multi_value_slot")
    if manager_decision in {"merge", "supersede", "audit_conflict"}:
        checks.append("manager_decision_consistency")
    return _ordered_strings(checks)


def _memory_operation_lifecycle_decision(entry: dict[str, Any]) -> str:
    actions = {str(action) for action in entry.get("operation_actions") or ()}
    operations = {str(operation) for operation in entry.get("operations") or ()}
    graph_signals = {str(signal) for signal in entry.get("graph_signals") or ()}
    status_counts = entry.get("status_counts") or {}
    target_type = str(entry.get("target_type") or "")
    status = str(entry.get("status") or "")
    if not (entry.get("source_backed") or entry.get("source_ids")):
        return "quarantine_audit"
    if (
        "supersede" in actions
        or "supersede" in operations
        or "supersede" in graph_signals
        or status == "superseded"
        or status_counts.get("superseded")
    ):
        return "supersede"
    if target_type == "conflict_slot" or "conflict_slot" in graph_signals:
        return "audit_conflict"
    if "merge" in actions or "merge" in operations or "merge_value_slot" in operations:
        return "merge"
    if "update" in actions or "update" in operations or "update_value_slot" in operations:
        return "update"
    if "create" in actions:
        return "create"
    if target_type in {"value_slot", "operation_slot"}:
        return "retain_slot"
    return "retain"


def _memory_operation_lifecycle_phase(decision: str) -> str:
    if decision == "create":
        return "write"
    if decision in {"update", "merge", "supersede"}:
        return "consolidate"
    if decision in {"audit_conflict", "quarantine_audit"}:
        return "verify_audit"
    return "retain"


def _memory_operation_lifecycle_transition(
    entry: dict[str, Any],
    decision: str,
) -> str:
    if decision == "create":
        return "raw_observation_to_memory_object"
    if decision == "update":
        return "source_backed_state_update"
    if decision == "merge":
        return "duplicate_or_parallel_values_to_canonical_slot"
    if decision == "supersede":
        return "active_to_archival_non_destructive"
    if decision == "audit_conflict":
        return "conflicting_slot_to_verification_audit"
    if decision == "quarantine_audit":
        return "source_incomplete_to_quarantine_audit"
    if str(entry.get("target_type") or "") in {"value_slot", "operation_slot"}:
        return "source_backed_slot_retention"
    return "source_backed_memory_retention"


def _memory_operation_lifecycle_consumers(
    entry: dict[str, Any],
    decision: str,
) -> list[str]:
    operations = {str(operation) for operation in entry.get("operations") or ()}
    consumers: list[str] = []
    if operations.intersection({"retrieve", "expand"}):
        consumers.append("retrieval")
    if operations.intersection({"verify", "audit"}):
        consumers.append("verifier")
    if decision in {"update", "merge", "supersede", "audit_conflict"}:
        consumers.append("context_organization")
    if decision in {"quarantine_audit", "audit_conflict"}:
        consumers.append("audit")
    return _ordered_strings(consumers)


def _memory_context_interface_role_operations(layer: str) -> list[str]:
    if layer == "short_term_memory":
        return ["retrieve", "expand"]
    if layer == "working_memory":
        return [
            "create",
            "update",
            "merge",
            "supersede",
            "retrieve",
            "expand",
            "verify",
            "audit",
        ]
    if layer == "long_term_memory":
        return ["retrieve", "expand", "verify", "audit"]
    if layer == "archival_memory":
        return ["retrieve", "expand", "verify", "audit"]
    if layer == "quarantine_memory":
        return ["audit"]
    return ["audit"]


def _memory_context_interface_operation_view(
    entries: list[dict[str, Any]],
    *,
    operation_signals: tuple[str, ...],
    lifecycle_stages: tuple[str, ...],
    operations: tuple[str, ...],
    match_operations: bool = False,
) -> dict[str, Any]:
    source_ids: list[str] = []
    entry_count = 0
    for entry in entries:
        entry_signals = set(_ordered_strings(entry.get("graph_signals") or ()))
        entry_operations = set(_ordered_strings(entry.get("operations") or ()))
        entry_stage = str(entry.get("lifecycle_stage") or "")
        if not (
            entry_signals.intersection(operation_signals)
            or entry_stage in lifecycle_stages
            or (match_operations and entry_operations.intersection(operations))
        ):
            continue
        entry_count += 1
        _memory_layer_manifest_extend_unique(
            source_ids,
            entry.get("source_ids") or (),
            max_items=96,
        )
    return {
        "entry_count": entry_count,
        "source_ids": source_ids,
        "source_count": len(source_ids),
        "operation_signals": list(operation_signals),
        "lifecycle_stages": list(lifecycle_stages),
        "operations": list(operations),
        "source_policy": {
            "raw_evidence_required": True,
            "final_evidence_policy": "raw_source_rows",
        },
    }


def _memory_working_view_layer_contract() -> dict[str, str]:
    return {
        "short_term_memory": (
            "query-local raw turns and cited Memory rows; not persisted by build memory"
        ),
        "working_memory": (
            "active source-backed objects, value slots, conflict slots, and "
            "operation targets for current state organization"
        ),
        "long_term_memory": (
            "source-backed stable recall objects and slots; retrieved or expanded "
            "through raw source ids"
        ),
        "archival_memory": (
            "superseded or historical objects retained for conflict audit and "
            "temporal comparison"
        ),
        "quarantine_memory": (
            "low-confidence or source-incomplete objects; not eligible as "
            "independent evidence"
        ),
    }


def _memory_working_view_operation_contract() -> list[str]:
    return [
        "create",
        "update",
        "merge",
        "supersede",
        "retrieve",
        "expand",
        "verify",
        "audit",
    ]


def _memory_lifecycle_audit(
    *,
    operation_registry: dict[str, Any],
    working_memory_view: dict[str, Any],
) -> dict[str, Any]:
    interface_source, raw_entries = _memory_lifecycle_audit_source_entries(
        operation_registry=operation_registry,
        working_memory_view=working_memory_view,
    )
    entries: list[dict[str, Any]] = []
    for ordinal, raw_entry in enumerate(raw_entries):
        if not isinstance(raw_entry, dict):
            continue
        source_ids = _ordered_strings(
            raw_entry.get("expand_source_order") or raw_entry.get("source_ids") or ()
        )[:12]
        status_counts = _memory_lifecycle_entry_status_counts(raw_entry)
        operations = _ordered_strings(raw_entry.get("operations") or ())
        audit_actions = _memory_lifecycle_entry_actions(raw_entry, operations)
        flags = _memory_lifecycle_entry_flags(
            raw_entry,
            source_ids=source_ids,
            status_counts=status_counts,
            operations=operations,
        )
        operation_current_source_order = _memory_lifecycle_entry_order_field(
            raw_entry,
            "operation_current_source_order",
            "current_source_order",
            fallback=source_ids,
        )
        operation_historical_source_order = _memory_lifecycle_entry_order_field(
            raw_entry,
            "operation_historical_source_order",
            "historical_source_order",
            fallback=source_ids,
        )
        validity_current_source_order = _memory_lifecycle_entry_order_field(
            raw_entry,
            "validity_current_source_order",
            "current_source_order",
            fallback=operation_current_source_order or source_ids,
        )
        validity_historical_source_order = _memory_lifecycle_entry_order_field(
            raw_entry,
            "validity_historical_source_order",
            "historical_source_order",
            fallback=operation_historical_source_order or source_ids,
        )
        entries.append(
            {
                "audit_id": f"audit:{raw_entry.get('entry_id') or ordinal}",
                "interface_source": interface_source,
                "interface_entry_id": str(raw_entry.get("entry_id") or ""),
                "target_type": str(raw_entry.get("target_type") or "object"),
                "target_id": str(raw_entry.get("target_id") or ""),
                "slot_id": str(raw_entry.get("slot_id") or ""),
                "memory_id": str(raw_entry.get("memory_id") or ""),
                "memory_type": str(raw_entry.get("memory_type") or ""),
                "namespace": str(raw_entry.get("namespace") or ""),
                "layer": str(raw_entry.get("layer") or ""),
                "memory_tier": str(raw_entry.get("memory_tier") or ""),
                "workspace_layer": str(raw_entry.get("workspace_layer") or ""),
                "workspace_role": str(raw_entry.get("workspace_role") or ""),
                "lifecycle_stage": _memory_lifecycle_entry_stage(raw_entry, flags),
                "status": str(raw_entry.get("status") or ""),
                "status_counts": status_counts,
                "subject": _normalize_key_text(str(raw_entry.get("subject") or "")),
                "predicate": _normalize_key_text(str(raw_entry.get("predicate") or "")),
                "values": _ordered_strings(raw_entry.get("values") or ())[:12],
                "operations": operations,
                "graph_signals": _ordered_strings(
                    raw_entry.get("graph_signals") or ()
                )[:12],
                "lexical_terms": _ordered_strings(
                    raw_entry.get("lexical_terms") or ()
                )[:32],
                "record_count": int(raw_entry.get("record_count") or 0),
                "audit_actions": audit_actions,
                "audit_flags": flags,
                "active_memory_ids": _ordered_strings(
                    raw_entry.get("active_memory_ids") or ()
                )[:12],
                "superseded_memory_ids": _ordered_strings(
                    raw_entry.get("superseded_memory_ids") or ()
                )[:12],
                "source_backed": bool(raw_entry.get("source_backed") or source_ids),
                "source_ids": source_ids,
                "current_source_order": _memory_lifecycle_entry_source_order(
                    raw_entry,
                    scope="current",
                    fallback=source_ids,
                ),
                "historical_source_order": _memory_lifecycle_entry_source_order(
                    raw_entry,
                    scope="historical",
                    fallback=source_ids,
                ),
                "operation_current_source_order": operation_current_source_order,
                "operation_historical_source_order": (
                    operation_historical_source_order
                ),
                "validity_current_source_order": validity_current_source_order,
                "validity_historical_source_order": (
                    validity_historical_source_order
                ),
                "verify_policy": "expand_to_raw_source_rows",
                "audit_policy": "source_support_status_slot_lifecycle_and_conflict",
            }
        )

    source_backed_count = sum(1 for entry in entries if entry["source_backed"])
    flag_counts: dict[str, int] = defaultdict(int)
    operation_coverage: dict[str, int] = defaultdict(int)
    stage_counts: dict[str, int] = defaultdict(int)
    for entry in entries:
        stage_counts[str(entry.get("lifecycle_stage") or "unknown")] += 1
        for flag in entry.get("audit_flags") or ():
            flag_counts[str(flag)] += 1
        for action in entry.get("audit_actions") or ():
            operation_coverage[str(action)] += 1

    return {
        "schema_version": "memory_lifecycle_audit_v1",
        "trace_only": False,
        "applied": bool(entries),
        "interface_source": interface_source,
        "entry_count": len(entries),
        "source_backed_entry_count": source_backed_count,
        "source_incomplete_entry_count": max(0, len(entries) - source_backed_count),
        "conflict_entry_count": flag_counts.get("conflict_resolution", 0),
        "stateful_entry_count": flag_counts.get("stateful_memory", 0),
        "active_entry_count": flag_counts.get("active_state", 0),
        "superseded_entry_count": flag_counts.get("superseded_state", 0),
        "operation_coverage": dict(sorted(operation_coverage.items())),
        "flag_counts": dict(sorted(flag_counts.items())),
        "stage_counts": dict(sorted(stage_counts.items())),
        "operation_contract": _memory_working_view_operation_contract(),
        "source_policy": {
            "raw_evidence_required": True,
            "final_evidence_policy": "raw_source_rows",
            "question_independent_build": True,
        },
        "entries": entries,
        "clean_note": (
            "Question-independent lifecycle audit over the build-owned memory "
            "operation interface. It organizes create/update/merge/supersede/"
            "retrieve/expand/verify/audit readiness, source backing, state "
            "conflicts, and current/historical source order without using "
            "questions, labels, gold answers, judge outputs, sample ids, or "
            "test feedback."
        ),
    }


def _memory_lifecycle_audit_source_entries(
    *,
    operation_registry: dict[str, Any],
    working_memory_view: dict[str, Any],
) -> tuple[str, tuple[dict[str, Any], ...]]:
    if working_memory_view.get("applied"):
        return (
            "memory_working_view",
            tuple(
                entry
                for entry in working_memory_view.get("entries") or ()
                if isinstance(entry, dict)
            ),
        )
    if operation_registry.get("applied"):
        return (
            "memory_operation_registry",
            tuple(
                entry
                for entry in operation_registry.get("entries") or ()
                if isinstance(entry, dict)
            ),
        )
    return "", ()


def _memory_lifecycle_entry_status_counts(entry: dict[str, Any]) -> dict[str, int]:
    raw_counts = entry.get("status_counts")
    if isinstance(raw_counts, dict) and raw_counts:
        result: dict[str, int] = {}
        for key, value in raw_counts.items():
            try:
                count = int(value)
            except (TypeError, ValueError):
                continue
            if count > 0:
                result[str(key)] = count
        if result:
            return dict(sorted(result.items()))
    status = str(entry.get("status") or "")
    return {status: 1} if status else {}


def _memory_lifecycle_entry_actions(
    entry: dict[str, Any],
    operations: tuple[str, ...],
) -> tuple[str, ...]:
    operation_set = {str(operation) for operation in operations}
    actions: list[str] = []
    if str(entry.get("target_type") or "") == "object":
        actions.append("create")
    if "update" in operation_set or "update_value_slot" in operation_set:
        actions.append("update")
    if "merge" in operation_set or "merge_value_slot" in operation_set:
        actions.append("merge")
    if (
        "supersede" in operation_set
        or "supersede_value" in operation_set
        or str(entry.get("status") or "") == "superseded"
    ):
        actions.append("supersede")
    for operation in ("retrieve", "expand", "verify", "audit"):
        if operation in operation_set or entry.get("source_backed"):
            actions.append(operation)
    return tuple(
        action
        for action in _ordered_strings(actions)
        if action in set(_memory_working_view_operation_contract())
    )


def _memory_lifecycle_entry_flags(
    entry: dict[str, Any],
    *,
    source_ids: tuple[str, ...],
    status_counts: dict[str, int],
    operations: tuple[str, ...],
) -> tuple[str, ...]:
    flags: list[str] = []
    target_type = str(entry.get("target_type") or "")
    memory_type = str(entry.get("memory_type") or "")
    operation_set = {str(operation) for operation in operations}
    has_active = bool(
        status_counts.get("active")
        or entry.get("active_memory_ids")
        or entry.get("active_values")
        or str(entry.get("status") or "") == "active"
    )
    has_superseded = bool(
        status_counts.get("superseded")
        or entry.get("superseded_memory_ids")
        or entry.get("superseded_values")
        or str(entry.get("status") or "") == "superseded"
    )
    if entry.get("source_backed") or source_ids:
        flags.append("source_backed")
    else:
        flags.append("source_incomplete")
    if memory_type in _STATEFUL_MEMORY_TYPES:
        flags.append("stateful_memory")
    if has_active:
        flags.append("active_state")
    if has_superseded:
        flags.append("superseded_state")
    if has_active and has_superseded:
        flags.append("active_superseded_pair")
    if target_type == "conflict_slot" or operation_set.intersection(
        {"conflict_slot", "audit_conflict_slot", "audit_state_conflict_slot"}
    ):
        flags.append("conflict_resolution")
    if target_type in {"operation_slot", "value_slot", "conflict_slot"}:
        flags.append("slot_level_audit")
    if str(entry.get("memory_tier") or "") == "quarantine_memory":
        flags.append("quarantine_memory")
    return tuple(_ordered_strings(flags))


def _memory_lifecycle_entry_stage(
    entry: dict[str, Any],
    flags: tuple[str, ...],
) -> str:
    target_type = str(entry.get("target_type") or "")
    if "conflict_resolution" in flags:
        return "conflict_resolution"
    if target_type == "value_slot":
        return "state_value_management"
    if target_type == "operation_slot":
        return "operation_management"
    if "superseded_state" in flags and "active_state" not in flags:
        return "archival_state"
    if "active_state" in flags:
        return "active_state"
    if "quarantine_memory" in flags:
        return "quarantine"
    return "long_term_recall"


def _memory_lifecycle_entry_order_field(
    entry: dict[str, Any],
    *fields: str,
    fallback: tuple[str, ...],
) -> tuple[str, ...]:
    for field in fields:
        source_ids = _ordered_strings(entry.get(field) or ())
        if source_ids:
            return tuple(source_ids[:12])
    return tuple(fallback[:12])


def _memory_lifecycle_entry_source_order(
    entry: dict[str, Any],
    *,
    scope: str,
    fallback: tuple[str, ...],
) -> tuple[str, ...]:
    if scope == "historical":
        fields = (
            "validity_historical_source_order",
            "operation_historical_source_order",
            "historical_source_order",
        )
    else:
        fields = (
            "validity_current_source_order",
            "operation_current_source_order",
            "current_source_order",
        )
    for field in fields:
        source_ids = _ordered_strings(entry.get(field) or ())
        if source_ids:
            return source_ids[:12]
    return tuple(fallback[:12])


def _memory_workspace_layer(entry: dict[str, Any]) -> str:
    memory_tier = str(entry.get("memory_tier") or "")
    if memory_tier in {
        "working_memory",
        "long_term_memory",
        "archival_memory",
        "quarantine_memory",
    }:
        return memory_tier
    if str(entry.get("target_type") or "") in {"value_slot", "conflict_slot"}:
        return "working_memory"
    return "long_term_memory"


def _memory_workspace_role(entry: dict[str, Any]) -> str:
    target_type = str(entry.get("target_type") or "")
    operations = {str(item) for item in entry.get("operations") or ()}
    status = str(entry.get("status") or "")
    if target_type == "conflict_slot":
        return "conflict_resolution"
    if target_type == "value_slot":
        return "state_value_tracking"
    if target_type == "operation_slot":
        if operations.intersection(
            {
                "supersede",
                "conflict_slot",
                "audit_supersede",
                "audit_conflict_slot",
                "audit_state_conflict_slot",
            }
        ):
            return "lifecycle_operation"
        return "retrieval_operation"
    if status == "superseded":
        return "archival_object"
    if str(entry.get("memory_tier") or "") == "quarantine_memory":
        return "quarantine_object"
    if str(entry.get("memory_tier") or "") == "working_memory":
        return "active_state_object"
    return "long_term_recall_object"


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
                "memory_tier": _slot_memory_tier(
                    {
                        "memory_type": memory_type,
                        "managed": memory_type in managed_memory_types,
                        "status_counts": _memory_operation_slot_status_counts(
                            record_tuple
                        ),
                    },
                    managed_memory_types=managed_memory_types,
                ),
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
