"""Question-only retrieval planning for clean multi-query search."""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any

from common.schemas import RouteResult, TokenUsage


@dataclass(frozen=True)
class QueryPlannerCacheStats:
    hits: int = 0
    misses: int = 0
    writes: int = 0

    def to_dict(self) -> dict[str, int]:
        return asdict(self)


@dataclass(frozen=True)
class RetrievalPlan:
    queries: tuple[str, ...]
    token_usage: TokenUsage = TokenUsage()
    cache_stats: QueryPlannerCacheStats = QueryPlannerCacheStats()
    cache_enabled: bool = False
    planner: str = "null"
    raw_response: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "queries": list(self.queries),
            "token_usage": self.token_usage.to_dict(),
            "cache": self.cache_stats.to_dict(),
            "cache_enabled": self.cache_enabled,
            "planner": self.planner,
            "raw_response": self.raw_response,
        }


class NullQueryPlanner:
    """No-op planner used by default and for ablations."""

    def plan(
        self,
        question: str,
        question_time: str | None,
        route: RouteResult,
    ) -> RetrievalPlan:
        del question_time, route
        return RetrievalPlan(queries=(question,), planner="null")


class OpenAICompatibleQueryPlanner:
    """LLM planner that sees only the question, question time, and clean route."""

    def __init__(
        self,
        base_url: str,
        model: str,
        temperature: float,
        max_tokens: int,
        timeout: float,
        max_queries: int,
        max_query_chars: int,
        cache_path: str | None = None,
        cache_namespace: str | None = None,
        api_key_env: str | None = None,
        response_format_json: bool = False,
    ):
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._timeout = timeout
        self._max_queries = max(1, max_queries)
        self._max_query_chars = max(32, max_query_chars)
        self._cache_path = Path(cache_path).expanduser() if cache_path else None
        self._cache_namespace = cache_namespace or model
        self._api_key_env = api_key_env
        self._response_format_json = response_format_json
        self._connection: sqlite3.Connection | None = None
        self._cache_stats = QueryPlannerCacheStats()

    def plan(
        self,
        question: str,
        question_time: str | None,
        route: RouteResult,
    ) -> RetrievalPlan:
        cache_stats_before = self._cache_stats
        prompt = _build_planner_prompt(
            question=question,
            question_time=question_time,
            route=route,
            max_queries=self._max_queries,
        )
        cache_key = _cache_key(
            self._cache_namespace,
            self._model,
            self._max_tokens,
            self._max_queries,
            self._max_query_chars,
            self._response_format_json,
            prompt,
        )
        payload = self._get(cache_key)
        if payload is None:
            response = self._chat_completion(prompt)
            message = response["choices"][0]["message"]
            payload = {
                "content": _message_text(message).strip(),
                "usage": response.get("usage") or {},
            }
            self._put(cache_key, payload)

        queries = _normalize_queries(
            question=question,
            raw_queries=_queries_from_payload(str(payload.get("content") or "")),
            max_queries=self._max_queries,
            max_query_chars=self._max_query_chars,
        )
        return RetrievalPlan(
            queries=queries,
            token_usage=TokenUsage(
                build_tokens=0,
                query_tokens=_usage_total_tokens(payload.get("usage")),
            ),
            cache_stats=_cache_stats_delta(cache_stats_before, self._cache_stats),
            cache_enabled=self._cache_path is not None,
            planner=self._model,
            raw_response=str(payload.get("content") or ""),
        )

    def _chat_completion(self, prompt: str) -> dict[str, Any]:
        endpoint = self._base_url + "/chat/completions"
        payload: dict[str, Any] = {
            "model": self._model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self._temperature,
            "max_tokens": self._max_tokens,
        }
        if self._response_format_json:
            payload["response_format"] = {"type": "json_object"}
        request_body = json.dumps(
            payload,
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
            raise RuntimeError(f"Query planner request failed: {error.code} {body}") from error

    def _get(self, key: str) -> dict[str, Any] | None:
        if self._cache_path is None:
            self._cache_stats = replace(
                self._cache_stats,
                misses=self._cache_stats.misses + 1,
            )
            return None
        row = self._connect().execute(
            "SELECT payload_json FROM query_plans WHERE cache_key = ?",
            (key,),
        ).fetchone()
        if row is None:
            self._cache_stats = replace(
                self._cache_stats,
                misses=self._cache_stats.misses + 1,
            )
            return None
        self._cache_stats = replace(self._cache_stats, hits=self._cache_stats.hits + 1)
        return json.loads(str(row[0]))

    def _put(self, key: str, payload: dict[str, Any]) -> None:
        if self._cache_path is None:
            return
        self._connect().execute(
            "INSERT OR REPLACE INTO query_plans(cache_key, payload_json) VALUES(?, ?)",
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
                "CREATE TABLE IF NOT EXISTS query_plans("
                "cache_key TEXT PRIMARY KEY, "
                "payload_json TEXT NOT NULL)"
            )
            self._connection.commit()
        return self._connection


def _build_planner_prompt(
    *,
    question: str,
    question_time: str | None,
    route: RouteResult,
    max_queries: int,
) -> str:
    return "\n".join(
        [
            "Generate clean retrieval queries for a long-term memory system.",
            "Use only the question, question time, and information need below.",
            "Do not answer the question.",
            "Do not use gold answers, judge output, benchmark labels, sample ids, qids, row indices, or test feedback.",
            "The original question is already searched; add only useful complementary queries.",
            "Good queries preserve exact names, objects, quantities, time phrases, and relationship words.",
            "For list, count, comparison, or multi-part questions, include separate focused queries for the important entities or subevents.",
            "For current or update questions, include queries that can retrieve older and newer states for the same subject.",
            f"Return at most {max_queries} total queries including the original question if you repeat it.",
            "Return ONLY valid JSON with this schema: {\"queries\":[\"...\"]}",
            "",
            f"Question time: {question_time or 'not provided'}",
            f"Information need: {route.information_need}",
            f"Route signals: {', '.join(route.signals) if route.signals else 'none'}",
            f"Question: {question}",
        ]
    )


def _queries_from_payload(content: str) -> list[str]:
    payload = _parse_json_object(content)
    if not isinstance(payload, dict):
        return []
    queries = payload.get("queries")
    if not isinstance(queries, list):
        return []
    return [str(query) for query in queries]


def _normalize_queries(
    *,
    question: str,
    raw_queries: list[str],
    max_queries: int,
    max_query_chars: int,
) -> tuple[str, ...]:
    queries: list[str] = []
    seen: set[str] = set()
    for query in (question, *raw_queries):
        normalized = " ".join(str(query).split())
        if not normalized:
            continue
        normalized = normalized[:max_query_chars].rstrip()
        key = normalized.lower()
        if key in seen:
            continue
        seen.add(key)
        queries.append(normalized)
        if len(queries) >= max_queries:
            break
    return tuple(queries) or (question,)


def _parse_json_object(content: str) -> Any:
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        start = content.find("{")
        end = content.rfind("}")
        if start < 0 or end <= start:
            return None
        try:
            return json.loads(content[start : end + 1])
        except json.JSONDecodeError:
            return None


def _message_text(message: dict[str, Any]) -> str:
    for key in ("content", "reasoning", "reasoning_content"):
        value = message.get(key)
        if value is not None:
            return str(value)
    return ""


def _usage_total_tokens(usage: Any) -> int:
    if not isinstance(usage, dict):
        return 0
    total = usage.get("total_tokens")
    if total is not None:
        return int(total)
    return int(usage.get("prompt_tokens") or 0) + int(usage.get("completion_tokens") or 0)


def _cache_key(
    namespace: str,
    model: str,
    max_tokens: int,
    max_queries: int,
    max_query_chars: int,
    response_format_json: bool,
    prompt: str,
) -> str:
    digest = hashlib.sha256()
    for part in (
        namespace,
        model,
        str(max_tokens),
        str(max_queries),
        str(max_query_chars),
        str(response_format_json),
        prompt,
    ):
        digest.update(part.encode("utf-8"))
        digest.update(b"\0")
    return digest.hexdigest()


def _cache_stats_delta(
    before: QueryPlannerCacheStats,
    after: QueryPlannerCacheStats,
) -> QueryPlannerCacheStats:
    return QueryPlannerCacheStats(
        hits=after.hits - before.hits,
        misses=after.misses - before.misses,
        writes=after.writes - before.writes,
    )
