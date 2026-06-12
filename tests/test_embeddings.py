from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from agent_memory.embeddings import CachedEmbeddingClient, EmbeddingBatch


class EmbeddingCacheTest(unittest.TestCase):
    def test_cached_embedding_client_avoids_repeated_service_tokens(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            client = CachedEmbeddingClient(
                _CountingEmbedder(),
                cache_path=Path(tmpdir) / "embeddings.sqlite",
                namespace="test-model",
            )

            first = client.embed_texts(["alpha", "beta"], input_type="document")
            second = client.embed_texts(["alpha", "beta"], input_type="document")

        self.assertEqual(first.vectors, second.vectors)
        self.assertEqual(first.total_tokens, 2)
        self.assertEqual(second.total_tokens, 0)
        self.assertEqual(
            client.stats().to_dict(),
            {"hits": 2, "misses": 2, "writes": 2},
        )

    def test_cached_embedding_client_batches_partial_misses(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            embedder = _CountingEmbedder()
            client = CachedEmbeddingClient(
                embedder,
                cache_path=Path(tmpdir) / "embeddings.sqlite",
                namespace="test-model",
            )

            client.embed_texts(["alpha"], input_type="document")
            mixed = client.embed_texts(["alpha", "gamma"], input_type="document")

        self.assertEqual(mixed.total_tokens, 1)
        self.assertEqual(embedder.calls, 2)
        self.assertEqual(
            client.stats().to_dict(),
            {"hits": 1, "misses": 2, "writes": 2},
        )


class _CountingEmbedder:
    def __init__(self) -> None:
        self.calls = 0

    def embed_texts(self, texts: list[str], input_type: str) -> EmbeddingBatch:
        del input_type
        self.calls += 1
        vectors = tuple((float(len(text)), float(sum(ord(ch) for ch in text))) for text in texts)
        return EmbeddingBatch(vectors=vectors, total_tokens=len(texts))


if __name__ == "__main__":
    unittest.main()
