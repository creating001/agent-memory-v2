from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from memory.build import (
    MemoryRecord,
    OpenAICompatibleMemoryBuilder,
    _bounded_records,
    _cache_key,
    _chunk_turns,
    _manage_records,
    _manage_records_with_trace,
    _management_summary,
    _records_from_payload,
)
from memory.compiler import EvidenceCompiler
from memory.retrieval import BuildMemoryBM25Retriever, memory_hits_to_source_hits
from common.schemas import RetrievalHit, RouteResult, Turn


class BuildMemoryTest(unittest.TestCase):
    def test_openai_memory_builder_sends_chat_template_kwargs(self) -> None:
        captured: dict[str, object] = {}

        class FakeResponse:
            def __enter__(self) -> "FakeResponse":
                return self

            def __exit__(self, *_args: object) -> None:
                return None

            def read(self) -> bytes:
                return json.dumps(
                    {
                        "choices": [
                            {
                                "message": {
                                    "content": (
                                        '{"records":[{"type":"fact",'
                                        '"text":"Alex likes jasmine tea.",'
                                        '"source_ids":["s1:t0"]}]}'
                                    )
                                }
                            }
                        ],
                        "usage": {"prompt_tokens": 20, "completion_tokens": 5},
                    }
                ).encode("utf-8")

        class FakeOpener:
            def open(self, request: object, timeout: float) -> FakeResponse:
                del timeout
                captured["payload"] = json.loads(request.data.decode("utf-8"))
                return FakeResponse()

        builder = OpenAICompatibleMemoryBuilder(
            base_url="http://unused.local/v1",
            model="fake-model",
            temperature=0.0,
            max_tokens=256,
            timeout=1.0,
            max_turns_per_chunk=10,
            max_chars_per_turn=1000,
            max_records_per_chunk=4,
            chat_template_kwargs={"enable_thinking": False},
        )

        with patch("memory.build.urllib.request.build_opener", return_value=FakeOpener()):
            builder.build(
                (
                    Turn(
                        source_id="s1:t0",
                        session_id="s1",
                        turn_index=0,
                        role="user",
                        text="Alex likes jasmine tea.",
                    ),
                )
            )

        self.assertEqual(
            captured["payload"]["chat_template_kwargs"],
            {"enable_thinking": False},
        )

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

    def test_build_cache_hit_separates_cached_thinking_tokens(self) -> None:
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
                        "completion_tokens": 12,
                        "total_tokens": 42,
                        "completion_tokens_details": {"reasoning_tokens": 5},
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
        self.assertEqual(first.token_usage.build_think_tokens, 5)
        self.assertEqual(first.token_usage.build_total_tokens, 42)
        self.assertEqual(second.token_usage.build_tokens, 37)
        self.assertEqual(second.token_usage.build_think_tokens, 5)
        self.assertEqual(second.token_usage.build_total_tokens, 42)
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

    def test_lossless_atomic_prompt_is_opt_in_and_clean(self) -> None:
        turns = (
            Turn(
                source_id="s1:t0",
                session_id="s1",
                turn_index=0,
                role="user",
                text="I bought a Bellroy case and a Mophie battery last week.",
                timestamp="2024-01-08",
            ),
        )
        builder = OpenAICompatibleMemoryBuilder(
            base_url="http://unused.local/v1",
            model="fake-model",
            temperature=0.0,
            max_tokens=256,
            timeout=1.0,
            max_turns_per_chunk=10,
            max_chars_per_turn=1000,
            max_records_per_chunk=8,
            prompt_profile="lossless_atomic",
        )

        prompt = builder._build_prompt(turns)

        self.assertIn("lossless atomic typed memory index", prompt)
        self.assertIn("split them into separate records", prompt)
        self.assertIn("source_id=s1:t0", prompt)
        self.assertIn("Do not use any question, gold answer", prompt)

    def test_chunk_turns_supports_overlap(self) -> None:
        turns = tuple(
            Turn(
                source_id=f"s1:t{index}",
                session_id="s1",
                turn_index=index,
                role="user",
                text=f"turn {index}",
            )
            for index in range(7)
        )

        chunks = _chunk_turns(turns, max_turns_per_chunk=3, overlap_turns=1)

        self.assertEqual(
            [[turn.source_id for turn in chunk] for chunk in chunks],
            [
                ["s1:t0", "s1:t1", "s1:t2"],
                ["s1:t2", "s1:t3", "s1:t4"],
                ["s1:t4", "s1:t5", "s1:t6"],
            ],
        )

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

    def test_memory_operation_ledger_tracks_management_operations(self) -> None:
        managed_types = frozenset({"preference", "profile", "relationship", "state"})
        records = (
            MemoryRecord(
                memory_id="fact-dup-low",
                memory_type="fact",
                text="Alex bought black tea.",
                source_ids=("s1:t0",),
                subject="Alex",
                predicate="bought",
                value="black tea",
                confidence=0.4,
            ),
            MemoryRecord(
                memory_id="fact-dup-high",
                memory_type="fact",
                text="Alex bought black tea.",
                source_ids=("s1:t0",),
                subject="Alex",
                predicate="bought",
                value="black tea",
                confidence=0.9,
            ),
            MemoryRecord(
                memory_id="fact-coffee",
                memory_type="fact",
                text="Alex bought coffee.",
                source_ids=("s1:t1",),
                subject="Alex",
                predicate="bought",
                value="coffee",
            ),
            MemoryRecord(
                memory_id="state-old",
                memory_type="state",
                text="Alex lives in Austin.",
                source_ids=("s2:t0",),
                subject="Alex",
                predicate="lives_in",
                value="Austin",
                timestamp="2024-01-01",
                valid_from="2024-01-01",
            ),
            MemoryRecord(
                memory_id="state-new",
                memory_type="state",
                text="Alex lives in Seattle.",
                source_ids=("s2:t1",),
                subject="Alex",
                predicate="lives_in",
                value="Seattle",
                timestamp="2024-03-01",
                valid_from="2024-03-01",
            ),
        )

        managed, trace = _manage_records_with_trace(
            records,
            managed_memory_types=managed_types,
        )
        summary = _management_summary(
            managed,
            policy="stateful_only",
            managed_memory_types=managed_types,
            raw_records=records,
            deduped_records=trace["deduped_records"],
            merge_groups=trace["merge_groups"],
            supersede_pairs=trace["supersede_pairs"],
            include_operation_ledger=True,
        )
        ledger = summary["operation_ledger"]

        self.assertTrue(ledger["trace_only"])
        self.assertEqual(ledger["operation_counts"]["create"], 4)
        self.assertEqual(ledger["operation_counts"]["merge"], 1)
        self.assertEqual(ledger["operation_counts"]["supersede"], 1)
        self.assertEqual(
            ledger["operation_counts"]["retain_collection_multi_value_slot"],
            1,
        )
        self.assertEqual(ledger["operation_counts"]["audit_conflict_slot"], 1)
        self.assertEqual(ledger["source_unbacked_record_count"], 0)
        self.assertEqual(
            ledger["samples"]["merge"][0]["memory_id"],
            "fact-dup-high",
        )
        self.assertEqual(
            ledger["samples"]["supersede"][0]["superseded_by"],
            "state-new",
        )

    def test_memory_system_graph_tracks_namespaces_sources_and_operations(self) -> None:
        managed_types = frozenset({"preference", "profile", "relationship", "state"})
        records = (
            MemoryRecord(
                memory_id="profile-old",
                memory_type="state",
                text="Alex lives in Austin.",
                source_ids=("s1:t0",),
                subject="Alex",
                predicate="lives_in",
                value="Austin",
                timestamp="2024-01-01",
                valid_from="2024-01-01",
            ),
            MemoryRecord(
                memory_id="profile-new",
                memory_type="state",
                text="Alex lives in Seattle.",
                source_ids=("s1:t1",),
                subject="Alex",
                predicate="lives_in",
                value="Seattle",
                timestamp="2024-03-01",
                valid_from="2024-03-01",
            ),
            MemoryRecord(
                memory_id="event-visit",
                memory_type="event",
                text="Alex visited Portland.",
                source_ids=("s2:t0",),
                subject="Alex",
                predicate="visited",
                value="Portland",
                timestamp="2024-02-01",
            ),
        )

        managed, trace = _manage_records_with_trace(
            records,
            managed_memory_types=managed_types,
        )
        summary = _management_summary(
            managed,
            policy="stateful_only",
            managed_memory_types=managed_types,
            raw_records=records,
            deduped_records=trace["deduped_records"],
            merge_groups=trace["merge_groups"],
            supersede_pairs=trace["supersede_pairs"],
            include_memory_system_graph=True,
        )
        graph = summary["memory_system_graph"]

        self.assertFalse(graph["trace_only"])
        self.assertTrue(graph["applied"])
        self.assertEqual(graph["memory_object_count"], 3)
        self.assertEqual(graph["source_span_count"], 3)
        self.assertEqual(graph["slot_count"], 2)
        self.assertEqual(graph["managed_lifecycle_slot_count"], 1)
        self.assertEqual(graph["namespace_counts"]["long_term_profile_state"], 2)
        self.assertEqual(graph["namespace_counts"]["long_term_episodic"], 1)
        self.assertEqual(graph["operation_edge_counts"]["supersede"], 1)
        self.assertEqual(graph["operation_edge_counts"]["source_support"], 3)
        self.assertEqual(graph["operation_edge_counts"]["state_conflict_cluster"], 1)
        operation_manifest = graph["operation_manifest"]
        self.assertEqual(
            operation_manifest["schema_version"],
            "memory_operation_manifest_v1",
        )
        self.assertFalse(operation_manifest["trace_only"])
        self.assertEqual(operation_manifest["operation_counts"]["create"], 3)
        self.assertEqual(operation_manifest["operation_counts"]["update"], 1)
        self.assertEqual(operation_manifest["operation_counts"]["supersede"], 1)
        self.assertEqual(operation_manifest["operation_counts"]["retrieve"], 3)
        self.assertEqual(operation_manifest["operation_counts"]["expand"], 3)
        self.assertEqual(operation_manifest["operation_counts"]["verify"], 3)
        self.assertEqual(operation_manifest["operation_counts"]["audit"], 2)
        self.assertEqual(
            operation_manifest["operation_counts"]["audit_state_conflict_slot"],
            1,
        )
        self.assertEqual(
            operation_manifest["object_contract"]["final_evidence_policy"],
            "raw_source_rows",
        )
        self.assertIn(
            "archival_memory",
            operation_manifest["object_contract"]["memory_layers"],
        )
        transition_manifest = graph["memory_layer_transition_manifest"]
        self.assertEqual(
            transition_manifest["schema_version"],
            "memory_layer_transition_manifest_v1",
        )
        self.assertFalse(transition_manifest["trace_only"])
        self.assertTrue(transition_manifest["applied"])
        self.assertEqual(transition_manifest["record_transition_count"], 3)
        self.assertEqual(transition_manifest["slot_transition_count"], 2)
        self.assertEqual(
            transition_manifest["layer_contract"]["final_evidence_policy"],
            "raw_source_rows",
        )
        self.assertEqual(
            transition_manifest["layer_contract"]["delete_policy"],
            "non_destructive_supersede_or_archival",
        )
        lives_in_transition = next(
            transition
            for transition in transition_manifest["slot_transition_index"]
            if transition["predicate"] == "lives_in"
        )
        self.assertEqual(
            lives_in_transition["transition_type"],
            "non_destructive_update",
        )
        self.assertTrue(lives_in_transition["raw_evidence_required"])
        self.assertEqual(lives_in_transition["current_source_count"], 2)
        self.assertEqual(lives_in_transition["historical_source_count"], 2)
        operation_plan = graph["memory_operation_plan"]
        self.assertEqual(
            operation_plan["schema_version"],
            "memory_operation_plan_v1",
        )
        self.assertFalse(operation_plan["trace_only"])
        self.assertTrue(operation_plan["applied"])
        self.assertEqual(operation_plan["operation_plan_count"], 2)
        self.assertEqual(
            operation_plan["operation_contract"]["final_evidence_policy"],
            "raw_source_rows",
        )
        self.assertIn(
            "as_of_state",
            operation_plan["operation_contract"]["view_modes"],
        )
        lives_in_plan = next(
            plan
            for plan in operation_plan["workspace_operation_plans"]
            if plan["predicate"] == "lives_in"
        )
        self.assertEqual(lives_in_plan["memory_tier"], "working_memory")
        self.assertTrue(lives_in_plan["conflict_cluster"])
        self.assertIn("retrieve", lives_in_plan["allowed_operations"])
        self.assertIn("expand", lives_in_plan["allowed_operations"])
        self.assertIn("verify", lives_in_plan["allowed_operations"])
        self.assertIn("audit", lives_in_plan["allowed_operations"])
        self.assertIn("context_pack", lives_in_plan["allowed_operations"])
        self.assertIn("update", lives_in_plan["allowed_operations"])
        self.assertIn("supersede", lives_in_plan["allowed_operations"])
        self.assertEqual(
            lives_in_plan["operation_sequence"][:3],
            ["retrieve", "expand", "verify"],
        )
        self.assertEqual(
            lives_in_plan["source_expansion_plan"]["current_source_order"],
            ["s1:t1", "s1:t0"],
        )
        self.assertEqual(
            lives_in_plan["source_expansion_plan"]["historical_source_order"],
            ["s1:t0", "s1:t1"],
        )
        self.assertIn(
            "audit_conflict_cluster",
            lives_in_plan["audit_plan"]["obligations"],
        )
        self.assertIn(
            "audit_superseded_chain",
            lives_in_plan["audit_plan"]["obligations"],
        )
        self.assertEqual(
            lives_in_plan["verification_plan"]["answer_gate"],
            "raw_rows_must_support_final_answer",
        )
        self.assertTrue(lives_in_plan["context_pack_plan"]["raw_rows_first"])
        readiness_manifest = graph["memory_query_readiness_manifest"]
        self.assertEqual(
            readiness_manifest["schema_version"],
            "memory_query_readiness_manifest_v1",
        )
        self.assertFalse(readiness_manifest["trace_only"])
        self.assertTrue(readiness_manifest["applied"])
        self.assertEqual(readiness_manifest["readiness_slot_count"], 2)
        self.assertEqual(
            readiness_manifest["readiness_contract"]["final_evidence_policy"],
            "raw_source_rows",
        )
        self.assertEqual(
            readiness_manifest["readiness_contract"]["default_consumer_mode"],
            "additive_source_backed_index",
        )
        self.assertEqual(
            readiness_manifest["replace_state_value_guide_blocked_count"],
            2,
        )
        lives_in_readiness = next(
            readiness
            for readiness in readiness_manifest["readiness_index"]
            if readiness["predicate"] == "lives_in"
        )
        self.assertEqual(lives_in_readiness["readiness_state"], "guarded_ready")
        self.assertIn("additive_index", lives_in_readiness["safe_consumption_modes"])
        self.assertIn(
            "conflict_chain_audit",
            lives_in_readiness["safe_consumption_modes"],
        )
        self.assertIn(
            "derived_memory_as_final_evidence",
            lives_in_readiness["unsafe_consumption_modes"],
        )
        self.assertFalse(
            lives_in_readiness["query_gate"]["replace_state_value_guide_allowed"]
        )
        self.assertEqual(
            lives_in_readiness["source_expansion_readiness"][
                "final_evidence_policy"
            ],
            "raw_source_rows",
        )
        self.assertEqual(
            lives_in_readiness["state_value_readiness"]["active_values"],
            ["seattle"],
        )
        self.assertEqual(
            lives_in_readiness["state_value_readiness"]["superseded_values"],
            ["austin"],
        )
        self.assertFalse(
            lives_in_readiness["state_value_readiness"][
                "state_value_equivalence_verified"
            ]
        )
        state_conflict_manifest = graph["state_conflict_manifest"]
        self.assertEqual(
            state_conflict_manifest["schema_version"],
            "memory_state_conflict_manifest_v1",
        )
        self.assertFalse(state_conflict_manifest["trace_only"])
        self.assertEqual(state_conflict_manifest["cluster_count"], 1)
        self.assertEqual(
            state_conflict_manifest["source_backed_cluster_count"],
            1,
        )
        conflict_cluster = state_conflict_manifest["clusters"][0]
        self.assertEqual(conflict_cluster["predicate"], "lives_in")
        self.assertEqual(conflict_cluster["active_values"], ["seattle"])
        self.assertEqual(conflict_cluster["superseded_values"], ["austin"])
        self.assertEqual(conflict_cluster["active_source_order"], ["s1:t1"])
        self.assertEqual(conflict_cluster["superseded_source_order"], ["s1:t0"])
        self.assertEqual(
            graph["operation_edge_samples"]["supersede"][0]["old_memory_id"],
            "profile-old",
        )
        self.assertEqual(
            graph["governance_manifest"]["source_activation_ready_memory_ids"],
            ["event-visit", "profile-new", "profile-old"],
        )
        self.assertEqual(
            graph["governance_manifest"]["activation_priority_memory_ids"],
            ["profile-new", "profile-old", "event-visit"],
        )
        self.assertEqual(
            graph["governance_manifest"]["activation_role_counts"],
            {
                "episodic_candidate": 1,
                "lifecycle_context": 1,
                "stateful_candidate": 1,
            },
        )
        self.assertEqual(
            graph["governance_manifest"]["activation_utility_bucket_counts"],
            {"high": 3},
        )

    def test_builder_can_keep_parallel_facts_active_without_temporal_fields(self) -> None:
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
                    manage_facts=False,
                )

            def _chat_completion(self, prompt: str) -> dict:
                del prompt
                return {
                    "choices": [
                        {
                            "message": {
                                "content": (
                                    '{"records":['
                                    '{"type":"fact","text":"Alex bought black tea.",'
                                    '"subject":"Alex","predicate":"bought",'
                                    '"value":"black tea","source_ids":["s1:t0"],'
                                    '"timestamp":"2023-01-01","confidence":0.9},'
                                    '{"type":"fact","text":"Alex bought jasmine tea.",'
                                    '"subject":"Alex","predicate":"bought",'
                                    '"value":"jasmine tea","source_ids":["s1:t1"],'
                                    '"timestamp":"2023-02-01","confidence":0.9}'
                                    "]} "
                                )
                            }
                        }
                    ],
                    "usage": {"total_tokens": 43},
                }

        built = FakeBuilder().build(
            (
                Turn(
                    source_id="s1:t0",
                    session_id="s1",
                    turn_index=0,
                    role="user",
                    text="Alex bought black tea.",
                ),
                Turn(
                    source_id="s1:t1",
                    session_id="s1",
                    turn_index=1,
                    role="user",
                    text="Alex bought jasmine tea.",
                ),
            )
        )

        by_value = {record.value: record for record in built.records}
        self.assertEqual(by_value["black tea"].status, "active")
        self.assertEqual(by_value["jasmine tea"].status, "active")
        self.assertNotIn("operation_ledger", built.management or {})

    def test_builder_can_emit_operation_ledger(self) -> None:
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
                    manage_facts=False,
                    operation_ledger=True,
                )

            def _chat_completion(self, prompt: str) -> dict:
                del prompt
                return {
                    "choices": [
                        {
                            "message": {
                                "content": (
                                    '{"records":['
                                    '{"type":"state","text":"Alex lives in Austin.",'
                                    '"subject":"Alex","predicate":"lives_in",'
                                    '"value":"Austin","source_ids":["s1:t0"],'
                                    '"timestamp":"2024-01-01","confidence":0.9},'
                                    '{"type":"state","text":"Alex lives in Seattle.",'
                                    '"subject":"Alex","predicate":"lives_in",'
                                    '"value":"Seattle","source_ids":["s1:t1"],'
                                    '"timestamp":"2024-03-01","confidence":0.9}'
                                    "]} "
                                )
                            }
                        }
                    ],
                    "usage": {"total_tokens": 43},
                }

        built = FakeBuilder().build(
            (
                Turn(
                    source_id="s1:t0",
                    session_id="s1",
                    turn_index=0,
                    role="user",
                    text="Alex lives in Austin.",
                ),
                Turn(
                    source_id="s1:t1",
                    session_id="s1",
                    turn_index=1,
                    role="user",
                    text="Alex lives in Seattle.",
                ),
            )
        )

        ledger = (built.management or {})["operation_ledger"]
        self.assertTrue(ledger["applied"])
        self.assertEqual(ledger["operation_counts"]["supersede"], 1)
        self.assertEqual(ledger["source_backed_record_count"], 2)

    def test_builder_can_emit_memory_system_graph(self) -> None:
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
                    manage_facts=False,
                    memory_system_graph=True,
                )

            def _chat_completion(self, prompt: str) -> dict:
                del prompt
                return {
                    "choices": [
                        {
                            "message": {
                                "content": (
                                    '{"records":['
                                    '{"type":"state","text":"Alex lives in Austin.",'
                                    '"subject":"Alex","predicate":"lives_in",'
                                    '"value":"Austin","source_ids":["s1:t0"],'
                                    '"timestamp":"2024-01-01","confidence":0.9},'
                                    '{"type":"state","text":"Alex lives in Seattle.",'
                                    '"subject":"Alex","predicate":"lives_in",'
                                    '"value":"Seattle","source_ids":["s1:t1"],'
                                    '"timestamp":"2024-03-01","confidence":0.9}'
                                    "]} "
                                )
                            }
                        }
                    ],
                    "usage": {"total_tokens": 43},
                }

        built = FakeBuilder().build(
            (
                Turn(
                    source_id="s1:t0",
                    session_id="s1",
                    turn_index=0,
                    role="user",
                    text="Alex lives in Austin.",
                ),
                Turn(
                    source_id="s1:t1",
                    session_id="s1",
                    turn_index=1,
                    role="user",
                    text="Alex lives in Seattle.",
                ),
            )
        )

        graph = (built.management or {})["memory_system_graph"]
        self.assertTrue(graph["applied"])
        self.assertEqual(graph["memory_object_count"], 2)
        self.assertEqual(graph["operation_edge_counts"]["supersede"], 1)

    def test_management_policy_keeps_collection_facts_out_of_lifecycle(self) -> None:
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
                    management_policy="stateful_only",
                )

            def _chat_completion(self, prompt: str) -> dict:
                del prompt
                return {
                    "choices": [
                        {
                            "message": {
                                "content": (
                                    '{"records":['
                                    '{"type":"fact","text":"Alex read Dune.",'
                                    '"subject":"Alex","predicate":"read",'
                                    '"value":"Dune","source_ids":["s1:t0"],'
                                    '"timestamp":"2023-01-01","confidence":0.9},'
                                    '{"type":"fact","text":"Alex read Foundation.",'
                                    '"subject":"Alex","predicate":"read",'
                                    '"value":"Foundation","source_ids":["s1:t1"],'
                                    '"timestamp":"2023-02-01","confidence":0.9}'
                                    "]} "
                                )
                            }
                        }
                    ],
                    "usage": {"total_tokens": 43},
                }

        built = FakeBuilder().build(
            (
                Turn(
                    source_id="s1:t0",
                    session_id="s1",
                    turn_index=0,
                    role="user",
                    text="Alex read Dune.",
                ),
                Turn(
                    source_id="s1:t1",
                    session_id="s1",
                    turn_index=1,
                    role="user",
                    text="Alex read Foundation.",
                ),
            )
        )

        self.assertEqual(built.management_policy, "stateful_only")
        self.assertEqual(built.managed_memory_types, ("preference", "profile", "relationship", "state"))
        self.assertEqual({record.status for record in built.records}, {"active"})
        self.assertEqual(built.management["layer_counts"]["semantic"], 2)
        self.assertEqual(
            built.management["operation_counts"]["retain_collection_multi_value_slot"],
            1,
        )
        self.assertEqual(built.management["operation_counts"]["supersede"], 0)

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

    def test_external_naive_context_can_group_by_session_thread(self) -> None:
        compiler = EvidenceCompiler(
            max_evidence_items=3,
            max_evidence_chars=4000,
            answer_style="concise",
            prompt_mode="external_naive",
            context_layout="session_thread",
        )
        route = RouteResult(information_need="temporal_lookup", signals=("temporal",))
        compiled = compiler.compile(
            question="When did Morgan visit the clinic?",
            question_time=None,
            route=route,
            hits=(
                RetrievalHit("s1:t2", 1.0, 1, "test"),
                RetrievalHit("s2:t0", 0.9, 2, "test"),
                RetrievalHit("s1:t0", 0.8, 3, "test"),
            ),
            evidence_turns=(
                Turn(
                    source_id="s1:t2",
                    session_id="s1",
                    turn_index=2,
                    role="Morgan",
                    text="I visited the clinic today.",
                    timestamp="2023-05-08",
                ),
                Turn(
                    source_id="s2:t0",
                    session_id="s2",
                    turn_index=0,
                    role="Morgan",
                    text="I planned a grocery trip.",
                    timestamp="2023-05-09",
                ),
                Turn(
                    source_id="s1:t0",
                    session_id="s1",
                    turn_index=0,
                    role="Morgan",
                    text="I woke up early.",
                    timestamp="2023-05-08",
                ),
            ),
        )

        self.assertEqual(
            [row.source_id for row in compiled.evidence_rows],
            ["s1:t0", "s1:t2", "s2:t0"],
        )
        self.assertIn("### Episode 1\nSession: s1", compiled.prompt)
        self.assertIn("#### Memory 1\nDate: 2023-05-08\nTurn: 0", compiled.prompt)
        self.assertIn("#### Memory 2\nDate: 2023-05-08\nTurn: 2", compiled.prompt)
        self.assertIn("Memory Context is grouped by session", compiled.prompt)

    def test_external_naive_route_override_can_select_session_thread_layout(self) -> None:
        compiler = EvidenceCompiler(
            max_evidence_items=2,
            max_evidence_chars=3000,
            answer_style="concise",
            prompt_mode="external_naive",
            context_layout="flat",
            route_overrides={
                "list_count": {
                    "context_layout": "session_thread",
                }
            },
        )
        turns = (
            Turn(
                source_id="s1:t1",
                session_id="s1",
                turn_index=1,
                role="Morgan",
                text="I need to pick up boots.",
                timestamp="2023-05-08",
            ),
            Turn(
                source_id="s1:t0",
                session_id="s1",
                turn_index=0,
                role="Morgan",
                text="I need to pick up dry cleaning.",
                timestamp="2023-05-08",
            ),
        )

        fact_context = compiler.compile(
            question="What does Morgan need to pick up?",
            question_time=None,
            route=RouteResult(information_need="fact_lookup", signals=()),
            hits=(RetrievalHit("s1:t1", 1.0, 1, "test"),),
            evidence_turns=turns,
        )
        list_context = compiler.compile(
            question="How many items does Morgan need to pick up?",
            question_time=None,
            route=RouteResult(information_need="list_count", signals=("list_or_count",)),
            hits=(RetrievalHit("s1:t1", 1.0, 1, "test"),),
            evidence_turns=turns,
        )

        self.assertNotIn("### Episode 1", fact_context.prompt)
        self.assertIn("### Episode 1", list_context.prompt)
        self.assertEqual(
            [row.source_id for row in list_context.evidence_rows],
            ["s1:t0", "s1:t1"],
        )

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
