"""Stage-1 clean Agent-Memory pipeline."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from dataclasses import replace
from typing import Any

from memory.answer import CachedAnswerer, NullAnswerer, OpenAICompatibleAnswerer
from memory.build import NullMemoryBuilder, OpenAICompatibleMemoryBuilder
from memory.compiler import EvidenceCompiler, SUPPORTED_INFORMATION_NEEDS
from memory.embeddings import CachedEmbeddingClient, OpenAICompatibleEmbeddingClient
from memory.finalize import (
    AnswerFinalization,
    finalize_structured_answer,
    guard_source_grounded_answer,
)
from memory.repair import maybe_repair_answer
from memory.rerank import (
    OpenAICompatibleRerankClient,
    format_rerank_evidence_document,
    format_rerank_turn_document,
    rerank_hits_filter_preserve_order,
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
from common.schemas import (
    AnswerResult,
    CompiledContext,
    PredictionRequest,
    RetrievalHit,
    RouteResult,
    TokenUsage,
)
from memory.store import RawEvidenceStore


_LIFECYCLE_MEMORY_TYPES = frozenset(
    {"fact", "preference", "profile", "relationship", "state"}
)
_STATE_UPDATE_MEMORY_TYPES = frozenset(
    {"preference", "profile", "relationship", "state"}
)
_LIFECYCLE_TERM_PATTERN = re.compile(r"[A-Za-z0-9_]+")
_LIFECYCLE_TERM_STOPWORDS = frozenset(
    {
        "about",
        "after",
        "again",
        "been",
        "before",
        "current",
        "currently",
        "does",
        "have",
        "latest",
        "most",
        "recent",
        "still",
        "that",
        "the",
        "their",
        "there",
        "this",
        "what",
        "when",
        "where",
        "which",
        "with",
        "your",
    }
)


class Stage1Pipeline:
    """Minimal, clean, ablation-friendly memory pipeline."""

    def __init__(self, config: Mapping[str, Any]):
        self._config = dict(config)
        retrieval_config = self._config.get("retrieval", {})
        build_memory_config = self._config.get("build_memory", {})
        lexical_config = retrieval_config.get("lexical", {})
        dense_config = retrieval_config.get("dense", {})
        turn_window_config = retrieval_config.get("turn_window_bm25", {})
        selected_context_config = retrieval_config.get("selected_context", {})
        selected_context_audit_config = selected_context_config.get("risk_audit", {})
        if not isinstance(selected_context_audit_config, Mapping):
            raise ValueError("retrieval.selected_context.risk_audit must be an object")
        granularity_profile_audit_config = retrieval_config.get(
            "granularity_profile_audit", {}
        )
        if not isinstance(granularity_profile_audit_config, Mapping):
            raise ValueError("retrieval.granularity_profile_audit must be an object")
        context_budget_config = retrieval_config.get("context_budget", {})
        if not isinstance(context_budget_config, Mapping):
            raise ValueError("retrieval.context_budget must be an object")
        context_budget_audit_config = retrieval_config.get("context_budget_audit", {})
        if not isinstance(context_budget_audit_config, Mapping):
            raise ValueError("retrieval.context_budget_audit must be an object")
        memory_slot_chain_config = retrieval_config.get("memory_slot_chain", {})
        if not isinstance(memory_slot_chain_config, Mapping):
            raise ValueError("retrieval.memory_slot_chain must be an object")
        object_slot_activation_config = retrieval_config.get(
            "object_slot_activation", {}
        )
        if not isinstance(object_slot_activation_config, Mapping):
            raise ValueError("retrieval.object_slot_activation must be an object")
        rerank_config = retrieval_config.get("rerank", {})
        route_config = self._config.get("route", {})
        if self._config.get("question_analysis", {}).get("enabled", False):
            raise ValueError("question_analysis is retired; use heuristic route")
        compiler_config = self._config.get("compiler", {})
        compiler_context_pressure_config = compiler_config.get(
            "context_pressure", {}
        )
        if not isinstance(compiler_context_pressure_config, Mapping):
            raise ValueError("compiler.context_pressure must be an object")
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
        self._base_top_k = int(retrieval_config.get("top_k", 8))
        self._max_top_k = int(retrieval_config.get("max_top_k", self._base_top_k))
        self._retrieval_route_overrides = _validate_retrieval_route_overrides(
            retrieval_config.get("route_overrides") or {}
        )
        self._retrieval_route_override_precedence = str(
            retrieval_config.get("route_override_precedence", "after_profile")
        )
        if self._retrieval_route_override_precedence not in {
            "after_profile",
            "before_profile",
        }:
            raise ValueError(
                "retrieval.route_override_precedence must be "
                "'after_profile' or 'before_profile'"
            )
        self._granularity_profiles = _validate_granularity_profiles(
            retrieval_config.get("granularity_profiles") or ()
        )
        self._granularity_profile_audit_enabled = bool(
            granularity_profile_audit_config.get("enabled", False)
        )
        self._granularity_routers = {
            profile["name"]: _configured_router(
                _merged_config(route_config, profile["route"])
            )
            for profile in self._granularity_profiles
            if profile.get("route")
        }
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
        self._build_memory_source_alignment_require_assistant_answer_source = bool(
            source_alignment_config.get("require_assistant_answer_source", False)
        )
        self._build_memory_source_alignment_memory_types = _tuple_config(
            source_alignment_config.get("memory_types")
        )
        self._build_memory_source_alignment_source_order = str(
            source_alignment_config.get("source_order", "prepend")
        )
        if self._build_memory_source_alignment_source_order not in {
            "prepend",
            "append",
        }:
            raise ValueError(
                "build_memory.source_alignment.source_order must be "
                "prepend or append"
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
            "chat_template_kwargs": build_memory_config.get("chat_template_kwargs"),
            "temporal_fields": bool(build_memory_config.get("temporal_fields", False)),
            "prompt_profile": str(
                build_memory_config.get("prompt_profile", "typed_compact")
            ),
            "manage_facts": bool(build_memory_config.get("manage_facts", True)),
            "management_policy": build_memory_config.get("management_policy"),
            "source_alignment": {
                "enabled": self._build_memory_source_alignment_enabled,
                "window": self._build_memory_source_alignment_window,
                "max_sources_per_record": (
                    self._build_memory_source_alignment_max_sources
                ),
                "min_score": self._build_memory_source_alignment_min_score,
                "min_delta": self._build_memory_source_alignment_min_delta,
                "require_assistant_answer_source": (
                    self._build_memory_source_alignment_require_assistant_answer_source
                ),
                "memory_types": self._build_memory_source_alignment_memory_types,
                "source_order": self._build_memory_source_alignment_source_order,
            },
        }
        self._memory_slot_chain_enabled = bool(
            memory_slot_chain_config.get("enabled", False)
        )
        self._memory_slot_chain_information_needs = _tuple_config(
            memory_slot_chain_config.get(
                "information_needs",
                ("current_state", "profile_preference"),
            )
        )
        self._memory_slot_chain_max_chains = int(
            memory_slot_chain_config.get("max_chains", 4)
        )
        self._memory_slot_chain_max_sources_per_chain = int(
            memory_slot_chain_config.get("max_sources_per_chain", 6)
        )
        self._memory_slot_chain_memory_types = _tuple_config(
            memory_slot_chain_config.get(
                "memory_types",
                ("preference", "profile", "relationship", "state"),
            )
        )
        self._memory_slot_chain_question_scope_gate = bool(
            memory_slot_chain_config.get("question_scope_gate", False)
        )
        self._memory_slot_chain_source_policy = str(
            memory_slot_chain_config.get("source_policy", "all")
        )
        if self._memory_slot_chain_source_policy not in {"all", "query_scope"}:
            raise ValueError(
                "retrieval.memory_slot_chain.source_policy must be all or query_scope"
            )
        self._object_slot_activation_enabled = bool(
            object_slot_activation_config.get("enabled", False)
        )
        self._object_slot_activation_information_needs = _tuple_config(
            object_slot_activation_config.get("information_needs", ("list_count",))
        )
        self._object_slot_activation_memory_types = _tuple_config(
            object_slot_activation_config.get(
                "memory_types",
                (
                    "event",
                    "fact",
                    "plan",
                    "preference",
                    "profile",
                    "relationship",
                    "state",
                ),
            )
        )
        self._object_slot_activation_max_slots = int(
            object_slot_activation_config.get("max_slots", 3)
        )
        self._object_slot_activation_max_sources_per_slot = int(
            object_slot_activation_config.get("max_sources_per_slot", 8)
        )
        self._object_slot_activation_min_overlap_terms = int(
            object_slot_activation_config.get("min_overlap_terms", 1)
        )
        self._object_slot_activation_require_collection_slot = bool(
            object_slot_activation_config.get("require_collection_slot", True)
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
        self._selected_context_enabled = bool(
            selected_context_config.get("enabled", False)
        )
        self._selected_context_window_before = int(
            selected_context_config.get("window_before", 1)
        )
        self._selected_context_window_after = int(
            selected_context_config.get("window_after", 1)
        )
        self._selected_context_max_rows = int(
            selected_context_config.get("max_rows", 0)
        )
        self._selected_context_max_neighbor_chars = int(
            selected_context_config.get("max_neighbor_chars", 180)
        )
        self._selected_context_max_center_chars = int(
            selected_context_config.get("max_center_chars", 0)
        )
        self._selected_context_context_format = _selected_context_context_format(
            selected_context_config.get("context_format", "verbose")
        )
        self._selected_context_timestamp_policy = _selected_context_timestamp_policy(
            selected_context_config.get("timestamp_policy", "all")
        )
        self._selected_context_require_anaphora = bool(
            selected_context_config.get("require_anaphora", True)
        )
        self._selected_context_require_question_reference = bool(
            selected_context_config.get("require_question_reference", False)
        )
        self._selected_context_require_question_reference_min_center_chars = int(
            selected_context_config.get(
                "require_question_reference_min_center_chars", 0
            )
        )
        self._selected_context_require_source_grounded_self_reference = bool(
            selected_context_config.get(
                "require_source_grounded_self_reference", False
            )
        )
        self._selected_context_source_grounded_min_terms = int(
            selected_context_config.get("source_grounded_min_terms", 0)
        )
        self._selected_context_source_grounded_min_coverage = float(
            selected_context_config.get("source_grounded_min_coverage", 0.0)
        )
        self._selected_context_require_materialized_source_grounded = bool(
            selected_context_config.get("require_materialized_source_grounded", False)
        )
        self._selected_context_materialized_source_grounded_min_terms = int(
            selected_context_config.get(
                "materialized_source_grounded_min_terms",
                self._selected_context_source_grounded_min_terms,
            )
        )
        self._selected_context_materialized_source_grounded_min_coverage = float(
            selected_context_config.get(
                "materialized_source_grounded_min_coverage",
                self._selected_context_source_grounded_min_coverage,
            )
        )
        self._selected_context_min_context_budget_headroom_chars = int(
            selected_context_config.get("min_context_budget_headroom_chars", 0)
        )
        self._selected_context_information_needs = _tuple_config(
            selected_context_config.get("information_needs")
        )
        self._selected_context_route_overrides = (
            _validate_selected_context_route_overrides(
                selected_context_config.get("route_overrides") or {}
            )
        )
        self._selected_context_risk_audit_enabled = bool(
            selected_context_audit_config.get("enabled", False)
        )
        self._selected_context_risk_audit_information_needs = _tuple_config(
            selected_context_audit_config.get("information_needs")
        )
        self._selected_context_risk_audit_source_grounded_min_terms = int(
            selected_context_audit_config.get("source_grounded_min_terms", 2)
        )
        self._selected_context_risk_audit_source_grounded_min_coverage = float(
            selected_context_audit_config.get("source_grounded_min_coverage", 0.6)
        )
        self._selected_context_trace_config = {
            "enabled": self._selected_context_enabled,
            "window_before": self._selected_context_window_before,
            "window_after": self._selected_context_window_after,
            "max_rows": self._selected_context_max_rows,
            "max_neighbor_chars": self._selected_context_max_neighbor_chars,
            "max_center_chars": self._selected_context_max_center_chars,
            "context_format": self._selected_context_context_format,
            "timestamp_policy": self._selected_context_timestamp_policy,
            "require_anaphora": self._selected_context_require_anaphora,
            "require_question_reference": (
                self._selected_context_require_question_reference
            ),
            "require_question_reference_min_center_chars": (
                self._selected_context_require_question_reference_min_center_chars
            ),
            "require_source_grounded_self_reference": (
                self._selected_context_require_source_grounded_self_reference
            ),
            "source_grounded_min_terms": (
                self._selected_context_source_grounded_min_terms
            ),
            "source_grounded_min_coverage": (
                self._selected_context_source_grounded_min_coverage
            ),
            "require_materialized_source_grounded": (
                self._selected_context_require_materialized_source_grounded
            ),
            "materialized_source_grounded_min_terms": (
                self._selected_context_materialized_source_grounded_min_terms
            ),
            "materialized_source_grounded_min_coverage": (
                self._selected_context_materialized_source_grounded_min_coverage
            ),
            "min_context_budget_headroom_chars": (
                self._selected_context_min_context_budget_headroom_chars
            ),
            "information_needs": self._selected_context_information_needs,
            "route_overrides": self._selected_context_route_overrides,
            "risk_audit": {
                "enabled": self._selected_context_risk_audit_enabled,
                "information_needs": (
                    self._selected_context_risk_audit_information_needs
                ),
                "source_grounded_min_terms": (
                    self._selected_context_risk_audit_source_grounded_min_terms
                ),
                "source_grounded_min_coverage": (
                    self._selected_context_risk_audit_source_grounded_min_coverage
                ),
                "trace_only": True,
            },
        }
        self._context_budget_enabled = bool(
            context_budget_config.get("enabled", False)
        )
        self._context_budget_max_chars = int(
            context_budget_config.get("max_chars", 0)
        )
        self._context_budget_min_hits = int(
            context_budget_config.get("min_hits", 0)
        )
        self._context_budget_protect_top_n = int(
            context_budget_config.get("protect_top_n", 0)
        )
        self._context_budget_max_hits = int(
            context_budget_config.get("max_hits", 0)
        )
        self._context_budget_information_needs = _tuple_config(
            context_budget_config.get("information_needs")
        )
        self._context_budget_audit_enabled = bool(
            context_budget_audit_config.get("enabled", False)
        )
        self._context_budget_audit_max_chars = int(
            context_budget_audit_config.get("max_chars", 0)
        )
        self._context_budget_audit_min_hits = int(
            context_budget_audit_config.get("min_hits", 0)
        )
        self._context_budget_audit_protect_top_n = int(
            context_budget_audit_config.get("protect_top_n", 0)
        )
        self._context_budget_audit_max_hits = int(
            context_budget_audit_config.get("max_hits", 0)
        )
        self._context_budget_audit_information_needs = _tuple_config(
            context_budget_audit_config.get("information_needs")
        )
        self._rerank_enabled = bool(rerank_config.get("enabled", False))
        self._rerank_model = rerank_config.get("model")
        self._rerank_base_url = rerank_config.get("base_url")
        self._rerank_pool_k = int(rerank_config.get("pool_k", self._base_top_k))
        self._rerank_min_effective_top_k = int(
            rerank_config.get("min_effective_top_k", 0)
        )
        self._rerank_return_top_k = max(
            0, int(rerank_config.get("return_top_k", 0))
        )
        self._rerank_batch_size = int(rerank_config.get("batch_size", 0))
        self._rerank_timeout = float(rerank_config.get("timeout", 120.0))
        self._rerank_document_max_chars = int(
            rerank_config.get("document_max_chars", 0)
        )
        self._rerank_document_text_mode = str(
            rerank_config.get("document_text_mode", "turn")
        )
        if self._rerank_document_text_mode not in {
            "turn",
            "turn_with_neighbors",
            "turn_with_neighbors_and_memory",
        }:
            raise ValueError(
                "Unsupported retrieval.rerank.document_text_mode: "
                f"{self._rerank_document_text_mode}"
            )
        self._rerank_document_neighbor_window = int(
            rerank_config.get("document_neighbor_window", 1)
        )
        self._rerank_document_neighbor_max_chars = int(
            rerank_config.get("document_neighbor_max_chars", 240)
        )
        self._rerank_document_max_memory_records = int(
            rerank_config.get("document_max_memory_records", 3)
        )
        self._rerank_document_memory_max_chars = int(
            rerank_config.get("document_memory_max_chars", 220)
        )
        self._rerank_anchor_keep = int(rerank_config.get("anchor_keep", 0))
        self._rerank_anchor_after_top = int(
            rerank_config.get("anchor_after_top", 0)
        )
        self._rerank_selection_mode = str(
            rerank_config.get("selection_mode", "reorder")
        )
        if self._rerank_selection_mode not in {
            "reorder",
            "filter_preserve_order",
        }:
            raise ValueError(
                "Unsupported retrieval.rerank.selection_mode: "
                f"{self._rerank_selection_mode}"
            )
        self._rerank_query_text_mode = str(
            rerank_config.get("query_text_mode", "external_naive")
        )
        self._rerank_information_needs = _tuple_config(
            rerank_config.get("information_needs")
        )
        rerank_exchange_guard_config = rerank_config.get("exchange_guard", {})
        if not isinstance(rerank_exchange_guard_config, Mapping):
            raise ValueError("retrieval.rerank.exchange_guard must be an object")
        self._rerank_exchange_guard_enabled = bool(
            rerank_exchange_guard_config.get("enabled", False)
        )
        self._rerank_exchange_guard_protect_memory_sources = bool(
            rerank_exchange_guard_config.get("protect_memory_sources", True)
        )
        self._rerank_exchange_guard_protect_adjacent_session = bool(
            rerank_exchange_guard_config.get("protect_adjacent_session", True)
        )
        self._rerank_exchange_guard_question_overlap_min_terms = max(
            0,
            int(
                rerank_exchange_guard_config.get(
                    "protect_question_overlap_min_terms",
                    0,
                )
            ),
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
                management_policy=build_memory_config.get("management_policy"),
                chat_template_kwargs=_dict_config(
                    build_memory_config.get("chat_template_kwargs")
                ),
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
            event_timeline=bool(compiler_config.get("event_timeline", False)),
            event_timeline_information_needs=_tuple_config(
                compiler_config.get(
                    "event_timeline_information_needs",
                    ("current_state", "list_count", "temporal_lookup"),
                )
            ),
            event_timeline_max_rows=int(
                compiler_config.get("event_timeline_max_rows", 12)
            ),
            event_timeline_snippet_chars=int(
                compiler_config.get("event_timeline_snippet_chars", 180)
            ),
            event_time_candidate_manifest=bool(
                compiler_config.get("event_time_candidate_manifest", False)
            ),
            event_time_candidate_manifest_information_needs=_tuple_config(
                compiler_config.get(
                    "event_time_candidate_manifest_information_needs",
                    ("current_state", "list_count", "temporal_lookup"),
                )
            ),
            event_time_candidate_manifest_max_rows=int(
                compiler_config.get("event_time_candidate_manifest_max_rows", 12)
            ),
            event_time_candidate_manifest_snippet_chars=int(
                compiler_config.get("event_time_candidate_manifest_snippet_chars", 160)
            ),
            event_time_candidate_manifest_question_gate=bool(
                compiler_config.get("event_time_candidate_manifest_question_gate", True)
            ),
            event_time_candidate_manifest_grouped_view=bool(
                compiler_config.get(
                    "event_time_candidate_manifest_grouped_view", False
                )
            ),
            event_time_candidate_manifest_max_groups=int(
                compiler_config.get("event_time_candidate_manifest_max_groups", 8)
            ),
            event_time_candidate_map=bool(
                compiler_config.get("event_time_candidate_map", False)
            ),
            event_time_candidate_map_information_needs=_tuple_config(
                compiler_config.get(
                    "event_time_candidate_map_information_needs",
                    ("temporal_lookup",),
                )
            ),
            event_time_candidate_map_max_groups=int(
                compiler_config.get("event_time_candidate_map_max_groups", 1)
            ),
            event_time_candidate_map_snippet_chars=int(
                compiler_config.get("event_time_candidate_map_snippet_chars", 140)
            ),
            event_time_candidate_map_min_terms=int(
                compiler_config.get("event_time_candidate_map_min_terms", 2)
            ),
            event_time_candidate_map_min_coverage=float(
                compiler_config.get("event_time_candidate_map_min_coverage", 0.6)
            ),
            event_time_candidate_map_allowed_time_kinds=_tuple_config(
                compiler_config.get(
                    "event_time_candidate_map_allowed_time_kinds",
                    ("exact_today", "explicit_date", "relative_phrase"),
                )
            ),
            event_time_candidate_map_strip_context_wrappers=bool(
                compiler_config.get(
                    "event_time_candidate_map_strip_context_wrappers", False
                )
            ),
            event_time_candidate_map_segment_local_context=bool(
                compiler_config.get(
                    "event_time_candidate_map_segment_local_context", False
                )
            ),
            event_time_candidate_map_rank_by_coverage=bool(
                compiler_config.get("event_time_candidate_map_rank_by_coverage", False)
            ),
            event_time_candidate_map_normalize_terms=bool(
                compiler_config.get("event_time_candidate_map_normalize_terms", False)
            ),
            event_time_candidate_map_exact_today_min_coverage=(
                None
                if compiler_config.get(
                    "event_time_candidate_map_exact_today_min_coverage"
                )
                is None
                else float(
                    compiler_config.get(
                        "event_time_candidate_map_exact_today_min_coverage"
                    )
                )
            ),
            event_time_candidate_map_require_role_match=bool(
                compiler_config.get("event_time_candidate_map_require_role_match", False)
            ),
            event_time_candidate_map_allow_time_of_day_questions=bool(
                compiler_config.get(
                    "event_time_candidate_map_allow_time_of_day_questions", True
                )
            ),
            event_time_candidate_map_audit=bool(
                compiler_config.get("event_time_candidate_map_audit", False)
            ),
            event_time_candidate_map_temporal_ambiguity_contract=bool(
                compiler_config.get(
                    "event_time_candidate_map_temporal_ambiguity_contract", False
                )
            ),
            event_time_candidate_map_include_mention_time=bool(
                compiler_config.get(
                    "event_time_candidate_map_include_mention_time", False
                )
            ),
            event_time_candidate_map_mention_time_fallback=bool(
                compiler_config.get(
                    "event_time_candidate_map_mention_time_fallback", False
                )
            ),
            event_time_candidate_map_mention_time_fallback_min_coverage=float(
                compiler_config.get(
                    "event_time_candidate_map_mention_time_fallback_min_coverage",
                    0.8,
                )
            ),
            event_time_candidate_map_mention_time_fallback_trigger_max_coverage=float(
                compiler_config.get(
                    "event_time_candidate_map_mention_time_fallback_trigger_max_coverage",
                    0.8,
                )
            ),
            enable_weekend_relative_time=bool(
                compiler_config.get("enable_weekend_relative_time", False)
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
            structured_guide_memory_hints=bool(
                compiler_config.get("structured_guide_memory_hints", False)
            ),
            structured_guide_max_memory_hints_per_row=int(
                compiler_config.get("structured_guide_max_memory_hints_per_row", 1)
            ),
            structured_guide_memory_hint_chars=int(
                compiler_config.get("structured_guide_memory_hint_chars", 70)
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
            candidate_guide_include_memory_hints=bool(
                compiler_config.get("candidate_guide_include_memory_hints", False)
            ),
            candidate_guide_max_memory_hints=int(
                compiler_config.get("candidate_guide_max_memory_hints", 2)
            ),
            candidate_guide_memory_hint_chars=int(
                compiler_config.get("candidate_guide_memory_hint_chars", 120)
            ),
            update_conflict_guide=bool(
                compiler_config.get("update_conflict_guide", False)
            ),
            update_conflict_guide_information_needs=_tuple_config(
                compiler_config.get(
                    "update_conflict_guide_information_needs",
                    ("current_state", "fact_lookup", "list_count", "temporal_lookup"),
                )
            ),
            update_conflict_guide_max_rows=int(
                compiler_config.get("update_conflict_guide_max_rows", 6)
            ),
            update_conflict_guide_snippet_chars=int(
                compiler_config.get("update_conflict_guide_snippet_chars", 180)
            ),
            memory_state_guide=bool(
                compiler_config.get("memory_state_guide", False)
            ),
            memory_state_guide_information_needs=_tuple_config(
                compiler_config.get(
                    "memory_state_guide_information_needs",
                    ("current_state", "fact_lookup", "profile_preference"),
                )
            ),
            memory_state_guide_max_records=int(
                compiler_config.get("memory_state_guide_max_records", 8)
            ),
            memory_state_guide_candidate_records=int(
                compiler_config.get("memory_state_guide_candidate_records", 12)
            ),
            memory_state_guide_value_chars=int(
                compiler_config.get("memory_state_guide_value_chars", 120)
            ),
            memory_state_guide_include_superseded=bool(
                compiler_config.get("memory_state_guide_include_superseded", True)
            ),
            memory_state_guide_require_conflict=bool(
                compiler_config.get("memory_state_guide_require_conflict", False)
            ),
            memory_state_guide_require_active_superseded_pair=bool(
                compiler_config.get(
                    "memory_state_guide_require_active_superseded_pair", False
                )
            ),
            memory_state_guide_require_slot_overlap=bool(
                compiler_config.get("memory_state_guide_require_slot_overlap", False)
            ),
            memory_state_guide_require_stateful_slot=bool(
                compiler_config.get("memory_state_guide_require_stateful_slot", False)
            ),
            profile_activation_guide=bool(
                compiler_config.get("profile_activation_guide", False)
            ),
            profile_activation_guide_information_needs=_tuple_config(
                compiler_config.get(
                    "profile_activation_guide_information_needs",
                    ("profile_preference",),
                )
            ),
            profile_activation_guide_max_records=int(
                compiler_config.get("profile_activation_guide_max_records", 4)
            ),
            profile_activation_guide_value_chars=int(
                compiler_config.get("profile_activation_guide_value_chars", 160)
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
            personalized_advice_contract=bool(
                compiler_config.get("personalized_advice_contract", False)
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
            tail_row_text_mode=str(
                compiler_config.get("tail_row_text_mode", "full")
            ),
            tail_row_text_after_rank=int(
                compiler_config.get("tail_row_text_after_rank", 0)
            ),
            tail_max_row_text_chars=int(
                compiler_config.get("tail_max_row_text_chars", 0)
            ),
            route_guidance=bool(compiler_config.get("route_guidance", False)),
            evidence_row_labels=bool(
                compiler_config.get("evidence_row_labels", False)
            ),
            final_answer_checklist=bool(
                compiler_config.get("final_answer_checklist", False)
            ),
            max_memory_records=int(compiler_config.get("max_memory_records", 12)),
            memory_context_newlines_after_blocks=int(
                compiler_config.get("memory_context_newlines_after_blocks", 3)
            ),
            prompt_mode=str(compiler_config.get("prompt_mode", "default")),
            route_overrides=compiler_config.get("route_overrides") or {},
        )
        self._compiler_memory_record_source = _validate_memory_record_source(
            str(compiler_config.get("memory_record_source", "retrieval"))
        )
        self._compiler_memory_state_guide_record_source = _validate_memory_record_source(
            str(
                compiler_config.get(
                    "memory_state_guide_record_source",
                    self._compiler_memory_record_source,
                )
            )
        )
        self._compiler_context_pressure_enabled = bool(
            compiler_context_pressure_config.get("enabled", False)
        )
        self._compiler_context_pressure_max_headroom_chars = int(
            compiler_context_pressure_config.get("max_headroom_chars", 0)
        )
        self._compiler_context_pressure_information_needs = _tuple_config(
            compiler_context_pressure_config.get("information_needs")
        )
        self._compiler_context_pressure_overrides = _dict_config(
            compiler_context_pressure_config.get("compiler") or {}
        )
        self._compiler_context_pressure_compiler = _configured_compiler(
            _merged_config(
                compiler_config,
                self._compiler_context_pressure_overrides,
            )
        )
        self._compiler_context_pressure_trace_config = _compiler_trace_config(
            _merged_config(
                compiler_config,
                self._compiler_context_pressure_overrides,
            ),
            memory_record_source=self._compiler_memory_record_source,
            memory_state_guide_record_source=(
                self._compiler_memory_state_guide_record_source
            ),
        )
        self._compiler_trace_config = _compiler_trace_config(
            compiler_config,
            memory_record_source=self._compiler_memory_record_source,
            memory_state_guide_record_source=(
                self._compiler_memory_state_guide_record_source
            ),
        )
        self._granularity_compilers = {
            profile["name"]: _configured_compiler(
                _merged_config(compiler_config, profile["compiler"])
            )
            for profile in self._granularity_profiles
            if profile.get("compiler")
        }
        self._granularity_context_pressure_compilers = {
            profile["name"]: _configured_compiler(
                _merged_config(
                    _merged_config(compiler_config, profile["compiler"]),
                    self._compiler_context_pressure_overrides,
                )
            )
            for profile in self._granularity_profiles
            if profile.get("compiler")
        }
        self._granularity_context_pressure_trace_configs = {
            profile["name"]: _compiler_trace_config(
                _merged_config(
                    _merged_config(compiler_config, profile["compiler"]),
                    self._compiler_context_pressure_overrides,
                ),
                memory_record_source=self._compiler_memory_record_source,
                memory_state_guide_record_source=(
                    self._compiler_memory_state_guide_record_source
                ),
            )
            for profile in self._granularity_profiles
            if profile.get("compiler")
        }
        self._granularity_compiler_trace_configs = {
            profile["name"]: _compiler_trace_config(
                _merged_config(compiler_config, profile["compiler"]),
                memory_record_source=self._compiler_memory_record_source,
                memory_state_guide_record_source=(
                    self._compiler_memory_state_guide_record_source
                ),
            )
            for profile in self._granularity_profiles
            if profile.get("compiler")
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
        self._answer_finalizer_enable_missing_detail = bool(
            answer_finalizer_config.get("enable_missing_detail", False)
        )
        self._answer_finalizer_enable_count_answer_detail = bool(
            answer_finalizer_config.get("enable_count_answer_detail", False)
        )
        self._answer_finalizer_enable_average_calculation = bool(
            answer_finalizer_config.get("enable_average_calculation", False)
        )
        self._answer_finalizer_enable_money_difference_calculation = bool(
            answer_finalizer_config.get("enable_money_difference_calculation", False)
        )
        self._answer_finalizer_enable_date_endpoint_duration_calculation = bool(
            answer_finalizer_config.get(
                "enable_date_endpoint_duration_calculation",
                False,
            )
        )
        self._answer_finalizer_enable_relative_time_calculation = bool(
            answer_finalizer_config.get("enable_relative_time_calculation", False)
        )
        self._answer_finalizer_enable_numeric_slot_label_preservation = bool(
            answer_finalizer_config.get(
                "enable_numeric_slot_label_preservation",
                False,
            )
        )
        self._answer_finalizer_enable_source_value_specificity_preservation = bool(
            answer_finalizer_config.get(
                "enable_source_value_specificity_preservation",
                False,
            )
        )
        self._answer_finalizer_enable_profile_preference_value_preservation = bool(
            answer_finalizer_config.get(
                "enable_profile_preference_value_preservation",
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
            "enable_missing_detail": self._answer_finalizer_enable_missing_detail,
            "enable_count_answer_detail": (
                self._answer_finalizer_enable_count_answer_detail
            ),
            "enable_average_calculation": (
                self._answer_finalizer_enable_average_calculation
            ),
            "enable_money_difference_calculation": (
                self._answer_finalizer_enable_money_difference_calculation
            ),
            "enable_date_endpoint_duration_calculation": (
                self._answer_finalizer_enable_date_endpoint_duration_calculation
            ),
            "enable_relative_time_calculation": (
                self._answer_finalizer_enable_relative_time_calculation
            ),
            "enable_numeric_slot_label_preservation": (
                self._answer_finalizer_enable_numeric_slot_label_preservation
            ),
            "enable_source_value_specificity_preservation": (
                self._answer_finalizer_enable_source_value_specificity_preservation
            ),
            "enable_profile_preference_value_preservation": (
                self._answer_finalizer_enable_profile_preference_value_preservation
            ),
        }
        self._answer_finalizer_profile_settings = {
            profile["name"]: _answer_finalizer_settings_from_config(
                _merged_config(answer_finalizer_config, profile["answer_finalizer"])
            )
            for profile in self._granularity_profiles
            if profile.get("answer_finalizer")
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
        self._answer_repair_uncertain_trigger_information_needs = _tuple_config(
            answer_repair_config.get("uncertain_trigger_information_needs")
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
        self._answer_repair_enable_profile_advice_abstention_trigger = bool(
            answer_repair_config.get(
                "enable_profile_advice_abstention_trigger", False
            )
        )
        self._answer_repair_enable_cross_route_profile_advice_abstention_trigger = (
            bool(
                answer_repair_config.get(
                    "enable_cross_route_profile_advice_abstention_trigger",
                    False,
                )
            )
        )
        self._answer_repair_cross_route_profile_advice_abstention_information_needs = (
            _tuple_config(
                answer_repair_config.get(
                    "cross_route_profile_advice_abstention_information_needs"
                )
            )
        )
        self._answer_repair_enable_modal_abstention_trigger = bool(
            answer_repair_config.get("enable_modal_abstention_trigger", False)
        )
        self._answer_repair_modal_abstention_information_needs = _tuple_config(
            answer_repair_config.get("modal_abstention_information_needs")
        )
        self._answer_repair_enable_source_grounded_modal_inference_trigger = bool(
            answer_repair_config.get(
                "enable_source_grounded_modal_inference_trigger", False
            )
        )
        self._answer_repair_source_grounded_modal_inference_information_needs = (
            _tuple_config(
                answer_repair_config.get(
                    "source_grounded_modal_inference_information_needs"
                )
            )
        )
        self._answer_repair_enable_source_grounded_temporal_calculation_trigger = bool(
            answer_repair_config.get(
                "enable_source_grounded_temporal_calculation_trigger", False
            )
        )
        self._answer_repair_source_grounded_temporal_calculation_information_needs = (
            _tuple_config(
                answer_repair_config.get(
                    "source_grounded_temporal_calculation_information_needs"
                )
            )
        )
        self._answer_repair_enable_source_grounded_temporal_order_trigger = bool(
            answer_repair_config.get(
                "enable_source_grounded_temporal_order_trigger", False
            )
        )
        self._answer_repair_source_grounded_temporal_order_information_needs = (
            _tuple_config(
                answer_repair_config.get(
                    "source_grounded_temporal_order_information_needs"
                )
            )
        )
        self._answer_repair_enable_lifecycle_ledger = bool(
            answer_repair_config.get("enable_lifecycle_ledger", False)
        )
        self._answer_repair_enable_lifecycle_slot_trigger = bool(
            answer_repair_config.get("enable_lifecycle_slot_trigger", False)
        )
        self._answer_repair_enable_source_backed_lifecycle_memory_trigger = bool(
            answer_repair_config.get(
                "enable_source_backed_lifecycle_memory_trigger", False
            )
        )
        self._answer_repair_uncertain_min_support_items = int(
            answer_repair_config.get("uncertain_min_support_items", 0)
        )
        self._answer_repair_source_grounded_modal_min_support_items = int(
            answer_repair_config.get("source_grounded_modal_min_support_items", 2)
        )
        self._answer_repair_source_grounded_temporal_calculation_min_support_items = (
            int(
                answer_repair_config.get(
                    "source_grounded_temporal_calculation_min_support_items", 1
                )
            )
        )
        self._answer_repair_source_grounded_temporal_order_min_support_items = int(
            answer_repair_config.get(
                "source_grounded_temporal_order_min_support_items", 3
            )
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
            "uncertain_trigger_information_needs": (
                self._answer_repair_uncertain_trigger_information_needs
            ),
            "enable_short_list_trigger": (
                self._answer_repair_enable_short_list_trigger
            ),
            "enable_temporal_conflict_trigger": (
                self._answer_repair_enable_temporal_conflict_trigger
            ),
            "enable_profile_preference_trigger": (
                self._answer_repair_enable_profile_preference_trigger
            ),
            "enable_profile_advice_abstention_trigger": (
                self._answer_repair_enable_profile_advice_abstention_trigger
            ),
            "enable_cross_route_profile_advice_abstention_trigger": (
                self._answer_repair_enable_cross_route_profile_advice_abstention_trigger
            ),
            "cross_route_profile_advice_abstention_information_needs": (
                self._answer_repair_cross_route_profile_advice_abstention_information_needs
            ),
            "enable_modal_abstention_trigger": (
                self._answer_repair_enable_modal_abstention_trigger
            ),
            "modal_abstention_information_needs": (
                self._answer_repair_modal_abstention_information_needs
            ),
            "enable_source_grounded_modal_inference_trigger": (
                self._answer_repair_enable_source_grounded_modal_inference_trigger
            ),
            "source_grounded_modal_inference_information_needs": (
                self._answer_repair_source_grounded_modal_inference_information_needs
            ),
            "enable_source_grounded_temporal_calculation_trigger": (
                self._answer_repair_enable_source_grounded_temporal_calculation_trigger
            ),
            "source_grounded_temporal_calculation_information_needs": (
                self._answer_repair_source_grounded_temporal_calculation_information_needs
            ),
            "enable_source_grounded_temporal_order_trigger": (
                self._answer_repair_enable_source_grounded_temporal_order_trigger
            ),
            "source_grounded_temporal_order_information_needs": (
                self._answer_repair_source_grounded_temporal_order_information_needs
            ),
            "enable_lifecycle_ledger": (
                self._answer_repair_enable_lifecycle_ledger
            ),
            "enable_lifecycle_slot_trigger": (
                self._answer_repair_enable_lifecycle_slot_trigger
            ),
            "enable_source_backed_lifecycle_memory_trigger": (
                self._answer_repair_enable_source_backed_lifecycle_memory_trigger
            ),
            "uncertain_min_support_items": (
                self._answer_repair_uncertain_min_support_items
            ),
            "source_grounded_modal_min_support_items": (
                self._answer_repair_source_grounded_modal_min_support_items
            ),
            "source_grounded_temporal_calculation_min_support_items": (
                self._answer_repair_source_grounded_temporal_calculation_min_support_items
            ),
            "source_grounded_temporal_order_min_support_items": (
                self._answer_repair_source_grounded_temporal_order_min_support_items
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
                "chat_template_kwargs": repair_answer_config.get(
                    "chat_template_kwargs"
                ),
                "cache_enabled": self._answer_repair_cache_enabled,
                "cache_path": self._answer_repair_cache_path,
                "cache_namespace": self._answer_repair_cache_namespace,
            }

    def predict(self, request: PredictionRequest) -> dict[str, Any]:
        store = RawEvidenceStore(request.turns)
        granularity_profile = _select_granularity_profile(
            self._granularity_profiles,
            avg_turn_chars=store.average_turn_chars,
            total_turn_chars=store.total_turn_chars,
        )
        granularity_profile_audit = _granularity_profile_audit(
            enabled=self._granularity_profile_audit_enabled,
            profiles=self._granularity_profiles,
            selected_profile=granularity_profile,
            avg_turn_chars=store.average_turn_chars,
            total_turn_chars=store.total_turn_chars,
        )
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
                require_assistant_answer_source=(
                    self._build_memory_source_alignment_require_assistant_answer_source
                ),
                memory_types=self._build_memory_source_alignment_memory_types,
                source_order=self._build_memory_source_alignment_source_order,
            )
            built_memory = replace(built_memory, records=aligned_records)
        profile_name = granularity_profile.get("name") if granularity_profile else None
        router = self._granularity_routers.get(str(profile_name), self._router)
        heuristic_route = router.route(request.question, request.question_time)
        route = heuristic_route
        retrieval_settings = self._retrieval_settings_for_route(
            route,
            granularity_profile=granularity_profile,
        )
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
        memory_slot_chain_source_hits = ()
        object_slot_source_hits = ()
        memory_slot_chain_trace = _disabled_memory_slot_chain_trace(
            enabled=self._memory_slot_chain_enabled,
            information_needs=self._memory_slot_chain_information_needs,
            max_chains=self._memory_slot_chain_max_chains,
            max_sources_per_chain=self._memory_slot_chain_max_sources_per_chain,
            memory_types=self._memory_slot_chain_memory_types,
            question_scope_gate=self._memory_slot_chain_question_scope_gate,
            source_policy=self._memory_slot_chain_source_policy,
        )
        object_slot_activation_trace = _disabled_object_slot_activation_trace(
            enabled=self._object_slot_activation_enabled,
            information_needs=self._object_slot_activation_information_needs,
            memory_types=self._object_slot_activation_memory_types,
            max_slots=self._object_slot_activation_max_slots,
            max_sources_per_slot=(
                self._object_slot_activation_max_sources_per_slot
            ),
            min_overlap_terms=self._object_slot_activation_min_overlap_terms,
            require_collection_slot=(
                self._object_slot_activation_require_collection_slot
            ),
        )
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
            if _memory_slot_chain_applies(
                enabled=self._memory_slot_chain_enabled,
                route=route,
                information_needs=self._memory_slot_chain_information_needs,
            ):
                (
                    memory_slot_chain_source_hits,
                    memory_slot_chain_trace,
                ) = _memory_slot_chain_source_hits(
                    memory_hits=memory_hits,
                    built_memory_records=built_memory.records,
                    question=request.question,
                    route=route,
                    available_source_ids={turn.source_id for turn in store.turns},
                    max_chains=self._memory_slot_chain_max_chains,
                    max_sources_per_chain=(
                        self._memory_slot_chain_max_sources_per_chain
                    ),
                    memory_types=self._memory_slot_chain_memory_types,
                    question_scope_gate=self._memory_slot_chain_question_scope_gate,
                    source_policy=self._memory_slot_chain_source_policy,
                )
            if _object_slot_activation_applies(
                enabled=self._object_slot_activation_enabled,
                route=route,
                information_needs=self._object_slot_activation_information_needs,
            ):
                (
                    object_slot_source_hits,
                    object_slot_activation_trace,
                ) = _memory_object_slot_source_hits(
                    memory_hits=memory_hits,
                    built_memory_records=built_memory.records,
                    question=request.question,
                    route=route,
                    available_source_ids={turn.source_id for turn in store.turns},
                    max_slots=self._object_slot_activation_max_slots,
                    max_sources_per_slot=(
                        self._object_slot_activation_max_sources_per_slot
                    ),
                    memory_types=self._object_slot_activation_memory_types,
                    min_overlap_terms=(
                        self._object_slot_activation_min_overlap_terms
                    ),
                    require_collection_slot=(
                        self._object_slot_activation_require_collection_slot
                    ),
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
        if self._embedding_client is not None:
            hit_lists = tuple(
                hits for hits in (lexical_hits, dense_hits) if hits
            )
            if memory_source_hits:
                hit_lists = (*hit_lists, memory_source_hits)
            if memory_slot_chain_source_hits:
                hit_lists = (*hit_lists, memory_slot_chain_source_hits)
            if object_slot_source_hits:
                hit_lists = (*hit_lists, object_slot_source_hits)
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
            if (
                memory_source_hits
                or memory_slot_chain_source_hits
                or object_slot_source_hits
                or turn_window_source_hits
            ):
                hits = _merge_hit_lists(
                    tuple(
                        hits
                        for hits in (
                            lexical_hits,
                            memory_source_hits,
                            memory_slot_chain_source_hits,
                            object_slot_source_hits,
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
            min_effective_top_k=self._rerank_min_effective_top_k,
            return_top_k=self._rerank_return_top_k,
            exchange_guard_enabled=self._rerank_exchange_guard_enabled,
        )
        rerank_skipped_reason = _rerank_skip_reason(
            route=route,
            enabled_information_needs=self._rerank_information_needs,
            top_k=top_k,
            min_effective_top_k=self._rerank_min_effective_top_k,
        )
        protected_rerank_source_ids = _ordered_unique(
            (
                *_source_ids_from_hits(memory_source_hits),
                *_source_ids_from_hits(memory_slot_chain_source_hits),
                *_source_ids_from_hits(object_slot_source_hits),
            )
        )
        if self._rerank_client is not None and rerank_skipped_reason is None:
            hits, rerank_trace = self._rerank_hits(
                store=store,
                request=request,
                hits=hits,
                top_k=top_k,
                memory_hits=memory_hits,
                protected_source_ids=protected_rerank_source_ids,
            )
        elif self._rerank_enabled:
            rerank_trace["skipped_reason"] = rerank_skipped_reason
        pre_context_budget_hits = hits
        context_budget_trace = _disabled_context_budget_trace(
            enabled=self._context_budget_enabled,
            max_chars=self._context_budget_max_chars,
            min_hits=self._context_budget_min_hits,
            protect_top_n=self._context_budget_protect_top_n,
            max_hits=self._context_budget_max_hits,
            information_needs=self._context_budget_information_needs,
        )
        if _context_budget_applies(
            route=route,
            enabled=self._context_budget_enabled,
            max_chars=self._context_budget_max_chars,
            information_needs=self._context_budget_information_needs,
        ):
            hits, context_budget_trace = _apply_context_budget(
                store=store,
                hits=hits,
                max_chars=self._context_budget_max_chars,
                min_hits=self._context_budget_min_hits,
                protect_top_n=self._context_budget_protect_top_n,
                max_hits=self._context_budget_max_hits,
                information_needs=self._context_budget_information_needs,
            )
        evidence_turns = store.expand_neighbors(
            (hit.source_id for hit in hits),
            window=self._neighbor_window,
            order=self._neighbor_order,
        )
        selected_context_settings = self._selected_context_settings(
            granularity_profile,
            route,
        )
        selected_context_enabled, selected_context_budget_gate = (
            _selected_context_budget_gate(
                enabled=selected_context_settings["enabled"],
                min_context_budget_headroom_chars=selected_context_settings[
                    "min_context_budget_headroom_chars"
                ],
                context_budget_trace=context_budget_trace,
            )
        )
        evidence_turns, selected_context = _materialize_selected_context(
            store=store,
            turns=evidence_turns,
            route=route,
            enabled=selected_context_enabled,
            information_needs=selected_context_settings["information_needs"],
            window_before=selected_context_settings["window_before"],
            window_after=selected_context_settings["window_after"],
            max_rows=selected_context_settings["max_rows"],
            max_neighbor_chars=selected_context_settings["max_neighbor_chars"],
            max_center_chars=selected_context_settings["max_center_chars"],
            context_format=selected_context_settings["context_format"],
            timestamp_policy=selected_context_settings["timestamp_policy"],
            require_anaphora=selected_context_settings["require_anaphora"],
            question=request.question,
            require_question_reference=selected_context_settings[
                "require_question_reference"
            ],
            require_question_reference_min_center_chars=selected_context_settings[
                "require_question_reference_min_center_chars"
            ],
            require_source_grounded_self_reference=selected_context_settings[
                "require_source_grounded_self_reference"
            ],
            source_grounded_min_terms=selected_context_settings[
                "source_grounded_min_terms"
            ],
            source_grounded_min_coverage=selected_context_settings[
                "source_grounded_min_coverage"
            ],
            require_materialized_source_grounded=selected_context_settings[
                "require_materialized_source_grounded"
            ],
            materialized_source_grounded_min_terms=selected_context_settings[
                "materialized_source_grounded_min_terms"
            ],
            materialized_source_grounded_min_coverage=selected_context_settings[
                "materialized_source_grounded_min_coverage"
            ],
        )
        selected_context.update(selected_context_budget_gate)
        selected_context["granularity_profile"] = granularity_profile
        selected_context["route_override"] = selected_context_settings.get(
            "route_override"
        )
        selected_context["risk_audit"] = _selected_context_risk_audit(
            store=store,
            evidence_turns=evidence_turns,
            route=route,
            question=request.question,
            selected_context=selected_context,
            enabled=self._selected_context_risk_audit_enabled,
            information_needs=self._selected_context_risk_audit_information_needs,
            source_grounded_min_terms=(
                self._selected_context_risk_audit_source_grounded_min_terms
            ),
            source_grounded_min_coverage=(
                self._selected_context_risk_audit_source_grounded_min_coverage
            ),
        )
        compiler_memory_records = _compiler_memory_records(
            source=self._compiler_memory_record_source,
            memory_hits=memory_hits,
            built_memory_records=built_memory.records,
            evidence_turns=evidence_turns,
        )
        compiler_memory_state_guide_records = (
            compiler_memory_records
            if self._compiler_memory_state_guide_record_source
            == self._compiler_memory_record_source
            else _compiler_memory_records(
                source=self._compiler_memory_state_guide_record_source,
                memory_hits=memory_hits,
                built_memory_records=built_memory.records,
                evidence_turns=evidence_turns,
            )
        )
        compiler = self._granularity_compilers.get(
            str(profile_name),
            self._compiler,
        )
        compiler_trace_config = self._granularity_compiler_trace_configs.get(
            str(profile_name),
            self._compiler_trace_config,
        )
        compiler_context_pressure = _compiler_context_pressure_trace(
            enabled=self._compiler_context_pressure_enabled,
            max_headroom_chars=(
                self._compiler_context_pressure_max_headroom_chars
            ),
            information_needs=(
                self._compiler_context_pressure_information_needs
            ),
            route=route,
            overrides=self._compiler_context_pressure_overrides,
            context_budget_trace=context_budget_trace,
        )
        if compiler_context_pressure["applied"]:
            compiler = self._granularity_context_pressure_compilers.get(
                str(profile_name),
                self._compiler_context_pressure_compiler,
            )
            compiler_trace_config = (
                self._granularity_context_pressure_trace_configs.get(
                    str(profile_name),
                    self._compiler_context_pressure_trace_config,
                )
            )
        compiled = compiler.compile(
            question=request.question,
            question_time=request.question_time,
            route=route,
            hits=hits,
            evidence_turns=evidence_turns,
            memory_records=compiler_memory_records,
            memory_state_guide_records=compiler_memory_state_guide_records,
        )
        memory_lifecycle_manifest = _memory_lifecycle_manifest(
            question=request.question,
            route=route,
            built_memory_records=built_memory.records,
            compiler_memory_records=compiler_memory_records,
            evidence_rows=compiled.evidence_rows,
        )
        context_budget_audit = _disabled_context_budget_audit_trace(
            enabled=self._context_budget_audit_enabled,
            max_chars=self._context_budget_audit_max_chars,
            min_hits=self._context_budget_audit_min_hits,
            protect_top_n=self._context_budget_audit_protect_top_n,
            max_hits=self._context_budget_audit_max_hits,
            information_needs=self._context_budget_audit_information_needs,
        )
        if _context_budget_applies(
            route=route,
            enabled=self._context_budget_audit_enabled,
            max_chars=self._context_budget_audit_max_chars,
            information_needs=self._context_budget_audit_information_needs,
        ):
            projected_hits, projected_budget = _apply_context_budget(
                store=store,
                hits=pre_context_budget_hits,
                max_chars=self._context_budget_audit_max_chars,
                min_hits=self._context_budget_audit_min_hits,
                protect_top_n=self._context_budget_audit_protect_top_n,
                max_hits=self._context_budget_audit_max_hits,
                information_needs=self._context_budget_audit_information_needs,
            )
            context_budget_audit = _context_budget_audit_trace(
                store=store,
                projected_hits=projected_hits,
                projected_budget=projected_budget,
                neighbor_window=self._neighbor_window,
                neighbor_order=self._neighbor_order,
                evidence_rows=compiled.evidence_rows,
                selected_context=selected_context,
            )
        context_manifest = _context_manifest(
            store=store,
            route=route,
            lexical_hits=lexical_hits,
            dense_hits=dense_hits,
            memory_hits=memory_hits,
            memory_source_hits=memory_source_hits,
            memory_slot_chain_source_hits=memory_slot_chain_source_hits,
            object_slot_source_hits=object_slot_source_hits,
            turn_window_source_hits=turn_window_source_hits,
            pre_context_budget_hits=pre_context_budget_hits,
            retrieval_hits=hits,
            context_budget_trace=context_budget_trace,
            context_budget_audit=context_budget_audit,
            evidence_turns=evidence_turns,
            selected_context=selected_context,
            built_memory_records=built_memory.records,
            compiler_memory_records=compiler_memory_records,
            evidence_rows=compiled.evidence_rows,
            compiled_context_chars=compiled.context_chars,
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
            enable_uncertain_trigger=(
                self._answer_repair_enable_uncertain_trigger
                and (
                    not self._answer_repair_uncertain_trigger_information_needs
                    or route.information_need
                    in self._answer_repair_uncertain_trigger_information_needs
                )
            ),
            enable_short_list_trigger=self._answer_repair_enable_short_list_trigger,
            enable_temporal_conflict_trigger=(
                self._answer_repair_enable_temporal_conflict_trigger
            ),
            enable_profile_preference_trigger=(
                self._answer_repair_enable_profile_preference_trigger
            ),
            enable_profile_advice_abstention_trigger=(
                self._answer_repair_enable_profile_advice_abstention_trigger
            ),
            enable_cross_route_profile_advice_abstention_trigger=(
                self._answer_repair_enable_cross_route_profile_advice_abstention_trigger
                and (
                    not self._answer_repair_cross_route_profile_advice_abstention_information_needs
                    or route.information_need
                    in self._answer_repair_cross_route_profile_advice_abstention_information_needs
                )
            ),
            enable_modal_abstention_trigger=(
                self._answer_repair_enable_modal_abstention_trigger
                and (
                    not self._answer_repair_modal_abstention_information_needs
                    or route.information_need
                    in self._answer_repair_modal_abstention_information_needs
                )
            ),
            enable_source_grounded_modal_inference_trigger=(
                self._answer_repair_enable_source_grounded_modal_inference_trigger
                and (
                    not self._answer_repair_source_grounded_modal_inference_information_needs
                    or route.information_need
                    in self._answer_repair_source_grounded_modal_inference_information_needs
                )
            ),
            enable_source_grounded_temporal_calculation_trigger=(
                self._answer_repair_enable_source_grounded_temporal_calculation_trigger
                and (
                    not self._answer_repair_source_grounded_temporal_calculation_information_needs
                    or route.information_need
                    in self._answer_repair_source_grounded_temporal_calculation_information_needs
                )
            ),
            enable_source_grounded_temporal_order_trigger=(
                self._answer_repair_enable_source_grounded_temporal_order_trigger
                and (
                    not self._answer_repair_source_grounded_temporal_order_information_needs
                    or route.information_need
                    in self._answer_repair_source_grounded_temporal_order_information_needs
                )
            ),
            uncertain_min_support_items=(
                self._answer_repair_uncertain_min_support_items
            ),
            source_grounded_modal_min_support_items=(
                self._answer_repair_source_grounded_modal_min_support_items
            ),
            source_grounded_temporal_calculation_min_support_items=(
                self._answer_repair_source_grounded_temporal_calculation_min_support_items
            ),
            source_grounded_temporal_order_min_support_items=(
                self._answer_repair_source_grounded_temporal_order_min_support_items
            ),
            max_context_chars=self._answer_repair_max_context_chars,
            max_row_text_chars=self._answer_repair_max_row_text_chars,
            enable_lifecycle_ledger=self._answer_repair_enable_lifecycle_ledger,
            enable_lifecycle_slot_trigger=(
                self._answer_repair_enable_lifecycle_slot_trigger
            ),
            enable_source_backed_lifecycle_memory_trigger=(
                self._answer_repair_enable_source_backed_lifecycle_memory_trigger
            ),
        )
        repair_cache_after = _answer_cache_stats(self._answer_repairer)
        answer = answer_repair.answer
        finalizer_settings = self._finalizer_settings(granularity_profile)
        answer_finalization = self._finalize_answer(
            question=request.question,
            answer=answer,
            settings=finalizer_settings,
        )
        if answer_finalization.applied:
            answer = AnswerResult(
                answer=answer_finalization.answer,
                model=answer.model,
                token_usage=answer.token_usage,
                raw_response=answer.raw_response,
            )
        token_usage = built_memory.token_usage + answer.token_usage
        return {
            "answer": answer.answer,
            "trace": {
                "store": store.manifest(),
                "build_memory": built_memory.to_dict(),
                "build_memory_config": self._build_memory_trace_config,
                "build_memory_source_alignment": source_alignment,
                "memory_lifecycle_manifest": memory_lifecycle_manifest,
                "context_manifest": context_manifest,
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
                    "route_override_precedence": (
                        self._retrieval_route_override_precedence
                    ),
                    "route_override": self._retrieval_route_overrides.get(
                        route.information_need, {}
                    ),
                    "granularity_profile": granularity_profile,
                    "granularity_profile_audit": granularity_profile_audit,
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
                    "compiler_memory_state_guide_record_source": (
                        self._compiler_memory_state_guide_record_source
                    ),
                    "compiler_profile": profile_name
                    if str(profile_name) in self._granularity_compilers
                    else None,
                    "compiler_memory_records": [
                        record.to_dict() for record in compiler_memory_records
                    ],
                    "compiler_memory_state_guide_records": [
                        record.to_dict()
                        for record in compiler_memory_state_guide_records
                    ],
                    "memory_source_hits": [
                        hit.to_dict() for hit in memory_source_hits
                    ],
                    "memory_slot_chain_enabled": self._memory_slot_chain_enabled,
                    "memory_slot_chain_applied": memory_slot_chain_trace["applied"],
                    "memory_slot_chain_information_needs": (
                        self._memory_slot_chain_information_needs
                    ),
                    "memory_slot_chain_max_chains": (
                        self._memory_slot_chain_max_chains
                    ),
                    "memory_slot_chain_max_sources_per_chain": (
                        self._memory_slot_chain_max_sources_per_chain
                    ),
                    "memory_slot_chain_memory_types": (
                        self._memory_slot_chain_memory_types
                    ),
                    "memory_slot_chain_question_scope_gate": (
                        self._memory_slot_chain_question_scope_gate
                    ),
                    "memory_slot_chain_source_policy": (
                        self._memory_slot_chain_source_policy
                    ),
                    "memory_slot_chain_question_scope": memory_slot_chain_trace[
                        "question_scope"
                    ],
                    "memory_slot_chain_source_hits": [
                        hit.to_dict() for hit in memory_slot_chain_source_hits
                    ],
                    "memory_slot_chain_chains": memory_slot_chain_trace["chains"],
                    "memory_slot_chain_skipped_reason": memory_slot_chain_trace[
                        "skipped_reason"
                    ],
                    "object_slot_activation_enabled": (
                        self._object_slot_activation_enabled
                    ),
                    "object_slot_activation_applied": (
                        object_slot_activation_trace["applied"]
                    ),
                    "object_slot_activation_information_needs": (
                        self._object_slot_activation_information_needs
                    ),
                    "object_slot_activation_memory_types": (
                        self._object_slot_activation_memory_types
                    ),
                    "object_slot_activation_max_slots": (
                        self._object_slot_activation_max_slots
                    ),
                    "object_slot_activation_max_sources_per_slot": (
                        self._object_slot_activation_max_sources_per_slot
                    ),
                    "object_slot_activation_min_overlap_terms": (
                        self._object_slot_activation_min_overlap_terms
                    ),
                    "object_slot_activation_require_collection_slot": (
                        self._object_slot_activation_require_collection_slot
                    ),
                    "object_slot_activation_source_hits": [
                        hit.to_dict() for hit in object_slot_source_hits
                    ],
                    "object_slot_activation_slots": (
                        object_slot_activation_trace["slots"]
                    ),
                    "object_slot_activation_skipped_reason": (
                        object_slot_activation_trace["skipped_reason"]
                    ),
                    "dense_hits": [hit.to_dict() for hit in dense_hits],
                    "turn_window_hits": [
                        hit.to_dict() for hit in turn_window_hits
                    ],
                    "turn_window_source_hits": [
                        hit.to_dict() for hit in turn_window_source_hits
                    ],
                    "selected_context": selected_context,
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
                    "rerank_min_effective_top_k": (
                        self._rerank_min_effective_top_k
                        if self._rerank_enabled
                        else None
                    ),
                    "rerank_return_top_k": rerank_trace.get("return_top_k")
                    if self._rerank_enabled
                    else None,
                    "rerank_query_text_mode": self._rerank_query_text_mode
                    if self._rerank_enabled
                    else None,
                    "rerank_document_max_chars": self._rerank_document_max_chars
                    if self._rerank_enabled
                    else None,
                    "rerank_document_text_mode": self._rerank_document_text_mode
                    if self._rerank_enabled
                    else None,
                    "rerank_document_neighbor_window": (
                        self._rerank_document_neighbor_window
                        if self._rerank_enabled
                        else None
                    ),
                    "rerank_document_max_memory_records": (
                        self._rerank_document_max_memory_records
                        if self._rerank_enabled
                        else None
                    ),
                    "rerank_anchor_keep": self._rerank_anchor_keep
                    if self._rerank_enabled
                    else None,
                    "rerank_anchor_after_top": self._rerank_anchor_after_top
                    if self._rerank_enabled
                    else None,
                    "rerank_selection_mode": self._rerank_selection_mode
                    if self._rerank_enabled
                    else None,
                    "rerank_information_needs": self._rerank_information_needs,
                    "rerank_exchange_guard_enabled": (
                        self._rerank_exchange_guard_enabled
                    )
                    if self._rerank_enabled
                    else None,
                    "rerank_exchange_guard": rerank_trace.get("exchange_guard"),
                    "rerank_candidate_count": rerank_trace["candidate_count"],
                    "rerank_returned_count": rerank_trace["returned_count"],
                    "rerank_total_tokens": rerank_trace["total_tokens"],
                    "rerank_skipped_reason": rerank_trace["skipped_reason"],
                    "rerank_response": rerank_trace["response"],
                    "pre_rerank_hits": [
                        hit.to_dict() for hit in pre_rerank_hits
                    ],
                    "context_budget_enabled": self._context_budget_enabled,
                    "context_budget_applied": context_budget_trace["applied"],
                    "context_budget_max_chars": self._context_budget_max_chars
                    if self._context_budget_enabled
                    else None,
                    "context_budget_min_hits": self._context_budget_min_hits
                    if self._context_budget_enabled
                    else None,
                    "context_budget_protect_top_n": (
                        self._context_budget_protect_top_n
                        if self._context_budget_enabled
                        else None
                    ),
                    "context_budget_max_hits": self._context_budget_max_hits
                    if self._context_budget_enabled
                    else None,
                    "context_budget_information_needs": (
                        self._context_budget_information_needs
                    ),
                    "context_budget_candidate_count": (
                        context_budget_trace["candidate_count"]
                    ),
                    "context_budget_returned_count": (
                        context_budget_trace["returned_count"]
                    ),
                    "context_budget_estimated_chars": (
                        context_budget_trace["estimated_chars"]
                    ),
                    "context_budget_dropped_count": (
                        context_budget_trace["dropped_count"]
                    ),
                    "context_budget_dropped_source_ids": (
                        context_budget_trace["dropped_source_ids"]
                    ),
                    "context_budget_audit": context_budget_audit,
                    "pre_context_budget_hits": [
                        hit.to_dict() for hit in pre_context_budget_hits
                    ],
                    "hits": [hit.to_dict() for hit in hits],
                },
                "compiled_context": compiled.to_dict(),
                "compiler": compiler_trace_config,
                "compiler_context_pressure": compiler_context_pressure,
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
                    **finalizer_settings,
                    "granularity_profile": granularity_profile,
                    **answer_finalization.to_dict(),
                },
                "answer": answer.to_dict(),
                "token_cost": token_usage.to_dict(),
            },
        }

    def _retrieval_settings_for_route(
        self,
        route: RouteResult,
        *,
        granularity_profile: Mapping[str, Any] | None = None,
    ) -> dict[str, int]:
        settings = {
            "top_k": self._base_top_k,
            "max_top_k": self._max_top_k,
            "dense_top_k": self._dense_top_k,
            "lexical_protect_top_n": self._lexical_protect_top_n,
            "dense_protect_top_n": self._dense_protect_top_n,
        }
        route_override = self._retrieval_route_overrides.get(
            route.information_need,
            {},
        )
        if self._retrieval_route_override_precedence == "before_profile":
            settings.update(route_override)
            if granularity_profile:
                settings.update(granularity_profile.get("retrieval", {}))
        else:
            if granularity_profile:
                settings.update(granularity_profile.get("retrieval", {}))
            settings.update(route_override)
        top_k = min(
            settings["top_k"] * route.retrieval_multiplier,
            settings["max_top_k"],
        )
        candidate_top_k = top_k
        dense_top_k = settings["dense_top_k"]
        if self._rerank_enabled and _rerank_skip_reason(
            route=route,
            enabled_information_needs=self._rerank_information_needs,
            top_k=top_k,
            min_effective_top_k=self._rerank_min_effective_top_k,
        ) is None:
            candidate_top_k = max(candidate_top_k, self._rerank_pool_k)
            dense_top_k = max(dense_top_k, candidate_top_k)
        return {
            "top_k": top_k,
            "candidate_top_k": candidate_top_k,
            "dense_top_k": dense_top_k,
            "lexical_protect_top_n": settings["lexical_protect_top_n"],
            "dense_protect_top_n": settings["dense_protect_top_n"],
        }

    def _selected_context_settings(
        self,
        granularity_profile: Mapping[str, Any] | None,
        route: RouteResult,
    ) -> dict[str, Any]:
        settings: dict[str, Any] = {
            "enabled": self._selected_context_enabled,
            "window_before": self._selected_context_window_before,
            "window_after": self._selected_context_window_after,
            "max_rows": self._selected_context_max_rows,
            "max_neighbor_chars": self._selected_context_max_neighbor_chars,
            "max_center_chars": self._selected_context_max_center_chars,
            "context_format": self._selected_context_context_format,
            "timestamp_policy": self._selected_context_timestamp_policy,
            "require_anaphora": self._selected_context_require_anaphora,
            "require_question_reference": (
                self._selected_context_require_question_reference
            ),
            "require_question_reference_min_center_chars": (
                self._selected_context_require_question_reference_min_center_chars
            ),
            "require_source_grounded_self_reference": (
                self._selected_context_require_source_grounded_self_reference
            ),
            "source_grounded_min_terms": (
                self._selected_context_source_grounded_min_terms
            ),
            "source_grounded_min_coverage": (
                self._selected_context_source_grounded_min_coverage
            ),
            "require_materialized_source_grounded": (
                self._selected_context_require_materialized_source_grounded
            ),
            "materialized_source_grounded_min_terms": (
                self._selected_context_materialized_source_grounded_min_terms
            ),
            "materialized_source_grounded_min_coverage": (
                self._selected_context_materialized_source_grounded_min_coverage
            ),
            "min_context_budget_headroom_chars": (
                self._selected_context_min_context_budget_headroom_chars
            ),
            "information_needs": self._selected_context_information_needs,
        }
        route_override = self._selected_context_route_overrides.get(
            route.information_need
        )
        if route_override:
            settings.update(route_override)
            settings["route_override"] = route.information_need
        if granularity_profile:
            settings.update(granularity_profile.get("selected_context", {}))
            settings["information_needs"] = _tuple_config(
                settings.get("information_needs")
            )
        return settings

    def _finalizer_settings(
        self,
        granularity_profile: Mapping[str, Any] | None,
    ) -> dict[str, Any]:
        if granularity_profile:
            profile_name = str(granularity_profile.get("name"))
            settings = self._answer_finalizer_profile_settings.get(profile_name)
            if settings is not None:
                return settings
        return dict(self._answer_finalizer_trace_config)

    def _rerank_hits(
        self,
        *,
        store: RawEvidenceStore,
        request: PredictionRequest,
        hits: tuple[RetrievalHit, ...],
        top_k: int,
        memory_hits: tuple[Any, ...],
        protected_source_ids: tuple[str, ...] = (),
    ) -> tuple[tuple[RetrievalHit, ...], dict[str, Any]]:
        if self._rerank_client is None or not hits:
            return hits[:top_k], _disabled_rerank_trace(
                enabled=self._rerank_enabled,
                information_needs=self._rerank_information_needs,
                min_effective_top_k=self._rerank_min_effective_top_k,
                return_top_k=self._rerank_return_top_k,
                exchange_guard_enabled=self._rerank_exchange_guard_enabled,
            )

        rerank_items = tuple(
            (hit, turn)
            for hit in hits
            if (turn := store.get(hit.source_id)) is not None
        )
        return_top_k = self._rerank_return_top_k or top_k
        return_top_k = min(top_k, max(0, return_top_k), len(rerank_items))
        if not rerank_items:
            trace = _disabled_rerank_trace(
                enabled=self._rerank_enabled,
                information_needs=self._rerank_information_needs,
                min_effective_top_k=self._rerank_min_effective_top_k,
                return_top_k=return_top_k,
                exchange_guard_enabled=self._rerank_exchange_guard_enabled,
            )
            trace["response"] = {"skipped": "no_source_documents"}
            return hits[:top_k], trace
        rerank_hits = tuple(hit for hit, _turn in rerank_items)
        guard_reason, guard_trace = _rerank_exchange_guard(
            store=store,
            question=request.question,
            hits=rerank_hits,
            top_k=top_k,
            return_top_k=return_top_k,
            selection_mode=self._rerank_selection_mode,
            anchor_keep=self._rerank_anchor_keep,
            protected_source_ids=protected_source_ids,
            enabled=self._rerank_exchange_guard_enabled,
            protect_memory_sources=(
                self._rerank_exchange_guard_protect_memory_sources
            ),
            protect_adjacent_session=(
                self._rerank_exchange_guard_protect_adjacent_session
            ),
            question_overlap_min_terms=(
                self._rerank_exchange_guard_question_overlap_min_terms
            ),
        )
        if guard_reason is not None:
            trace = _disabled_rerank_trace(
                enabled=self._rerank_enabled,
                information_needs=self._rerank_information_needs,
                min_effective_top_k=self._rerank_min_effective_top_k,
                skipped_reason=guard_reason,
                return_top_k=return_top_k,
                exchange_guard_enabled=self._rerank_exchange_guard_enabled,
                exchange_guard=guard_trace,
            )
            trace["candidate_count"] = len(rerank_hits)
            trace["returned_count"] = min(top_k, len(hits))
            trace["response"] = {"exchange_guard": guard_trace}
            return hits[:top_k], trace
        memory_records_by_source = _memory_records_by_source(memory_hits)
        documents = [
            self._format_rerank_document(
                store=store,
                turn=turn,
                memory_records=memory_records_by_source.get(hit.source_id, ()),
            )
            for hit, turn in rerank_items
        ]
        query = _dense_query_text(
            request.question,
            request.question_time,
            mode=self._rerank_query_text_mode,
        )
        result = self._rerank_client.rerank(query=query, documents=documents)
        if self._rerank_selection_mode == "filter_preserve_order":
            reranked_hits = rerank_hits_filter_preserve_order(
                hits=rerank_hits,
                scores=result.scores,
                top_k=return_top_k,
                anchor_keep=self._rerank_anchor_keep,
                anchor_after_top=self._rerank_anchor_after_top,
            )
        else:
            reranked_hits = rerank_hits_with_anchor_retention(
                hits=rerank_hits,
                scores=result.scores,
                top_k=return_top_k,
                anchor_keep=self._rerank_anchor_keep,
                anchor_after_top=self._rerank_anchor_after_top,
            )
        response = dict(result.response)
        response["exchange_guard"] = guard_trace
        return reranked_hits, {
            "enabled": self._rerank_enabled,
            "applied": True,
            "information_needs": self._rerank_information_needs,
            "selection_mode": self._rerank_selection_mode,
            "min_effective_top_k": self._rerank_min_effective_top_k,
            "return_top_k": return_top_k,
            "exchange_guard_enabled": self._rerank_exchange_guard_enabled,
            "exchange_guard": guard_trace,
            "candidate_count": len(rerank_hits),
            "returned_count": len(reranked_hits),
            "total_tokens": result.total_tokens,
            "skipped_reason": None,
            "document_text_mode": self._rerank_document_text_mode,
            "document_neighbor_window": self._rerank_document_neighbor_window,
            "document_max_memory_records": (
                self._rerank_document_max_memory_records
            ),
            "response": response,
        }

    def _format_rerank_document(
        self,
        *,
        store: RawEvidenceStore,
        turn: Any,
        memory_records: tuple[Any, ...],
    ) -> str:
        if self._rerank_document_text_mode == "turn":
            return format_rerank_turn_document(
                turn,
                max_chars=self._rerank_document_max_chars,
            )
        neighbor_turns = _neighbor_turns_for_rerank(
            store,
            turn,
            window=self._rerank_document_neighbor_window,
        )
        return format_rerank_evidence_document(
            turn,
            mode=self._rerank_document_text_mode,
            neighbor_turns=neighbor_turns,
            memory_records=memory_records,
            max_chars=self._rerank_document_max_chars,
            neighbor_max_chars=self._rerank_document_neighbor_max_chars,
            max_memory_records=self._rerank_document_max_memory_records,
            memory_max_chars=self._rerank_document_memory_max_chars,
        )

    def _finalize_answer(
        self,
        *,
        question: str,
        answer: AnswerResult,
        settings: Mapping[str, Any],
    ) -> AnswerFinalization:
        if not bool(settings.get("enabled", False)):
            return AnswerFinalization(
                answer=answer.answer,
                before=answer.answer,
                applied=False,
                reason="disabled",
            )
        mode = str(settings.get("mode", "structured_evidence_mechanical"))
        if mode == "source_grounded_consistency_guard":
            return guard_source_grounded_answer(
                question=question,
                draft_answer=answer.answer,
                raw_response=answer.raw_response,
                enable_missing_detail=bool(
                    settings.get("enable_missing_detail", False)
                ),
                enable_numeric_slot_label_preservation=bool(
                    settings.get("enable_numeric_slot_label_preservation", False)
                ),
                enable_source_value_specificity_preservation=bool(
                    settings.get(
                        "enable_source_value_specificity_preservation",
                        False,
                    )
                ),
                enable_profile_preference_value_preservation=bool(
                    settings.get(
                        "enable_profile_preference_value_preservation",
                        False,
                    )
                ),
            )
        if mode != "structured_evidence_mechanical":
            raise ValueError(
                f"Unsupported answer.finalizer.mode: {mode}"
            )
        return finalize_structured_answer(
            question=question,
            draft_answer=answer.answer,
            raw_response=answer.raw_response,
            enable_count_correction=bool(settings.get("enable_count_correction", False)),
            enable_evidence_report_count_correction=(
                bool(settings.get("enable_evidence_report_count_correction", False))
            ),
            enable_money_sum_correction=(
                bool(settings.get("enable_money_sum_correction", True))
            ),
            enable_duration_rounding_correction=(
                bool(settings.get("enable_duration_rounding_correction", False))
            ),
            enable_missing_detail=bool(settings.get("enable_missing_detail", False)),
            enable_count_answer_detail=(
                bool(settings.get("enable_count_answer_detail", False))
            ),
            enable_average_calculation=(
                bool(settings.get("enable_average_calculation", False))
            ),
            enable_money_difference_calculation=(
                bool(settings.get("enable_money_difference_calculation", False))
            ),
            enable_date_endpoint_duration_calculation=(
                bool(
                    settings.get(
                        "enable_date_endpoint_duration_calculation",
                        False,
                    )
                )
            ),
            enable_relative_time_calculation=(
                bool(settings.get("enable_relative_time_calculation", False))
            ),
        )


def _neighbor_turns_for_rerank(
    store: RawEvidenceStore,
    turn: Any,
    *,
    window: int,
) -> tuple[Any, ...]:
    window = max(0, int(window))
    if window <= 0:
        return ()
    session_turns = store.session_turns(turn.session_id)
    positions = {
        candidate.source_id: index for index, candidate in enumerate(session_turns)
    }
    position = positions.get(turn.source_id)
    if position is None:
        return ()
    start = max(0, position - window)
    end = min(len(session_turns), position + window + 1)
    return tuple(
        candidate
        for candidate in session_turns[start:end]
        if candidate.source_id != turn.source_id
    )


def _memory_records_by_source(
    memory_hits: tuple[Any, ...],
) -> dict[str, tuple[Any, ...]]:
    records_by_source: dict[str, list[Any]] = {}
    seen_by_source: dict[str, set[str]] = {}
    for memory_hit in memory_hits:
        record = getattr(memory_hit, "record", None)
        if record is None:
            continue
        memory_id = str(getattr(record, "memory_id", id(record)))
        for source_id in getattr(record, "source_ids", ()) or ():
            seen = seen_by_source.setdefault(source_id, set())
            if memory_id in seen:
                continue
            seen.add(memory_id)
            records_by_source.setdefault(source_id, []).append(record)
    return {
        source_id: tuple(records)
        for source_id, records in records_by_source.items()
    }


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
    require_assistant_answer_source: bool = False,
    memory_types: tuple[str, ...] = (),
    source_order: str = "prepend",
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
    allowed_memory_types = {
        str(memory_type).strip().lower()
        for memory_type in memory_types
        if str(memory_type).strip()
    }

    for record in records:
        if allowed_memory_types and str(
            getattr(record, "memory_type", "") or ""
        ).strip().lower() not in allowed_memory_types:
            aligned_records.append(record)
            continue
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
            require_assistant_answer_source=require_assistant_answer_source,
        )
        if not aligned_source_ids:
            aligned_records.append(record)
            continue

        if source_order == "append":
            merged_candidates = (*source_ids, *aligned_source_ids)
        else:
            merged_candidates = (*aligned_source_ids, *source_ids)
        merged_source_ids = tuple(dict.fromkeys(merged_candidates))[:safe_limit]
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
    require_assistant_answer_source: bool = False,
) -> tuple[str, ...]:
    if not candidates:
        return ()
    original_set = set(original_source_ids)
    assistant_answer_origins: tuple[tuple[str, int], ...] = ()
    if require_assistant_answer_source:
        assistant_answer_origins = tuple(
            (turn.session_id, turn.turn_index)
            for turn in candidates
            if turn.source_id in original_set and _normalized_role(turn.role) == "user"
        )
        if not assistant_answer_origins:
            return ()
    record_text = _alignment_record_text(record)
    record_terms = _alignment_terms(record_text)
    record_numbers = set(re.findall(r"\b\d+(?:[.,]\d+)?\b", record_text.lower()))
    record_phrases = _alignment_phrases(record)
    scored = []
    for index, turn in enumerate(candidates):
        if require_assistant_answer_source and not _is_later_assistant_answer_turn(
            turn,
            assistant_answer_origins=assistant_answer_origins,
        ):
            continue
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


def _is_later_assistant_answer_turn(
    turn: Turn,
    *,
    assistant_answer_origins: tuple[tuple[str, int], ...],
) -> bool:
    if _normalized_role(turn.role) != "assistant":
        return False
    return any(
        session_id == turn.session_id and turn.turn_index > turn_index
        for session_id, turn_index in assistant_answer_origins
    )


def _normalized_role(role: str) -> str:
    return " ".join(str(role or "").strip().lower().split())


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


def _memory_lifecycle_manifest(
    *,
    question: str,
    route: RouteResult,
    built_memory_records: tuple[Any, ...],
    compiler_memory_records: tuple[Any, ...],
    evidence_rows: tuple[Any, ...],
) -> dict[str, Any]:
    """Trace-only lifecycle view over source-linked build memory.

    This manifest is deliberately not fed back into retrieval, compiler, answer,
    or repair. It makes typed-memory lifecycle state auditable without changing
    prediction behavior.
    """

    evidence_source_ids = {str(row.source_id) for row in evidence_rows}
    question_terms = _lifecycle_terms(question)
    built_stats = _memory_lifecycle_record_stats(
        built_memory_records,
        evidence_source_ids=evidence_source_ids,
    )
    activated_stats = _memory_lifecycle_record_stats(
        compiler_memory_records,
        evidence_source_ids=evidence_source_ids,
    )
    built_slot_items = _memory_lifecycle_slots(
        built_memory_records,
        question_terms=question_terms,
        evidence_source_ids=evidence_source_ids,
    )
    activated_slot_items = _memory_lifecycle_slots(
        compiler_memory_records,
        question_terms=question_terms,
        evidence_source_ids=evidence_source_ids,
    )
    state_update_organization = {
        "trace_only": True,
        "built": _state_update_organization_ledger(
            built_memory_records,
            question_terms=question_terms,
            evidence_source_ids=evidence_source_ids,
        ),
        "activated": _state_update_organization_ledger(
            compiler_memory_records,
            question_terms=question_terms,
            evidence_source_ids=evidence_source_ids,
        ),
        "clean_note": (
            "Trace-only state/update organization ledger. It separates "
            "source-backed superseded state chains from ordinary multi-value "
            "memory slots and is not used by prediction modules."
        ),
    }
    conflict_slots = sum(1 for item in built_slot_items if item["has_conflict"])
    visible_slots = sum(
        1 for item in built_slot_items if item["visible_source_count"] > 0
    )
    activated_conflict_slots = sum(
        1 for item in activated_slot_items if item["has_conflict"]
    )
    activated_visible_slots = sum(
        1 for item in activated_slot_items if item["visible_source_count"] > 0
    )
    return {
        "enabled": True,
        "trace_only": True,
        "information_need": route.information_need,
        "built_records": built_stats,
        "activated_records": activated_stats,
        "slot_count": len(built_slot_items),
        "visible_slot_count": visible_slots,
        "conflict_slot_count": conflict_slots,
        "slots": built_slot_items[:8],
        "activated_slot_count": len(activated_slot_items),
        "activated_visible_slot_count": activated_visible_slots,
        "activated_conflict_slot_count": activated_conflict_slots,
        "activated_slots": activated_slot_items[:8],
        "state_update_organization": state_update_organization,
        "note": (
            "Trace-only source-backed lifecycle manifest; not used by prediction "
            "modules."
        ),
    }


def _context_manifest(
    *,
    store: RawEvidenceStore,
    route: RouteResult,
    lexical_hits: tuple[Any, ...],
    dense_hits: tuple[Any, ...],
    memory_hits: tuple[Any, ...],
    memory_source_hits: tuple[Any, ...],
    memory_slot_chain_source_hits: tuple[Any, ...],
    turn_window_source_hits: tuple[Any, ...],
    pre_context_budget_hits: tuple[Any, ...],
    retrieval_hits: tuple[Any, ...],
    context_budget_trace: Mapping[str, Any],
    context_budget_audit: Mapping[str, Any],
    evidence_turns: tuple[Any, ...],
    selected_context: Mapping[str, Any],
    built_memory_records: tuple[Any, ...],
    compiler_memory_records: tuple[Any, ...],
    evidence_rows: tuple[Any, ...],
    compiled_context_chars: int | None = None,
    object_slot_source_hits: tuple[Any, ...] = (),
) -> dict[str, Any]:
    """Trace-only source flow manifest for memory/context organization.

    The manifest is a compact, normalized view over fields already available in
    the trace. It is intentionally not used by retrieval, compiler, answer,
    repair, finalizer, or cache keys.
    """

    final_evidence_source_ids = _source_ids_from_rows(evidence_rows)
    evidence_turn_source_ids = _source_ids_from_turns(evidence_turns)
    selected_context_source_ids = _ordered_unique(
        selected_context.get("materialized_source_ids") or ()
    )
    memory_projected_source_ids = _ordered_unique(
        (
            *_source_ids_from_hits(memory_source_hits),
            *_source_ids_from_hits(memory_slot_chain_source_hits),
            *_source_ids_from_hits(object_slot_source_hits),
        )
    )
    typed_memory_source_ids = _ordered_unique(
        source_id
        for record in compiler_memory_records
        for source_id in getattr(record, "source_ids", ()) or ()
    )
    final_set = set(final_evidence_source_ids)
    selected_set = set(selected_context_source_ids)
    memory_projected_set = set(memory_projected_source_ids)
    typed_memory_set = set(typed_memory_source_ids)
    context_budget_max_chars = context_budget_trace.get("max_chars")
    context_budget_estimated_chars = context_budget_trace.get("estimated_chars")
    try:
        context_budget_headroom_chars = (
            int(context_budget_max_chars) - int(context_budget_estimated_chars)
        )
    except (TypeError, ValueError):
        context_budget_headroom_chars = None
    selected_context_manifest = _selected_context_manifest(
        selected_context=selected_context,
        final_evidence_source_ids=final_evidence_source_ids,
        typed_memory_source_ids=typed_memory_source_ids,
        memory_projected_source_ids=memory_projected_source_ids,
    )
    return {
        "enabled": True,
        "trace_only": True,
        "information_need": route.information_need,
        "store": store.manifest(),
        "retrieval": {
            "lexical_hit_count": len(lexical_hits),
            "dense_hit_count": len(dense_hits),
            "memory_hit_count": len(memory_hits),
            "memory_projected_source_hit_count": len(memory_source_hits),
            "memory_slot_chain_source_hit_count": len(
                memory_slot_chain_source_hits
            ),
            "object_slot_source_hit_count": len(object_slot_source_hits),
            "turn_window_source_hit_count": len(turn_window_source_hits),
            "pre_context_budget_hit_count": len(pre_context_budget_hits),
            "final_hit_count": len(retrieval_hits),
            "context_budget_applied": bool(context_budget_trace.get("applied")),
            "context_budget_dropped_count": int(
                context_budget_trace.get("dropped_count") or 0
            ),
            "context_budget_safe_for_current_prompt": context_budget_audit.get(
                "safe_for_current_prompt"
            ),
        },
        "source_flow": {
            "lexical_source_ids": _source_ids_from_hits(lexical_hits),
            "dense_source_ids": _source_ids_from_hits(dense_hits),
            "memory_projected_source_ids": memory_projected_source_ids,
            "object_slot_source_ids": _source_ids_from_hits(
                object_slot_source_hits
            ),
            "turn_window_source_ids": _source_ids_from_hits(
                turn_window_source_hits
            ),
            "pre_context_budget_source_ids": _source_ids_from_hits(
                pre_context_budget_hits
            ),
            "context_budget_dropped_source_ids": list(
                context_budget_trace.get("dropped_source_ids") or ()
            ),
            "final_hit_source_ids": _source_ids_from_hits(retrieval_hits),
            "evidence_turn_source_ids": evidence_turn_source_ids,
            "final_evidence_source_ids": final_evidence_source_ids,
            "selected_context_source_ids": selected_context_source_ids,
        },
        "typed_memory": {
            "built": _memory_record_manifest(
                built_memory_records,
                final_evidence_source_ids=final_evidence_source_ids,
            ),
            "retrieved": _memory_hit_manifest(
                memory_hits,
                final_evidence_source_ids=final_evidence_source_ids,
            ),
            "compiler": _memory_record_manifest(
                compiler_memory_records,
                final_evidence_source_ids=final_evidence_source_ids,
            ),
        },
        "coverage": {
            "final_evidence_row_count": len(final_evidence_source_ids),
            "evidence_turn_count": len(evidence_turn_source_ids),
            "selected_context_final_row_count": len(final_set & selected_set),
            "final_evidence_from_memory_projection_count": len(
                final_set & memory_projected_set
            ),
            "final_evidence_from_typed_memory_source_count": len(
                final_set & typed_memory_set
            ),
            "typed_memory_source_count": len(typed_memory_source_ids),
            "selected_context_materialized_count": int(
                selected_context.get("materialized_count") or 0
            ),
        },
        "context_organization": {
            "trace_only": True,
            "prompt_context_chars": (
                int(compiled_context_chars)
                if compiled_context_chars is not None
                else None
            ),
            "context_budget": {
                "applied": bool(context_budget_trace.get("applied")),
                "max_chars": context_budget_max_chars,
                "estimated_chars": context_budget_estimated_chars,
                "headroom_chars": context_budget_headroom_chars,
                "dropped_count": int(context_budget_trace.get("dropped_count") or 0),
                "safe_for_current_prompt": context_budget_audit.get(
                    "safe_for_current_prompt"
                ),
            },
            "selected_context": selected_context_manifest,
            "evidence_pressure": _evidence_pressure_manifest(evidence_rows),
            "clean_note": (
                "Trace-only ledger for prompt-visible context organization. It "
                "summarizes source-backed selected-context risk and context "
                "pressure without changing prediction behavior."
            ),
        },
        "clean_note": (
            "Trace-only Context Manifest inspired by provenance-first memory "
            "systems. It summarizes already-selected sources and typed-memory "
            "activation; it does not alter prediction behavior."
        ),
    }


def _evidence_pressure_manifest(evidence_rows: tuple[Any, ...]) -> dict[str, Any]:
    """Summarize final evidence pressure without changing row selection.

    Agent-memory retrieval often returns correlated dialogue spans rather than
    independent documents. This trace-only ledger separates tail-rank pressure
    from source/span concentration so future pruning or rerank experiments can
    preserve raw evidence anchors and temporal neighbor chains.
    """

    row_count = len(evidence_rows)
    total_chars = 0
    session_counts: dict[str, int] = {}
    turn_indices_by_session: dict[str, list[int]] = {}
    tail_after_32 = {"row_count": 0, "char_count": 0, "source_ids": []}
    tail_after_40 = {"row_count": 0, "char_count": 0, "source_ids": []}

    for row in evidence_rows:
        source_id = str(getattr(row, "source_id", "") or "")
        session_id = str(getattr(row, "session_id", "") or "")
        text = str(getattr(row, "text", "") or "")
        total_chars += len(text)
        if session_id:
            session_counts[session_id] = session_counts.get(session_id, 0) + 1
        turn_index = getattr(row, "turn_index", None)
        if session_id and isinstance(turn_index, int):
            turn_indices_by_session.setdefault(session_id, []).append(turn_index)
        try:
            rank = int(getattr(row, "retrieval_rank", 0) or 0)
        except (TypeError, ValueError):
            rank = 0
        if rank > 32:
            tail_after_32["row_count"] += 1
            tail_after_32["char_count"] += len(text)
            if len(tail_after_32["source_ids"]) < 16:
                tail_after_32["source_ids"].append(source_id)
        if rank > 40:
            tail_after_40["row_count"] += 1
            tail_after_40["char_count"] += len(text)
            if len(tail_after_40["source_ids"]) < 16:
                tail_after_40["source_ids"].append(source_id)

    adjacent_pair_count = 0
    adjacent_session_count = 0
    for indices in turn_indices_by_session.values():
        ordered = sorted(set(indices))
        pairs = sum(1 for left, right in zip(ordered, ordered[1:]) if right == left + 1)
        adjacent_pair_count += pairs
        if pairs:
            adjacent_session_count += 1

    top_sessions = [
        {"session_id": session_id, "row_count": count}
        for session_id, count in sorted(
            session_counts.items(),
            key=lambda item: (-item[1], item[0]),
        )[:8]
    ]
    max_rows_per_session = max(session_counts.values(), default=0)
    concentration = (
        max_rows_per_session / row_count
        if row_count
        else 0.0
    )

    return {
        "trace_only": True,
        "row_count": row_count,
        "total_text_chars": total_chars,
        "session_count": len(session_counts),
        "max_rows_per_session": max_rows_per_session,
        "max_session_row_share": concentration,
        "top_sessions": top_sessions,
        "adjacent_turn_pair_count": adjacent_pair_count,
        "adjacent_turn_session_count": adjacent_session_count,
        "tail_after_rank_32": tail_after_32,
        "tail_after_rank_40": tail_after_40,
        "clean_note": (
            "Trace-only evidence pressure ledger inspired by xMemory "
            "decoupling/aggregation and hybrid retrieval systems. It is not "
            "used by prediction modules or cache keys."
        ),
    }


def _selected_context_manifest(
    *,
    selected_context: Mapping[str, Any],
    final_evidence_source_ids: tuple[str, ...],
    typed_memory_source_ids: tuple[str, ...],
    memory_projected_source_ids: tuple[str, ...],
) -> dict[str, Any]:
    risk_audit = selected_context.get("risk_audit") or {}
    materialized_source_ids = _ordered_unique(
        selected_context.get("materialized_source_ids") or ()
    )
    safe_source_ids = _ordered_unique(risk_audit.get("safe_source_ids") or ())
    risk_source_ids = _ordered_unique(risk_audit.get("risk_source_ids") or ())
    risk_reasons = {
        str(source_id): str(reason)
        for source_id, reason in (risk_audit.get("risk_reasons") or {}).items()
    }
    reason_counts: dict[str, int] = {}
    for reason in risk_reasons.values():
        reason_counts[reason] = reason_counts.get(reason, 0) + 1

    final_set = set(final_evidence_source_ids)
    typed_memory_set = set(typed_memory_source_ids)
    memory_projected_set = set(memory_projected_source_ids)
    materialized_set = set(materialized_source_ids)
    risk_set = set(risk_source_ids)
    safe_set = set(safe_source_ids)
    severity = _selected_context_source_flow_severity(
        risk_source_ids=risk_source_ids,
        final_evidence_source_ids=final_evidence_source_ids,
        typed_memory_source_ids=typed_memory_source_ids,
        memory_projected_source_ids=memory_projected_source_ids,
        risk_reasons=risk_reasons,
    )

    risk_details = []
    for source_id in risk_source_ids[:8]:
        risk_details.append(
            {
                "source_id": source_id,
                "reason": risk_reasons.get(source_id, "unknown"),
                "in_final_evidence": source_id in final_set,
                "from_typed_memory_source": source_id in typed_memory_set,
                "from_memory_projection": source_id in memory_projected_set,
            }
        )

    return {
        "trace_only": True,
        "enabled": bool(selected_context.get("enabled")),
        "applied": bool(selected_context.get("applied")),
        "eligible": bool(selected_context.get("eligible")),
        "skip_reason": selected_context.get("skip_reason"),
        "question_reference": bool(selected_context.get("question_reference")),
        "materialized_count": len(materialized_source_ids),
        "materialized_final_row_count": len(materialized_set & final_set),
        "materialized_from_typed_memory_source_count": len(
            materialized_set & typed_memory_set
        ),
        "materialized_from_memory_projection_count": len(
            materialized_set & memory_projected_set
        ),
        "risk_audit_applied": bool(risk_audit.get("applied")),
        "risk_count": len(risk_source_ids),
        "safe_count": len(safe_source_ids),
        "risk_reason_counts": dict(sorted(reason_counts.items())),
        "risk_final_row_count": len(risk_set & final_set),
        "risk_not_final_row_count": len(risk_set - final_set),
        "risk_from_typed_memory_source_count": len(risk_set & typed_memory_set),
        "risk_from_memory_projection_count": len(risk_set & memory_projected_set),
        "safe_final_row_count": len(safe_set & final_set),
        "safe_from_typed_memory_source_count": len(safe_set & typed_memory_set),
        "safe_from_memory_projection_count": len(safe_set & memory_projected_set),
        "source_flow_severity": severity,
        "materialized_source_ids": list(materialized_source_ids),
        "risk_source_ids": list(risk_source_ids),
        "safe_source_ids": list(safe_source_ids),
        "risk_details": risk_details,
        "text_source": risk_audit.get("text_source"),
        "materialized_text_audit_count": int(
            risk_audit.get("materialized_text_audit_count") or 0
        ),
        "raw_center_text_audit_count": int(
            risk_audit.get("raw_center_text_audit_count") or 0
        ),
    }


def _selected_context_source_flow_severity(
    *,
    risk_source_ids: tuple[str, ...],
    final_evidence_source_ids: tuple[str, ...],
    typed_memory_source_ids: tuple[str, ...],
    memory_projected_source_ids: tuple[str, ...],
    risk_reasons: Mapping[str, str],
) -> dict[str, Any]:
    """Classify selected-context audit rows without changing prediction.

    A row that looks risky by local question-term matching is much less safe to
    drop or reorder if it is also a final evidence row. This trace-only split
    keeps future gates from treating source-backed local context as disposable
    prompt noise.
    """

    final_set = set(final_evidence_source_ids)
    typed_memory_set = set(typed_memory_source_ids)
    memory_projected_set = set(memory_projected_source_ids)
    counts = {
        "raw_evidence_backed": 0,
        "typed_memory_backed": 0,
        "memory_projected_backed": 0,
        "not_final_evidence": 0,
    }
    guarded_rerank_eligible_source_ids: list[str] = []
    blocked_source_ids: list[str] = []
    details: list[dict[str, Any]] = []

    for source_id in risk_source_ids:
        in_final = source_id in final_set
        from_typed_memory = source_id in typed_memory_set
        from_memory_projection = source_id in memory_projected_set
        if in_final:
            counts["raw_evidence_backed"] += 1
            blocked_source_ids.append(source_id)
        else:
            counts["not_final_evidence"] += 1
            guarded_rerank_eligible_source_ids.append(source_id)
        if from_typed_memory:
            counts["typed_memory_backed"] += 1
        if from_memory_projection:
            counts["memory_projected_backed"] += 1
        if len(details) < 8:
            details.append(
                {
                    "source_id": source_id,
                    "reason": risk_reasons.get(source_id, "unknown"),
                    "in_final_evidence": in_final,
                    "from_typed_memory_source": from_typed_memory,
                    "from_memory_projection": from_memory_projection,
                    "guarded_rerank_eligible": not in_final,
                }
            )

    return {
        "trace_only": True,
        "counts": counts,
        "guarded_rerank_eligible_count": len(guarded_rerank_eligible_source_ids),
        "guarded_rerank_blocked_by_final_evidence_count": len(blocked_source_ids),
        "guarded_rerank_eligible_source_ids": guarded_rerank_eligible_source_ids[:16],
        "blocked_by_final_evidence_source_ids": blocked_source_ids[:16],
        "details": details,
        "clean_note": (
            "Trace-only severity for future guarded rerank/order decisions; "
            "rows already used as final evidence are not treated as safe tail "
            "noise solely because the local selected-context text has weak "
            "question-term overlap."
        ),
    }


def _memory_hit_manifest(
    memory_hits: tuple[Any, ...],
    *,
    final_evidence_source_ids: tuple[str, ...],
) -> dict[str, Any]:
    return _memory_record_manifest(
        tuple(
            record
            for hit in memory_hits
            for record in (getattr(hit, "record", None),)
            if record is not None
        ),
        final_evidence_source_ids=final_evidence_source_ids,
    )


def _memory_record_manifest(
    records: tuple[Any, ...],
    *,
    final_evidence_source_ids: tuple[str, ...],
) -> dict[str, Any]:
    final_set = set(final_evidence_source_ids)
    type_counts: dict[str, int] = {}
    status_counts: dict[str, int] = {}
    source_ids: list[str] = []
    visible_records = 0
    items: list[dict[str, Any]] = []
    for record in records:
        memory_type = str(getattr(record, "memory_type", "unknown") or "unknown")
        status = str(getattr(record, "status", "unknown") or "unknown")
        type_counts[memory_type] = type_counts.get(memory_type, 0) + 1
        status_counts[status] = status_counts.get(status, 0) + 1
        record_source_ids = tuple(str(source_id) for source_id in (
            getattr(record, "source_ids", ()) or ()
        ))
        source_ids.extend(record_source_ids)
        visible_source_ids = tuple(
            source_id for source_id in record_source_ids if source_id in final_set
        )
        if visible_source_ids:
            visible_records += 1
        if len(items) < 8:
            items.append(
                {
                    "memory_id": str(getattr(record, "memory_id", "")),
                    "memory_type": memory_type,
                    "status": status,
                    "source_ids": list(record_source_ids),
                    "visible_source_ids": list(visible_source_ids),
                }
            )
    unique_source_ids = _ordered_unique(source_ids)
    return {
        "record_count": len(records),
        "type_counts": dict(sorted(type_counts.items())),
        "status_counts": dict(sorted(status_counts.items())),
        "source_count": len(unique_source_ids),
        "visible_record_count": visible_records,
        "visible_source_count": len(set(unique_source_ids) & final_set),
        "records": items,
    }


def _source_ids_from_hits(hits: tuple[Any, ...]) -> tuple[str, ...]:
    return _ordered_unique(
        str(source_id)
        for hit in hits
        for source_id in (getattr(hit, "source_id", None),)
        if source_id
    )


def _source_ids_from_turns(turns: tuple[Any, ...]) -> tuple[str, ...]:
    return _ordered_unique(
        str(source_id)
        for turn in turns
        for source_id in (getattr(turn, "source_id", None),)
        if source_id
    )


def _source_ids_from_rows(rows: tuple[Any, ...]) -> tuple[str, ...]:
    return _ordered_unique(
        str(source_id)
        for row in rows
        for source_id in (getattr(row, "source_id", None),)
        if source_id
    )


def _ordered_unique(values: Any) -> tuple[str, ...]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = str(value)
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return tuple(result)


def _memory_lifecycle_record_stats(
    records: tuple[Any, ...],
    *,
    evidence_source_ids: set[str],
) -> dict[str, Any]:
    by_type: dict[str, int] = {}
    status_counts: dict[str, int] = {}
    source_linked = 0
    visible_source_linked = 0
    lifecycle_records = 0
    for record in records:
        memory_type = str(getattr(record, "memory_type", "") or "unknown")
        status = str(getattr(record, "status", "") or "active")
        by_type[memory_type] = by_type.get(memory_type, 0) + 1
        status_counts[status] = status_counts.get(status, 0) + 1
        source_ids = tuple(
            str(source_id) for source_id in getattr(record, "source_ids", ())
        )
        if source_ids:
            source_linked += 1
        if any(source_id in evidence_source_ids for source_id in source_ids):
            visible_source_linked += 1
        if memory_type in _LIFECYCLE_MEMORY_TYPES:
            lifecycle_records += 1
    return {
        "total": len(records),
        "lifecycle_total": lifecycle_records,
        "by_type": dict(sorted(by_type.items())),
        "status_counts": dict(sorted(status_counts.items())),
        "source_linked": source_linked,
        "visible_source_linked": visible_source_linked,
    }


def _memory_lifecycle_slots(
    records: tuple[Any, ...],
    *,
    question_terms: frozenset[str],
    evidence_source_ids: set[str],
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str], list[Any]] = {}
    for record in records:
        memory_type = str(getattr(record, "memory_type", "") or "unknown")
        if memory_type not in _LIFECYCLE_MEMORY_TYPES:
            continue
        subject = _lifecycle_field(getattr(record, "subject", ""))
        predicate = _lifecycle_field(getattr(record, "predicate", ""))
        if not subject and not predicate:
            continue
        grouped.setdefault((memory_type, subject, predicate), []).append(record)

    slots: list[dict[str, Any]] = []
    for (memory_type, subject, predicate), slot_records in grouped.items():
        active_values: list[str] = []
        superseded_values: list[str] = []
        source_ids: set[str] = set()
        visible_source_ids: set[str] = set()
        statuses: dict[str, int] = {}
        matched_terms: set[str] = set()
        for record in slot_records:
            status = str(getattr(record, "status", "") or "active")
            statuses[status] = statuses.get(status, 0) + 1
            value = _lifecycle_field(
                getattr(record, "value", "") or getattr(record, "text", "")
            )
            if value:
                if status == "superseded":
                    superseded_values.append(value)
                else:
                    active_values.append(value)
            for source_id in getattr(record, "source_ids", ()):
                source_id_text = str(source_id)
                source_ids.add(source_id_text)
                if source_id_text in evidence_source_ids:
                    visible_source_ids.add(source_id_text)
            matched_terms.update(
                question_terms.intersection(
                    _lifecycle_terms(
                        " ".join(
                            str(part)
                            for part in (
                                getattr(record, "subject", ""),
                                getattr(record, "predicate", ""),
                                getattr(record, "value", ""),
                                getattr(record, "text", ""),
                            )
                            if part
                        )
                    )
                )
            )
        distinct_values = set(active_values).union(superseded_values)
        has_conflict = len(distinct_values) > 1 or bool(superseded_values)
        slots.append(
            {
                "memory_type": memory_type,
                "subject": subject,
                "predicate": predicate,
                "record_count": len(slot_records),
                "status_counts": dict(sorted(statuses.items())),
                "active_values": sorted(set(active_values))[:4],
                "superseded_values": sorted(set(superseded_values))[:4],
                "source_count": len(source_ids),
                "visible_source_count": len(visible_source_ids),
                "has_conflict": has_conflict,
                "question_overlap_terms": sorted(matched_terms)[:8],
            }
        )
    slots.sort(
        key=lambda item: (
            not item["has_conflict"],
            -len(item["question_overlap_terms"]),
            -item["visible_source_count"],
            item["memory_type"],
            item["subject"],
            item["predicate"],
        )
    )
    return slots


def _state_update_organization_ledger(
    records: tuple[Any, ...],
    *,
    question_terms: frozenset[str],
    evidence_source_ids: set[str],
) -> dict[str, Any]:
    """Classify typed-memory slots without treating every multi-value as update.

    A real update/state chain has lifecycle evidence such as a superseded record,
    a valid_to boundary, or a superseded_by pointer. Multiple active values in a
    fact/profile slot can be a list, preference set, or extraction duplication,
    so it is traced separately and not promoted to state-conflict logic.
    """

    grouped: dict[tuple[str, str, str], list[Any]] = {}
    for record in records:
        memory_type = str(getattr(record, "memory_type", "") or "unknown")
        if memory_type not in _LIFECYCLE_MEMORY_TYPES:
            continue
        subject = _lifecycle_field(getattr(record, "subject", ""))
        predicate = _lifecycle_field(getattr(record, "predicate", ""))
        if not subject and not predicate:
            continue
        grouped.setdefault((memory_type, subject, predicate), []).append(record)

    items: list[dict[str, Any]] = []
    update_candidate_slot_count = 0
    update_candidate_visible_slot_count = 0
    update_candidate_missing_active_source_count = 0
    update_candidate_missing_superseded_source_count = 0
    multi_active_stateful_slot_count = 0
    non_stateful_multi_value_slot_count = 0
    non_stateful_multi_value_visible_slot_count = 0
    source_linked_slot_count = 0
    visible_slot_count = 0

    for (memory_type, subject, predicate), slot_records in grouped.items():
        status_counts: dict[str, int] = {}
        active_values: set[str] = set()
        superseded_values: set[str] = set()
        active_source_ids: set[str] = set()
        superseded_source_ids: set[str] = set()
        source_ids: set[str] = set()
        visible_source_ids: set[str] = set()
        question_overlap_terms: set[str] = set()
        lifecycle_update_signal = False

        for record in slot_records:
            status = str(getattr(record, "status", "") or "active")
            status_counts[status] = status_counts.get(status, 0) + 1
            value = _lifecycle_field(
                getattr(record, "value", "") or getattr(record, "text", "")
            )
            record_source_ids = {
                str(source_id) for source_id in getattr(record, "source_ids", ())
            }
            source_ids.update(record_source_ids)
            visible_source_ids.update(record_source_ids & evidence_source_ids)
            if status == "superseded":
                if value:
                    superseded_values.add(value)
                superseded_source_ids.update(record_source_ids)
            else:
                if value:
                    active_values.add(value)
                active_source_ids.update(record_source_ids)
            if (
                status == "superseded"
                or getattr(record, "superseded_by", None)
                or getattr(record, "valid_to", None)
            ):
                lifecycle_update_signal = True
            question_overlap_terms.update(
                question_terms.intersection(
                    _lifecycle_terms(
                        " ".join(
                            str(part)
                            for part in (
                                getattr(record, "subject", ""),
                                getattr(record, "predicate", ""),
                                getattr(record, "value", ""),
                                getattr(record, "text", ""),
                            )
                            if part
                        )
                    )
                )
            )

        source_linked = bool(source_ids)
        visible = bool(visible_source_ids)
        if source_linked:
            source_linked_slot_count += 1
        if visible:
            visible_slot_count += 1

        distinct_values = active_values | superseded_values
        update_candidate = (
            memory_type in _STATE_UPDATE_MEMORY_TYPES
            and lifecycle_update_signal
            and bool(distinct_values)
        )
        multi_active_stateful = (
            memory_type in _STATE_UPDATE_MEMORY_TYPES
            and len(active_values) > 1
            and not lifecycle_update_signal
        )
        non_stateful_multi_value = (
            not update_candidate
            and not multi_active_stateful
            and len(distinct_values) > 1
        )

        if update_candidate:
            update_candidate_slot_count += 1
            if visible:
                update_candidate_visible_slot_count += 1
            if active_source_ids and not (active_source_ids & evidence_source_ids):
                update_candidate_missing_active_source_count += 1
            if superseded_source_ids and not (
                superseded_source_ids & evidence_source_ids
            ):
                update_candidate_missing_superseded_source_count += 1
        if multi_active_stateful:
            multi_active_stateful_slot_count += 1
        if non_stateful_multi_value:
            non_stateful_multi_value_slot_count += 1
            if visible:
                non_stateful_multi_value_visible_slot_count += 1

        if update_candidate or multi_active_stateful or non_stateful_multi_value:
            items.append(
                {
                    "memory_type": memory_type,
                    "subject": subject,
                    "predicate": predicate,
                    "record_count": len(slot_records),
                    "status_counts": dict(sorted(status_counts.items())),
                    "active_values": sorted(active_values)[:4],
                    "superseded_values": sorted(superseded_values)[:4],
                    "source_count": len(source_ids),
                    "visible_source_count": len(visible_source_ids),
                    "active_source_visible": bool(
                        active_source_ids & evidence_source_ids
                    ),
                    "superseded_source_visible": bool(
                        superseded_source_ids & evidence_source_ids
                    ),
                    "state_update_candidate": update_candidate,
                    "multi_active_stateful": multi_active_stateful,
                    "non_stateful_multi_value": non_stateful_multi_value,
                    "question_overlap_terms": sorted(question_overlap_terms)[:8],
                }
            )

    items.sort(
        key=lambda item: (
            not item["state_update_candidate"],
            not item["multi_active_stateful"],
            not item["non_stateful_multi_value"],
            -len(item["question_overlap_terms"]),
            -item["visible_source_count"],
            item["memory_type"],
            item["subject"],
            item["predicate"],
        )
    )
    return {
        "slot_count": len(grouped),
        "source_linked_slot_count": source_linked_slot_count,
        "visible_slot_count": visible_slot_count,
        "state_update_candidate_slot_count": update_candidate_slot_count,
        "state_update_candidate_visible_slot_count": (
            update_candidate_visible_slot_count
        ),
        "state_update_missing_active_source_count": (
            update_candidate_missing_active_source_count
        ),
        "state_update_missing_superseded_source_count": (
            update_candidate_missing_superseded_source_count
        ),
        "multi_active_stateful_slot_count": multi_active_stateful_slot_count,
        "non_stateful_multi_value_slot_count": non_stateful_multi_value_slot_count,
        "non_stateful_multi_value_visible_slot_count": (
            non_stateful_multi_value_visible_slot_count
        ),
        "items": items[:8],
    }


def _lifecycle_field(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def _lifecycle_terms(text: str) -> frozenset[str]:
    terms = []
    for match in _LIFECYCLE_TERM_PATTERN.finditer(text or ""):
        term = match.group(0).lower()
        if len(term) < 3 or term in _LIFECYCLE_TERM_STOPWORDS:
            continue
        terms.append(term)
    return frozenset(terms)


def _memory_slot_chain_applies(
    *,
    enabled: bool,
    route: RouteResult,
    information_needs: tuple[str, ...],
) -> bool:
    if not enabled:
        return False
    if information_needs and route.information_need not in information_needs:
        return False
    return route.information_need in {"current_state", "profile_preference"}


def _object_slot_activation_applies(
    *,
    enabled: bool,
    route: RouteResult,
    information_needs: tuple[str, ...],
) -> bool:
    if not enabled:
        return False
    if information_needs and route.information_need not in information_needs:
        return False
    return route.information_need in {
        "current_state",
        "fact_lookup",
        "list_count",
        "profile_preference",
    }


def _disabled_object_slot_activation_trace(
    *,
    enabled: bool,
    information_needs: tuple[str, ...],
    memory_types: tuple[str, ...],
    max_slots: int,
    max_sources_per_slot: int,
    min_overlap_terms: int,
    require_collection_slot: bool,
    skipped_reason: str = "",
) -> dict[str, Any]:
    return {
        "enabled": enabled,
        "applied": False,
        "information_needs": information_needs,
        "memory_types": memory_types,
        "max_slots": max_slots,
        "max_sources_per_slot": max_sources_per_slot,
        "min_overlap_terms": min_overlap_terms,
        "require_collection_slot": require_collection_slot,
        "skipped_reason": skipped_reason,
        "slots": [],
    }


def _memory_object_slot_source_hits(
    *,
    memory_hits: tuple[Any, ...],
    built_memory_records: tuple[Any, ...],
    question: str,
    route: RouteResult,
    available_source_ids: set[str],
    max_slots: int,
    max_sources_per_slot: int,
    memory_types: tuple[str, ...],
    min_overlap_terms: int = 1,
    require_collection_slot: bool = True,
) -> tuple[tuple[RetrievalHit, ...], dict[str, Any]]:
    """Expand a matched build-memory object slot back to raw source rows.

    This uses derived memory only as a source-backed index. It never exposes
    typed memory text as final evidence and never drops existing retrieval hits.
    """

    trace = _disabled_object_slot_activation_trace(
        enabled=True,
        information_needs=(route.information_need,),
        memory_types=memory_types,
        max_slots=max_slots,
        max_sources_per_slot=max_sources_per_slot,
        min_overlap_terms=min_overlap_terms,
        require_collection_slot=require_collection_slot,
    )
    if not memory_hits or not built_memory_records:
        return (), trace
    if max_slots <= 0 or max_sources_per_slot <= 0:
        return (), {**trace, "skipped_reason": "non_positive_budget"}

    question_terms = _memory_object_slot_question_terms(question)
    if not question_terms:
        return (), {**trace, "skipped_reason": "no_question_terms"}

    groups: dict[tuple[str, str, str], list[Any]] = {}
    for record in built_memory_records:
        key = _memory_object_slot_key(record, memory_types=memory_types)
        if key is None:
            continue
        groups.setdefault(key, []).append(record)

    selected_hits: list[RetrievalHit] = []
    slot_traces: list[dict[str, Any]] = []
    seen_sources: set[str] = set()
    seen_keys: set[tuple[str, str, str]] = set()
    rank = 1
    for memory_hit in memory_hits:
        if len(slot_traces) >= max_slots:
            break
        record = getattr(memory_hit, "record", None)
        key = _memory_object_slot_key(record, memory_types=memory_types)
        if key is None or key in seen_keys:
            continue
        seen_keys.add(key)
        records = tuple(groups.get(key, ()))
        if require_collection_slot and not _is_memory_object_collection_slot(records):
            continue
        matched_terms = _memory_object_slot_matched_terms(
            question_terms=question_terms,
            key=key,
            records=records,
        )
        if len(matched_terms) < max(0, min_overlap_terms):
            continue

        source_ids = _memory_object_slot_sources(
            records,
            available_source_ids=available_source_ids,
            max_sources=max_sources_per_slot,
        )
        if not source_ids:
            continue

        base_score = float(getattr(memory_hit, "score", 0.0) or 0.0)
        emitted_sources: list[str] = []
        for offset, source_id in enumerate(source_ids):
            if source_id in seen_sources:
                continue
            seen_sources.add(source_id)
            emitted_sources.append(source_id)
            selected_hits.append(
                RetrievalHit(
                    source_id=source_id,
                    score=base_score - (offset * 1e-6),
                    rank=rank,
                    retriever="build_memory_object_slot",
                    matched_terms=matched_terms,
                )
            )
            rank += 1
        if not emitted_sources:
            continue

        slot_traces.append(
            {
                "slot": {
                    "memory_type": key[0],
                    "subject": key[1],
                    "predicate": key[2],
                },
                "matched_memory_id": str(getattr(record, "memory_id", "")),
                "matched_terms": matched_terms,
                "record_count": len(records),
                "source_ids": tuple(emitted_sources),
                "values": _memory_object_slot_values(records)[:6],
            }
        )

    return tuple(selected_hits), {
        **trace,
        "applied": bool(slot_traces),
        "slots": slot_traces,
    }


def _memory_object_slot_key(
    record: Any,
    *,
    memory_types: tuple[str, ...],
) -> tuple[str, str, str] | None:
    if record is None:
        return None
    memory_type = str(getattr(record, "memory_type", "") or "").lower()
    allowed_types = {item.lower() for item in memory_types} if memory_types else {
        "event",
        "fact",
        "plan",
        "preference",
        "profile",
        "relationship",
        "state",
    }
    if memory_type not in allowed_types:
        return None
    subject = _normalize_memory_slot_text(str(getattr(record, "subject", "") or ""))
    predicate = _normalize_memory_slot_text(str(getattr(record, "predicate", "") or ""))
    if not subject or not predicate:
        return None
    return (memory_type, subject, predicate)


def _is_memory_object_collection_slot(records: tuple[Any, ...]) -> bool:
    if len(records) < 2:
        return False
    return len(_memory_object_slot_values(records)) > 1


def _memory_object_slot_matched_terms(
    *,
    question_terms: frozenset[str],
    key: tuple[str, str, str],
    records: tuple[Any, ...],
) -> tuple[str, ...]:
    _memory_type, subject, _predicate = key
    subject_terms = _memory_slot_chain_text_terms(subject)
    scoped_question_terms = question_terms.difference(subject_terms)
    if not scoped_question_terms:
        return ()
    slot_terms: set[str] = set()
    for record in records:
        slot_terms.update(
            _memory_slot_chain_text_terms(
                " ".join(
                    str(part)
                    for part in (
                        getattr(record, "predicate", "") or "",
                        getattr(record, "value", "") or "",
                        getattr(record, "text", "") or "",
                        " ".join(tuple(getattr(record, "entities", ()) or ())),
                    )
                    if part
                )
            )
        )
    return tuple(sorted(scoped_question_terms.intersection(slot_terms)))


def _memory_object_slot_sources(
    records: tuple[Any, ...],
    *,
    available_source_ids: set[str],
    max_sources: int,
) -> tuple[str, ...]:
    selected: list[str] = []
    for record in sorted(records, key=_memory_object_slot_record_sort_key):
        for source_id in tuple(getattr(record, "source_ids", ()) or ()):
            source_id = str(source_id)
            if source_id not in available_source_ids or source_id in selected:
                continue
            selected.append(source_id)
            if len(selected) >= max_sources:
                return tuple(selected)
    return tuple(selected)


def _memory_object_slot_values(records: tuple[Any, ...]) -> tuple[str, ...]:
    values: list[str] = []
    seen: set[str] = set()
    for record in records:
        value = _normalize_memory_slot_text(
            str(getattr(record, "value", "") or getattr(record, "text", "") or "")
        )
        if not value or value in seen:
            continue
        seen.add(value)
        values.append(value)
    return tuple(values)


def _memory_object_slot_question_terms(question: str) -> frozenset[str]:
    return _memory_slot_chain_question_terms(question)


def _memory_object_slot_record_sort_key(record: Any) -> tuple[int, str, str]:
    status = str(getattr(record, "status", "active") or "active")
    status_rank = 0 if status == "active" else 1
    time_value = (
        getattr(record, "valid_from", None)
        or getattr(record, "timestamp", None)
        or getattr(record, "mention_time", None)
        or ""
    )
    return (status_rank, str(time_value), str(getattr(record, "memory_id", "")))


def _disabled_memory_slot_chain_trace(
    *,
    enabled: bool,
    information_needs: tuple[str, ...],
    max_chains: int,
    max_sources_per_chain: int,
    memory_types: tuple[str, ...],
    question_scope_gate: bool = False,
    source_policy: str = "all",
    question_scope: str = "unspecified",
    skipped_reason: str = "",
) -> dict[str, Any]:
    return {
        "enabled": enabled,
        "applied": False,
        "information_needs": information_needs,
        "max_chains": max_chains,
        "max_sources_per_chain": max_sources_per_chain,
        "memory_types": memory_types,
        "question_scope_gate": question_scope_gate,
        "source_policy": source_policy,
        "question_scope": question_scope,
        "skipped_reason": skipped_reason,
        "chains": [],
    }


def _memory_slot_chain_source_hits(
    *,
    memory_hits: tuple[Any, ...],
    built_memory_records: tuple[Any, ...],
    route: RouteResult,
    available_source_ids: set[str],
    max_chains: int,
    max_sources_per_chain: int,
    memory_types: tuple[str, ...],
    question: str = "",
    question_scope_gate: bool = False,
    source_policy: str = "all",
) -> tuple[tuple[RetrievalHit, ...], dict[str, Any]]:
    question_scope = _memory_slot_chain_question_scope(question)
    question_terms = _memory_slot_chain_question_terms(question)
    trace = _disabled_memory_slot_chain_trace(
        enabled=True,
        information_needs=(route.information_need,),
        max_chains=max_chains,
        max_sources_per_chain=max_sources_per_chain,
        memory_types=memory_types,
        question_scope_gate=question_scope_gate,
        source_policy=source_policy,
        question_scope=question_scope,
    )
    if question_scope_gate and question_scope == "unspecified":
        return (), {
            **trace,
            "skipped_reason": "question_scope_unspecified",
        }
    if not memory_hits or not built_memory_records:
        return (), trace

    groups: dict[tuple[str, str, str], list[Any]] = {}
    for record in built_memory_records:
        key = _memory_slot_chain_key(record, route=route, memory_types=memory_types)
        if key is None:
            continue
        groups.setdefault(key, []).append(record)

    selected_hits: list[RetrievalHit] = []
    chain_traces: list[dict[str, Any]] = []
    seen_sources: set[str] = set()
    seen_keys: set[tuple[str, str, str]] = set()
    rank = 1
    for memory_hit in memory_hits:
        if len(chain_traces) >= max(0, max_chains):
            break
        record = getattr(memory_hit, "record", None)
        key = _memory_slot_chain_key(record, route=route, memory_types=memory_types)
        if key is None or key in seen_keys:
            continue
        seen_keys.add(key)
        records = tuple(groups.get(key, ()))
        if not _is_memory_slot_chain(records):
            continue

        source_ids = _memory_slot_chain_sources(
            records,
            available_source_ids=available_source_ids,
            max_sources=max_sources_per_chain,
            question_scope=question_scope,
            question_terms=question_terms,
            source_policy=source_policy,
        )
        if not source_ids:
            continue

        chain_memory_ids = tuple(
            str(getattr(item, "memory_id", "")) for item in records
        )
        chain_statuses = tuple(str(getattr(item, "status", "active")) for item in records)
        chain_traces.append(
            {
                "slot": {
                    "memory_type": key[0],
                    "subject": key[1],
                    "predicate": key[2],
                },
                "matched_memory_id": str(getattr(record, "memory_id", "")),
                "question_scope": question_scope,
                "source_policy": source_policy,
                "memory_ids": chain_memory_ids,
                "statuses": chain_statuses,
                "source_ids": source_ids,
            }
        )

        base_score = float(getattr(memory_hit, "score", 0.0) or 0.0)
        for offset, source_id in enumerate(source_ids):
            if source_id in seen_sources:
                continue
            seen_sources.add(source_id)
            selected_hits.append(
                RetrievalHit(
                    source_id=source_id,
                    score=base_score - (offset * 1e-6),
                    rank=rank,
                    retriever="build_memory_slot_chain",
                    matched_terms=tuple(getattr(memory_hit, "matched_terms", ()) or ()),
                )
            )
            rank += 1

    return tuple(selected_hits), {
        **trace,
        "applied": bool(chain_traces),
        "chains": chain_traces,
    }


def _memory_slot_chain_key(
    record: Any,
    *,
    route: RouteResult,
    memory_types: tuple[str, ...],
) -> tuple[str, str, str] | None:
    if record is None:
        return None
    memory_type = str(getattr(record, "memory_type", "") or "").lower()
    allowed_types = {item.lower() for item in memory_types} if memory_types else {
        "preference",
        "profile",
        "relationship",
        "state",
    }
    if memory_type not in allowed_types:
        return None
    if route.information_need == "current_state" and memory_type not in {
        "preference",
        "profile",
        "relationship",
        "state",
    }:
        return None
    if route.information_need == "profile_preference" and memory_type not in {
        "preference",
        "profile",
        "relationship",
        "state",
    }:
        return None
    subject = _normalize_memory_slot_text(str(getattr(record, "subject", "") or ""))
    predicate = _normalize_memory_slot_text(str(getattr(record, "predicate", "") or ""))
    if not subject or not predicate:
        return None
    return (memory_type, subject, predicate)


def _is_memory_slot_chain(records: tuple[Any, ...]) -> bool:
    if len(records) < 2:
        return False
    values = {
        _normalize_memory_slot_text(
            str(getattr(record, "value", "") or getattr(record, "text", "") or "")
        )
        for record in records
    }
    statuses = {str(getattr(record, "status", "active") or "active") for record in records}
    return len(values) > 1 or "superseded" in statuses


def _memory_slot_chain_sources(
    records: tuple[Any, ...],
    *,
    available_source_ids: set[str],
    max_sources: int,
    question_scope: str = "unspecified",
    question_terms: frozenset[str] = frozenset(),
    source_policy: str = "all",
) -> tuple[str, ...]:
    if max_sources <= 0:
        return ()
    selected: list[str] = []
    ordered_records = sorted(records, key=_memory_slot_chain_record_sort_key)
    if source_policy == "query_scope":
        ordered_records = _query_scoped_memory_slot_chain_records(
            tuple(ordered_records),
            question_scope=question_scope,
            question_terms=question_terms,
        )
    for record in ordered_records:
        for source_id in tuple(getattr(record, "source_ids", ()) or ()):
            source_id = str(source_id)
            if source_id not in available_source_ids or source_id in selected:
                continue
            selected.append(source_id)
            if len(selected) >= max_sources:
                return tuple(selected)
    return tuple(selected)


def _query_scoped_memory_slot_chain_records(
    records: tuple[Any, ...],
    *,
    question_scope: str,
    question_terms: frozenset[str],
) -> list[Any]:
    matched_records = [
        record
        for record in records
        if _memory_slot_chain_record_matches_question(record, question_terms)
    ]
    if question_scope == "current":
        return [
            record
            for record in matched_records
            if str(getattr(record, "status", "active") or "active") == "active"
        ]
    if question_scope == "historical":
        return [
            record
            for record in matched_records
            if str(getattr(record, "status", "active") or "active") != "active"
        ]
    return list(matched_records)


def _memory_slot_chain_question_scope(question: str) -> str:
    lowered = question.lower()
    current = bool(
        re.search(
            r"\b(current|currently|latest|most recent|recently|recent|now|"
            r"today|still|as of|these days|at present|present)\b",
            lowered,
        )
        or re.search(r"(当前|现在|目前|最新|最近|今天|仍然)", question)
    )
    historical = bool(
        re.search(
            r"\b(previous|previously|former|formerly|original|originally|"
            r"initial|initially|earlier|prior|before|used to|old)\b",
            lowered,
        )
        or re.search(r"(之前|以前|原来|原本|最初|过去|曾经|上次)", question)
    )
    change = bool(
        re.search(
            r"\b(changed|updated|switched|moved|became|no longer|instead|"
            r"correction|corrected|actually)\b",
            lowered,
        )
        or re.search(r"(更新|改变|变化|换成|搬到|变成|不再|纠正|其实)", question)
    )
    if change or (current and historical):
        return "change"
    if current:
        return "current"
    if historical:
        return "historical"
    return "unspecified"


def _memory_slot_chain_record_matches_question(
    record: Any,
    question_terms: frozenset[str],
) -> bool:
    if not question_terms:
        return False
    subject_terms = _memory_slot_chain_text_terms(
        str(getattr(record, "subject", "") or "")
    )
    scoped_question_terms = question_terms.difference(subject_terms)
    if not scoped_question_terms:
        return False
    record_terms = _memory_slot_chain_text_terms(
        " ".join(
            str(part)
            for part in (
                getattr(record, "predicate", "") or "",
                getattr(record, "value", "") or "",
                getattr(record, "text", "") or "",
                " ".join(tuple(getattr(record, "entities", ()) or ())),
            )
            if part
        )
    ).difference(subject_terms)
    return bool(scoped_question_terms.intersection(record_terms))


def _memory_slot_chain_question_terms(question: str) -> frozenset[str]:
    weak_terms = {
        "a",
        "about",
        "after",
        "all",
        "an",
        "and",
        "any",
        "are",
        "as",
        "at",
        "be",
        "been",
        "before",
        "could",
        "current",
        "currently",
        "did",
        "do",
        "does",
        "day",
        "days",
        "earliest",
        "event",
        "events",
        "for",
        "from",
        "had",
        "has",
        "have",
        "her",
        "his",
        "how",
        "i",
        "in",
        "is",
        "it",
        "latest",
        "long",
        "me",
        "month",
        "months",
        "most",
        "my",
        "now",
        "of",
        "on",
        "or",
        "order",
        "our",
        "participated",
        "past",
        "previous",
        "recent",
        "recently",
        "remind",
        "still",
        "the",
        "their",
        "they",
        "to",
        "today",
        "was",
        "were",
        "week",
        "weeks",
        "what",
        "when",
        "where",
        "which",
        "who",
        "whom",
        "why",
        "would",
        "year",
        "years",
        "you",
        "your",
    }
    return frozenset(_memory_slot_chain_text_terms(question).difference(weak_terms))


def _memory_slot_chain_text_terms(value: str) -> set[str]:
    normalized = re.sub(r"[_/\\-]+", " ", value.lower())
    terms: set[str] = set()
    for token in re.findall(r"[a-z0-9]+", normalized):
        if len(token) <= 1:
            continue
        terms.add(token)
        if token.endswith("ves") and len(token) > 4:
            terms.add(token[:-1])
        if token.endswith("ies") and len(token) > 4:
            terms.add(token[:-3] + "y")
        if token.endswith("ed") and len(token) > 4:
            terms.add(token[:-1])
            terms.add(token[:-2])
        if token.endswith("ing") and len(token) > 5:
            terms.add(token[:-3])
        if token.endswith("s") and len(token) > 3:
            terms.add(token[:-1])
    return terms


def _memory_slot_chain_record_sort_key(record: Any) -> tuple[int, str, str]:
    status = str(getattr(record, "status", "active") or "active")
    status_rank = 0 if status == "active" else 1
    time_value = (
        getattr(record, "valid_from", None)
        or getattr(record, "timestamp", None)
        or getattr(record, "mention_time", None)
        or ""
    )
    return (status_rank, str(time_value), str(getattr(record, "memory_id", "")))


def _normalize_memory_slot_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


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


def _rerank_skip_reason(
    *,
    route: RouteResult,
    enabled_information_needs: tuple[str, ...],
    top_k: int,
    min_effective_top_k: int,
) -> str | None:
    if not _rerank_applies(
        route=route,
        enabled_information_needs=enabled_information_needs,
    ):
        return "information_need_not_enabled"
    if min_effective_top_k > 0 and top_k < min_effective_top_k:
        return "top_k_below_min_effective_top_k"
    return None


def _rerank_exchange_guard(
    *,
    store: RawEvidenceStore,
    question: str,
    hits: tuple[RetrievalHit, ...],
    top_k: int,
    return_top_k: int,
    selection_mode: str,
    anchor_keep: int,
    protected_source_ids: tuple[str, ...],
    enabled: bool,
    protect_memory_sources: bool,
    protect_adjacent_session: bool,
    question_overlap_min_terms: int,
) -> tuple[str | None, dict[str, Any]]:
    if not enabled:
        return None, {"enabled": False}
    trace: dict[str, Any] = {
        "enabled": True,
        "selection_mode": selection_mode,
        "top_k": top_k,
        "return_top_k": return_top_k,
        "anchor_keep": anchor_keep,
        "protect_memory_sources": protect_memory_sources,
        "protect_adjacent_session": protect_adjacent_session,
        "protect_question_overlap_min_terms": question_overlap_min_terms,
        "reason": None,
    }
    if selection_mode != "filter_preserve_order":
        trace["reason"] = "selection_mode_not_supported"
        return None, trace
    if return_top_k <= 0 or return_top_k >= top_k:
        trace["reason"] = "no_tail_exchange"
        return None, trace
    if not hits:
        trace["reason"] = "no_hits"
        return None, trace

    anchor_count = max(0, min(anchor_keep, len(hits), return_top_k))
    exchangeable_hits = hits[anchor_count:return_top_k]
    exchangeable_source_ids = tuple(hit.source_id for hit in exchangeable_hits)
    trace["exchangeable_source_ids"] = exchangeable_source_ids[:16]
    trace["exchangeable_count"] = len(exchangeable_source_ids)
    trace["protected_source_ids"] = protected_source_ids[:16]
    if not exchangeable_hits:
        trace["reason"] = "no_exchangeable_tail"
        return None, trace

    protected_set = set(protected_source_ids)
    if protect_memory_sources:
        protected_tail = tuple(
            source_id
            for source_id in exchangeable_source_ids
            if source_id in protected_set
        )
        trace["protected_memory_source_ids"] = protected_tail[:16]
        if protected_tail:
            trace["reason"] = "exchange_tail_protected_memory_source"
            return trace["reason"], trace

    top_window_ids = tuple(hit.source_id for hit in hits[:top_k])
    top_window_set = set(top_window_ids)
    exchangeable_set = set(exchangeable_source_ids)
    if protect_adjacent_session:
        adjacent_pairs: list[dict[str, Any]] = []
        for hit in exchangeable_hits:
            turn = store.get(hit.source_id)
            if turn is None:
                continue
            for neighbor in store.session_turns(turn.session_id):
                if abs(int(neighbor.turn_index) - int(turn.turn_index)) != 1:
                    continue
                if neighbor.source_id not in top_window_set:
                    continue
                if neighbor.source_id in exchangeable_set:
                    continue
                adjacent_pairs.append(
                    {
                        "source_id": hit.source_id,
                        "neighbor_source_id": neighbor.source_id,
                        "session_id": turn.session_id,
                    }
                )
                break
        trace["adjacent_session_pairs"] = adjacent_pairs[:16]
        if adjacent_pairs:
            trace["reason"] = "exchange_tail_protected_adjacent_session"
            return trace["reason"], trace

    if question_overlap_min_terms > 0:
        question_terms = _lifecycle_terms(question)
        overlap_items: list[dict[str, Any]] = []
        for hit in exchangeable_hits:
            turn = store.get(hit.source_id)
            if turn is None:
                continue
            overlap = tuple(sorted(question_terms & _lifecycle_terms(turn.text)))
            if len(overlap) < question_overlap_min_terms:
                continue
            overlap_items.append(
                {
                    "source_id": hit.source_id,
                    "overlap_terms": overlap[:8],
                }
            )
        trace["question_overlap_items"] = overlap_items[:16]
        if overlap_items:
            trace["reason"] = "exchange_tail_protected_question_overlap"
            return trace["reason"], trace

    trace["reason"] = "allowed"
    return None, trace


def _disabled_rerank_trace(
    *,
    enabled: bool,
    information_needs: tuple[str, ...],
    min_effective_top_k: int = 0,
    skipped_reason: str | None = None,
    return_top_k: int = 0,
    exchange_guard_enabled: bool = False,
    exchange_guard: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "enabled": enabled,
        "applied": False,
        "information_needs": information_needs,
        "min_effective_top_k": min_effective_top_k,
        "return_top_k": return_top_k,
        "exchange_guard_enabled": exchange_guard_enabled,
        "exchange_guard": exchange_guard,
        "candidate_count": 0,
        "returned_count": 0,
        "total_tokens": 0,
        "skipped_reason": skipped_reason,
        "response": None,
    }


def _context_budget_applies(
    *,
    route: RouteResult,
    enabled: bool,
    max_chars: int,
    information_needs: tuple[str, ...],
) -> bool:
    if not enabled or max_chars <= 0:
        return False
    if not information_needs:
        return True
    return route.information_need in information_needs


def _disabled_context_budget_trace(
    *,
    enabled: bool,
    max_chars: int,
    min_hits: int,
    protect_top_n: int,
    max_hits: int,
    information_needs: tuple[str, ...],
) -> dict[str, Any]:
    return {
        "enabled": enabled,
        "applied": False,
        "max_chars": max_chars,
        "min_hits": min_hits,
        "protect_top_n": protect_top_n,
        "max_hits": max_hits,
        "information_needs": information_needs,
        "candidate_count": 0,
        "returned_count": 0,
        "estimated_chars": 0,
        "dropped_count": 0,
        "dropped_source_ids": [],
    }


def _disabled_context_budget_audit_trace(
    *,
    enabled: bool,
    max_chars: int,
    min_hits: int,
    protect_top_n: int,
    max_hits: int,
    information_needs: tuple[str, ...],
) -> dict[str, Any]:
    return {
        "enabled": enabled,
        "trace_only": True,
        "applied": False,
        "reason": "disabled" if not enabled else "not_applicable",
        "max_chars": max_chars,
        "min_hits": min_hits,
        "protect_top_n": protect_top_n,
        "max_hits": max_hits,
        "information_needs": information_needs,
        "candidate_count": 0,
        "projected_returned_count": 0,
        "projected_estimated_chars": 0,
        "projected_dropped_count": 0,
        "projected_dropped_source_ids": [],
        "projected_available_source_count": 0,
        "prompt_row_count": 0,
        "prompt_rows_missing_count": 0,
        "prompt_rows_missing_source_ids": [],
        "selected_context_materialized_count": 0,
        "selected_context_missing_count": 0,
        "selected_context_missing_source_ids": [],
        "safe_for_current_prompt": None,
        "clean_note": (
            "Trace-only simulation of retrieval context-budget pressure. It is not "
            "included in retrieval, compiler, answer, repair, finalizer, or cache keys."
        ),
    }


def _apply_context_budget(
    *,
    store: RawEvidenceStore,
    hits: tuple[RetrievalHit, ...],
    max_chars: int,
    min_hits: int,
    protect_top_n: int,
    max_hits: int,
    information_needs: tuple[str, ...],
) -> tuple[tuple[RetrievalHit, ...], dict[str, Any]]:
    if not hits:
        return hits, {
            **_disabled_context_budget_trace(
                enabled=True,
                max_chars=max_chars,
                min_hits=min_hits,
                protect_top_n=protect_top_n,
                max_hits=max_hits,
                information_needs=information_needs,
            ),
            "applied": True,
        }

    protected = max(0, protect_top_n)
    minimum = max(0, min_hits)
    hard_max = max(0, max_hits)
    selected: list[RetrievalHit] = []
    dropped: list[str] = []
    estimated_chars = 0

    for index, hit in enumerate(hits):
        if hard_max > 0 and len(selected) >= hard_max:
            dropped.extend(candidate.source_id for candidate in hits[index:])
            break
        turn = store.get(hit.source_id)
        turn_chars = len(turn.text) if turn is not None else 0
        force_keep = index < protected or len(selected) < minimum
        if force_keep or estimated_chars + turn_chars <= max_chars:
            selected.append(hit)
            estimated_chars += turn_chars
        else:
            dropped.append(hit.source_id)

    return tuple(selected), {
        "enabled": True,
        "applied": True,
        "max_chars": max_chars,
        "min_hits": min_hits,
        "protect_top_n": protect_top_n,
        "max_hits": max_hits,
        "information_needs": information_needs,
        "candidate_count": len(hits),
        "returned_count": len(selected),
        "estimated_chars": estimated_chars,
        "dropped_count": len(dropped),
        "dropped_source_ids": dropped,
    }


def _context_budget_audit_trace(
    *,
    store: RawEvidenceStore,
    projected_hits: tuple[RetrievalHit, ...],
    projected_budget: Mapping[str, Any],
    neighbor_window: int,
    neighbor_order: str,
    evidence_rows: tuple[Any, ...],
    selected_context: Mapping[str, Any],
) -> dict[str, Any]:
    projected_turns = store.expand_neighbors(
        (hit.source_id for hit in projected_hits),
        window=neighbor_window,
        order=neighbor_order,
    )
    projected_available = {turn.source_id for turn in projected_turns}
    prompt_source_ids = tuple(
        row.source_id for row in evidence_rows if getattr(row, "source_id", None)
    )
    prompt_missing = tuple(
        source_id for source_id in prompt_source_ids if source_id not in projected_available
    )
    selected_context_source_ids = tuple(
        source_id for source_id in selected_context.get("materialized_source_ids") or ()
    )
    selected_context_missing = tuple(
        source_id
        for source_id in selected_context_source_ids
        if source_id not in projected_available
    )
    return {
        "enabled": True,
        "trace_only": True,
        "applied": True,
        "reason": "simulated",
        "max_chars": projected_budget.get("max_chars"),
        "min_hits": projected_budget.get("min_hits"),
        "protect_top_n": projected_budget.get("protect_top_n"),
        "max_hits": projected_budget.get("max_hits"),
        "information_needs": projected_budget.get("information_needs"),
        "candidate_count": projected_budget.get("candidate_count"),
        "projected_returned_count": projected_budget.get("returned_count"),
        "projected_estimated_chars": projected_budget.get("estimated_chars"),
        "projected_dropped_count": projected_budget.get("dropped_count"),
        "projected_dropped_source_ids": projected_budget.get("dropped_source_ids"),
        "projected_available_source_count": len(projected_available),
        "prompt_row_count": len(prompt_source_ids),
        "prompt_rows_missing_count": len(prompt_missing),
        "prompt_rows_missing_source_ids": list(prompt_missing),
        "selected_context_materialized_count": len(selected_context_source_ids),
        "selected_context_missing_count": len(selected_context_missing),
        "selected_context_missing_source_ids": list(selected_context_missing),
        "safe_for_current_prompt": not prompt_missing,
        "clean_note": (
            "Trace-only simulation of retrieval context-budget pressure. It is not "
            "included in retrieval, compiler, answer, repair, finalizer, or cache keys."
        ),
    }


def _granularity_profile_audit(
    *,
    enabled: bool,
    profiles: tuple[dict[str, Any], ...],
    selected_profile: dict[str, Any] | None,
    avg_turn_chars: float,
    total_turn_chars: int,
) -> dict[str, Any]:
    profile_summaries = [
        _granularity_profile_audit_summary(profile) for profile in profiles
    ]
    trace: dict[str, Any] = {
        "enabled": enabled,
        "trace_only": True,
        "applied": False,
        "skip_reason": "disabled" if not enabled else None,
        "selector": "profile_thresholds",
        "average_turn_chars": round(float(avg_turn_chars), 3),
        "total_turn_chars": int(total_turn_chars),
        "configured_profile_count": len(profiles),
        "profiles": profile_summaries,
        "selected": False,
        "selected_profile_name": None,
        "selected_profile": None,
        "behavior_affecting": False,
        "behavior_sections": [],
        "risk_count": 0,
        "risk_reasons": [],
        "clean_note": (
            "Trace-only audit of granularity profile selection. It is not included "
            "in retrieval, compiler, answer, repair, finalizer, or cache keys."
        ),
    }
    if not enabled:
        return trace
    if not profiles:
        trace["skip_reason"] = "no_profiles_configured"
        return trace

    trace["applied"] = True
    trace["skip_reason"] = None
    if selected_profile is None:
        return trace

    selected_summary = _granularity_profile_audit_summary(selected_profile)
    behavior_sections = tuple(selected_summary["behavior_sections"])
    risk_reasons = [
        *_granularity_profile_selector_reasons(selected_profile),
        *[f"profile_threshold_changes_{section}" for section in behavior_sections],
    ]
    trace.update(
        {
            "selected": True,
            "selected_profile_name": selected_summary["name"],
            "selected_profile": selected_summary,
            "behavior_affecting": bool(behavior_sections),
            "behavior_sections": list(behavior_sections),
            "risk_count": len(risk_reasons) if behavior_sections else 0,
            "risk_reasons": risk_reasons if behavior_sections else [],
        }
    )
    return trace


def _granularity_profile_audit_summary(profile: Mapping[str, Any]) -> dict[str, Any]:
    behavior_sections = [
        section
        for section in (
            "route",
            "retrieval",
            "selected_context",
            "compiler",
            "answer_finalizer",
        )
        if profile.get(section)
    ]
    return {
        "name": str(profile.get("name") or ""),
        "min_avg_turn_chars": profile.get("min_avg_turn_chars"),
        "max_avg_turn_chars": profile.get("max_avg_turn_chars"),
        "min_total_chars": profile.get("min_total_chars"),
        "max_total_chars": profile.get("max_total_chars"),
        "behavior_sections": behavior_sections,
    }


def _granularity_profile_selector_reasons(profile: Mapping[str, Any]) -> list[str]:
    reasons: list[str] = []
    if (
        profile.get("min_avg_turn_chars") is not None
        or profile.get("max_avg_turn_chars") is not None
    ):
        reasons.append("avg_turn_length_selected_profile")
    if (
        profile.get("min_total_chars") is not None
        or profile.get("max_total_chars") is not None
    ):
        reasons.append("total_context_pressure_selected_profile")
    return reasons


def _selected_context_budget_gate(
    *,
    enabled: bool,
    min_context_budget_headroom_chars: int,
    context_budget_trace: Mapping[str, Any],
) -> tuple[bool, dict[str, Any]]:
    threshold = max(0, min_context_budget_headroom_chars)
    trace: dict[str, Any] = {
        "budget_gate_enabled": threshold > 0,
        "budget_gate_applied": False,
        "budget_gate_allowed": enabled,
        "budget_gate_reason": "selected_context_disabled"
        if not enabled
        else "gate_disabled",
        "min_context_budget_headroom_chars": threshold,
        "context_budget_headroom_chars": None,
        "context_budget_estimated_chars": (
            context_budget_trace.get("estimated_chars")
        ),
        "context_budget_max_chars": context_budget_trace.get("max_chars"),
    }
    if not enabled:
        return False, trace
    if threshold <= 0:
        trace["budget_gate_allowed"] = True
        return True, trace
    if not context_budget_trace.get("applied"):
        trace["budget_gate_allowed"] = True
        trace["budget_gate_reason"] = "no_context_budget"
        return True, trace
    max_chars = int(context_budget_trace.get("max_chars") or 0)
    estimated_chars = int(context_budget_trace.get("estimated_chars") or 0)
    headroom = max_chars - estimated_chars
    trace["context_budget_headroom_chars"] = headroom
    trace["budget_gate_applied"] = True
    if headroom >= threshold:
        trace["budget_gate_allowed"] = True
        trace["budget_gate_reason"] = "enough_headroom"
        return True, trace
    trace["budget_gate_allowed"] = False
    trace["budget_gate_reason"] = "insufficient_headroom"
    return False, trace


def _selected_context_risk_audit(
    *,
    store: RawEvidenceStore,
    evidence_turns: tuple[Turn, ...],
    route: RouteResult,
    question: str,
    selected_context: Mapping[str, Any],
    enabled: bool,
    information_needs: tuple[str, ...],
    source_grounded_min_terms: int,
    source_grounded_min_coverage: float,
) -> dict[str, Any]:
    source_grounded_term_threshold = max(0, int(source_grounded_min_terms))
    source_grounded_coverage_threshold = min(
        1.0, max(0.0, float(source_grounded_min_coverage))
    )
    materialized_ids = tuple(
        str(source_id)
        for source_id in selected_context.get("materialized_source_ids") or ()
    )
    trace: dict[str, Any] = {
        "enabled": enabled,
        "trace_only": True,
        "applied": False,
        "skip_reason": "disabled" if not enabled else None,
        "information_needs": information_needs,
        "source_grounded_min_terms": source_grounded_term_threshold,
        "source_grounded_min_coverage": source_grounded_coverage_threshold,
        "question_reference": bool(selected_context.get("question_reference")),
        "materialized_count": len(materialized_ids),
        "audited_count": 0,
        "safe_count": 0,
        "risk_count": 0,
        "safe_source_ids": [],
        "risk_source_ids": [],
        "risk_reasons": {},
        "text_source": "prompt_visible_materialized_context",
        "materialized_text_audit_count": 0,
        "raw_center_text_audit_count": 0,
    }
    if not enabled:
        return trace
    if information_needs and route.information_need not in information_needs:
        trace["skip_reason"] = "route_not_enabled"
        return trace
    if not materialized_ids:
        trace["skip_reason"] = "no_materialized_rows"
        return trace
    if trace["question_reference"]:
        trace["skip_reason"] = "question_reference_present"
        return trace

    trace["applied"] = True
    trace["skip_reason"] = None
    safe_source_ids: list[str] = []
    risk_source_ids: list[str] = []
    risk_reasons: dict[str, str] = {}
    materialized_text_count = 0
    raw_center_text_count = 0
    prompt_turns_by_source_id = {turn.source_id: turn for turn in evidence_turns}
    for source_id in materialized_ids:
        raw_turn = store.get(source_id)
        if raw_turn is None:
            risk_source_ids.append(source_id)
            risk_reasons[source_id] = "missing_source"
            continue
        prompt_turn = prompt_turns_by_source_id.get(source_id, raw_turn)
        uses_materialized_text = prompt_turn.text != raw_turn.text
        if uses_materialized_text:
            materialized_text_count += 1
        else:
            raw_center_text_count += 1
        source_grounded_match = _selected_context_source_grounded_match(
            question=question,
            turn=prompt_turn,
            min_terms=source_grounded_term_threshold,
            min_coverage=source_grounded_coverage_threshold,
            role_sensitive=not uses_materialized_text,
        )
        if source_grounded_match["matched"]:
            safe_source_ids.append(source_id)
        else:
            risk_source_ids.append(source_id)
            risk_reasons[source_id] = str(source_grounded_match["reason"])

    trace["audited_count"] = len(materialized_ids)
    trace["safe_count"] = len(safe_source_ids)
    trace["risk_count"] = len(risk_source_ids)
    trace["safe_source_ids"] = safe_source_ids
    trace["risk_source_ids"] = risk_source_ids
    trace["risk_reasons"] = risk_reasons
    trace["materialized_text_audit_count"] = materialized_text_count
    trace["raw_center_text_audit_count"] = raw_center_text_count
    return trace


def _compiler_context_pressure_trace(
    *,
    enabled: bool,
    max_headroom_chars: int,
    information_needs: tuple[str, ...],
    route: RouteResult,
    overrides: Mapping[str, Any],
    context_budget_trace: Mapping[str, Any],
) -> dict[str, Any]:
    threshold = max(0, int(max_headroom_chars))
    trace: dict[str, Any] = {
        "enabled": enabled,
        "applied": False,
        "reason": "disabled" if not enabled else "not_under_pressure",
        "max_headroom_chars": threshold,
        "information_needs": information_needs,
        "headroom_chars": None,
        "context_budget_estimated_chars": (
            context_budget_trace.get("estimated_chars")
        ),
        "context_budget_max_chars": context_budget_trace.get("max_chars"),
        "compiler_overrides": dict(overrides),
    }
    if not enabled:
        return trace
    if information_needs and route.information_need not in information_needs:
        trace["reason"] = "route_not_enabled"
        return trace
    if not context_budget_trace.get("applied"):
        trace["reason"] = "no_context_budget"
        return trace
    max_chars = int(context_budget_trace.get("max_chars") or 0)
    estimated_chars = int(context_budget_trace.get("estimated_chars") or 0)
    headroom = max_chars - estimated_chars
    trace["headroom_chars"] = headroom
    if headroom <= threshold:
        trace["applied"] = True
        trace["reason"] = "low_headroom"
    return trace


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


SELECTED_CONTEXT_ANAPHORA_PATTERN = re.compile(
    r"\b("
    r"this|that|these|those|it|they|them|there|here|same|such|"
    r"recently|previously|earlier|later|then|also|too|"
    r"last|next|before|after"
    r")\b",
    re.IGNORECASE,
)

SELECTED_CONTEXT_QUESTION_REFERENCE_PATTERN = re.compile(
    r"\b("
    r"these|those|it|they|them|there|here|same|such|"
    r"else|other|previously|earlier|later|then|mentioned|above"
    r")\b|"
    r"\bwhat\s+else\b|\bwhich\s+one\b|"
    r"\bthat\s+(?:one|same|thing|topic|conversation|event|option)\b|"
    r"\bthe\s+(?:former|latter)\b",
    re.IGNORECASE,
)
SELECTED_CONTEXT_TERM_PATTERN = re.compile(r"[A-Za-z0-9_]+")
SELECTED_CONTEXT_SELF_REFERENCE_PATTERN = re.compile(
    r"\b("
    r"i|i['’]?m|i['’]?ve|i['’]?d|me|my|mine|"
    r"we|we['’]?re|we['’]?ve|us|our|ours"
    r")\b",
    re.IGNORECASE,
)
SELECTED_CONTEXT_TERM_STOPWORDS = frozenset(
    {
        "a",
        "about",
        "an",
        "and",
        "are",
        "at",
        "be",
        "been",
        "being",
        "by",
        "could",
        "did",
        "do",
        "does",
        "during",
        "for",
        "from",
        "had",
        "has",
        "have",
        "he",
        "here",
        "her",
        "hers",
        "herself",
        "him",
        "himself",
        "his",
        "how",
        "i",
        "in",
        "is",
        "it",
        "me",
        "many",
        "my",
        "of",
        "on",
        "or",
        "our",
        "own",
        "owned",
        "owns",
        "same",
        "she",
        "should",
        "such",
        "that",
        "the",
        "their",
        "theirs",
        "them",
        "themselves",
        "they",
        "this",
        "those",
        "these",
        "there",
        "to",
        "up",
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
        "you",
        "your",
        "with",
    }
)
SELECTED_CONTEXT_GENERIC_ROLE_TERMS = frozenset({"assistant", "system", "user"})
SELECTED_CONTEXT_NO_SINGULAR_VARIANT_TERMS = frozenset(
    {
        "alexis",
        "chris",
        "james",
    }
)
SELECTED_CONTEXT_TERM_ALIASES: dict[str, tuple[str, ...]] = {
    "admires": ("admire", "like"),
    "admired": ("admire", "like"),
    "admiring": ("admire", "like"),
    "admire": ("like",),
    "enjoyed": ("enjoy", "like"),
    "enjoying": ("enjoy", "like"),
    "enjoys": ("enjoy", "like"),
    "enjoy": ("like",),
    "fan": ("support",),
    "fans": ("fan", "support"),
    "mum": ("mom", "mother"),
    "mom": ("mum", "mother"),
    "mother": ("mom", "mum"),
    "motivation": ("motivate", "support"),
    "motivates": ("motivate", "support"),
    "motivated": ("motivate", "support"),
    "motivating": ("motivate", "support"),
    "encouragement": ("encourage", "support"),
    "encourages": ("encourage", "support"),
    "encouraged": ("encourage", "support"),
    "encouraging": ("encourage", "support"),
    "educaton": ("education",),
    "goes": ("go",),
    "going": ("go",),
    "persue": ("pursue",),
    "planned": ("plan",),
    "planning": ("plan",),
    "recieved": ("received",),
    "signed": ("sign",),
    "went": ("go",),
}

def _materialize_selected_context(
    *,
    store: RawEvidenceStore,
    turns: tuple[Turn, ...],
    route: RouteResult,
    enabled: bool,
    information_needs: tuple[str, ...],
    window_before: int,
    window_after: int,
    max_rows: int,
    max_neighbor_chars: int,
    max_center_chars: int,
    context_format: str,
    timestamp_policy: str,
    require_anaphora: bool,
    question: str,
    require_question_reference: bool,
    require_question_reference_min_center_chars: int,
    require_source_grounded_self_reference: bool,
    source_grounded_min_terms: int,
    source_grounded_min_coverage: float,
    require_materialized_source_grounded: bool,
    materialized_source_grounded_min_terms: int,
    materialized_source_grounded_min_coverage: float,
) -> tuple[tuple[Turn, ...], dict[str, Any]]:
    row_question_reference_threshold = max(
        0, int(require_question_reference_min_center_chars)
    )
    source_grounded_term_threshold = max(0, int(source_grounded_min_terms))
    source_grounded_coverage_threshold = min(
        1.0, max(0.0, float(source_grounded_min_coverage))
    )
    materialized_source_grounded_term_threshold = max(
        0, int(materialized_source_grounded_min_terms)
    )
    materialized_source_grounded_coverage_threshold = min(
        1.0, max(0.0, float(materialized_source_grounded_min_coverage))
    )
    trace: dict[str, Any] = {
        "enabled": enabled,
        "applied": False,
        "information_needs": information_needs,
        "window_before": window_before,
        "window_after": window_after,
        "max_rows": max_rows,
        "max_neighbor_chars": max_neighbor_chars,
        "max_center_chars": max_center_chars,
        "context_format": context_format,
        "timestamp_policy": timestamp_policy,
        "require_anaphora": require_anaphora,
        "require_question_reference": require_question_reference,
        "require_question_reference_min_center_chars": (
            row_question_reference_threshold
        ),
        "require_source_grounded_self_reference": (
            require_source_grounded_self_reference
        ),
        "source_grounded_min_terms": source_grounded_term_threshold,
        "source_grounded_min_coverage": source_grounded_coverage_threshold,
        "require_materialized_source_grounded": (
            require_materialized_source_grounded
        ),
        "materialized_source_grounded_min_terms": (
            materialized_source_grounded_term_threshold
        ),
        "materialized_source_grounded_min_coverage": (
            materialized_source_grounded_coverage_threshold
        ),
        "question_reference": False,
        "skip_reason": None,
        "eligible": False,
        "materialized_count": 0,
        "materialized_source_ids": [],
        "skipped_long_center_count": 0,
        "skipped_long_center_source_ids": [],
        "skipped_question_reference_center_count": 0,
        "skipped_question_reference_center_source_ids": [],
        "skipped_source_grounded_count": 0,
        "skipped_source_grounded_source_ids": [],
        "skipped_source_grounded_reasons": {},
        "skipped_materialized_source_grounded_count": 0,
        "skipped_materialized_source_grounded_source_ids": [],
        "skipped_materialized_source_grounded_reasons": {},
    }
    if not enabled or not turns:
        trace["skip_reason"] = "disabled_or_empty"
        return turns, trace
    if information_needs and route.information_need not in information_needs:
        trace["skip_reason"] = "route_not_enabled"
        return turns, trace
    question_reference = bool(
        SELECTED_CONTEXT_QUESTION_REFERENCE_PATTERN.search(question or "")
    )
    trace["question_reference"] = question_reference
    if require_question_reference and not question_reference:
        trace["skip_reason"] = "question_reference_required"
        return turns, trace

    trace["eligible"] = True
    trace["skip_reason"] = None
    row_limit = max_rows if max_rows > 0 else len(turns)
    before = max(0, window_before)
    after = max(0, window_after)
    neighbor_chars = max(40, max_neighbor_chars)
    materialized_ids: list[str] = []
    materialized_turns: list[Turn] = []
    skipped_long_center_ids: list[str] = []
    skipped_question_reference_center_ids: list[str] = []
    skipped_source_grounded_ids: list[str] = []
    skipped_source_grounded_reasons: dict[str, str] = {}
    skipped_materialized_source_grounded_ids: list[str] = []
    skipped_materialized_source_grounded_reasons: dict[str, str] = {}

    for turn in turns:
        if max_center_chars > 0 and len(turn.text) > max_center_chars:
            skipped_long_center_ids.append(turn.source_id)
            materialized_turns.append(turn)
            continue
        if (
            row_question_reference_threshold > 0
            and len(turn.text) >= row_question_reference_threshold
            and not question_reference
        ):
            skipped_question_reference_center_ids.append(turn.source_id)
            materialized_turns.append(turn)
            continue
        if len(materialized_ids) >= row_limit or (
            require_anaphora
            and not SELECTED_CONTEXT_ANAPHORA_PATTERN.search(turn.text)
        ):
            materialized_turns.append(turn)
            continue
        if require_source_grounded_self_reference and not question_reference:
            source_grounded_match = _selected_context_source_grounded_match(
                question=question,
                turn=turn,
                min_terms=source_grounded_term_threshold,
                min_coverage=source_grounded_coverage_threshold,
            )
            if not source_grounded_match["matched"]:
                skipped_source_grounded_ids.append(turn.source_id)
                skipped_source_grounded_reasons[turn.source_id] = str(
                    source_grounded_match["reason"]
                )
                materialized_turns.append(turn)
                continue
        context_text = _selected_context_text(
            store=store,
            turn=turn,
            window_before=before,
            window_after=after,
            max_neighbor_chars=neighbor_chars,
            context_format=context_format,
            timestamp_policy=timestamp_policy,
        )
        if context_text == turn.text:
            materialized_turns.append(turn)
            continue
        materialized_turn = replace(turn, text=context_text)
        if require_materialized_source_grounded:
            materialized_match = _selected_context_source_grounded_match(
                question=question,
                turn=materialized_turn,
                min_terms=materialized_source_grounded_term_threshold,
                min_coverage=materialized_source_grounded_coverage_threshold,
                role_sensitive=False,
            )
            if not materialized_match["matched"]:
                skipped_materialized_source_grounded_ids.append(turn.source_id)
                skipped_materialized_source_grounded_reasons[turn.source_id] = str(
                    materialized_match["reason"]
                )
                materialized_turns.append(turn)
                continue
        materialized_ids.append(turn.source_id)
        materialized_turns.append(materialized_turn)

    trace["materialized_count"] = len(materialized_ids)
    trace["materialized_source_ids"] = materialized_ids
    trace["skipped_long_center_count"] = len(skipped_long_center_ids)
    trace["skipped_long_center_source_ids"] = skipped_long_center_ids
    trace["skipped_question_reference_center_count"] = len(
        skipped_question_reference_center_ids
    )
    trace["skipped_question_reference_center_source_ids"] = (
        skipped_question_reference_center_ids
    )
    trace["skipped_source_grounded_count"] = len(skipped_source_grounded_ids)
    trace["skipped_source_grounded_source_ids"] = skipped_source_grounded_ids
    trace["skipped_source_grounded_reasons"] = skipped_source_grounded_reasons
    trace["skipped_materialized_source_grounded_count"] = len(
        skipped_materialized_source_grounded_ids
    )
    trace["skipped_materialized_source_grounded_source_ids"] = (
        skipped_materialized_source_grounded_ids
    )
    trace["skipped_materialized_source_grounded_reasons"] = (
        skipped_materialized_source_grounded_reasons
    )
    trace["applied"] = bool(materialized_ids)
    return tuple(materialized_turns), trace


def _selected_context_source_grounded_match(
    *,
    question: str,
    turn: Turn,
    min_terms: int,
    min_coverage: float,
    role_sensitive: bool = True,
) -> dict[str, object]:
    question_terms = _selected_context_content_terms(question)
    if not question_terms:
        return {"matched": False, "reason": "empty_question_terms"}
    role_terms = _selected_context_role_terms(turn.role)
    if role_sensitive and role_terms and not role_terms.intersection(question_terms):
        return {"matched": False, "reason": "role_not_in_question"}
    if (
        role_sensitive
        and
        role_terms
        and role_terms.intersection(question_terms)
        and not SELECTED_CONTEXT_SELF_REFERENCE_PATTERN.search(turn.text)
    ):
        return {"matched": False, "reason": "missing_self_reference"}
    turn_terms = _selected_context_content_terms(turn.text).union(role_terms)
    matched_terms = question_terms.intersection(turn_terms)
    if len(matched_terms) < min_terms:
        return {"matched": False, "reason": "insufficient_slot_terms"}
    coverage = len(matched_terms) / max(1, len(question_terms))
    if coverage < min_coverage:
        return {"matched": False, "reason": "insufficient_slot_coverage"}
    return {"matched": True, "reason": "source_grounded_self_reference"}


def _selected_context_role_terms(role: str) -> frozenset[str]:
    return _selected_context_content_terms(role).difference(
        SELECTED_CONTEXT_GENERIC_ROLE_TERMS
    )


def _selected_context_content_terms(text: str) -> frozenset[str]:
    terms: set[str] = set()
    for match in SELECTED_CONTEXT_TERM_PATTERN.finditer(text.lower()):
        token = match.group(0)
        if len(token) <= 1 or token in SELECTED_CONTEXT_TERM_STOPWORDS:
            continue
        terms.update(_selected_context_term_variants(token))
    return frozenset(terms)


def _selected_context_term_variants(token: str) -> set[str]:
    variants = {token}
    if len(token) > 4 and token.endswith("ies"):
        variants = {f"{token[:-3]}y"}
    elif (
        len(token) > 4
        and token.endswith(("ses", "xes", "zes", "ches", "shes"))
        and token not in SELECTED_CONTEXT_NO_SINGULAR_VARIANT_TERMS
    ):
        variants = {token[:-2]}
    elif (
        len(token) > 3
        and token.endswith("s")
        and token not in SELECTED_CONTEXT_NO_SINGULAR_VARIANT_TERMS
        and not token.endswith(("ss", "us"))
    ):
        variants = {token[:-1]}
    queue = list(variants)
    while queue:
        current = queue.pop()
        for alias in SELECTED_CONTEXT_TERM_ALIASES.get(current, ()):
            if (
                len(alias) > 1
                and alias not in SELECTED_CONTEXT_TERM_STOPWORDS
                and alias not in variants
            ):
                variants.add(alias)
                queue.append(alias)
    return variants


def _selected_context_text(
    *,
    store: RawEvidenceStore,
    turn: Turn,
    window_before: int,
    window_after: int,
    max_neighbor_chars: int,
    context_format: str = "verbose",
    timestamp_policy: str = "all",
) -> str:
    session_turns = store.session_turns(turn.session_id)
    positions = {
        candidate.source_id: index for index, candidate in enumerate(session_turns)
    }
    position = positions.get(turn.source_id)
    if position is None:
        return turn.text
    start = max(0, position - window_before)
    end = min(len(session_turns), position + window_after + 1)
    neighbors = session_turns[start:end]
    if len(neighbors) <= 1:
        return turn.text

    compact = context_format == "compact"
    lines = [
        "Same-session context:"
        if compact
        else "Local dialogue context from the same session:"
    ]
    for neighbor in neighbors:
        if neighbor.source_id == turn.source_id:
            label = "center" if compact else "selected turn"
        else:
            label = "near" if compact else "nearby turn"
        text = neighbor.text
        if neighbor.source_id != turn.source_id:
            text = _truncate_text(text, max_neighbor_chars)
        include_timestamp = timestamp_policy == "all" or (
            timestamp_policy == "center_only" and neighbor.source_id == turn.source_id
        )
        timestamp = (
            f" ({neighbor.timestamp})"
            if include_timestamp and neighbor.timestamp
            else ""
        )
        lines.append(f"- {label}{timestamp} | {neighbor.role}: {text}")
    if len(lines) <= 2:
        return turn.text
    return "\n".join(lines)


def _truncate_text(text: str, max_chars: int) -> str:
    normalized = " ".join(text.split())
    if len(normalized) <= max_chars:
        return normalized
    return normalized[: max(0, max_chars - 3)].rstrip() + "..."


def _tuple_config(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    if isinstance(value, (list, tuple)):
        return tuple(str(item) for item in value)
    return (str(value),)


def _dict_config(value: object) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, Mapping):
        return dict(value)
    raise ValueError(f"Expected mapping config, got {type(value).__name__}")


RETRIEVAL_ROUTE_OVERRIDE_KEYS = {
    "top_k",
    "max_top_k",
    "dense_top_k",
    "lexical_protect_top_n",
    "dense_protect_top_n",
}
SELECTED_CONTEXT_OVERRIDE_KEYS = {
    "enabled",
    "window_before",
    "window_after",
    "max_rows",
    "max_neighbor_chars",
    "max_center_chars",
    "context_format",
    "timestamp_policy",
    "min_context_budget_headroom_chars",
    "require_anaphora",
    "require_question_reference",
    "require_question_reference_min_center_chars",
    "require_source_grounded_self_reference",
    "source_grounded_min_terms",
    "source_grounded_min_coverage",
    "require_materialized_source_grounded",
    "materialized_source_grounded_min_terms",
    "materialized_source_grounded_min_coverage",
    "information_needs",
}


def _selected_context_context_format(value: object) -> str:
    context_format = str(value or "verbose")
    if context_format not in {"verbose", "compact"}:
        raise ValueError(
            "retrieval.selected_context.context_format must be verbose or compact"
        )
    return context_format


def _selected_context_timestamp_policy(value: object) -> str:
    timestamp_policy = str(value or "all")
    if timestamp_policy not in {"all", "center_only", "none"}:
        raise ValueError(
            "retrieval.selected_context.timestamp_policy must be all, "
            "center_only, or none"
        )
    return timestamp_policy


def _merged_config(
    base: Mapping[str, Any],
    override: Mapping[str, Any],
) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if (
            isinstance(value, Mapping)
            and isinstance(merged.get(key), Mapping)
        ):
            merged[key] = {**dict(merged[key]), **dict(value)}
        else:
            merged[key] = value
    return merged


def _configured_router(route_config: Mapping[str, Any]) -> QuestionRouter:
    return QuestionRouter(
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


def _compiler_trace_config(
    compiler_config: Mapping[str, Any],
    *,
    memory_record_source: str,
    memory_state_guide_record_source: str | None = None,
) -> dict[str, Any]:
    return {
        "prompt_mode": str(compiler_config.get("prompt_mode", "default")),
        "memory_record_source": memory_record_source,
        "memory_state_guide_record_source": (
            memory_state_guide_record_source or memory_record_source
        ),
        "evidence_order": str(compiler_config.get("evidence_order", "retrieval")),
        "memory_order": str(compiler_config.get("memory_order", "retrieval")),
        "memory_layout": str(compiler_config.get("memory_layout", "flat")),
        "row_text_mode": str(compiler_config.get("row_text_mode", "full")),
        "max_row_text_chars": int(compiler_config.get("max_row_text_chars", 0)),
        "tail_row_text_mode": str(compiler_config.get("tail_row_text_mode", "full")),
        "tail_row_text_after_rank": int(
            compiler_config.get("tail_row_text_after_rank", 0)
        ),
        "tail_max_row_text_chars": int(
            compiler_config.get("tail_max_row_text_chars", 0)
        ),
        "evidence_row_labels": bool(compiler_config.get("evidence_row_labels", False)),
        "final_answer_checklist": bool(
            compiler_config.get("final_answer_checklist", False)
        ),
        "route_guidance": bool(compiler_config.get("route_guidance", False)),
        "answer_style": str(compiler_config.get("answer_style", "grounded")),
        "temporal_grounding": bool(compiler_config.get("temporal_grounding", False)),
        "temporal_hints": bool(compiler_config.get("temporal_hints", False)),
        "temporal_workpad": bool(compiler_config.get("temporal_workpad", False)),
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
        "event_timeline": bool(compiler_config.get("event_timeline", False)),
        "event_timeline_information_needs": _tuple_config(
            compiler_config.get(
                "event_timeline_information_needs",
                ("current_state", "list_count", "temporal_lookup"),
            )
        ),
        "event_timeline_max_rows": int(
            compiler_config.get("event_timeline_max_rows", 12)
        ),
        "event_timeline_snippet_chars": int(
            compiler_config.get("event_timeline_snippet_chars", 180)
        ),
        "event_time_candidate_manifest": bool(
            compiler_config.get("event_time_candidate_manifest", False)
        ),
        "event_time_candidate_manifest_information_needs": _tuple_config(
            compiler_config.get(
                "event_time_candidate_manifest_information_needs",
                ("current_state", "list_count", "temporal_lookup"),
            )
        ),
        "event_time_candidate_manifest_max_rows": int(
            compiler_config.get("event_time_candidate_manifest_max_rows", 12)
        ),
        "event_time_candidate_manifest_question_gate": bool(
            compiler_config.get("event_time_candidate_manifest_question_gate", True)
        ),
        "event_time_candidate_manifest_snippet_chars": int(
            compiler_config.get("event_time_candidate_manifest_snippet_chars", 160)
        ),
        "event_time_candidate_manifest_grouped_view": bool(
            compiler_config.get("event_time_candidate_manifest_grouped_view", False)
        ),
        "event_time_candidate_manifest_max_groups": int(
            compiler_config.get("event_time_candidate_manifest_max_groups", 8)
        ),
        "event_time_candidate_map": bool(
            compiler_config.get("event_time_candidate_map", False)
        ),
        "event_time_candidate_map_information_needs": _tuple_config(
            compiler_config.get(
                "event_time_candidate_map_information_needs",
                ("temporal_lookup",),
            )
        ),
        "event_time_candidate_map_max_groups": int(
            compiler_config.get("event_time_candidate_map_max_groups", 1)
        ),
        "event_time_candidate_map_snippet_chars": int(
            compiler_config.get("event_time_candidate_map_snippet_chars", 140)
        ),
        "event_time_candidate_map_min_terms": int(
            compiler_config.get("event_time_candidate_map_min_terms", 2)
        ),
        "event_time_candidate_map_min_coverage": float(
            compiler_config.get("event_time_candidate_map_min_coverage", 0.6)
        ),
        "event_time_candidate_map_allowed_time_kinds": _tuple_config(
            compiler_config.get(
                "event_time_candidate_map_allowed_time_kinds",
                ("exact_today", "explicit_date", "relative_phrase"),
            )
        ),
        "event_time_candidate_map_strip_context_wrappers": bool(
            compiler_config.get("event_time_candidate_map_strip_context_wrappers", False)
        ),
        "event_time_candidate_map_segment_local_context": bool(
            compiler_config.get("event_time_candidate_map_segment_local_context", False)
        ),
        "event_time_candidate_map_rank_by_coverage": bool(
            compiler_config.get("event_time_candidate_map_rank_by_coverage", False)
        ),
        "event_time_candidate_map_normalize_terms": bool(
            compiler_config.get("event_time_candidate_map_normalize_terms", False)
        ),
        "event_time_candidate_map_exact_today_min_coverage": (
            None
            if compiler_config.get("event_time_candidate_map_exact_today_min_coverage")
            is None
            else float(
                compiler_config.get("event_time_candidate_map_exact_today_min_coverage")
            )
        ),
        "event_time_candidate_map_require_role_match": bool(
            compiler_config.get("event_time_candidate_map_require_role_match", False)
        ),
        "event_time_candidate_map_allow_time_of_day_questions": bool(
            compiler_config.get(
                "event_time_candidate_map_allow_time_of_day_questions", True
            )
        ),
        "event_time_candidate_map_audit": bool(
            compiler_config.get("event_time_candidate_map_audit", False)
        ),
        "event_time_candidate_map_temporal_ambiguity_contract": bool(
            compiler_config.get(
                "event_time_candidate_map_temporal_ambiguity_contract", False
            )
        ),
        "event_time_candidate_map_include_mention_time": bool(
            compiler_config.get(
                "event_time_candidate_map_include_mention_time", False
            )
        ),
        "event_time_candidate_map_mention_time_fallback": bool(
            compiler_config.get("event_time_candidate_map_mention_time_fallback", False)
        ),
        "event_time_candidate_map_mention_time_fallback_min_coverage": float(
            compiler_config.get(
                "event_time_candidate_map_mention_time_fallback_min_coverage",
                0.8,
            )
        ),
        "event_time_candidate_map_mention_time_fallback_trigger_max_coverage": float(
            compiler_config.get(
                "event_time_candidate_map_mention_time_fallback_trigger_max_coverage",
                0.8,
            )
        ),
        "enable_weekend_relative_time": bool(
            compiler_config.get("enable_weekend_relative_time", False)
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
        "structured_guide_memory_hints": bool(
            compiler_config.get("structured_guide_memory_hints", False)
        ),
        "structured_guide_max_memory_hints_per_row": int(
            compiler_config.get("structured_guide_max_memory_hints_per_row", 1)
        ),
        "structured_guide_memory_hint_chars": int(
            compiler_config.get("structured_guide_memory_hint_chars", 70)
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
        "candidate_guide_include_memory_hints": bool(
            compiler_config.get("candidate_guide_include_memory_hints", False)
        ),
        "candidate_guide_max_memory_hints": int(
            compiler_config.get("candidate_guide_max_memory_hints", 2)
        ),
        "candidate_guide_memory_hint_chars": int(
            compiler_config.get("candidate_guide_memory_hint_chars", 120)
        ),
        "update_conflict_guide": bool(
            compiler_config.get("update_conflict_guide", False)
        ),
        "update_conflict_guide_information_needs": _tuple_config(
            compiler_config.get(
                "update_conflict_guide_information_needs",
                ("current_state", "fact_lookup", "list_count", "temporal_lookup"),
            )
        ),
        "update_conflict_guide_max_rows": int(
            compiler_config.get("update_conflict_guide_max_rows", 6)
        ),
        "update_conflict_guide_snippet_chars": int(
            compiler_config.get("update_conflict_guide_snippet_chars", 180)
        ),
        "memory_state_guide": bool(compiler_config.get("memory_state_guide", False)),
        "memory_state_guide_information_needs": _tuple_config(
            compiler_config.get(
                "memory_state_guide_information_needs",
                ("current_state", "fact_lookup", "profile_preference"),
            )
        ),
        "memory_state_guide_max_records": int(
            compiler_config.get("memory_state_guide_max_records", 8)
        ),
        "memory_state_guide_candidate_records": int(
            compiler_config.get("memory_state_guide_candidate_records", 12)
        ),
        "memory_state_guide_value_chars": int(
            compiler_config.get("memory_state_guide_value_chars", 120)
        ),
        "memory_state_guide_include_superseded": bool(
            compiler_config.get("memory_state_guide_include_superseded", True)
        ),
        "memory_state_guide_require_conflict": bool(
            compiler_config.get("memory_state_guide_require_conflict", False)
        ),
        "memory_state_guide_require_active_superseded_pair": bool(
            compiler_config.get(
                "memory_state_guide_require_active_superseded_pair", False
            )
        ),
        "memory_state_guide_require_slot_overlap": bool(
            compiler_config.get("memory_state_guide_require_slot_overlap", False)
        ),
        "memory_state_guide_require_stateful_slot": bool(
            compiler_config.get("memory_state_guide_require_stateful_slot", False)
        ),
        "profile_activation_guide": bool(
            compiler_config.get("profile_activation_guide", False)
        ),
        "profile_activation_guide_information_needs": _tuple_config(
            compiler_config.get(
                "profile_activation_guide_information_needs",
                ("profile_preference",),
            )
        ),
        "profile_activation_guide_max_records": int(
            compiler_config.get("profile_activation_guide_max_records", 4)
        ),
        "profile_activation_guide_value_chars": int(
            compiler_config.get("profile_activation_guide_value_chars", 160)
        ),
        "operation_workpad": bool(compiler_config.get("operation_workpad", False)),
        "operation_workpad_information_needs": _tuple_config(
            compiler_config.get(
                "operation_workpad_information_needs",
                ("list_count", "temporal_lookup"),
            )
        ),
        "operation_workpad_question_gate": bool(
            compiler_config.get("operation_workpad_question_gate", False)
        ),
        "personalized_advice_contract": bool(
            compiler_config.get("personalized_advice_contract", False)
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
        "memory_context_newlines_after_blocks": int(
            compiler_config.get("memory_context_newlines_after_blocks", 3)
        ),
        "max_memory_records": int(compiler_config.get("max_memory_records", 12)),
        "route_overrides": compiler_config.get("route_overrides") or {},
    }


def _configured_compiler(compiler_config: Mapping[str, Any]) -> EvidenceCompiler:
    return EvidenceCompiler(
        answer_style=str(compiler_config.get("answer_style", "grounded")),
        max_evidence_items=int(compiler_config.get("max_evidence_items", 12)),
        max_evidence_chars=int(compiler_config.get("max_evidence_chars", 12000)),
        max_memory_records=int(compiler_config.get("max_memory_records", 12)),
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
        event_timeline=bool(compiler_config.get("event_timeline", False)),
        event_timeline_information_needs=_tuple_config(
            compiler_config.get(
                "event_timeline_information_needs",
                ("current_state", "list_count", "temporal_lookup"),
            )
        ),
        event_timeline_max_rows=int(
            compiler_config.get("event_timeline_max_rows", 12)
        ),
        event_timeline_snippet_chars=int(
            compiler_config.get("event_timeline_snippet_chars", 180)
        ),
        event_time_candidate_manifest=bool(
            compiler_config.get("event_time_candidate_manifest", False)
        ),
        event_time_candidate_manifest_information_needs=_tuple_config(
            compiler_config.get(
                "event_time_candidate_manifest_information_needs",
                ("current_state", "list_count", "temporal_lookup"),
            )
        ),
        event_time_candidate_manifest_max_rows=int(
            compiler_config.get("event_time_candidate_manifest_max_rows", 12)
        ),
        event_time_candidate_manifest_snippet_chars=int(
            compiler_config.get("event_time_candidate_manifest_snippet_chars", 160)
        ),
        event_time_candidate_manifest_question_gate=bool(
            compiler_config.get("event_time_candidate_manifest_question_gate", True)
        ),
        event_time_candidate_manifest_grouped_view=bool(
            compiler_config.get("event_time_candidate_manifest_grouped_view", False)
        ),
        event_time_candidate_manifest_max_groups=int(
            compiler_config.get("event_time_candidate_manifest_max_groups", 8)
        ),
        event_time_candidate_map=bool(
            compiler_config.get("event_time_candidate_map", False)
        ),
        event_time_candidate_map_information_needs=_tuple_config(
            compiler_config.get(
                "event_time_candidate_map_information_needs",
                ("temporal_lookup",),
            )
        ),
        event_time_candidate_map_max_groups=int(
            compiler_config.get("event_time_candidate_map_max_groups", 1)
        ),
        event_time_candidate_map_snippet_chars=int(
            compiler_config.get("event_time_candidate_map_snippet_chars", 140)
        ),
        event_time_candidate_map_min_terms=int(
            compiler_config.get("event_time_candidate_map_min_terms", 2)
        ),
        event_time_candidate_map_min_coverage=float(
            compiler_config.get("event_time_candidate_map_min_coverage", 0.6)
        ),
        event_time_candidate_map_allowed_time_kinds=_tuple_config(
            compiler_config.get(
                "event_time_candidate_map_allowed_time_kinds",
                ("exact_today", "explicit_date", "relative_phrase"),
            )
        ),
        event_time_candidate_map_strip_context_wrappers=bool(
            compiler_config.get("event_time_candidate_map_strip_context_wrappers", False)
        ),
        event_time_candidate_map_segment_local_context=bool(
            compiler_config.get("event_time_candidate_map_segment_local_context", False)
        ),
        event_time_candidate_map_rank_by_coverage=bool(
            compiler_config.get("event_time_candidate_map_rank_by_coverage", False)
        ),
        event_time_candidate_map_normalize_terms=bool(
            compiler_config.get("event_time_candidate_map_normalize_terms", False)
        ),
        event_time_candidate_map_exact_today_min_coverage=(
            None
            if compiler_config.get("event_time_candidate_map_exact_today_min_coverage")
            is None
            else float(
                compiler_config.get("event_time_candidate_map_exact_today_min_coverage")
            )
        ),
        event_time_candidate_map_require_role_match=bool(
            compiler_config.get("event_time_candidate_map_require_role_match", False)
        ),
        event_time_candidate_map_allow_time_of_day_questions=bool(
            compiler_config.get(
                "event_time_candidate_map_allow_time_of_day_questions", True
            )
        ),
        event_time_candidate_map_audit=bool(
            compiler_config.get("event_time_candidate_map_audit", False)
        ),
        event_time_candidate_map_temporal_ambiguity_contract=bool(
            compiler_config.get(
                "event_time_candidate_map_temporal_ambiguity_contract", False
            )
        ),
        event_time_candidate_map_include_mention_time=bool(
            compiler_config.get(
                "event_time_candidate_map_include_mention_time", False
            )
        ),
        event_time_candidate_map_mention_time_fallback=bool(
            compiler_config.get("event_time_candidate_map_mention_time_fallback", False)
        ),
        event_time_candidate_map_mention_time_fallback_min_coverage=float(
            compiler_config.get(
                "event_time_candidate_map_mention_time_fallback_min_coverage",
                0.8,
            )
        ),
        event_time_candidate_map_mention_time_fallback_trigger_max_coverage=float(
            compiler_config.get(
                "event_time_candidate_map_mention_time_fallback_trigger_max_coverage",
                0.8,
            )
        ),
        enable_weekend_relative_time=bool(
            compiler_config.get("enable_weekend_relative_time", False)
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
        structured_guide_memory_hints=bool(
            compiler_config.get("structured_guide_memory_hints", False)
        ),
        structured_guide_max_memory_hints_per_row=int(
            compiler_config.get("structured_guide_max_memory_hints_per_row", 1)
        ),
        structured_guide_memory_hint_chars=int(
            compiler_config.get("structured_guide_memory_hint_chars", 70)
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
        candidate_guide_include_memory_hints=bool(
            compiler_config.get("candidate_guide_include_memory_hints", False)
        ),
        candidate_guide_max_memory_hints=int(
            compiler_config.get("candidate_guide_max_memory_hints", 2)
        ),
        candidate_guide_memory_hint_chars=int(
            compiler_config.get("candidate_guide_memory_hint_chars", 120)
        ),
        update_conflict_guide=bool(
            compiler_config.get("update_conflict_guide", False)
        ),
        update_conflict_guide_information_needs=_tuple_config(
            compiler_config.get(
                "update_conflict_guide_information_needs",
                ("current_state", "fact_lookup", "list_count", "temporal_lookup"),
            )
        ),
        update_conflict_guide_max_rows=int(
            compiler_config.get("update_conflict_guide_max_rows", 6)
        ),
        update_conflict_guide_snippet_chars=int(
            compiler_config.get("update_conflict_guide_snippet_chars", 180)
        ),
        memory_state_guide=bool(compiler_config.get("memory_state_guide", False)),
        memory_state_guide_information_needs=_tuple_config(
            compiler_config.get(
                "memory_state_guide_information_needs",
                ("current_state", "fact_lookup", "profile_preference"),
            )
        ),
        memory_state_guide_max_records=int(
            compiler_config.get("memory_state_guide_max_records", 8)
        ),
        memory_state_guide_candidate_records=int(
            compiler_config.get("memory_state_guide_candidate_records", 12)
        ),
        memory_state_guide_value_chars=int(
            compiler_config.get("memory_state_guide_value_chars", 120)
        ),
        memory_state_guide_include_superseded=bool(
            compiler_config.get("memory_state_guide_include_superseded", True)
        ),
        memory_state_guide_require_conflict=bool(
            compiler_config.get("memory_state_guide_require_conflict", False)
        ),
        memory_state_guide_require_active_superseded_pair=bool(
            compiler_config.get(
                "memory_state_guide_require_active_superseded_pair", False
            )
        ),
        memory_state_guide_require_slot_overlap=bool(
            compiler_config.get("memory_state_guide_require_slot_overlap", False)
        ),
        memory_state_guide_require_stateful_slot=bool(
            compiler_config.get("memory_state_guide_require_stateful_slot", False)
        ),
        profile_activation_guide=bool(
            compiler_config.get("profile_activation_guide", False)
        ),
        profile_activation_guide_information_needs=_tuple_config(
            compiler_config.get(
                "profile_activation_guide_information_needs",
                ("profile_preference",),
            )
        ),
        profile_activation_guide_max_records=int(
            compiler_config.get("profile_activation_guide_max_records", 4)
        ),
        profile_activation_guide_value_chars=int(
            compiler_config.get("profile_activation_guide_value_chars", 160)
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
        personalized_advice_contract=bool(
            compiler_config.get("personalized_advice_contract", False)
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
        tail_row_text_mode=str(compiler_config.get("tail_row_text_mode", "full")),
        tail_row_text_after_rank=int(
            compiler_config.get("tail_row_text_after_rank", 0)
        ),
        tail_max_row_text_chars=int(
            compiler_config.get("tail_max_row_text_chars", 0)
        ),
        route_guidance=bool(compiler_config.get("route_guidance", False)),
        evidence_row_labels=bool(compiler_config.get("evidence_row_labels", False)),
        final_answer_checklist=bool(
            compiler_config.get("final_answer_checklist", False)
        ),
        memory_context_newlines_after_blocks=int(
            compiler_config.get("memory_context_newlines_after_blocks", 3)
        ),
        prompt_mode=str(compiler_config.get("prompt_mode", "default")),
        route_overrides=compiler_config.get("route_overrides") or {},
    )


def _answer_finalizer_settings_from_config(
    config: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "enabled": bool(config.get("enabled", False)),
        "mode": str(config.get("mode", "structured_evidence_mechanical")),
        "enable_count_correction": bool(config.get("enable_count_correction", False)),
        "enable_evidence_report_count_correction": bool(
            config.get("enable_evidence_report_count_correction", False)
        ),
        "enable_money_sum_correction": bool(
            config.get("enable_money_sum_correction", True)
        ),
        "enable_duration_rounding_correction": bool(
            config.get("enable_duration_rounding_correction", False)
        ),
        "enable_missing_detail": bool(config.get("enable_missing_detail", False)),
        "enable_count_answer_detail": bool(
            config.get("enable_count_answer_detail", False)
        ),
        "enable_average_calculation": bool(
            config.get("enable_average_calculation", False)
        ),
        "enable_money_difference_calculation": bool(
            config.get("enable_money_difference_calculation", False)
        ),
        "enable_date_endpoint_duration_calculation": bool(
            config.get("enable_date_endpoint_duration_calculation", False)
        ),
        "enable_relative_time_calculation": bool(
            config.get("enable_relative_time_calculation", False)
        ),
        "enable_numeric_slot_label_preservation": bool(
            config.get("enable_numeric_slot_label_preservation", False)
        ),
        "enable_source_value_specificity_preservation": bool(
            config.get("enable_source_value_specificity_preservation", False)
        ),
        "enable_profile_preference_value_preservation": bool(
            config.get("enable_profile_preference_value_preservation", False)
        ),
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


def _validate_selected_context_route_overrides(
    route_overrides: Mapping[str, Mapping[str, Any]],
) -> dict[str, dict[str, Any]]:
    normalized: dict[str, dict[str, Any]] = {}
    for information_need, raw_overrides in route_overrides.items():
        if information_need not in SUPPORTED_INFORMATION_NEEDS:
            raise ValueError(
                "Unsupported retrieval.selected_context route override: "
                f"{information_need}"
            )
        if not isinstance(raw_overrides, Mapping):
            raise ValueError(
                "retrieval.selected_context.route_overrides."
                f"{information_need} must be an object"
            )
        unknown_keys = set(raw_overrides).difference(SELECTED_CONTEXT_OVERRIDE_KEYS)
        if unknown_keys:
            keys = ", ".join(sorted(unknown_keys))
            raise ValueError(
                "Unsupported retrieval.selected_context.route_overrides."
                f"{information_need} keys: {keys}"
            )
        normalized[information_need] = _normalized_selected_context_override(
            raw_overrides
        )
    return normalized


def _validate_granularity_profiles(value: object) -> tuple[dict[str, Any], ...]:
    if not value:
        return ()
    if not isinstance(value, (list, tuple)):
        raise ValueError("retrieval.granularity_profiles must be a list")
    profiles: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, raw_profile in enumerate(value):
        if not isinstance(raw_profile, Mapping):
            raise ValueError("retrieval.granularity_profiles entries must be objects")
        name = str(raw_profile.get("name") or f"profile_{index}")
        if name in seen:
            raise ValueError(f"Duplicate granularity profile name: {name}")
        seen.add(name)
        min_avg_turn_chars = raw_profile.get("min_avg_turn_chars")
        max_avg_turn_chars = raw_profile.get("max_avg_turn_chars")
        min_total_chars = raw_profile.get("min_total_chars")
        max_total_chars = raw_profile.get("max_total_chars")
        retrieval = raw_profile.get("retrieval") or {}
        route = raw_profile.get("route") or {}
        selected_context = raw_profile.get("selected_context") or {}
        compiler = raw_profile.get("compiler") or {}
        answer_finalizer = raw_profile.get("answer_finalizer") or {}
        if not isinstance(retrieval, Mapping):
            raise ValueError(f"granularity profile {name}.retrieval must be an object")
        if not isinstance(route, Mapping):
            raise ValueError(f"granularity profile {name}.route must be an object")
        if not isinstance(selected_context, Mapping):
            raise ValueError(
                f"granularity profile {name}.selected_context must be an object"
            )
        if not isinstance(compiler, Mapping):
            raise ValueError(f"granularity profile {name}.compiler must be an object")
        if not isinstance(answer_finalizer, Mapping):
            raise ValueError(
                f"granularity profile {name}.answer_finalizer must be an object"
            )
        unknown_retrieval = set(retrieval).difference(RETRIEVAL_ROUTE_OVERRIDE_KEYS)
        if unknown_retrieval:
            keys = ", ".join(sorted(unknown_retrieval))
            raise ValueError(f"Unsupported granularity retrieval keys: {keys}")
        unknown_selected = set(selected_context).difference(
            SELECTED_CONTEXT_OVERRIDE_KEYS
        )
        if unknown_selected:
            keys = ", ".join(sorted(unknown_selected))
            raise ValueError(f"Unsupported granularity selected_context keys: {keys}")
        allowed_route = {
            "enable_broad_list_patterns",
            "enable_recommendation_profile_patterns",
            "enable_advice_profile_patterns",
            "temporal_priority_over_recent",
        }
        unknown_route = set(route).difference(allowed_route)
        if unknown_route:
            keys = ", ".join(sorted(unknown_route))
            raise ValueError(f"Unsupported granularity route keys: {keys}")
        profiles.append(
            {
                "name": name,
                "min_avg_turn_chars": (
                    float(min_avg_turn_chars)
                    if min_avg_turn_chars is not None
                    else None
                ),
                "max_avg_turn_chars": (
                    float(max_avg_turn_chars)
                    if max_avg_turn_chars is not None
                    else None
                ),
                "min_total_chars": (
                    int(min_total_chars)
                    if min_total_chars is not None
                    else None
                ),
                "max_total_chars": (
                    int(max_total_chars)
                    if max_total_chars is not None
                    else None
                ),
                "retrieval": {
                    key: max(0, int(value))
                    for key, value in retrieval.items()
                },
                "route": {key: bool(value) for key, value in route.items()},
                "selected_context": _normalized_selected_context_override(
                    selected_context
                ),
                "compiler": dict(compiler),
                "answer_finalizer": dict(answer_finalizer),
            }
        )
    return tuple(profiles)


def _normalized_selected_context_override(
    raw: Mapping[str, Any],
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in raw.items():
        if key in {
            "enabled",
            "require_anaphora",
            "require_question_reference",
            "require_source_grounded_self_reference",
            "require_materialized_source_grounded",
        }:
            result[key] = bool(value)
        elif key in {
            "window_before",
            "window_after",
            "max_rows",
            "max_neighbor_chars",
            "max_center_chars",
            "min_context_budget_headroom_chars",
            "require_question_reference_min_center_chars",
            "source_grounded_min_terms",
            "materialized_source_grounded_min_terms",
        }:
            result[key] = int(value)
        elif key in {
            "source_grounded_min_coverage",
            "materialized_source_grounded_min_coverage",
        }:
            result[key] = min(1.0, max(0.0, float(value)))
        elif key == "information_needs":
            result[key] = _tuple_config(value)
        elif key == "context_format":
            result[key] = _selected_context_context_format(value)
        elif key == "timestamp_policy":
            result[key] = _selected_context_timestamp_policy(value)
    return result


def _select_granularity_profile(
    profiles: tuple[dict[str, Any], ...],
    *,
    avg_turn_chars: float,
    total_turn_chars: int,
) -> dict[str, Any] | None:
    for profile in profiles:
        min_chars = profile.get("min_avg_turn_chars")
        max_chars = profile.get("max_avg_turn_chars")
        if min_chars is not None and avg_turn_chars < float(min_chars):
            continue
        if max_chars is not None and avg_turn_chars > float(max_chars):
            continue
        min_total_chars = profile.get("min_total_chars")
        max_total_chars = profile.get("max_total_chars")
        if min_total_chars is not None and total_turn_chars < int(min_total_chars):
            continue
        if max_total_chars is not None and total_turn_chars > int(max_total_chars):
            continue
        return profile
    return None


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
        "chat_template_kwargs": json.dumps(
            _dict_config(answer_config.get("chat_template_kwargs")),
            ensure_ascii=False,
            sort_keys=True,
        ),
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
        "chat_template_kwargs",
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
            chat_template_kwargs=_dict_config(answer_config.get("chat_template_kwargs")),
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
