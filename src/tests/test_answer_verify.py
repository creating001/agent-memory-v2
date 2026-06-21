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

    def test_source_grounded_audit_tracks_lifecycle_audit_support(self) -> None:
        audit = audit_answer_support(
            compiled=_compiled(row_count=3),
            answer=_answer(
                {
                    "sufficient": True,
                    "evidence_report": [{"memory": "Memory 3", "status": "support"}],
                    "answer": "jasmine tea",
                }
            ),
            enabled=True,
            context_manifest={
                "memory_operations": {
                    "lifecycle_audit_final_source_ids": ("s1:t2",)
                }
            },
        )

        self.assertEqual(audit.registry_backed_final_evidence_count, 1)
        self.assertEqual(audit.registry_backed_support_reference_count, 1)
        self.assertEqual(audit.registry_backed_support_references, (3,))

    def test_source_grounded_audit_tracks_layer_manifest_support(self) -> None:
        audit = audit_answer_support(
            compiled=_compiled(row_count=3),
            answer=_answer(
                {
                    "sufficient": True,
                    "evidence_report": [{"memory": "Memory 1", "status": "support"}],
                    "answer": "jasmine tea",
                }
            ),
            enabled=True,
            context_manifest={
                "memory_operations": {
                    "layer_manifest_final_source_ids": ("s1:t0",)
                }
            },
        )

        self.assertEqual(audit.registry_backed_final_evidence_count, 1)
        self.assertEqual(audit.registry_backed_support_reference_count, 1)
        self.assertEqual(audit.registry_backed_support_references, (1,))

    def test_source_grounded_audit_tracks_workspace_query_policy(self) -> None:
        audit = audit_answer_support(
            compiled=_compiled(row_count=1),
            answer=_answer(
                {
                    "sufficient": True,
                    "evidence_report": [{"memory": "Memory 1", "status": "support"}],
                    "answer": "Alex prefers jasmine tea.",
                }
            ),
            enabled=True,
            context_manifest={
                "context_organization": {
                    "workspace_query_policy": {
                        "available": True,
                        "applied": True,
                        "replaced_components": (
                            "structured_guide",
                            "memory_value_slot_guide",
                        ),
                        "packet_candidate_count": 1,
                        "packet_candidate_source_labels": ("Memory 1",),
                        "packet_candidate_focus_counts": {"current_state": 1},
                        "packet_candidate_verifier_checks": (
                            "source_backing",
                            "raw_row_expansion",
                        ),
                    }
                }
            },
        )

        self.assertTrue(audit.workspace_query_policy_available)
        self.assertTrue(audit.workspace_query_policy_applied)
        self.assertEqual(
            audit.workspace_query_policy_replaced_components,
            ("structured_guide", "memory_value_slot_guide"),
        )
        self.assertEqual(audit.workspace_query_policy_packet_candidate_count, 1)
        self.assertEqual(
            audit.workspace_query_policy_packet_candidate_source_labels,
            ("Memory 1",),
        )
        self.assertEqual(
            audit.workspace_query_policy_packet_candidate_focus_counts,
            {"current_state": 1},
        )
        self.assertEqual(
            audit.workspace_query_policy_packet_candidate_verifier_checks,
            ("source_backing", "raw_row_expansion"),
        )

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

    def test_consistency_audit_flags_numeric_value_not_in_support(self) -> None:
        audit = audit_answer_support(
            compiled=_compiled_from_rows(
                question="How many postcards does Alex have?",
                rows=(
                    _row(
                        source_id="s1:t0",
                        role="user",
                        text="Alex said they have 41 postcards.",
                    ),
                ),
            ),
            answer=_answer(
                {
                    "sufficient": True,
                    "evidence_report": [{"memory": "Memory 1", "status": "support"}],
                    "answer": "Alex has 42 postcards.",
                }
            ),
            enabled=True,
        )

        self.assertEqual(audit.risks, ())
        self.assertIn("numeric_value_not_in_support", audit.consistency_risks)
        self.assertEqual(audit.consistency_dimension_counts["numeric"], 1)
        self.assertEqual(audit.consistency_risk_counts["numeric"], 1)

    def test_consistency_audit_flags_speaker_role_mismatch(self) -> None:
        audit = audit_answer_support(
            compiled=_compiled_from_rows(
                question="What did you recommend to Alex?",
                rows=(
                    _row(
                        source_id="s1:t0",
                        role="user",
                        text="Alex recommended jasmine tea.",
                    ),
                ),
            ),
            answer=_answer(
                {
                    "sufficient": True,
                    "evidence_report": [{"memory": "Memory 1", "status": "support"}],
                    "answer": "Jasmine tea.",
                }
            ),
            enabled=True,
        )

        self.assertEqual(audit.risks, ())
        self.assertIn("speaker_role_mismatch", audit.consistency_risks)
        self.assertEqual(audit.consistency_dimension_counts["speaker"], 1)
        self.assertEqual(audit.consistency_risk_counts["speaker"], 1)

    def test_consistency_audit_flags_state_conflict_without_verify_audit(
        self,
    ) -> None:
        audit = audit_answer_support(
            compiled=_compiled_from_rows(
                question="Where does Alex live now?",
                rows=(
                    _row(
                        source_id="s2:t0",
                        role="user",
                        text="Alex moved to Seattle.",
                    ),
                ),
            ),
            answer=_answer(
                {
                    "sufficient": True,
                    "evidence_report": [{"memory": "Memory 1", "status": "support"}],
                    "answer": "Seattle.",
                }
            ),
            enabled=True,
            context_manifest={
                "memory_operations": {
                    "memory_system_state_available": True,
                    "memory_system_state_focus_counts": {"conflict_chain": 1},
                    "memory_operation_journal_available": True,
                    "memory_operation_journal_operation_counts": {"supersede": 1},
                }
            },
        )

        self.assertEqual(audit.risks, ())
        self.assertIn(
            "state_conflict_without_verify_or_audit",
            audit.consistency_risks,
        )
        self.assertEqual(audit.consistency_dimension_counts["state_conflict"], 1)
        self.assertEqual(audit.consistency_risk_counts["state_conflict"], 1)


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


def _compiled_from_rows(
    *,
    question: str,
    rows: tuple[EvidenceRow, ...],
) -> CompiledContext:
    return CompiledContext(
        question=question,
        question_time=None,
        route=RouteResult("fact_lookup", ("fact",)),
        evidence_rows=rows,
        prompt="Memory Context",
        context_chars=120,
    )


def _row(*, source_id: str, role: str, text: str) -> EvidenceRow:
    turn_index = int(source_id.rsplit("t", 1)[-1])
    return EvidenceRow(
        source_id=source_id,
        session_id=source_id.split(":", 1)[0],
        turn_index=turn_index,
        role=role,
        text=text,
        timestamp=None,
        retrieval_rank=turn_index + 1,
        retrieval_score=1.0,
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
