#!/usr/bin/env python3
"""Run the stage-1 clean skeleton on prediction JSONL."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import sys
import threading
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from common.experiment import (  # noqa: E402
    append_jsonl,
    collect_git_state,
    utc_now_iso,
    write_json,
)
from data.io import load_prediction_jsonl  # noqa: E402
from memory.pipeline import Stage1Pipeline  # noqa: E402


def main() -> int:
    args = _parse_args()
    config = _load_json(args.config)
    run_id = args.run_id
    output_dir = REPO_ROOT / "outputs" / args.experiment_kind / run_id
    experiment_dir = REPO_ROOT / "experiments" / args.experiment_kind / run_id
    predictions_path = output_dir / "predictions.jsonl"
    traces_path = output_dir / "traces.jsonl"

    _reset_file(predictions_path)
    _reset_file(traces_path)

    envelopes = []
    for index, envelope in enumerate(load_prediction_jsonl(args.input), start=1):
        if args.limit is not None and index > args.limit:
            break
        envelopes.append((index, envelope))

    results = _predict_records(envelopes, config, workers=max(1, args.workers))
    records = []
    total_query_tokens = 0
    total_build_tokens = 0
    total_query_think_tokens = 0
    total_build_think_tokens = 0
    total_query_total_tokens = 0
    total_build_total_tokens = 0
    total_evidence_items = 0
    total_compiler_memory_records = 0
    total_context_chars = 0
    total_update_conflict_guide_applied = 0
    total_personalized_advice_contract_applied = 0
    total_compiler_context_pressure_applied = 0
    total_compiler_context_pressure_headroom = 0
    total_compiler_context_pressure_headroom_count = 0
    total_embedding_tokens = 0
    total_effective_top_k = 0
    total_effective_dense_top_k = 0
    total_effective_dense_protect_top_n = 0
    total_turn_window_bm25_applied = 0
    total_turn_window_hits = 0
    total_turn_window_source_hits = 0
    total_selected_context_applied = 0
    total_selected_context_materialized = 0
    total_selected_context_skipped_long_center = 0
    total_selected_context_budget_gate_applied = 0
    total_selected_context_budget_gate_blocked = 0
    total_selected_context_budget_gate_headroom = 0
    total_selected_context_budget_gate_headroom_count = 0
    total_rerank_applied = 0
    total_rerank_candidate_count = 0
    total_rerank_returned_count = 0
    total_rerank_tokens = 0
    total_context_budget_applied = 0
    total_context_budget_candidate_count = 0
    total_context_budget_returned_count = 0
    total_context_budget_estimated_chars = 0
    total_context_budget_dropped_count = 0
    total_embedding_cache_hits = 0
    total_embedding_cache_misses = 0
    total_embedding_cache_writes = 0
    total_build_memory_records = 0
    total_build_memory_active_records = 0
    total_build_memory_superseded_records = 0
    total_build_memory_chunks = 0
    total_build_memory_cache_hits = 0
    total_build_memory_cache_misses = 0
    total_build_memory_cache_writes = 0
    total_build_memory_source_alignment_changed = 0
    total_build_memory_source_alignment_added = 0
    total_memory_hits = 0
    total_memory_source_hits = 0
    total_answer_cache_hits = 0
    total_answer_cache_misses = 0
    total_answer_cache_writes = 0
    total_answer_finalizer_applied = 0
    total_answer_repair_triggered = 0
    total_answer_repair_applied = 0
    total_answer_repair_query_tokens = 0
    total_answer_repair_cache_hits = 0
    total_answer_repair_cache_misses = 0
    total_answer_repair_cache_writes = 0
    for _index, envelope, result in results:
        token_cost = result["trace"]["token_cost"]
        compiled = result["trace"]["compiled_context"]
        prediction_record = {
            "record_key": envelope.record_key,
            "answer": result["answer"],
        }
        trace_record = {
            "record_key": envelope.record_key,
            "trace": result["trace"],
        }
        append_jsonl(predictions_path, prediction_record)
        append_jsonl(traces_path, trace_record)
        records.append(result)
        total_build_tokens += int(token_cost["build_tokens"])
        total_query_tokens += int(token_cost["query_tokens"])
        total_build_think_tokens += int(token_cost.get("build_think_tokens") or 0)
        total_query_think_tokens += int(token_cost.get("query_think_tokens") or 0)
        total_build_total_tokens += int(
            token_cost.get("build_total_tokens")
            if token_cost.get("build_total_tokens") is not None
            else int(token_cost["build_tokens"])
            + int(token_cost.get("build_think_tokens") or 0)
        )
        total_query_total_tokens += int(
            token_cost.get("query_total_tokens")
            if token_cost.get("query_total_tokens") is not None
            else int(token_cost["query_tokens"])
            + int(token_cost.get("query_think_tokens") or 0)
        )
        total_evidence_items += len(compiled["evidence_rows"])
        total_compiler_memory_records += len(compiled.get("memory_records") or [])
        total_context_chars += int(compiled["context_chars"])
        prompt_text = str(compiled.get("prompt") or "")
        if "Update/Conflict Candidate Chain:" in prompt_text:
            total_update_conflict_guide_applied += 1
        if "Personalized Advice Discipline:" in prompt_text:
            total_personalized_advice_contract_applied += 1
        compiler_context_pressure = result["trace"].get(
            "compiler_context_pressure"
        ) or {}
        if compiler_context_pressure.get("applied"):
            total_compiler_context_pressure_applied += 1
        pressure_headroom = compiler_context_pressure.get("headroom_chars")
        if pressure_headroom is not None:
            total_compiler_context_pressure_headroom += int(pressure_headroom)
            total_compiler_context_pressure_headroom_count += 1
        retrieval_trace = result["trace"]["retrieval"]
        total_embedding_tokens += int(retrieval_trace.get("embedding_tokens") or 0)
        total_effective_top_k += int(retrieval_trace.get("top_k") or 0)
        total_effective_dense_top_k += int(retrieval_trace.get("dense_top_k") or 0)
        total_effective_dense_protect_top_n += int(
            retrieval_trace.get("dense_protect_top_n") or 0
        )
        if retrieval_trace.get("turn_window_bm25_applied"):
            total_turn_window_bm25_applied += 1
        total_turn_window_hits += len(retrieval_trace.get("turn_window_hits") or [])
        total_turn_window_source_hits += len(
            retrieval_trace.get("turn_window_source_hits") or []
        )
        selected_context = retrieval_trace.get("selected_context") or {}
        if selected_context.get("applied"):
            total_selected_context_applied += 1
        total_selected_context_materialized += int(
            selected_context.get("materialized_count") or 0
        )
        total_selected_context_skipped_long_center += int(
            selected_context.get("skipped_long_center_count") or 0
        )
        if selected_context.get("budget_gate_applied"):
            total_selected_context_budget_gate_applied += 1
            if not selected_context.get("budget_gate_allowed"):
                total_selected_context_budget_gate_blocked += 1
        budget_headroom = selected_context.get("context_budget_headroom_chars")
        if budget_headroom is not None:
            total_selected_context_budget_gate_headroom += int(budget_headroom)
            total_selected_context_budget_gate_headroom_count += 1
        if retrieval_trace.get("rerank_applied"):
            total_rerank_applied += 1
        total_rerank_candidate_count += int(
            retrieval_trace.get("rerank_candidate_count") or 0
        )
        total_rerank_returned_count += int(
            retrieval_trace.get("rerank_returned_count") or 0
        )
        total_rerank_tokens += int(retrieval_trace.get("rerank_total_tokens") or 0)
        if retrieval_trace.get("context_budget_applied"):
            total_context_budget_applied += 1
        total_context_budget_candidate_count += int(
            retrieval_trace.get("context_budget_candidate_count") or 0
        )
        total_context_budget_returned_count += int(
            retrieval_trace.get("context_budget_returned_count") or 0
        )
        total_context_budget_estimated_chars += int(
            retrieval_trace.get("context_budget_estimated_chars") or 0
        )
        total_context_budget_dropped_count += int(
            retrieval_trace.get("context_budget_dropped_count") or 0
        )
        embedding_cache = retrieval_trace.get("embedding_cache") or {}
        total_embedding_cache_hits += int(embedding_cache.get("hits") or 0)
        total_embedding_cache_misses += int(embedding_cache.get("misses") or 0)
        total_embedding_cache_writes += int(embedding_cache.get("writes") or 0)
        build_memory = result["trace"].get("build_memory") or {}
        build_memory_records = build_memory.get("records") or []
        total_build_memory_records += len(build_memory_records)
        total_build_memory_active_records += sum(
            1 for record in build_memory_records if record.get("status") == "active"
        )
        total_build_memory_superseded_records += sum(
            1
            for record in build_memory_records
            if record.get("status") == "superseded"
        )
        total_build_memory_chunks += int(build_memory.get("chunks") or 0)
        build_memory_cache = build_memory.get("cache") or {}
        total_build_memory_cache_hits += int(build_memory_cache.get("hits") or 0)
        total_build_memory_cache_misses += int(build_memory_cache.get("misses") or 0)
        total_build_memory_cache_writes += int(build_memory_cache.get("writes") or 0)
        source_alignment = result["trace"].get("build_memory_source_alignment") or {}
        total_build_memory_source_alignment_changed += int(
            source_alignment.get("records_changed") or 0
        )
        total_build_memory_source_alignment_added += int(
            source_alignment.get("sources_added") or 0
        )
        total_memory_hits += len(retrieval_trace.get("memory_hits") or [])
        total_memory_source_hits += len(
            retrieval_trace.get("memory_source_hits") or []
        )
        answer_cache = result["trace"].get("answer_cache") or {}
        total_answer_cache_hits += int(answer_cache.get("hits") or 0)
        total_answer_cache_misses += int(answer_cache.get("misses") or 0)
        total_answer_cache_writes += int(answer_cache.get("writes") or 0)
        answer_finalizer = result["trace"].get("answer_finalizer") or {}
        if answer_finalizer.get("applied"):
            total_answer_finalizer_applied += 1
        answer_repair = result["trace"].get("answer_repair") or {}
        if answer_repair.get("triggered"):
            total_answer_repair_triggered += 1
        if answer_repair.get("applied"):
            total_answer_repair_applied += 1
        repair_response = answer_repair.get("response") or {}
        repair_token_usage = repair_response.get("token_usage") or {}
        total_answer_repair_query_tokens += int(
            repair_token_usage.get("query_tokens") or 0
        )
        repair_cache = answer_repair.get("cache") or {}
        total_answer_repair_cache_hits += int(repair_cache.get("hits") or 0)
        total_answer_repair_cache_misses += int(repair_cache.get("misses") or 0)
        total_answer_repair_cache_writes += int(repair_cache.get("writes") or 0)

    sample_count = len(records)
    metrics = {
        "benchmark": args.benchmark,
        "subset": args.subset,
        "experiment_kind": args.experiment_kind,
        "n_samples": sample_count,
        "accuracy": None,
        "f1": None,
        "bleu": None,
        "metrics_note": "No gold answers or judge outputs are used by this prediction runner.",
        "token_cost": {
            "total_build_tokens": total_build_tokens,
            "total_query_tokens": total_query_tokens,
            "total_build_think_tokens": total_build_think_tokens,
            "total_query_think_tokens": total_query_think_tokens,
            "total_build_total_tokens": total_build_total_tokens,
            "total_query_total_tokens": total_query_total_tokens,
            "avg_build_tokens": _safe_average(total_build_tokens, sample_count),
            "avg_query_tokens": _safe_average(total_query_tokens, sample_count),
            "avg_build_think_tokens": _safe_average(
                total_build_think_tokens,
                sample_count,
            ),
            "avg_query_think_tokens": _safe_average(
                total_query_think_tokens,
                sample_count,
            ),
            "avg_build_total_tokens": _safe_average(
                total_build_total_tokens,
                sample_count,
            ),
            "avg_query_total_tokens": _safe_average(
                total_query_total_tokens,
                sample_count,
            ),
        },
        "retrieval": {
            "top_k": config.get("retrieval", {}).get("top_k"),
            "max_top_k": config.get("retrieval", {}).get("max_top_k"),
            "route_overrides": config.get("retrieval", {}).get("route_overrides") or {},
            "avg_effective_top_k": _safe_average(
                total_effective_top_k, sample_count
            ),
            "avg_effective_dense_top_k": _safe_average(
                total_effective_dense_top_k, sample_count
            ),
            "avg_effective_dense_protect_top_n": _safe_average(
                total_effective_dense_protect_top_n, sample_count
            ),
            "neighbor_window": config.get("retrieval", {}).get("neighbor_window"),
            "neighbor_order": config.get("retrieval", {}).get(
                "neighbor_order", "hit_priority"
            ),
            "drop_query_stopwords": config.get("retrieval", {}).get(
                "drop_query_stopwords", False
            ),
            "lexical_enabled": config.get("retrieval", {})
            .get("lexical", {})
            .get("enabled", True),
            "build_memory_enabled": config.get("build_memory", {}).get(
                "enabled", False
            ),
            "build_memory_top_k": config.get("build_memory", {}).get("top_k"),
            "build_memory_max_sources_per_record": config.get("build_memory", {}).get(
                "max_sources_per_record"
            ),
            "build_memory_include_superseded": config.get("build_memory", {}).get(
                "include_superseded", False
            ),
            "build_memory_include_superseded_information_needs": config.get(
                "build_memory", {}
            ).get("include_superseded_information_needs"),
            "avg_memory_hits": _safe_average(total_memory_hits, sample_count),
            "avg_memory_source_hits": _safe_average(
                total_memory_source_hits, sample_count
            ),
            "dense_enabled": config.get("retrieval", {})
            .get("dense", {})
            .get("enabled", False),
            "lexical_protect_top_n": config.get("retrieval", {})
            .get("dense", {})
            .get("lexical_protect_top_n"),
            "dense_protect_top_n": config.get("retrieval", {})
            .get("dense", {})
            .get("protect_top_n"),
            "dense_document_text_mode": config.get("retrieval", {})
            .get("dense", {})
            .get("document_text_mode", "text"),
            "dense_query_text_mode": config.get("retrieval", {})
            .get("dense", {})
            .get("query_text_mode", "question"),
            "embedding_cache_enabled": config.get("retrieval", {})
            .get("dense", {})
            .get("cache", {})
            .get("enabled", False),
            "embedding_cache_path": config.get("retrieval", {})
            .get("dense", {})
            .get("cache", {})
            .get("path"),
            "embedding_cache_hits": total_embedding_cache_hits,
            "embedding_cache_misses": total_embedding_cache_misses,
            "embedding_cache_writes": total_embedding_cache_writes,
            "turn_window_bm25_enabled": config.get("retrieval", {})
            .get("turn_window_bm25", {})
            .get("enabled", False),
            "turn_window_top_k": config.get("retrieval", {})
            .get("turn_window_bm25", {})
            .get("top_k"),
            "turn_window_window_before": config.get("retrieval", {})
            .get("turn_window_bm25", {})
            .get("window_before"),
            "turn_window_window_after": config.get("retrieval", {})
            .get("turn_window_bm25", {})
            .get("window_after"),
            "turn_window_max_sources_per_window": config.get("retrieval", {})
            .get("turn_window_bm25", {})
            .get("max_sources_per_window"),
            "turn_window_max_chars_per_turn": config.get("retrieval", {})
            .get("turn_window_bm25", {})
            .get("max_chars_per_turn"),
            "turn_window_enabled_route_signals": config.get("retrieval", {})
            .get("turn_window_bm25", {})
            .get("enabled_route_signals"),
            "turn_window_enabled_information_needs": config.get("retrieval", {})
            .get("turn_window_bm25", {})
            .get("enabled_information_needs"),
            "turn_window_enabled_query_patterns": config.get("retrieval", {})
            .get("turn_window_bm25", {})
            .get("enabled_query_patterns"),
            "turn_window_bm25_applied_count": total_turn_window_bm25_applied,
            "turn_window_bm25_applied_rate": _safe_average(
                total_turn_window_bm25_applied, sample_count
            ),
            "avg_turn_window_hits": _safe_average(
                total_turn_window_hits, sample_count
            ),
            "avg_turn_window_source_hits": _safe_average(
                total_turn_window_source_hits, sample_count
            ),
            "selected_context_enabled": config.get("retrieval", {})
            .get("selected_context", {})
            .get("enabled", False),
            "selected_context_window_before": config.get("retrieval", {})
            .get("selected_context", {})
            .get("window_before"),
            "selected_context_window_after": config.get("retrieval", {})
            .get("selected_context", {})
            .get("window_after"),
            "selected_context_max_rows": config.get("retrieval", {})
            .get("selected_context", {})
            .get("max_rows"),
            "selected_context_max_neighbor_chars": config.get("retrieval", {})
            .get("selected_context", {})
            .get("max_neighbor_chars"),
            "selected_context_max_center_chars": config.get("retrieval", {})
            .get("selected_context", {})
            .get("max_center_chars"),
            "selected_context_information_needs": config.get("retrieval", {})
            .get("selected_context", {})
            .get("information_needs"),
            "selected_context_require_anaphora": config.get("retrieval", {})
            .get("selected_context", {})
            .get("require_anaphora"),
            "selected_context_min_context_budget_headroom_chars": config.get(
                "retrieval", {}
            )
            .get("selected_context", {})
            .get("min_context_budget_headroom_chars"),
            "selected_context_applied_count": total_selected_context_applied,
            "selected_context_applied_rate": _safe_average(
                total_selected_context_applied, sample_count
            ),
            "selected_context_budget_gate_applied_count": (
                total_selected_context_budget_gate_applied
            ),
            "selected_context_budget_gate_blocked_count": (
                total_selected_context_budget_gate_blocked
            ),
            "avg_selected_context_budget_gate_headroom_chars": _safe_average(
                total_selected_context_budget_gate_headroom,
                total_selected_context_budget_gate_headroom_count,
            ),
            "avg_selected_context_materialized_rows": _safe_average(
                total_selected_context_materialized, sample_count
            ),
            "avg_selected_context_skipped_long_center_rows": _safe_average(
                total_selected_context_skipped_long_center, sample_count
            ),
            "rerank_enabled": config.get("retrieval", {})
            .get("rerank", {})
            .get("enabled", False),
            "rerank_model": config.get("retrieval", {}).get("rerank", {}).get("model"),
            "rerank_base_url": config.get("retrieval", {})
            .get("rerank", {})
            .get("base_url"),
            "rerank_pool_k": config.get("retrieval", {}).get("rerank", {}).get("pool_k"),
            "rerank_query_text_mode": config.get("retrieval", {})
            .get("rerank", {})
            .get("query_text_mode"),
            "rerank_document_max_chars": config.get("retrieval", {})
            .get("rerank", {})
            .get("document_max_chars"),
            "rerank_document_text_mode": config.get("retrieval", {})
            .get("rerank", {})
            .get("document_text_mode", "turn"),
            "rerank_document_neighbor_window": config.get("retrieval", {})
            .get("rerank", {})
            .get("document_neighbor_window"),
            "rerank_document_max_memory_records": config.get("retrieval", {})
            .get("rerank", {})
            .get("document_max_memory_records"),
            "rerank_anchor_keep": config.get("retrieval", {})
            .get("rerank", {})
            .get("anchor_keep"),
            "rerank_anchor_after_top": config.get("retrieval", {})
            .get("rerank", {})
            .get("anchor_after_top"),
            "rerank_information_needs": config.get("retrieval", {})
            .get("rerank", {})
            .get("information_needs"),
            "rerank_applied_count": total_rerank_applied,
            "rerank_applied_rate": _safe_average(total_rerank_applied, sample_count),
            "avg_rerank_candidate_count": _safe_average(
                total_rerank_candidate_count,
                total_rerank_applied,
            ),
            "avg_rerank_returned_count": _safe_average(
                total_rerank_returned_count,
                total_rerank_applied,
            ),
            "total_rerank_tokens": total_rerank_tokens,
            "avg_rerank_tokens_when_applied": _safe_average(
                total_rerank_tokens,
                total_rerank_applied,
            ),
            "context_budget_enabled": config.get("retrieval", {})
            .get("context_budget", {})
            .get("enabled", False),
            "context_budget_max_chars": config.get("retrieval", {})
            .get("context_budget", {})
            .get("max_chars"),
            "context_budget_min_hits": config.get("retrieval", {})
            .get("context_budget", {})
            .get("min_hits"),
            "context_budget_protect_top_n": config.get("retrieval", {})
            .get("context_budget", {})
            .get("protect_top_n"),
            "context_budget_max_hits": config.get("retrieval", {})
            .get("context_budget", {})
            .get("max_hits"),
            "context_budget_information_needs": config.get("retrieval", {})
            .get("context_budget", {})
            .get("information_needs"),
            "context_budget_applied_count": total_context_budget_applied,
            "context_budget_applied_rate": _safe_average(
                total_context_budget_applied, sample_count
            ),
            "avg_context_budget_candidate_count": _safe_average(
                total_context_budget_candidate_count,
                total_context_budget_applied,
            ),
            "avg_context_budget_returned_count": _safe_average(
                total_context_budget_returned_count,
                total_context_budget_applied,
            ),
            "avg_context_budget_estimated_chars": _safe_average(
                total_context_budget_estimated_chars,
                total_context_budget_applied,
            ),
            "avg_context_budget_dropped_count": _safe_average(
                total_context_budget_dropped_count,
                total_context_budget_applied,
            ),
            "total_embedding_tokens": total_embedding_tokens,
            "avg_embedding_tokens": _safe_average(total_embedding_tokens, sample_count),
            "avg_compiled_evidence_items": _safe_average(
                total_evidence_items, sample_count
            ),
            "avg_context_chars": _safe_average(total_context_chars, sample_count),
        },
        "build_memory": {
            "enabled": config.get("build_memory", {}).get("enabled", False),
            "mode": config.get("build_memory", {}).get("mode"),
            "model": config.get("build_memory", {}).get("model"),
            "base_url": config.get("build_memory", {}).get("base_url"),
            "temperature": config.get("build_memory", {}).get("temperature"),
            "max_tokens": config.get("build_memory", {}).get("max_tokens"),
            "max_turns_per_chunk": config.get("build_memory", {}).get(
                "max_turns_per_chunk"
            ),
            "overlap_turns": config.get("build_memory", {}).get("overlap_turns", 0),
            "max_chars_per_turn": config.get("build_memory", {}).get(
                "max_chars_per_turn"
            ),
            "max_records_per_chunk": config.get("build_memory", {}).get(
                "max_records_per_chunk"
            ),
            "chat_template_kwargs": config.get("build_memory", {}).get(
                "chat_template_kwargs"
            ),
            "temporal_fields": config.get("build_memory", {}).get(
                "temporal_fields", False
            ),
            "prompt_profile": config.get("build_memory", {}).get(
                "prompt_profile", "typed_compact"
            ),
            "manage_facts": config.get("build_memory", {}).get("manage_facts", True),
            "include_superseded": config.get("build_memory", {}).get(
                "include_superseded", False
            ),
            "include_superseded_information_needs": config.get("build_memory", {}).get(
                "include_superseded_information_needs"
            ),
            "cache_enabled": config.get("build_memory", {})
            .get("cache", {})
            .get("enabled", False),
            "cache_path": config.get("build_memory", {})
            .get("cache", {})
            .get("path"),
            "cache_hits": total_build_memory_cache_hits,
            "cache_misses": total_build_memory_cache_misses,
            "cache_writes": total_build_memory_cache_writes,
            "source_alignment": config.get("build_memory", {}).get(
                "source_alignment", {}
            ),
            "source_alignment_changed_records": (
                total_build_memory_source_alignment_changed
            ),
            "source_alignment_added_sources": (
                total_build_memory_source_alignment_added
            ),
            "avg_source_alignment_changed_records": _safe_average(
                total_build_memory_source_alignment_changed,
                sample_count,
            ),
            "avg_source_alignment_added_sources": _safe_average(
                total_build_memory_source_alignment_added,
                sample_count,
            ),
            "total_chunks": total_build_memory_chunks,
            "avg_chunks": _safe_average(total_build_memory_chunks, sample_count),
            "total_records": total_build_memory_records,
            "total_active_records": total_build_memory_active_records,
            "total_superseded_records": total_build_memory_superseded_records,
            "avg_records": _safe_average(total_build_memory_records, sample_count),
            "avg_active_records": _safe_average(
                total_build_memory_active_records, sample_count
            ),
        },
        "answer": {
            **_answer_metrics(config),
            "cache_hits": total_answer_cache_hits,
            "cache_misses": total_answer_cache_misses,
            "cache_writes": total_answer_cache_writes,
            "finalizer_applied_count": total_answer_finalizer_applied,
            "finalizer_applied_rate": _safe_average(
                total_answer_finalizer_applied,
                sample_count,
            ),
            "repair_triggered_count": total_answer_repair_triggered,
            "repair_triggered_rate": _safe_average(
                total_answer_repair_triggered,
                sample_count,
            ),
            "repair_applied_count": total_answer_repair_applied,
            "repair_applied_rate": _safe_average(
                total_answer_repair_applied,
                sample_count,
            ),
            "repair_total_query_tokens": total_answer_repair_query_tokens,
            "repair_avg_query_tokens_when_triggered": _safe_average(
                total_answer_repair_query_tokens,
                total_answer_repair_triggered,
            ),
            "repair_cache_hits": total_answer_repair_cache_hits,
            "repair_cache_misses": total_answer_repair_cache_misses,
            "repair_cache_writes": total_answer_repair_cache_writes,
        },
        "compiler": {
            "prompt_mode": config.get("compiler", {}).get("prompt_mode", "default"),
            "answer_style": config.get("compiler", {}).get("answer_style", "grounded"),
            "memory_record_source": config.get("compiler", {}).get(
                "memory_record_source", "retrieval"
            ),
            "avg_compiled_memory_records": _safe_average(
                total_compiler_memory_records, sample_count
            ),
            "evidence_order": config.get("compiler", {}).get(
                "evidence_order", "retrieval"
            ),
            "memory_order": config.get("compiler", {}).get(
                "memory_order", "retrieval"
            ),
            "memory_layout": config.get("compiler", {}).get(
                "memory_layout", "flat"
            ),
            "row_text_mode": config.get("compiler", {}).get("row_text_mode", "full"),
            "max_row_text_chars": config.get("compiler", {}).get(
                "max_row_text_chars", 0
            ),
            "evidence_row_labels": config.get("compiler", {}).get(
                "evidence_row_labels", False
            ),
            "final_answer_checklist": config.get("compiler", {}).get(
                "final_answer_checklist", False
            ),
            "max_memory_records": config.get("compiler", {}).get(
                "max_memory_records", 12
            ),
            "route_guidance": config.get("compiler", {}).get(
                "route_guidance", False
            ),
            "temporal_grounding": config.get("compiler", {}).get(
                "temporal_grounding", False
            ),
            "temporal_hints": config.get("compiler", {}).get("temporal_hints", False),
            "temporal_workpad": config.get("compiler", {}).get(
                "temporal_workpad", False
            ),
            "temporal_text_normalization": config.get("compiler", {}).get(
                "temporal_text_normalization", False
            ),
            "temporal_event_contract": config.get("compiler", {}).get(
                "temporal_event_contract", False
            ),
            "temporal_workpad_scope": config.get("compiler", {}).get(
                "temporal_workpad_scope", "route"
            ),
            "temporal_workpad_max_rows": config.get("compiler", {}).get(
                "temporal_workpad_max_rows", 10
            ),
            "temporal_workpad_max_pairs": config.get("compiler", {}).get(
                "temporal_workpad_max_pairs", 12
            ),
            "structured_guide": config.get("compiler", {}).get(
                "structured_guide", False
            ),
            "structured_guide_max_rows": config.get("compiler", {}).get(
                "structured_guide_max_rows", 12
            ),
            "structured_guide_include_rows": config.get("compiler", {}).get(
                "structured_guide_include_rows", True
            ),
            "structured_guide_include_memory": config.get("compiler", {}).get(
                "structured_guide_include_memory", True
            ),
            "structured_guide_disabled_signals": config.get("compiler", {}).get(
                "structured_guide_disabled_signals"
            ),
            "structured_answer_contract": config.get("compiler", {}).get(
                "structured_answer_contract", False
            ),
            "structured_answer_contract_information_needs": config.get(
                "compiler", {}
            ).get("structured_answer_contract_information_needs"),
            "structured_answer_contract_max_items": config.get("compiler", {}).get(
                "structured_answer_contract_max_items", 10
            ),
            "evidence_report_contract": config.get("compiler", {}).get(
                "evidence_report_contract", False
            ),
            "evidence_report_information_needs": config.get("compiler", {}).get(
                "evidence_report_information_needs"
            ),
            "evidence_report_max_items": config.get("compiler", {}).get(
                "evidence_report_max_items", 8
            ),
            "evidence_report_detail": config.get("compiler", {}).get(
                "evidence_report_detail", False
            ),
            "aggregation_report_contract": config.get("compiler", {}).get(
                "aggregation_report_contract", False
            ),
            "aggregation_report_information_needs": config.get("compiler", {}).get(
                "aggregation_report_information_needs"
            ),
            "candidate_guide": config.get("compiler", {}).get(
                "candidate_guide", False
            ),
            "candidate_guide_information_needs": config.get("compiler", {}).get(
                "candidate_guide_information_needs"
            ),
            "candidate_guide_max_rows": config.get("compiler", {}).get(
                "candidate_guide_max_rows", 6
            ),
            "candidate_guide_snippet_chars": config.get("compiler", {}).get(
                "candidate_guide_snippet_chars", 160
            ),
            "update_conflict_guide": config.get("compiler", {}).get(
                "update_conflict_guide", False
            ),
            "update_conflict_guide_information_needs": config.get(
                "compiler", {}
            ).get("update_conflict_guide_information_needs"),
            "update_conflict_guide_max_rows": config.get("compiler", {}).get(
                "update_conflict_guide_max_rows", 6
            ),
            "update_conflict_guide_snippet_chars": config.get("compiler", {}).get(
                "update_conflict_guide_snippet_chars", 180
            ),
            "update_conflict_guide_applied": total_update_conflict_guide_applied,
            "operation_workpad": config.get("compiler", {}).get(
                "operation_workpad", False
            ),
            "operation_workpad_information_needs": config.get("compiler", {}).get(
                "operation_workpad_information_needs"
            ),
            "operation_workpad_question_gate": config.get("compiler", {}).get(
                "operation_workpad_question_gate", False
            ),
            "personalized_advice_contract": config.get("compiler", {}).get(
                "personalized_advice_contract", False
            ),
            "personalized_advice_contract_applied": (
                total_personalized_advice_contract_applied
            ),
            "context_pressure_enabled": config.get("compiler", {})
            .get("context_pressure", {})
            .get("enabled", False),
            "context_pressure_max_headroom_chars": config.get("compiler", {})
            .get("context_pressure", {})
            .get("max_headroom_chars"),
            "context_pressure_overrides": config.get("compiler", {})
            .get("context_pressure", {})
            .get("compiler"),
            "context_pressure_applied_count": (
                total_compiler_context_pressure_applied
            ),
            "context_pressure_applied_rate": _safe_average(
                total_compiler_context_pressure_applied,
                sample_count,
            ),
            "avg_context_pressure_headroom_chars": _safe_average(
                total_compiler_context_pressure_headroom,
                total_compiler_context_pressure_headroom_count,
            ),
            "current_state_update_contract": config.get("compiler", {}).get(
                "current_state_update_contract", False
            ),
            "dialogue_inference_contract": config.get("compiler", {}).get(
                "dialogue_inference_contract", False
            ),
            "temporal_order_contract": config.get("compiler", {}).get(
                "temporal_order_contract", False
            ),
            "source_anchor_keep": config.get("compiler", {}).get(
                "source_anchor_keep", 0
            ),
            "source_anchor_memory_rows": config.get("compiler", {}).get(
                "source_anchor_memory_rows", 0
            ),
            "source_anchor_per_session": config.get("compiler", {}).get(
                "source_anchor_per_session", 0
            ),
            "source_anchor_session_rows": config.get("compiler", {}).get(
                "source_anchor_session_rows", 0
            ),
            "route_overrides": config.get("compiler", {}).get(
                "route_overrides", {}
            ),
        },
        "route": {
            "enable_broad_list_patterns": config.get("route", {}).get(
                "enable_broad_list_patterns", False
            ),
            "enable_recommendation_profile_patterns": config.get("route", {}).get(
                "enable_recommendation_profile_patterns", False
            ),
            "enable_advice_profile_patterns": config.get("route", {}).get(
                "enable_advice_profile_patterns", False
            ),
            "temporal_priority_over_recent": config.get("route", {}).get(
                "temporal_priority_over_recent", False
            ),
        },
        "runner": {
            "workers": max(1, args.workers),
        },
    }
    manifest = {
        "run_id": run_id,
        "created_at_utc": utc_now_iso(),
        "benchmark": args.benchmark,
        "subset": args.subset,
        "experiment_kind": args.experiment_kind,
        "config_path": str(Path(args.config).resolve()),
        "input_path": str(Path(args.input).resolve()),
        "output_path": str(predictions_path),
        "trace_path": str(traces_path),
        "outputs": {
            "predictions": str(predictions_path),
            "traces": str(traces_path),
        },
        "experiment_dir": str(experiment_dir),
        "git": collect_git_state(REPO_ROOT),
        "clean_assertions": [
            "Prediction loader rejects gold/reference/target answers.",
            "Prediction loader rejects judge outputs and benchmark labels.",
            "Prediction loader rejects sample ids, qids, and row indices.",
            "record_key is copied only by the runner and is not passed into pipeline modules.",
            "Derived context rows always retain raw source_id back-links.",
            "Build-stage typed memory is created only from raw dialogue turns and visible metadata.",
        ],
    }

    experiment_dir.mkdir(parents=True, exist_ok=True)
    write_json(experiment_dir / "metrics.json", metrics)
    write_json(experiment_dir / "manifest.json", manifest)
    write_json(experiment_dir / "config_snapshot.json", config)
    _write_summary(experiment_dir / "summary.md", manifest, metrics, args, config)
    _write_diagnosis(experiment_dir / "diagnosis.md", manifest, metrics, config)
    return 0


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        default=str(REPO_ROOT / "data" / "examples" / "toy_memory.jsonl"),
        help="Clean prediction JSONL. Must not contain gold/judge/label/id fields.",
    )
    parser.add_argument(
        "--config",
        default=str(REPO_ROOT / "configs" / "stage1_clean_skeleton.json"),
    )
    parser.add_argument("--run-id", default=f"stage1_smoke_{utc_now_iso().replace(':', '')}")
    parser.add_argument("--benchmark", default="toy")
    parser.add_argument("--subset", default="smoke")
    parser.add_argument("--experiment-kind", default="smoke")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Number of samples to predict concurrently. Outputs are still written in input order.",
    )
    return parser.parse_args()


def _predict_records(
    envelopes: list[tuple[int, Any]],
    config: dict[str, Any],
    workers: int,
) -> list[tuple[int, Any, dict[str, Any]]]:
    if workers <= 1:
        pipeline = Stage1Pipeline(config)
        results = []
        for index, envelope in envelopes:
            results.append((index, envelope, pipeline.predict(envelope.request)))
            _report_progress(len(results), len(envelopes))
        return results

    thread_local = threading.local()

    def pipeline_for_thread() -> Stage1Pipeline:
        pipeline = getattr(thread_local, "pipeline", None)
        if pipeline is None:
            pipeline = Stage1Pipeline(config)
            thread_local.pipeline = pipeline
        return pipeline

    def predict_one(item: tuple[int, Any]) -> tuple[int, Any, dict[str, Any]]:
        index, envelope = item
        return index, envelope, pipeline_for_thread().predict(envelope.request)

    results_by_position: list[tuple[int, Any, dict[str, Any]] | None] = [
        None
    ] * len(envelopes)
    completed = 0
    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_to_position = {
            executor.submit(predict_one, item): position
            for position, item in enumerate(envelopes)
        }
        for future in as_completed(future_to_position):
            position = future_to_position[future]
            results_by_position[position] = future.result()
            completed += 1
            _report_progress(completed, len(envelopes))

    return [result for result in results_by_position if result is not None]


def _report_progress(completed: int, total: int) -> None:
    if total == 0:
        return
    if completed == total or completed % 10 == 0:
        print(f"completed {completed}/{total}", file=sys.stderr, flush=True)


def _load_json(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _reset_file(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("", encoding="utf-8")


def _safe_average(total: int, count: int) -> float | None:
    if count == 0:
        return None
    return total / count


def _answer_metrics(config: dict[str, Any]) -> dict[str, Any]:
    answer_config = config.get("answer", {})
    max_output_tokens = _answer_max_output_tokens(answer_config)
    cache_config = answer_config.get("cache", {})
    repair_config = answer_config.get("repair", {})
    repair_cache_config = repair_config.get("cache", {})
    repair_answer_config = _repair_answer_config_for_metrics(answer_config, repair_config)
    return {
        "mode": answer_config.get("mode", "null_answerer"),
        "model": answer_config.get("model"),
        "base_url": answer_config.get("base_url"),
        "temperature": answer_config.get("temperature"),
        "max_input_tokens": answer_config.get("max_input_tokens"),
        "max_output_tokens": max_output_tokens,
        "max_tokens": max_output_tokens,
        "chat_template_kwargs": answer_config.get("chat_template_kwargs"),
        "output_format": answer_config.get("output_format", "text"),
        "timeout": answer_config.get("timeout"),
        "cache_enabled": cache_config.get("enabled", False),
        "cache_path": cache_config.get("path"),
        "cache_namespace": _answer_cache_namespace(answer_config),
        "finalizer_enabled": answer_config.get("finalizer", {}).get(
            "enabled", False
        ),
        "finalizer_mode": answer_config.get("finalizer", {}).get(
            "mode", "structured_evidence_mechanical"
        ),
        "finalizer_enable_count_correction": answer_config.get(
            "finalizer", {}
        ).get("enable_count_correction", False),
        "finalizer_enable_evidence_report_count_correction": answer_config.get(
            "finalizer", {}
        ).get("enable_evidence_report_count_correction", False),
        "finalizer_enable_money_sum_correction": answer_config.get(
            "finalizer", {}
        ).get("enable_money_sum_correction", True),
        "finalizer_enable_duration_rounding_correction": answer_config.get(
            "finalizer", {}
        ).get("enable_duration_rounding_correction", False),
        "finalizer_enable_missing_detail": answer_config.get("finalizer", {}).get(
            "enable_missing_detail", False
        ),
        "finalizer_enable_relative_time_calculation": answer_config.get(
            "finalizer", {}
        ).get("enable_relative_time_calculation", False),
        "repair_enabled": repair_config.get("enabled", False),
        "repair_mode": repair_config.get("mode", answer_config.get("mode")),
        "repair_model": repair_answer_config.get("model"),
        "repair_base_url": repair_answer_config.get("base_url"),
        "repair_temperature": repair_answer_config.get("temperature"),
        "repair_max_input_tokens": repair_answer_config.get("max_input_tokens"),
        "repair_max_output_tokens": _answer_max_output_tokens(repair_answer_config),
        "repair_chat_template_kwargs": repair_answer_config.get(
            "chat_template_kwargs"
        ),
        "repair_output_format": repair_answer_config.get("output_format", "json_answer"),
        "repair_information_needs": repair_config.get("information_needs"),
        "repair_enable_uncertain_trigger": repair_config.get(
            "enable_uncertain_trigger", True
        ),
        "repair_enable_short_list_trigger": repair_config.get(
            "enable_short_list_trigger", True
        ),
        "repair_enable_temporal_conflict_trigger": repair_config.get(
            "enable_temporal_conflict_trigger", True
        ),
        "repair_enable_profile_preference_trigger": repair_config.get(
            "enable_profile_preference_trigger", False
        ),
        "repair_enable_modal_abstention_trigger": repair_config.get(
            "enable_modal_abstention_trigger", False
        ),
        "repair_max_context_chars": repair_config.get("max_context_chars", 14000),
        "repair_max_row_text_chars": repair_config.get("max_row_text_chars", 700),
        "repair_cache_enabled": repair_cache_config.get("enabled", False),
        "repair_cache_path": repair_cache_config.get("path"),
        "repair_cache_namespace": repair_cache_config.get("namespace"),
    }


def _answer_note(config: dict[str, Any]) -> str:
    answer = _answer_metrics(config)
    if answer["mode"] == "openai_compatible":
        return (
            "OpenAI-compatible answerer using "
            f"{answer['model']} at {answer['base_url']} with temperature "
            f"{answer['temperature']}, max_input_tokens "
            f"{answer['max_input_tokens']}, and max_output_tokens "
            f"{answer['max_output_tokens']}, chat_template_kwargs "
            f"{answer['chat_template_kwargs']}."
        )
    if answer["mode"] == "null_answerer":
        return "Null answerer; generated answers are placeholders and accuracy is not meaningful."
    return f"Answer mode: {answer['mode']}."


def _repair_answer_config_for_metrics(
    answer_config: dict[str, Any],
    repair_config: dict[str, Any],
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
    merged = {
        key: answer_config[key] for key in inherited_keys if key in answer_config
    }
    for key in inherited_keys:
        if key in repair_config:
            merged[key] = repair_config[key]
    if "output_format" not in merged:
        merged["output_format"] = "json_answer"
    return merged


def _write_summary(
    path: Path,
    manifest: dict[str, Any],
    metrics: dict[str, Any],
    args: argparse.Namespace,
    config: dict[str, Any],
) -> None:
    git_state = manifest["git"]
    outputs = manifest["outputs"]
    lines = [
        f"# {manifest['run_id']}",
        "",
        "## Purpose",
        "",
        "Stage-1 clean skeleton run: validate raw evidence storage, lexical retrieval, neighbor expansion, evidence compilation, answer generation, trace output, and experiment bookkeeping.",
        "",
        "## Scope",
        "",
        f"- benchmark: {args.benchmark}",
        f"- subset: {args.subset}",
        f"- experiment_kind: {args.experiment_kind}",
        f"- limit: {args.limit}",
        f"- workers: {max(1, args.workers)}",
        f"- input_path: {manifest['input_path']}",
        f"- config_path: {manifest['config_path']}",
        f"- answer: {_answer_note(config)}",
        "",
        "## Git",
        "",
        f"- inside_work_tree: {git_state['inside_work_tree']}",
        f"- commit: {git_state['commit']}",
        f"- dirty: {git_state['dirty']}",
        f"- note: {git_state['note']}",
        "",
        "## Metrics",
        "",
        f"- n_samples: {metrics['n_samples']}",
        f"- accuracy: {metrics['accuracy']}",
        f"- f1: {metrics['f1']}",
        f"- bleu: {metrics['bleu']}",
        f"- avg_build_tokens: {metrics['token_cost']['avg_build_tokens']}",
        f"- avg_build_think_tokens: {metrics['token_cost']['avg_build_think_tokens']}",
        f"- avg_build_total_tokens: {metrics['token_cost']['avg_build_total_tokens']}",
        "- build_token_accounting: logical cold-build visible LLM tokens; cached build chunks count from stored usage, while cache hits only avoid repeated local API calls.",
        f"- avg_query_tokens: {metrics['token_cost']['avg_query_tokens']}",
        f"- avg_query_think_tokens: {metrics['token_cost']['avg_query_think_tokens']}",
        f"- avg_query_total_tokens: {metrics['token_cost']['avg_query_total_tokens']}",
        "- token_accounting_note: avg_build_tokens / avg_query_tokens exclude explicit reasoning tokens when the provider reports them; avg_*_total_tokens include visible plus think tokens.",
        f"- avg_compiled_evidence_items: {metrics['retrieval']['avg_compiled_evidence_items']}",
        f"- retrieval_route_overrides: {metrics['retrieval']['route_overrides']}",
        f"- avg_effective_top_k: {metrics['retrieval']['avg_effective_top_k']}",
        f"- avg_effective_dense_top_k: {metrics['retrieval']['avg_effective_dense_top_k']}",
        f"- avg_effective_dense_protect_top_n: {metrics['retrieval']['avg_effective_dense_protect_top_n']}",
        f"- build_memory_enabled: {metrics['build_memory']['enabled']}",
        f"- build_memory_model: {metrics['build_memory']['model']}",
        f"- build_memory_temporal_fields: {metrics['build_memory']['temporal_fields']}",
        f"- build_memory_prompt_profile: {metrics['build_memory']['prompt_profile']}",
        f"- build_memory_manage_facts: {metrics['build_memory']['manage_facts']}",
        f"- build_memory_overlap_turns: {metrics['build_memory']['overlap_turns']}",
        f"- build_memory_chat_template_kwargs: {metrics['build_memory']['chat_template_kwargs']}",
        f"- build_memory_cache_enabled: {metrics['build_memory']['cache_enabled']}",
        f"- build_memory_cache_path: {metrics['build_memory']['cache_path']}",
        f"- build_memory_cache_hits: {metrics['build_memory']['cache_hits']}",
        f"- build_memory_cache_misses: {metrics['build_memory']['cache_misses']}",
        f"- build_memory_cache_writes: {metrics['build_memory']['cache_writes']}",
        f"- build_memory_source_alignment: {metrics['build_memory']['source_alignment']}",
        f"- build_memory_source_alignment_changed_records: {metrics['build_memory']['source_alignment_changed_records']}",
        f"- build_memory_source_alignment_added_sources: {metrics['build_memory']['source_alignment_added_sources']}",
        f"- avg_build_memory_source_alignment_changed_records: {metrics['build_memory']['avg_source_alignment_changed_records']}",
        f"- avg_build_memory_source_alignment_added_sources: {metrics['build_memory']['avg_source_alignment_added_sources']}",
        f"- avg_build_memory_records: {metrics['build_memory']['avg_records']}",
        f"- avg_active_build_memory_records: {metrics['build_memory']['avg_active_records']}",
        f"- avg_memory_hits: {metrics['retrieval']['avg_memory_hits']}",
        f"- avg_memory_source_hits: {metrics['retrieval']['avg_memory_source_hits']}",
        f"- build_memory_include_superseded: {metrics['retrieval']['build_memory_include_superseded']}",
        f"- build_memory_include_superseded_information_needs: {metrics['retrieval']['build_memory_include_superseded_information_needs']}",
        f"- neighbor_order: {metrics['retrieval']['neighbor_order']}",
        f"- drop_query_stopwords: {metrics['retrieval']['drop_query_stopwords']}",
        f"- lexical_enabled: {metrics['retrieval']['lexical_enabled']}",
        f"- dense_enabled: {metrics['retrieval']['dense_enabled']}",
        f"- lexical_protect_top_n: {metrics['retrieval']['lexical_protect_top_n']}",
        f"- dense_protect_top_n: {metrics['retrieval']['dense_protect_top_n']}",
        f"- dense_document_text_mode: {metrics['retrieval']['dense_document_text_mode']}",
        f"- dense_query_text_mode: {metrics['retrieval']['dense_query_text_mode']}",
        f"- embedding_cache_enabled: {metrics['retrieval']['embedding_cache_enabled']}",
        f"- embedding_cache_path: {metrics['retrieval']['embedding_cache_path']}",
        f"- embedding_cache_hits: {metrics['retrieval']['embedding_cache_hits']}",
        f"- embedding_cache_misses: {metrics['retrieval']['embedding_cache_misses']}",
        f"- embedding_cache_writes: {metrics['retrieval']['embedding_cache_writes']}",
        f"- turn_window_bm25_enabled: {metrics['retrieval']['turn_window_bm25_enabled']}",
        f"- turn_window_top_k: {metrics['retrieval']['turn_window_top_k']}",
        f"- turn_window_window_before: {metrics['retrieval']['turn_window_window_before']}",
        f"- turn_window_window_after: {metrics['retrieval']['turn_window_window_after']}",
        f"- turn_window_max_sources_per_window: {metrics['retrieval']['turn_window_max_sources_per_window']}",
        f"- turn_window_max_chars_per_turn: {metrics['retrieval']['turn_window_max_chars_per_turn']}",
        f"- turn_window_enabled_route_signals: {metrics['retrieval']['turn_window_enabled_route_signals']}",
        f"- turn_window_enabled_information_needs: {metrics['retrieval']['turn_window_enabled_information_needs']}",
        f"- turn_window_enabled_query_patterns: {metrics['retrieval']['turn_window_enabled_query_patterns']}",
        f"- turn_window_bm25_applied_count: {metrics['retrieval']['turn_window_bm25_applied_count']}",
        f"- turn_window_bm25_applied_rate: {metrics['retrieval']['turn_window_bm25_applied_rate']}",
        f"- avg_turn_window_hits: {metrics['retrieval']['avg_turn_window_hits']}",
        f"- avg_turn_window_source_hits: {metrics['retrieval']['avg_turn_window_source_hits']}",
        f"- selected_context_enabled: {metrics['retrieval']['selected_context_enabled']}",
        f"- selected_context_window_before: {metrics['retrieval']['selected_context_window_before']}",
        f"- selected_context_window_after: {metrics['retrieval']['selected_context_window_after']}",
        f"- selected_context_max_rows: {metrics['retrieval']['selected_context_max_rows']}",
        f"- selected_context_max_neighbor_chars: {metrics['retrieval']['selected_context_max_neighbor_chars']}",
        f"- selected_context_max_center_chars: {metrics['retrieval']['selected_context_max_center_chars']}",
        f"- selected_context_information_needs: {metrics['retrieval']['selected_context_information_needs']}",
        f"- selected_context_require_anaphora: {metrics['retrieval']['selected_context_require_anaphora']}",
        f"- selected_context_min_context_budget_headroom_chars: {metrics['retrieval']['selected_context_min_context_budget_headroom_chars']}",
        f"- selected_context_applied_count: {metrics['retrieval']['selected_context_applied_count']}",
        f"- selected_context_applied_rate: {metrics['retrieval']['selected_context_applied_rate']}",
        f"- selected_context_budget_gate_applied_count: {metrics['retrieval']['selected_context_budget_gate_applied_count']}",
        f"- selected_context_budget_gate_blocked_count: {metrics['retrieval']['selected_context_budget_gate_blocked_count']}",
        f"- avg_selected_context_budget_gate_headroom_chars: {metrics['retrieval']['avg_selected_context_budget_gate_headroom_chars']}",
        f"- avg_selected_context_materialized_rows: {metrics['retrieval']['avg_selected_context_materialized_rows']}",
        f"- avg_selected_context_skipped_long_center_rows: {metrics['retrieval']['avg_selected_context_skipped_long_center_rows']}",
        f"- rerank_enabled: {metrics['retrieval']['rerank_enabled']}",
        f"- rerank_model: {metrics['retrieval']['rerank_model']}",
        f"- rerank_pool_k: {metrics['retrieval']['rerank_pool_k']}",
        f"- rerank_document_text_mode: {metrics['retrieval']['rerank_document_text_mode']}",
        f"- rerank_document_neighbor_window: {metrics['retrieval']['rerank_document_neighbor_window']}",
        f"- rerank_document_max_memory_records: {metrics['retrieval']['rerank_document_max_memory_records']}",
        f"- rerank_anchor_keep: {metrics['retrieval']['rerank_anchor_keep']}",
        f"- rerank_anchor_after_top: {metrics['retrieval']['rerank_anchor_after_top']}",
        f"- rerank_applied_count: {metrics['retrieval']['rerank_applied_count']}",
        f"- rerank_applied_rate: {metrics['retrieval']['rerank_applied_rate']}",
        f"- avg_rerank_candidate_count: {metrics['retrieval']['avg_rerank_candidate_count']}",
        f"- avg_rerank_returned_count: {metrics['retrieval']['avg_rerank_returned_count']}",
        f"- avg_rerank_tokens_when_applied: {metrics['retrieval']['avg_rerank_tokens_when_applied']}",
        "- rerank_token_accounting: rerank model tokens are reported separately and are not included in build/query LLM token budgets.",
        f"- context_budget_enabled: {metrics['retrieval']['context_budget_enabled']}",
        f"- context_budget_max_chars: {metrics['retrieval']['context_budget_max_chars']}",
        f"- context_budget_min_hits: {metrics['retrieval']['context_budget_min_hits']}",
        f"- context_budget_protect_top_n: {metrics['retrieval']['context_budget_protect_top_n']}",
        f"- context_budget_max_hits: {metrics['retrieval']['context_budget_max_hits']}",
        f"- context_budget_information_needs: {metrics['retrieval']['context_budget_information_needs']}",
        f"- context_budget_applied_count: {metrics['retrieval']['context_budget_applied_count']}",
        f"- context_budget_applied_rate: {metrics['retrieval']['context_budget_applied_rate']}",
        f"- avg_context_budget_candidate_count: {metrics['retrieval']['avg_context_budget_candidate_count']}",
        f"- avg_context_budget_returned_count: {metrics['retrieval']['avg_context_budget_returned_count']}",
        f"- avg_context_budget_estimated_chars: {metrics['retrieval']['avg_context_budget_estimated_chars']}",
        f"- avg_context_budget_dropped_count: {metrics['retrieval']['avg_context_budget_dropped_count']}",
        f"- avg_embedding_tokens: {metrics['retrieval']['avg_embedding_tokens']}",
        f"- avg_context_chars: {metrics['retrieval']['avg_context_chars']}",
        f"- compiler_prompt_mode: {metrics['compiler']['prompt_mode']}",
        f"- compiler_memory_record_source: {metrics['compiler']['memory_record_source']}",
        f"- avg_compiled_memory_records: {metrics['compiler']['avg_compiled_memory_records']}",
        f"- answer_mode: {metrics['answer']['mode']}",
        f"- answer_model: {metrics['answer']['model']}",
        f"- answer_max_input_tokens: {metrics['answer']['max_input_tokens']}",
        f"- answer_max_output_tokens: {metrics['answer']['max_output_tokens']}",
        f"- answer_chat_template_kwargs: {metrics['answer']['chat_template_kwargs']}",
        f"- answer_output_format: {metrics['answer']['output_format']}",
        f"- answer_cache_enabled: {metrics['answer']['cache_enabled']}",
        f"- answer_cache_path: {metrics['answer']['cache_path']}",
        f"- answer_cache_namespace: {metrics['answer']['cache_namespace']}",
        f"- answer_cache_hits: {metrics['answer']['cache_hits']}",
        f"- answer_cache_misses: {metrics['answer']['cache_misses']}",
        f"- answer_cache_writes: {metrics['answer']['cache_writes']}",
        f"- answer_finalizer_enabled: {metrics['answer']['finalizer_enabled']}",
        f"- answer_finalizer_mode: {metrics['answer']['finalizer_mode']}",
        f"- answer_finalizer_enable_count_correction: {metrics['answer']['finalizer_enable_count_correction']}",
        f"- answer_finalizer_enable_evidence_report_count_correction: {metrics['answer']['finalizer_enable_evidence_report_count_correction']}",
        f"- answer_finalizer_enable_money_sum_correction: {metrics['answer']['finalizer_enable_money_sum_correction']}",
        f"- answer_finalizer_enable_duration_rounding_correction: {metrics['answer']['finalizer_enable_duration_rounding_correction']}",
        f"- answer_finalizer_enable_missing_detail: {metrics['answer']['finalizer_enable_missing_detail']}",
        f"- answer_finalizer_enable_relative_time_calculation: {metrics['answer']['finalizer_enable_relative_time_calculation']}",
        f"- answer_finalizer_applied_count: {metrics['answer']['finalizer_applied_count']}",
        f"- answer_finalizer_applied_rate: {metrics['answer']['finalizer_applied_rate']}",
        f"- answer_repair_enabled: {metrics['answer']['repair_enabled']}",
        f"- answer_repair_mode: {metrics['answer']['repair_mode']}",
        f"- answer_repair_model: {metrics['answer']['repair_model']}",
        f"- answer_repair_max_input_tokens: {metrics['answer']['repair_max_input_tokens']}",
        f"- answer_repair_max_output_tokens: {metrics['answer']['repair_max_output_tokens']}",
        f"- answer_repair_chat_template_kwargs: {metrics['answer']['repair_chat_template_kwargs']}",
        f"- answer_repair_output_format: {metrics['answer']['repair_output_format']}",
        f"- answer_repair_information_needs: {metrics['answer']['repair_information_needs']}",
        f"- answer_repair_enable_uncertain_trigger: {metrics['answer']['repair_enable_uncertain_trigger']}",
        f"- answer_repair_enable_short_list_trigger: {metrics['answer']['repair_enable_short_list_trigger']}",
        f"- answer_repair_enable_temporal_conflict_trigger: {metrics['answer']['repair_enable_temporal_conflict_trigger']}",
        f"- answer_repair_enable_profile_preference_trigger: {metrics['answer'].get('repair_enable_profile_preference_trigger', False)}",
        f"- answer_repair_enable_modal_abstention_trigger: {metrics['answer'].get('repair_enable_modal_abstention_trigger', False)}",
        f"- answer_repair_max_context_chars: {metrics['answer']['repair_max_context_chars']}",
        f"- answer_repair_max_row_text_chars: {metrics['answer']['repair_max_row_text_chars']}",
        f"- answer_repair_cache_enabled: {metrics['answer']['repair_cache_enabled']}",
        f"- answer_repair_cache_path: {metrics['answer']['repair_cache_path']}",
        f"- answer_repair_cache_namespace: {metrics['answer']['repair_cache_namespace']}",
        f"- answer_repair_cache_hits: {metrics['answer']['repair_cache_hits']}",
        f"- answer_repair_cache_misses: {metrics['answer']['repair_cache_misses']}",
        f"- answer_repair_cache_writes: {metrics['answer']['repair_cache_writes']}",
        f"- answer_repair_triggered_count: {metrics['answer']['repair_triggered_count']}",
        f"- answer_repair_triggered_rate: {metrics['answer']['repair_triggered_rate']}",
        f"- answer_repair_applied_count: {metrics['answer']['repair_applied_count']}",
        f"- answer_repair_applied_rate: {metrics['answer']['repair_applied_rate']}",
        f"- answer_repair_total_query_tokens: {metrics['answer']['repair_total_query_tokens']}",
        f"- answer_repair_avg_query_tokens_when_triggered: {metrics['answer']['repair_avg_query_tokens_when_triggered']}",
        f"- answer_style: {metrics['compiler']['answer_style']}",
        f"- evidence_order: {metrics['compiler']['evidence_order']}",
        f"- memory_order: {metrics['compiler']['memory_order']}",
        f"- memory_layout: {metrics['compiler']['memory_layout']}",
        f"- row_text_mode: {metrics['compiler']['row_text_mode']}",
        f"- max_row_text_chars: {metrics['compiler']['max_row_text_chars']}",
        f"- evidence_row_labels: {metrics['compiler']['evidence_row_labels']}",
        f"- final_answer_checklist: {metrics['compiler']['final_answer_checklist']}",
        f"- max_memory_records: {metrics['compiler']['max_memory_records']}",
        f"- route_guidance: {metrics['compiler']['route_guidance']}",
        f"- temporal_grounding: {metrics['compiler']['temporal_grounding']}",
        f"- temporal_hints: {metrics['compiler']['temporal_hints']}",
        f"- temporal_workpad: {metrics['compiler']['temporal_workpad']}",
        f"- temporal_text_normalization: {metrics['compiler']['temporal_text_normalization']}",
        f"- temporal_event_contract: {metrics['compiler']['temporal_event_contract']}",
        f"- temporal_workpad_scope: {metrics['compiler']['temporal_workpad_scope']}",
        f"- temporal_workpad_max_rows: {metrics['compiler']['temporal_workpad_max_rows']}",
        f"- temporal_workpad_max_pairs: {metrics['compiler']['temporal_workpad_max_pairs']}",
        f"- operation_workpad_question_gate: {metrics['compiler']['operation_workpad_question_gate']}",
        f"- personalized_advice_contract: {metrics['compiler']['personalized_advice_contract']}",
        f"- personalized_advice_contract_applied: {metrics['compiler']['personalized_advice_contract_applied']}",
        f"- context_pressure_enabled: {metrics['compiler']['context_pressure_enabled']}",
        f"- context_pressure_max_headroom_chars: {metrics['compiler']['context_pressure_max_headroom_chars']}",
        f"- context_pressure_overrides: {metrics['compiler']['context_pressure_overrides']}",
        f"- context_pressure_applied_count: {metrics['compiler']['context_pressure_applied_count']}",
        f"- context_pressure_applied_rate: {metrics['compiler']['context_pressure_applied_rate']}",
        f"- avg_context_pressure_headroom_chars: {metrics['compiler']['avg_context_pressure_headroom_chars']}",
        f"- structured_guide: {metrics['compiler']['structured_guide']}",
        f"- structured_guide_max_rows: {metrics['compiler']['structured_guide_max_rows']}",
        f"- structured_guide_include_rows: {metrics['compiler']['structured_guide_include_rows']}",
        f"- structured_guide_include_memory: {metrics['compiler']['structured_guide_include_memory']}",
        f"- structured_guide_disabled_signals: {metrics['compiler']['structured_guide_disabled_signals']}",
        f"- structured_answer_contract: {metrics['compiler']['structured_answer_contract']}",
        f"- structured_answer_contract_information_needs: {metrics['compiler']['structured_answer_contract_information_needs']}",
        f"- structured_answer_contract_max_items: {metrics['compiler']['structured_answer_contract_max_items']}",
        f"- evidence_report_contract: {metrics['compiler']['evidence_report_contract']}",
        f"- evidence_report_information_needs: {metrics['compiler']['evidence_report_information_needs']}",
        f"- evidence_report_max_items: {metrics['compiler']['evidence_report_max_items']}",
        f"- evidence_report_detail: {metrics['compiler']['evidence_report_detail']}",
        f"- aggregation_report_contract: {metrics['compiler']['aggregation_report_contract']}",
        f"- aggregation_report_information_needs: {metrics['compiler']['aggregation_report_information_needs']}",
        f"- candidate_guide: {metrics['compiler']['candidate_guide']}",
        f"- candidate_guide_information_needs: {metrics['compiler']['candidate_guide_information_needs']}",
        f"- candidate_guide_max_rows: {metrics['compiler']['candidate_guide_max_rows']}",
        f"- candidate_guide_snippet_chars: {metrics['compiler']['candidate_guide_snippet_chars']}",
        f"- update_conflict_guide: {metrics['compiler']['update_conflict_guide']}",
        f"- update_conflict_guide_information_needs: {metrics['compiler']['update_conflict_guide_information_needs']}",
        f"- update_conflict_guide_max_rows: {metrics['compiler']['update_conflict_guide_max_rows']}",
        f"- update_conflict_guide_snippet_chars: {metrics['compiler']['update_conflict_guide_snippet_chars']}",
        f"- update_conflict_guide_applied: {metrics['compiler']['update_conflict_guide_applied']}",
        f"- current_state_update_contract: {metrics['compiler']['current_state_update_contract']}",
        f"- dialogue_inference_contract: {metrics['compiler']['dialogue_inference_contract']}",
        f"- temporal_order_contract: {metrics['compiler']['temporal_order_contract']}",
        f"- source_anchor_keep: {metrics['compiler']['source_anchor_keep']}",
        f"- source_anchor_memory_rows: {metrics['compiler']['source_anchor_memory_rows']}",
        f"- source_anchor_per_session: {metrics['compiler']['source_anchor_per_session']}",
        f"- source_anchor_session_rows: {metrics['compiler']['source_anchor_session_rows']}",
        f"- route_overrides: {metrics['compiler']['route_overrides']}",
        f"- enable_broad_list_patterns: {metrics['route']['enable_broad_list_patterns']}",
        f"- enable_recommendation_profile_patterns: {metrics['route']['enable_recommendation_profile_patterns']}",
        f"- enable_advice_profile_patterns: {metrics['route'].get('enable_advice_profile_patterns', False)}",
        f"- temporal_priority_over_recent: {metrics['route']['temporal_priority_over_recent']}",
        "",
        "## Outputs",
        "",
        f"- predictions: {outputs['predictions']}",
        f"- traces: {outputs['traces']}",
        f"- metrics: {path.parent / 'metrics.json'}",
        f"- manifest: {path.parent / 'manifest.json'}",
        "",
        "## Clean Notes",
        "",
        "- No gold/reference/target answer, judge output, benchmark label, sample id, qid, or row index is passed into the prediction pipeline.",
        "- Build-stage typed memory is generated only from raw dialogue and visible metadata; it is recorded separately from offline labels and judge outputs.",
        "- Raw context remains available for fallback and diagnosis; build memory records keep source back-links when produced by the current builder.",
        "- Accuracy is intentionally not computed by the prediction runner; any gold or judge metrics must be produced offline after prediction.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_diagnosis(
    path: Path,
    manifest: dict[str, Any],
    metrics: dict[str, Any],
    config: dict[str, Any],
) -> None:
    lines = [
        f"# Diagnosis for {manifest['run_id']}",
        "",
        "## Summary",
        "",
        "The run validates pipeline shape, clean traceability, and answerer integration under the configured experiment kind.",
        "",
        "## Observations",
        "",
        f"- samples_processed: {metrics['n_samples']}",
        f"- avg_compiled_evidence_items: {metrics['retrieval']['avg_compiled_evidence_items']}",
        f"- avg_build_tokens: {metrics['token_cost']['avg_build_tokens']}",
        f"- avg_build_think_tokens: {metrics['token_cost']['avg_build_think_tokens']}",
        f"- avg_build_total_tokens: {metrics['token_cost']['avg_build_total_tokens']}",
        "- build_token_accounting: logical cold-build visible LLM tokens; cached build chunks count from stored usage, while cache hits only avoid repeated local API calls.",
        f"- avg_build_memory_records: {metrics['build_memory']['avg_records']}",
        f"- avg_active_build_memory_records: {metrics['build_memory']['avg_active_records']}",
        f"- build_memory_temporal_fields: {metrics['build_memory']['temporal_fields']}",
        f"- build_memory_prompt_profile: {metrics['build_memory']['prompt_profile']}",
        f"- build_memory_manage_facts: {metrics['build_memory']['manage_facts']}",
        f"- build_memory_overlap_turns: {metrics['build_memory']['overlap_turns']}",
        f"- build_memory_cache_hits: {metrics['build_memory']['cache_hits']}",
        f"- build_memory_cache_misses: {metrics['build_memory']['cache_misses']}",
        f"- build_memory_cache_writes: {metrics['build_memory']['cache_writes']}",
        f"- build_memory_source_alignment: {metrics['build_memory']['source_alignment']}",
        f"- build_memory_source_alignment_changed_records: {metrics['build_memory']['source_alignment_changed_records']}",
        f"- build_memory_source_alignment_added_sources: {metrics['build_memory']['source_alignment_added_sources']}",
        f"- avg_build_memory_source_alignment_changed_records: {metrics['build_memory']['avg_source_alignment_changed_records']}",
        f"- avg_build_memory_source_alignment_added_sources: {metrics['build_memory']['avg_source_alignment_added_sources']}",
        f"- avg_memory_hits: {metrics['retrieval']['avg_memory_hits']}",
        f"- avg_memory_source_hits: {metrics['retrieval']['avg_memory_source_hits']}",
        f"- build_memory_include_superseded: {metrics['retrieval']['build_memory_include_superseded']}",
        f"- build_memory_include_superseded_information_needs: {metrics['retrieval']['build_memory_include_superseded_information_needs']}",
        f"- avg_context_chars: {metrics['retrieval']['avg_context_chars']}",
        f"- avg_query_tokens: {metrics['token_cost']['avg_query_tokens']}",
        f"- avg_query_think_tokens: {metrics['token_cost']['avg_query_think_tokens']}",
        f"- avg_query_total_tokens: {metrics['token_cost']['avg_query_total_tokens']}",
        "- token_accounting_note: avg_build_tokens / avg_query_tokens exclude explicit reasoning tokens when the provider reports them; avg_*_total_tokens include visible plus think tokens.",
        f"- retrieval_route_overrides: {metrics['retrieval']['route_overrides']}",
        f"- avg_effective_top_k: {metrics['retrieval']['avg_effective_top_k']}",
        f"- avg_effective_dense_top_k: {metrics['retrieval']['avg_effective_dense_top_k']}",
        f"- avg_effective_dense_protect_top_n: {metrics['retrieval']['avg_effective_dense_protect_top_n']}",
        f"- dense_protect_top_n: {metrics['retrieval']['dense_protect_top_n']}",
        f"- turn_window_bm25_enabled: {metrics['retrieval']['turn_window_bm25_enabled']}",
        f"- turn_window_top_k: {metrics['retrieval']['turn_window_top_k']}",
        f"- turn_window_window_before: {metrics['retrieval']['turn_window_window_before']}",
        f"- turn_window_window_after: {metrics['retrieval']['turn_window_window_after']}",
        f"- turn_window_max_sources_per_window: {metrics['retrieval']['turn_window_max_sources_per_window']}",
        f"- turn_window_bm25_applied_count: {metrics['retrieval']['turn_window_bm25_applied_count']}",
        f"- turn_window_bm25_applied_rate: {metrics['retrieval']['turn_window_bm25_applied_rate']}",
        f"- avg_turn_window_hits: {metrics['retrieval']['avg_turn_window_hits']}",
        f"- avg_turn_window_source_hits: {metrics['retrieval']['avg_turn_window_source_hits']}",
        f"- selected_context_enabled: {metrics['retrieval']['selected_context_enabled']}",
        f"- selected_context_applied_count: {metrics['retrieval']['selected_context_applied_count']}",
        f"- selected_context_applied_rate: {metrics['retrieval']['selected_context_applied_rate']}",
        f"- selected_context_budget_gate_applied_count: {metrics['retrieval']['selected_context_budget_gate_applied_count']}",
        f"- selected_context_budget_gate_blocked_count: {metrics['retrieval']['selected_context_budget_gate_blocked_count']}",
        f"- avg_selected_context_budget_gate_headroom_chars: {metrics['retrieval']['avg_selected_context_budget_gate_headroom_chars']}",
        f"- avg_selected_context_materialized_rows: {metrics['retrieval']['avg_selected_context_materialized_rows']}",
        f"- avg_selected_context_skipped_long_center_rows: {metrics['retrieval']['avg_selected_context_skipped_long_center_rows']}",
        f"- rerank_enabled: {metrics['retrieval']['rerank_enabled']}",
        f"- rerank_model: {metrics['retrieval']['rerank_model']}",
        f"- rerank_pool_k: {metrics['retrieval']['rerank_pool_k']}",
        f"- rerank_document_text_mode: {metrics['retrieval']['rerank_document_text_mode']}",
        f"- rerank_document_neighbor_window: {metrics['retrieval']['rerank_document_neighbor_window']}",
        f"- rerank_document_max_memory_records: {metrics['retrieval']['rerank_document_max_memory_records']}",
        f"- rerank_anchor_keep: {metrics['retrieval']['rerank_anchor_keep']}",
        f"- rerank_anchor_after_top: {metrics['retrieval']['rerank_anchor_after_top']}",
        f"- rerank_applied_count: {metrics['retrieval']['rerank_applied_count']}",
        f"- rerank_applied_rate: {metrics['retrieval']['rerank_applied_rate']}",
        f"- avg_rerank_candidate_count: {metrics['retrieval']['avg_rerank_candidate_count']}",
        f"- avg_rerank_returned_count: {metrics['retrieval']['avg_rerank_returned_count']}",
        f"- avg_rerank_tokens_when_applied: {metrics['retrieval']['avg_rerank_tokens_when_applied']}",
        f"- context_budget_enabled: {metrics['retrieval']['context_budget_enabled']}",
        f"- context_budget_applied_count: {metrics['retrieval']['context_budget_applied_count']}",
        f"- context_budget_applied_rate: {metrics['retrieval']['context_budget_applied_rate']}",
        f"- avg_context_budget_candidate_count: {metrics['retrieval']['avg_context_budget_candidate_count']}",
        f"- avg_context_budget_returned_count: {metrics['retrieval']['avg_context_budget_returned_count']}",
        f"- avg_context_budget_estimated_chars: {metrics['retrieval']['avg_context_budget_estimated_chars']}",
        f"- avg_context_budget_dropped_count: {metrics['retrieval']['avg_context_budget_dropped_count']}",
        f"- embedding_cache_enabled: {metrics['retrieval']['embedding_cache_enabled']}",
        f"- embedding_cache_hits: {metrics['retrieval']['embedding_cache_hits']}",
        f"- embedding_cache_misses: {metrics['retrieval']['embedding_cache_misses']}",
        f"- evidence_order: {metrics['compiler']['evidence_order']}",
        f"- memory_record_source: {metrics['compiler']['memory_record_source']}",
        f"- avg_compiled_memory_records: {metrics['compiler']['avg_compiled_memory_records']}",
        f"- memory_order: {metrics['compiler']['memory_order']}",
        f"- memory_layout: {metrics['compiler']['memory_layout']}",
        f"- row_text_mode: {metrics['compiler']['row_text_mode']}",
        f"- max_row_text_chars: {metrics['compiler']['max_row_text_chars']}",
        f"- evidence_row_labels: {metrics['compiler']['evidence_row_labels']}",
        f"- final_answer_checklist: {metrics['compiler']['final_answer_checklist']}",
        f"- max_memory_records: {metrics['compiler']['max_memory_records']}",
        f"- route_guidance: {metrics['compiler']['route_guidance']}",
        f"- temporal_workpad: {metrics['compiler']['temporal_workpad']}",
        f"- temporal_text_normalization: {metrics['compiler']['temporal_text_normalization']}",
        f"- temporal_event_contract: {metrics['compiler']['temporal_event_contract']}",
        f"- temporal_workpad_scope: {metrics['compiler']['temporal_workpad_scope']}",
        f"- temporal_workpad_max_rows: {metrics['compiler']['temporal_workpad_max_rows']}",
        f"- temporal_workpad_max_pairs: {metrics['compiler']['temporal_workpad_max_pairs']}",
        f"- operation_workpad_question_gate: {metrics['compiler']['operation_workpad_question_gate']}",
        f"- personalized_advice_contract: {metrics['compiler']['personalized_advice_contract']}",
        f"- personalized_advice_contract_applied: {metrics['compiler']['personalized_advice_contract_applied']}",
        f"- context_pressure_enabled: {metrics['compiler']['context_pressure_enabled']}",
        f"- context_pressure_applied_count: {metrics['compiler']['context_pressure_applied_count']}",
        f"- context_pressure_applied_rate: {metrics['compiler']['context_pressure_applied_rate']}",
        f"- avg_context_pressure_headroom_chars: {metrics['compiler']['avg_context_pressure_headroom_chars']}",
        f"- structured_guide: {metrics['compiler']['structured_guide']}",
        f"- structured_guide_max_rows: {metrics['compiler']['structured_guide_max_rows']}",
        f"- structured_guide_include_rows: {metrics['compiler']['structured_guide_include_rows']}",
        f"- structured_guide_include_memory: {metrics['compiler']['structured_guide_include_memory']}",
        f"- structured_guide_disabled_signals: {metrics['compiler']['structured_guide_disabled_signals']}",
        f"- structured_answer_contract: {metrics['compiler']['structured_answer_contract']}",
        f"- structured_answer_contract_information_needs: {metrics['compiler']['structured_answer_contract_information_needs']}",
        f"- structured_answer_contract_max_items: {metrics['compiler']['structured_answer_contract_max_items']}",
        f"- evidence_report_contract: {metrics['compiler']['evidence_report_contract']}",
        f"- evidence_report_information_needs: {metrics['compiler']['evidence_report_information_needs']}",
        f"- evidence_report_max_items: {metrics['compiler']['evidence_report_max_items']}",
        f"- evidence_report_detail: {metrics['compiler']['evidence_report_detail']}",
        f"- aggregation_report_contract: {metrics['compiler']['aggregation_report_contract']}",
        f"- aggregation_report_information_needs: {metrics['compiler']['aggregation_report_information_needs']}",
        f"- candidate_guide: {metrics['compiler']['candidate_guide']}",
        f"- candidate_guide_information_needs: {metrics['compiler']['candidate_guide_information_needs']}",
        f"- candidate_guide_max_rows: {metrics['compiler']['candidate_guide_max_rows']}",
        f"- candidate_guide_snippet_chars: {metrics['compiler']['candidate_guide_snippet_chars']}",
        f"- update_conflict_guide: {metrics['compiler']['update_conflict_guide']}",
        f"- update_conflict_guide_information_needs: {metrics['compiler']['update_conflict_guide_information_needs']}",
        f"- update_conflict_guide_max_rows: {metrics['compiler']['update_conflict_guide_max_rows']}",
        f"- update_conflict_guide_snippet_chars: {metrics['compiler']['update_conflict_guide_snippet_chars']}",
        f"- update_conflict_guide_applied: {metrics['compiler']['update_conflict_guide_applied']}",
        f"- current_state_update_contract: {metrics['compiler']['current_state_update_contract']}",
        f"- dialogue_inference_contract: {metrics['compiler']['dialogue_inference_contract']}",
        f"- temporal_order_contract: {metrics['compiler']['temporal_order_contract']}",
        f"- source_anchor_keep: {metrics['compiler']['source_anchor_keep']}",
        f"- source_anchor_memory_rows: {metrics['compiler']['source_anchor_memory_rows']}",
        f"- source_anchor_per_session: {metrics['compiler']['source_anchor_per_session']}",
        f"- source_anchor_session_rows: {metrics['compiler']['source_anchor_session_rows']}",
        f"- route_overrides: {metrics['compiler']['route_overrides']}",
        f"- enable_recommendation_profile_patterns: {metrics['route']['enable_recommendation_profile_patterns']}",
        f"- enable_advice_profile_patterns: {metrics['route'].get('enable_advice_profile_patterns', False)}",
        f"- temporal_priority_over_recent: {metrics['route']['temporal_priority_over_recent']}",
        f"- answer_max_input_tokens: {metrics['answer']['max_input_tokens']}",
        f"- answer_max_output_tokens: {metrics['answer']['max_output_tokens']}",
        f"- answer_chat_template_kwargs: {metrics['answer']['chat_template_kwargs']}",
        f"- answer_cache_enabled: {metrics['answer']['cache_enabled']}",
        f"- answer_cache_path: {metrics['answer']['cache_path']}",
        f"- answer_cache_namespace: {metrics['answer']['cache_namespace']}",
        f"- answer_cache_hits: {metrics['answer']['cache_hits']}",
        f"- answer_cache_misses: {metrics['answer']['cache_misses']}",
        f"- answer_cache_writes: {metrics['answer']['cache_writes']}",
        f"- answer_finalizer_enabled: {metrics['answer']['finalizer_enabled']}",
        f"- answer_finalizer_mode: {metrics['answer']['finalizer_mode']}",
        f"- answer_finalizer_enable_count_correction: {metrics['answer']['finalizer_enable_count_correction']}",
        f"- answer_finalizer_enable_evidence_report_count_correction: {metrics['answer']['finalizer_enable_evidence_report_count_correction']}",
        f"- answer_finalizer_enable_money_sum_correction: {metrics['answer']['finalizer_enable_money_sum_correction']}",
        f"- answer_finalizer_enable_duration_rounding_correction: {metrics['answer']['finalizer_enable_duration_rounding_correction']}",
        f"- answer_finalizer_enable_missing_detail: {metrics['answer']['finalizer_enable_missing_detail']}",
        f"- answer_finalizer_enable_relative_time_calculation: {metrics['answer']['finalizer_enable_relative_time_calculation']}",
        f"- answer_finalizer_applied_count: {metrics['answer']['finalizer_applied_count']}",
        f"- answer_finalizer_applied_rate: {metrics['answer']['finalizer_applied_rate']}",
        f"- answer_repair_enabled: {metrics['answer']['repair_enabled']}",
        f"- answer_repair_mode: {metrics['answer']['repair_mode']}",
        f"- answer_repair_model: {metrics['answer']['repair_model']}",
        f"- answer_repair_max_input_tokens: {metrics['answer']['repair_max_input_tokens']}",
        f"- answer_repair_max_output_tokens: {metrics['answer']['repair_max_output_tokens']}",
        f"- answer_repair_information_needs: {metrics['answer']['repair_information_needs']}",
        f"- answer_repair_enable_profile_preference_trigger: {metrics['answer'].get('repair_enable_profile_preference_trigger', False)}",
        f"- answer_repair_enable_modal_abstention_trigger: {metrics['answer'].get('repair_enable_modal_abstention_trigger', False)}",
        f"- answer_repair_triggered_count: {metrics['answer']['repair_triggered_count']}",
        f"- answer_repair_triggered_rate: {metrics['answer']['repair_triggered_rate']}",
        f"- answer_repair_applied_count: {metrics['answer']['repair_applied_count']}",
        f"- answer_repair_applied_rate: {metrics['answer']['repair_applied_rate']}",
        f"- answer_repair_total_query_tokens: {metrics['answer']['repair_total_query_tokens']}",
        f"- answer_repair_avg_query_tokens_when_triggered: {metrics['answer']['repair_avg_query_tokens_when_triggered']}",
        f"- answer_repair_cache_hits: {metrics['answer']['repair_cache_hits']}",
        f"- answer_repair_cache_misses: {metrics['answer']['repair_cache_misses']}",
        f"- answer_repair_cache_writes: {metrics['answer']['repair_cache_writes']}",
        f"- answer: {_answer_note(config)}",
        "",
        "## Next Steps",
        "",
        "- Use offline lexical, judge, and evidence-recall scripts to diagnose quality after prediction is complete.",
        "- Compare typed build memory on/off before adding more expensive answer-time reasoning.",
        "- Keep each new method behind explicit config toggles for ablation.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _answer_max_output_tokens(answer_config: dict[str, Any]) -> int | None:
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
    return None


def _answer_cache_namespace(answer_config: dict[str, Any]) -> str | None:
    cache_config = answer_config.get("cache", {})
    namespace = cache_config.get("namespace")
    if namespace:
        return str(namespace)
    if not bool(cache_config.get("enabled", False)):
        return None
    max_output_tokens = _answer_max_output_tokens(answer_config)
    if max_output_tokens is None:
        max_output_tokens = 256
    answer_mode = str(answer_config.get("mode", "null_answerer"))
    fields = {
        "mode": answer_mode,
        "base_url": answer_config.get("base_url", "http://127.0.0.1:8000/v1"),
        "model": answer_config.get("model", answer_mode),
        "temperature": answer_config.get("temperature", 0.0),
        "max_input_tokens": answer_config.get("max_input_tokens"),
        "max_output_tokens": max_output_tokens,
        "output_format": answer_config.get("output_format", "text"),
        "chat_template_kwargs": json.dumps(
            answer_config.get("chat_template_kwargs") or {},
            ensure_ascii=False,
            sort_keys=True,
        ),
    }
    return "answer:" + "|".join(f"{key}={fields[key]}" for key in sorted(fields))


if __name__ == "__main__":
    raise SystemExit(main())
