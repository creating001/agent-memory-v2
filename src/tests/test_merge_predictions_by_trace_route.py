from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "merge_predictions_by_trace_route.py"

spec = importlib.util.spec_from_file_location(
    "merge_predictions_by_trace_route", SCRIPT_PATH
)
assert spec is not None
merge_module = importlib.util.module_from_spec(spec)
sys.modules["merge_predictions_by_trace_route"] = merge_module
assert spec.loader is not None
spec.loader.exec_module(merge_module)


class MergePredictionsByTraceRouteTest(unittest.TestCase):
    def test_merge_preserves_base_order_and_scopes_override_route(self) -> None:
        merged, counts = merge_module.merge_predictions_by_trace_route(
            base_predictions=[
                {"record_key": "a", "answer": "base a"},
                {"record_key": "b", "answer": "base b"},
                {"record_key": "c", "answer": "base c"},
            ],
            override_predictions={"b": "override b"},
            route_by_key={"a": "fact_lookup", "b": "temporal_lookup", "c": "list_count"},
            routes=frozenset({"temporal_lookup"}),
        )

        self.assertEqual(
            merged,
            [
                {"record_key": "a", "answer": "base a"},
                {"record_key": "b", "answer": "override b"},
                {"record_key": "c", "answer": "base c"},
            ],
        )
        self.assertEqual(
            counts,
            {
                "total": 3,
                "from_base": 2,
                "from_override": 1,
                "base_records_missing_route": 0,
                "override_predictions_missing_from_base": 0,
            },
        )

    def test_merge_rejects_override_outside_route(self) -> None:
        with self.assertRaisesRegex(ValueError, "outside routes"):
            merge_module.merge_predictions_by_trace_route(
                base_predictions=[{"record_key": "a", "answer": "base a"}],
                override_predictions={"a": "override a"},
                route_by_key={"a": "fact_lookup"},
                routes=frozenset({"temporal_lookup"}),
            )

    def test_merge_accepts_multiple_routes(self) -> None:
        merged, counts = merge_module.merge_predictions_by_trace_route(
            base_predictions=[
                {"record_key": "a", "answer": "base a"},
                {"record_key": "b", "answer": "base b"},
                {"record_key": "c", "answer": "base c"},
            ],
            override_predictions={"a": "override a", "b": "override b"},
            route_by_key={
                "a": "profile_preference",
                "b": "current_state",
                "c": "fact_lookup",
            },
            routes=frozenset({"profile_preference", "current_state"}),
        )

        self.assertEqual(
            merged,
            [
                {"record_key": "a", "answer": "override a"},
                {"record_key": "b", "answer": "override b"},
                {"record_key": "c", "answer": "base c"},
            ],
        )
        self.assertEqual(counts["from_override"], 2)


if __name__ == "__main__":
    unittest.main()
