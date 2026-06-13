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

from common.schemas import TokenUsage, Turn


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

    def to_dict(self) -> dict[str, Any]:
        return {
            "records": [record.to_dict() for record in self.records],
            "token_usage": self.token_usage.to_dict(),
            "cache": self.cache_stats.to_dict(),
            "chunks": self.chunks,
            "cache_enabled": self.cache_enabled,
            "builder": self.builder,
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
        cache_path: str | None = None,
        cache_namespace: str | None = None,
        api_key_env: str | None = None,
        temporal_fields: bool = False,
    ):
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._timeout = timeout
        self._max_turns_per_chunk = max(1, max_turns_per_chunk)
        self._max_chars_per_turn = max(80, max_chars_per_turn)
        self._max_records_per_chunk = max(1, max_records_per_chunk)
        self._cache_path = Path(cache_path).expanduser() if cache_path else None
        self._cache_namespace = cache_namespace or model
        self._api_key_env = api_key_env
        self._temporal_fields = temporal_fields
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
            )

        all_records: list[MemoryRecord] = []
        total_tokens = 0
        chunks = _chunk_turns(turns, self._max_turns_per_chunk)
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
            total_tokens += _usage_total_tokens(payload.get("usage"))

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
                )
                if record is not None:
                    all_records.append(record)

        managed = _manage_records(tuple(all_records))
        return BuiltMemory(
            records=managed,
            token_usage=TokenUsage(build_tokens=total_tokens, query_tokens=0),
            cache_stats=_cache_stats_delta(cache_stats_before, self._cache_stats),
            chunks=len(chunks),
            cache_enabled=self._cache_path is not None,
            builder=self._model,
        )

    def _build_prompt(self, turns: tuple[Turn, ...]) -> str:
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

    def _chat_completion(self, prompt: str) -> dict[str, Any]:
        endpoint = self._base_url + "/chat/completions"
        request_body = json.dumps(
            {
                "model": self._model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": self._temperature,
                "max_tokens": self._max_tokens,
            }
        ).encode("utf-8")
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


def _chunk_turns(turns: tuple[Turn, ...], max_turns_per_chunk: int) -> tuple[tuple[Turn, ...], ...]:
    chunks = []
    for start in range(0, len(turns), max_turns_per_chunk):
        chunks.append(turns[start : start + max_turns_per_chunk])
    return tuple(chunks)


def _usage_total_tokens(usage: Any) -> int:
    if not isinstance(usage, dict):
        return 0
    total = usage.get("total_tokens")
    if total is not None:
        return int(total)
    return int(usage.get("prompt_tokens") or 0) + int(usage.get("completion_tokens") or 0)


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
    valid_from = _clean_text(raw_record.get("valid_from")) or event_time or timestamp
    valid_to = _clean_text(raw_record.get("valid_to")) or None
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


def _manage_records(records: tuple[MemoryRecord, ...]) -> tuple[MemoryRecord, ...]:
    deduped: dict[tuple[str, str, tuple[str, ...]], MemoryRecord] = {}
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
        existing = deduped.get(key)
        if existing is None or record.confidence > existing.confidence:
            deduped[key] = record

    managed = list(deduped.values())
    grouped: dict[tuple[str, str, str], list[MemoryRecord]] = defaultdict(list)
    for record in managed:
        if record.memory_type not in {"preference", "profile", "state", "fact"}:
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
    return tuple(result)


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
