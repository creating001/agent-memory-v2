from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from memory.build import MemoryRecord
from memory.compiler import EvidenceCompiler
from memory.retrieval import BuildMemoryBM25Retriever, memory_hits_to_source_hits
from common.schemas import RetrievalHit, RouteResult, Turn


class BuildMemoryTest(unittest.TestCase):
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
        self.assertEqual(compiled.memory_records[0].memory_id, "m1")


if __name__ == "__main__":
    unittest.main()
