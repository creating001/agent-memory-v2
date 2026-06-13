from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from common.schemas import RouteResult
from memory.query_planner import (
    NullQueryPlanner,
    _build_planner_prompt,
    _normalize_queries,
    _queries_from_payload,
)


class QueryPlannerTest(unittest.TestCase):
    def test_null_planner_returns_original_question_without_token_cost(self) -> None:
        plan = NullQueryPlanner().plan(
            "What tea does Alex prefer?",
            "2024-01-02",
            RouteResult(information_need="fact_lookup", signals=()),
        )

        self.assertEqual(plan.queries, ("What tea does Alex prefer?",))
        self.assertEqual(plan.token_usage.query_tokens, 0)
        self.assertEqual(plan.planner, "null")

    def test_normalize_queries_keeps_original_first_and_deduplicates(self) -> None:
        queries = _normalize_queries(
            question="What tea does Alex prefer?",
            raw_queries=[
                "what tea does alex prefer?",
                "Alex preferred drink afternoon tea",
                "Alex beverage preference jasmine tea",
            ],
            max_queries=3,
            max_query_chars=80,
        )

        self.assertEqual(
            queries,
            (
                "What tea does Alex prefer?",
                "Alex preferred drink afternoon tea",
                "Alex beverage preference jasmine tea",
            ),
        )

    def test_queries_from_payload_accepts_json_object_only(self) -> None:
        self.assertEqual(
            _queries_from_payload('{"queries":["first","second"]}'),
            ["first", "second"],
        )
        self.assertEqual(_queries_from_payload('{"answer":"hidden"}'), [])
        self.assertEqual(_queries_from_payload("not json"), [])

    def test_planner_prompt_contains_clean_red_lines(self) -> None:
        prompt = _build_planner_prompt(
            question="What did Alex update?",
            question_time="2024-01-02",
            route=RouteResult(
                information_need="current_state",
                signals=("recent_or_current",),
            ),
            max_queries=4,
        )

        for forbidden_source in (
            "gold answers",
            "judge output",
            "benchmark labels",
            "sample ids",
            "qids",
            "row indices",
            "test feedback",
        ):
            self.assertIn(forbidden_source, prompt)
        self.assertIn("Do not answer the question", prompt)
        self.assertIn("Question: What did Alex update?", prompt)


if __name__ == "__main__":
    unittest.main()
