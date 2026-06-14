"""Stage-1 clean Agent-Memory pipeline."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import replace
from typing import Any

from memory.answer import CachedAnswerer, NullAnswerer, OpenAICompatibleAnswerer
from memory.build import NullMemoryBuilder, OpenAICompatibleMemoryBuilder
from memory.compiler import EvidenceCompiler, SUPPORTED_INFORMATION_NEEDS
from memory.embeddings import CachedEmbeddingClient, OpenAICompatibleEmbeddingClient
from memory.finalize import AnswerFinalization, finalize_structured_answer
from memory.repair import maybe_repair_answer
from memory.rerank import (
    OpenAICompatibleRerankClient,
    format_rerank_turn_document,
    rerank_hits_with_anchor_retention,
)
from memory.retrieval import (
    BuildMemoryBM25Retriever,
    DenseEmbeddingRetriever,
    LexicalBM25Retriever,
    TurnWindowBM25Retriever,
    build_turn_window_documents,
    memory_hits_to_source_hits,
    prepend_protected_hits,
    reciprocal_rank_fusion,
    turn_window_hits_to_source_hits,
)
from memory.route import QuestionRouter
from memory.scoped_evidence import (
    ScopedEvidenceRun,
    build_scoped_evidence_answer_prompt,
    build_scoped_evidence_extraction_prompt,
    disabled_scoped_evidence_run,
    extract_evidence_json_text,
    parsed_evidence_json,
    scoped_evidence_answer_result,
    should_apply_scoped_evidence,
)
from common.schemas import (
    AnswerResult,
    CompiledContext,
    PredictionRequest,
    RetrievalHit,
    RouteResult,
    TokenUsage,
)
from memory.store import RawEvidenceStore


class Stage1Pipeline:
    """Minimal, clean, ablation-friendly memory pipeline."""

    def __init__(self, config: Mapping[str, Any]):
        self._config = dict(config)
        retrieval_config = self._config.get("retrieval", {})
        build_memory_config = self._config.get("build_memory", {})
        lexical_config = retrieval_config.get("lexical", {})
        dense_config = retrieval_config.get("dense", {})
        turn_window_config = retrieval_config.get("turn_window_bm25", {})
        rerank_config = retrieval_config.get("rerank", {})
        route_config = self._config.get("route", {})
        if self._config.get("question_analysis", {}).get("enabled", False):
            raise ValueError("question_analysis is retired; use heuristic route")
        compiler_config = self._config.get("compiler", {})
        answer_config = self._config.get("answer", {})
        scoped_evidence_config = self._config.get("scoped_evidence", {})
        answer_finalizer_config = answer_config.get("finalizer", {})
        answer_repair_config = answer_config.get("repair", {})
        self._router = QuestionRouter(
            enable_broad_list_patterns=bool(
                route_config.get("enable_broad_list_patterns", False)
            ),
            enable_recommendation_profile_patterns=bool(
                route_config.get("enable_recommendation_profile_patterns", False)
            ),
            enable_advice_profile_patterns=bool(
                route_config.get("enable_advice_profile_patterns", False)
            ),
            temporal_priority_over_recent=bool(
                route_config.get("temporal_priority_over_recent", False)
            ),
        )
        self._route_trace_config = {
            "enable_broad_list_patterns": bool(
                route_config.get("enable_broad_list_patterns", False)
            ),
            "enable_recommendation_profile_patterns": bool(
                route_config.get("enable_recommendation_profile_patterns", False)
            ),
            "enable_advice_profile_patterns": bool(
                route_config.get("enable_advice_profile_patterns", False)
            ),
            "temporal_priority_over_recent": bool(
                route_config.get("temporal_priority_over_recent", False)
            ),
        }
        self._base_top_k = int(retrieval_config.get("top_k", 8))
        self._max_top_k = int(retrieval_config.get("max_top_k", self._base_top_k))
        self._retrieval_route_overrides = _validate_retrieval_route_overrides(
            retrieval_config.get("route_overrides") or {}
        )
        self._neighbor_window = int(retrieval_config.get("neighbor_window", 1))
        self._neighbor_order = str(retrieval_config.get("neighbor_order", "hit_priority"))
        self._lexical_enabled = bool(lexical_config.get("enabled", True))
        self._drop_query_stopwords = bool(retrieval_config.get("drop_query_stopwords", False))
        self._score_threshold = float(retrieval_config.get("score_threshold", 0.0))
        self._build_memory_enabled = bool(build_memory_config.get("enabled", False))
        self._build_memory_top_k = int(build_memory_config.get("top_k", 0))
        self._build_memory_max_sources_per_record = int(
            build_memory_config.get("max_sources_per_record", 3)
        )
        self._build_memory_include_superseded = bool(
            build_memory_config.get("include_superseded", False)
        )
        self._build_memory_include_superseded_information_needs = _tuple_config(
            build_memory_config.get("include_superseded_information_needs")
        )
        self._build_memory_drop_query_stopwords = bool(
            build_memory_config.get("drop_query_stopwords", True)
        )
        source_alignment_config = build_memory_config.get("source_alignment", {})
        self._build_memory_source_alignment_enabled = bool(
            source_alignment_config.get("enabled", False)
        )
        self._build_memory_source_alignment_window = int(
            source_alignment_config.get("window", 1)
        )
        self._build_memory_source_alignment_max_sources = int(
            source_alignment_config.get(
                "max_sources_per_record",
                self._build_memory_max_sources_per_record,
            )
        )
        self._build_memory_source_alignment_min_score = float(
            source_alignment_config.get("min_score", 2.0)
        )
        self._build_memory_source_alignment_min_delta = float(
            source_alignment_config.get("min_delta", 1.5)
        )
        self._build_memory_trace_config = {
            "enabled": self._build_memory_enabled,
            "mode": build_memory_config.get("mode"),
            "model": build_memory_config.get("model"),
            "max_tokens": build_memory_config.get("max_tokens"),
            "max_turns_per_chunk": build_memory_config.get("max_turns_per_chunk"),
            "overlap_turns": int(build_memory_config.get("overlap_turns", 0)),
            "max_chars_per_turn": build_memory_config.get("max_chars_per_turn"),
            "max_records_per_chunk": build_memory_config.get("max_records_per_chunk"),
            "temporal_fields": bool(build_memory_config.get("temporal_fields", False)),
            "prompt_profile": str(
                build_memory_config.get("prompt_profile", "typed_compact")
            ),
            "manage_facts": bool(build_memory_config.get("manage_facts", True)),
            "source_alignment": {
                "enabled": self._build_memory_source_alignment_enabled,
                "window": self._build_memory_source_alignment_window,
                "max_sources_per_record": (
                    self._build_memory_source_alignment_max_sources
                ),
                "min_score": self._build_memory_source_alignment_min_score,
                "min_delta": self._build_memory_source_alignment_min_delta,
            },
        }
        self._dense_enabled = bool(dense_config.get("enabled", False))
        self._dense_top_k = int(dense_config.get("top_k", self._base_top_k))
        self._dense_batch_size = int(dense_config.get("batch_size", 32))
        self._dense_document_text_mode = str(dense_config.get("document_text_mode", "text"))
        self._dense_query_text_mode = str(dense_config.get("query_text_mode", "question"))
        self._fusion_rrf_k = int(dense_config.get("rrf_k", 60))
        self._lexical_protect_top_n = int(dense_config.get("lexical_protect_top_n", 0))
        self._dense_protect_top_n = int(dense_config.get("protect_top_n", 0))
        cache_config = dense_config.get("cache", {})
        self._embedding_cache_enabled = bool(cache_config.get("enabled", False))
        self._embedding_cache_path = cache_config.get("path")
        self._embedding_cache_namespace = str(
            cache_config.get("namespace", dense_config.get("model", "unknown"))
        )
        self._turn_window_bm25_enabled = bool(turn_window_config.get("enabled", False))
        self._turn_window_bm25_top_k = int(turn_window_config.get("top_k", 0))
        self._turn_window_bm25_window_before = int(
            turn_window_config.get("window_before", 1)
        )
        self._turn_window_bm25_window_after = int(
            turn_window_config.get("window_after", 1)
        )
        self._turn_window_bm25_max_sources_per_window = int(
            turn_window_config.get("max_sources_per_window", 3)
        )
        self._turn_window_bm25_max_chars_per_turn = int(
            turn_window_config.get("max_chars_per_turn", 0)
        )
        self._turn_window_bm25_drop_query_stopwords = bool(
            turn_window_config.get("drop_query_stopwords", self._drop_query_stopwords)
        )
        self._turn_window_bm25_score_threshold = float(
            turn_window_config.get("score_threshold", 0.0)
        )
        self._turn_window_bm25_enabled_signals = _tuple_config(
            turn_window_config.get("enabled_route_signals")
        )
        self._turn_window_bm25_enabled_information_needs = _tuple_config(
            turn_window_config.get("enabled_information_needs")
        )
        self._turn_window_bm25_enabled_query_patterns = _tuple_config(
            turn_window_config.get("enabled_query_patterns")
        )
        self._rerank_enabled = bool(rerank_config.get("enabled", False))
        self._rerank_model = rerank_config.get("model")
        self._rerank_base_url = rerank_config.get("base_url")
        self._rerank_pool_k = int(rerank_config.get("pool_k", self._base_top_k))
        self._rerank_batch_size = int(rerank_config.get("batch_size", 0))
        self._rerank_timeout = float(rerank_config.get("timeout", 120.0))
        self._rerank_document_max_chars = int(
            rerank_config.get("document_max_chars", 0)
        )
        self._rerank_anchor_keep = int(rerank_config.get("anchor_keep", 0))
        self._rerank_anchor_after_top = int(
            rerank_config.get("anchor_after_top", 0)
        )
        self._rerank_query_text_mode = str(
            rerank_config.get("query_text_mode", "external_naive")
        )
        self._rerank_information_needs = _tuple_config(
            rerank_config.get("information_needs")
        )
        self._rerank_client = None
        if self._rerank_enabled:
            if not self._rerank_model:
                raise ValueError("retrieval.rerank.model is required when enabled")
            if not self._rerank_base_url:
                raise ValueError("retrieval.rerank.base_url is required when enabled")
            self._rerank_client = OpenAICompatibleRerankClient(
                base_url=str(self._rerank_base_url),
                model=str(self._rerank_model),
                timeout=self._rerank_timeout,
                batch_size=self._rerank_batch_size,
                api_key_env=rerank_config.get("api_key_env"),
                api_key=rerank_config.get("api_key"),
            )
        self._embedding_client = None
        self._memory_builder = NullMemoryBuilder()
        if self._build_memory_enabled:
            build_mode = str(build_memory_config.get("mode", "openai_compatible"))
            if build_mode != "openai_compatible":
                raise ValueError(f"Unsupported build_memory.mode: {build_mode}")
            build_cache_config = build_memory_config.get("cache", {})
            build_cache_path = (
                build_cache_config.get("path")
                if bool(build_cache_config.get("enabled", False))
                else None
            )
            self._memory_builder = OpenAICompatibleMemoryBuilder(
                base_url=str(
                    build_memory_config.get("base_url", "http://127.0.0.1:8000/v1")
                ),
                model=str(build_memory_config["model"]),
                temperature=float(build_memory_config.get("temperature", 0.0)),
                max_tokens=int(build_memory_config.get("max_tokens", 768)),
                timeout=float(build_memory_config.get("timeout", 120.0)),
                max_turns_per_chunk=int(build_memory_config.get("max_turns_per_chunk", 80)),
                max_chars_per_turn=int(build_memory_config.get("max_chars_per_turn", 500)),
                max_records_per_chunk=int(
                    build_memory_config.get("max_records_per_chunk", 16)
                ),
                overlap_turns=int(build_memory_config.get("overlap_turns", 0)),
                cache_path=build_cache_path,
                cache_namespace=str(
                    build_cache_config.get(
                        "namespace",
                        build_memory_config.get("model", "unknown"),
                    )
                ),
                api_key_env=build_memory_config.get("api_key_env"),
                temporal_fields=bool(build_memory_config.get("temporal_fields", False)),
                prompt_profile=str(
                    build_memory_config.get("prompt_profile", "typed_compact")
                ),
                manage_facts=bool(build_memory_config.get("manage_facts", True)),
            )
        if self._dense_enabled:
            self._embedding_client = OpenAICompatibleEmbeddingClient(
                base_url=str(dense_config.get("base_url", "http://127.0.0.1:8001/v1")),
                model=str(dense_config["model"]),
                timeout=float(dense_config.get("timeout", 120.0)),
            )
            if self._embedding_cache_enabled:
                if self._embedding_cache_path is None:
                    raise ValueError("dense.cache.path is required when cache is enabled")
                self._embedding_client = CachedEmbeddingClient(
                    self._embedding_client,
                    cache_path=str(self._embedding_cache_path),
                    namespace=self._embedding_cache_namespace,
                )
        self._compiler = EvidenceCompiler(
            max_evidence_items=int(compiler_config.get("max_evidence_items", 20)),
            max_evidence_chars=int(compiler_config.get("max_evidence_chars", 12000)),
            answer_style=str(compiler_config.get("answer_style", "grounded")),
            temporal_grounding=bool(compiler_config.get("temporal_grounding", False)),
            temporal_hints=bool(compiler_config.get("temporal_hints", False)),
            temporal_workpad=bool(compiler_config.get("temporal_workpad", False)),
            temporal_text_normalization=bool(
                compiler_config.get("temporal_text_normalization", False)
            ),
            temporal_event_contract=bool(
                compiler_config.get("temporal_event_contract", False)
            ),
            temporal_workpad_scope=str(
                compiler_config.get("temporal_workpad_scope", "route")
            ),
            temporal_workpad_max_rows=int(
                compiler_config.get("temporal_workpad_max_rows", 10)
            ),
            temporal_workpad_max_pairs=int(
                compiler_config.get("temporal_workpad_max_pairs", 12)
            ),
            structured_guide=bool(compiler_config.get("structured_guide", False)),
            structured_guide_max_rows=int(
                compiler_config.get("structured_guide_max_rows", 12)
            ),
            structured_guide_include_rows=bool(
                compiler_config.get("structured_guide_include_rows", True)
            ),
            structured_guide_include_memory=bool(
                compiler_config.get("structured_guide_include_memory", True)
            ),
            structured_guide_disabled_signals=_tuple_config(
                compiler_config.get("structured_guide_disabled_signals")
            ),
            structured_answer_contract=bool(
                compiler_config.get("structured_answer_contract", False)
            ),
            structured_answer_contract_information_needs=_tuple_config(
                compiler_config.get(
                    "structured_answer_contract_information_needs",
                    ("list_count", "temporal_lookup"),
                )
            ),
            structured_answer_contract_max_items=int(
                compiler_config.get("structured_answer_contract_max_items", 10)
            ),
            evidence_report_contract=bool(
                compiler_config.get("evidence_report_contract", False)
            ),
            evidence_report_information_needs=_tuple_config(
                compiler_config.get(
                    "evidence_report_information_needs",
                    (
                        "current_state",
                        "fact_lookup",
                        "list_count",
                        "profile_preference",
                        "temporal_lookup",
                    ),
                )
            ),
            evidence_report_max_items=int(
                compiler_config.get("evidence_report_max_items", 8)
            ),
            evidence_report_detail=bool(
                compiler_config.get("evidence_report_detail", False)
            ),
            aggregation_report_contract=bool(
                compiler_config.get("aggregation_report_contract", False)
            ),
            aggregation_report_information_needs=_tuple_config(
                compiler_config.get(
                    "aggregation_report_information_needs",
                    ("list_count", "temporal_lookup"),
                )
            ),
            candidate_guide=bool(compiler_config.get("candidate_guide", False)),
            candidate_guide_information_needs=_tuple_config(
                compiler_config.get(
                    "candidate_guide_information_needs",
                    ("list_count", "temporal_lookup"),
                )
            ),
            candidate_guide_max_rows=int(
                compiler_config.get("candidate_guide_max_rows", 6)
            ),
            candidate_guide_snippet_chars=int(
                compiler_config.get("candidate_guide_snippet_chars", 160)
            ),
            operation_workpad=bool(compiler_config.get("operation_workpad", False)),
            operation_workpad_information_needs=_tuple_config(
                compiler_config.get(
                    "operation_workpad_information_needs",
                    ("list_count", "temporal_lookup"),
                )
            ),
            operation_workpad_question_gate=bool(
                compiler_config.get("operation_workpad_question_gate", False)
            ),
            current_state_update_contract=bool(
                compiler_config.get("current_state_update_contract", False)
            ),
            dialogue_inference_contract=bool(
                compiler_config.get("dialogue_inference_contract", False)
            ),
            temporal_order_contract=bool(
                compiler_config.get("temporal_order_contract", False)
            ),
            endpoint_validation_contract=bool(
                compiler_config.get("endpoint_validation_contract", False)
            ),
            endpoint_validation_information_needs=_tuple_config(
                compiler_config.get(
                    "endpoint_validation_information_needs",
                    ("list_count", "temporal_lookup"),
                )
            ),
            endpoint_validation_question_gate=bool(
                compiler_config.get("endpoint_validation_question_gate", True)
            ),
            source_anchor_keep=int(compiler_config.get("source_anchor_keep", 0)),
            source_anchor_memory_rows=int(
                compiler_config.get("source_anchor_memory_rows", 0)
            ),
            source_anchor_per_session=int(
                compiler_config.get("source_anchor_per_session", 0)
            ),
            source_anchor_session_rows=int(
                compiler_config.get("source_anchor_session_rows", 0)
            ),
            context_layout=str(compiler_config.get("context_layout", "flat")),
            evidence_order=str(compiler_config.get("evidence_order", "retrieval")),
            memory_order=str(compiler_config.get("memory_order", "retrieval")),
            memory_layout=str(compiler_config.get("memory_layout", "flat")),
            row_text_mode=str(compiler_config.get("row_text_mode", "full")),
            max_row_text_chars=int(compiler_config.get("max_row_text_chars", 0)),
            route_guidance=bool(compiler_config.get("route_guidance", False)),
            evidence_row_labels=bool(
                compiler_config.get("evidence_row_labels", False)
            ),
            final_answer_checklist=bool(
                compiler_config.get("final_answer_checklist", False)
            ),
            max_memory_records=int(compiler_config.get("max_memory_records", 12)),
            prompt_mode=str(compiler_config.get("prompt_mode", "default")),
            route_overrides=compiler_config.get("route_overrides") or {},
        )
        self._compiler_memory_record_source = _validate_memory_record_source(
            str(compiler_config.get("memory_record_source", "retrieval"))
        )
        self._compiler_trace_config = {
            "prompt_mode": str(compiler_config.get("prompt_mode", "default")),
            "memory_record_source": self._compiler_memory_record_source,
            "evidence_order": str(compiler_config.get("evidence_order", "retrieval")),
            "memory_order": str(compiler_config.get("memory_order", "retrieval")),
            "memory_layout": str(compiler_config.get("memory_layout", "flat")),
            "row_text_mode": str(compiler_config.get("row_text_mode", "full")),
            "max_row_text_chars": int(compiler_config.get("max_row_text_chars", 0)),
            "evidence_row_labels": bool(
                compiler_config.get("evidence_row_labels", False)
            ),
            "final_answer_checklist": bool(
                compiler_config.get("final_answer_checklist", False)
            ),
            "route_guidance": bool(compiler_config.get("route_guidance", False)),
            "answer_style": str(compiler_config.get("answer_style", "grounded")),
            "temporal_grounding": bool(
                compiler_config.get("temporal_grounding", False)
            ),
            "temporal_hints": bool(compiler_config.get("temporal_hints", False)),
            "temporal_workpad": bool(
                compiler_config.get("temporal_workpad", False)
            ),
            "temporal_text_normalization": bool(
                compiler_config.get("temporal_text_normalization", False)
            ),
            "temporal_event_contract": bool(
                compiler_config.get("temporal_event_contract", False)
            ),
            "temporal_workpad_scope": str(
                compiler_config.get("temporal_workpad_scope", "route")
            ),
            "temporal_workpad_max_rows": int(
                compiler_config.get("temporal_workpad_max_rows", 10)
            ),
            "temporal_workpad_max_pairs": int(
                compiler_config.get("temporal_workpad_max_pairs", 12)
            ),
            "structured_guide": bool(compiler_config.get("structured_guide", False)),
            "structured_guide_max_rows": int(
                compiler_config.get("structured_guide_max_rows", 12)
            ),
            "structured_guide_include_rows": bool(
                compiler_config.get("structured_guide_include_rows", True)
            ),
            "structured_guide_include_memory": bool(
                compiler_config.get("structured_guide_include_memory", True)
            ),
            "structured_guide_disabled_signals": _tuple_config(
                compiler_config.get("structured_guide_disabled_signals")
            ),
            "structured_answer_contract": bool(
                compiler_config.get("structured_answer_contract", False)
            ),
            "structured_answer_contract_information_needs": _tuple_config(
                compiler_config.get(
                    "structured_answer_contract_information_needs",
                    ("list_count", "temporal_lookup"),
                )
            ),
            "structured_answer_contract_max_items": int(
                compiler_config.get("structured_answer_contract_max_items", 10)
            ),
            "evidence_report_contract": bool(
                compiler_config.get("evidence_report_contract", False)
            ),
            "evidence_report_information_needs": _tuple_config(
                compiler_config.get("evidence_report_information_needs")
            ),
            "evidence_report_max_items": int(
                compiler_config.get("evidence_report_max_items", 8)
            ),
            "evidence_report_detail": bool(
                compiler_config.get("evidence_report_detail", False)
            ),
            "aggregation_report_contract": bool(
                compiler_config.get("aggregation_report_contract", False)
            ),
            "aggregation_report_information_needs": _tuple_config(
                compiler_config.get(
                    "aggregation_report_information_needs",
                    ("list_count", "temporal_lookup"),
                )
            ),
            "candidate_guide": bool(compiler_config.get("candidate_guide", False)),
            "candidate_guide_information_needs": _tuple_config(
                compiler_config.get(
                    "candidate_guide_information_needs",
                    ("list_count", "temporal_lookup"),
                )
            ),
            "candidate_guide_max_rows": int(
                compiler_config.get("candidate_guide_max_rows", 6)
            ),
            "candidate_guide_snippet_chars": int(
                compiler_config.get("candidate_guide_snippet_chars", 160)
            ),
            "operation_workpad": bool(
                compiler_config.get("operation_workpad", False)
            ),
            "operation_workpad_information_needs": _tuple_config(
                compiler_config.get(
                    "operation_workpad_information_needs",
                    ("list_count", "temporal_lookup"),
                )
            ),
            "operation_workpad_question_gate": bool(
                compiler_config.get("operation_workpad_question_gate", False)
            ),
            "current_state_update_contract": bool(
                compiler_config.get("current_state_update_contract", False)
            ),
            "dialogue_inference_contract": bool(
                compiler_config.get("dialogue_inference_contract", False)
            ),
            "temporal_order_contract": bool(
                compiler_config.get("temporal_order_contract", False)
            ),
            "endpoint_validation_contract": bool(
                compiler_config.get("endpoint_validation_contract", False)
            ),
            "endpoint_validation_information_needs": _tuple_config(
                compiler_config.get(
                    "endpoint_validation_information_needs",
                    ("list_count", "temporal_lookup"),
                )
            ),
            "endpoint_validation_question_gate": bool(
                compiler_config.get("endpoint_validation_question_gate", True)
            ),
            "source_anchor_keep": int(compiler_config.get("source_anchor_keep", 0)),
            "source_anchor_memory_rows": int(
                compiler_config.get("source_anchor_memory_rows", 0)
            ),
            "source_anchor_per_session": int(
                compiler_config.get("source_anchor_per_session", 0)
            ),
            "source_anchor_session_rows": int(
                compiler_config.get("source_anchor_session_rows", 0)
            ),
            "context_layout": str(compiler_config.get("context_layout", "flat")),
            "max_memory_records": int(compiler_config.get("max_memory_records", 12)),
            "route_overrides": compiler_config.get("route_overrides") or {},
        }
        answer_mode = str(answer_config.get("mode", "null_answerer"))
        self._answer_finalizer_enabled = bool(
            answer_finalizer_config.get("enabled", False)
        )
        self._answer_finalizer_mode = str(
            answer_finalizer_config.get("mode", "structured_evidence_mechanical")
        )
        self._answer_finalizer_enable_count_correction = bool(
            answer_finalizer_config.get("enable_count_correction", False)
        )
        self._answer_finalizer_enable_evidence_report_count_correction = bool(
            answer_finalizer_config.get(
                "enable_evidence_report_count_correction", False
            )
        )
        self._answer_finalizer_enable_money_sum_correction = bool(
            answer_finalizer_config.get("enable_money_sum_correction", True)
        )
        self._answer_finalizer_enable_duration_rounding_correction = bool(
            answer_finalizer_config.get(
                "enable_duration_rounding_correction",
                False,
            )
        )
        self._answer_finalizer_trace_config = {
            "enabled": self._answer_finalizer_enabled,
            "mode": self._answer_finalizer_mode,
            "enable_count_correction": (
                self._answer_finalizer_enable_count_correction
            ),
            "enable_evidence_report_count_correction": (
                self._answer_finalizer_enable_evidence_report_count_correction
            ),
            "enable_money_sum_correction": (
                self._answer_finalizer_enable_money_sum_correction
            ),
            "enable_duration_rounding_correction": (
                self._answer_finalizer_enable_duration_rounding_correction
            ),
        }
        self._answer_repair_enabled = bool(answer_repair_config.get("enabled", False))
        self._answer_repair_information_needs = _tuple_config(
            answer_repair_config.get(
                "information_needs",
                (
                    "current_state",
                    "fact_lookup",
                    "list_count",
                    "profile_preference",
                    "temporal_lookup",
                ),
            )
        )
        self._answer_repair_enable_uncertain_trigger = bool(
            answer_repair_config.get("enable_uncertain_trigger", True)
        )
        self._answer_repair_enable_short_list_trigger = bool(
            answer_repair_config.get("enable_short_list_trigger", True)
        )
        self._answer_repair_enable_temporal_conflict_trigger = bool(
            answer_repair_config.get("enable_temporal_conflict_trigger", True)
        )
        self._answer_repair_enable_profile_preference_trigger = bool(
            answer_repair_config.get("enable_profile_preference_trigger", False)
        )
        self._answer_repair_uncertain_min_support_items = int(
            answer_repair_config.get("uncertain_min_support_items", 0)
        )
        self._answer_repair_max_context_chars = int(
            answer_repair_config.get("max_context_chars", 14000)
        )
        self._answer_repair_max_row_text_chars = int(
            answer_repair_config.get("max_row_text_chars", 700)
        )
        self._answer_repair_mode = str(answer_repair_config.get("mode", answer_mode))
        self._answer_repair_trace_config = {
            "enabled": self._answer_repair_enabled,
            "mode": self._answer_repair_mode if self._answer_repair_enabled else None,
            "information_needs": self._answer_repair_information_needs,
            "enable_uncertain_trigger": self._answer_repair_enable_uncertain_trigger,
            "enable_short_list_trigger": (
                self._answer_repair_enable_short_list_trigger
            ),
            "enable_temporal_conflict_trigger": (
                self._answer_repair_enable_temporal_conflict_trigger
            ),
            "enable_profile_preference_trigger": (
                self._answer_repair_enable_profile_preference_trigger
            ),
            "uncertain_min_support_items": (
                self._answer_repair_uncertain_min_support_items
            ),
            "max_context_chars": self._answer_repair_max_context_chars,
            "max_row_text_chars": self._answer_repair_max_row_text_chars,
        }
        self._answer_repairer = None
        self._answer_repair_cache_enabled = bool(
            answer_repair_config.get("cache", {}).get("enabled", False)
        )
        self._answer_repair_cache_path = answer_repair_config.get("cache", {}).get(
            "path"
        )
        self._answer_repair_cache_namespace = ""
        self._answer_cache_enabled = bool(
            answer_config.get("cache", {}).get("enabled", False)
        )
        self._answer_cache_path = answer_config.get("cache", {}).get("path")
        self._answer_cache_namespace = _answer_cache_namespace(
            answer_config,
            answer_mode,
        )
        self._answerer = _configured_answerer(
            answer_config,
            answer_mode=answer_mode,
            cache_error_prefix="answer",
        )
        if self._answer_repair_enabled:
            repair_answer_config = _repair_answer_config(
                answer_config,
                answer_repair_config,
            )
            self._answer_repair_cache_namespace = _answer_cache_namespace(
                repair_answer_config,
                self._answer_repair_mode,
            )
            self._answer_repairer = _configured_answerer(
                repair_answer_config,
                answer_mode=self._answer_repair_mode,
                cache_error_prefix="answer.repair",
            )
            self._answer_repair_trace_config = {
                **self._answer_repair_trace_config,
                "model": repair_answer_config.get("model"),
                "base_url": repair_answer_config.get("base_url"),
                "temperature": repair_answer_config.get("temperature"),
                "max_input_tokens": repair_answer_config.get("max_input_tokens"),
                "max_output_tokens": _answer_max_output_tokens(repair_answer_config),
                "output_format": repair_answer_config.get(
                    "output_format", "json_answer"
                ),
                "cache_enabled": self._answer_repair_cache_enabled,
                "cache_path": self._answer_repair_cache_path,
                "cache_namespace": self._answer_repair_cache_namespace,
            }
        self._scoped_evidence_enabled = bool(
            scoped_evidence_config.get("enabled", False)
        )
        self._scoped_evidence_information_needs = _tuple_config(
            scoped_evidence_config.get(
                "information_needs",
                ("list_count", "temporal_lookup"),
            )
        )
        self._scoped_evidence_max_rows = int(
            scoped_evidence_config.get("max_rows", 40)
        )
        self._scoped_evidence_max_row_chars = int(
            scoped_evidence_config.get("max_row_chars", 360)
        )
        self._scoped_evidence_extractor = None
        self._scoped_evidence_answerer = None
        self._scoped_evidence_trace_config = {
            "enabled": self._scoped_evidence_enabled,
            "information_needs": self._scoped_evidence_information_needs,
            "max_rows": self._scoped_evidence_max_rows,
            "max_row_chars": self._scoped_evidence_max_row_chars,
        }
        if self._scoped_evidence_enabled:
            scoped_mode = str(scoped_evidence_config.get("mode", answer_mode))
            extractor_config = _scoped_evidence_stage_config(
                answer_config=answer_config,
                scoped_evidence_config=scoped_evidence_config,
                stage="extractor",
                output_format="text",
            )
            final_answer_config = _scoped_evidence_stage_config(
                answer_config=answer_config,
                scoped_evidence_config=scoped_evidence_config,
                stage="answer",
                output_format="json_answer",
            )
            self._scoped_evidence_extractor = _configured_answerer(
                extractor_config,
                answer_mode=str(extractor_config.get("mode", scoped_mode)),
            )
            self._scoped_evidence_answerer = _configured_answerer(
                final_answer_config,
                answer_mode=str(final_answer_config.get("mode", scoped_mode)),
            )
            self._scoped_evidence_trace_config = {
                **self._scoped_evidence_trace_config,
                "extractor": _answerer_trace_config(extractor_config),
                "answer": _answerer_trace_config(final_answer_config),
            }

    def predict(self, request: PredictionRequest) -> dict[str, Any]:
        store = RawEvidenceStore(request.turns)
        built_memory = self._memory_builder.build(store.turns)
        source_alignment = _disabled_source_alignment_trace(
            enabled=self._build_memory_source_alignment_enabled
        )
        if self._build_memory_source_alignment_enabled:
            aligned_records, source_alignment = _align_build_memory_sources(
                built_memory.records,
                store=store,
                window=self._build_memory_source_alignment_window,
                max_sources_per_record=self._build_memory_source_alignment_max_sources,
                min_score=self._build_memory_source_alignment_min_score,
                min_delta=self._build_memory_source_alignment_min_delta,
            )
            built_memory = replace(built_memory, records=aligned_records)
        heuristic_route = self._router.route(request.question, request.question_time)
        route = heuristic_route
        retrieval_settings = self._retrieval_settings_for_route(route)
        top_k = retrieval_settings["top_k"]
        candidate_top_k = retrieval_settings["candidate_top_k"]
        dense_top_k = retrieval_settings["dense_top_k"]
        lexical_protect_top_n = retrieval_settings["lexical_protect_top_n"]
        dense_protect_top_n = retrieval_settings["dense_protect_top_n"]
        retriever = LexicalBM25Retriever(
            store.turns,
            drop_query_stopwords=self._drop_query_stopwords,
        )
        lexical_hits = ()
        if self._lexical_enabled:
            lexical_hits = retriever.retrieve(
                request.question,
                top_k=candidate_top_k,
                score_threshold=self._score_threshold,
            )
        memory_hits = ()
        memory_source_hits = ()
        build_memory_include_superseded = (
            self._build_memory_include_superseded
            or route.information_need
            in self._build_memory_include_superseded_information_needs
        )
        if self._build_memory_enabled and self._build_memory_top_k > 0:
            memory_hits = BuildMemoryBM25Retriever(
                built_memory.records,
                drop_query_stopwords=self._build_memory_drop_query_stopwords,
                include_superseded=build_memory_include_superseded,
            ).retrieve(
                request.question,
                top_k=self._build_memory_top_k,
                score_threshold=0.0,
            )
            memory_source_hits = memory_hits_to_source_hits(
                memory_hits,
                max_sources_per_memory=self._build_memory_max_sources_per_record,
            )
        turn_window_hits = ()
        turn_window_source_hits = ()
        turn_window_bm25_applied = False
        if (
            self._turn_window_bm25_enabled
            and self._turn_window_bm25_top_k > 0
            and self._turn_window_bm25_max_sources_per_window > 0
            and _turn_window_bm25_applies(
                route=route,
                question=request.question,
                enabled_signals=self._turn_window_bm25_enabled_signals,
                enabled_information_needs=self._turn_window_bm25_enabled_information_needs,
                enabled_query_patterns=self._turn_window_bm25_enabled_query_patterns,
            )
        ):
            turn_window_bm25_applied = True
            turn_window_documents = build_turn_window_documents(
                store.turns,
                window_before=self._turn_window_bm25_window_before,
                window_after=self._turn_window_bm25_window_after,
                max_chars_per_turn=self._turn_window_bm25_max_chars_per_turn,
            )
            turn_window_hits = TurnWindowBM25Retriever(
                turn_window_documents,
                drop_query_stopwords=self._turn_window_bm25_drop_query_stopwords,
            ).retrieve(
                request.question,
                top_k=self._turn_window_bm25_top_k,
                score_threshold=self._turn_window_bm25_score_threshold,
            )
            turn_window_source_hits = turn_window_hits_to_source_hits(
                turn_window_hits,
                max_sources_per_window=self._turn_window_bm25_max_sources_per_window,
            )
        dense_hits = ()
        embedding_tokens = 0
        embedding_cache_before = _embedding_cache_stats(self._embedding_client)
        if self._embedding_client is not None:
            dense_result = DenseEmbeddingRetriever(
                store.turns,
                self._embedding_client,
                batch_size=self._dense_batch_size,
                document_text_mode=self._dense_document_text_mode,
            ).retrieve(
                _dense_query_text(
                    request.question,
                    request.question_time,
                    mode=self._dense_query_text_mode,
                ),
                top_k=dense_top_k,
            )
            dense_hits = dense_result.hits
            embedding_tokens = dense_result.embedding_tokens
            hit_lists = tuple(
                hits for hits in (lexical_hits, dense_hits) if hits
            )
            if memory_source_hits:
                hit_lists = (*hit_lists, memory_source_hits)
            if turn_window_source_hits:
                hit_lists = (*hit_lists, turn_window_source_hits)
            hits = _merge_hit_lists(
                hit_lists,
                top_k=candidate_top_k,
                rrf_k=self._fusion_rrf_k,
            )
            if lexical_protect_top_n > 0 and lexical_hits:
                hits = prepend_protected_hits(
                    lexical_hits[:lexical_protect_top_n],
                    hits,
                    top_k=candidate_top_k,
                )
            if dense_protect_top_n > 0 and dense_hits:
                hits = prepend_protected_hits(
                    dense_hits[:dense_protect_top_n],
                    hits,
                    top_k=candidate_top_k,
                )
        else:
            if memory_source_hits or turn_window_source_hits:
                hits = _merge_hit_lists(
                    tuple(
                        hits
                        for hits in (
                            lexical_hits,
                            memory_source_hits,
                            turn_window_source_hits,
                        )
                        if hits
                    ),
                    top_k=candidate_top_k,
                    rrf_k=self._fusion_rrf_k,
                )
            else:
                hits = lexical_hits
        embedding_cache_after = _embedding_cache_stats(self._embedding_client)
        turn_hits = hits
        pre_rerank_hits = hits
        rerank_trace = _disabled_rerank_trace(
            enabled=self._rerank_enabled,
            information_needs=self._rerank_information_needs,
        )
        if self._rerank_client is not None and _rerank_applies(
            route=route,
            enabled_information_needs=self._rerank_information_needs,
        ):
            hits, rerank_trace = self._rerank_hits(
                store=store,
                request=request,
                hits=hits,
                top_k=top_k,
            )
        evidence_turns = store.expand_neighbors(
            (hit.source_id for hit in hits),
            window=self._neighbor_window,
            order=self._neighbor_order,
        )
        compiler_memory_records = _compiler_memory_records(
            source=self._compiler_memory_record_source,
            memory_hits=memory_hits,
            built_memory_records=built_memory.records,
            evidence_turns=evidence_turns,
        )
        compiled = self._compiler.compile(
            question=request.question,
            question_time=request.question_time,
            route=route,
            hits=hits,
            evidence_turns=evidence_turns,
            memory_records=compiler_memory_records,
        )
        answer_cache_before = _answer_cache_stats(self._answerer)
        scoped_evidence = disabled_scoped_evidence_run(
            enabled=self._scoped_evidence_enabled,
            information_needs=self._scoped_evidence_information_needs,
            max_rows=self._scoped_evidence_max_rows,
            max_row_chars=self._scoped_evidence_max_row_chars,
        )
        if (
            self._scoped_evidence_enabled
            and self._scoped_evidence_extractor is not None
            and self._scoped_evidence_answerer is not None
            and should_apply_scoped_evidence(
                compiled,
                self._scoped_evidence_information_needs,
            )
        ):
            draft_answer, scoped_evidence = self._answer_with_scoped_evidence(compiled)
            answer_cache_after = _answer_cache_stats(self._answerer)
        else:
            draft_answer = self._answerer.answer(compiled)
            answer_cache_after = _answer_cache_stats(self._answerer)
        repair_cache_before = _answer_cache_stats(self._answer_repairer)
        answer_repair = maybe_repair_answer(
            answerer=self._answer_repairer,
            compiled=compiled,
            draft=draft_answer,
            enabled=self._answer_repair_enabled,
            information_needs=self._answer_repair_information_needs,
            enable_uncertain_trigger=self._answer_repair_enable_uncertain_trigger,
            enable_short_list_trigger=self._answer_repair_enable_short_list_trigger,
            enable_temporal_conflict_trigger=(
                self._answer_repair_enable_temporal_conflict_trigger
            ),
            enable_profile_preference_trigger=(
                self._answer_repair_enable_profile_preference_trigger
            ),
            uncertain_min_support_items=(
                self._answer_repair_uncertain_min_support_items
            ),
            max_context_chars=self._answer_repair_max_context_chars,
            max_row_text_chars=self._answer_repair_max_row_text_chars,
        )
        repair_cache_after = _answer_cache_stats(self._answer_repairer)
        answer = answer_repair.answer
        answer_finalization = self._finalize_answer(
            question=request.question,
            answer=answer,
        )
        if answer_finalization.applied:
            answer = AnswerResult(
                answer=answer_finalization.answer,
                model=answer.model,
                token_usage=answer.token_usage,
                raw_response=answer.raw_response,
            )
        token_usage = TokenUsage(
            build_tokens=(
                built_memory.token_usage.build_tokens
                + answer.token_usage.build_tokens
            ),
            query_tokens=answer.token_usage.query_tokens,
        )
        return {
            "answer": answer.answer,
            "trace": {
                "store": store.manifest(),
                "build_memory": built_memory.to_dict(),
                "build_memory_config": self._build_memory_trace_config,
                "build_memory_source_alignment": source_alignment,
                "route": route.to_dict(),
                "heuristic_route": heuristic_route.to_dict(),
                "route_config": self._route_trace_config,
                "retrieval": {
                    "retriever": _retriever_name(
                        lexical_enabled=self._lexical_enabled,
                        dense_enabled=self._dense_enabled,
                        turn_window_bm25_enabled=self._turn_window_bm25_enabled,
                        build_memory_enabled=self._build_memory_enabled,
                        rerank_enabled=self._rerank_enabled,
                    ),
                    "top_k": top_k,
                    "candidate_top_k": candidate_top_k,
                    "base_top_k": self._base_top_k,
                    "max_top_k": self._max_top_k,
                    "route_overrides": self._retrieval_route_overrides,
                    "route_override": self._retrieval_route_overrides.get(
                        route.information_need, {}
                    ),
                    "neighbor_window": self._neighbor_window,
                    "neighbor_order": self._neighbor_order,
                    "drop_query_stopwords": self._drop_query_stopwords,
                    "lexical_enabled": self._lexical_enabled,
                    "build_memory_enabled": self._build_memory_enabled,
                    "build_memory_top_k": self._build_memory_top_k,
                    "build_memory_max_sources_per_record": (
                        self._build_memory_max_sources_per_record
                    ),
                    "build_memory_include_superseded": (
                        build_memory_include_superseded
                    ),
                    "build_memory_include_superseded_default": (
                        self._build_memory_include_superseded
                    ),
                    "build_memory_include_superseded_information_needs": (
                        self._build_memory_include_superseded_information_needs
                    ),
                    "dense_enabled": self._dense_enabled,
                    "dense_top_k": dense_top_k if self._dense_enabled else None,
                    "dense_document_text_mode": self._dense_document_text_mode
                    if self._dense_enabled
                    else None,
                    "dense_query_text_mode": self._dense_query_text_mode
                    if self._dense_enabled
                    else None,
                    "lexical_protect_top_n": lexical_protect_top_n
                    if self._dense_enabled
                    else None,
                    "dense_protect_top_n": dense_protect_top_n
                    if self._dense_enabled
                    else None,
                    "embedding_cache_enabled": self._embedding_cache_enabled
                    if self._dense_enabled
                    else None,
                    "embedding_cache_path": str(self._embedding_cache_path)
                    if self._dense_enabled and self._embedding_cache_enabled
                    else None,
                    "embedding_cache_namespace": self._embedding_cache_namespace
                    if self._dense_enabled and self._embedding_cache_enabled
                    else None,
                    "embedding_cache": _embedding_cache_delta(
                        embedding_cache_before,
                        embedding_cache_after,
                    ),
                    "turn_window_bm25_enabled": self._turn_window_bm25_enabled,
                    "turn_window_bm25_applied": turn_window_bm25_applied,
                    "turn_window_top_k": self._turn_window_bm25_top_k
                    if turn_window_bm25_applied
                    else None,
                    "turn_window_window_before": (
                        self._turn_window_bm25_window_before
                        if turn_window_bm25_applied
                        else None
                    ),
                    "turn_window_window_after": (
                        self._turn_window_bm25_window_after
                        if turn_window_bm25_applied
                        else None
                    ),
                    "turn_window_max_sources_per_window": (
                        self._turn_window_bm25_max_sources_per_window
                        if turn_window_bm25_applied
                        else None
                    ),
                    "turn_window_max_chars_per_turn": (
                        self._turn_window_bm25_max_chars_per_turn
                        if turn_window_bm25_applied
                        else None
                    ),
                    "turn_window_drop_query_stopwords": (
                        self._turn_window_bm25_drop_query_stopwords
                        if turn_window_bm25_applied
                        else None
                    ),
                    "turn_window_enabled_route_signals": (
                        self._turn_window_bm25_enabled_signals
                    ),
                    "turn_window_enabled_information_needs": (
                        self._turn_window_bm25_enabled_information_needs
                    ),
                    "turn_window_enabled_query_patterns": (
                        self._turn_window_bm25_enabled_query_patterns
                    ),
                    "embedding_tokens": embedding_tokens,
                    "lexical_hits": [hit.to_dict() for hit in lexical_hits],
                    "memory_hits": [hit.to_dict() for hit in memory_hits],
                    "compiler_memory_record_source": self._compiler_memory_record_source,
                    "compiler_memory_records": [
                        record.to_dict() for record in compiler_memory_records
                    ],
                    "memory_source_hits": [
                        hit.to_dict() for hit in memory_source_hits
                    ],
                    "dense_hits": [hit.to_dict() for hit in dense_hits],
                    "turn_window_hits": [
                        hit.to_dict() for hit in turn_window_hits
                    ],
                    "turn_window_source_hits": [
                        hit.to_dict() for hit in turn_window_source_hits
                    ],
                    "turn_hits": [hit.to_dict() for hit in turn_hits],
                    "rerank_enabled": self._rerank_enabled,
                    "rerank_applied": rerank_trace["applied"],
                    "rerank_model": self._rerank_model
                    if self._rerank_enabled
                    else None,
                    "rerank_base_url": self._rerank_base_url
                    if self._rerank_enabled
                    else None,
                    "rerank_pool_k": self._rerank_pool_k
                    if self._rerank_enabled
                    else None,
                    "rerank_query_text_mode": self._rerank_query_text_mode
                    if self._rerank_enabled
                    else None,
                    "rerank_document_max_chars": self._rerank_document_max_chars
                    if self._rerank_enabled
                    else None,
                    "rerank_anchor_keep": self._rerank_anchor_keep
                    if self._rerank_enabled
                    else None,
                    "rerank_anchor_after_top": self._rerank_anchor_after_top
                    if self._rerank_enabled
                    else None,
                    "rerank_information_needs": self._rerank_information_needs,
                    "rerank_candidate_count": rerank_trace["candidate_count"],
                    "rerank_returned_count": rerank_trace["returned_count"],
                    "rerank_total_tokens": rerank_trace["total_tokens"],
                    "rerank_response": rerank_trace["response"],
                    "pre_rerank_hits": [
                        hit.to_dict() for hit in pre_rerank_hits
                    ],
                    "hits": [hit.to_dict() for hit in hits],
                },
                "compiled_context": compiled.to_dict(),
                "compiler": self._compiler_trace_config,
                "answer_cache": _answer_cache_delta(
                    answer_cache_before,
                    answer_cache_after,
                ),
                "scoped_evidence": {
                    **self._scoped_evidence_trace_config,
                    **scoped_evidence.to_dict(),
                },
                "answer_draft": draft_answer.to_dict(),
                "answer_repair": {
                    **self._answer_repair_trace_config,
                    **answer_repair.to_dict(),
                    "cache": _answer_cache_delta(
                        repair_cache_before,
                        repair_cache_after,
                    ),
                },
                "answer_finalizer": {
                    **self._answer_finalizer_trace_config,
                    **answer_finalization.to_dict(),
                },
                "answer": answer.to_dict(),
                "token_cost": token_usage.to_dict(),
            },
        }

    def _answer_with_scoped_evidence(
        self,
        compiled: CompiledContext,
    ) -> tuple[AnswerResult, ScopedEvidenceRun]:
        if (
            self._scoped_evidence_extractor is None
            or self._scoped_evidence_answerer is None
        ):
            raise RuntimeError("scoped evidence answerers are not configured")

        extraction_prompt = build_scoped_evidence_extraction_prompt(
            compiled,
            max_rows=self._scoped_evidence_max_rows,
            max_row_chars=self._scoped_evidence_max_row_chars,
        )
        extraction_context = CompiledContext(
            question=compiled.question,
            question_time=compiled.question_time,
            route=compiled.route,
            evidence_rows=compiled.evidence_rows,
            prompt=extraction_prompt,
            context_chars=len(extraction_prompt),
            memory_records=compiled.memory_records,
        )
        extraction_cache_before = _answer_cache_stats(self._scoped_evidence_extractor)
        extraction_result = self._scoped_evidence_extractor.answer(extraction_context)
        extraction_cache_after = _answer_cache_stats(self._scoped_evidence_extractor)
        evidence_json = extract_evidence_json_text(extraction_result.answer)

        answer_prompt = build_scoped_evidence_answer_prompt(
            compiled,
            evidence_json=evidence_json,
        )
        answer_context = CompiledContext(
            question=compiled.question,
            question_time=compiled.question_time,
            route=compiled.route,
            evidence_rows=(),
            prompt=answer_prompt,
            context_chars=len(answer_prompt),
            memory_records=(),
        )
        answer_cache_before = _answer_cache_stats(self._scoped_evidence_answerer)
        final_result = self._scoped_evidence_answerer.answer(answer_context)
        answer_cache_after = _answer_cache_stats(self._scoped_evidence_answerer)
        answer = scoped_evidence_answer_result(
            extraction_result=extraction_result,
            final_result=final_result,
        )
        trace = ScopedEvidenceRun(
            enabled=True,
            applied=True,
            information_needs=self._scoped_evidence_information_needs,
            max_rows=self._scoped_evidence_max_rows,
            max_row_chars=self._scoped_evidence_max_row_chars,
            extraction_prompt_chars=len(extraction_prompt),
            answer_prompt_chars=len(answer_prompt),
            evidence_json_chars=len(evidence_json),
            extraction={
                "response": extraction_result.to_dict(),
                "evidence_json": evidence_json,
                "parsed_evidence": parsed_evidence_json(evidence_json),
            },
            answer={"response": final_result.to_dict()},
            extraction_cache=_answer_cache_delta(
                extraction_cache_before,
                extraction_cache_after,
            ),
            answer_cache=_answer_cache_delta(answer_cache_before, answer_cache_after),
        )
        return answer, trace

    def _retrieval_settings_for_route(self, route: RouteResult) -> dict[str, int]:
        settings = {
            "top_k": self._base_top_k,
            "max_top_k": self._max_top_k,
            "dense_top_k": self._dense_top_k,
            "lexical_protect_top_n": self._lexical_protect_top_n,
            "dense_protect_top_n": self._dense_protect_top_n,
        }
        settings.update(self._retrieval_route_overrides.get(route.information_need, {}))
        top_k = min(
            settings["top_k"] * route.retrieval_multiplier,
            settings["max_top_k"],
        )
        candidate_top_k = top_k
        dense_top_k = settings["dense_top_k"]
        if self._rerank_enabled and _rerank_applies(
            route=route,
            enabled_information_needs=self._rerank_information_needs,
        ):
            candidate_top_k = max(candidate_top_k, self._rerank_pool_k)
            dense_top_k = max(dense_top_k, candidate_top_k)
        return {
            "top_k": top_k,
            "candidate_top_k": candidate_top_k,
            "dense_top_k": dense_top_k,
            "lexical_protect_top_n": settings["lexical_protect_top_n"],
            "dense_protect_top_n": settings["dense_protect_top_n"],
        }

    def _rerank_hits(
        self,
        *,
        store: RawEvidenceStore,
        request: PredictionRequest,
        hits: tuple[RetrievalHit, ...],
        top_k: int,
    ) -> tuple[tuple[RetrievalHit, ...], dict[str, Any]]:
        if self._rerank_client is None or not hits:
            return hits[:top_k], _disabled_rerank_trace(
                enabled=self._rerank_enabled,
                information_needs=self._rerank_information_needs,
            )

        rerank_items = tuple(
            (hit, turn)
            for hit in hits
            if (turn := store.get(hit.source_id)) is not None
        )
        if not rerank_items:
            trace = _disabled_rerank_trace(
                enabled=self._rerank_enabled,
                information_needs=self._rerank_information_needs,
            )
            trace["response"] = {"skipped": "no_source_documents"}
            return hits[:top_k], trace
        rerank_hits = tuple(hit for hit, _turn in rerank_items)
        documents = [
            format_rerank_turn_document(
                turn,
                max_chars=self._rerank_document_max_chars,
            )
            for _hit, turn in rerank_items
        ]
        query = _dense_query_text(
            request.question,
            request.question_time,
            mode=self._rerank_query_text_mode,
        )
        result = self._rerank_client.rerank(query=query, documents=documents)
        reranked_hits = rerank_hits_with_anchor_retention(
            hits=rerank_hits,
            scores=result.scores,
            top_k=top_k,
            anchor_keep=self._rerank_anchor_keep,
            anchor_after_top=self._rerank_anchor_after_top,
        )
        return reranked_hits, {
            "enabled": self._rerank_enabled,
            "applied": True,
            "information_needs": self._rerank_information_needs,
            "candidate_count": len(rerank_hits),
            "returned_count": len(reranked_hits),
            "total_tokens": result.total_tokens,
            "response": result.response,
        }

    def _finalize_answer(
        self,
        *,
        question: str,
        answer: AnswerResult,
    ) -> AnswerFinalization:
        if not self._answer_finalizer_enabled:
            return AnswerFinalization(
                answer=answer.answer,
                before=answer.answer,
                applied=False,
                reason="disabled",
            )
        if self._answer_finalizer_mode != "structured_evidence_mechanical":
            raise ValueError(
                f"Unsupported answer.finalizer.mode: {self._answer_finalizer_mode}"
            )
        return finalize_structured_answer(
            question=question,
            draft_answer=answer.answer,
            raw_response=answer.raw_response,
            enable_count_correction=self._answer_finalizer_enable_count_correction,
            enable_evidence_report_count_correction=(
                self._answer_finalizer_enable_evidence_report_count_correction
            ),
            enable_money_sum_correction=(
                self._answer_finalizer_enable_money_sum_correction
            ),
            enable_duration_rounding_correction=(
                self._answer_finalizer_enable_duration_rounding_correction
            ),
        )

_SOURCE_ALIGNMENT_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "been",
    "by",
    "for",
    "from",
    "has",
    "have",
    "i",
    "in",
    "is",
    "it",
    "my",
    "of",
    "on",
    "or",
    "that",
    "the",
    "their",
    "they",
    "this",
    "to",
    "user",
    "was",
    "with",
}


def _disabled_source_alignment_trace(*, enabled: bool) -> dict[str, Any]:
    return {
        "enabled": enabled,
        "records_seen": 0,
        "records_changed": 0,
        "sources_added": 0,
    }


def _align_build_memory_sources(
    records: tuple[Any, ...],
    *,
    store: RawEvidenceStore,
    window: int,
    max_sources_per_record: int,
    min_score: float,
    min_delta: float,
) -> tuple[tuple[Any, ...], dict[str, Any]]:
    """Repair near-miss build-memory provenance using local raw turns.

    The LLM extractor sometimes assigns a memory to the user turn that asked for
    an assistant answer, while the factual value appears in the adjacent
    assistant turn. This pass is question-independent and uses only the built
    memory text plus same-session raw turns, so it is clean provenance repair
    rather than benchmark feedback.
    """

    trace = _disabled_source_alignment_trace(enabled=True)
    if not records or max_sources_per_record <= 0:
        return records, trace | {"records_seen": len(records)}

    aligned_records = []
    changed = 0
    added = 0
    safe_window = max(0, int(window))
    safe_limit = max(1, int(max_sources_per_record))

    for record in records:
        source_ids = tuple(getattr(record, "source_ids", ()))
        candidates = _source_alignment_candidates(
            source_ids,
            store=store,
            window=safe_window,
        )
        aligned_source_ids = _rank_aligned_source_ids(
            record,
            candidates,
            original_source_ids=source_ids,
            min_score=min_score,
            min_delta=min_delta,
        )
        if not aligned_source_ids:
            aligned_records.append(record)
            continue

        merged_source_ids = tuple(
            dict.fromkeys((*aligned_source_ids, *source_ids))
        )[:safe_limit]
        if merged_source_ids != source_ids:
            changed += 1
            added += len(set(merged_source_ids).difference(source_ids))
            aligned_records.append(replace(record, source_ids=merged_source_ids))
        else:
            aligned_records.append(record)

    trace.update(
        {
            "records_seen": len(records),
            "records_changed": changed,
            "sources_added": added,
        }
    )
    return tuple(aligned_records), trace


def _source_alignment_candidates(
    source_ids: tuple[str, ...],
    *,
    store: RawEvidenceStore,
    window: int,
) -> tuple[Turn, ...]:
    selected: dict[str, Turn] = {}
    for source_id in source_ids:
        source_turn = store.get(source_id)
        if source_turn is None:
            continue
        session_turns = store.session_turns(source_turn.session_id)
        if not session_turns:
            continue
        positions = {
            turn.source_id: position for position, turn in enumerate(session_turns)
        }
        position = positions.get(source_turn.source_id)
        if position is None:
            continue
        start = max(0, position - window)
        end = min(len(session_turns), position + window + 1)
        for turn in session_turns[start:end]:
            selected[turn.source_id] = turn
    return tuple(selected.values())


def _rank_aligned_source_ids(
    record: Any,
    candidates: tuple[Turn, ...],
    *,
    original_source_ids: tuple[str, ...],
    min_score: float,
    min_delta: float,
) -> tuple[str, ...]:
    if not candidates:
        return ()
    record_text = _alignment_record_text(record)
    record_terms = _alignment_terms(record_text)
    record_numbers = set(re.findall(r"\b\d+(?:[.,]\d+)?\b", record_text.lower()))
    record_phrases = _alignment_phrases(record)
    scored = []
    for index, turn in enumerate(candidates):
        turn_text = turn.text.lower()
        turn_terms = _alignment_terms(turn.text)
        overlap = len(record_terms.intersection(turn_terms))
        number_overlap = sum(1 for number in record_numbers if number in turn_text)
        phrase_overlap = sum(1 for phrase in record_phrases if phrase in turn_text)
        score = overlap + number_overlap * 2.0 + phrase_overlap * 1.5
        if score < min_score:
            continue
        scored.append((score, index, turn.source_id))
    if not scored:
        return ()

    original_set = set(original_source_ids)
    best_original_score = max(
        (score for score, _, source_id in scored if source_id in original_set),
        default=0.0,
    )
    cutoff = max(min_score, best_original_score + max(0.0, min_delta))
    return tuple(
        source_id
        for score, _, source_id in sorted(scored, key=lambda item: (-item[0], item[1]))
        if source_id not in original_set and score >= cutoff
    )


def _alignment_record_text(record: Any) -> str:
    parts = [
        getattr(record, "text", ""),
        getattr(record, "subject", ""),
        getattr(record, "predicate", ""),
        getattr(record, "value", ""),
        " ".join(getattr(record, "entities", ()) or ()),
    ]
    return " ".join(part for part in parts if part)


def _alignment_terms(text: str) -> frozenset[str]:
    return frozenset(
        term
        for term in re.findall(r"[\w]+", text.lower())
        if len(term) > 2 and term not in _SOURCE_ALIGNMENT_STOPWORDS
    )


def _alignment_phrases(record: Any) -> tuple[str, ...]:
    phrases = []
    for value in (
        getattr(record, "value", ""),
        *(getattr(record, "entities", ()) or ()),
    ):
        cleaned = str(value).strip().lower()
        if len(cleaned) >= 4:
            phrases.append(cleaned)
    return tuple(dict.fromkeys(phrases))


def _validate_memory_record_source(value: str) -> str:
    if value not in {"retrieval", "evidence_rows", "retrieval_and_evidence_rows"}:
        raise ValueError(f"Unsupported compiler.memory_record_source: {value}")
    return value


def _compiler_memory_records(
    *,
    source: str,
    memory_hits: tuple[Any, ...],
    built_memory_records: tuple[Any, ...],
    evidence_turns: tuple[Any, ...],
) -> tuple[Any, ...]:
    """Select build memory records for compiler guidance.

    `retrieval` preserves the historical behavior: only typed memory records
    found by memory BM25 enter the compiler. `evidence_rows` links records to
    raw rows already selected for context, so typed memory acts as an index over
    visible evidence instead of adding independent facts.
    """

    _validate_memory_record_source(source)
    if source == "retrieval":
        return tuple(memory_hit.record for memory_hit in memory_hits)

    records: list[Any] = []
    if source == "retrieval_and_evidence_rows":
        records.extend(memory_hit.record for memory_hit in memory_hits)

    evidence_source_ids = {turn.source_id for turn in evidence_turns}
    for record in built_memory_records:
        if any(source_id in evidence_source_ids for source_id in record.source_ids):
            records.append(record)
    return _dedupe_memory_records(tuple(records))


def _dedupe_memory_records(records: tuple[Any, ...]) -> tuple[Any, ...]:
    result = []
    seen: set[str] = set()
    for record in records:
        memory_id = getattr(record, "memory_id", "")
        if memory_id in seen:
            continue
        seen.add(memory_id)
        result.append(record)
    return tuple(result)


def _route_feature_applies(
    route: RouteResult,
    question: str,
    enabled_signals: tuple[str, ...],
    enabled_information_needs: tuple[str, ...],
    enabled_query_patterns: tuple[str, ...],
) -> bool:
    if not enabled_signals and not enabled_information_needs and not enabled_query_patterns:
        return True
    if route.information_need in enabled_information_needs:
        return True
    if set(route.signals).intersection(enabled_signals):
        return True
    normalized = question.lower()
    return any(re.search(pattern, normalized) for pattern in enabled_query_patterns)


def _turn_window_bm25_applies(
    route: RouteResult,
    question: str,
    enabled_signals: tuple[str, ...],
    enabled_information_needs: tuple[str, ...],
    enabled_query_patterns: tuple[str, ...],
) -> bool:
    return _route_feature_applies(
        route=route,
        question=question,
        enabled_signals=enabled_signals,
        enabled_information_needs=enabled_information_needs,
        enabled_query_patterns=enabled_query_patterns,
    )


def _rerank_applies(
    *,
    route: RouteResult,
    enabled_information_needs: tuple[str, ...],
) -> bool:
    if not enabled_information_needs:
        return True
    return route.information_need in enabled_information_needs


def _disabled_rerank_trace(
    *,
    enabled: bool,
    information_needs: tuple[str, ...],
) -> dict[str, Any]:
    return {
        "enabled": enabled,
        "applied": False,
        "information_needs": information_needs,
        "candidate_count": 0,
        "returned_count": 0,
        "total_tokens": 0,
        "response": None,
    }


def _embedding_cache_stats(client: object) -> dict[str, int] | None:
    stats_method = getattr(client, "stats", None)
    if stats_method is None:
        return None
    return stats_method().to_dict()


def _answer_cache_stats(client: object) -> dict[str, int] | None:
    stats_method = getattr(client, "stats", None)
    if stats_method is None:
        return None
    return stats_method().to_dict()


def _embedding_cache_delta(
    before: dict[str, int] | None,
    after: dict[str, int] | None,
) -> dict[str, int] | None:
    if before is None or after is None:
        return None
    return {
        key: int(after.get(key, 0)) - int(before.get(key, 0))
        for key in sorted(after)
    }


def _answer_cache_delta(
    before: dict[str, int] | None,
    after: dict[str, int] | None,
) -> dict[str, int] | None:
    if before is None or after is None:
        return None
    return {
        key: int(after.get(key, 0)) - int(before.get(key, 0))
        for key in sorted(after)
    }


def _tuple_config(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    if isinstance(value, (list, tuple)):
        return tuple(str(item) for item in value)
    return (str(value),)


RETRIEVAL_ROUTE_OVERRIDE_KEYS = {
    "top_k",
    "max_top_k",
    "dense_top_k",
    "lexical_protect_top_n",
    "dense_protect_top_n",
}


def _validate_retrieval_route_overrides(
    route_overrides: Mapping[str, Mapping[str, Any]],
) -> dict[str, dict[str, int]]:
    normalized: dict[str, dict[str, int]] = {}
    for information_need, raw_overrides in route_overrides.items():
        if information_need not in SUPPORTED_INFORMATION_NEEDS:
            raise ValueError(
                f"Unsupported retrieval route override: {information_need}"
            )
        if not isinstance(raw_overrides, Mapping):
            raise ValueError(
                f"retrieval.route_overrides.{information_need} must be an object"
            )
        unknown_keys = set(raw_overrides).difference(RETRIEVAL_ROUTE_OVERRIDE_KEYS)
        if unknown_keys:
            keys = ", ".join(sorted(unknown_keys))
            raise ValueError(
                f"Unsupported retrieval.route_overrides.{information_need} keys: {keys}"
            )
        overrides: dict[str, int] = {}
        for key in RETRIEVAL_ROUTE_OVERRIDE_KEYS:
            if key in raw_overrides:
                overrides[key] = max(0, int(raw_overrides[key]))
        normalized[information_need] = overrides
    return normalized


def _answer_max_output_tokens(answer_config: Mapping[str, Any]) -> int:
    max_tokens = answer_config.get("max_tokens")
    max_output_tokens = answer_config.get("max_output_tokens")
    if max_tokens is not None and max_output_tokens is not None:
        if int(max_tokens) != int(max_output_tokens):
            raise ValueError(
                "answer.max_tokens and answer.max_output_tokens must match "
                f"when both are configured: {max_tokens} != {max_output_tokens}"
            )
        return int(max_tokens)
    if max_output_tokens is not None:
        return int(max_output_tokens)
    if max_tokens is not None:
        return int(max_tokens)
    return 256


def _answer_cache_namespace(
    answer_config: Mapping[str, Any],
    answer_mode: str,
) -> str:
    cache_config = answer_config.get("cache", {})
    namespace = cache_config.get("namespace")
    if namespace:
        return str(namespace)
    fields = {
        "mode": answer_mode,
        "base_url": answer_config.get("base_url", "http://127.0.0.1:8000/v1"),
        "model": answer_config.get("model", answer_mode),
        "temperature": answer_config.get("temperature", 0.0),
        "max_input_tokens": answer_config.get("max_input_tokens"),
        "max_output_tokens": _answer_max_output_tokens(answer_config),
        "output_format": answer_config.get("output_format", "text"),
    }
    return "answer:" + "|".join(f"{key}={fields[key]}" for key in sorted(fields))


def _repair_answer_config(
    answer_config: Mapping[str, Any],
    repair_config: Mapping[str, Any],
) -> dict[str, Any]:
    inherited_keys = (
        "base_url",
        "model",
        "temperature",
        "max_input_tokens",
        "max_output_tokens",
        "max_tokens",
        "timeout",
        "api_key_env",
        "output_format",
        "fallback_answer",
    )
    merged: dict[str, Any] = {
        key: answer_config[key] for key in inherited_keys if key in answer_config
    }
    for key in inherited_keys:
        if key in repair_config:
            merged[key] = repair_config[key]
    merged["cache"] = repair_config.get("cache", {})
    if "output_format" not in merged:
        merged["output_format"] = "json_answer"
    return merged


def _scoped_evidence_stage_config(
    *,
    answer_config: Mapping[str, Any],
    scoped_evidence_config: Mapping[str, Any],
    stage: str,
    output_format: str,
) -> dict[str, Any]:
    inherited_keys = (
        "mode",
        "base_url",
        "model",
        "temperature",
        "max_input_tokens",
        "max_output_tokens",
        "max_tokens",
        "timeout",
        "api_key_env",
        "fallback_answer",
    )
    merged: dict[str, Any] = {
        key: answer_config[key] for key in inherited_keys if key in answer_config
    }
    for key in inherited_keys:
        if key in scoped_evidence_config:
            merged[key] = scoped_evidence_config[key]

    stage_config = scoped_evidence_config.get(stage, {})
    if not isinstance(stage_config, Mapping):
        raise ValueError(f"scoped_evidence.{stage} must be an object")
    for key in (*inherited_keys, "output_format"):
        if key in stage_config:
            merged[key] = stage_config[key]
    merged["output_format"] = str(stage_config.get("output_format", output_format))
    if stage == "extractor":
        merged["cache"] = stage_config.get(
            "cache",
            scoped_evidence_config.get("cache", {}),
        )
    elif stage == "answer":
        merged["cache"] = stage_config.get(
            "cache",
            scoped_evidence_config.get("answer_cache", {}),
        )
    else:
        raise ValueError(f"Unsupported scoped_evidence stage: {stage}")
    return merged


def _configured_answerer(
    answer_config: Mapping[str, Any],
    *,
    answer_mode: str,
    cache_error_prefix: str = "",
) -> Any:
    if answer_mode == "openai_compatible":
        answerer: Any = OpenAICompatibleAnswerer(
            base_url=str(answer_config.get("base_url", "http://127.0.0.1:8000/v1")),
            model=str(answer_config["model"]),
            temperature=float(answer_config.get("temperature", 0.0)),
            max_tokens=_answer_max_output_tokens(answer_config),
            timeout=float(answer_config.get("timeout", 120.0)),
            max_input_tokens=_optional_int(answer_config.get("max_input_tokens")),
            api_key_env=answer_config.get("api_key_env"),
            output_format=str(answer_config.get("output_format", "text")),
        )
    elif answer_mode == "null_answerer":
        answerer = NullAnswerer(
            fallback_answer=str(
                answer_config.get(
                    "fallback_answer",
                    "I do not know based on the available evidence.",
                )
            )
        )
    else:
        raise ValueError(f"Unsupported answer mode: {answer_mode}")

    cache_config = answer_config.get("cache", {})
    if bool(cache_config.get("enabled", False)):
        cache_path = cache_config.get("path")
        if cache_path is None:
            prefix = f"{cache_error_prefix}." if cache_error_prefix else ""
            raise ValueError(f"{prefix}cache.path is required when cache is enabled")
        answerer = CachedAnswerer(
            answerer,
            cache_path=str(cache_path),
            namespace=_answer_cache_namespace(answer_config, answer_mode),
            output_format=str(answer_config.get("output_format", "text")),
        )
    return answerer


def _answerer_trace_config(answer_config: Mapping[str, Any]) -> dict[str, Any]:
    answer_mode = str(answer_config.get("mode", "null_answerer"))
    cache_config = answer_config.get("cache", {})
    return {
        "mode": answer_mode,
        "model": answer_config.get("model"),
        "base_url": answer_config.get("base_url"),
        "temperature": answer_config.get("temperature"),
        "max_input_tokens": answer_config.get("max_input_tokens"),
        "max_output_tokens": _answer_max_output_tokens(answer_config),
        "output_format": answer_config.get("output_format", "text"),
        "cache_enabled": bool(cache_config.get("enabled", False)),
        "cache_path": cache_config.get("path"),
        "cache_namespace": _answer_cache_namespace(answer_config, answer_mode),
    }


def _optional_int(value: object) -> int | None:
    if value is None:
        return None
    return int(value)


def _dense_query_text(question: str, question_time: str | None, *, mode: str) -> str:
    if mode == "question":
        return question
    if mode == "external_naive":
        if question_time:
            return f"Current Date: {question_time}\nQuestion: {question}"
        return question
    raise ValueError(f"Unsupported dense query_text_mode: {mode}")


def _retriever_name(
    lexical_enabled: bool,
    dense_enabled: bool,
    turn_window_bm25_enabled: bool,
    build_memory_enabled: bool,
    rerank_enabled: bool,
) -> str:
    names = []
    if lexical_enabled:
        names.append("lexical_bm25")
    if dense_enabled:
        names.append("dense_embedding" if not lexical_enabled else "dense_hybrid_rrf")
    if build_memory_enabled:
        names.append("build_memory_bm25")
    if turn_window_bm25_enabled:
        names.append("turn_window_bm25")
    if rerank_enabled:
        names.append("rerank")
    return "+".join(names) or "no_retriever"


def _merge_hit_lists(
    hit_lists: tuple[tuple[RetrievalHit, ...], ...],
    *,
    top_k: int,
    rrf_k: int,
) -> tuple[RetrievalHit, ...]:
    if not hit_lists:
        return ()
    if len(hit_lists) == 1:
        return hit_lists[0][:top_k]
    return reciprocal_rank_fusion(hit_lists, top_k=top_k, rrf_k=rrf_k)
