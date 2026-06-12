from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from evaluation.diagnostics import evidence_recall


class DiagnosticsTest(unittest.TestCase):
    def test_locomo_evidence_recall_matches_dialog_id(self) -> None:
        metrics = evidence_recall(
            [
                {
                    "record_key": "a",
                    "trace": {
                        "compiled_context": {
                            "evidence_rows": [{"source_id": "D1:3"}],
                        }
                    },
                }
            ],
            [{"record_key": "a", "evidence": ["D1:3"], "category": 2}],
        )

        self.assertEqual(metrics["evidence_recall"], 1.0)
        self.assertEqual(metrics["by_type"]["2"]["n"], 1)

    def test_longmemeval_evidence_recall_matches_session_prefix(self) -> None:
        metrics = evidence_recall(
            [
                {
                    "record_key": "a",
                    "trace": {
                        "compiled_context": {
                            "evidence_rows": [{"source_id": "answer-session:turn_0000"}],
                        }
                    },
                }
            ],
            [
                {
                    "record_key": "a",
                    "answer_session_ids": ["answer-session"],
                    "question_type": "multi-session",
                }
            ],
        )

        self.assertEqual(metrics["evidence_recall"], 1.0)

    def test_longmemeval_evidence_recall_matches_duplicate_session_prefix(self) -> None:
        metrics = evidence_recall(
            [
                {
                    "record_key": "a",
                    "trace": {
                        "compiled_context": {
                            "evidence_rows": [
                                {"source_id": "answer-session:occ_0001:turn_0000"}
                            ],
                        }
                    },
                }
            ],
            [{"record_key": "a", "answer_session_ids": ["answer-session"]}],
        )

        self.assertEqual(metrics["evidence_recall"], 1.0)


if __name__ == "__main__":
    unittest.main()
