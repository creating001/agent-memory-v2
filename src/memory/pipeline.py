"""Stage-1 clean Agent-Memory pipeline."""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

from memory.answer import CachedAnswerer, NullAnswerer, OpenAICompatibleAnswerer
from memory.build import NullMemoryBuilder, OpenAICompatibleMemoryBuilder
from memory.compiler import EvidenceCompiler, SUPPORTED_INFORMATION_NEEDS
from memory.embeddings import CachedEmbeddingClient, OpenAICompatibleEmbeddingClient
from memory.finalize import AnswerFinalization, finalize_structured_answer
from memory.question_analysis import (
    CachedQuestionAnalyzer,
    OpenAICompatibleQuestionAnalyzer,
    route_from_question_analysis,
)
from memory.repair import maybe_repair_answer
from memory.retrieval import (
    BuildMemoryBM25Retriever,
    DenseEmbeddingRetriever,
    LexicalBM25Retriever,
    SessionBM25Retriever,
    SessionDocument,
    memory_hits_to_source_hits,
    prepend_protected_hits,
    reciprocal_rank_fusion,
)
from memory.route import QuestionRouter
from common.schemas import AnswerResult, PredictionRequest, RetrievalHit, RouteResult, TokenUsage
from memory.store import RawEvidenceStore


class Stage1Pipeline:
    """Minimal, clean, ablation-friendly memory pipeline."""

    def __init__(self, config: Mapping[str, Any]):
        self._config = dict(config)
        retrieval_config = self._config.get("retrieval", {})
        build_memory_config = self._config.get("build_memory", {})
        lexical_config = retrieval_config.get("lexical", {})
        dense_config = retrieval_config.get("dense", {})
        session_config = retrieval_config.get("session_bm25", {})
        route_config = self._config.get("route", {})
        question_analysis_config = self._config.get("question_analysis", {})
        compiler_config = self._config.get("compiler", {})
        answer_config = self._config.get("answer", {})
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
        self._question_analysis_enabled = bool(
            question_analysis_config.get("enabled", False)
        )
        self._question_analyzer = None
        self._question_analysis_trace_config = {
            "enabled": self._question_analysis_enabled,
            "mode": question_analysis_config.get("mode"),
            "model": question_analysis_config.get("model"),
            "base_url": question_analysis_config.get("base_url"),
            "temperature": question_analysis_config.get("temperature"),
            "max_tokens": question_analysis_config.get("max_tokens"),
            "cache_enabled": bool(
                question_analysis_config.get("cache", {}).get("enabled", False)
            ),
            "cache_path": question_analysis_config.get("cache", {}).get("path"),
            "cache_namespace": question_analysis_config.get("cache", {}).get(
                "namespace"
            ),
        }
        if self._question_analysis_enabled:
            analysis_mode = str(
                question_analysis_config.get("mode", "openai_compatible")
            )
            if analysis_mode != "openai_compatible":
                raise ValueError(
                    f"Unsupported question_analysis.mode: {analysis_mode}"
                )
            self._question_analyzer = OpenAICompatibleQuestionAnalyzer(
                base_url=str(
                    question_analysis_config.get(
                        "base_url",
                        "http://127.0.0.1:8000/v1",
                    )
                ),
                model=str(question_analysis_config["model"]),
                temperature=float(question_analysis_config.get("temperature", 0.0)),
                max_tokens=int(question_analysis_config.get("max_tokens", 512)),
                timeout=float(question_analysis_config.get("timeout", 120.0)),
                api_key_env=question_analysis_config.get("api_key_env"),
            )
            analysis_cache_config = question_analysis_config.get("cache", {})
            if bool(analysis_cache_config.get("enabled", False)):
                self._question_analyzer = CachedQuestionAnalyzer(
                    self._question_analyzer,
                    cache_path=str(analysis_cache_config["path"]),
                    namespace=str(
                        analysis_cache_config.get(
                            "namespace",
                            question_analysis_config.get("model", "unknown"),
                        )
                    ),
                )
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
        self._session_bm25_enabled = bool(session_config.get("enabled", False))
        self._session_bm25_top_k = int(session_config.get("top_k", 0))
        self._session_bm25_anchor_top_k = int(session_config.get("anchor_top_k", 1))
        self._session_bm25_max_anchor_hits = int(
            session_config.get(
                "max_anchor_hits",
                self._session_bm25_top_k * self._session_bm25_anchor_top_k,
            )
        )
        self._session_bm25_protect_turn_hits = int(
            session_config.get("protect_turn_hits", self._lexical_protect_top_n)
        )
        self._session_bm25_drop_query_stopwords = bool(
            session_config.get("drop_query_stopwords", self._drop_query_stopwords)
        )
        self._session_bm25_anchor_drop_query_stopwords = bool(
            session_config.get(
                "anchor_drop_query_stopwords",
                self._session_bm25_drop_query_stopwords,
            )
        )
        self._session_bm25_score_threshold = float(
            session_config.get("score_threshold", 0.0)
        )
        self._session_bm25_anchor_score_threshold = float(
            session_config.get("anchor_score_threshold", 0.0)
        )
        self._session_bm25_enabled_signals = _tuple_config(
            session_config.get("enabled_route_signals")
        )
        self._session_bm25_enabled_information_needs = _tuple_config(
            session_config.get("enabled_information_needs")
        )
        self._session_bm25_enabled_query_patterns = _tuple_config(
            session_config.get("enabled_query_patterns")
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
                cache_path=build_cache_path,
                cache_namespace=str(
                    build_cache_config.get(
                        "namespace",
                        build_memory_config.get("model", "unknown"),
                    )
                ),
                api_key_env=build_memory_config.get("api_key_env"),
                temporal_fields=bool(build_memory_config.get("temporal_fields", False)),
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
        if answer_mode == "openai_compatible":
            self._answerer = OpenAICompatibleAnswerer(
                base_url=str(answer_config.get("base_url", "http://127.0.0.1:8000/v1")),
                model=str(answer_config["model"]),
                temperature=float(answer_config.get("temperature", 0.0)),
                max_tokens=_answer_max_output_tokens(answer_config),
                timeout=float(answer_config.get("timeout", 120.0)),
                max_input_tokens=_optional_int(answer_config.get("max_input_tokens")),
                api_key_env=answer_config.get("api_key_env"),
                output_format=str(answer_config.get("output_format", "text")),
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
        if self._answer_cache_enabled:
            if self._answer_cache_path is None:
                raise ValueError("answer.cache.path is required when cache is enabled")
            self._answerer = CachedAnswerer(
                self._answerer,
                cache_path=str(self._answer_cache_path),
                namespace=self._answer_cache_namespace,
                output_format=str(answer_config.get("output_format", "text")),
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
            if self._answer_repair_mode == "openai_compatible":
                self._answer_repairer = OpenAICompatibleAnswerer(
                    base_url=str(
                        repair_answer_config.get(
                            "base_url", "http://127.0.0.1:8000/v1"
                        )
                    ),
                    model=str(repair_answer_config["model"]),
                    temperature=float(repair_answer_config.get("temperature", 0.0)),
                    max_tokens=_answer_max_output_tokens(repair_answer_config),
                    timeout=float(repair_answer_config.get("timeout", 120.0)),
                    max_input_tokens=_optional_int(
                        repair_answer_config.get("max_input_tokens")
                    ),
                    api_key_env=repair_answer_config.get("api_key_env"),
                    output_format=str(
                        repair_answer_config.get("output_format", "json_answer")
                    ),
                )
            elif self._answer_repair_mode == "null_answerer":
                self._answer_repairer = NullAnswerer(
                    fallback_answer=str(
                        repair_answer_config.get(
                            "fallback_answer",
                            "I do not know based on the available evidence.",
                        )
                    )
                )
            else:
                raise ValueError(
                    f"Unsupported answer.repair.mode: {self._answer_repair_mode}"
                )
            if self._answer_repair_cache_enabled:
                if self._answer_repair_cache_path is None:
                    raise ValueError(
                        "answer.repair.cache.path is required when cache is enabled"
                    )
                self._answer_repairer = CachedAnswerer(
                    self._answer_repairer,
                    cache_path=str(self._answer_repair_cache_path),
                    namespace=self._answer_repair_cache_namespace,
                    output_format=str(
                        repair_answer_config.get("output_format", "json_answer")
                    ),
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

    def predict(self, request: PredictionRequest) -> dict[str, Any]:
        store = RawEvidenceStore(request.turns)
        built_memory = self._memory_builder.build(store.turns)
        heuristic_route = self._router.route(request.question, request.question_time)
        route = heuristic_route
        question_analysis = None
        question_analysis_cache_before = _answer_cache_stats(self._question_analyzer)
        if self._question_analyzer is not None:
            question_analysis = self._question_analyzer.analyze(
                question=request.question,
                question_time=request.question_time,
            )
            route = route_from_question_analysis(question_analysis, heuristic_route)
        question_analysis_cache_after = _answer_cache_stats(self._question_analyzer)
        retrieval_settings = self._retrieval_settings_for_route(route)
        top_k = retrieval_settings["top_k"]
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
                top_k=top_k,
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
            hits = _merge_hit_lists(hit_lists, top_k=top_k, rrf_k=self._fusion_rrf_k)
            if lexical_protect_top_n > 0 and lexical_hits:
                hits = prepend_protected_hits(
                    lexical_hits[:lexical_protect_top_n],
                    hits,
                    top_k=top_k,
                )
            if dense_protect_top_n > 0 and dense_hits:
                hits = prepend_protected_hits(
                    dense_hits[:dense_protect_top_n],
                    hits,
                    top_k=top_k,
                )
        else:
            if memory_source_hits:
                hits = _merge_hit_lists(
                    tuple(hits for hits in (lexical_hits, memory_source_hits) if hits),
                    top_k=top_k,
                    rrf_k=self._fusion_rrf_k,
                )
            else:
                hits = lexical_hits
        embedding_cache_after = _embedding_cache_stats(self._embedding_client)
        turn_hits = hits
        session_hits = ()
        session_anchor_hits = ()
        session_bm25_applied = False
        if self._session_bm25_enabled and _session_bm25_applies(
            route=route,
            question=request.question,
            enabled_signals=self._session_bm25_enabled_signals,
            enabled_information_needs=self._session_bm25_enabled_information_needs,
            enabled_query_patterns=self._session_bm25_enabled_query_patterns,
        ):
            session_bm25_applied = True
            session_hits = self._retrieve_session_hits(store, request.question)
            session_anchor_hits = self._retrieve_session_anchor_hits(
                store,
                session_hits,
                request.question,
            )
            hits = _merge_turn_and_session_anchor_hits(
                turn_hits,
                session_anchor_hits,
                protect_turn_hits=self._session_bm25_protect_turn_hits,
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
                + (
                    question_analysis.token_usage.build_tokens
                    if question_analysis is not None
                    else 0
                )
            ),
            query_tokens=(
                answer.token_usage.query_tokens
                + (
                    question_analysis.token_usage.query_tokens
                    if question_analysis is not None
                    else 0
                )
            ),
        )
        return {
            "answer": answer.answer,
            "trace": {
                "store": store.manifest(),
                "build_memory": built_memory.to_dict(),
                "route": route.to_dict(),
                "heuristic_route": heuristic_route.to_dict(),
                "route_config": self._route_trace_config,
                "question_analysis": {
                    **self._question_analysis_trace_config,
                    "result": (
                        question_analysis.to_dict()
                        if question_analysis is not None
                        else None
                    ),
                    "route_changed": route.information_need
                    != heuristic_route.information_need,
                    "cache": _answer_cache_delta(
                        question_analysis_cache_before,
                        question_analysis_cache_after,
                    ),
                },
                "retrieval": {
                    "retriever": _retriever_name(
                        lexical_enabled=self._lexical_enabled,
                        dense_enabled=self._dense_enabled,
                        session_bm25_enabled=self._session_bm25_enabled,
                        build_memory_enabled=self._build_memory_enabled,
                    ),
                    "top_k": top_k,
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
                    "session_bm25_enabled": self._session_bm25_enabled,
                    "session_bm25_applied": session_bm25_applied,
                    "session_bm25_top_k": self._session_bm25_top_k
                    if session_bm25_applied
                    else None,
                    "session_anchor_top_k": self._session_bm25_anchor_top_k
                    if session_bm25_applied
                    else None,
                    "session_max_anchor_hits": self._session_bm25_max_anchor_hits
                    if session_bm25_applied
                    else None,
                    "session_protect_turn_hits": self._session_bm25_protect_turn_hits
                    if session_bm25_applied
                    else None,
                    "session_drop_query_stopwords": self._session_bm25_drop_query_stopwords
                    if session_bm25_applied
                    else None,
                    "session_anchor_drop_query_stopwords": (
                        self._session_bm25_anchor_drop_query_stopwords
                        if session_bm25_applied
                        else None
                    ),
                    "session_enabled_route_signals": self._session_bm25_enabled_signals,
                    "session_enabled_information_needs": (
                        self._session_bm25_enabled_information_needs
                    ),
                    "session_enabled_query_patterns": (
                        self._session_bm25_enabled_query_patterns
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
                    "turn_hits": [hit.to_dict() for hit in turn_hits],
                    "session_hits": [hit.to_dict() for hit in session_hits],
                    "session_anchor_hits": [
                        hit.to_dict() for hit in session_anchor_hits
                    ],
                    "hits": [hit.to_dict() for hit in hits],
                },
                "compiled_context": compiled.to_dict(),
                "compiler": self._compiler_trace_config,
                "answer_cache": _answer_cache_delta(
                    answer_cache_before,
                    answer_cache_after,
                ),
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
        return {
            "top_k": top_k,
            "dense_top_k": settings["dense_top_k"],
            "lexical_protect_top_n": settings["lexical_protect_top_n"],
            "dense_protect_top_n": settings["dense_protect_top_n"],
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

    def _retrieve_session_hits(
        self,
        store: RawEvidenceStore,
        question: str,
    ) -> tuple[RetrievalHit, ...]:
        if self._session_bm25_top_k <= 0:
            return ()
        documents = _session_documents(store)
        if not documents:
            return ()
        return SessionBM25Retriever(
            documents,
            drop_query_stopwords=self._session_bm25_drop_query_stopwords,
        ).retrieve(
            question,
            top_k=self._session_bm25_top_k,
            score_threshold=self._session_bm25_score_threshold,
        )

    def _retrieve_session_anchor_hits(
        self,
        store: RawEvidenceStore,
        session_hits: tuple[RetrievalHit, ...],
        question: str,
    ) -> tuple[RetrievalHit, ...]:
        if (
            self._session_bm25_anchor_top_k <= 0
            or self._session_bm25_max_anchor_hits <= 0
        ):
            return ()

        anchors: list[RetrievalHit] = []
        seen_source_ids: set[str] = set()
        for session_hit in session_hits:
            session_turns = store.session_turns(session_hit.source_id)
            local_hits = LexicalBM25Retriever(
                session_turns,
                drop_query_stopwords=self._session_bm25_anchor_drop_query_stopwords,
            ).retrieve(
                question,
                top_k=self._session_bm25_anchor_top_k,
                score_threshold=self._session_bm25_anchor_score_threshold,
            )
            for local_hit in local_hits:
                if local_hit.source_id in seen_source_ids:
                    continue
                seen_source_ids.add(local_hit.source_id)
                anchors.append(
                    _session_anchor_hit(
                        session_hit=session_hit,
                        local_hit=local_hit,
                        rank=len(anchors) + 1,
                    )
                )
                if len(anchors) >= self._session_bm25_max_anchor_hits:
                    return tuple(anchors)
        return tuple(anchors)


def _session_documents(store: RawEvidenceStore) -> tuple[SessionDocument, ...]:
    documents = []
    for session_id, turns in store.sessions():
        lines = []
        for turn in turns:
            prefix = " ".join(
                part for part in (turn.timestamp, turn.role) if part is not None
            )
            lines.append(f"{prefix}: {turn.text}" if prefix else turn.text)
        documents.append(
            SessionDocument(
                session_id=session_id,
                text="\n".join(lines),
                turn_count=len(turns),
            )
        )
    return tuple(documents)


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


def _session_anchor_hit(
    session_hit: RetrievalHit,
    local_hit: RetrievalHit,
    rank: int,
) -> RetrievalHit:
    matched_terms = tuple(
        dict.fromkeys((*session_hit.matched_terms, *local_hit.matched_terms))
    )
    return RetrievalHit(
        source_id=local_hit.source_id,
        score=session_hit.score + local_hit.score,
        rank=rank,
        retriever="session_bm25+anchor_bm25",
        matched_terms=matched_terms,
    )


def _merge_turn_and_session_anchor_hits(
    turn_hits: tuple[RetrievalHit, ...],
    session_anchor_hits: tuple[RetrievalHit, ...],
    protect_turn_hits: int,
) -> tuple[RetrievalHit, ...]:
    selected: list[RetrievalHit] = []
    seen_source_ids: set[str] = set()

    def append(hit: RetrievalHit) -> None:
        if hit.source_id in seen_source_ids:
            return
        seen_source_ids.add(hit.source_id)
        selected.append(hit)

    protected_count = max(0, protect_turn_hits)
    for hit in turn_hits[:protected_count]:
        append(hit)
    for hit in session_anchor_hits:
        append(hit)
    for hit in turn_hits[protected_count:]:
        append(hit)

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


def _session_bm25_applies(
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
    session_bm25_enabled: bool,
    build_memory_enabled: bool,
) -> str:
    names = []
    if lexical_enabled:
        names.append("lexical_bm25")
    if dense_enabled:
        names.append("dense_embedding" if not lexical_enabled else "dense_hybrid_rrf")
    if build_memory_enabled:
        names.append("build_memory_bm25")
    if session_bm25_enabled:
        names.append("session_bm25")
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
