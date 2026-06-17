from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from evaluation.judge import (
    JudgeExample,
    accuracy_from_judgments,
    build_judge_prompt,
    dual_accuracy_from_judgments,
    parse_judge_label,
)


class JudgeTest(unittest.TestCase):
    def test_locomo_prompt_requires_single_label(self) -> None:
        prompt = build_judge_prompt(
            JudgeExample(
                record_key="a",
                question="What tea?",
                gold_answer="jasmine tea",
                generated_answer="jasmine tea",
                benchmark="locomo",
            )
        )

        self.assertIn("Return exactly one label: CORRECT or WRONG", prompt)
        self.assertNotIn("reasoning", prompt)
        self.assertEqual(parse_judge_label("locomo", "CORRECT"), "CORRECT")
        self.assertEqual(parse_judge_label("locomo", "WRONG"), "WRONG")
        self.assertEqual(
            parse_judge_label("locomo", '{"reasoning":"legacy","label":"CORRECT"}'),
            "CORRECT",
        )

    def test_longmemeval_temporal_prompt_uses_off_by_one_rule(self) -> None:
        prompt = build_judge_prompt(
            JudgeExample(
                record_key="a",
                question="How many days?",
                gold_answer="18",
                generated_answer="19",
                benchmark="longmemeval",
                question_type="temporal-reasoning",
            )
        )

        self.assertIn("off-by-one", prompt)
        self.assertEqual(parse_judge_label("longmemeval", "yes"), "CORRECT")

    def test_accuracy_counts_only_valid_judgments(self) -> None:
        metrics = accuracy_from_judgments(
            [
                {"label": "CORRECT"},
                {"label": "WRONG"},
                {"label": "INVALID"},
            ]
        )

        self.assertEqual(metrics["n_valid"], 2)
        self.assertEqual(metrics["accuracy"], 0.5)

    def test_dual_accuracy_reports_strict_and_lenient(self) -> None:
        report = dual_accuracy_from_judgments(
            [
                {"record_key": "a", "label": "CORRECT"},
                {"record_key": "b", "label": "CORRECT"},
                {"record_key": "c", "label": "INVALID"},
            ],
            [
                {"record_key": "a", "label": "CORRECT"},
                {"record_key": "b", "label": "WRONG"},
                {"record_key": "c", "label": "CORRECT"},
            ],
            labels_by_key={
                "a": {"question_type": "single-hop"},
                "b": {"question_type": "multi-hop"},
                "c": {"question_type": "multi-hop"},
            },
            group_field="question_type",
        )

        metrics = report["metrics"]
        self.assertEqual(metrics["n_joined"], 3)
        self.assertEqual(metrics["strict_correct"], 1)
        self.assertEqual(metrics["lenient_correct"], 3)
        self.assertEqual(metrics["n_any_invalid"], 1)
        self.assertEqual(metrics["strict_accuracy"], 1 / 3)
        self.assertEqual(metrics["lenient_accuracy"], 1.0)
        self.assertEqual(report["by_group"]["multi-hop"]["n_joined"], 2)


if __name__ == "__main__":
    unittest.main()
