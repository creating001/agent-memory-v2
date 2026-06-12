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
    output_dir = REPO_ROOT / "outputs" / run_id
    experiment_dir = REPO_ROOT / "experiments" / run_id
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
    total_evidence_items = 0
    total_context_chars = 0
    total_embedding_tokens = 0
    total_session_bm25_applied = 0
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
    total_memory_hits = 0
    total_memory_source_hits = 0

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
        total_evidence_items += len(compiled["evidence_rows"])
        total_context_chars += int(compiled["context_chars"])
        total_embedding_tokens += int(result["trace"]["retrieval"].get("embedding_tokens") or 0)
        if result["trace"]["retrieval"].get("session_bm25_applied"):
            total_session_bm25_applied += 1
        embedding_cache = result["trace"]["retrieval"].get("embedding_cache") or {}
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
        total_memory_hits += len(result["trace"]["retrieval"].get("memory_hits") or [])
        total_memory_source_hits += len(
            result["trace"]["retrieval"].get("memory_source_hits") or []
        )

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
            "avg_build_tokens": _safe_average(total_build_tokens, sample_count),
            "avg_query_tokens": _safe_average(total_query_tokens, sample_count),
        },
        "retrieval": {
            "top_k": config.get("retrieval", {}).get("top_k"),
            "max_top_k": config.get("retrieval", {}).get("max_top_k"),
            "neighbor_window": config.get("retrieval", {}).get("neighbor_window"),
            "neighbor_order": config.get("retrieval", {}).get(
                "neighbor_order", "hit_priority"
            ),
            "drop_query_stopwords": config.get("retrieval", {}).get(
                "drop_query_stopwords", False
            ),
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
            "session_bm25_enabled": config.get("retrieval", {})
            .get("session_bm25", {})
            .get("enabled", False),
            "session_bm25_top_k": config.get("retrieval", {})
            .get("session_bm25", {})
            .get("top_k"),
            "session_anchor_top_k": config.get("retrieval", {})
            .get("session_bm25", {})
            .get("anchor_top_k"),
            "session_max_anchor_hits": config.get("retrieval", {})
            .get("session_bm25", {})
            .get("max_anchor_hits"),
            "session_protect_turn_hits": config.get("retrieval", {})
            .get("session_bm25", {})
            .get("protect_turn_hits"),
            "session_enabled_route_signals": config.get("retrieval", {})
            .get("session_bm25", {})
            .get("enabled_route_signals"),
            "session_enabled_information_needs": config.get("retrieval", {})
            .get("session_bm25", {})
            .get("enabled_information_needs"),
            "session_enabled_query_patterns": config.get("retrieval", {})
            .get("session_bm25", {})
            .get("enabled_query_patterns"),
            "session_bm25_applied_count": total_session_bm25_applied,
            "session_bm25_applied_rate": _safe_average(
                total_session_bm25_applied, sample_count
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
            "max_chars_per_turn": config.get("build_memory", {}).get(
                "max_chars_per_turn"
            ),
            "max_records_per_chunk": config.get("build_memory", {}).get(
                "max_records_per_chunk"
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
        "answer": _answer_metrics(config),
        "compiler": {
            "answer_style": config.get("compiler", {}).get("answer_style", "grounded"),
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
        },
        "route": {
            "enable_broad_list_patterns": config.get("route", {}).get(
                "enable_broad_list_patterns", False
            ),
            "enable_recommendation_profile_patterns": config.get("route", {}).get(
                "enable_recommendation_profile_patterns", False
            ),
        },
        "runner": {
            "workers": max(1, args.workers),
        },
    }
    manifest = {
        "run_id": run_id,
        "created_at_utc": utc_now_iso(),
        "config_path": str(Path(args.config).resolve()),
        "input_path": str(Path(args.input).resolve()),
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
    return {
        "mode": answer_config.get("mode", "null_answerer"),
        "model": answer_config.get("model"),
        "base_url": answer_config.get("base_url"),
        "temperature": answer_config.get("temperature"),
        "max_tokens": answer_config.get("max_tokens"),
        "timeout": answer_config.get("timeout"),
    }


def _answer_note(config: dict[str, Any]) -> str:
    answer = _answer_metrics(config)
    if answer["mode"] == "openai_compatible":
        return (
            "OpenAI-compatible answerer using "
            f"{answer['model']} at {answer['base_url']} with temperature "
            f"{answer['temperature']} and max_tokens {answer['max_tokens']}."
        )
    if answer["mode"] == "null_answerer":
        return "Null answerer; generated answers are placeholders and accuracy is not meaningful."
    return f"Answer mode: {answer['mode']}."


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
        f"- avg_query_tokens: {metrics['token_cost']['avg_query_tokens']}",
        f"- avg_compiled_evidence_items: {metrics['retrieval']['avg_compiled_evidence_items']}",
        f"- build_memory_enabled: {metrics['build_memory']['enabled']}",
        f"- build_memory_model: {metrics['build_memory']['model']}",
        f"- build_memory_cache_enabled: {metrics['build_memory']['cache_enabled']}",
        f"- build_memory_cache_path: {metrics['build_memory']['cache_path']}",
        f"- build_memory_cache_hits: {metrics['build_memory']['cache_hits']}",
        f"- build_memory_cache_misses: {metrics['build_memory']['cache_misses']}",
        f"- build_memory_cache_writes: {metrics['build_memory']['cache_writes']}",
        f"- avg_build_memory_records: {metrics['build_memory']['avg_records']}",
        f"- avg_active_build_memory_records: {metrics['build_memory']['avg_active_records']}",
        f"- avg_memory_hits: {metrics['retrieval']['avg_memory_hits']}",
        f"- avg_memory_source_hits: {metrics['retrieval']['avg_memory_source_hits']}",
        f"- neighbor_order: {metrics['retrieval']['neighbor_order']}",
        f"- drop_query_stopwords: {metrics['retrieval']['drop_query_stopwords']}",
        f"- dense_enabled: {metrics['retrieval']['dense_enabled']}",
        f"- lexical_protect_top_n: {metrics['retrieval']['lexical_protect_top_n']}",
        f"- embedding_cache_enabled: {metrics['retrieval']['embedding_cache_enabled']}",
        f"- embedding_cache_path: {metrics['retrieval']['embedding_cache_path']}",
        f"- embedding_cache_hits: {metrics['retrieval']['embedding_cache_hits']}",
        f"- embedding_cache_misses: {metrics['retrieval']['embedding_cache_misses']}",
        f"- embedding_cache_writes: {metrics['retrieval']['embedding_cache_writes']}",
        f"- session_bm25_enabled: {metrics['retrieval']['session_bm25_enabled']}",
        f"- session_bm25_top_k: {metrics['retrieval']['session_bm25_top_k']}",
        f"- session_anchor_top_k: {metrics['retrieval']['session_anchor_top_k']}",
        f"- session_max_anchor_hits: {metrics['retrieval']['session_max_anchor_hits']}",
        f"- session_protect_turn_hits: {metrics['retrieval']['session_protect_turn_hits']}",
        f"- session_enabled_route_signals: {metrics['retrieval']['session_enabled_route_signals']}",
        f"- session_enabled_information_needs: {metrics['retrieval']['session_enabled_information_needs']}",
        f"- session_enabled_query_patterns: {metrics['retrieval']['session_enabled_query_patterns']}",
        f"- session_bm25_applied_count: {metrics['retrieval']['session_bm25_applied_count']}",
        f"- session_bm25_applied_rate: {metrics['retrieval']['session_bm25_applied_rate']}",
        f"- avg_embedding_tokens: {metrics['retrieval']['avg_embedding_tokens']}",
        f"- avg_context_chars: {metrics['retrieval']['avg_context_chars']}",
        f"- answer_mode: {metrics['answer']['mode']}",
        f"- answer_model: {metrics['answer']['model']}",
        f"- answer_style: {metrics['compiler']['answer_style']}",
        f"- evidence_order: {metrics['compiler']['evidence_order']}",
        f"- memory_order: {metrics['compiler']['memory_order']}",
        f"- memory_layout: {metrics['compiler']['memory_layout']}",
        f"- row_text_mode: {metrics['compiler']['row_text_mode']}",
        f"- max_row_text_chars: {metrics['compiler']['max_row_text_chars']}",
        f"- max_memory_records: {metrics['compiler']['max_memory_records']}",
        f"- route_guidance: {metrics['compiler']['route_guidance']}",
        f"- temporal_grounding: {metrics['compiler']['temporal_grounding']}",
        f"- temporal_hints: {metrics['compiler']['temporal_hints']}",
        f"- temporal_workpad: {metrics['compiler']['temporal_workpad']}",
        f"- enable_broad_list_patterns: {metrics['route']['enable_broad_list_patterns']}",
        f"- enable_recommendation_profile_patterns: {metrics['route']['enable_recommendation_profile_patterns']}",
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
        f"- avg_build_memory_records: {metrics['build_memory']['avg_records']}",
        f"- avg_active_build_memory_records: {metrics['build_memory']['avg_active_records']}",
        f"- build_memory_cache_hits: {metrics['build_memory']['cache_hits']}",
        f"- build_memory_cache_misses: {metrics['build_memory']['cache_misses']}",
        f"- build_memory_cache_writes: {metrics['build_memory']['cache_writes']}",
        f"- avg_memory_hits: {metrics['retrieval']['avg_memory_hits']}",
        f"- avg_memory_source_hits: {metrics['retrieval']['avg_memory_source_hits']}",
        f"- avg_context_chars: {metrics['retrieval']['avg_context_chars']}",
        f"- avg_query_tokens: {metrics['token_cost']['avg_query_tokens']}",
        f"- session_bm25_enabled: {metrics['retrieval']['session_bm25_enabled']}",
        f"- session_bm25_top_k: {metrics['retrieval']['session_bm25_top_k']}",
        f"- session_anchor_top_k: {metrics['retrieval']['session_anchor_top_k']}",
        f"- session_enabled_route_signals: {metrics['retrieval']['session_enabled_route_signals']}",
        f"- session_bm25_applied_count: {metrics['retrieval']['session_bm25_applied_count']}",
        f"- session_bm25_applied_rate: {metrics['retrieval']['session_bm25_applied_rate']}",
        f"- embedding_cache_enabled: {metrics['retrieval']['embedding_cache_enabled']}",
        f"- embedding_cache_hits: {metrics['retrieval']['embedding_cache_hits']}",
        f"- embedding_cache_misses: {metrics['retrieval']['embedding_cache_misses']}",
        f"- evidence_order: {metrics['compiler']['evidence_order']}",
        f"- memory_order: {metrics['compiler']['memory_order']}",
        f"- memory_layout: {metrics['compiler']['memory_layout']}",
        f"- row_text_mode: {metrics['compiler']['row_text_mode']}",
        f"- max_row_text_chars: {metrics['compiler']['max_row_text_chars']}",
        f"- max_memory_records: {metrics['compiler']['max_memory_records']}",
        f"- route_guidance: {metrics['compiler']['route_guidance']}",
        f"- temporal_workpad: {metrics['compiler']['temporal_workpad']}",
        f"- enable_recommendation_profile_patterns: {metrics['route']['enable_recommendation_profile_patterns']}",
        f"- answer: {_answer_note(config)}",
        "",
        "## Next Steps",
        "",
        "- Use offline lexical, judge, and evidence-recall scripts to diagnose quality after prediction is complete.",
        "- Compare typed build memory on/off before adding more expensive answer-time reasoning.",
        "- Keep each new method behind explicit config toggles for ablation.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
