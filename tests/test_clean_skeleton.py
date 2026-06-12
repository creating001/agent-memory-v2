from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from agent_memory.clean import CleanProtocolViolation, assert_clean_prediction_payload
from agent_memory.io import load_prediction_jsonl
from agent_memory.pipeline import Stage1Pipeline
from agent_memory.schemas import PredictionRequest, Turn


class CleanSkeletonTest(unittest.TestCase):
    def test_clean_guard_rejects_gold_answer(self) -> None:
        with self.assertRaises(CleanProtocolViolation):
            assert_clean_prediction_payload(
                {
                    "question": "What did I say?",
                    "gold_answer": "hidden",
                    "turns": [],
                }
            )

    def test_clean_guard_rejects_benchmark_label(self) -> None:
        with self.assertRaises(CleanProtocolViolation):
            assert_clean_prediction_payload(
                {
                    "question": "What did I say?",
                    "question_type": "temporal-reasoning",
                    "turns": [],
                }
            )

    def test_record_key_does_not_enter_pipeline(self) -> None:
        payload = {
            "record_key": "runner-only",
            "question": "What tea does Alex prefer?",
            "sessions": [
                {
                    "session_id": "s1",
                    "turns": [
                        {"role": "user", "text": "Alex prefers jasmine tea."}
                    ],
                }
            ],
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "input.jsonl"
            path.write_text(json.dumps(payload) + "\n", encoding="utf-8")
            envelopes = list(load_prediction_jsonl(path))

        self.assertEqual(envelopes[0].record_key, "runner-only")
        self.assertNotIn("runner-only", envelopes[0].request.question)
        self.assertEqual(envelopes[0].request.turns[0].source_id, "s1:turn_0000")

    def test_pipeline_keeps_source_ids_in_compiled_context(self) -> None:
        config = {
            "retrieval": {"top_k": 4, "max_top_k": 8, "neighbor_window": 1},
            "compiler": {"max_evidence_items": 10, "max_evidence_chars": 4000},
            "answer": {"fallback_answer": "I do not know."},
        }
        request = PredictionRequest(
            question="What tea does Alex prefer?",
            turns=(
                Turn(
                    source_id="s1:t0",
                    session_id="s1",
                    turn_index=0,
                    role="user",
                    text="Alex drinks coffee in the morning.",
                ),
                Turn(
                    source_id="s1:t1",
                    session_id="s1",
                    turn_index=1,
                    role="user",
                    text="Alex prefers jasmine tea in the afternoon.",
                ),
            ),
        )
        result = Stage1Pipeline(config).predict(request)
        rows = result["trace"]["compiled_context"]["evidence_rows"]

        self.assertTrue(rows)
        self.assertTrue(all(row["source_id"] for row in rows))
        self.assertEqual(result["trace"]["token_cost"]["query_tokens"], 0)


if __name__ == "__main__":
    unittest.main()
