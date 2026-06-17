#!/usr/bin/env python3
"""Run and aggregate DeepSeek flash/pro offline judges for predictions."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from common.experiment import collect_git_state, utc_now_iso, write_json  # noqa: E402
from evaluation.judge import dual_accuracy_from_judgments  # noqa: E402


FLASH_MODEL = "deepseek-v4-flash"
PRO_MODEL = "deepseek-v4-pro"


def main() -> int:
    args = _parse_args()
    output = Path(args.output)
    flash_output = (
        Path(args.flash_output)
        if args.flash_output
        else output.with_name("deepseek_judge_v4_flash.json")
    )
    pro_output = (
        Path(args.pro_output)
        if args.pro_output
        else output.with_name("deepseek_judge_v4_pro.json")
    )

    if not args.aggregate_only:
        _ensure_judge_output(args, model=FLASH_MODEL, output=flash_output)
        _ensure_judge_output(args, model=PRO_MODEL, output=pro_output)

    flash_payload = _read_json(flash_output)
    pro_payload = _read_json(pro_output)
    labels_by_key = _labels_by_key(args.labels)
    group_field = args.group_field or (
        "category" if args.benchmark == "locomo" else "question_type"
    )
    dual_report = dual_accuracy_from_judgments(
        list(flash_payload.get("judgments", [])),
        list(pro_payload.get("judgments", [])),
        labels_by_key=labels_by_key,
        group_field=group_field,
    )

    payload = {
        "created_at_utc": utc_now_iso(),
        "benchmark": args.benchmark,
        "predictions": str(Path(args.predictions).resolve()),
        "labels": str(Path(args.labels).resolve()),
        "judge_outputs": {
            "flash": str(flash_output.resolve()),
            "pro": str(pro_output.resolve()),
        },
        "judge_models": {
            "flash": FLASH_MODEL,
            "pro": PRO_MODEL,
        },
        "temperature": args.temperature,
        "metrics": dual_report["metrics"],
        "by_group": dual_report["by_group"],
        "single_judge_metrics": {
            "flash": flash_payload.get("metrics", {}),
            "pro": pro_payload.get("metrics", {}),
        },
        "usage": {
            "flash": flash_payload.get("usage", {}),
            "pro": pro_payload.get("usage", {}),
            "total": _sum_usage(
                flash_payload.get("usage", {}), pro_payload.get("usage", {})
            ),
        },
        "records": dual_report["records"],
        "clean_note": (
            "Dual judge is an offline evaluation-only aggregation. It reads gold labels "
            "after prediction and must not feed prediction, retrieval, compiler, answer, "
            "verifier, or cache construction."
        ),
        "git": collect_git_state(REPO_ROOT),
    }
    write_json(output, payload)
    print(str(output.resolve()))
    return 0


def _ensure_judge_output(args: argparse.Namespace, *, model: str, output: Path) -> None:
    if output.exists() and not args.refresh:
        print(f"using existing {model} judge: {output}", flush=True)
        return
    command = [
        sys.executable,
        str(REPO_ROOT / "scripts" / "judge_predictions_deepseek.py"),
        "--predictions",
        args.predictions,
        "--labels",
        args.labels,
        "--output",
        str(output),
        "--benchmark",
        args.benchmark,
        "--model",
        model,
        "--base-url",
        args.base_url,
        "--api-key-env",
        args.api_key_env,
        "--temperature",
        str(args.temperature),
        "--timeout",
        str(args.timeout),
        "--max-retries",
        str(args.max_retries),
        "--retry-sleep",
        str(args.retry_sleep),
        "--workers",
        str(args.workers),
        "--progress-every",
        str(args.progress_every),
    ]
    if not args.resume:
        command.append("--no-resume")
    subprocess.run(command, cwd=REPO_ROOT, check=True)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--predictions", required=True)
    parser.add_argument("--labels", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--benchmark", required=True, choices=("longmemeval", "locomo"))
    parser.add_argument("--flash-output")
    parser.add_argument("--pro-output")
    parser.add_argument("--group-field")
    parser.add_argument("--base-url", default="https://api.deepseek.com")
    parser.add_argument("--api-key-env", default="DEEPSEEK_API_KEY")
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--timeout", type=float, default=60.0)
    parser.add_argument("--max-retries", type=int, default=6)
    parser.add_argument("--retry-sleep", type=float, default=2.0)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--progress-every", type=int, default=50)
    parser.add_argument("--aggregate-only", action="store_true")
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--no-resume", action="store_false", dest="resume")
    parser.set_defaults(resume=True)
    return parser.parse_args()


def _read_json(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _labels_by_key(path: str | Path) -> dict[str, dict[str, Any]]:
    labels: dict[str, dict[str, Any]] = {}
    with Path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            item = json.loads(line)
            labels[str(item.get("record_key"))] = item
    return labels


def _sum_usage(first: Any, second: Any) -> dict[str, int]:
    totals = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    for usage in (first, second):
        if not isinstance(usage, dict):
            continue
        for key in totals:
            value = usage.get(key)
            if isinstance(value, int):
                totals[key] += value
    return totals


if __name__ == "__main__":
    raise SystemExit(main())
