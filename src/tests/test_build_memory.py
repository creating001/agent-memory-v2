from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from memory.build import (
    MemoryRecord,
    OpenAICompatibleMemoryBuilder,
    _bounded_records,
    _cache_key,
    _manage_records,
    _records_from_payload,
)
from memory.compiler import EvidenceCompiler
from memory.retrieval import BuildMemoryBM25Retriever, memory_hits_to_source_hits
from common.schemas import RetrievalHit, RouteResult, Turn


class BuildMemoryTest(unittest.TestCase):
    def test_build_cache_hit_counts_cached_usage_as_logical_build_cost(self) -> None:
        class FakeBuilder(OpenAICompatibleMemoryBuilder):
            def __init__(self, cache_path: str):
                super().__init__(
                    base_url="http://unused.local/v1",
                    model="fake-model",
                    temperature=0.0,
                    max_tokens=256,
                    timeout=1.0,
                    max_turns_per_chunk=10,
                    max_chars_per_turn=1000,
                    max_records_per_chunk=4,
                    cache_path=cache_path,
                    cache_namespace="test",
                )
                self.calls = 0

            def _chat_completion(self, prompt: str) -> dict:
                del prompt
                self.calls += 1
                return {
                    "choices": [
                        {
                            "message": {
                                "content": (
                                    '{"records":[{"type":"fact","text":"Alex prefers jasmine tea.",'
                                    '"subject":"Alex","predicate":"prefers","value":"jasmine tea",'
                                    '"source_ids":["s1:t0"],"confidence":0.9}]}'
                                )
                            }
                        }
                    ],
                    "usage": {
                        "prompt_tokens": 30,
                        "completion_tokens": 7,
                        "total_tokens": 37,
                    },
                }

        turns = (
            Turn(
                source_id="s1:t0",
                session_id="s1",
                turn_index=0,
                role="user",
                text="Alex prefers jasmine tea.",
            ),
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            builder = FakeBuilder(str(Path(temp_dir) / "build.sqlite3"))

            first = builder.build(turns)
            second = builder.build(turns)

        self.assertEqual(builder.calls, 1)
        self.assertEqual(first.token_usage.build_tokens, 37)
        self.assertEqual(first.cache_stats.misses, 1)
        self.assertEqual(first.cache_stats.hits, 0)
        self.assertEqual(second.token_usage.build_tokens, 37)
        self.assertEqual(second.cache_stats.misses, 0)
        self.assertEqual(second.cache_stats.hits, 1)

    def test_temporal_build_fields_are_opt_in(self) -> None:
        turns = (
            Turn(
                source_id="s1:t0",
                session_id="s1",
                turn_index=0,
                role="user",
                text="The speaker visited the museum last week.",
                timestamp="2024-01-08",
            ),
        )
        default_builder = OpenAICompatibleMemoryBuilder(
            base_url="http://unused.local/v1",
            model="fake-model",
            temperature=0.0,
            max_tokens=256,
            timeout=1.0,
            max_turns_per_chunk=10,
            max_chars_per_turn=1000,
            max_records_per_chunk=4,
        )
        temporal_builder = OpenAICompatibleMemoryBuilder(
            base_url="http://unused.local/v1",
            model="fake-model",
            temperature=0.0,
            max_tokens=256,
            timeout=1.0,
            max_turns_per_chunk=10,
            max_chars_per_turn=1000,
            max_records_per_chunk=4,
            temporal_fields=True,
        )

        self.assertNotIn("mention_time", default_builder._build_prompt(turns))
        temporal_prompt = temporal_builder._build_prompt(turns)
        self.assertIn("mention_time", temporal_prompt)
        self.assertIn("event_time", temporal_prompt)
        self.assertIn("valid_from", temporal_prompt)

    def test_temporal_build_fields_preserve_event_time_but_not_event_validity(self) -> None:
        class FakeBuilder(OpenAICompatibleMemoryBuilder):
            def __init__(self) -> None:
                super().__init__(
                    base_url="http://unused.local/v1",
                    model="fake-model",
                    temperature=0.0,
                    max_tokens=256,
                    timeout=1.0,
                    max_turns_per_chunk=10,
                    max_chars_per_turn=1000,
                    max_records_per_chunk=4,
                    temporal_fields=True,
            )

            def _chat_completion(self, prompt: str) -> dict:
                assert "event_time" in prompt
                return {
                    "choices": [
                        {
                            "message": {
                                "content": (
                                    '{"records":[{"type":"event",'
                                    '"text":"The speaker visited the museum during the previous week.",'
                                    '"subject":"speaker","predicate":"visited","value":"museum",'
                                    '"source_ids":["s1:t0"],"timestamp":"2024-01-01 to 2024-01-07",'
                                    '"mention_time":"2024-01-08",'
                                    '"event_time":"2024-01-01 to 2024-01-07",'
                                    '"valid_from":"2024-01-01 to 2024-01-07",'
                                    '"entities":["museum"],"confidence":0.9}]}'
                                )
                            }
                        }
                    ],
                    "usage": {"total_tokens": 41},
                }

        built = FakeBuilder().build(
            (
                Turn(
                    source_id="s1:t0",
                    session_id="s1",
                    turn_index=0,
                    role="user",
                    text="The speaker visited the museum last week.",
                    timestamp="2024-01-08",
                ),
            )
        )

        self.assertEqual(len(built.records), 1)
        self.assertEqual(built.records[0].mention_time, "2024-01-08")
        self.assertEqual(built.records[0].event_time, "2024-01-01 to 2024-01-07")
        self.assertIsNone(built.records[0].valid_from)

    def test_temporal_build_fields_preserve_state_validity(self) -> None:
        class FakeBuilder(OpenAICompatibleMemoryBuilder):
            def __init__(self) -> None:
                super().__init__(
                    base_url="http://unused.local/v1",
                    model="fake-model",
                    temperature=0.0,
                    max_tokens=256,
                    timeout=1.0,
                    max_turns_per_chunk=10,
                    max_chars_per_turn=1000,
                    max_records_per_chunk=4,
                    temporal_fields=True,
                )

            def _chat_completion(self, prompt: str) -> dict:
                del prompt
                return {
                    "choices": [
                        {
                            "message": {
                                "content": (
                                    '{"records":[{"type":"state",'
                                    '"text":"The speaker lives in Seattle.",'
                                    '"subject":"speaker","predicate":"lives in","value":"Seattle",'
                                    '"source_ids":["s1:t0"],"timestamp":"2024-01-08",'
                                    '"mention_time":"2024-01-08",'
                                    '"valid_from":"2024-01-01",'
                                    '"entities":["Seattle"],"confidence":0.9}]}'
                                )
                            }
                        }
                    ],
                    "usage": {"total_tokens": 41},
                }

        built = FakeBuilder().build(
            (
                Turn(
                    source_id="s1:t0",
                    session_id="s1",
                    turn_index=0,
                    role="user",
                    text="The speaker moved to Seattle last week and lives there now.",
                    timestamp="2024-01-08",
                ),
            )
        )

        self.assertEqual(len(built.records), 1)
        self.assertEqual(built.records[0].valid_from, "2024-01-01")

    def test_temporal_event_time_does_not_imply_validity_interval(self) -> None:
        class FakeBuilder(OpenAICompatibleMemoryBuilder):
            def __init__(self) -> None:
                super().__init__(
                    base_url="http://unused.local/v1",
                    model="fake-model",
                    temperature=0.0,
                    max_tokens=256,
                    timeout=1.0,
                    max_turns_per_chunk=10,
                    max_chars_per_turn=1000,
                    max_records_per_chunk=4,
                    temporal_fields=True,
                )

            def _chat_completion(self, prompt: str) -> dict:
                del prompt
                return {
                    "choices": [
                        {
                            "message": {
                                "content": (
                                    '{"records":[{"type":"event",'
                                    '"text":"The speaker visited the museum during the previous week.",'
                                    '"source_ids":["s1:t0"],"timestamp":"2024-01-01 to 2024-01-07",'
                                    '"mention_time":"2024-01-08",'
                                    '"event_time":"2024-01-01 to 2024-01-07",'
                                    '"entities":["museum"],"confidence":0.9}]}'
                                )
                            }
                        }
                    ],
                    "usage": {"total_tokens": 39},
                }

        built = FakeBuilder().build(
            (
                Turn(
                    source_id="s1:t0",
                    session_id="s1",
                    turn_index=0,
                    role="user",
                    text="The speaker visited the museum last week.",
                    timestamp="2024-01-08",
                ),
            )
        )

        self.assertEqual(built.records[0].event_time, "2024-01-01 to 2024-01-07")
        self.assertIsNone(built.records[0].valid_from)

    def test_truncated_build_payload_recovers_complete_records(self) -> None:
        payload = (
            '{"records":['
            '{"type":"fact","text":"A","source_ids":["s1:t0"],"confidence":0.9},'
            '{"type":"event","text":"B","source_ids":["s1:t1"],"confidence":0.8},'
            '{"type":"fact","text":"truncated","source_ids":["s1:t2"'
        )

        records = _records_from_payload(payload)

        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]["text"], "A")
        self.assertEqual(records[1]["text"], "B")

    def test_build_cache_key_includes_output_budget(self) -> None:
        prompt = "Build memory from source_id=s1:t0: Alex prefers jasmine tea."

        key_low = _cache_key("ns", "model", 768, 16, prompt)
        key_high = _cache_key("ns", "model", 3072, 16, prompt)

        self.assertNotEqual(key_low, key_high)

    def test_build_records_are_bounded_by_configured_limit(self) -> None:
        raw_records = [
            {"type": "fact", "text": f"record {index}", "source_ids": ["s1:t0"]}
            for index in range(5)
        ]

        records = _bounded_records(raw_records, max_records=2)

        self.assertEqual([record["text"] for record in records], ["record 0", "record 1"])

    def test_build_memory_retrieval_maps_records_to_raw_sources(self) -> None:
        records = (
            MemoryRecord(
                memory_id="m1",
                memory_type="preference",
                text="Alex prefers jasmine tea.",
                source_ids=("s1:t1",),
                subject="Alex",
                predicate="prefers",
                value="jasmine tea",
            ),
            MemoryRecord(
                memory_id="m2",
                memory_type="event",
                text="Alex bought coffee beans.",
                source_ids=("s1:t2",),
                subject="Alex",
                predicate="bought",
                value="coffee beans",
            ),
        )

        memory_hits = BuildMemoryBM25Retriever(records).retrieve(
            "What tea does Alex prefer?",
            top_k=2,
        )
        source_hits = memory_hits_to_source_hits(memory_hits, max_sources_per_memory=2)

        self.assertTrue(memory_hits)
        self.assertEqual(source_hits[0].source_id, "s1:t1")
        self.assertEqual(source_hits[0].retriever, "build_memory_bm25")

    def test_build_memory_retriever_filters_superseded_by_default(self) -> None:
        records = (
            MemoryRecord(
                memory_id="old",
                memory_type="state",
                text="Alex used to prefer black tea.",
                source_ids=("s1:t0",),
                subject="Alex",
                predicate="prefers",
                value="black tea",
                status="superseded",
            ),
            MemoryRecord(
                memory_id="new",
                memory_type="state",
                text="Alex now prefers jasmine tea.",
                source_ids=("s1:t1",),
                subject="Alex",
                predicate="prefers",
                value="jasmine tea",
            ),
        )

        default_hits = BuildMemoryBM25Retriever(records).retrieve(
            "What tea did Alex prefer?",
            top_k=5,
        )
        history_hits = BuildMemoryBM25Retriever(
            records,
            include_superseded=True,
        ).retrieve(
            "What tea did Alex prefer?",
            top_k=5,
        )

        self.assertEqual([hit.record.memory_id for hit in default_hits], ["new"])
        self.assertEqual(
            {hit.record.memory_id for hit in history_hits},
            {"old", "new"},
        )

    def test_memory_manager_adds_validity_interval_to_superseded_record(self) -> None:
        managed = _manage_records(
            (
                MemoryRecord(
                    memory_id="old",
                    memory_type="state",
                    text="Alex prefers black tea.",
                    source_ids=("s1:t0",),
                    subject="Alex",
                    predicate="prefers",
                    value="black tea",
                    timestamp="2023-01-01",
                    valid_from="2023-01-01",
                ),
                MemoryRecord(
                    memory_id="new",
                    memory_type="state",
                    text="Alex prefers jasmine tea.",
                    source_ids=("s1:t1",),
                    subject="Alex",
                    predicate="prefers",
                    value="jasmine tea",
                    timestamp="2023-02-01",
                    valid_from="2023-02-01",
                ),
            )
        )
        by_id = {record.memory_id: record for record in managed}

        self.assertEqual(by_id["old"].status, "superseded")
        self.assertEqual(by_id["old"].valid_to, "2023-02-01")
        self.assertEqual(by_id["old"].superseded_by, "new")
        self.assertEqual(by_id["new"].status, "active")
        self.assertIsNone(by_id["new"].valid_to)

    def test_temporal_memory_manager_does_not_supersede_plain_facts(self) -> None:
        managed = _manage_records(
            (
                MemoryRecord(
                    memory_id="old",
                    memory_type="fact",
                    text="Alex bought black tea.",
                    source_ids=("s1:t0",),
                    subject="Alex",
                    predicate="bought",
                    value="black tea",
                    timestamp="2023-01-01",
                ),
                MemoryRecord(
                    memory_id="new",
                    memory_type="fact",
                    text="Alex bought jasmine tea.",
                    source_ids=("s1:t1",),
                    subject="Alex",
                    predicate="bought",
                    value="jasmine tea",
                    timestamp="2023-02-01",
                ),
            ),
            managed_memory_types=frozenset({"preference", "profile", "relationship", "state"}),
        )
        by_id = {record.memory_id: record for record in managed}

        self.assertEqual(by_id["old"].status, "active")
        self.assertIsNone(by_id["old"].valid_to)
        self.assertEqual(by_id["new"].status, "active")

    def test_compiler_includes_build_memory_view(self) -> None:
        compiler = EvidenceCompiler(
            max_evidence_items=2,
            max_evidence_chars=2000,
            answer_style="concise",
            max_memory_records=1,
        )
        route = RouteResult(information_need="profile_preference", signals=())
        memory_record = MemoryRecord(
            memory_id="m1",
            memory_type="preference",
            text="Alex prefers jasmine tea.",
            source_ids=("s1:t1",),
            subject="Alex",
            predicate="prefers",
            value="jasmine tea",
            valid_from="2023-05-01",
        )
        compiled = compiler.compile(
            question="What tea does Alex prefer?",
            question_time=None,
            route=route,
            hits=(
                RetrievalHit(
                    source_id="s1:t1",
                    score=1.0,
                    rank=1,
                    retriever="test",
                ),
            ),
            evidence_turns=(
                Turn(
                    source_id="s1:t1",
                    session_id="s1",
                    turn_index=1,
                    role="user",
                    text="Alex prefers jasmine tea.",
                ),
            ),
            memory_records=(memory_record,),
        )

        self.assertIn("Build-stage typed memory view", compiled.prompt)
        self.assertIn("Alex prefers jasmine tea", compiled.prompt)
        self.assertIn("valid_from=2023-05-01", compiled.prompt)
        self.assertIn("valid_to=open", compiled.prompt)
        self.assertEqual(compiled.memory_records[0].memory_id, "m1")

    def test_compiler_includes_build_memory_temporal_fields(self) -> None:
        compiler = EvidenceCompiler(
            max_evidence_items=1,
            max_evidence_chars=2000,
            answer_style="concise",
            max_memory_records=1,
            prompt_mode="external_naive",
            structured_guide=True,
            structured_guide_include_memory=True,
        )
        route = RouteResult(information_need="temporal_lookup", signals=("temporal",))
        memory_record = MemoryRecord(
            memory_id="m1",
            memory_type="event",
            text="The speaker visited the museum during the previous week.",
            source_ids=("s1:t0",),
            subject="speaker",
            predicate="visited",
            value="museum",
            timestamp="2024-01-01 to 2024-01-07",
            mention_time="2024-01-08",
            event_time="2024-01-01 to 2024-01-07",
            valid_from="2024-01-01 to 2024-01-07",
        )
        compiled = compiler.compile(
            question="When did the speaker visit the museum?",
            question_time=None,
            route=route,
            hits=(RetrievalHit("s1:t0", 1.0, 1, "test"),),
            evidence_turns=(
                Turn(
                    source_id="s1:t0",
                    session_id="s1",
                    turn_index=0,
                    role="user",
                    text="The speaker visited the museum last week.",
                    timestamp="2024-01-08",
                ),
            ),
            memory_records=(memory_record,),
        )

        self.assertIn("activated_build_memory", compiled.prompt)
        self.assertIn("mention_time=2024-01-08", compiled.prompt)
        self.assertIn("event_time=2024-01-01 to 2024-01-07", compiled.prompt)

    def test_external_naive_prompt_can_include_temporal_aid(self) -> None:
        compiler = EvidenceCompiler(
            max_evidence_items=2,
            max_evidence_chars=2000,
            answer_style="concise",
            max_memory_records=0,
            prompt_mode="external_naive",
            temporal_workpad=True,
            temporal_text_normalization=True,
            temporal_workpad_scope="route",
        )
        route = RouteResult(information_need="temporal_lookup", signals=("temporal",))
        compiled = compiler.compile(
            question="When did Caroline go to the support group?",
            question_time=None,
            route=route,
            hits=(
                RetrievalHit(
                    source_id="s1:t0",
                    score=1.0,
                    rank=1,
                    retriever="test",
                ),
            ),
            evidence_turns=(
                Turn(
                    source_id="s1:t0",
                    session_id="s1",
                    turn_index=0,
                    role="Caroline",
                    text="I went to a LGBTQ support group yesterday and it was powerful.",
                    timestamp="1:56 pm on 8 May, 2023",
                ),
            ),
        )

        self.assertIn("Temporal Aid:", compiled.prompt)
        self.assertIn("Memory 1: row_date=2023-05-08", compiled.prompt)
        self.assertIn('phrase="yesterday" normalized="2023-05-07"', compiled.prompt)
        self.assertIn("Use Temporal Aid only to interpret row dates", compiled.prompt)

    def test_external_naive_prompt_omits_temporal_aid_when_disabled(self) -> None:
        compiler = EvidenceCompiler(
            max_evidence_items=2,
            max_evidence_chars=2000,
            answer_style="concise",
            max_memory_records=0,
            prompt_mode="external_naive",
            temporal_workpad=False,
            temporal_text_normalization=False,
        )
        route = RouteResult(information_need="temporal_lookup", signals=("temporal",))
        compiled = compiler.compile(
            question="When did Caroline go to the support group?",
            question_time=None,
            route=route,
            hits=(),
            evidence_turns=(
                Turn(
                    source_id="s1:t0",
                    session_id="s1",
                    turn_index=0,
                    role="Caroline",
                    text="I went to a LGBTQ support group yesterday and it was powerful.",
                    timestamp="2023-05-08",
                ),
            ),
        )

        self.assertNotIn("Temporal Aid:", compiled.prompt)
        self.assertNotIn("Use Temporal Aid only", compiled.prompt)
        self.assertIn("2. If the context is insufficient", compiled.prompt)

    def test_external_naive_prompt_can_include_structured_evidence_guide(self) -> None:
        compiler = EvidenceCompiler(
            max_evidence_items=2,
            max_evidence_chars=2000,
            answer_style="concise",
            max_memory_records=2,
            prompt_mode="external_naive",
            structured_guide=True,
            structured_guide_max_rows=2,
            temporal_text_normalization=True,
        )
        route = RouteResult(information_need="profile_preference", signals=())
        memory_record = MemoryRecord(
            memory_id="m1",
            memory_type="preference",
            text="Alex prefers jasmine tea.",
            source_ids=("s1:t0",),
            subject="Alex",
            predicate="prefers",
            value="jasmine tea",
            valid_from="2023-05-08",
        )
        compiled = compiler.compile(
            question="What tea does Alex prefer?",
            question_time=None,
            route=route,
            hits=(
                RetrievalHit(
                    source_id="s1:t0",
                    score=1.0,
                    rank=1,
                    retriever="test",
                ),
            ),
            evidence_turns=(
                Turn(
                    source_id="s1:t0",
                    session_id="s1",
                    turn_index=0,
                    role="Alex",
                    text="I preferred jasmine tea yesterday.",
                    timestamp="2023-05-08",
                ),
            ),
            memory_records=(memory_record,),
        )

        self.assertIn("Structured Evidence Guide:", compiled.prompt)
        self.assertIn("Memory 1: row_date=2023-05-08", compiled.prompt)
        self.assertIn('"yesterday"=>"2023-05-07"', compiled.prompt)
        self.assertIn("activated_build_memory", compiled.prompt)
        self.assertIn("type=preference", compiled.prompt)
        self.assertIn("sources=Memory 1", compiled.prompt)
        self.assertIn("Use Structured Evidence Guide only as an index", compiled.prompt)

    def test_external_naive_prompt_omits_structured_guide_when_disabled(self) -> None:
        compiler = EvidenceCompiler(
            max_evidence_items=1,
            max_evidence_chars=2000,
            answer_style="concise",
            prompt_mode="external_naive",
            structured_guide=False,
        )
        route = RouteResult(information_need="fact_lookup", signals=())
        compiled = compiler.compile(
            question="What tea does Alex prefer?",
            question_time=None,
            route=route,
            hits=(),
            evidence_turns=(
                Turn(
                    source_id="s1:t0",
                    session_id="s1",
                    turn_index=0,
                    role="Alex",
                    text="I prefer jasmine tea.",
                    timestamp="2023-05-08",
                ),
            ),
        )

        self.assertNotIn("Structured Evidence Guide:", compiled.prompt)
        self.assertNotIn("Use Structured Evidence Guide only", compiled.prompt)

    def test_external_naive_structured_guide_can_use_source_map_only(self) -> None:
        compiler = EvidenceCompiler(
            max_evidence_items=2,
            max_evidence_chars=2000,
            answer_style="concise",
            max_memory_records=1,
            prompt_mode="external_naive",
            structured_guide=True,
            structured_guide_include_rows=False,
            structured_guide_include_memory=True,
        )
        route = RouteResult(information_need="fact_lookup", signals=())
        memory_record = MemoryRecord(
            memory_id="m1",
            memory_type="fact",
            text="Morgan keeps the spare key in the blue bowl.",
            source_ids=("s1:t1",),
            subject="Morgan",
            predicate="keeps",
            value="spare key in the blue bowl",
            valid_from="2023-05-08",
        )
        compiled = compiler.compile(
            question="Where does Morgan keep the spare key?",
            question_time=None,
            route=route,
            hits=(
                RetrievalHit(
                    source_id="s1:t0",
                    score=1.0,
                    rank=1,
                    retriever="test",
                ),
                RetrievalHit(
                    source_id="s1:t1",
                    score=0.9,
                    rank=2,
                    retriever="test",
                ),
            ),
            evidence_turns=(
                Turn(
                    source_id="s1:t0",
                    session_id="s1",
                    turn_index=0,
                    role="Morgan",
                    text="I moved some things around today.",
                    timestamp="2023-05-08",
                ),
                Turn(
                    source_id="s1:t1",
                    session_id="s1",
                    turn_index=1,
                    role="Morgan",
                    text="I keep the spare key in the blue bowl by the door.",
                    timestamp="2023-05-08",
                ),
            ),
            memory_records=(memory_record,),
        )

        self.assertIn("Structured Evidence Guide:", compiled.prompt)
        self.assertNotIn("- row_index:", compiled.prompt)
        self.assertIn("- activated_build_memory:", compiled.prompt)
        self.assertIn("sources=Memory 2", compiled.prompt)
        self.assertIn("value=spare key in the blue bowl", compiled.prompt)

    def test_external_naive_route_override_can_select_memory_guide(self) -> None:
        compiler = EvidenceCompiler(
            max_evidence_items=2,
            max_evidence_chars=2000,
            answer_style="concise",
            max_memory_records=0,
            prompt_mode="external_naive",
            structured_guide=True,
            structured_guide_include_rows=True,
            structured_guide_include_memory=False,
            route_overrides={
                "temporal_lookup": {
                    "max_memory_records": 1,
                    "structured_guide_include_memory": True,
                }
            },
        )
        memory_record = MemoryRecord(
            memory_id="m1",
            memory_type="event",
            text="Morgan visited the clinic on 2023-05-08.",
            source_ids=("s1:t1",),
            subject="Morgan",
            predicate="visited",
            value="clinic",
            valid_from="2023-05-08",
        )
        turns = (
            Turn(
                source_id="s1:t0",
                session_id="s1",
                turn_index=0,
                role="Morgan",
                text="I planned errands.",
                timestamp="2023-05-07",
            ),
            Turn(
                source_id="s1:t1",
                session_id="s1",
                turn_index=1,
                role="Morgan",
                text="I visited the clinic today.",
                timestamp="2023-05-08",
            ),
        )

        fact_context = compiler.compile(
            question="Where did Morgan go?",
            question_time=None,
            route=RouteResult(information_need="fact_lookup", signals=()),
            hits=(),
            evidence_turns=turns,
            memory_records=(memory_record,),
        )
        temporal_context = compiler.compile(
            question="When did Morgan visit the clinic?",
            question_time=None,
            route=RouteResult(
                information_need="temporal_lookup",
                signals=("temporal",),
            ),
            hits=(),
            evidence_turns=turns,
            memory_records=(memory_record,),
        )

        self.assertIn("- row_index:", fact_context.prompt)
        self.assertNotIn("- activated_build_memory:", fact_context.prompt)
        self.assertEqual(fact_context.memory_records, ())
        self.assertIn("- row_index:", temporal_context.prompt)
        self.assertIn("- activated_build_memory:", temporal_context.prompt)
        self.assertIn("sources=Memory 2", temporal_context.prompt)
        self.assertEqual(len(temporal_context.memory_records), 1)

    def test_external_naive_structured_guide_can_be_disabled_by_signal(self) -> None:
        compiler = EvidenceCompiler(
            max_evidence_items=1,
            max_evidence_chars=2000,
            answer_style="concise",
            prompt_mode="external_naive",
            structured_guide=True,
            structured_guide_include_rows=True,
            structured_guide_include_memory=False,
            structured_guide_disabled_signals=("personalized_recommendation",),
        )
        disabled = compiler.compile(
            question="Can you recommend something for dinner?",
            question_time=None,
            route=RouteResult(
                information_need="profile_preference",
                signals=("profile_or_preference", "personalized_recommendation"),
            ),
            hits=(),
            evidence_turns=(
                Turn(
                    source_id="s1:t0",
                    session_id="s1",
                    turn_index=0,
                    role="Alex",
                    text="I like jasmine tea.",
                    timestamp="2023-05-08",
                ),
            ),
        )
        enabled = compiler.compile(
            question="What tea does Alex like?",
            question_time=None,
            route=RouteResult(
                information_need="profile_preference",
                signals=("profile_or_preference",),
            ),
            hits=(),
            evidence_turns=(
                Turn(
                    source_id="s1:t0",
                    session_id="s1",
                    turn_index=0,
                    role="Alex",
                    text="I like jasmine tea.",
                    timestamp="2023-05-08",
                ),
            ),
        )

        self.assertNotIn("Structured Evidence Guide:", disabled.prompt)
        self.assertIn("Structured Evidence Guide:", enabled.prompt)
        self.assertIn("- row_index:", enabled.prompt)


if __name__ == "__main__":
    unittest.main()
