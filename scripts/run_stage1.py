#!/usr/bin/env python3
"""Run the stage-1 clean skeleton on prediction JSONL."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from agent_memory.experiment import (  # noqa: E402
    append_jsonl,
    collect_git_state,
    utc_now_iso,
    write_json,
)
from agent_memory.io import load_prediction_jsonl  # noqa: E402
from agent_memory.pipeline import Stage1Pipeline  # noqa: E402


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

    pipeline = Stage1Pipeline(config)
    records = []
    total_query_tokens = 0
    total_build_tokens = 0
    total_evidence_items = 0
    total_context_chars = 0

    for envelope in load_prediction_jsonl(args.input):
        result = pipeline.predict(envelope.request)
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
            "avg_compiled_evidence_items": _safe_average(
                total_evidence_items, sample_count
            ),
            "avg_context_chars": _safe_average(total_context_chars, sample_count),
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
        ],
    }

    experiment_dir.mkdir(parents=True, exist_ok=True)
    write_json(experiment_dir / "metrics.json", metrics)
    write_json(experiment_dir / "manifest.json", manifest)
    write_json(experiment_dir / "config_snapshot.json", config)
    _write_summary(experiment_dir / "summary.md", manifest, metrics, args)
    _write_diagnosis(experiment_dir / "diagnosis.md", manifest, metrics)
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
    return parser.parse_args()


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


def _write_summary(
    path: Path,
    manifest: dict[str, Any],
    metrics: dict[str, Any],
    args: argparse.Namespace,
) -> None:
    git_state = manifest["git"]
    outputs = manifest["outputs"]
    lines = [
        f"# {manifest['run_id']}",
        "",
        "## Purpose",
        "",
        "Stage-1 clean skeleton smoke run: validate raw evidence storage, lexical retrieval, neighbor expansion, evidence compilation, trace output, and experiment bookkeeping.",
        "",
        "## Scope",
        "",
        f"- benchmark: {args.benchmark}",
        f"- subset: {args.subset}",
        f"- experiment_kind: {args.experiment_kind}",
        f"- input_path: {manifest['input_path']}",
        f"- config_path: {manifest['config_path']}",
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
        f"- avg_context_chars: {metrics['retrieval']['avg_context_chars']}",
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
        "- Raw evidence remains the only factual source; compiled evidence rows keep source_id links.",
        "- This runner uses a null answerer, so accuracy is intentionally not reported.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_diagnosis(
    path: Path, manifest: dict[str, Any], metrics: dict[str, Any]
) -> None:
    lines = [
        f"# Diagnosis for {manifest['run_id']}",
        "",
        "## Summary",
        "",
        "The run validates pipeline shape and traceability, not benchmark quality. The null answerer makes zero LLM calls, so token cost is zero and answer accuracy is not meaningful.",
        "",
        "## Observations",
        "",
        f"- samples_processed: {metrics['n_samples']}",
        f"- avg_compiled_evidence_items: {metrics['retrieval']['avg_compiled_evidence_items']}",
        f"- avg_context_chars: {metrics['retrieval']['avg_context_chars']}",
        "",
        "## Next Steps",
        "",
        "- Add dataset adapters that strip gold/judge/type/id fields before prediction.",
        "- Add local answer-model client behind the existing answerer interface.",
        "- Add offline evaluation scripts that consume predictions and gold after prediction is complete.",
        "- Add dense/BM25 hybrid retrieval and source-grounded compiler ablations.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
