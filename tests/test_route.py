from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from agent_memory.route import QuestionRouter


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


if __name__ == "__main__":
    unittest.main()
