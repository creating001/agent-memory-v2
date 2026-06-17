#!/usr/bin/env python3
"""Run and aggregate two DeepSeek flash offline judges for predictions."""

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


def main() -> int:
    args = _parse_args()
    output = Path(args.output)
    flash_1_output = (
        Path(args.flash_1_output)
        if args.flash_1_output
        else output.with_name("deepseek_judge_flash_1.json")
    )
    flash_2_output = (
        Path(args.flash_2_output)
        if args.flash_2_output
        else output.with_name("deepseek_judge_flash_2.json")
    )

    if not args.aggregate_only:
        _ensure_judge_output(
            args,
            run_name="flash_1",
            output=flash_1_output,
            thinking=args.flash_1_thinking,
        )
        _ensure_judge_output(
            args,
            run_name="flash_2",
            output=flash_2_output,
            thinking=args.flash_2_thinking,
        )

    flash_1_payload = _read_json(flash_1_output)
    flash_2_payload = _read_json(flash_2_output)
    labels_by_key = _labels_by_key(args.labels)
    group_field = args.group_field or (
        "category" if args.benchmark == "locomo" else "question_type"
    )
    dual_report = dual_accuracy_from_judgments(
        list(flash_1_payload.get("judgments", [])),
        list(flash_2_payload.get("judgments", [])),
        labels_by_key=labels_by_key,
        group_field=group_field,
        judge_names=("flash_1", "flash_2"),
    )

    payload = {
        "created_at_utc": utc_now_iso(),
        "benchmark": args.benchmark,
        "predictions": str(Path(args.predictions).resolve()),
        "labels": str(Path(args.labels).resolve()),
        "judge_outputs": {
            "flash_1": str(flash_1_output.resolve()),
            "flash_2": str(flash_2_output.resolve()),
        },
        "judge_models": {
            "flash_1": FLASH_MODEL,
            "flash_2": FLASH_MODEL,
        },
        "judge_thinking": {
            "flash_1": flash_1_payload.get("thinking"),
            "flash_2": flash_2_payload.get("thinking"),
        },
        "judge_request_body_options": {
            "flash_1": flash_1_payload.get("request_body_options", {}),
            "flash_2": flash_2_payload.get("request_body_options", {}),
        },
        "temperature": args.temperature,
        "metrics": dual_report["metrics"],
        "by_group": dual_report["by_group"],
        "single_judge_metrics": {
            "flash_1": flash_1_payload.get("metrics", {}),
            "flash_2": flash_2_payload.get("metrics", {}),
        },
        "usage": {
            "flash_1": flash_1_payload.get("usage", {}),
            "flash_2": flash_2_payload.get("usage", {}),
            "total": _sum_usage(
                flash_1_payload.get("usage", {}), flash_2_payload.get("usage", {})
            ),
        },
        "records": dual_report["records"],
        "clean_note": (
            "Dual flash judge is an offline evaluation-only aggregation. It reads gold "
            "labels after prediction and must not feed prediction, retrieval, compiler, "
            "answer, verifier, or cache construction."
        ),
        "git": collect_git_state(REPO_ROOT),
    }
    write_json(output, payload)
    print(str(output.resolve()))
    return 0


def _ensure_judge_output(
    args: argparse.Namespace,
    *,
    run_name: str,
    output: Path,
    thinking: str | None,
) -> None:
    if output.exists() and not args.refresh:
        print(f"using existing {run_name} judge: {output}", flush=True)
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
        FLASH_MODEL,
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
    if thinking:
        command.extend(["--thinking", thinking])
    if not args.resume:
        command.append("--no-resume")
    subprocess.run(command, cwd=REPO_ROOT, check=True)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--predictions", required=True)
    parser.add_argument("--labels", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--benchmark", required=True, choices=("longmemeval", "locomo"))
    parser.add_argument("--flash-1-output", "--flash-output", dest="flash_1_output")
    parser.add_argument("--flash-2-output", "--pro-output", dest="flash_2_output")
    parser.add_argument("--group-field")
    parser.add_argument("--base-url", default="https://api.deepseek.com")
    parser.add_argument("--api-key-env", default="DEEPSEEK_API_KEY")
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument(
        "--flash-1-thinking",
        "--flash-thinking",
        dest="flash_1_thinking",
        choices=("enabled", "disabled"),
    )
    parser.add_argument(
        "--flash-2-thinking",
        "--pro-thinking",
        dest="flash_2_thinking",
        choices=("enabled", "disabled"),
    )
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
