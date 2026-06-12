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
    total_embedding_tokens = 0

    for index, envelope in enumerate(load_prediction_jsonl(args.input), start=1):
        if args.limit is not None and index > args.limit:
            break
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
        total_embedding_tokens += int(result["trace"]["retrieval"].get("embedding_tokens") or 0)

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
            "dense_enabled": config.get("retrieval", {})
            .get("dense", {})
            .get("enabled", False),
            "lexical_protect_top_n": config.get("retrieval", {})
            .get("dense", {})
            .get("lexical_protect_top_n"),
            "total_embedding_tokens": total_embedding_tokens,
            "avg_embedding_tokens": _safe_average(total_embedding_tokens, sample_count),
            "avg_compiled_evidence_items": _safe_average(
                total_evidence_items, sample_count
            ),
            "avg_context_chars": _safe_average(total_context_chars, sample_count),
        },
        "answer": _answer_metrics(config),
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
        f"- neighbor_order: {metrics['retrieval']['neighbor_order']}",
        f"- drop_query_stopwords: {metrics['retrieval']['drop_query_stopwords']}",
        f"- dense_enabled: {metrics['retrieval']['dense_enabled']}",
        f"- lexical_protect_top_n: {metrics['retrieval']['lexical_protect_top_n']}",
        f"- avg_embedding_tokens: {metrics['retrieval']['avg_embedding_tokens']}",
        f"- avg_context_chars: {metrics['retrieval']['avg_context_chars']}",
        f"- answer_mode: {metrics['answer']['mode']}",
        f"- answer_model: {metrics['answer']['model']}",
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
        f"- avg_context_chars: {metrics['retrieval']['avg_context_chars']}",
        f"- avg_query_tokens: {metrics['token_cost']['avg_query_tokens']}",
        f"- answer: {_answer_note(config)}",
        "",
        "## Next Steps",
        "",
        "- Use offline lexical, judge, and evidence-recall scripts to diagnose quality after prediction is complete.",
        "- Improve retrieval and compiler recall before adding more expensive answer-time reasoning.",
        "- Keep each new method behind explicit config toggles for ablation.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
