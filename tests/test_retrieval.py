from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from agent_memory.embeddings import EmbeddingBatch
from agent_memory.retrieval import (
    DenseEmbeddingRetriever,
    LexicalBM25Retriever,
    SessionBM25Retriever,
    SessionDocument,
    prepend_protected_hits,
)
from agent_memory.schemas import RetrievalHit
from agent_memory.schemas import Turn


class RetrievalTest(unittest.TestCase):
    def test_query_stopwords_are_optional(self) -> None:
        turns = (
            Turn(
                source_id="generic",
                session_id="s1",
                turn_index=0,
                role="speaker",
                text="what to be in her",
            ),
            Turn(
                source_id="specific",
                session_id="s1",
                turn_index=1,
                role="speaker",
                text="Caroline plans to pursue counseling.",
            ),
        )

        raw_hits = LexicalBM25Retriever(turns).retrieve(
            "What would Caroline be likely to pursue in her education?",
            top_k=2,
        )
        filtered_hits = LexicalBM25Retriever(
            turns,
            drop_query_stopwords=True,
        ).retrieve(
            "What would Caroline be likely to pursue in her education?",
            top_k=2,
        )

        self.assertEqual(raw_hits[0].source_id, "generic")
        self.assertEqual(filtered_hits[0].source_id, "specific")

    def test_session_bm25_retrieves_coarse_session(self) -> None:
        documents = (
            SessionDocument(
                session_id="session_1",
                text="when did in when did in",
                turn_count=1,
            ),
            SessionDocument(
                session_id="session_2",
                text="Melanie mentioned camping in July.",
                turn_count=1,
            ),
        )

        hits = SessionBM25Retriever(
            documents,
            drop_query_stopwords=True,
        ).retrieve(
            "When did Melanie go camping in July?",
            top_k=1,
        )

        self.assertEqual(hits[0].source_id, "session_2")

    def test_dense_retriever_scores_embedding_similarity(self) -> None:
        turns = (
            Turn(
                source_id="coffee",
                session_id="s1",
                turn_index=0,
                role="speaker",
                text="coffee creamer coupon",
            ),
            Turn(
                source_id="career",
                session_id="s1",
                turn_index=1,
                role="speaker",
                text="counseling and mental health career",
            ),
        )

        result = DenseEmbeddingRetriever(turns, _FakeEmbedder()).retrieve(
            "What education field would Caroline pursue?",
            top_k=2,
        )

        self.assertEqual(result.hits[0].source_id, "career")
        self.assertGreater(result.embedding_tokens, 0)

    def test_prepend_protected_hits_preserves_primary_order(self) -> None:
        protected = (
            RetrievalHit("lexical-a", 10.0, 1, "lexical_bm25"),
            RetrievalHit("lexical-b", 9.0, 2, "lexical_bm25"),
        )
        fused = (
            RetrievalHit("dense-a", 0.4, 1, "dense_embedding"),
            RetrievalHit("lexical-a", 0.3, 2, "lexical_bm25+dense_embedding"),
        )

        hits = prepend_protected_hits(protected, fused, top_k=3)

        self.assertEqual([hit.source_id for hit in hits], ["lexical-a", "lexical-b", "dense-a"])


class _FakeEmbedder:
    def embed_texts(self, texts: list[str], input_type: str) -> EmbeddingBatch:
        vectors = []
        for text in texts:
            if any(term in text.lower() for term in ("career", "field", "education")):
                vectors.append((1.0, 0.0))
            else:
                vectors.append((0.0, 1.0))
        return EmbeddingBatch(vectors=tuple(vectors), total_tokens=len(texts))


if __name__ == "__main__":
    unittest.main()
