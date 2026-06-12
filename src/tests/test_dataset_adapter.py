from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from data.adapters import prepare_records
from common.clean import assert_clean_prediction_payload
from evaluation.metrics import evaluate_offline


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
                    "conversation": {
                        "session_1": [{"speaker": "A", "dia_id": "D1:1", "text": "hello"}],
                    },
                    "qa": [
                        {
                            "question": "Included?",
                            "answer": "yes",
                            "category": "1",
                        },
                        {
                            "question": "Excluded?",
                            "answer": "no",
                            "category": "5",
                        },
                    ],
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

    def test_longmemeval_adapter_separates_labels(self) -> None:
        records = prepare_records(
            [
                {
                    "question_id": "qid-1",
                    "question_type": "multi-session",
                    "question": "What degree did I graduate with?",
                    "question_date": "2023/05/30",
                    "answer": "Business Administration",
                    "answer_session_ids": ["answer-session"],
                    "haystack_dates": ["2023/05/20"],
                    "haystack_session_ids": ["session-a"],
                    "haystack_sessions": [
                        [
                            {
                                "role": "user",
                                "content": "I graduated with Business Administration.",
                                "has_answer": True,
                            }
                        ]
                    ],
                }
            ],
            benchmark="longmemeval",
            subset="s_cleaned",
        )

        prediction = records[0].prediction
        label = records[0].label
        assert_clean_prediction_payload(
            {key: value for key, value in prediction.items() if key != "record_key"}
        )
        prediction_text = str(prediction)
        self.assertNotIn("qid-1", prediction_text)
        self.assertNotIn("multi-session", prediction_text)
        self.assertNotIn("answer_session_ids", prediction_text)
        self.assertNotIn("'answer'", prediction_text)
        self.assertNotIn("has_answer", prediction_text)
        self.assertEqual(label["source_question_id"], "qid-1")
        self.assertEqual(label["gold_answer"], "Business Administration")

    def test_longmemeval_adapter_skips_empty_turns(self) -> None:
        records = prepare_records(
            [
                {
                    "question_id": "qid-empty",
                    "question_type": "single-session-user",
                    "question": "What did I say?",
                    "answer": "hello",
                    "haystack_session_ids": ["session-a"],
                    "haystack_sessions": [
                        [
                            {"role": "user", "content": ""},
                            {"role": "user", "content": "hello"},
                        ]
                    ],
                }
            ],
            benchmark="longmemeval",
            subset="s_cleaned",
        )

        turns = records[0].prediction["sessions"][0]["turns"]
        self.assertEqual(len(turns), 1)
        self.assertEqual(turns[0]["source_id"], "session-a:turn_0001")

    def test_longmemeval_duplicate_session_ids_get_unique_source_ids(self) -> None:
        records = prepare_records(
            [
                {
                    "question": "What play did I attend?",
                    "answer": "Hamlet",
                    "answer_session_ids": ["session-a"],
                    "haystack_session_ids": ["session-a", "session-a"],
                    "haystack_sessions": [
                        [{"role": "user", "content": "first copy"}],
                        [{"role": "user", "content": "second copy"}],
                    ],
                }
            ],
            benchmark="longmemeval",
            subset="s_cleaned",
        )

        turns = [
            turn
            for session in records[0].prediction["sessions"]
            for turn in session["turns"]
        ]
        source_ids = [turn["source_id"] for turn in turns]
        self.assertEqual(len(source_ids), len(set(source_ids)))
        self.assertEqual(source_ids[0], "session-a:turn_0000")
        self.assertEqual(source_ids[1], "session-a:occ_0001:turn_0000")

    def test_locomo_adapter_expands_qa_and_filters_category_5(self) -> None:
        records = prepare_records(
            [
                {
                    "sample_id": "conv-1",
                    "conversation": {
                        "speaker_a": "A",
                        "speaker_b": "B",
                        "session_1_date_time": "1 Jan, 2024",
                        "session_1": [
                            {
                                "speaker": "A",
                                "dia_id": "D1:1",
                                "text": "I went to a support group.",
                            }
                        ],
                    },
                    "qa": [
                        {
                            "question": "Where did A go?",
                            "answer": "support group",
                            "category": 2,
                            "evidence": ["D1:1"],
                        },
                        {
                            "question": "Adversarial?",
                            "answer": "hidden",
                            "category": 5,
                            "evidence": ["D1:1"],
                        },
                    ],
                }
            ],
            benchmark="locomo",
            subset="non-adversarial",
        )

        self.assertEqual(len(records), 1)
        prediction = records[0].prediction
        label = records[0].label
        assert_clean_prediction_payload(
            {key: value for key, value in prediction.items() if key != "record_key"}
        )
        prediction_text = str(prediction)
        self.assertNotIn("category", prediction_text)
        self.assertNotIn("evidence", prediction_text)
        self.assertNotIn("conv-1", prediction_text)
        self.assertEqual(label["category"], 2)
        self.assertEqual(label["evidence"], ["D1:1"])

    def test_locomo_duplicate_clean_payloads_get_unique_runner_keys(self) -> None:
        records = prepare_records(
            [
                {
                    "sample_id": "conv-dup",
                    "conversation": {
                        "session_1": [
                            {"speaker": "A", "dia_id": "D1:1", "text": "hello"}
                        ],
                    },
                    "qa": [
                        {"question": "Same question?", "answer": "one", "category": 1},
                        {"question": "Same question?", "answer": "two", "category": 1},
                    ],
                }
            ],
            benchmark="locomo",
            subset="non-adversarial",
        )

        keys = [record.prediction["record_key"] for record in records]
        self.assertEqual(len(keys), 2)
        self.assertEqual(len(set(keys)), 2)


if __name__ == "__main__":
    unittest.main()
