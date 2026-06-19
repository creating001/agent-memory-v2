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


if __name__ == "__main__":
    unittest.main()
