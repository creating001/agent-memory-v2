#!/usr/bin/env python3
"""Run offline lexical metrics after predictions are complete."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from common.experiment import collect_git_state, utc_now_iso, write_json  # noqa: E402
from evaluation.metrics import evaluate_offline  # noqa: E402


def main() -> int:
    args = _parse_args()
    predictions = _read_jsonl(args.predictions)
    labels = _read_jsonl(args.labels)
    metrics = evaluate_offline(predictions, labels)
    payload = {
        "created_at_utc": utc_now_iso(),
        "predictions": str(Path(args.predictions).resolve()),
        "labels": str(Path(args.labels).resolve()),
        "metrics": metrics,
        "clean_note": (
            "This script is offline-only. Its outputs must not be read by "
            "prediction, retrieval, compiler, answer, or verifier modules."
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
    return parser.parse_args()


def _read_jsonl(path: str | Path) -> list[dict[str, object]]:
    rows = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


if __name__ == "__main__":
    raise SystemExit(main())
