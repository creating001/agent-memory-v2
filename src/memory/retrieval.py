"""Standard-library lexical retrieval baseline."""

from __future__ import annotations

import math
import re
import hashlib
import threading
from collections import Counter, OrderedDict, defaultdict
from dataclasses import dataclass
from typing import Protocol

from memory.build import MemoryRecord
from memory.embeddings import EmbeddingBatch
from common.schemas import RetrievalHit, Turn


TOKEN_PATTERN = re.compile(r"[\w]+", re.UNICODE)
_DENSE_DOCUMENT_CACHE_MAX_ENTRIES = 16
_DENSE_DOCUMENT_CACHE_LOCK = threading.Lock()
_DENSE_DOCUMENT_CACHE_LOCKS: dict[str, threading.Lock] = {}
_DENSE_DOCUMENT_CACHE: OrderedDict[str, tuple[tuple[float, ...], ...]] = OrderedDict()
QUERY_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "been",
    "being",
    "by",
    "can",
    "could",
    "did",
    "do",
    "does",
    "for",
    "from",
    "had",
    "has",
    "have",
    "he",
    "her",
    "his",
    "how",
    "i",
    "in",
    "is",
    "it",
    "me",
    "my",
    "of",
    "on",
    "or",
    "our",
    "should",
    "that",
    "the",
    "their",
    "them",
    "then",
    "there",
    "these",
    "they",
    "this",
    "those",
    "to",
    "up",
    "us",
    "was",
    "we",
    "were",
    "what",
    "when",
    "where",
    "which",
    "who",
    "whom",
    "why",
    "with",
    "would",
    "you",
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
class TurnWindowDocument:
    """Adjacent raw-turn window used only as a retrieval document."""

    document_id: str
    source_ids: tuple[str, ...]
    center_source_id: str
    session_id: str
    center_turn_index: int
    text: str

    def to_dict(self) -> dict[str, object]:
        return {
            "document_id": self.document_id,
            "source_ids": self.source_ids,
            "center_source_id": self.center_source_id,
            "session_id": self.session_id,
            "center_turn_index": self.center_turn_index,
            "text_chars": len(self.text),
        }


@dataclass(frozen=True)
class TurnWindowHit:
    document: TurnWindowDocument
    score: float
    rank: int
    matched_terms: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "document": self.document.to_dict(),
            "score": self.score,
            "rank": self.rank,
            "matched_terms": self.matched_terms,
        }


class TurnWindowBM25Retriever:
    """BM25 over adjacent turn windows, projected back to raw turns later."""

    def __init__(
        self,
        documents: tuple[TurnWindowDocument, ...],
        k1: float = 1.5,
        b: float = 0.75,
        drop_query_stopwords: bool = True,
    ):
        self._documents = documents
        self._index = _BM25Index(
            texts=tuple(document.text for document in documents),
            sort_keys=tuple(
                (document.session_id, document.center_turn_index, document.document_id)
                for document in documents
            ),
            k1=k1,
            b=b,
            drop_query_stopwords=drop_query_stopwords,
        )

    def retrieve(
        self,
        question: str,
        top_k: int,
        score_threshold: float = 0.0,
    ) -> tuple[TurnWindowHit, ...]:
        hits = []
        for rank, scored in enumerate(
            self._index.retrieve(question, top_k=top_k, score_threshold=score_threshold),
            start=1,
        ):
            hits.append(
                TurnWindowHit(
                    document=self._documents[scored.index],
                    score=scored.score,
                    rank=rank,
                    matched_terms=scored.matched_terms,
                )
            )
        return tuple(hits)


def build_turn_window_documents(
    turns: tuple[Turn, ...],
    *,
    window_before: int,
    window_after: int,
    max_chars_per_turn: int = 0,
) -> tuple[TurnWindowDocument, ...]:
    """Build query-time retrieval windows from visible raw conversation turns."""

    if window_before < 0 or window_after < 0:
        raise ValueError("turn-window sizes must be non-negative")

    grouped: dict[str, list[Turn]] = defaultdict(list)
    for turn in turns:
        grouped[turn.session_id].append(turn)

    documents: list[TurnWindowDocument] = []
    for session_id in sorted(grouped):
        session_turns = sorted(grouped[session_id], key=lambda item: item.turn_index)
        for position, center_turn in enumerate(session_turns):
            start = max(0, position - window_before)
            end = min(len(session_turns), position + window_after + 1)
            window_turns = tuple(session_turns[start:end])
            start_turn_index = window_turns[0].turn_index
            end_turn_index = window_turns[-1].turn_index
            documents.append(
                TurnWindowDocument(
                    document_id=(
                        f"{session_id}:window:"
                        f"{start_turn_index}:"
                        f"{center_turn.turn_index}:"
                        f"{end_turn_index}"
                    ),
                    source_ids=tuple(turn.source_id for turn in window_turns),
                    center_source_id=center_turn.source_id,
                    session_id=session_id,
                    center_turn_index=center_turn.turn_index,
                    text="\n".join(
                        _turn_window_text(turn, max_chars=max_chars_per_turn)
                        for turn in window_turns
                    ),
                )
            )
    return tuple(documents)


def turn_window_hits_to_source_hits(
    window_hits: tuple[TurnWindowHit, ...],
    max_sources_per_window: int,
) -> tuple[RetrievalHit, ...]:
    """Project window hits to original raw source turns for clean prompting."""

    if max_sources_per_window <= 0:
        return ()

    hits: list[RetrievalHit] = []
    seen: set[str] = set()
    rank = 1
    for window_hit in window_hits:
        for offset, source_id in enumerate(_window_source_projection(window_hit.document)):
            if offset >= max_sources_per_window:
                break
            if source_id in seen:
                continue
            seen.add(source_id)
            hits.append(
                RetrievalHit(
                    source_id=source_id,
                    score=window_hit.score - (offset * 1e-6),
                    rank=rank,
                    retriever="turn_window_bm25",
                    matched_terms=window_hit.matched_terms,
                )
            )
            rank += 1
    return tuple(hits)


def _turn_window_text(turn: Turn, *, max_chars: int) -> str:
    text = turn.text
    if max_chars > 0 and len(text) > max_chars:
        text = text[:max_chars].rstrip()
    prefix = " ".join(part for part in (turn.timestamp, turn.role) if part)
    return f"{prefix}: {text}" if prefix else text


def _window_source_projection(document: TurnWindowDocument) -> tuple[str, ...]:
    if document.center_source_id not in document.source_ids:
        return document.source_ids
    return (
        document.center_source_id,
        *(
            source_id
            for source_id in document.source_ids
            if source_id != document.center_source_id
        ),
    )


@dataclass(frozen=True)
class MemoryHit:
    record: MemoryRecord
    score: float
    rank: int
    matched_terms: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "memory": self.record.to_dict(),
            "score": self.score,
            "rank": self.rank,
            "matched_terms": self.matched_terms,
        }


class BuildMemoryBM25Retriever:
    """BM25 over build-stage typed memory records."""

    def __init__(
        self,
        records: tuple[MemoryRecord, ...],
        k1: float = 1.5,
        b: float = 0.75,
        drop_query_stopwords: bool = True,
        include_superseded: bool = False,
    ):
        self._records = tuple(
            record
            for record in records
            if include_superseded or record.status == "active"
        )
        self._index = _BM25Index(
            texts=tuple(record.search_text for record in self._records),
            sort_keys=tuple(
                (
                    0 if record.status == "active" else 1,
                    record.memory_type,
                    record.timestamp or "",
                    record.memory_id,
                )
                for record in self._records
            ),
            k1=k1,
            b=b,
            drop_query_stopwords=drop_query_stopwords,
        )

    def retrieve(
        self,
        question: str,
        top_k: int,
        score_threshold: float = 0.0,
    ) -> tuple[MemoryHit, ...]:
        hits = []
        for rank, scored in enumerate(
            self._index.retrieve(question, top_k=top_k, score_threshold=score_threshold),
            start=1,
        ):
            hits.append(
                MemoryHit(
                    record=self._records[scored.index],
                    score=scored.score,
                    rank=rank,
                    matched_terms=scored.matched_terms,
                )
            )
        return tuple(hits)


def memory_hits_to_source_hits(
    memory_hits: tuple[MemoryHit, ...],
    max_sources_per_memory: int,
) -> tuple[RetrievalHit, ...]:
    """Project typed memory hits back to raw source turns for fusion."""

    hits: list[RetrievalHit] = []
    seen: set[str] = set()
    rank = 1
    source_limit = max(1, max_sources_per_memory)
    for memory_hit in memory_hits:
        for source_id in memory_hit.record.source_ids[:source_limit]:
            if source_id in seen:
                continue
            seen.add(source_id)
            hits.append(
                RetrievalHit(
                    source_id=source_id,
                    score=memory_hit.score,
                    rank=rank,
                    retriever="build_memory_bm25",
                    matched_terms=memory_hit.matched_terms,
                )
            )
            rank += 1
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
        document_text_mode: str = "text",
    ):
        if document_text_mode not in {"text", "external_naive"}:
            raise ValueError(f"Unsupported dense document_text_mode: {document_text_mode}")
        self._turns = turns
        self._embedder = embedder
        self._batch_size = batch_size
        self._document_text_mode = document_text_mode
        self._doc_vectors: tuple[tuple[float, ...], ...]
        self._document_embedding_tokens = 0
        self._doc_vectors, self._document_embedding_tokens = (
            self._load_or_embed_documents()
        )

    def retrieve(
        self,
        query_text: str,
        top_k: int,
        score_threshold: float = -1.0,
    ) -> DenseRetrievalResult:
        if not self._turns:
            return DenseRetrievalResult(hits=(), embedding_tokens=0)
        query_batch = self._embedder.embed_texts([query_text], input_type="query")
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

    def _load_or_embed_documents(self) -> tuple[tuple[tuple[float, ...], ...], int]:
        cache_key = _dense_document_cache_key(self._turns, self._document_text_mode)
        cached = _get_dense_document_cache(cache_key)
        if cached is not None:
            return cached, 0

        build_lock = _dense_document_build_lock(cache_key)
        with build_lock:
            cached = _get_dense_document_cache(cache_key)
            if cached is not None:
                return cached, 0
            vectors, tokens = self._embed_documents()
            _put_dense_document_cache(cache_key, vectors)
            return vectors, tokens

    def _embed_documents(self) -> tuple[tuple[tuple[float, ...], ...], int]:
        vectors: list[tuple[float, ...]] = []
        tokens = 0
        for start in range(0, len(self._turns), self._batch_size):
            batch_turns = self._turns[start : start + self._batch_size]
            batch = self._embedder.embed_texts(
                [
                    _dense_document_text(turn, mode=self._document_text_mode)
                    for turn in batch_turns
                ],
                input_type="document",
            )
            tokens += batch.total_tokens
            vectors.extend(_normalize_vector(vector) for vector in batch.vectors)
        return tuple(vectors), tokens


def _dense_document_text(turn: Turn, *, mode: str) -> str:
    if mode == "text":
        return turn.text
    if mode != "external_naive":
        raise ValueError(f"Unsupported dense document_text_mode: {mode}")
    text = f"{turn.role}: {turn.text}"
    if turn.timestamp:
        return f"Date: {turn.timestamp}\n{text}"
    return text


def _dense_document_cache_key(turns: tuple[Turn, ...], document_text_mode: str) -> str:
    digest = hashlib.sha256()
    digest.update(document_text_mode.encode("utf-8"))
    digest.update(b"\0")
    for turn in turns:
        digest.update(turn.source_id.encode("utf-8"))
        digest.update(b"\0")
        digest.update(turn.session_id.encode("utf-8"))
        digest.update(b"\0")
        digest.update(str(turn.turn_index).encode("utf-8"))
        digest.update(b"\0")
        digest.update(turn.role.encode("utf-8"))
        digest.update(b"\0")
        digest.update((turn.timestamp or "").encode("utf-8"))
        digest.update(b"\0")
        digest.update(turn.text.encode("utf-8"))
        digest.update(b"\0")
    return digest.hexdigest()


def _get_dense_document_cache(
    cache_key: str,
) -> tuple[tuple[float, ...], ...] | None:
    with _DENSE_DOCUMENT_CACHE_LOCK:
        vectors = _DENSE_DOCUMENT_CACHE.get(cache_key)
        if vectors is None:
            return None
        _DENSE_DOCUMENT_CACHE.move_to_end(cache_key)
        return vectors


def _put_dense_document_cache(
    cache_key: str, vectors: tuple[tuple[float, ...], ...]
) -> None:
    with _DENSE_DOCUMENT_CACHE_LOCK:
        _DENSE_DOCUMENT_CACHE[cache_key] = vectors
        _DENSE_DOCUMENT_CACHE.move_to_end(cache_key)
        while len(_DENSE_DOCUMENT_CACHE) > _DENSE_DOCUMENT_CACHE_MAX_ENTRIES:
            _DENSE_DOCUMENT_CACHE.popitem(last=False)


def _dense_document_build_lock(cache_key: str) -> threading.Lock:
    with _DENSE_DOCUMENT_CACHE_LOCK:
        lock = _DENSE_DOCUMENT_CACHE_LOCKS.get(cache_key)
        if lock is None:
            lock = threading.Lock()
            _DENSE_DOCUMENT_CACHE_LOCKS[cache_key] = lock
        return lock


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
