from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from common.schemas import RetrievalHit, RouteResult, Turn
from memory.build import MemoryRecord
from memory.compiler import EvidenceCompiler


class CompilerTest(unittest.TestCase):
    def test_compact_query_contract_reduces_external_prompt_without_dropping_evidence(
        self,
    ) -> None:
        kwargs = {
            "max_evidence_items": 4,
            "max_evidence_chars": 4000,
            "prompt_mode": "external_naive",
            "structured_guide": True,
            "temporal_workpad": True,
            "temporal_text_normalization": True,
            "temporal_event_contract": True,
            "evidence_report_contract": True,
            "evidence_report_information_needs": ("temporal_lookup",),
        }
        evidence_turns = (
            Turn(
                source_id="s1:t0",
                session_id="s1",
                turn_index=0,
                role="user",
                text="I visited the clinic yesterday for the follow-up.",
                timestamp="2024-01-08",
            ),
            Turn(
                source_id="s1:t1",
                session_id="s1",
                turn_index=1,
                role="assistant",
                text="Good to know the follow-up was yesterday.",
                timestamp="2024-01-08",
            ),
        )
        compile_kwargs = {
            "question": "When was the clinic follow-up?",
            "question_time": "2024-01-09",
            "route": RouteResult("temporal_lookup", ("temporal",)),
            "hits": (
                RetrievalHit("s1:t0", 1.0, 1, "test"),
                RetrievalHit("s1:t1", 0.9, 2, "test"),
            ),
            "evidence_turns": evidence_turns,
        }

        verbose = EvidenceCompiler(**kwargs).compile(**compile_kwargs)
        compact = EvidenceCompiler(
            **kwargs,
            compact_query_contract=True,
        ).compile(**compile_kwargs)

        self.assertLess(len(compact.prompt), len(verbose.prompt))
        self.assertIn("Structured Evidence Guide:", compact.prompt)
        self.assertIn("Temporal Aid:", compact.prompt)
        self.assertIn("Memory Context:", compact.prompt)
        self.assertIn("### Memory 1", compact.prompt)
        self.assertIn('"evidence_report"', compact.prompt)

    def test_workspace_query_policy_replaces_ready_guides_with_source_backed_packet(
        self,
    ) -> None:
        compiler = EvidenceCompiler(
            max_evidence_items=2,
            max_evidence_chars=4000,
            prompt_mode="external_naive",
            structured_guide=True,
            memory_value_slot_guide=True,
            workspace_query_policy=True,
            workspace_query_policy_replacement_components=(
                "structured_guide",
                "memory_value_slot_guide",
            ),
        )
        memory_object_index = {
            "applied": True,
            "memory_workspace_policy": {
                "applied": True,
                "schema_version": "memory_workspace_policy_v1",
                "query_component_policy": {
                    "structured_guide": {"ready": True},
                    "memory_value_slot_guide": {"ready": True},
                },
            },
            "memory_system_state": {
                "applied": True,
                "entries": (
                    {
                        "target_type": "value_slot",
                        "memory_type": "state",
                        "memory_tier": "working_memory",
                        "focus": "current_state",
                        "status": "active",
                        "source_backed": True,
                        "subject": "Alex",
                        "predicate": "lives_in",
                        "value": "Austin",
                        "values": ("Austin",),
                        "operations": ("retrieve", "expand", "verify"),
                        "source_expansion": {"source_ids": ("s1:t1",)},
                        "slot_coverage_terms": ("alex", "live", "lives", "austin"),
                    },
                ),
            },
            "value_slot_index": (
                {
                    "memory_type": "state",
                    "subject": "Alex",
                    "predicate": "lives_in",
                    "source_backed": True,
                    "value_objects": (
                        {
                            "value": "Austin",
                            "status": "active",
                            "source_ids": ("s1:t1",),
                        },
                    ),
                },
            ),
        }

        compiled = compiler.compile(
            question="Where does Alex live now?",
            question_time=None,
            route=RouteResult("current_state", ("current_state",)),
            hits=(RetrievalHit("s1:t1", 1.0, 1, "test"),),
            evidence_turns=(
                Turn(
                    source_id="s1:t1",
                    session_id="s1",
                    turn_index=1,
                    role="user",
                    text="I live in Austin now.",
                    timestamp="2024-04-01",
                ),
            ),
            memory_object_index=memory_object_index,
        )

        self.assertIn("Working Memory Packet:", compiled.prompt)
        self.assertNotIn("Structured Evidence Guide:", compiled.prompt)
        self.assertNotIn("Memory Value Slot Guide:", compiled.prompt)
        self.assertEqual(
            compiled.diagnostics["workspace_query_policy"]["replaced_components"],
            ["structured_guide", "memory_value_slot_guide"],
        )

    def test_workspace_query_policy_keeps_guides_without_visible_packet_sources(
        self,
    ) -> None:
        compiler = EvidenceCompiler(
            max_evidence_items=2,
            max_evidence_chars=4000,
            prompt_mode="external_naive",
            structured_guide=True,
            workspace_query_policy=True,
            workspace_query_policy_replacement_components=("structured_guide",),
        )
        memory_object_index = {
            "applied": True,
            "memory_workspace_policy": {
                "applied": True,
                "schema_version": "memory_workspace_policy_v1",
                "query_component_policy": {
                    "structured_guide": {"ready": True},
                },
            },
            "memory_system_state": {
                "applied": True,
                "entries": (
                    {
                        "target_type": "value_slot",
                        "memory_type": "state",
                        "source_backed": True,
                        "subject": "Alex",
                        "predicate": "lives_in",
                        "value": "Austin",
                        "values": ("Austin",),
                        "source_expansion": {"source_ids": ("s1:t9",)},
                    },
                ),
            },
        }

        compiled = compiler.compile(
            question="Where does Alex live now?",
            question_time=None,
            route=RouteResult("current_state", ("current_state",)),
            hits=(RetrievalHit("s1:t1", 1.0, 1, "test"),),
            evidence_turns=(
                Turn(
                    source_id="s1:t1",
                    session_id="s1",
                    turn_index=1,
                    role="user",
                    text="I live in Austin now.",
                    timestamp="2024-04-01",
                ),
            ),
            memory_object_index=memory_object_index,
        )

        self.assertIn("Structured Evidence Guide:", compiled.prompt)
        self.assertNotIn("Working Memory Packet:", compiled.prompt)
        self.assertEqual(
            compiled.diagnostics["workspace_query_policy"]["reason"],
            "no_source_backed_packet_candidates",
        )

    def test_compact_query_can_keep_answer_contract_detailed(self) -> None:
        kwargs = {
            "max_evidence_items": 4,
            "max_evidence_chars": 4000,
            "prompt_mode": "external_naive",
            "structured_guide": True,
            "temporal_workpad": True,
            "temporal_text_normalization": True,
            "temporal_event_contract": True,
            "evidence_report_contract": True,
            "evidence_report_information_needs": ("temporal_lookup",),
        }
        evidence_turns = (
            Turn(
                source_id="s1:t0",
                session_id="s1",
                turn_index=0,
                role="user",
                text="I visited the clinic yesterday for the follow-up.",
                timestamp="2024-01-08",
            ),
            Turn(
                source_id="s1:t1",
                session_id="s1",
                turn_index=1,
                role="assistant",
                text="Good to know the follow-up was yesterday.",
                timestamp="2024-01-08",
            ),
        )
        compile_kwargs = {
            "question": "When was the clinic follow-up?",
            "question_time": "2024-01-09",
            "route": RouteResult("temporal_lookup", ("temporal",)),
            "hits": (
                RetrievalHit("s1:t0", 1.0, 1, "test"),
                RetrievalHit("s1:t1", 0.9, 2, "test"),
            ),
            "evidence_turns": evidence_turns,
        }

        verbose = EvidenceCompiler(**kwargs).compile(**compile_kwargs)
        full_compact = EvidenceCompiler(
            **kwargs,
            compact_query_contract=True,
        ).compile(**compile_kwargs)
        guide_compact = EvidenceCompiler(
            **kwargs,
            compact_query_contract=True,
            compact_query_answer_contract=False,
        ).compile(**compile_kwargs)

        self.assertLess(len(guide_compact.prompt), len(verbose.prompt))
        self.assertGreater(len(guide_compact.prompt), len(full_compact.prompt))
        self.assertIn(
            "Use Structured Evidence Guide only as an index into Memory Context",
            guide_compact.prompt,
        )
        self.assertIn('  "evidence_report": [', guide_compact.prompt)
        self.assertNotIn(
            '{"reasoning":"compact evidence decision"', guide_compact.prompt
        )

    def test_inline_memory_context_header_reduces_prompt_without_dropping_evidence(
        self,
    ) -> None:
        kwargs = {
            "max_evidence_items": 4,
            "max_evidence_chars": 4000,
            "prompt_mode": "external_naive",
            "evidence_report_contract": True,
            "evidence_report_information_needs": ("fact_lookup",),
        }
        compile_kwargs = {
            "question": "Which music streaming service does Alex use?",
            "question_time": None,
            "route": RouteResult("fact_lookup", ("fact",)),
            "hits": (RetrievalHit("s1:t0", 1.0, 1, "test"),),
            "evidence_turns": (
                Turn(
                    source_id="s1:t0",
                    session_id="s1",
                    turn_index=0,
                    role="user",
                    text="Alex uses Spotify for music streaming.",
                    timestamp="2024-01-01",
                ),
            ),
        }

        multiline = EvidenceCompiler(**kwargs).compile(**compile_kwargs)
        inline = EvidenceCompiler(
            **kwargs,
            memory_context_header_format="inline",
        ).compile(**compile_kwargs)

        self.assertLess(len(inline.prompt), len(multiline.prompt))
        self.assertIn("### Memory 1", inline.prompt)
        self.assertIn("2024-01-01", inline.prompt)
        self.assertIn("s1", inline.prompt)
        self.assertIn("user: Alex uses Spotify for music streaming.", inline.prompt)
        self.assertIn(
            "### Memory 1 [2024-01-01; s1]\nuser:",
            inline.prompt,
        )
        self.assertNotIn("\nDate: 2024-01-01\nSession: s1\nuser:", inline.prompt)

    def test_inline_spaced_memory_context_header_keeps_row_spacing(self) -> None:
        compiler = EvidenceCompiler(
            max_evidence_items=4,
            max_evidence_chars=4000,
            prompt_mode="external_naive",
            evidence_report_contract=True,
            evidence_report_information_needs=("fact_lookup",),
            memory_context_header_format="inline_spaced",
        )

        compiled = compiler.compile(
            question="Which music streaming service does Alex use?",
            question_time=None,
            route=RouteResult("fact_lookup", ("fact",)),
            hits=(
                RetrievalHit("s1:t0", 1.0, 1, "test"),
                RetrievalHit("s2:t0", 0.9, 2, "test"),
            ),
            evidence_turns=(
                Turn(
                    source_id="s1:t0",
                    session_id="s1",
                    turn_index=0,
                    role="user",
                    text="Alex uses Spotify for music streaming.",
                    timestamp="2024-01-01",
                ),
                Turn(
                    source_id="s2:t0",
                    session_id="s2",
                    turn_index=0,
                    role="assistant",
                    text="I can help compare music services.",
                    timestamp="2024-01-02",
                ),
            ),
        )

        self.assertIn(
            "### Memory 1 [2024-01-01; s1]\nuser: Alex uses Spotify",
            compiled.prompt,
        )
        self.assertIn(
            "music streaming.\n\n### Memory 2 [2024-01-02; s2]\nassistant:",
            compiled.prompt,
        )
        self.assertNotIn("\nDate: 2024-01-01\nSession: s1\nuser:", compiled.prompt)

    def test_structured_guide_memory_hints_are_opt_in(self) -> None:
        compiler = EvidenceCompiler(
            max_evidence_items=4,
            max_evidence_chars=4000,
            prompt_mode="external_naive",
            structured_guide=True,
            max_memory_records=2,
        )

        compiled = compiler.compile(
            question="What books has Melanie read?",
            question_time=None,
            route=RouteResult("list_count", ("list_or_count",)),
            hits=(RetrievalHit("s1:t0", 1.0, 1, "test"),),
            evidence_turns=(
                Turn(
                    source_id="s1:t0",
                    session_id="s1",
                    turn_index=0,
                    role="user",
                    text="I finished Charlotte's Web last weekend.",
                    timestamp="2024-01-08",
                ),
            ),
            memory_records=(
                MemoryRecord(
                    memory_id="m1",
                    memory_type="event",
                    text="Melanie finished Charlotte's Web.",
                    source_ids=("s1:t0",),
                    value="Charlotte's Web",
                ),
            ),
        )

        self.assertIn("Structured Evidence Guide:", compiled.prompt)
        self.assertNotIn("memory_hint=", compiled.prompt)

    def test_structured_guide_memory_hints_are_source_linked_and_route_filtered(self) -> None:
        compiler = EvidenceCompiler(
            max_evidence_items=4,
            max_evidence_chars=4000,
            prompt_mode="external_naive",
            structured_guide=True,
            structured_guide_memory_hints=True,
            max_memory_records=4,
        )

        compiled = compiler.compile(
            question="What books has Melanie read?",
            question_time=None,
            route=RouteResult("list_count", ("list_or_count",)),
            hits=(RetrievalHit("s1:t0", 1.0, 1, "test"),),
            evidence_turns=(
                Turn(
                    source_id="s1:t0",
                    session_id="s1",
                    turn_index=0,
                    role="user",
                    text="I finished Charlotte's Web last weekend.",
                    timestamp="2024-01-08",
                ),
            ),
            memory_records=(
                MemoryRecord(
                    memory_id="m1",
                    memory_type="event",
                    text="Melanie finished Charlotte's Web.",
                    source_ids=("s1:t0",),
                    value="Charlotte's Web",
                ),
                MemoryRecord(
                    memory_id="m2",
                    memory_type="profile",
                    text="Melanie likes reading.",
                    source_ids=("s1:t0",),
                    value="reading",
                ),
                MemoryRecord(
                    memory_id="m3",
                    memory_type="event",
                    text="Melanie read Nothing is Impossible.",
                    source_ids=("s1:t9",),
                    value="Nothing is Impossible",
                ),
            ),
        )

        self.assertIn("memory_hint=event:Charlotte's Web", compiled.prompt)
        self.assertNotIn("profile:reading", compiled.prompt)
        self.assertNotIn("Nothing is Impossible", compiled.prompt)

    def test_candidate_guide_memory_hints_are_opt_in(self) -> None:
        compiler = EvidenceCompiler(
            max_evidence_items=4,
            max_evidence_chars=4000,
            prompt_mode="external_naive",
            candidate_guide=True,
            max_memory_records=2,
        )

        compiled = compiler.compile(
            question="What books has Melanie read?",
            question_time=None,
            route=RouteResult("list_count", ("list_or_count",)),
            hits=(RetrievalHit("s1:t0", 1.0, 1, "test"),),
            evidence_turns=(
                Turn(
                    source_id="s1:t0",
                    session_id="s1",
                    turn_index=0,
                    role="user",
                    text="I finished Charlotte's Web last weekend.",
                    timestamp="2024-01-08",
                ),
            ),
            memory_records=(
                MemoryRecord(
                    memory_id="m1",
                    memory_type="event",
                    text="Melanie finished Charlotte's Web.",
                    source_ids=("s1:t0",),
                    value="Charlotte's Web",
                ),
            ),
        )

        self.assertIn("Candidate Evidence Map:", compiled.prompt)
        self.assertNotIn("source_memory_hints=", compiled.prompt)

    def test_fixed_set_memory_source_interleave_preserves_budget_set(self) -> None:
        turns = (
            Turn(
                source_id="s1:t0",
                session_id="s1",
                turn_index=0,
                role="user",
                text="I asked about choosing a first instrument.",
            ),
            Turn(
                source_id="s2:t0",
                session_id="s2",
                turn_index=0,
                role="user",
                text="I rented a keyboard for practice.",
            ),
            Turn(
                source_id="s3:t0",
                session_id="s3",
                turn_index=0,
                role="user",
                text="I bought a saxophone for jazz lessons.",
            ),
        )
        hits = (
            RetrievalHit("s1:t0", 1.0, 1, "test"),
            RetrievalHit("s2:t0", 0.9, 2, "test"),
            RetrievalHit("s3:t0", 0.8, 3, "test"),
        )
        memory_records = (
            MemoryRecord(
                memory_id="m1",
                memory_type="fact",
                text="The user bought a saxophone.",
                source_ids=("s3:t0",),
                value="saxophone",
            ),
        )
        route = RouteResult("fact_lookup", ())

        regular = EvidenceCompiler(
            max_evidence_items=2,
            max_evidence_chars=4000,
            evidence_order="memory_source_interleave",
            source_anchor_keep=0,
            source_anchor_memory_rows=1,
            max_memory_records=0,
        ).compile(
            question="Which instrument did I buy?",
            question_time=None,
            route=route,
            hits=hits,
            evidence_turns=turns,
            memory_records=memory_records,
        )
        fixed_set = EvidenceCompiler(
            max_evidence_items=2,
            max_evidence_chars=4000,
            evidence_order="fixed_set_memory_source_interleave",
            source_anchor_keep=0,
            source_anchor_memory_rows=1,
            max_memory_records=0,
        ).compile(
            question="Which instrument did I buy?",
            question_time=None,
            route=route,
            hits=hits,
            evidence_turns=turns,
            memory_records=memory_records,
        )

        self.assertEqual(
            [row.source_id for row in regular.evidence_rows],
            ["s3:t0", "s1:t0"],
        )
        self.assertEqual(
            [row.source_id for row in fixed_set.evidence_rows],
            ["s1:t0", "s2:t0"],
        )

    def test_memory_state_guide_links_managed_state_to_raw_rows(self) -> None:
        compiler = EvidenceCompiler(
            max_evidence_items=4,
            max_evidence_chars=4000,
            prompt_mode="external_naive",
            max_memory_records=4,
            memory_state_guide=True,
            memory_state_guide_information_needs=("current_state",),
        )

        compiled = compiler.compile(
            question="Where does Alex live now?",
            question_time=None,
            route=RouteResult("current_state", ("current_state",)),
            hits=(
                RetrievalHit("s1:t0", 1.0, 1, "test"),
                RetrievalHit("s2:t0", 0.9, 2, "test"),
            ),
            evidence_turns=(
                Turn(
                    source_id="s1:t0",
                    session_id="s1",
                    turn_index=0,
                    role="user",
                    text="I live in Austin.",
                    timestamp="2023-03-01",
                ),
                Turn(
                    source_id="s2:t0",
                    session_id="s2",
                    turn_index=0,
                    role="user",
                    text="I moved to Seattle last month.",
                    timestamp="2024-04-01",
                ),
            ),
            memory_records=(
                MemoryRecord(
                    memory_id="old",
                    memory_type="state",
                    text="Alex lives in Austin.",
                    source_ids=("s1:t0",),
                    subject="Alex",
                    predicate="lives_in",
                    value="Austin",
                    timestamp="2023-03-01",
                    status="superseded",
                    superseded_by="new",
                ),
                MemoryRecord(
                    memory_id="new",
                    memory_type="state",
                    text="Alex lives in Seattle.",
                    source_ids=("s2:t0",),
                    subject="Alex",
                    predicate="lives_in",
                    value="Seattle",
                    timestamp="2024-04-01",
                    status="active",
                ),
            ),
        )

        self.assertIn("Managed Memory State Guide:", compiled.prompt)
        self.assertIn("status=active", compiled.prompt)
        self.assertIn("value=Seattle", compiled.prompt)
        self.assertIn("status=superseded", compiled.prompt)
        self.assertIn("value=Austin", compiled.prompt)
        self.assertIn("sources=Memory 1", compiled.prompt)
        self.assertIn("sources=Memory 2", compiled.prompt)
        self.assertIn("not independent evidence", compiled.prompt)

    def test_memory_state_guide_can_use_build_conflict_manifest(self) -> None:
        compiler = EvidenceCompiler(
            max_evidence_items=4,
            max_evidence_chars=4000,
            prompt_mode="external_naive",
            max_memory_records=4,
            memory_state_guide=True,
            memory_state_guide_information_needs=("current_state",),
            memory_state_guide_require_conflict=True,
            memory_state_guide_conflict_source="build_manifest",
            memory_state_guide_require_active_superseded_pair=True,
            memory_state_guide_require_slot_overlap=True,
            memory_state_guide_require_stateful_slot=True,
        )
        records = (
            MemoryRecord(
                memory_id="old",
                memory_type="state",
                text="Alex lives in Austin.",
                source_ids=("s1:t0",),
                subject="Alex",
                predicate="lives_in",
                value="Austin",
                timestamp="2023-03-01",
                status="superseded",
                superseded_by="new",
            ),
            MemoryRecord(
                memory_id="new",
                memory_type="state",
                text="Alex lives in Seattle.",
                source_ids=("s2:t0",),
                subject="Alex",
                predicate="lives_in",
                value="Seattle",
                timestamp="2024-04-01",
                status="active",
            ),
        )

        compiled = compiler.compile(
            question="Where does Alex live now?",
            question_time=None,
            route=RouteResult("current_state", ("current_state",)),
            hits=(
                RetrievalHit("s1:t0", 1.0, 1, "test"),
                RetrievalHit("s2:t0", 0.9, 2, "test"),
            ),
            evidence_turns=(
                Turn(
                    source_id="s1:t0",
                    session_id="s1",
                    turn_index=0,
                    role="user",
                    text="I live in Austin.",
                    timestamp="2023-03-01",
                ),
                Turn(
                    source_id="s2:t0",
                    session_id="s2",
                    turn_index=0,
                    role="user",
                    text="I moved to Seattle last month.",
                    timestamp="2024-04-01",
                ),
            ),
            memory_records=records,
            memory_state_conflict_manifest={
                "schema_version": "memory_state_conflict_manifest_v1",
                "applied": True,
                "clusters": [
                    {
                        "memory_type": "state",
                        "subject": "alex",
                        "predicate": "lives_in",
                        "source_backed": True,
                    }
                ],
            },
        )

        self.assertIn("Managed Memory State Guide:", compiled.prompt)
        self.assertIn("value=Seattle", compiled.prompt)
        self.assertIn("value=Austin", compiled.prompt)
        self.assertIn("sources=Memory 1", compiled.prompt)
        self.assertIn("sources=Memory 2", compiled.prompt)

    def test_memory_value_slot_guide_uses_visible_manifest_values(self) -> None:
        compiler = EvidenceCompiler(
            max_evidence_items=4,
            max_evidence_chars=4000,
            prompt_mode="external_naive",
            memory_value_slot_guide=True,
            memory_value_slot_guide_information_needs=("current_state",),
            memory_value_slot_guide_max_slots=2,
            memory_value_slot_guide_max_values=4,
        )

        compiled = compiler.compile(
            question="What is Alex's current follower count?",
            question_time=None,
            route=RouteResult("current_state", ("current_state",)),
            hits=(
                RetrievalHit("s1:t0", 1.0, 1, "test"),
                RetrievalHit("s2:t0", 0.9, 2, "test"),
            ),
            evidence_turns=(
                Turn(
                    source_id="s1:t0",
                    session_id="s1",
                    turn_index=0,
                    role="user",
                    text="Alex had 1,200 followers in January.",
                    timestamp="2024-01-01",
                ),
                Turn(
                    source_id="s2:t0",
                    session_id="s2",
                    turn_index=0,
                    role="user",
                    text="Alex now has 1,350 followers.",
                    timestamp="2024-02-01",
                ),
            ),
            memory_scalar_value_manifest={
                "schema_version": "memory_scalar_value_manifest_v1",
                "applied": True,
                "slot_index": [
                    {
                        "memory_type": "state",
                        "managed": True,
                        "subject": "Alex",
                        "predicate": "follower count",
                        "source_backed": True,
                        "operation_hints": [
                            "create_value_object",
                            "supersede_value",
                            "verify_value_source",
                        ],
                        "value_objects": [
                            {
                                "status": "superseded",
                                "value": "1,200 followers",
                                "scalar_values": ["1,200 followers"],
                                "source_ids": ["s1:t0"],
                                "time": "2024-01-01",
                            },
                            {
                                "status": "active",
                                "value": "1,350 followers",
                                "scalar_values": ["1,350 followers"],
                                "source_ids": ["s2:t0"],
                                "time": "2024-02-01",
                            },
                            {
                                "status": "active",
                                "value": "1,500 followers",
                                "scalar_values": ["1,500 followers"],
                                "source_ids": ["s3:t0"],
                                "time": "2024-03-01",
                            },
                        ],
                    },
                    {
                        "memory_type": "state",
                        "managed": True,
                        "subject": "Alex",
                        "predicate": "follower count",
                        "source_backed": True,
                        "value_objects": [
                            {
                                "status": "active",
                                "value": "1,800 followers",
                                "source_ids": ["hidden:t0"],
                                "time": "2024-04-01",
                            }
                        ],
                    },
                ],
            },
        )

        self.assertIn("Memory Value Slot Guide:", compiled.prompt)
        self.assertIn("active_values=1,350 followers", compiled.prompt)
        self.assertIn("superseded_values=1,200 followers", compiled.prompt)
        self.assertIn("sources=Memory 1, Memory 2", compiled.prompt)
        self.assertIn("not independent evidence", compiled.prompt)
        self.assertNotIn("1,500 followers", compiled.prompt)
        self.assertNotIn("1,800 followers", compiled.prompt)
        self.assertNotIn("Memory 3", compiled.prompt)

    def test_memory_value_slot_guide_can_filter_memory_types(self) -> None:
        compiler = EvidenceCompiler(
            max_evidence_items=4,
            max_evidence_chars=4000,
            prompt_mode="external_naive",
            memory_value_slot_guide=True,
            memory_value_slot_guide_information_needs=("current_state",),
            memory_value_slot_guide_memory_types=("state",),
        )

        compiled = compiler.compile(
            question="Where does Alex live now?",
            question_time=None,
            route=RouteResult("current_state", ("current_state",)),
            hits=(
                RetrievalHit("s1:t0", 1.0, 1, "test"),
                RetrievalHit("s2:t0", 0.9, 2, "test"),
            ),
            evidence_turns=(
                Turn(
                    source_id="s1:t0",
                    session_id="s1",
                    turn_index=0,
                    role="user",
                    text="Alex is considering a NAS device.",
                    timestamp="2024-01-01",
                ),
                Turn(
                    source_id="s2:t0",
                    session_id="s2",
                    turn_index=0,
                    role="user",
                    text="Alex now lives in Seattle.",
                    timestamp="2024-02-01",
                ),
            ),
            memory_scalar_value_manifest={
                "schema_version": "memory_scalar_value_manifest_v1",
                "applied": True,
                "slot_index": [
                    {
                        "memory_type": "plan",
                        "subject": "Alex",
                        "predicate": "is considering",
                        "source_backed": True,
                        "value_objects": [
                            {
                                "status": "active",
                                "value": "NAS device",
                                "source_ids": ["s1:t0"],
                                "time": "2024-01-01",
                            }
                        ],
                    },
                    {
                        "memory_type": "state",
                        "subject": "Alex",
                        "predicate": "lives in",
                        "source_backed": True,
                        "value_objects": [
                            {
                                "status": "active",
                                "value": "Seattle",
                                "source_ids": ["s2:t0"],
                                "time": "2024-02-01",
                            }
                        ],
                    },
                ],
            },
        )

        self.assertIn("Memory Value Slot Guide:", compiled.prompt)
        guide_block = compiled.prompt.split("Memory Value Slot Guide:", 1)[1].split(
            "\n\n", 1
        )[0]
        self.assertIn("type=state", guide_block)
        self.assertIn("active_values=Seattle", guide_block)
        self.assertNotIn("type=plan", guide_block)
        self.assertNotIn("NAS device", guide_block)

    def test_memory_value_slot_guide_can_use_memory_object_index(self) -> None:
        compiler = EvidenceCompiler(
            max_evidence_items=4,
            max_evidence_chars=4000,
            prompt_mode="external_naive",
            memory_value_slot_guide=True,
            memory_value_slot_guide_information_needs=("current_state",),
            memory_value_slot_guide_memory_types=("state",),
        )

        compiled = compiler.compile(
            question="Where does Alex live now?",
            question_time=None,
            route=RouteResult("current_state", ("current_state",)),
            hits=(
                RetrievalHit("s1:t0", 1.0, 1, "test"),
                RetrievalHit("s2:t0", 0.9, 2, "test"),
            ),
            evidence_turns=(
                Turn(
                    source_id="s1:t0",
                    session_id="s1",
                    turn_index=0,
                    role="user",
                    text="Alex lived in Austin before.",
                    timestamp="2024-01-01",
                ),
                Turn(
                    source_id="s2:t0",
                    session_id="s2",
                    turn_index=0,
                    role="user",
                    text="Alex now lives in Seattle.",
                    timestamp="2024-02-01",
                ),
            ),
            memory_object_index={
                "schema_version": "memory_object_index_v1",
                "applied": True,
                "value_slot_index": [
                    {
                        "memory_type": "state",
                        "subject": "Alex",
                        "predicate": "lives in",
                        "source_backed": True,
                        "conflict_cluster": True,
                        "operation_hints": [
                            "retrieve",
                            "expand",
                            "verify",
                            "audit",
                        ],
                        "value_objects": [
                            {
                                "status": "superseded",
                                "value": "Austin",
                                "source_ids": ["s1:t0"],
                                "time": "2024-01-01",
                            },
                            {
                                "status": "active",
                                "value": "Seattle",
                                "source_ids": ["s2:t0"],
                                "time": "2024-02-01",
                            },
                        ],
                    }
                ],
            },
        )

        self.assertIn("Memory Value Slot Guide:", compiled.prompt)
        self.assertIn("active_values=Seattle", compiled.prompt)
        self.assertIn("superseded_values=Austin", compiled.prompt)
        self.assertIn("sources=Memory 1, Memory 2", compiled.prompt)
        self.assertIn("not independent evidence", compiled.prompt)

    def test_source_backed_memory_state_ledger_diagnostics_use_visible_sources(
        self,
    ) -> None:
        compiler = EvidenceCompiler(
            max_evidence_items=4,
            max_evidence_chars=4000,
            prompt_mode="external_naive",
            memory_state_guide=True,
            memory_state_guide_information_needs=("current_state",),
            memory_state_guide_candidate_records=8,
        )

        compiled = compiler.compile(
            question="How many engineers does Alex lead now?",
            question_time=None,
            route=RouteResult("current_state", ("current_state",)),
            hits=(
                RetrievalHit("s1:t0", 1.0, 1, "test"),
                RetrievalHit("s2:t0", 0.9, 2, "test"),
            ),
            evidence_turns=(
                Turn(
                    source_id="s1:t0",
                    session_id="s1",
                    turn_index=0,
                    role="user",
                    text="Alex led four engineers in the old role.",
                    timestamp="2024-01-01",
                ),
                Turn(
                    source_id="s2:t0",
                    session_id="s2",
                    turn_index=0,
                    role="user",
                    text="Alex now leads five engineers.",
                    timestamp="2025-01-01",
                ),
            ),
            memory_records=(
                MemoryRecord(
                    memory_id="visible",
                    memory_type="profile",
                    text="Alex leads five engineers.",
                    source_ids=("s2:t0",),
                    subject="Alex",
                    predicate="team_size",
                    value="five engineers",
                    timestamp="2025-01-01",
                    status="active",
                ),
                MemoryRecord(
                    memory_id="hidden",
                    memory_type="profile",
                    text="Alex leads ten engineers.",
                    source_ids=("s9:t0",),
                    subject="Alex",
                    predicate="team_size",
                    value="ten engineers",
                    timestamp="2025-02-01",
                    status="active",
                ),
            ),
        )

        ledger = compiled.diagnostics["source_backed_memory_state_ledger"]
        self.assertTrue(ledger["applied"])
        self.assertEqual(ledger["entry_count"], 1)
        self.assertEqual(ledger["entries"][0]["value"], "five engineers")
        self.assertEqual(ledger["entries"][0]["source_labels"], ("Memory 2",))

    def test_memory_state_guide_skips_unlinked_memory(self) -> None:
        compiler = EvidenceCompiler(
            max_evidence_items=4,
            max_evidence_chars=4000,
            prompt_mode="external_naive",
            max_memory_records=4,
            memory_state_guide=True,
            memory_state_guide_information_needs=("profile_preference",),
        )

        compiled = compiler.compile(
            question="What tea does Alex prefer?",
            question_time=None,
            route=RouteResult("profile_preference", ("preference",)),
            hits=(RetrievalHit("s1:t0", 1.0, 1, "test"),),
            evidence_turns=(
                Turn(
                    source_id="s1:t0",
                    session_id="s1",
                    turn_index=0,
                    role="user",
                    text="We discussed tea generally.",
                    timestamp="2024-01-01",
                ),
            ),
            memory_records=(
                MemoryRecord(
                    memory_id="unlinked",
                    memory_type="preference",
                    text="Alex prefers jasmine tea.",
                    source_ids=("s9:t0",),
                    subject="Alex",
                    predicate="prefers",
                    value="jasmine tea",
                    timestamp="2024-01-02",
                ),
            ),
        )

        self.assertNotIn("Managed Memory State Guide:", compiled.prompt)
        self.assertNotIn("jasmine tea", compiled.prompt)

    def test_memory_state_guide_require_conflict_skips_single_active_state(self) -> None:
        compiler = EvidenceCompiler(
            max_evidence_items=4,
            max_evidence_chars=4000,
            prompt_mode="external_naive",
            max_memory_records=4,
            memory_state_guide=True,
            memory_state_guide_information_needs=("current_state",),
            memory_state_guide_require_conflict=True,
        )

        compiled = compiler.compile(
            question="Where does Alex live now?",
            question_time=None,
            route=RouteResult("current_state", ("current_state",)),
            hits=(RetrievalHit("s2:t0", 0.9, 1, "test"),),
            evidence_turns=(
                Turn(
                    source_id="s2:t0",
                    session_id="s2",
                    turn_index=0,
                    role="user",
                    text="I moved to Seattle last month.",
                    timestamp="2024-04-01",
                ),
            ),
            memory_records=(
                MemoryRecord(
                    memory_id="new",
                    memory_type="state",
                    text="Alex lives in Seattle.",
                    source_ids=("s2:t0",),
                    subject="Alex",
                    predicate="lives_in",
                    value="Seattle",
                    timestamp="2024-04-01",
                    status="active",
                ),
            ),
        )

        self.assertNotIn("Managed Memory State Guide:", compiled.prompt)
        self.assertNotIn("value=Seattle", compiled.prompt)

    def test_memory_state_guide_require_conflict_keeps_source_linked_chain(self) -> None:
        compiler = EvidenceCompiler(
            max_evidence_items=4,
            max_evidence_chars=4000,
            prompt_mode="external_naive",
            max_memory_records=4,
            memory_state_guide=True,
            memory_state_guide_information_needs=("current_state",),
            memory_state_guide_require_conflict=True,
        )

        compiled = compiler.compile(
            question="Where does Alex live now?",
            question_time=None,
            route=RouteResult("current_state", ("current_state",)),
            hits=(
                RetrievalHit("s1:t0", 1.0, 1, "test"),
                RetrievalHit("s2:t0", 0.9, 2, "test"),
            ),
            evidence_turns=(
                Turn(
                    source_id="s1:t0",
                    session_id="s1",
                    turn_index=0,
                    role="user",
                    text="I live in Austin.",
                    timestamp="2023-03-01",
                ),
                Turn(
                    source_id="s2:t0",
                    session_id="s2",
                    turn_index=0,
                    role="user",
                    text="I moved to Seattle last month.",
                    timestamp="2024-04-01",
                ),
            ),
            memory_records=(
                MemoryRecord(
                    memory_id="old",
                    memory_type="state",
                    text="Alex lives in Austin.",
                    source_ids=("s1:t0",),
                    subject="Alex",
                    predicate="lives_in",
                    value="Austin",
                    timestamp="2023-03-01",
                    valid_to="2024-04-01",
                    status="superseded",
                    superseded_by="new",
                ),
                MemoryRecord(
                    memory_id="new",
                    memory_type="state",
                    text="Alex lives in Seattle.",
                    source_ids=("s2:t0",),
                    subject="Alex",
                    predicate="lives_in",
                    value="Seattle",
                    timestamp="2024-04-01",
                    status="active",
                ),
            ),
        )

        self.assertIn("Managed Memory State Guide:", compiled.prompt)
        self.assertIn("value=Austin", compiled.prompt)
        self.assertIn("value=Seattle", compiled.prompt)
        self.assertIn("valid_to=2024-04-01", compiled.prompt)
        self.assertIn("sources=Memory 1", compiled.prompt)
        self.assertIn("sources=Memory 2", compiled.prompt)

    def test_memory_state_guide_can_use_separate_source_records(self) -> None:
        compiler = EvidenceCompiler(
            max_evidence_items=4,
            max_evidence_chars=4000,
            prompt_mode="external_naive",
            max_memory_records=0,
            memory_state_guide=True,
            memory_state_guide_information_needs=("current_state",),
            memory_state_guide_require_conflict=True,
        )

        compiled = compiler.compile(
            question="Where does Alex live now?",
            question_time=None,
            route=RouteResult("current_state", ("current_state",)),
            hits=(
                RetrievalHit("s1:t0", 1.0, 1, "test"),
                RetrievalHit("s2:t0", 0.9, 2, "test"),
            ),
            evidence_turns=(
                Turn(
                    source_id="s1:t0",
                    session_id="s1",
                    turn_index=0,
                    role="user",
                    text="I live in Austin.",
                    timestamp="2023-03-01",
                ),
                Turn(
                    source_id="s2:t0",
                    session_id="s2",
                    turn_index=0,
                    role="user",
                    text="I moved to Seattle last month.",
                    timestamp="2024-04-01",
                ),
            ),
            memory_records=(),
            memory_state_guide_records=(
                MemoryRecord(
                    memory_id="old",
                    memory_type="state",
                    text="Alex lives in Austin.",
                    source_ids=("s1:t0",),
                    subject="Alex",
                    predicate="lives_in",
                    value="Austin",
                    timestamp="2023-03-01",
                    status="superseded",
                    superseded_by="new",
                ),
                MemoryRecord(
                    memory_id="new",
                    memory_type="state",
                    text="Alex lives in Seattle.",
                    source_ids=("s2:t0",),
                    subject="Alex",
                    predicate="lives_in",
                    value="Seattle",
                    timestamp="2024-04-01",
                    status="active",
                ),
            ),
        )

        self.assertEqual(compiled.memory_records, ())
        self.assertIn("Managed Memory State Guide:", compiled.prompt)
        self.assertIn("value=Austin", compiled.prompt)
        self.assertIn("value=Seattle", compiled.prompt)

    def test_memory_state_guide_slot_overlap_splits_predicate_underscores(self) -> None:
        compiler = EvidenceCompiler(
            max_evidence_items=4,
            max_evidence_chars=4000,
            prompt_mode="external_naive",
            max_memory_records=0,
            memory_state_guide=True,
            memory_state_guide_information_needs=("current_state",),
            memory_state_guide_require_conflict=True,
            memory_state_guide_require_active_superseded_pair=True,
            memory_state_guide_require_slot_overlap=True,
            memory_state_guide_require_stateful_slot=True,
        )

        compiled = compiler.compile(
            question="What was my previous frequent flyer status?",
            question_time=None,
            route=RouteResult("current_state", ("recent_or_current",)),
            hits=(
                RetrievalHit("s1:t0", 1.0, 1, "test"),
                RetrievalHit("s2:t0", 0.9, 2, "test"),
            ),
            evidence_turns=(
                Turn(
                    source_id="s1:t0",
                    session_id="s1",
                    turn_index=0,
                    role="user",
                    text="I became eligible for Premier Silver status.",
                    timestamp="2022-09-16",
                ),
                Turn(
                    source_id="s2:t0",
                    session_id="s2",
                    turn_index=0,
                    role="user",
                    text="I just reached Premier Gold status.",
                    timestamp="2023-05-30",
                ),
            ),
            memory_records=(),
            memory_state_guide_records=(
                MemoryRecord(
                    memory_id="old",
                    memory_type="profile",
                    text="User had Premier Silver frequent flyer status.",
                    source_ids=("s1:t0",),
                    subject="User",
                    predicate="has_status",
                    value="Premier Silver",
                    timestamp="2022-09-16",
                    valid_to="2023-05-30",
                    status="superseded",
                    superseded_by="new",
                ),
                MemoryRecord(
                    memory_id="new",
                    memory_type="profile",
                    text="User has Premier Gold frequent flyer status.",
                    source_ids=("s2:t0",),
                    subject="User",
                    predicate="has_status",
                    value="Premier Gold",
                    timestamp="2023-05-30",
                    status="active",
                ),
            ),
        )

        self.assertIn("Managed Memory State Guide:", compiled.prompt)
        self.assertIn("predicate=has_status", compiled.prompt)
        self.assertIn("value=Premier Silver", compiled.prompt)
        self.assertIn("value=Premier Gold", compiled.prompt)

    def test_memory_state_guide_pair_gate_skips_superseded_only_slot(self) -> None:
        compiler = EvidenceCompiler(
            max_evidence_items=4,
            max_evidence_chars=4000,
            prompt_mode="external_naive",
            max_memory_records=0,
            memory_state_guide=True,
            memory_state_guide_information_needs=("current_state",),
            memory_state_guide_require_conflict=True,
            memory_state_guide_require_active_superseded_pair=True,
            memory_state_guide_require_slot_overlap=True,
            memory_state_guide_require_stateful_slot=True,
        )

        compiled = compiler.compile(
            question="What was my previous frequent flyer status?",
            question_time=None,
            route=RouteResult("current_state", ("recent_or_current",)),
            hits=(RetrievalHit("s1:t0", 1.0, 1, "test"),),
            evidence_turns=(
                Turn(
                    source_id="s1:t0",
                    session_id="s1",
                    turn_index=0,
                    role="user",
                    text="I became eligible for Premier Silver status.",
                    timestamp="2022-09-16",
                ),
            ),
            memory_records=(),
            memory_state_guide_records=(
                MemoryRecord(
                    memory_id="old",
                    memory_type="profile",
                    text="User had Premier Silver frequent flyer status.",
                    source_ids=("s1:t0",),
                    subject="User",
                    predicate="has_status",
                    value="Premier Silver",
                    timestamp="2022-09-16",
                    valid_to="2023-05-30",
                    status="superseded",
                    superseded_by="new",
                ),
            ),
        )

        self.assertNotIn("Managed Memory State Guide:", compiled.prompt)

    def test_memory_state_guide_stateful_slot_gate_skips_text_only_overlap(self) -> None:
        compiler = EvidenceCompiler(
            max_evidence_items=4,
            max_evidence_chars=4000,
            prompt_mode="external_naive",
            max_memory_records=0,
            memory_state_guide=True,
            memory_state_guide_information_needs=("current_state",),
            memory_state_guide_require_conflict=True,
            memory_state_guide_require_slot_overlap=True,
            memory_state_guide_require_stateful_slot=True,
        )

        compiled = compiler.compile(
            question="How long have I been living in my current apartment?",
            question_time=None,
            route=RouteResult("current_state", ("recent_or_current",)),
            hits=(RetrievalHit("s1:t0", 1.0, 1, "test"),),
            evidence_turns=(
                Turn(
                    source_id="s1:t0",
                    session_id="s1",
                    turn_index=0,
                    role="user",
                    text="I keep low-maintenance plants in the living room.",
                    timestamp="2023-10-15",
                ),
            ),
            memory_records=(),
            memory_state_guide_records=(
                MemoryRecord(
                    memory_id="plants",
                    memory_type="preference",
                    text="User prefers low-maintenance plants in the living room.",
                    source_ids=("s1:t0",),
                    subject="User",
                    predicate="prefers",
                    value="low-maintenance plants",
                    timestamp="2023-10-15",
                    valid_to="2023-10-16",
                    status="superseded",
                    superseded_by="new-plants",
                ),
            ),
        )

        self.assertNotIn("Managed Memory State Guide:", compiled.prompt)

    def test_memory_version_chain_interleave_groups_active_and_superseded_source_rows(self) -> None:
        compiler = EvidenceCompiler(
            max_evidence_items=5,
            max_evidence_chars=8000,
            prompt_mode="external_naive",
            max_memory_records=0,
            route_overrides={
                "current_state": {
                    "evidence_order": "memory_version_chain_interleave",
                    "source_anchor_keep": 1,
                    "source_anchor_memory_rows": 3,
                }
            },
        )

        turns_by_id = {
            "s1:t0": Turn(
                source_id="s1:t0",
                session_id="s1",
                turn_index=0,
                role="user",
                text="We talked about unrelated moving logistics.",
                timestamp="2024-01-01",
            ),
            "s1:t1": Turn(
                source_id="s1:t1",
                session_id="s1",
                turn_index=1,
                role="user",
                text="I live in Austin.",
                timestamp="2024-01-02",
            ),
            "s1:t2": Turn(
                source_id="s1:t2",
                session_id="s1",
                turn_index=2,
                role="user",
                text="The weather was rainy.",
                timestamp="2024-01-03",
            ),
            "s1:t3": Turn(
                source_id="s1:t3",
                session_id="s1",
                turn_index=3,
                role="user",
                text="I moved to Seattle last month.",
                timestamp="2024-04-01",
            ),
            "s1:t4": Turn(
                source_id="s1:t4",
                session_id="s1",
                turn_index=4,
                role="assistant",
                text="General advice about moving.",
                timestamp="2024-04-02",
            ),
        }
        evidence_order = ("s1:t0", "s1:t2", "s1:t4", "s1:t1", "s1:t3")

        compiled = compiler.compile(
            question="Where does Alex live now?",
            question_time=None,
            route=RouteResult("current_state", ("current_state",)),
            hits=tuple(
                RetrievalHit(source_id, 1.0 / (rank + 1), rank + 1, "test")
                for rank, source_id in enumerate(evidence_order)
            ),
            evidence_turns=tuple(turns_by_id[source_id] for source_id in evidence_order),
            memory_records=(
                MemoryRecord(
                    memory_id="old",
                    memory_type="state",
                    text="Alex lives in Austin.",
                    source_ids=("s1:t1",),
                    subject="Alex",
                    predicate="lives_in",
                    value="Austin",
                    timestamp="2024-01-02",
                    status="superseded",
                    superseded_by="new",
                ),
                MemoryRecord(
                    memory_id="new",
                    memory_type="state",
                    text="Alex lives in Seattle.",
                    source_ids=("s1:t3",),
                    subject="Alex",
                    predicate="lives_in",
                    value="Seattle",
                    timestamp="2024-04-01",
                    status="active",
                ),
            ),
        )

        self.assertEqual(
            [row.source_id for row in compiled.evidence_rows],
            ["s1:t0", "s1:t3", "s1:t1", "s1:t2", "s1:t4"],
        )
        self.assertNotIn("Managed Memory State Guide:", compiled.prompt)
        self.assertNotIn("value=Seattle", compiled.prompt)
        self.assertIn("I moved to Seattle last month.", compiled.prompt)
        self.assertIn("I live in Austin.", compiled.prompt)

    def test_candidate_guide_includes_only_source_linked_memory_hints(self) -> None:
        compiler = EvidenceCompiler(
            max_evidence_items=4,
            max_evidence_chars=4000,
            prompt_mode="external_naive",
            candidate_guide=True,
            candidate_guide_include_memory_hints=True,
            candidate_guide_max_memory_hints=1,
            max_memory_records=4,
        )

        compiled = compiler.compile(
            question="What books has Melanie read?",
            question_time=None,
            route=RouteResult("list_count", ("list_or_count",)),
            hits=(RetrievalHit("s1:t0", 1.0, 1, "test"),),
            evidence_turns=(
                Turn(
                    source_id="s1:t0",
                    session_id="s1",
                    turn_index=0,
                    role="user",
                    text="I finished Charlotte's Web last weekend.",
                    timestamp="2024-01-08",
                ),
            ),
            memory_records=(
                MemoryRecord(
                    memory_id="m1",
                    memory_type="event",
                    text="Melanie finished Charlotte's Web.",
                    source_ids=("s1:t0",),
                    value="Charlotte's Web",
                ),
                MemoryRecord(
                    memory_id="m2",
                    memory_type="event",
                    text="Melanie read Nothing is Impossible.",
                    source_ids=("s1:t9",),
                    value="Nothing is Impossible",
                ),
            ),
        )

        self.assertIn("source_memory_hints=event", compiled.prompt)
        self.assertIn("Charlotte's Web", compiled.prompt)
        self.assertNotIn("Nothing is Impossible", compiled.prompt)

    def test_event_time_candidate_manifest_blocks_low_precision_order(self) -> None:
        turns = (
            Turn(
                source_id="s1:t0",
                session_id="s1",
                turn_index=0,
                role="user",
                text="I visited the Science Museum today.",
                timestamp="2023-01-15",
            ),
            Turn(
                source_id="s1:t1",
                session_id="s1",
                turn_index=1,
                role="user",
                text="I recently attended a lecture at the Museum of Contemporary Art.",
                timestamp="2023-01-15",
            ),
        )
        baseline = EvidenceCompiler(
            max_evidence_items=2,
            max_evidence_chars=4000,
            prompt_mode="external_naive",
        ).compile(
            question="What is the chronological order of the museums I visited?",
            question_time=None,
            route=RouteResult("current_state", ()),
            hits=(),
            evidence_turns=turns,
        )
        compiled = EvidenceCompiler(
            max_evidence_items=2,
            max_evidence_chars=4000,
            prompt_mode="external_naive",
            event_time_candidate_manifest=True,
            event_time_candidate_manifest_information_needs=("current_state",),
        ).compile(
            question="What is the chronological order of the museums I visited?",
            question_time=None,
            route=RouteResult("current_state", ()),
            hits=(),
            evidence_turns=turns,
        )

        self.assertEqual(compiled.prompt, baseline.prompt)
        self.assertNotIn("event_time_candidate_manifest", compiled.prompt)
        manifest = compiled.to_dict()["diagnostics"]["event_time_candidate_manifest"]
        self.assertTrue(manifest["applied"])
        self.assertFalse(manifest["safe_order_available"])
        self.assertEqual(
            manifest["safe_order_blocked_reason"],
            "low_precision_event_time_present",
        )
        self.assertEqual(len(manifest["items"]), 2)
        time_kinds = {item["time_kind"] for item in manifest["items"]}
        self.assertIn("vague_relative_recent", time_kinds)
        self.assertNotIn("gold answer", manifest["clean_note"])
        self.assertNotIn("judge output", manifest["clean_note"])

    def test_event_time_candidate_manifest_safe_order_needs_precise_slots(
        self,
    ) -> None:
        turns = (
            Turn(
                source_id="s1:t0",
                session_id="s1",
                turn_index=0,
                role="user",
                text="I visited the Science Museum on January 15.",
                timestamp="2023-01-20",
            ),
            Turn(
                source_id="s2:t0",
                session_id="s2",
                turn_index=0,
                role="user",
                text="I toured the Metropolitan Museum on February 10.",
                timestamp="2023-02-12",
            ),
        )

        compiled = EvidenceCompiler(
            max_evidence_items=2,
            max_evidence_chars=4000,
            prompt_mode="external_naive",
            event_time_candidate_manifest=True,
            event_time_candidate_manifest_information_needs=("temporal_lookup",),
        ).compile(
            question="When did I visit the Science Museum?",
            question_time=None,
            route=RouteResult("temporal_lookup", ("temporal",)),
            hits=(),
            evidence_turns=turns,
        )

        manifest = compiled.to_dict()["diagnostics"]["event_time_candidate_manifest"]
        self.assertTrue(manifest["applied"])
        self.assertTrue(manifest["safe_order_available"])
        self.assertEqual(manifest["safe_order_source_ids"], ["s1:t0", "s2:t0"])
        self.assertEqual(manifest["conflict_groups"], [])
        self.assertNotIn("Source Event Timeline:", compiled.prompt)

    def test_event_time_candidate_manifest_grouped_view_is_trace_only(self) -> None:
        turns = (
            Turn(
                source_id="s1:t0",
                session_id="s1",
                turn_index=0,
                role="user",
                text="I visited the Science Museum on January 15.",
                timestamp="2023-01-20",
            ),
            Turn(
                source_id="s2:t0",
                session_id="s2",
                turn_index=0,
                role="user",
                text="I visited the Science Museum on February 10.",
                timestamp="2023-02-12",
            ),
            Turn(
                source_id="s3:t0",
                session_id="s3",
                turn_index=0,
                role="user",
                text="I toured the Metropolitan Museum on March 3.",
                timestamp="2023-03-04",
            ),
        )
        baseline = EvidenceCompiler(
            max_evidence_items=3,
            max_evidence_chars=4000,
            prompt_mode="external_naive",
            event_time_candidate_manifest=True,
            event_time_candidate_manifest_information_needs=("temporal_lookup",),
        ).compile(
            question="When did I visit the Science Museum?",
            question_time=None,
            route=RouteResult("temporal_lookup", ("temporal",)),
            hits=(),
            evidence_turns=turns,
        )
        compiled = EvidenceCompiler(
            max_evidence_items=3,
            max_evidence_chars=4000,
            prompt_mode="external_naive",
            event_time_candidate_manifest=True,
            event_time_candidate_manifest_information_needs=("temporal_lookup",),
            event_time_candidate_manifest_grouped_view=True,
        ).compile(
            question="When did I visit the Science Museum?",
            question_time=None,
            route=RouteResult("temporal_lookup", ("temporal",)),
            hits=(),
            evidence_turns=turns,
        )

        self.assertEqual(compiled.prompt, baseline.prompt)
        self.assertNotIn("candidate_groups", compiled.prompt)
        manifest = compiled.to_dict()["diagnostics"]["event_time_candidate_manifest"]
        groups = manifest["candidate_groups"]
        self.assertTrue(manifest["grouped_view"])
        self.assertGreaterEqual(len(groups), 2)
        science_group = next(
            group for group in groups if "science" in group["dedup_key"]
        )
        self.assertEqual(science_group["conflict_type"], "event_time_conflict")
        self.assertEqual(science_group["candidate_count"], 2)
        self.assertIn("s1:t0", science_group["source_ids"])
        self.assertIn("s2:t0", science_group["source_ids"])
        self.assertIn(science_group["best_source_id"], {"s1:t0", "s2:t0"})

    def test_event_time_candidate_map_includes_only_clear_target_event_time(
        self,
    ) -> None:
        turns = (
            Turn(
                source_id="s1:t0",
                session_id="s1",
                turn_index=0,
                role="user",
                text="The sunrise mural happened on May 8.",
                timestamp="2023-05-09",
            ),
            Turn(
                source_id="s2:t0",
                session_id="s2",
                turn_index=0,
                role="user",
                text="The blue mural happened on June 2.",
                timestamp="2023-06-03",
            ),
        )

        compiled = EvidenceCompiler(
            max_evidence_items=2,
            max_evidence_chars=4000,
            prompt_mode="external_naive",
            event_time_candidate_map=True,
        ).compile(
            question="When did the sunrise mural happen?",
            question_time=None,
            route=RouteResult("temporal_lookup", ("temporal",)),
            hits=(),
            evidence_turns=turns,
        )

        self.assertIn("Event-Time Candidate Map:", compiled.prompt)
        self.assertIn("Memory 1: event_time=2023-05-08", compiled.prompt)
        self.assertNotIn("mention_time=2023-05-09", compiled.prompt)
        self.assertIn("event_time=2023-05-08", compiled.prompt)
        self.assertIn("matched_terms=mural, sunrise", compiled.prompt)
        self.assertIn("not independent evidence", compiled.prompt)
        self.assertNotIn("event_time=2023-06-02", compiled.prompt)

    def test_event_time_candidate_map_blocks_duration_questions(self) -> None:
        turns = (
            Turn(
                source_id="s1:t0",
                session_id="s1",
                turn_index=0,
                role="user",
                text="The sunrise mural happened on May 8.",
                timestamp="2023-05-09",
            ),
            Turn(
                source_id="s2:t0",
                session_id="s2",
                turn_index=0,
                role="user",
                text="The pottery class happened on June 2.",
                timestamp="2023-06-03",
            ),
        )

        compiled = EvidenceCompiler(
            max_evidence_items=2,
            max_evidence_chars=4000,
            prompt_mode="external_naive",
            event_time_candidate_map=True,
        ).compile(
            question="How long after the sunrise mural did the pottery class happen?",
            question_time=None,
            route=RouteResult("temporal_lookup", ("temporal",)),
            hits=(),
            evidence_turns=turns,
        )

        self.assertNotIn("Event-Time Candidate Map:", compiled.prompt)

    def test_event_time_candidate_map_blocks_ambiguous_top_times(self) -> None:
        turns = (
            Turn(
                source_id="s1:t0",
                session_id="s1",
                turn_index=0,
                role="user",
                text="The sunrise mural happened on May 8.",
                timestamp="2023-05-09",
            ),
            Turn(
                source_id="s2:t0",
                session_id="s2",
                turn_index=0,
                role="user",
                text="The pottery class happened on June 2.",
                timestamp="2023-06-03",
            ),
        )

        compiled = EvidenceCompiler(
            max_evidence_items=2,
            max_evidence_chars=4000,
            prompt_mode="external_naive",
            event_time_candidate_map=True,
            event_time_candidate_map_min_coverage=0.5,
        ).compile(
            question="When did the sunrise mural or pottery class happen?",
            question_time=None,
            route=RouteResult("temporal_lookup", ("temporal",)),
            hits=(),
            evidence_turns=turns,
        )

        self.assertNotIn("Event-Time Candidate Map:", compiled.prompt)

    def test_event_time_candidate_map_can_ignore_selected_context_timestamps(
        self,
    ) -> None:
        wrapped_text = (
            "Local dialogue context from the same session:\n"
            "- nearby turn (4:04 pm on 20 January, 2023) | Gina: "
            "Are they yours at the festival?\n"
            "- selected turn (4:04 pm on 20 January, 2023) | Jon: "
            "They are performing at the festival next month.\n"
        )

        compiled = EvidenceCompiler(
            max_evidence_items=1,
            max_evidence_chars=4000,
            prompt_mode="external_naive",
            event_time_candidate_map=True,
            event_time_candidate_map_allowed_time_kinds=("exact_today", "explicit_date"),
            event_time_candidate_map_strip_context_wrappers=True,
        ).compile(
            question="When is Jon's group performing at a festival?",
            question_time=None,
            route=RouteResult("temporal_lookup", ("temporal",)),
            hits=(),
            evidence_turns=(
                Turn(
                    source_id="s1:t0",
                    session_id="s1",
                    turn_index=0,
                    role="user",
                    text=wrapped_text,
                    timestamp="2023-01-20",
                ),
            ),
        )

        self.assertNotIn("Event-Time Candidate Map:", compiled.prompt)
        self.assertNotIn("event_time=2023-01-20", compiled.prompt)

    def test_event_time_candidate_map_can_ignore_compact_selected_context_timestamps(
        self,
    ) -> None:
        wrapped_text = (
            "Same-session context:\n"
            "- near (4:04 pm on 20 January, 2023) | Gina: "
            "Are they yours at the festival?\n"
            "- center (4:04 pm on 20 January, 2023) | Jon: "
            "They are performing at the festival next month.\n"
        )

        compiled = EvidenceCompiler(
            max_evidence_items=1,
            max_evidence_chars=4000,
            prompt_mode="external_naive",
            event_time_candidate_map=True,
            event_time_candidate_map_allowed_time_kinds=("exact_today", "explicit_date"),
            event_time_candidate_map_strip_context_wrappers=True,
        ).compile(
            question="When is Jon's group performing at a festival?",
            question_time=None,
            route=RouteResult("temporal_lookup", ("temporal",)),
            hits=(),
            evidence_turns=(
                Turn(
                    source_id="s1:t0",
                    session_id="s1",
                    turn_index=0,
                    role="user",
                    text=wrapped_text,
                    timestamp="2023-01-20",
                ),
            ),
        )

        self.assertNotIn("Event-Time Candidate Map:", compiled.prompt)
        self.assertNotIn("event_time=2023-01-20", compiled.prompt)

    def test_event_time_candidate_map_can_block_time_of_day_questions(self) -> None:
        turns = (
            Turn(
                source_id="s1:t0",
                session_id="s1",
                turn_index=0,
                role="user",
                text="I usually go to the gym at 6:00 pm.",
                timestamp="2023-05-30",
            ),
        )

        compiled = EvidenceCompiler(
            max_evidence_items=1,
            max_evidence_chars=4000,
            prompt_mode="external_naive",
            event_time_candidate_map=True,
            event_time_candidate_map_allow_time_of_day_questions=False,
        ).compile(
            question="What time do I usually go to the gym?",
            question_time=None,
            route=RouteResult("temporal_lookup", ("temporal",)),
            hits=(),
            evidence_turns=turns,
        )

        self.assertNotIn("Event-Time Candidate Map:", compiled.prompt)

    def test_event_time_candidate_map_segment_local_blocks_nearby_today(
        self,
    ) -> None:
        wrapped_text = (
            "Local dialogue context from the same session:\n"
            "- selected turn (12:48 am on 1 February, 2023) | Jon: "
            "I am still searching for a place to open my dance studio.\n"
            "- nearby turn (12:48 am on 1 February, 2023) | Gina: "
            "A wholesaler replied yes today.\n"
        )

        compiled = EvidenceCompiler(
            max_evidence_items=1,
            max_evidence_chars=4000,
            prompt_mode="external_naive",
            event_time_candidate_map=True,
            event_time_candidate_map_allowed_time_kinds=("exact_today",),
            event_time_candidate_map_strip_context_wrappers=True,
            event_time_candidate_map_segment_local_context=True,
            event_time_candidate_map_rank_by_coverage=True,
            event_time_candidate_map_normalize_terms=True,
        ).compile(
            question="When is Jon planning to open his dance studio?",
            question_time=None,
            route=RouteResult("temporal_lookup", ("temporal",)),
            hits=(),
            evidence_turns=(
                Turn(
                    source_id="s1:t0",
                    session_id="s1",
                    turn_index=0,
                    role="Jon",
                    text=wrapped_text,
                    timestamp="2023-02-01",
                ),
            ),
        )

        self.assertNotIn("Event-Time Candidate Map:", compiled.prompt)
        self.assertNotIn("event_time=2023-02-01", compiled.prompt)

    def test_event_time_candidate_map_rank_by_coverage_prefers_specific_slot(
        self,
    ) -> None:
        turns = (
            Turn(
                source_id="s1:t0",
                session_id="s1",
                turn_index=0,
                role="Nate",
                text=(
                    "Nate said today that pets are great companions and that "
                    "chilling with pets is relaxing."
                ),
                timestamp="2022-03-18",
            ),
            Turn(
                source_id="s2:t0",
                session_id="s2",
                turn_index=0,
                role="Nate",
                text=(
                    "Nate will take time off to chill with his pets on "
                    "August 22, 2022."
                ),
                timestamp="2022-08-20",
            ),
        )

        compiled = EvidenceCompiler(
            max_evidence_items=2,
            max_evidence_chars=4000,
            prompt_mode="external_naive",
            event_time_candidate_map=True,
            event_time_candidate_map_allowed_time_kinds=(
                "exact_today",
                "explicit_date",
            ),
            event_time_candidate_map_rank_by_coverage=True,
            event_time_candidate_map_normalize_terms=True,
            event_time_candidate_map_exact_today_min_coverage=0.85,
        ).compile(
            question="When did Nate take time off to chill with pets?",
            question_time=None,
            route=RouteResult("temporal_lookup", ("temporal",)),
            hits=(),
            evidence_turns=turns,
        )

        self.assertIn("Event-Time Candidate Map:", compiled.prompt)
        self.assertIn("Memory 2: event_time=2022-08-22", compiled.prompt)
        self.assertNotIn("mention_time=2022-08-20", compiled.prompt)
        self.assertIn("event_time=2022-08-22", compiled.prompt)
        self.assertIn("matched_terms=chill, nate, off", compiled.prompt)
        self.assertIn("pets", compiled.prompt)
        self.assertIn("take", compiled.prompt)
        self.assertNotIn("event_time=2022-03-18", compiled.prompt)

    def test_event_time_candidate_map_can_require_role_match(self) -> None:
        turns = (
            Turn(
                source_id="s1:t0",
                session_id="s1",
                turn_index=0,
                role="James",
                text=(
                    "Hey John, yesterday I spent time with my family and dogs "
                    "during a road trip."
                ),
                timestamp="2022-11-05",
            ),
            Turn(
                source_id="s2:t0",
                session_id="s2",
                turn_index=0,
                role="John",
                text=(
                    "It is great that you spent time with family and dogs. "
                    "I should spend more time with my sister someday."
                ),
                timestamp="2022-11-06",
            ),
        )

        compiled = EvidenceCompiler(
            max_evidence_items=2,
            max_evidence_chars=4000,
            prompt_mode="external_naive",
            event_time_candidate_map=True,
            event_time_candidate_map_allowed_time_kinds=("relative_phrase",),
            event_time_candidate_map_rank_by_coverage=True,
            event_time_candidate_map_normalize_terms=True,
            event_time_candidate_map_require_role_match=True,
        ).compile(
            question="When did John spend time with his sister and dogs?",
            question_time=None,
            route=RouteResult("temporal_lookup", ("temporal",)),
            hits=(),
            evidence_turns=turns,
        )

        self.assertNotIn("Event-Time Candidate Map:", compiled.prompt)
        self.assertNotIn("event_time=2022-11-04", compiled.prompt)

    def test_event_time_candidate_map_resolves_this_weekend(self) -> None:
        wrapped_text = (
            "Local dialogue context from the same session:\n"
            "- selected turn (10:57 am on 22 August, 2022) | Nate: "
            "I'm taking some time off this weekend to chill with my pets.\n"
            "- nearby turn (10:57 am on 22 August, 2022) | Joanna: "
            "I'm relaxing and recharging this weekend with a long walk.\n"
        )

        compiled = EvidenceCompiler(
            max_evidence_items=1,
            max_evidence_chars=4000,
            prompt_mode="external_naive",
            event_time_candidate_map=True,
            event_time_candidate_map_allowed_time_kinds=("relative_phrase",),
            event_time_candidate_map_strip_context_wrappers=True,
            event_time_candidate_map_segment_local_context=True,
            event_time_candidate_map_rank_by_coverage=True,
            event_time_candidate_map_normalize_terms=True,
            event_time_candidate_map_require_role_match=True,
            event_time_candidate_map_include_mention_time=True,
            enable_weekend_relative_time=True,
        ).compile(
            question="When did Nate take time off to chill with his pets?",
            question_time=None,
            route=RouteResult("temporal_lookup", ("temporal",)),
            hits=(),
            evidence_turns=(
                Turn(
                    source_id="s1:t0",
                    session_id="s1",
                    turn_index=0,
                    role="Nate",
                    text=wrapped_text,
                    timestamp="2022-08-22",
                ),
            ),
        )

        self.assertIn("Event-Time Candidate Map:", compiled.prompt)
        self.assertIn("mention_time=2022-08-22", compiled.prompt)
        self.assertIn("event_time=2022-08-27 to 2022-08-28", compiled.prompt)
        self.assertIn('relative_phrase: phrase="this weekend"', compiled.prompt)
        self.assertNotIn("planned, intended, scheduled", compiled.prompt)

    def test_event_time_candidate_map_skips_weekend_by_default(self) -> None:
        wrapped_text = (
            "Local dialogue context from the same session:\n"
            "- selected turn (10:57 am on 22 August, 2022) | Nate: "
            "I'm taking some time off this weekend to chill with my pets.\n"
            "- nearby turn (10:57 am on 22 August, 2022) | Joanna: "
            "I'm relaxing and recharging this weekend with a long walk.\n"
        )

        compiled = EvidenceCompiler(
            max_evidence_items=1,
            max_evidence_chars=4000,
            prompt_mode="external_naive",
            event_time_candidate_map=True,
            event_time_candidate_map_allowed_time_kinds=("relative_phrase",),
            event_time_candidate_map_strip_context_wrappers=True,
            event_time_candidate_map_segment_local_context=True,
            event_time_candidate_map_rank_by_coverage=True,
            event_time_candidate_map_normalize_terms=True,
            event_time_candidate_map_require_role_match=True,
        ).compile(
            question="When did Nate take time off to chill with his pets?",
            question_time=None,
            route=RouteResult("temporal_lookup", ("temporal",)),
            hits=(),
            evidence_turns=(
                Turn(
                    source_id="s1:t0",
                    session_id="s1",
                    turn_index=0,
                    role="Nate",
                    text=wrapped_text,
                    timestamp="2022-08-22",
                ),
            ),
        )

        self.assertNotIn("Event-Time Candidate Map:", compiled.prompt)
        self.assertNotIn("event_time=2022-08-27 to 2022-08-28", compiled.prompt)
        self.assertNotIn('relative_phrase: phrase="this weekend"', compiled.prompt)

    def test_event_time_candidate_map_audit_is_trace_only(self) -> None:
        compiled = EvidenceCompiler(
            max_evidence_items=1,
            max_evidence_chars=4000,
            prompt_mode="external_naive",
            event_time_candidate_map=False,
            event_time_candidate_map_audit=True,
            event_time_candidate_map_allowed_time_kinds=("exact_today",),
            event_time_candidate_map_strip_context_wrappers=True,
        ).compile(
            question="When did Nate chill with his pets?",
            question_time=None,
            route=RouteResult("temporal_lookup", ("temporal",)),
            hits=(),
            evidence_turns=(
                Turn(
                    source_id="s1:t0",
                    session_id="s1",
                    turn_index=0,
                    role="Nate",
                    text="Today I decided to chill with my pets.",
                    timestamp="2022-03-18",
                ),
            ),
        )

        self.assertNotIn("Event-Time Candidate Map:", compiled.prompt)
        audit = compiled.diagnostics["event_time_candidate_map_audit"]
        self.assertTrue(audit["applied"])
        self.assertEqual(audit["prompt_eligible_count"], 1)
        self.assertIn("exact_today_prompt_candidate", audit["risk_flags"])

    def test_event_time_candidate_map_adds_narrow_mention_time_fallback(
        self,
    ) -> None:
        turns = (
            Turn(
                source_id="s1:t0",
                session_id="s1",
                turn_index=0,
                role="Nate",
                text="Nate says pets bring joy, and today he will chill with pets.",
                timestamp="2022-03-18",
            ),
            Turn(
                source_id="s2:t0",
                session_id="s2",
                turn_index=0,
                role="Nate",
                text=(
                    "Nate is taking time off to chill with his pets and recharge."
                ),
                timestamp="2022-08-22",
            ),
        )

        compiled = EvidenceCompiler(
            max_evidence_items=2,
            max_evidence_chars=4000,
            prompt_mode="external_naive",
            event_time_candidate_map=True,
            event_time_candidate_map_allowed_time_kinds=("exact_today",),
            event_time_candidate_map_min_coverage=0.6,
            event_time_candidate_map_mention_time_fallback=True,
            event_time_candidate_map_mention_time_fallback_min_coverage=0.8,
            event_time_candidate_map_mention_time_fallback_trigger_max_coverage=0.8,
        ).compile(
            question="When did Nate take time off to chill with his pets?",
            question_time=None,
            route=RouteResult("temporal_lookup", ("temporal",)),
            hits=(),
            evidence_turns=turns,
        )

        self.assertIn("Event-Time Candidate Map:", compiled.prompt)
        self.assertIn("time_kind=exact_today", compiled.prompt)
        self.assertIn("time_kind=mention_time_fallback", compiled.prompt)
        self.assertIn("event_time=2022-08-22", compiled.prompt)

    def test_event_time_candidate_map_can_add_temporal_ambiguity_contract(
        self,
    ) -> None:
        turns = (
            Turn(
                source_id="s1:t0",
                session_id="s1",
                turn_index=0,
                role="Nate",
                text="I'm taking some time off this weekend to chill with my pets.",
                timestamp="2022-08-22",
            ),
        )

        compiled = EvidenceCompiler(
            max_evidence_items=1,
            max_evidence_chars=4000,
            prompt_mode="external_naive",
            event_time_candidate_map=True,
            event_time_candidate_map_allowed_time_kinds=("relative_phrase",),
            event_time_candidate_map_rank_by_coverage=True,
            event_time_candidate_map_normalize_terms=True,
            event_time_candidate_map_require_role_match=True,
            event_time_candidate_map_temporal_ambiguity_contract=True,
            event_time_candidate_map_include_mention_time=True,
            enable_weekend_relative_time=True,
        ).compile(
            question="When did Nate take time off to chill with his pets?",
            question_time=None,
            route=RouteResult("temporal_lookup", ("temporal",)),
            hits=(),
            evidence_turns=turns,
        )

        self.assertIn("Event-Time Candidate Map:", compiled.prompt)
        self.assertIn("mention_time=2022-08-22", compiled.prompt)
        self.assertIn("event_time=2022-08-27 to 2022-08-28", compiled.prompt)
        self.assertIn("planned, intended, scheduled", compiled.prompt)
        self.assertIn("include both mention_time and planned event_time", compiled.prompt)

    def test_memory_tail_filter_preserves_retrieval_order(self) -> None:
        compiler = EvidenceCompiler(
            max_evidence_items=10,
            max_evidence_chars=8000,
            prompt_mode="external_naive",
            route_overrides={
                "fact_lookup": {
                    "evidence_order": "memory_tail_filter_preserve_order",
                    "source_anchor_keep": 2,
                    "source_anchor_memory_rows": 1,
                    "source_anchor_per_session": 1,
                }
            },
        )

        turns = tuple(
            Turn(
                source_id=f"s1:t{index}",
                session_id="s1",
                turn_index=index,
                role="user",
                text=text,
                timestamp="2024-01-08",
            )
            for index, text in enumerate(
                (
                    "I talked about unrelated setup.",
                    "I mentioned a possible store.",
                    "The weather was rainy.",
                    "We discussed dinner.",
                    "The coupon was redeemed at Target.",
                )
            )
        )

        compiled = compiler.compile(
            question="Where was the coupon redeemed?",
            question_time=None,
            route=RouteResult("fact_lookup", ("factoid",)),
            hits=tuple(
                RetrievalHit(turn.source_id, 1.0 / (index + 1), index + 1, "test")
                for index, turn in enumerate(turns)
            ),
            evidence_turns=turns,
            memory_records=(
                MemoryRecord(
                    memory_id="m1",
                    memory_type="fact",
                    text="The coupon was redeemed at Target.",
                    source_ids=("s1:t4",),
                    value="Target",
                ),
            ),
        )

        self.assertEqual(
            [row.source_id for row in compiled.evidence_rows],
            ["s1:t0", "s1:t1", "s1:t4"],
        )
        self.assertIn("Target", compiled.prompt)
        self.assertNotIn("The weather was rainy.", compiled.prompt)

    def test_tail_row_text_compression_applies_only_after_direct_hit_rank(self) -> None:
        compiler = EvidenceCompiler(
            max_evidence_items=4,
            max_evidence_chars=12000,
            prompt_mode="external_naive",
            route_overrides={
                "fact_lookup": {
                    "tail_row_text_after_rank": 2,
                    "tail_row_text_mode": "query_snippet",
                    "tail_max_row_text_chars": 90,
                }
            },
        )

        tail_text = (
            "TAIL_PREFIX_SHOULD_BE_REMOVED "
            + ("unrelated setup " * 20)
            + "The coupon redeemed at Target after lunch. "
            + ("unrelated close " * 20)
            + "TAIL_SUFFIX_SHOULD_BE_REMOVED"
        )
        neighbor_text = (
            "NEIGHBOR_FULL_SENTINEL_START "
            + ("neighbor detail " * 20)
            + "NEIGHBOR_FULL_SENTINEL_END"
        )
        turns = (
            Turn(
                source_id="s1:t0",
                session_id="s1",
                turn_index=0,
                role="user",
                text="TOP_RANK_FULL_SENTINEL_START " + ("top detail " * 20)
                + "TOP_RANK_FULL_SENTINEL_END",
                timestamp="2024-01-08",
            ),
            Turn(
                source_id="s1:t1",
                session_id="s1",
                turn_index=1,
                role="user",
                text="SECOND_RANK_FULL_SENTINEL",
                timestamp="2024-01-08",
            ),
            Turn(
                source_id="s1:t2",
                session_id="s1",
                turn_index=2,
                role="user",
                text=tail_text,
                timestamp="2024-01-08",
            ),
            Turn(
                source_id="s1:t3",
                session_id="s1",
                turn_index=3,
                role="assistant",
                text=neighbor_text,
                timestamp="2024-01-08",
            ),
        )

        compiled = compiler.compile(
            question="Where was the coupon redeemed?",
            question_time=None,
            route=RouteResult("fact_lookup", ("factoid",)),
            hits=(
                RetrievalHit("s1:t0", 1.0, 1, "test"),
                RetrievalHit("s1:t1", 0.9, 2, "test"),
                RetrievalHit("s1:t2", 0.8, 3, "test"),
            ),
            evidence_turns=turns,
            memory_records=(),
        )

        self.assertIn("TOP_RANK_FULL_SENTINEL_END", compiled.prompt)
        self.assertIn("The coupon redeemed at Target", compiled.prompt)
        self.assertNotIn("TAIL_PREFIX_SHOULD_BE_REMOVED", compiled.prompt)
        self.assertNotIn("TAIL_SUFFIX_SHOULD_BE_REMOVED", compiled.prompt)
        self.assertIn("NEIGHBOR_FULL_SENTINEL_START", compiled.prompt)
        self.assertIn("NEIGHBOR_FULL_SENTINEL_END", compiled.prompt)

    def test_tail_row_text_compression_does_not_admit_extra_rows(self) -> None:
        compiler = EvidenceCompiler(
            max_evidence_items=4,
            max_evidence_chars=1600,
            prompt_mode="external_naive",
            route_overrides={
                "fact_lookup": {
                    "tail_row_text_after_rank": 2,
                    "tail_row_text_mode": "query_snippet",
                    "tail_max_row_text_chars": 80,
                }
            },
        )

        turns = (
            Turn(
                source_id="s1:t0",
                session_id="s1",
                turn_index=0,
                role="user",
                text="alpha short top row",
                timestamp="2024-01-08",
            ),
            Turn(
                source_id="s1:t1",
                session_id="s1",
                turn_index=1,
                role="user",
                text="beta short second row",
                timestamp="2024-01-08",
            ),
            Turn(
                source_id="s1:t2",
                session_id="s1",
                turn_index=2,
                role="user",
                text="TAIL_PREFIX "
                + ("unrelated filler " * 55)
                + "coupon redeemed at Target "
                + ("more filler " * 20)
                + "TAIL_SUFFIX",
                timestamp="2024-01-08",
            ),
            Turn(
                source_id="s1:t3",
                session_id="s1",
                turn_index=3,
                role="user",
                text="EXTRA_ROW_SHOULD_NOT_BE_SELECTED",
                timestamp="2024-01-08",
            ),
        )

        compiled = compiler.compile(
            question="Where was the coupon redeemed?",
            question_time=None,
            route=RouteResult("fact_lookup", ("factoid",)),
            hits=(
                RetrievalHit("s1:t0", 1.0, 1, "test"),
                RetrievalHit("s1:t1", 0.9, 2, "test"),
                RetrievalHit("s1:t2", 0.8, 3, "test"),
                RetrievalHit("s1:t3", 0.7, 4, "test"),
            ),
            evidence_turns=turns,
            memory_records=(),
        )

        self.assertEqual(
            [row.source_id for row in compiled.evidence_rows],
            ["s1:t0", "s1:t1", "s1:t2"],
        )
        self.assertIn("coupon redeemed at Target", compiled.prompt)
        self.assertNotIn("TAIL_PREFIX", compiled.prompt)
        self.assertNotIn("EXTRA_ROW_SHOULD_NOT_BE_SELECTED", compiled.prompt)

    def test_assistant_query_miss_tail_snippet_preserves_supported_rows(self) -> None:
        compiler = EvidenceCompiler(
            max_evidence_items=5,
            max_evidence_chars=12000,
            prompt_mode="external_naive",
            route_overrides={
                "fact_lookup": {
                    "tail_row_text_after_rank": 2,
                    "tail_row_text_mode": "assistant_query_miss_snippet",
                    "tail_max_row_text_chars": 80,
                }
            },
        )

        turns = (
            Turn(
                source_id="s1:t0",
                session_id="s1",
                turn_index=0,
                role="assistant",
                text="TOP_ASSISTANT_FULL_START " + ("general advice " * 20)
                + "TOP_ASSISTANT_FULL_END",
                timestamp="2024-01-08",
            ),
            Turn(
                source_id="s1:t1",
                session_id="s1",
                turn_index=1,
                role="user",
                text="SECOND_RANK_FULL_SENTINEL",
                timestamp="2024-01-08",
            ),
            Turn(
                source_id="s1:t2",
                session_id="s1",
                turn_index=2,
                role="assistant",
                text="ASSISTANT_MISS_START " + ("unrelated planning filler " * 20)
                + "ASSISTANT_MISS_END",
                timestamp="2024-01-08",
            ),
            Turn(
                source_id="s1:t3",
                session_id="s1",
                turn_index=3,
                role="assistant",
                text="ASSISTANT_HIT_START The degree was Business Administration. "
                + ("support detail " * 12)
                + "ASSISTANT_HIT_END",
                timestamp="2024-01-08",
            ),
            Turn(
                source_id="s1:t4",
                session_id="s1",
                turn_index=4,
                role="user",
                text="USER_TAIL_FULL_START " + ("unrelated user detail " * 20)
                + "USER_TAIL_FULL_END",
                timestamp="2024-01-08",
            ),
        )

        compiled = compiler.compile(
            question="What degree did I graduate with?",
            question_time=None,
            route=RouteResult("fact_lookup", ("factoid",)),
            hits=(
                RetrievalHit("s1:t0", 1.0, 1, "test"),
                RetrievalHit("s1:t1", 0.9, 2, "test"),
                RetrievalHit("s1:t2", 0.8, 3, "test"),
                RetrievalHit("s1:t3", 0.7, 4, "test"),
                RetrievalHit("s1:t4", 0.6, 5, "test"),
            ),
            evidence_turns=turns,
            memory_records=(),
        )

        self.assertIn("TOP_ASSISTANT_FULL_END", compiled.prompt)
        self.assertIn("ASSISTANT_MISS_START", compiled.prompt)
        self.assertNotIn("ASSISTANT_MISS_END", compiled.prompt)
        self.assertIn("ASSISTANT_HIT_END", compiled.prompt)
        self.assertIn("USER_TAIL_FULL_END", compiled.prompt)


if __name__ == "__main__":
    unittest.main()
