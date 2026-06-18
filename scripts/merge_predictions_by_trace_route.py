#!/usr/bin/env python3
"""Merge completed prediction files by prediction-time trace route.

This is an offline diagnostic helper for controlled ablations. It reads only
prediction outputs and prediction-time traces. It must not read labels, judge
outputs, benchmark categories, sample ids, row indices, or test feedback.
"""

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

from common.experiment import collect_git_state, utc_now_iso, write_json  # noqa: E402


def main() -> int:
    args = _parse_args()
    base_predictions = _read_prediction_records(args.base_predictions)
    override_predictions = _read_prediction_map(args.override_predictions)
    route_by_key = _read_trace_routes(args.traces)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    merged, counts = merge_predictions_by_trace_route(
        base_predictions=base_predictions,
        override_predictions=override_predictions,
        route_by_key=route_by_key,
        routes=_route_set(args.route),
    )
    with output_path.open("w", encoding="utf-8") as handle:
        for record in merged:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    manifest = {
        "created_at_utc": utc_now_iso(),
        "base_predictions": str(Path(args.base_predictions).resolve()),
        "override_predictions": str(Path(args.override_predictions).resolve()),
        "traces": str(Path(args.traces).resolve()),
        "route": args.route,
        "output": str(output_path.resolve()),
        "counts": counts,
        "clean_note": (
            "Merged from prediction outputs and prediction-time traces only; "
            "no labels, judge outputs, benchmark categories, sample ids, row "
            "indices, or test feedback were read."
        ),
        "git": collect_git_state(REPO_ROOT),
    }
    if args.manifest_output:
        write_json(args.manifest_output, manifest)
    print(json.dumps(manifest, ensure_ascii=False, sort_keys=True))
    return 0


def merge_predictions_by_trace_route(
    *,
    base_predictions: list[dict[str, str]],
    override_predictions: dict[str, str],
    route_by_key: dict[str, str],
    routes: frozenset[str],
) -> tuple[list[dict[str, str]], dict[str, int]]:
    override_keys = set(override_predictions)
    route_keys = {key for key, value in route_by_key.items() if value in routes}
    missing_route_keys = sorted(override_keys.difference(route_keys))
    if missing_route_keys:
        preview = ", ".join(missing_route_keys[:5])
        route_names = ", ".join(sorted(routes))
        raise ValueError(
            f"override predictions include keys outside routes {route_names}: {preview}"
        )

    merged: list[dict[str, str]] = []
    seen_base: set[str] = set()
    counts = {
        "total": 0,
        "from_base": 0,
        "from_override": 0,
        "base_records_missing_route": 0,
        "override_predictions_missing_from_base": 0,
    }
    for record in base_predictions:
        key = record["record_key"]
        seen_base.add(key)
        if key not in route_by_key:
            counts["base_records_missing_route"] += 1
        if key in override_predictions:
            answer = override_predictions[key]
            counts["from_override"] += 1
        else:
            answer = record["answer"]
            counts["from_base"] += 1
        counts["total"] += 1
        merged.append({"record_key": key, "answer": answer})

    counts["override_predictions_missing_from_base"] = len(
        override_keys.difference(seen_base)
    )
    if counts["override_predictions_missing_from_base"]:
        missing = sorted(override_keys.difference(seen_base))
        preview = ", ".join(missing[:5])
        raise ValueError(f"override predictions missing from base: {preview}")
    return merged, counts


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-predictions", required=True)
    parser.add_argument("--override-predictions", required=True)
    parser.add_argument("--traces", required=True)
    parser.add_argument(
        "--route",
        required=True,
        help="Allowed prediction-time route, or comma-separated routes.",
    )
    parser.add_argument("--output", required=True)
    parser.add_argument("--manifest-output")
    return parser.parse_args()


def _read_prediction_records(path: str | Path) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            item = json.loads(line)
            record_key = item.get("record_key")
            if record_key is None:
                raise ValueError(f"Missing record_key in {path}")
            records.append(
                {
                    "record_key": str(record_key),
                    "answer": str(item.get("answer", "")),
                }
            )
    return records


def _read_prediction_map(path: str | Path) -> dict[str, str]:
    return {
        record["record_key"]: record["answer"]
        for record in _read_prediction_records(path)
    }


def _read_trace_routes(path: str | Path) -> dict[str, str]:
    routes: dict[str, str] = {}
    with Path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            item = json.loads(line)
            record_key = item.get("record_key")
            if record_key is None:
                raise ValueError(f"Missing record_key in {path}")
            trace = item.get("trace") or {}
            route = trace.get("route") or {}
            routes[str(record_key)] = str(route.get("information_need") or "")
    return routes


def _route_set(value: str) -> frozenset[str]:
    routes = frozenset(route.strip() for route in value.split(",") if route.strip())
    if not routes:
        raise ValueError("--route must include at least one route")
    return routes


if __name__ == "__main__":
    raise SystemExit(main())
