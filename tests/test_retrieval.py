from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from agent_memory.retrieval import LexicalBM25Retriever
from agent_memory.schemas import Turn


class RetrievalTest(unittest.TestCase):
    def test_query_stopwords_are_optional(self) -> None:
        turns = (
            Turn(
                source_id="generic",
                session_id="s1",
                turn_index=0,
                role="speaker",
                text="what to be in her",
            ),
            Turn(
                source_id="specific",
                session_id="s1",
                turn_index=1,
                role="speaker",
                text="Caroline plans to pursue counseling.",
            ),
        )

        raw_hits = LexicalBM25Retriever(turns).retrieve(
            "What would Caroline be likely to pursue in her education?",
            top_k=2,
        )
        filtered_hits = LexicalBM25Retriever(
            turns,
            drop_query_stopwords=True,
        ).retrieve(
            "What would Caroline be likely to pursue in her education?",
            top_k=2,
        )

        self.assertEqual(raw_hits[0].source_id, "generic")
        self.assertEqual(filtered_hits[0].source_id, "specific")


if __name__ == "__main__":
    unittest.main()
