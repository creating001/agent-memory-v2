from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from common.schemas import (  # noqa: E402
    AnswerResult,
    CompiledContext,
    EvidenceRow,
    RouteResult,
    TokenUsage,
)
from memory.answer_verify import audit_answer_support  # noqa: E402


class AnswerVerifyTest(unittest.TestCase):
    def test_source_grounded_audit_passes_supported_answer(self) -> None:
        audit = audit_answer_support(
            compiled=_compiled(row_count=2),
            answer=_answer(
                {
                    "sufficient": True,
                    "evidence_report": [
                        {
                            "memory": "Memory 1",
                            "status": "support",
                            "value": "jasmine tea",
                        }
                    ],
                    "answer": "jasmine tea",
                }
            ),
            enabled=True,
        )

        self.assertTrue(audit.applied)
        self.assertEqual(audit.risks, ())
        self.assertEqual(audit.support_item_count, 1)
        self.assertEqual(audit.final_evidence_row_count, 2)

    def test_source_grounded_audit_flags_answer_without_support(self) -> None:
        audit = audit_answer_support(
            compiled=_compiled(row_count=1),
            answer=_answer(
                {
                    "sufficient": True,
                    "evidence_report": [],
                    "answer": "jasmine tea",
                }
            ),
            enabled=True,
        )

        self.assertIn("missing_evidence_report", audit.risks)
        self.assertIn("answered_without_support_item", audit.risks)

    def test_source_grounded_audit_flags_sufficiency_conflict(self) -> None:
        audit = audit_answer_support(
            compiled=_compiled(row_count=1),
            answer=_answer(
                {
                    "sufficient": False,
                    "evidence_report": [
                        {"memory": "Memory 1", "status": "support"}
                    ],
                    "answer": "jasmine tea",
                }
            ),
            enabled=True,
        )

        self.assertIn("sufficiency_false_but_answered", audit.risks)

    def test_source_grounded_audit_flags_unresolved_memory_reference(self) -> None:
        audit = audit_answer_support(
            compiled=_compiled(row_count=2),
            answer=_answer(
                {
                    "sufficient": True,
                    "evidence_report": [
                        {"memory": "Memory 99", "status": "support"}
                    ],
                    "answer": "jasmine tea",
                }
            ),
            enabled=True,
        )

        self.assertIn("unresolved_memory_reference", audit.risks)
        self.assertEqual(audit.unresolved_memory_references, ("Memory 99",))

    def test_source_grounded_audit_accepts_bare_numeric_memory_reference(self) -> None:
        audit = audit_answer_support(
            compiled=_compiled(row_count=16),
            answer=_answer(
                {
                    "sufficient": True,
                    "evidence_report": [{"memory": "16", "status": "support"}],
                    "answer": "jasmine tea",
                }
            ),
            enabled=True,
        )

        self.assertNotIn("unresolved_memory_reference", audit.risks)
        self.assertEqual(audit.memory_reference_count, 1)

    def test_source_grounded_audit_tracks_registry_backed_support(self) -> None:
        audit = audit_answer_support(
            compiled=_compiled(row_count=3),
            answer=_answer(
                {
                    "sufficient": True,
                    "evidence_report": [{"memory": "Memory 2", "status": "support"}],
                    "answer": "jasmine tea",
                }
            ),
            enabled=True,
            context_manifest={
                "memory_operations": {
                    "registry_projected_final_source_ids": ("s1:t1", "s1:t2")
                }
            },
        )

        self.assertTrue(audit.context_manifest_present)
        self.assertEqual(audit.registry_backed_final_evidence_count, 2)
        self.assertEqual(audit.registry_backed_support_reference_count, 1)
        self.assertEqual(audit.registry_backed_support_references, (2,))

    def test_source_grounded_audit_uses_final_answer_when_json_answer_missing(
        self,
    ) -> None:
        audit = audit_answer_support(
            compiled=_compiled(row_count=1),
            answer=_answer(
                {
                    "sufficient": False,
                    "evidence_report": [
                        {"memory": "Memory 1", "status": "support"}
                    ],
                    "answer": None,
                },
                final_answer="The provided information is not enough.",
            ),
            enabled=True,
        )

        self.assertNotIn("empty_answer", audit.risks)
        self.assertNotIn("sufficiency_false_but_answered", audit.risks)

    def test_source_grounded_audit_disabled_is_noop(self) -> None:
        audit = audit_answer_support(
            compiled=_compiled(row_count=1),
            answer=_answer({"answer": "jasmine tea"}),
            enabled=False,
        )

        self.assertFalse(audit.applied)
        self.assertEqual(audit.reason, "disabled")
        self.assertEqual(audit.risks, ())


def _compiled(*, row_count: int) -> CompiledContext:
    rows = tuple(
        EvidenceRow(
            source_id=f"s1:t{index}",
            session_id="s1",
            turn_index=index,
            role="user",
            text=f"Memory text {index}",
            timestamp=None,
            retrieval_rank=index + 1,
            retrieval_score=1.0,
        )
        for index in range(row_count)
    )
    return CompiledContext(
        question="What tea does Alex prefer?",
        question_time=None,
        route=RouteResult("fact_lookup", ("fact",)),
        evidence_rows=rows,
        prompt="Memory Context",
        context_chars=120,
    )


def _answer(
    payload: dict[str, object],
    *,
    final_answer: str | None = None,
) -> AnswerResult:
    content = json.dumps(payload)
    return AnswerResult(
        answer=(
            final_answer
            if final_answer is not None
            else str(payload.get("answer") or "")
        ),
        model="fake",
        token_usage=TokenUsage(query_tokens=7),
        raw_response=json.dumps({"content": content, "usage": {"total_tokens": 7}}),
    )


if __name__ == "__main__":
    unittest.main()
