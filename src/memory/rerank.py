"""OpenAI-compatible rerank client and clean hit reordering helpers."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

from common.schemas import RetrievalHit, Turn


@dataclass(frozen=True)
class RerankResult:
    scores: tuple[float, ...]
    response: dict[str, Any]
    total_tokens: int


class OpenAICompatibleRerankClient:
    """Client for local vLLM-compatible rerank services."""

    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        timeout: float,
        batch_size: int = 0,
        api_key_env: str | None = None,
        api_key: str | None = None,
    ):
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._timeout = timeout
        self._batch_size = max(0, int(batch_size))
        self._api_key_env = api_key_env
        self._api_key = api_key

    def rerank(self, *, query: str, documents: list[str]) -> RerankResult:
        if not documents:
            return RerankResult(scores=(), response={"results": []}, total_tokens=0)
        if self._batch_size <= 0 or self._batch_size >= len(documents):
            return self._rerank_batch(query=query, documents=documents, offset=0)

        scores = [float("-inf")] * len(documents)
        results: list[dict[str, Any]] = []
        total_tokens = 0
        for start in range(0, len(documents), self._batch_size):
            batch = documents[start : start + self._batch_size]
            result = self._rerank_batch(query=query, documents=batch, offset=start)
            total_tokens += result.total_tokens
            for index, score in enumerate(result.scores, start=start):
                scores[index] = score
            results.extend(result.response.get("results") or [])

        return RerankResult(
            scores=tuple(scores),
            response={
                "id": None,
                "model": self._model,
                "usage": {"total_tokens": total_tokens},
                "results": results,
            },
            total_tokens=total_tokens,
        )

    def _rerank_batch(
        self,
        *,
        query: str,
        documents: list[str],
        offset: int,
    ) -> RerankResult:
        request_body = json.dumps(
            {
                "model": self._model,
                "query": query,
                "documents": documents,
            },
            ensure_ascii=False,
        ).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        api_key = self._api_key
        if api_key is None and self._api_key_env:
            api_key = os.environ.get(self._api_key_env)
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        request = urllib.request.Request(
            self._base_url + "/rerank",
            data=request_body,
            headers=headers,
            method="POST",
        )
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        try:
            with opener.open(request, timeout=self._timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            body = error.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Rerank request failed: {error.code} {body}") from error

        scores = [float("-inf")] * len(documents)
        for item in payload.get("results") or []:
            if not isinstance(item, dict):
                continue
            index = int(item.get("index", -1))
            if 0 <= index < len(scores):
                raw_score = item.get("relevance_score", item.get("score"))
                scores[index] = float(raw_score)
        usage = payload.get("usage") if isinstance(payload, dict) else None
        total_tokens = int((usage or {}).get("total_tokens") or 0)
        return RerankResult(
            scores=tuple(scores),
            response=_compact_response(payload, index_offset=offset),
            total_tokens=total_tokens,
        )


def rerank_hits_with_anchor_retention(
    *,
    hits: tuple[RetrievalHit, ...],
    scores: tuple[float, ...],
    top_k: int,
    anchor_keep: int = 0,
    anchor_after_top: int = 0,
) -> tuple[RetrievalHit, ...]:
    """Sort hits by rerank score while retaining high-rank retrieval anchors."""

    if not hits or top_k <= 0:
        return ()
    if len(hits) != len(scores):
        raise ValueError("rerank scores must align with hits")

    scored_hits = sorted(
        zip(hits, scores, range(len(hits)), strict=True),
        key=lambda item: (-item[1], item[2]),
    )
    reranked = tuple(
        _reranked_hit(hit=hit, score=score, rank=rank)
        for rank, (hit, score, _index) in enumerate(scored_hits, start=1)
    )
    by_source_id = {hit.source_id: hit for hit in reranked}
    selected: list[RetrievalHit] = []
    seen: set[str] = set()

    def add(hit: RetrievalHit) -> None:
        if hit.source_id in seen:
            return
        seen.add(hit.source_id)
        selected.append(hit)

    for hit in reranked[: max(0, anchor_after_top)]:
        add(hit)
    for hit in hits[: max(0, anchor_keep)]:
        add(by_source_id.get(hit.source_id, hit))
    for hit in reranked:
        add(hit)
    return tuple(
        RetrievalHit(
            source_id=hit.source_id,
            score=hit.score,
            rank=rank,
            retriever=hit.retriever,
            matched_terms=hit.matched_terms,
        )
        for rank, hit in enumerate(selected[:top_k], start=1)
    )


def format_rerank_turn_document(turn: Turn, *, max_chars: int = 0) -> str:
    text = f"{turn.role}: {turn.text}"
    if turn.timestamp:
        text = f"Date: {turn.timestamp}\n{text}"
    return truncate_for_rerank(text, max_chars=max_chars)


def truncate_for_rerank(document: str, *, max_chars: int = 0) -> str:
    if max_chars <= 0 or len(document) <= max_chars:
        return document
    marker = "\n...\n"
    if max_chars <= len(marker) + 64:
        return document[:max_chars]
    left = (max_chars - len(marker)) // 2
    right = max_chars - len(marker) - left
    return f"{document[:left]}{marker}{document[-right:]}"


def _reranked_hit(*, hit: RetrievalHit, score: float, rank: int) -> RetrievalHit:
    retriever = hit.retriever
    if "rerank" not in retriever:
        retriever = f"{retriever}+rerank"
    return RetrievalHit(
        source_id=hit.source_id,
        score=score,
        rank=rank,
        retriever=retriever,
        matched_terms=hit.matched_terms,
    )


def _compact_response(payload: dict[str, Any], *, index_offset: int) -> dict[str, Any]:
    return {
        "id": payload.get("id"),
        "model": payload.get("model"),
        "usage": payload.get("usage"),
        "results": [
            {
                "index": int(item.get("index", 0)) + index_offset,
                "relevance_score": item.get("relevance_score", item.get("score")),
            }
            for item in payload.get("results") or []
            if isinstance(item, dict)
        ],
    }
