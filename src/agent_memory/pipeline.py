"""Stage-1 clean Agent-Memory pipeline."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from agent_memory.answer import NullAnswerer, OpenAICompatibleAnswerer
from agent_memory.compiler import EvidenceCompiler
from agent_memory.retrieval import LexicalBM25Retriever
from agent_memory.route import QuestionRouter
from agent_memory.schemas import PredictionRequest
from agent_memory.store import RawEvidenceStore


class Stage1Pipeline:
    """Minimal, clean, ablation-friendly memory pipeline."""

    def __init__(self, config: Mapping[str, Any]):
        self._config = dict(config)
        retrieval_config = self._config.get("retrieval", {})
        compiler_config = self._config.get("compiler", {})
        answer_config = self._config.get("answer", {})
        self._router = QuestionRouter()
        self._base_top_k = int(retrieval_config.get("top_k", 8))
        self._max_top_k = int(retrieval_config.get("max_top_k", self._base_top_k))
        self._neighbor_window = int(retrieval_config.get("neighbor_window", 1))
        self._neighbor_order = str(retrieval_config.get("neighbor_order", "hit_priority"))
        self._score_threshold = float(retrieval_config.get("score_threshold", 0.0))
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
        retriever = LexicalBM25Retriever(store.turns)
        hits = retriever.retrieve(
            request.question,
            top_k=top_k,
            score_threshold=self._score_threshold,
        )
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
                    "retriever": "lexical_bm25",
                    "top_k": top_k,
                    "base_top_k": self._base_top_k,
                    "neighbor_window": self._neighbor_window,
                    "neighbor_order": self._neighbor_order,
                    "hits": [hit.to_dict() for hit in hits],
                },
                "compiled_context": compiled.to_dict(),
                "answer": answer.to_dict(),
                "token_cost": answer.token_usage.to_dict(),
            },
        }
