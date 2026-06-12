from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from agent_memory.adapters import prepare_records
from agent_memory.clean import assert_clean_prediction_payload
from agent_memory.metrics import evaluate_offline


class DatasetAdapterTest(unittest.TestCase):
    def test_prepare_records_strips_prediction_forbidden_fields(self) -> None:
        records = prepare_records(
            [
                {
                    "sample_id": "leaky-id",
                    "question": "What tea does Alex prefer?",
                    "gold_answer": "jasmine tea",
                    "question_type": "profile",
                    "sessions": [
                        {
                            "session_id": "s1",
                            "turns": [
                                {
                                    "role": "user",
                                    "text": "Alex prefers jasmine tea.",
                                }
                            ],
                        }
                    ],
                }
            ],
            benchmark="generic",
            subset="full",
        )

        self.assertEqual(len(records), 1)
        prediction = records[0].prediction
        label = records[0].label
        assert_clean_prediction_payload(
            {key: value for key, value in prediction.items() if key != "record_key"}
        )
        self.assertNotIn("sample_id", prediction)
        self.assertNotIn("gold_answer", prediction)
        self.assertEqual(label["question"], "What tea does Alex prefer?")
        self.assertEqual(label["gold_answer"], "jasmine tea")
        self.assertEqual(label["question_type"], "profile")

    def test_locomo_non_adversarial_filters_category_5(self) -> None:
        records = prepare_records(
            [
                {
                    "question": "Included?",
                    "answer": "yes",
                    "category": "1",
                    "conversation": [{"role": "user", "text": "hello"}],
                },
                {
                    "question": "Excluded?",
                    "answer": "no",
                    "category": "5",
                    "conversation": [{"role": "user", "text": "secret"}],
                },
            ],
            benchmark="locomo",
            subset="non-adversarial",
        )

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].label["category"], "1")

    def test_offline_metrics_join_by_record_key(self) -> None:
        metrics = evaluate_offline(
            [{"record_key": "a", "answer": "jasmine tea"}],
            [{"record_key": "a", "gold_answer": "jasmine tea", "question_type": "profile"}],
        )

        self.assertEqual(metrics["n_joined"], 1)
        self.assertEqual(metrics["accuracy_exact"], 1.0)
        self.assertEqual(metrics["by_type"]["profile"]["n"], 1)


if __name__ == "__main__":
    unittest.main()
