from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from memory.embeddings import EmbeddingBatch
from memory.build import MemoryRecord
from memory.retrieval import (
    DenseEmbeddingRetriever,
    LexicalBM25Retriever,
    _DENSE_DOCUMENT_CACHE,
    _DENSE_DOCUMENT_CACHE_LOCK,
    _DENSE_DOCUMENT_CACHE_LOCKS,
    prepend_protected_hits,
)
from memory.rerank import (
    format_rerank_evidence_document,
    format_rerank_turn_document,
    rerank_hits_with_anchor_retention,
)
from common.schemas import RetrievalHit
from common.schemas import Turn


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

    def test_query_stopwords_drop_pronouns_and_prepositions(self) -> None:
        turns = (
            Turn(
                source_id="generic",
                session_id="s1",
                turn_index=0,
                role="speaker",
                text="I was with you and we talked with them.",
            ),
            Turn(
                source_id="specific",
                session_id="s1",
                turn_index=1,
                role="speaker",
                text="Avery graduated with a degree in Business Administration.",
            ),
        )

        hits = LexicalBM25Retriever(
            turns,
            drop_query_stopwords=True,
        ).retrieve(
            "What degree did I graduate with?",
            top_k=2,
        )

        self.assertEqual(hits[0].source_id, "specific")
        self.assertEqual(hits[0].matched_terms, ("degree",))

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

    def test_dense_retriever_reuses_document_vectors_for_identical_turns(self) -> None:
        with _DENSE_DOCUMENT_CACHE_LOCK:
            _DENSE_DOCUMENT_CACHE.clear()
            _DENSE_DOCUMENT_CACHE_LOCKS.clear()
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
        embedder = _CountingEmbedder()

        first = DenseEmbeddingRetriever(turns, embedder).retrieve("career", top_k=1)
        second = DenseEmbeddingRetriever(turns, embedder).retrieve("coffee", top_k=1)

        self.assertEqual(first.embedding_tokens, 3)
        self.assertEqual(second.embedding_tokens, 1)
        self.assertEqual(embedder.document_calls, 1)
        self.assertEqual(embedder.query_calls, 2)

    def test_dense_retriever_external_naive_document_text_includes_date_and_role(self) -> None:
        with _DENSE_DOCUMENT_CACHE_LOCK:
            _DENSE_DOCUMENT_CACHE.clear()
            _DENSE_DOCUMENT_CACHE_LOCKS.clear()
        turns = (
            Turn(
                source_id="career",
                session_id="s1",
                turn_index=1,
                role="user",
                text="counseling and mental health career",
                timestamp="2024-01-01",
            ),
        )
        embedder = _RecordingEmbedder()

        DenseEmbeddingRetriever(
            turns,
            embedder,
            document_text_mode="external_naive",
        ).retrieve("career", top_k=1)

        self.assertEqual(
            embedder.document_texts,
            ["Date: 2024-01-01\nuser: counseling and mental health career"],
        )

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

    def test_rerank_hits_retains_retrieval_anchors(self) -> None:
        hits = (
            RetrievalHit("anchor", 0.9, 1, "dense_embedding"),
            RetrievalHit("winner", 0.3, 2, "lexical_bm25"),
            RetrievalHit("other", 0.2, 3, "lexical_bm25"),
        )

        reranked = rerank_hits_with_anchor_retention(
            hits=hits,
            scores=(0.1, 0.9, 0.2),
            top_k=3,
            anchor_keep=1,
            anchor_after_top=1,
        )

        self.assertEqual(
            [hit.source_id for hit in reranked],
            ["winner", "anchor", "other"],
        )
        self.assertTrue(reranked[0].retriever.endswith("+rerank"))

    def test_format_rerank_turn_document_includes_date_role_and_truncates(self) -> None:
        turn = Turn(
            source_id="s1:t0",
            session_id="s1",
            turn_index=0,
            role="user",
            text="A" * 200,
            timestamp="2024-01-01",
        )

        document = format_rerank_turn_document(turn, max_chars=80)

        self.assertLessEqual(len(document), 80)
        self.assertIn("Date: 2024-01-01", document)
        self.assertIn("...", document)

    def test_format_rerank_evidence_document_adds_neighbors_and_memory(self) -> None:
        turn = Turn(
            source_id="s1:t1",
            session_id="s1",
            turn_index=1,
            role="user",
            text="Alex redeemed the coupon at Target.",
            timestamp="2024-01-02",
        )
        neighbor = Turn(
            source_id="s1:t0",
            session_id="s1",
            turn_index=0,
            role="assistant",
            text="The coupon was for a grocery trip.",
            timestamp="2024-01-02",
        )
        memory = MemoryRecord(
            memory_id="m1",
            memory_type="profile",
            text="Alex usually redeems grocery coupons at Target.",
            source_ids=("s1:t1",),
            status="active",
        )

        document = format_rerank_evidence_document(
            turn,
            mode="turn_with_neighbors_and_memory",
            neighbor_turns=(neighbor,),
            memory_records=(memory,),
        )

        self.assertIn("Center Turn", document)
        self.assertIn("Alex redeemed the coupon at Target", document)
        self.assertIn("Neighbor Context", document)
        self.assertIn("The coupon was for a grocery trip", document)
        self.assertIn("Activated Build Memory", document)
        self.assertIn("type=profile", document)
        self.assertIn("sources=s1:t1", document)
        self.assertNotIn("question_type", document)


class _FakeEmbedder:
    def embed_texts(self, texts: list[str], input_type: str) -> EmbeddingBatch:
        vectors = []
        for text in texts:
            if any(term in text.lower() for term in ("career", "field", "education")):
                vectors.append((1.0, 0.0))
            else:
                vectors.append((0.0, 1.0))
        return EmbeddingBatch(vectors=tuple(vectors), total_tokens=len(texts))


class _CountingEmbedder(_FakeEmbedder):
    def __init__(self) -> None:
        self.document_calls = 0
        self.query_calls = 0

    def embed_texts(self, texts: list[str], input_type: str) -> EmbeddingBatch:
        if input_type == "document":
            self.document_calls += 1
        if input_type == "query":
            self.query_calls += 1
        return super().embed_texts(texts, input_type)


class _RecordingEmbedder(_FakeEmbedder):
    def __init__(self) -> None:
        self.document_texts: list[str] = []

    def embed_texts(self, texts: list[str], input_type: str) -> EmbeddingBatch:
        if input_type == "document":
            self.document_texts.extend(texts)
        return super().embed_texts(texts, input_type)


if __name__ == "__main__":
    unittest.main()
