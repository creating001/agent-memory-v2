"""Stage-1 clean Agent-Memory pipeline."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from agent_memory.answer import NullAnswerer, OpenAICompatibleAnswerer
from agent_memory.compiler import EvidenceCompiler
from agent_memory.embeddings import OpenAICompatibleEmbeddingClient
from agent_memory.retrieval import (
    DenseEmbeddingRetriever,
    LexicalBM25Retriever,
    prepend_protected_hits,
    reciprocal_rank_fusion,
)
from agent_memory.route import QuestionRouter
from agent_memory.schemas import PredictionRequest
from agent_memory.store import RawEvidenceStore


class Stage1Pipeline:
    """Minimal, clean, ablation-friendly memory pipeline."""

    def __init__(self, config: Mapping[str, Any]):
        self._config = dict(config)
        retrieval_config = self._config.get("retrieval", {})
        dense_config = retrieval_config.get("dense", {})
        compiler_config = self._config.get("compiler", {})
        answer_config = self._config.get("answer", {})
        self._router = QuestionRouter()
        self._base_top_k = int(retrieval_config.get("top_k", 8))
        self._max_top_k = int(retrieval_config.get("max_top_k", self._base_top_k))
        self._neighbor_window = int(retrieval_config.get("neighbor_window", 1))
        self._neighbor_order = str(retrieval_config.get("neighbor_order", "hit_priority"))
        self._drop_query_stopwords = bool(retrieval_config.get("drop_query_stopwords", False))
        self._score_threshold = float(retrieval_config.get("score_threshold", 0.0))
        self._dense_enabled = bool(dense_config.get("enabled", False))
        self._dense_top_k = int(dense_config.get("top_k", self._base_top_k))
        self._dense_batch_size = int(dense_config.get("batch_size", 32))
        self._fusion_rrf_k = int(dense_config.get("rrf_k", 60))
        self._lexical_protect_top_n = int(dense_config.get("lexical_protect_top_n", 0))
        self._embedding_client = None
        if self._dense_enabled:
            self._embedding_client = OpenAICompatibleEmbeddingClient(
                base_url=str(dense_config.get("base_url", "http://127.0.0.1:8001/v1")),
                model=str(dense_config["model"]),
                timeout=float(dense_config.get("timeout", 120.0)),
            )
        self._compiler = EvidenceCompiler(
            max_evidence_items=int(compiler_config.get("max_evidence_items", 20)),
            max_evidence_chars=int(compiler_config.get("max_evidence_chars", 12000)),
        )
        answer_mode = str(answer_config.get("mode", "null_answerer"))
        if answer_mode == "openai_compatible":
            self._answerer = OpenAICompatibleAnswerer(
                base_url=str(answer_config.get("base_url", "http://127.0.0.1:8000/v1")),
                model=str(answer_config["model"]),
                temperature=float(answer_config.get("temperature", 0.0)),
                max_tokens=int(answer_config.get("max_tokens", 256)),
                timeout=float(answer_config.get("timeout", 120.0)),
                api_key_env=answer_config.get("api_key_env"),
            )
        else:
            self._answerer = NullAnswerer(
                fallback_answer=str(
                    answer_config.get(
                        "fallback_answer",
                        "I do not know based on the available evidence.",
                    )
                )
            )

    def predict(self, request: PredictionRequest) -> dict[str, Any]:
        store = RawEvidenceStore(request.turns)
        route = self._router.route(request.question, request.question_time)
        top_k = min(self._base_top_k * route.retrieval_multiplier, self._max_top_k)
        retriever = LexicalBM25Retriever(
            store.turns,
            drop_query_stopwords=self._drop_query_stopwords,
        )
        lexical_hits = retriever.retrieve(
            request.question,
            top_k=top_k,
            score_threshold=self._score_threshold,
        )
        dense_hits = ()
        embedding_tokens = 0
        if self._embedding_client is not None:
            dense_result = DenseEmbeddingRetriever(
                store.turns,
                self._embedding_client,
                batch_size=self._dense_batch_size,
            ).retrieve(
                request.question,
                top_k=self._dense_top_k,
            )
            dense_hits = dense_result.hits
            embedding_tokens = dense_result.embedding_tokens
            hits = reciprocal_rank_fusion(
                (lexical_hits, dense_hits),
                top_k=top_k,
                rrf_k=self._fusion_rrf_k,
            )
            if self._lexical_protect_top_n > 0:
                hits = prepend_protected_hits(
                    lexical_hits[: self._lexical_protect_top_n],
                    hits,
                    top_k=top_k,
                )
        else:
            hits = lexical_hits
        evidence_turns = store.expand_neighbors(
            (hit.source_id for hit in hits),
            window=self._neighbor_window,
            order=self._neighbor_order,
        )
        compiled = self._compiler.compile(
            question=request.question,
            question_time=request.question_time,
            route=route,
            hits=hits,
            evidence_turns=evidence_turns,
        )
        answer = self._answerer.answer(compiled)
        return {
            "answer": answer.answer,
            "trace": {
                "store": store.manifest(),
                "route": route.to_dict(),
                "retrieval": {
                    "retriever": "dense_hybrid_rrf"
                    if self._dense_enabled
                    else "lexical_bm25",
                    "top_k": top_k,
                    "base_top_k": self._base_top_k,
                    "neighbor_window": self._neighbor_window,
                    "neighbor_order": self._neighbor_order,
                    "drop_query_stopwords": self._drop_query_stopwords,
                    "dense_enabled": self._dense_enabled,
                    "dense_top_k": self._dense_top_k if self._dense_enabled else None,
                    "lexical_protect_top_n": self._lexical_protect_top_n
                    if self._dense_enabled
                    else None,
                    "embedding_tokens": embedding_tokens,
                    "lexical_hits": [hit.to_dict() for hit in lexical_hits],
                    "dense_hits": [hit.to_dict() for hit in dense_hits],
                    "hits": [hit.to_dict() for hit in hits],
                },
                "compiled_context": compiled.to_dict(),
                "answer": answer.to_dict(),
                "token_cost": answer.token_usage.to_dict(),
            },
        }
