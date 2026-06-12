"""Standard-library lexical retrieval baseline."""

from __future__ import annotations

import math
import re
from collections import Counter

from agent_memory.schemas import RetrievalHit, Turn


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
        self._k1 = k1
        self._b = b
        self._drop_query_stopwords = drop_query_stopwords
        self._doc_tokens = [_tokenize(turn.text) for turn in turns]
        self._doc_term_counts = [Counter(tokens) for tokens in self._doc_tokens]
        self._doc_lengths = [len(tokens) for tokens in self._doc_tokens]
        self._avg_doc_length = (
            sum(self._doc_lengths) / len(self._doc_lengths) if self._doc_lengths else 0.0
        )
        self._idf = self._build_idf()

    def retrieve(self, question: str, top_k: int, score_threshold: float = 0.0) -> tuple[RetrievalHit, ...]:
        query_terms = self._query_terms(question)
        if not query_terms or not self._turns:
            return ()

        scored: list[tuple[float, Turn, tuple[str, ...]]] = []
        for turn, term_counts, doc_length in zip(
            self._turns, self._doc_term_counts, self._doc_lengths, strict=True
        ):
            score, matched_terms = self._score_doc(query_terms, term_counts, doc_length)
            if score > score_threshold:
                scored.append((score, turn, matched_terms))

        scored.sort(key=lambda item: (-item[0], item[1].session_id, item[1].turn_index))
        hits = []
        for rank, (score, turn, matched_terms) in enumerate(scored[:top_k], start=1):
            hits.append(
                RetrievalHit(
                    source_id=turn.source_id,
                    score=score,
                    rank=rank,
                    retriever="lexical_bm25",
                    matched_terms=matched_terms,
                )
            )
        return tuple(hits)

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
        self, query_terms: tuple[str, ...], term_counts: Counter[str], doc_length: int
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


def _tokenize(text: str) -> list[str]:
    return [match.group(0).lower() for match in TOKEN_PATTERN.finditer(text)]
