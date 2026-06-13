from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from memory.build import (
    MemoryRecord,
    _bounded_records,
    _cache_key,
    _manage_records,
    _records_from_payload,
)
from memory.compiler import EvidenceCompiler
from memory.retrieval import BuildMemoryBM25Retriever, memory_hits_to_source_hits
from common.schemas import RetrievalHit, RouteResult, Turn


class BuildMemoryTest(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
