#!/usr/bin/env python3
"""Offline DeepSeek judge for completed predictions."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from common.experiment import collect_git_state, utc_now_iso, write_json  # noqa: E402
from evaluation.judge import (  # noqa: E402
    JudgeExample,
    accuracy_from_judgments,
    build_judge_prompt,
    parse_judge_label,
)


def main() -> int:
    args = _parse_args()
    predictions = {str(item.get("record_key")): item for item in _read_jsonl(args.predictions)}
    labels = {str(item.get("record_key")): item for item in _read_jsonl(args.labels)}
    shared_keys = [key for key in labels if key in predictions]
    judgments = []

    api_key = os.environ.get(args.api_key_env)
    if not args.dry_run and not api_key:
        raise SystemExit(f"Missing API key environment variable: {args.api_key_env}")

    for key in shared_keys:
        label = labels[key]
        gold_answer = label.get("gold_answer")
        if gold_answer is None:
            judgments.append(
                {
                    "record_key": key,
                    "label": "INVALID",
                    "error": "missing_gold_answer",
                }
            )
            continue

        example = JudgeExample(
            record_key=key,
            question=str(label.get("question") or predictions[key].get("question") or ""),
            gold_answer=_stringify_gold(gold_answer),
            generated_answer=str(predictions[key].get("answer", "")),
            benchmark=args.benchmark,
            question_type=_optional_text(label.get("question_type")),
        )
        prompt = build_judge_prompt(example)
        prompt_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:16]
        if args.dry_run:
            judgments.append(
                {
                    "record_key": key,
                    "label": "PENDING",
                    "prompt_hash": prompt_hash,
                    "question_type": example.question_type,
                }
            )
            continue

        response = _call_deepseek(
            base_url=args.base_url,
            api_key=api_key or "",
            model=args.model,
            prompt=prompt,
            timeout=args.timeout,
        )
        response_text = response["choices"][0]["message"]["content"]
        judgments.append(
            {
                "record_key": key,
                "label": parse_judge_label(args.benchmark, response_text),
                "raw_response": response_text,
                "prompt_hash": prompt_hash,
                "question_type": example.question_type,
                "usage": response.get("usage", {}),
            }
        )

    payload = {
        "created_at_utc": utc_now_iso(),
        "benchmark": args.benchmark,
        "model": args.model,
        "base_url": args.base_url,
        "api_key_env": args.api_key_env,
        "dry_run": args.dry_run,
        "predictions": str(Path(args.predictions).resolve()),
        "labels": str(Path(args.labels).resolve()),
        "metrics": accuracy_from_judgments(judgments),
        "judgments": judgments,
        "clean_note": (
            "Offline judge reads gold labels only after prediction. This output must "
            "not be consumed by prediction, retrieval, compiler, answer, or verifier."
        ),
        "git": collect_git_state(REPO_ROOT),
    }
    write_json(args.output, payload)
    print(str(Path(args.output).resolve()))
    return 0


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--predictions", required=True)
    parser.add_argument("--labels", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--benchmark", required=True, choices=("longmemeval", "locomo"))
    parser.add_argument("--model", default="deepseek-v4-flash")
    parser.add_argument("--base-url", default="https://api.deepseek.com")
    parser.add_argument("--api-key-env", default="DEEPSEEK_API_KEY")
    parser.add_argument("--timeout", type=float, default=60.0)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def _call_deepseek(
    base_url: str, api_key: str, model: str, prompt: str, timeout: float
) -> dict[str, Any]:
    endpoint = base_url.rstrip("/") + "/chat/completions"
    request_body = json.dumps(
        {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.0,
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        endpoint,
        data=request_body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"DeepSeek judge request failed: {error.code} {body}") from error


def _read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    rows = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def _stringify_gold(gold: Any) -> str:
    if isinstance(gold, list):
        return " / ".join(str(item) for item in gold)
    return str(gold)


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text if text else None


if __name__ == "__main__":
    raise SystemExit(main())
