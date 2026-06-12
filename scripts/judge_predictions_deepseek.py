#!/usr/bin/env python3
"""Offline DeepSeek judge for completed predictions."""

from __future__ import annotations

import argparse
import http.client
import hashlib
import json
import os
import sys
import time
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
    partial_path = Path(args.partial_output) if args.partial_output else _default_partial_path(args.output)
    previous_judgments = _load_partial_judgments(partial_path) if args.resume else {}
    judgments_by_key: dict[str, dict[str, Any]] = dict(previous_judgments)

    api_key = os.environ.get(args.api_key_env)
    if not args.dry_run and not api_key:
        raise SystemExit(f"Missing API key environment variable: {args.api_key_env}")

    for index, key in enumerate(shared_keys, start=1):
        label = labels[key]
        gold_answer = label.get("gold_answer")
        if gold_answer is None:
            previous = judgments_by_key.get(key)
            if previous and previous.get("error") == "missing_gold_answer":
                continue
            judgment = {
                "record_key": key,
                "label": "INVALID",
                "error": "missing_gold_answer",
            }
            judgments_by_key[key] = judgment
            _append_partial_judgment(partial_path, judgment)
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
        previous = judgments_by_key.get(key)
        if previous and previous.get("prompt_hash") == prompt_hash:
            continue

        if args.dry_run:
            judgment = {
                "record_key": key,
                "label": "PENDING",
                "prompt_hash": prompt_hash,
                "question_type": example.question_type,
            }
            judgments_by_key[key] = judgment
            _append_partial_judgment(partial_path, judgment)
            if index % args.progress_every == 0 or index == len(shared_keys):
                print(f"judged {index}/{len(shared_keys)}", flush=True)
            continue

        response = _call_deepseek_with_retries(
            base_url=args.base_url,
            api_key=api_key or "",
            model=args.model,
            prompt=prompt,
            timeout=args.timeout,
            max_retries=args.max_retries,
            retry_sleep=args.retry_sleep,
        )
        response_text = response["choices"][0]["message"]["content"]
        judgment = {
            "record_key": key,
            "label": parse_judge_label(args.benchmark, response_text),
            "raw_response": response_text,
            "prompt_hash": prompt_hash,
            "question_type": example.question_type,
            "usage": response.get("usage", {}),
        }
        judgments_by_key[key] = judgment
        _append_partial_judgment(partial_path, judgment)
        if index % args.progress_every == 0 or index == len(shared_keys):
            print(f"judged {index}/{len(shared_keys)}", flush=True)

    judgments = [judgments_by_key[key] for key in shared_keys if key in judgments_by_key]
    payload = {
        "created_at_utc": utc_now_iso(),
        "benchmark": args.benchmark,
        "model": args.model,
        "base_url": args.base_url,
        "api_key_env": args.api_key_env,
        "dry_run": args.dry_run,
        "predictions": str(Path(args.predictions).resolve()),
        "labels": str(Path(args.labels).resolve()),
        "partial_output": str(partial_path.resolve()),
        "metrics": accuracy_from_judgments(judgments),
        "usage": _summarize_usage(judgments),
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
    parser.add_argument("--max-retries", type=int, default=6)
    parser.add_argument("--retry-sleep", type=float, default=2.0)
    parser.add_argument("--progress-every", type=int, default=25)
    parser.add_argument("--partial-output")
    parser.add_argument("--no-resume", action="store_false", dest="resume")
    parser.add_argument("--dry-run", action="store_true")
    parser.set_defaults(resume=True)
    return parser.parse_args()


def _call_deepseek_with_retries(
    base_url: str,
    api_key: str,
    model: str,
    prompt: str,
    timeout: float,
    max_retries: int,
    retry_sleep: float,
) -> dict[str, Any]:
    attempts = max(1, max_retries + 1)
    last_error: BaseException | None = None
    for attempt in range(1, attempts + 1):
        try:
            return _call_deepseek(
                base_url=base_url,
                api_key=api_key,
                model=model,
                prompt=prompt,
                timeout=timeout,
            )
        except _retryable_errors() as error:
            last_error = error
            if attempt == attempts:
                break
            sleep_seconds = retry_sleep * attempt
            print(
                f"DeepSeek judge request failed on attempt {attempt}/{attempts}: "
                f"{error}. Retrying in {sleep_seconds:.1f}s.",
                file=sys.stderr,
                flush=True,
            )
            time.sleep(sleep_seconds)
    raise RuntimeError(f"DeepSeek judge request failed after {attempts} attempts: {last_error}")


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
        if 400 <= error.code < 500 and error.code not in {408, 409, 425, 429}:
            raise RuntimeError(f"DeepSeek judge request failed: {error.code} {body}") from error
        raise urllib.error.URLError(f"{error.code} {body}") from error


def _retryable_errors() -> tuple[type[BaseException], ...]:
    return (
        TimeoutError,
        ConnectionError,
        http.client.RemoteDisconnected,
        urllib.error.URLError,
        OSError,
    )


def _read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    rows = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def _default_partial_path(output: str | Path) -> Path:
    output_path = Path(output)
    return output_path.with_suffix(output_path.suffix + ".partial.jsonl")


def _load_partial_judgments(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    judgments: dict[str, dict[str, Any]] = {}
    for item in _read_jsonl(path):
        key = str(item.get("record_key"))
        if key:
            judgments[key] = item
    return judgments


def _append_partial_judgment(path: Path, judgment: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(judgment, ensure_ascii=False, sort_keys=True))
        handle.write("\n")


def _summarize_usage(judgments: list[dict[str, Any]]) -> dict[str, int]:
    usage_fields = ("prompt_tokens", "completion_tokens", "total_tokens")
    totals = {field: 0 for field in usage_fields}
    for judgment in judgments:
        usage = judgment.get("usage")
        if not isinstance(usage, dict):
            continue
        for field in usage_fields:
            value = usage.get(field)
            if isinstance(value, int):
                totals[field] += value
    return totals


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
