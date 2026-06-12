"""OpenAI-compatible embedding client."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class EmbeddingBatch:
    vectors: tuple[tuple[float, ...], ...]
    total_tokens: int


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
