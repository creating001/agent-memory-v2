"""Standard-library lexical retrieval baseline."""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from typing import Protocol

from memory.embeddings import EmbeddingBatch
from common.schemas import RetrievalHit, Turn


TOKEN_PATTERN = re.compile(r"[\w]+", re.UNICODE)
QUERY_STOPWORDS = {
    "a",
    "an",
    "are",
    "at",
    "be",
    "been",
    "being",
    "could",
    "did",
    "do",
    "does",
    "for",
    "her",
    "his",
    "how",
    "in",
    "is",
    "my",
    "of",
    "on",
    "our",
    "should",
    "the",
    "their",
    "to",
    "was",
    "were",
    "what",
    "when",
    "where",
    "which",
    "who",
    "whom",
    "why",
    "would",
    "your",
}


@dataclass(frozen=True)
class _BM25Score:
    index: int
    score: float
    matched_terms: tuple[str, ...]


class _BM25Index:
    """Shared BM25 index for turn and session lexical retrieval."""

    def __init__(
        self,
        texts: tuple[str, ...],
        sort_keys: tuple[tuple[object, ...], ...],
        k1: float,
        b: float,
        drop_query_stopwords: bool,
    ):
        self._k1 = k1
        self._b = b
        self._drop_query_stopwords = drop_query_stopwords
        self._sort_keys = sort_keys
        self._doc_tokens = [_tokenize(text) for text in texts]
        self._doc_term_counts = [Counter(tokens) for tokens in self._doc_tokens]
        self._doc_lengths = [len(tokens) for tokens in self._doc_tokens]
        self._avg_doc_length = (
            sum(self._doc_lengths) / len(self._doc_lengths) if self._doc_lengths else 0.0
        )
        self._idf = self._build_idf()

    def retrieve(
        self,
        question: str,
        top_k: int,
        score_threshold: float,
    ) -> tuple[_BM25Score, ...]:
        query_terms = self._query_terms(question)
        if top_k <= 0 or not query_terms or not self._doc_tokens:
            return ()

        scored: list[_BM25Score] = []
        for index, (term_counts, doc_length) in enumerate(
            zip(self._doc_term_counts, self._doc_lengths, strict=True)
        ):
            score, matched_terms = self._score_doc(query_terms, term_counts, doc_length)
            if score > score_threshold:
                scored.append(
                    _BM25Score(
                        index=index,
                        score=score,
                        matched_terms=matched_terms,
                    )
                )

        scored.sort(key=lambda item: (-item.score, self._sort_keys[item.index]))
        return tuple(scored[:top_k])

    def _query_terms(self, question: str) -> tuple[str, ...]:
        terms = tuple(dict.fromkeys(_tokenize(question)))
        if not self._drop_query_stopwords:
            return terms
        filtered_terms = tuple(term for term in terms if term not in QUERY_STOPWORDS)
        return filtered_terms or terms

    def _build_idf(self) -> dict[str, float]:
        doc_count = len(self._doc_tokens)
        document_frequency: Counter[str] = Counter()
        for tokens in self._doc_tokens:
            document_frequency.update(set(tokens))
        return {
            term: math.log(1.0 + (doc_count - frequency + 0.5) / (frequency + 0.5))
            for term, frequency in document_frequency.items()
        }

    def _score_doc(
        self,
        query_terms: tuple[str, ...],
        term_counts: Counter[str],
        doc_length: int,
    ) -> tuple[float, tuple[str, ...]]:
        if doc_length == 0:
            return 0.0, ()

        score = 0.0
        matched_terms: list[str] = []
        for term in query_terms:
            frequency = term_counts.get(term, 0)
            if frequency == 0:
                continue
            matched_terms.append(term)
            idf = self._idf.get(term, 0.0)
            denominator = frequency + self._k1 * (
                1.0 - self._b + self._b * doc_length / (self._avg_doc_length or 1.0)
            )
            score += idf * (frequency * (self._k1 + 1.0)) / denominator
        return score, tuple(matched_terms)


class LexicalBM25Retriever:
    """Small BM25 implementation for a dependency-free baseline."""

    def __init__(
        self,
        turns: tuple[Turn, ...],
        k1: float = 1.5,
        b: float = 0.75,
        drop_query_stopwords: bool = False,
    ):
        self._turns = turns
        self._index = _BM25Index(
            texts=tuple(turn.text for turn in turns),
            sort_keys=tuple(
                (turn.session_id, turn.turn_index, turn.source_id) for turn in turns
            ),
            k1=k1,
            b=b,
            drop_query_stopwords=drop_query_stopwords,
        )

    def retrieve(self, question: str, top_k: int, score_threshold: float = 0.0) -> tuple[RetrievalHit, ...]:
        hits = []
        for rank, scored in enumerate(
            self._index.retrieve(question, top_k=top_k, score_threshold=score_threshold),
            start=1,
        ):
            turn = self._turns[scored.index]
            hits.append(
                RetrievalHit(
                    source_id=turn.source_id,
                    score=scored.score,
                    rank=rank,
                    retriever="lexical_bm25",
                    matched_terms=scored.matched_terms,
                )
            )
        return tuple(hits)


@dataclass(frozen=True)
class SessionDocument:
    session_id: str
    text: str
    turn_count: int


class SessionBM25Retriever:
    """BM25 over raw session documents for clean coarse retrieval."""

    def __init__(
        self,
        documents: tuple[SessionDocument, ...],
        k1: float = 1.5,
        b: float = 0.75,
        drop_query_stopwords: bool = False,
    ):
        self._documents = documents
        self._index = _BM25Index(
            texts=tuple(document.text for document in documents),
            sort_keys=tuple((document.session_id,) for document in documents),
            k1=k1,
            b=b,
            drop_query_stopwords=drop_query_stopwords,
        )

    def retrieve(
        self,
        question: str,
        top_k: int,
        score_threshold: float = 0.0,
    ) -> tuple[RetrievalHit, ...]:
        hits = []
        for rank, scored in enumerate(
            self._index.retrieve(question, top_k=top_k, score_threshold=score_threshold),
            start=1,
        ):
            document = self._documents[scored.index]
            hits.append(
                RetrievalHit(
                    source_id=document.session_id,
                    score=scored.score,
                    rank=rank,
                    retriever="session_bm25",
                    matched_terms=scored.matched_terms,
                )
            )
        return tuple(hits)


class Embedder(Protocol):
    def embed_texts(self, texts: list[str], input_type: str) -> EmbeddingBatch:
        ...


@dataclass(frozen=True)
class DenseRetrievalResult:
    hits: tuple[RetrievalHit, ...]
    embedding_tokens: int


class DenseEmbeddingRetriever:
    """Cosine-similarity dense retriever over raw turns."""

    def __init__(
        self,
        turns: tuple[Turn, ...],
        embedder: Embedder,
        batch_size: int = 32,
    ):
        self._turns = turns
        self._embedder = embedder
        self._batch_size = batch_size
        self._doc_vectors: tuple[tuple[float, ...], ...]
        self._document_embedding_tokens = 0
        self._doc_vectors = self._embed_documents()

    def retrieve(
        self,
        question: str,
        top_k: int,
        score_threshold: float = -1.0,
    ) -> DenseRetrievalResult:
        if not self._turns:
            return DenseRetrievalResult(hits=(), embedding_tokens=0)
        query_batch = self._embedder.embed_texts([question], input_type="query")
        if not query_batch.vectors:
            return DenseRetrievalResult(
                hits=(),
                embedding_tokens=self._document_embedding_tokens
                + query_batch.total_tokens,
            )
        query_vector = _normalize_vector(query_batch.vectors[0])
        scored = []
        for turn, vector in zip(self._turns, self._doc_vectors, strict=True):
            score = _dot(query_vector, vector)
            if score > score_threshold:
                scored.append((score, turn))
        scored.sort(key=lambda item: (-item[0], item[1].session_id, item[1].turn_index))
        hits = tuple(
            RetrievalHit(
                source_id=turn.source_id,
                score=score,
                rank=rank,
                retriever="dense_embedding",
                matched_terms=(),
            )
            for rank, (score, turn) in enumerate(scored[:top_k], start=1)
        )
        return DenseRetrievalResult(
            hits=hits,
            embedding_tokens=self._document_embedding_tokens + query_batch.total_tokens,
        )

    def _embed_documents(self) -> tuple[tuple[float, ...], ...]:
        vectors: list[tuple[float, ...]] = []
        for start in range(0, len(self._turns), self._batch_size):
            batch_turns = self._turns[start : start + self._batch_size]
            batch = self._embedder.embed_texts(
                [turn.text for turn in batch_turns],
                input_type="document",
            )
            self._document_embedding_tokens += batch.total_tokens
            vectors.extend(_normalize_vector(vector) for vector in batch.vectors)
        return tuple(vectors)


def reciprocal_rank_fusion(
    hit_lists: tuple[tuple[RetrievalHit, ...], ...],
    top_k: int,
    rrf_k: int = 60,
) -> tuple[RetrievalHit, ...]:
    scores: dict[str, float] = {}
    source_retrievers: dict[str, list[str]] = {}
    for hits in hit_lists:
        for hit in hits:
            scores[hit.source_id] = scores.get(hit.source_id, 0.0) + 1.0 / (
                rrf_k + hit.rank
            )
            source_retrievers.setdefault(hit.source_id, []).append(hit.retriever)

    ranked = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
    return tuple(
        RetrievalHit(
            source_id=source_id,
            score=score,
            rank=rank,
            retriever="+".join(dict.fromkeys(source_retrievers[source_id])),
            matched_terms=(),
        )
        for rank, (source_id, score) in enumerate(ranked[:top_k], start=1)
    )


def prepend_protected_hits(
    protected_hits: tuple[RetrievalHit, ...],
    candidate_hits: tuple[RetrievalHit, ...],
    top_k: int,
) -> tuple[RetrievalHit, ...]:
    """Keep high-confidence primary hits before fused candidates."""

    selected: list[RetrievalHit] = []
    seen: set[str] = set()
    for hit in (*protected_hits, *candidate_hits):
        if hit.source_id in seen:
            continue
        seen.add(hit.source_id)
        selected.append(hit)
        if len(selected) >= top_k:
            break
    return tuple(
        RetrievalHit(
            source_id=hit.source_id,
            score=hit.score,
            rank=rank,
            retriever=hit.retriever,
            matched_terms=hit.matched_terms,
        )
        for rank, hit in enumerate(selected, start=1)
    )


def _normalize_vector(vector: tuple[float, ...]) -> tuple[float, ...]:
    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return vector
    return tuple(value / norm for value in vector)


def _dot(left: tuple[float, ...], right: tuple[float, ...]) -> float:
    return sum(a * b for a, b in zip(left, right, strict=True))


def _tokenize(text: str) -> list[str]:
    return [match.group(0).lower() for match in TOKEN_PATTERN.finditer(text)]
