"""OpenAI-compatible embedding client."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class EmbeddingBatch:
    vectors: tuple[tuple[float, ...], ...]
    total_tokens: int


@dataclass(frozen=True)
class EmbeddingCacheStats:
    hits: int = 0
    misses: int = 0
    writes: int = 0

    def to_dict(self) -> dict[str, int]:
        return {
            "hits": self.hits,
            "misses": self.misses,
            "writes": self.writes,
        }


class OpenAICompatibleEmbeddingClient:
    """Embedding client for local vLLM/OpenAI-compatible services."""

    def __init__(
        self,
        base_url: str,
        model: str,
        timeout: float,
    ):
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._timeout = timeout

    def embed_texts(self, texts: list[str], input_type: str) -> EmbeddingBatch:
        if not texts:
            return EmbeddingBatch(vectors=(), total_tokens=0)
        endpoint = self._base_url + "/embeddings"
        request_body = json.dumps(
            {
                "model": self._model,
                "input": texts,
                "input_type": input_type,
            }
        ).encode("utf-8")
        request = urllib.request.Request(
            endpoint,
            data=request_body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        try:
            with opener.open(request, timeout=self._timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            body = error.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Embedding request failed: {error.code} {body}") from error

        vectors_by_index: dict[int, tuple[float, ...]] = {}
        for item in payload.get("data", []):
            vectors_by_index[int(item["index"])] = tuple(
                float(value) for value in item["embedding"]
            )
        vectors = tuple(vectors_by_index[index] for index in range(len(texts)))
        usage = payload.get("usage") or {}
        return EmbeddingBatch(
            vectors=vectors,
            total_tokens=int(usage.get("total_tokens") or usage.get("prompt_tokens") or 0),
        )


class CachedEmbeddingClient:
    """SQLite-backed cache wrapper for deterministic text embeddings."""

    def __init__(
        self,
        delegate: Any,
        cache_path: str | Path,
        namespace: str,
    ):
        self._delegate = delegate
        self._cache_path = Path(cache_path).expanduser()
        self._namespace = namespace
        self._stats = EmbeddingCacheStats()
        self._connection: sqlite3.Connection | None = None

    @property
    def cache_path(self) -> Path:
        return self._cache_path

    @property
    def namespace(self) -> str:
        return self._namespace

    def stats(self) -> EmbeddingCacheStats:
        return self._stats

    def embed_texts(self, texts: list[str], input_type: str) -> EmbeddingBatch:
        if not texts:
            return EmbeddingBatch(vectors=(), total_tokens=0)

        cached_vectors: dict[str, tuple[float, ...]] = {}
        missing_by_key: dict[str, str] = {}
        keys = [_cache_key(self._namespace, input_type, text) for text in texts]

        for key, text in zip(keys, texts, strict=True):
            vector = self._get(key)
            if vector is None:
                missing_by_key.setdefault(key, text)
            else:
                cached_vectors[key] = vector

        hits = sum(1 for key in keys if key in cached_vectors)
        misses = len(keys) - hits
        service_tokens = 0
        writes = 0

        if missing_by_key:
            missing_keys = list(missing_by_key)
            missing_texts = [missing_by_key[key] for key in missing_keys]
            batch = self._delegate.embed_texts(missing_texts, input_type=input_type)
            service_tokens = batch.total_tokens
            for key, vector in zip(missing_keys, batch.vectors, strict=True):
                cached_vectors[key] = vector
                self._put(key, vector)
                writes += 1

        self._stats = EmbeddingCacheStats(
            hits=self._stats.hits + hits,
            misses=self._stats.misses + misses,
            writes=self._stats.writes + writes,
        )
        return EmbeddingBatch(
            vectors=tuple(cached_vectors[key] for key in keys),
            total_tokens=service_tokens,
        )

    def _get(self, key: str) -> tuple[float, ...] | None:
        row = self._connect().execute(
            "SELECT vector_json FROM embeddings WHERE cache_key = ?",
            (key,),
        ).fetchone()
        if row is None:
            return None
        return tuple(float(value) for value in json.loads(str(row[0])))

    def _put(self, key: str, vector: tuple[float, ...]) -> None:
        self._connect().execute(
            "INSERT OR REPLACE INTO embeddings(cache_key, vector_json) VALUES(?, ?)",
            (key, json.dumps(vector, separators=(",", ":"))),
        )
        self._connect().commit()

    def _connect(self) -> sqlite3.Connection:
        if self._connection is None:
            self._cache_path.parent.mkdir(parents=True, exist_ok=True)
            self._connection = sqlite3.connect(str(self._cache_path))
            self._connection.execute(
                "CREATE TABLE IF NOT EXISTS embeddings("
                "cache_key TEXT PRIMARY KEY, "
                "vector_json TEXT NOT NULL)"
            )
            self._connection.commit()
        return self._connection


def _cache_key(namespace: str, input_type: str, text: str) -> str:
    digest = hashlib.sha256()
    digest.update(namespace.encode("utf-8"))
    digest.update(b"\0")
    digest.update(input_type.encode("utf-8"))
    digest.update(b"\0")
    digest.update(text.encode("utf-8"))
    return digest.hexdigest()
