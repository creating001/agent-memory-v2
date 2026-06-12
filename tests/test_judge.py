from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from agent_memory.judge import (
    JudgeExample,
    accuracy_from_judgments,
    build_judge_prompt,
    parse_judge_label,
)


class JudgeTest(unittest.TestCase):
    def test_locomo_prompt_requires_json_label(self) -> None:
        prompt = build_judge_prompt(
            JudgeExample(
                record_key="a",
                question="What tea?",
                gold_answer="jasmine tea",
                generated_answer="jasmine tea",
                benchmark="locomo",
            )
        )

        self.assertIn("Return ONLY a valid JSON object", prompt)
        self.assertEqual(parse_judge_label("locomo", '{"label":"CORRECT"}'), "CORRECT")

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


if __name__ == "__main__":
    unittest.main()
