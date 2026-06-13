"""Question-only operation analysis for clean routing."""

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


TASKS = {"single_fact", "multi_evidence", "preference_advice", "temporal", "recency_state"}
OPERATIONS = {
    "none",
    "count",
    "sum",
    "compare",
    "list",
    "set_relation",
    "duration",
    "order",
    "date_time",
    "preference",
    "recency",
}
TEMPORAL_SUBTYPES = {"none", "duration", "order", "date_time"}
ANSWER_SLOTS = {
    "fact",
    "person",
    "place",
    "time",
    "duration",
    "count",
    "list",
    "event",
    "preference",
    "state",
    "other",
}


@dataclass(frozen=True)
class QuestionAnalysisCacheStats:
    hits: int = 0
    misses: int = 0
    writes: int = 0

    def to_dict(self) -> dict[str, int]:
        return asdict(self)


@dataclass(frozen=True)
class QuestionAnalysisResult:
    task: str
    operation: str
    temporal_subtype: str
    answer_slot: str
    target_phrases: tuple[str, ...] = ()
    temporal_hints: tuple[str, ...] = ()
    confidence: float = 0.0
    route_source: str = "heuristic"
    token_usage: TokenUsage = TokenUsage()
    raw_response: str | None = None

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["token_usage"] = self.token_usage.to_dict()
        return result


class OpenAICompatibleQuestionAnalyzer:
    """LLM analyzer that uses only question text and visible question time."""

    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        temperature: float,
        max_tokens: int,
        timeout: float,
        api_key_env: str | None = None,
    ):
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._timeout = timeout
        self._api_key_env = api_key_env

    def analyze(self, *, question: str, question_time: str | None) -> QuestionAnalysisResult:
        prompt = _analysis_prompt(question=question, question_time=question_time)
        response = self._chat_completion(prompt)
        message = response["choices"][0]["message"]
        raw_content = _message_text(message).strip()
        usage = response.get("usage") or {}
        prompt_tokens = int(usage.get("prompt_tokens") or 0)
        completion_tokens = int(usage.get("completion_tokens") or 0)
        total_tokens = int(usage.get("total_tokens") or prompt_tokens + completion_tokens)
        result = _parse_analysis(raw_content)
        return replace(
            result,
            route_source="llm_question_analysis",
            token_usage=TokenUsage(query_tokens=total_tokens),
            raw_response=json.dumps(
                {
                    "content": raw_content,
                    "id": response.get("id"),
                    "model": response.get("model"),
                    "usage": usage,
                },
                ensure_ascii=False,
                sort_keys=True,
            ),
        )

    def _chat_completion(self, prompt: str) -> dict[str, Any]:
        endpoint = self._base_url + "/chat/completions"
        payload = {
            "model": self._model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self._temperature,
            "max_tokens": self._max_tokens,
            "response_format": {"type": "json_object"},
        }
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
            raise RuntimeError(
                f"Question analysis request failed: {error.code} {body}"
            ) from error


class CachedQuestionAnalyzer:
    """Prompt-keyed cache for question analysis calls."""

    def __init__(self, inner: Any, *, cache_path: str, namespace: str):
        self._inner = inner
        self._cache_path = Path(cache_path).expanduser()
        self._namespace = namespace
        self._connection: sqlite3.Connection | None = None
        self._cache_stats = QuestionAnalysisCacheStats()

    def analyze(self, *, question: str, question_time: str | None) -> QuestionAnalysisResult:
        key = _cache_key(
            namespace=self._namespace,
            question=question,
            question_time=question_time,
        )
        payload = self._get(key)
        if payload is None:
            result = self._inner.analyze(question=question, question_time=question_time)
            payload = result.to_dict()
            self._put(key, payload)
        token_usage = payload.get("token_usage") or {}
        return QuestionAnalysisResult(
            task=str(payload.get("task") or "single_fact"),
            operation=str(payload.get("operation") or "none"),
            temporal_subtype=str(payload.get("temporal_subtype") or "none"),
            answer_slot=str(payload.get("answer_slot") or "fact"),
            target_phrases=tuple(str(value) for value in payload.get("target_phrases") or ()),
            temporal_hints=tuple(str(value) for value in payload.get("temporal_hints") or ()),
            confidence=float(payload.get("confidence") or 0.0),
            route_source=str(payload.get("route_source") or "llm_question_analysis"),
            token_usage=TokenUsage(
                build_tokens=int(token_usage.get("build_tokens") or 0),
                query_tokens=int(token_usage.get("query_tokens") or 0),
            ),
            raw_response=payload.get("raw_response"),
        )

    def stats(self) -> QuestionAnalysisCacheStats:
        return self._cache_stats

    def _get(self, key: str) -> dict[str, Any] | None:
        row = self._connect().execute(
            "SELECT payload_json FROM question_analysis_cache WHERE cache_key = ?",
            (key,),
        ).fetchone()
        if row is None:
            self._cache_stats = replace(
                self._cache_stats,
                misses=self._cache_stats.misses + 1,
            )
            return None
        self._cache_stats = replace(
            self._cache_stats,
            hits=self._cache_stats.hits + 1,
        )
        return json.loads(str(row[0]))

    def _put(self, key: str, payload: dict[str, Any]) -> None:
        self._connect().execute(
            "INSERT OR REPLACE INTO question_analysis_cache(cache_key, payload_json) VALUES(?, ?)",
            (key, json.dumps(payload, ensure_ascii=False, sort_keys=True)),
        )
        self._connect().commit()
        self._cache_stats = replace(
            self._cache_stats,
            writes=self._cache_stats.writes + 1,
        )

    def _connect(self) -> sqlite3.Connection:
        if self._connection is None:
            self._cache_path.parent.mkdir(parents=True, exist_ok=True)
            self._connection = sqlite3.connect(str(self._cache_path), timeout=30.0)
            self._connection.execute("PRAGMA busy_timeout = 30000")
            self._connection.execute("PRAGMA journal_mode = WAL")
            self._connection.execute(
                "CREATE TABLE IF NOT EXISTS question_analysis_cache("
                "cache_key TEXT PRIMARY KEY, "
                "payload_json TEXT NOT NULL)"
            )
            self._connection.commit()
        return self._connection


def route_from_question_analysis(
    analysis: QuestionAnalysisResult,
    fallback: RouteResult,
) -> RouteResult:
    """Map general question operation analysis to existing information needs."""

    operation = analysis.operation
    task = analysis.task
    temporal_subtype = analysis.temporal_subtype
    signals = [
        "llm_question_analysis",
        f"operation:{operation}",
        f"answer_slot:{analysis.answer_slot}",
    ]
    if analysis.temporal_hints or temporal_subtype != "none":
        signals.append("temporal")
    if task == "recency_state" or operation == "recency":
        signals.append("recent_or_current")
        return RouteResult("current_state", tuple(signals), retrieval_multiplier=2)
    if task == "preference_advice" or operation == "preference":
        signals.append("profile_or_preference")
        return RouteResult("profile_preference", tuple(signals), retrieval_multiplier=2)
    if operation in {"count", "sum", "list", "set_relation"}:
        signals.append("list_or_count")
        return RouteResult("list_count", tuple(signals), retrieval_multiplier=3)
    if operation in {"duration", "order", "date_time"} or task == "temporal":
        signals.append("temporal")
        return RouteResult("temporal_lookup", tuple(dict.fromkeys(signals)), retrieval_multiplier=2)
    if operation == "compare":
        signals.append("list_or_count")
        return RouteResult("list_count", tuple(signals), retrieval_multiplier=3)
    if not analysis.raw_response:
        return fallback
    return RouteResult("fact_lookup", tuple(signals), retrieval_multiplier=1)


def _analysis_prompt(*, question: str, question_time: str | None) -> str:
    return "\n".join(
        [
            "Classify a memory question for a general retrieval-and-answer pipeline.",
            "Use only the question text and visible question date.",
            "Do not use or infer hidden benchmark metadata, row identifiers, reference solutions, offline evaluator results, or test feedback.",
            "Do not answer the question.",
            "",
            f"Question date: {question_time or ''}",
            f"Question: {question}",
            "",
            "Return ONLY a JSON object with this schema:",
            "{",
            '  "task": "single_fact|multi_evidence|preference_advice|temporal|recency_state",',
            '  "operation": "none|count|sum|compare|list|set_relation|duration|order|date_time|preference|recency",',
            '  "temporal_subtype": "none|duration|order|date_time",',
            '  "answer_slot": "fact|person|place|time|duration|count|list|event|preference|state|other",',
            '  "target_phrases": ["short concrete entity/action/object/time-scope phrases from the question"],',
            '  "temporal_hints": ["short date/range/search phrase from the question, or empty list"],',
            '  "confidence": 0.0',
            "}",
        ]
    )


def _parse_analysis(text: str) -> QuestionAnalysisResult:
    parsed = _extract_json_object(text) or {}
    task = _choice(parsed.get("task"), TASKS, "single_fact")
    operation = _choice(parsed.get("operation"), OPERATIONS, "none")
    temporal_subtype = _choice(
        parsed.get("temporal_subtype"),
        TEMPORAL_SUBTYPES,
        "none",
    )
    answer_slot = _choice(parsed.get("answer_slot"), ANSWER_SLOTS, "fact")
    try:
        confidence = float(parsed.get("confidence", 0.0))
    except (TypeError, ValueError):
        confidence = 0.0
    return QuestionAnalysisResult(
        task=task,
        operation=operation,
        temporal_subtype=temporal_subtype,
        answer_slot=answer_slot,
        target_phrases=_string_tuple(parsed.get("target_phrases"), limit=8),
        temporal_hints=_string_tuple(parsed.get("temporal_hints"), limit=6),
        confidence=max(0.0, min(1.0, confidence)),
        raw_response=text,
    )


def _choice(value: object, choices: set[str], default: str) -> str:
    text = str(value or default).strip()
    return text if text in choices else default


def _string_tuple(value: object, *, limit: int) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    result: list[str] = []
    seen: set[str] = set()
    for item in value:
        text = " ".join(str(item or "").split())[:120]
        key = text.lower()
        if not text or key in seen:
            continue
        result.append(text)
        seen.add(key)
        if len(result) >= limit:
            break
    return tuple(result)


def _extract_json_object(text: str) -> dict[str, Any] | None:
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start < 0 or end <= start:
            return None
        try:
            value = json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            return None
    return value if isinstance(value, dict) else None


def _message_text(message: dict[str, Any]) -> str:
    for key in ("content", "reasoning", "reasoning_content"):
        value = message.get(key)
        if value is not None:
            return str(value)
    return ""


def _cache_key(*, namespace: str, question: str, question_time: str | None) -> str:
    payload = json.dumps(
        {"namespace": namespace, "question": question, "question_time": question_time},
        ensure_ascii=False,
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
