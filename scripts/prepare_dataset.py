#!/usr/bin/env python3
"""Prepare clean prediction JSONL and offline labels from benchmark rows."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from data.adapters import prepare_records, read_json_or_jsonl  # noqa: E402
from common.clean import assert_clean_prediction_payload  # noqa: E402
from common.experiment import collect_git_state, utc_now_iso, write_json  # noqa: E402


def main() -> int:
    args = _parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    prediction_path = output_dir / "prediction_input.jsonl"
    labels_path = output_dir / "labels.jsonl"
    manifest_path = output_dir / "prepare_manifest.json"

    rows = read_json_or_jsonl(args.input)
    prepared = prepare_records(rows, benchmark=args.benchmark, subset=args.subset)

    with prediction_path.open("w", encoding="utf-8") as prediction_handle:
        with labels_path.open("w", encoding="utf-8") as labels_handle:
            for record in prepared:
                prediction_payload = {
                    key: value
                    for key, value in record.prediction.items()
                    if key != "record_key"
                }
                assert_clean_prediction_payload(prediction_payload)
                prediction_handle.write(
                    json.dumps(record.prediction, ensure_ascii=False, sort_keys=True)
                    + "\n"
                )
                labels_handle.write(
                    json.dumps(record.label, ensure_ascii=False, sort_keys=True) + "\n"
                )

    write_json(
        manifest_path,
        {
            "created_at_utc": utc_now_iso(),
            "input": str(Path(args.input).resolve()),
            "benchmark": args.benchmark,
            "subset": args.subset,
            "n_input_rows": len(rows),
            "n_prepared_rows": len(prepared),
            "outputs": {
                "prediction_input": str(prediction_path.resolve()),
                "labels": str(labels_path.resolve()),
            },
            "clean_note": (
                "Gold answers, benchmark labels, categories, qids, sample ids, and "
                "row indices are excluded from prediction_input.jsonl. Labels are "
                "for offline evaluation only."
            ),
            "git": collect_git_state(REPO_ROOT),
        },
    )
    print(str(prediction_path))
    print(str(labels_path))
    return 0


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument(
        "--benchmark",
        required=True,
        choices=("longmemeval", "locomo", "generic"),
    )
    parser.add_argument("--subset", default="full")
    return parser.parse_args()


if __name__ == "__main__":
    raise SystemExit(main())
