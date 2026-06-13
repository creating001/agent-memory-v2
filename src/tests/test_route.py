from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from common.schemas import RouteResult, TokenUsage
from memory.question_analysis import (
    QuestionAnalysisResult,
    route_from_question_analysis,
)
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

    def test_recommendation_profile_route_is_disabled_by_default(self) -> None:
        route = QuestionRouter().route(
            "Can you recommend a show or movie for me to watch tonight?"
        )

        self.assertEqual(route.information_need, "fact_lookup")
        self.assertNotIn("personalized_recommendation", route.signals)

    def test_recommendation_profile_route_can_be_enabled(self) -> None:
        route = QuestionRouter(enable_recommendation_profile_patterns=True).route(
            "Can you recommend a show or movie for me to watch tonight?"
        )

        self.assertEqual(route.information_need, "profile_preference")
        self.assertIn("profile_or_preference", route.signals)
        self.assertIn("personalized_recommendation", route.signals)

    def test_temporal_order_question_stays_temporal_when_recommendation_enabled(self) -> None:
        route = QuestionRouter(enable_recommendation_profile_patterns=True).route(
            "Which events happened in order from first to last by day?"
        )

        self.assertEqual(route.information_need, "temporal_lookup")
        self.assertIn("temporal", route.signals)

    def test_explicit_duration_overrides_latest_entity_description(self) -> None:
        route = QuestionRouter(temporal_priority_over_recent=True).route(
            "How many days had passed since I finished the novel when I attended "
            "the event where the author discussed her latest thriller?"
        )

        self.assertEqual(route.information_need, "temporal_lookup")
        self.assertIn("temporal", route.signals)
        self.assertNotIn("recent_or_current", route.signals)

    def test_plain_latest_question_still_routes_to_current_state(self) -> None:
        route = QuestionRouter().route("What is my latest phone model?")

        self.assertEqual(route.information_need, "current_state")
        self.assertIn("recent_or_current", route.signals)

    def test_recent_current_has_default_priority_over_temporal(self) -> None:
        route = QuestionRouter().route(
            "How many days had passed before the latest event?"
        )

        self.assertEqual(route.information_need, "current_state")
        self.assertIn("recent_or_current", route.signals)

    def test_question_analysis_routes_count_with_time_scope_as_list_count(self) -> None:
        fallback = RouteResult(
            information_need="temporal_lookup",
            signals=("temporal",),
            retrieval_multiplier=2,
        )
        analysis = QuestionAnalysisResult(
            task="multi_evidence",
            operation="count",
            temporal_subtype="date_time",
            answer_slot="count",
            temporal_hints=("past month",),
            confidence=0.9,
            route_source="llm_question_analysis",
            token_usage=TokenUsage(query_tokens=123),
            raw_response="{}",
        )

        route = route_from_question_analysis(analysis, fallback)

        self.assertEqual(route.information_need, "list_count")
        self.assertIn("llm_question_analysis", route.signals)
        self.assertIn("operation:count", route.signals)
        self.assertIn("temporal", route.signals)


if __name__ == "__main__":
    unittest.main()
