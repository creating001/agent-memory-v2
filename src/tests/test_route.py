from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from memory.route import QuestionRouter


class RouteTest(unittest.TestCase):
    def test_when_at_question_start_routes_to_temporal(self) -> None:
        route = QuestionRouter().route("When did Melanie go camping?")

        self.assertEqual(route.information_need, "temporal_lookup")
        self.assertIn("temporal", route.signals)

    def test_subordinate_when_does_not_route_to_temporal(self) -> None:
        route = QuestionRouter().route(
            "Who supports Caroline when she has a negative experience?"
        )

        self.assertEqual(route.information_need, "fact_lookup")
        self.assertNotIn("temporal", route.signals)

    def test_broad_activity_question_is_disabled_by_default(self) -> None:
        route = QuestionRouter().route("What activities has Melanie done with family?")

        self.assertEqual(route.information_need, "fact_lookup")
        self.assertNotIn("list_or_count", route.signals)

    def test_broad_activity_question_can_route_to_list_count(self) -> None:
        route = QuestionRouter(enable_broad_list_patterns=True).route(
            "What activities has Melanie done with family?"
        )

        self.assertEqual(route.information_need, "list_count")
        self.assertIn("list_or_count", route.signals)

    def test_where_has_question_can_route_to_list_count(self) -> None:
        route = QuestionRouter(enable_broad_list_patterns=True).route(
            "Where has Melanie camped?"
        )

        self.assertEqual(route.information_need, "list_count")
        self.assertIn("list_or_count", route.signals)


if __name__ == "__main__":
    unittest.main()
