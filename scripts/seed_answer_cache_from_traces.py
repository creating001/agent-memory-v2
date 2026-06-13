#!/usr/bin/env python3
"""Seed an answer cache from prior prediction traces.

This is an operational helper for controlled query-side ablations. It reads only
prediction-time traces: compiled prompt, answer, raw response, and token usage.
It must not read labels, judge outputs, benchmark categories, sample ids, or
test feedback.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from memory.answer import _answer_cache_key  # noqa: E402


def main() -> int:
    args = _parse_args()
    cache_path = Path(args.cache_path)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(str(cache_path), timeout=30.0)
    connection.execute("PRAGMA busy_timeout = 30000")
    connection.execute("PRAGMA journal_mode = WAL")
    connection.execute(
        "CREATE TABLE IF NOT EXISTS answer_cache("
        "cache_key TEXT PRIMARY KEY, "
        "payload_json TEXT NOT NULL)"
    )

    rows = 0
    written = 0
    skipped = 0
    with Path(args.traces).open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            rows += 1
            record = json.loads(line)
            trace = record.get("trace") or {}
            compiled = trace.get("compiled_context") or {}
            answer = trace.get(args.answer_field) or {}
            prompt = compiled.get("prompt")
            if not isinstance(prompt, str) or not answer:
                skipped += 1
                continue
            payload = _cache_payload(answer)
            cache_key = _answer_cache_key(namespace=args.namespace, prompt=prompt)
            connection.execute(
                "INSERT OR REPLACE INTO answer_cache(cache_key, payload_json) "
                "VALUES(?, ?)",
                (cache_key, json.dumps(payload, ensure_ascii=False, sort_keys=True)),
            )
            written += 1
    connection.commit()
    connection.close()
    print(
        json.dumps(
            {
                "traces": str(Path(args.traces).resolve()),
                "cache_path": str(cache_path.resolve()),
                "namespace": args.namespace,
                "answer_field": args.answer_field,
                "rows": rows,
                "written": written,
                "skipped": skipped,
                "clean_note": (
                    "Seeded from prediction traces only; no labels, judge outputs, "
                    "benchmark categories, sample ids, or test feedback were read."
                ),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--traces", required=True)
    parser.add_argument("--cache-path", required=True)
    parser.add_argument("--namespace", required=True)
    parser.add_argument("--answer-field", default="answer")
    return parser.parse_args()


def _cache_payload(answer: dict[str, Any]) -> dict[str, Any]:
    token_usage = answer.get("token_usage") or {}
    return {
        "answer": str(answer.get("answer", "")),
        "model": str(answer.get("model", "cached_answerer")),
        "token_usage": {
            "build_tokens": int(token_usage.get("build_tokens") or 0),
            "query_tokens": int(token_usage.get("query_tokens") or 0),
        },
        "raw_response": answer.get("raw_response"),
    }


if __name__ == "__main__":
    raise SystemExit(main())
