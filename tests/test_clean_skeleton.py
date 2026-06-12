from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from agent_memory.clean import CleanProtocolViolation, assert_clean_prediction_payload
from agent_memory.answer import _message_text
from agent_memory.compiler import EvidenceCompiler
from agent_memory.io import load_prediction_jsonl
from agent_memory.pipeline import Stage1Pipeline
from agent_memory.schemas import PredictionRequest, RetrievalHit, RouteResult, Turn


class CleanSkeletonTest(unittest.TestCase):
    def test_clean_guard_rejects_gold_answer(self) -> None:
        with self.assertRaises(CleanProtocolViolation):
            assert_clean_prediction_payload(
                {
                    "question": "What did I say?",
                    "gold_answer": "hidden",
                    "turns": [],
                }
            )

    def test_clean_guard_rejects_benchmark_label(self) -> None:
        with self.assertRaises(CleanProtocolViolation):
            assert_clean_prediction_payload(
                {
                    "question": "What did I say?",
                    "question_type": "temporal-reasoning",
                    "turns": [],
                }
            )

    def test_record_key_does_not_enter_pipeline(self) -> None:
        payload = {
            "record_key": "runner-only",
            "question": "What tea does Alex prefer?",
            "sessions": [
                {
                    "session_id": "s1",
                    "turns": [
                        {"role": "user", "text": "Alex prefers jasmine tea."}
                    ],
                }
            ],
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "input.jsonl"
            path.write_text(json.dumps(payload) + "\n", encoding="utf-8")
            envelopes = list(load_prediction_jsonl(path))

        self.assertEqual(envelopes[0].record_key, "runner-only")
        self.assertNotIn("runner-only", envelopes[0].request.question)
        self.assertEqual(envelopes[0].request.turns[0].source_id, "s1:turn_0000")

    def test_pipeline_keeps_source_ids_in_compiled_context(self) -> None:
        config = {
            "retrieval": {"top_k": 4, "max_top_k": 8, "neighbor_window": 1},
            "compiler": {"max_evidence_items": 10, "max_evidence_chars": 4000},
            "answer": {"fallback_answer": "I do not know."},
        }
        request = PredictionRequest(
            question="What tea does Alex prefer?",
            turns=(
                Turn(
                    source_id="s1:t0",
                    session_id="s1",
                    turn_index=0,
                    role="user",
                    text="Alex drinks coffee in the morning.",
                ),
                Turn(
                    source_id="s1:t1",
                    session_id="s1",
                    turn_index=1,
                    role="user",
                    text="Alex prefers jasmine tea in the afternoon.",
                ),
            ),
        )
        result = Stage1Pipeline(config).predict(request)
        rows = result["trace"]["compiled_context"]["evidence_rows"]

        self.assertTrue(rows)
        self.assertTrue(all(row["source_id"] for row in rows))
        self.assertEqual(result["trace"]["token_cost"]["query_tokens"], 0)

    def test_hit_priority_neighbor_expansion_keeps_top_hit_when_compiler_is_tight(self) -> None:
        config = {
            "retrieval": {
                "top_k": 1,
                "max_top_k": 1,
                "neighbor_window": 1,
                "neighbor_order": "hit_priority",
            },
            "compiler": {"max_evidence_items": 1, "max_evidence_chars": 4000},
            "answer": {"fallback_answer": "I do not know."},
        }
        request = PredictionRequest(
            question="When did Caroline go to the LGBTQ support group?",
            turns=(
                Turn(
                    source_id="D1:2",
                    session_id="D1",
                    turn_index=2,
                    role="speaker",
                    text="Caroline discussed plans with a friend.",
                ),
                Turn(
                    source_id="D1:3",
                    session_id="D1",
                    turn_index=3,
                    role="speaker",
                    text="Caroline went to the LGBTQ support group on 7 May 2023.",
                ),
                Turn(
                    source_id="D1:4",
                    session_id="D1",
                    turn_index=4,
                    role="speaker",
                    text="They talked afterward about how helpful the group was.",
                ),
            ),
        )

        result = Stage1Pipeline(config).predict(request)
        rows = result["trace"]["compiled_context"]["evidence_rows"]

        self.assertEqual(rows[0]["source_id"], "D1:3")

    def test_pipeline_accepts_openai_compatible_config(self) -> None:
        config = {
            "retrieval": {"top_k": 1, "max_top_k": 1, "neighbor_window": 0},
            "compiler": {"max_evidence_items": 1, "max_evidence_chars": 1000},
            "answer": {
                "mode": "openai_compatible",
                "base_url": "http://127.0.0.1:65535/v1",
                "model": "test-model",
                "temperature": 0.0,
                "max_tokens": 16,
                "timeout": 0.01,
            },
        }

        pipeline = Stage1Pipeline(config)
        self.assertIsNotNone(pipeline)

    def test_answer_message_text_accepts_reasoning_field(self) -> None:
        self.assertEqual(_message_text({"content": None, "reasoning": "answer"}), "answer")

    def test_concise_answer_style_is_added_to_prompt(self) -> None:
        config = {
            "retrieval": {"top_k": 1, "max_top_k": 1, "neighbor_window": 0},
            "compiler": {
                "max_evidence_items": 1,
                "max_evidence_chars": 1000,
                "answer_style": "concise",
            },
            "answer": {"fallback_answer": "I do not know."},
        }
        request = PredictionRequest(
            question="What tea does Alex prefer?",
            turns=(
                Turn(
                    source_id="s1:t1",
                    session_id="s1",
                    turn_index=1,
                    role="user",
                    text="Alex prefers jasmine tea.",
                ),
            ),
        )

        result = Stage1Pipeline(config).predict(request)
        prompt = result["trace"]["compiled_context"]["prompt"]

        self.assertIn("shortest direct answer", prompt)

    def test_temporal_grounding_is_added_to_prompt(self) -> None:
        config = {
            "retrieval": {"top_k": 1, "max_top_k": 1, "neighbor_window": 0},
            "compiler": {
                "max_evidence_items": 1,
                "max_evidence_chars": 1000,
                "temporal_grounding": True,
                "temporal_hints": True,
            },
            "answer": {"fallback_answer": "I do not know."},
        }
        request = PredictionRequest(
            question="When did Alex visit?",
            turns=(
                Turn(
                    source_id="s1:t1",
                    session_id="s1",
                    turn_index=1,
                    role="user",
                    text="Alex visited yesterday.",
                    timestamp="2023-05-08",
                ),
            ),
        )

        result = Stage1Pipeline(config).predict(request)
        prompt = result["trace"]["compiled_context"]["prompt"]

        self.assertIn("Resolve relative time expressions", prompt)
        self.assertIn("supported absolute date", prompt)
        self.assertIn("Temporal normalization hints", prompt)
        self.assertIn('phrase="yesterday" normalized="2023-05-07"', prompt)

    def test_temporal_hints_are_disabled_by_default(self) -> None:
        config = {
            "retrieval": {"top_k": 1, "max_top_k": 1, "neighbor_window": 0},
            "compiler": {
                "max_evidence_items": 1,
                "max_evidence_chars": 1000,
                "temporal_grounding": True,
            },
            "answer": {"fallback_answer": "I do not know."},
        }
        request = PredictionRequest(
            question="When did Alex visit?",
            turns=(
                Turn(
                    source_id="s1:t1",
                    session_id="s1",
                    turn_index=1,
                    role="user",
                    text="Alex visited yesterday.",
                    timestamp="2023-05-08",
                ),
            ),
        )

        result = Stage1Pipeline(config).predict(request)
        prompt = result["trace"]["compiled_context"]["prompt"]

        self.assertIn("Resolve relative time expressions", prompt)
        self.assertNotIn("Temporal normalization hints", prompt)

    def test_compiler_retrieval_order_is_default(self) -> None:
        compiler = EvidenceCompiler(max_evidence_items=1, max_evidence_chars=4000)
        route = RouteResult(information_need="fact_lookup", signals=())
        compiled = compiler.compile(
            question="What fruit was used for the picnic menu?",
            question_time=None,
            route=route,
            hits=(RetrievalHit("s1:t0", 1.0, 1, "lexical_bm25"),),
            evidence_turns=(
                Turn(
                    source_id="s1:t0",
                    session_id="s1",
                    turn_index=0,
                    role="user",
                    text="Alex discussed the plan.",
                ),
                Turn(
                    source_id="s1:t1",
                    session_id="s1",
                    turn_index=1,
                    role="user",
                    text="The mango fruit was used for the picnic menu.",
                ),
            ),
        )

        self.assertEqual(compiled.evidence_rows[0].source_id, "s1:t0")

    def test_question_overlap_evidence_order_can_promote_relevant_neighbor(self) -> None:
        compiler = EvidenceCompiler(
            max_evidence_items=1,
            max_evidence_chars=4000,
            evidence_order="question_overlap",
        )
        route = RouteResult(information_need="fact_lookup", signals=())
        compiled = compiler.compile(
            question="What fruit was used for the picnic menu?",
            question_time=None,
            route=route,
            hits=(RetrievalHit("s1:t0", 1.0, 1, "lexical_bm25"),),
            evidence_turns=(
                Turn(
                    source_id="s1:t0",
                    session_id="s1",
                    turn_index=0,
                    role="user",
                    text="Alex discussed the plan.",
                ),
                Turn(
                    source_id="s1:t1",
                    session_id="s1",
                    turn_index=1,
                    role="user",
                    text="The mango fruit was used for the picnic menu.",
                ),
            ),
        )

        self.assertEqual(compiled.evidence_rows[0].source_id, "s1:t1")

    def test_query_snippet_row_text_mode_preserves_raw_trace_text(self) -> None:
        long_text = (
            "generic setup " * 40
            + "Alex said the reimbursement folder is the durable answer. "
            + "generic ending " * 40
        )
        compiler = EvidenceCompiler(
            max_evidence_items=1,
            max_evidence_chars=4000,
            row_text_mode="query_snippet",
            max_row_text_chars=120,
        )
        route = RouteResult(information_need="fact_lookup", signals=())
        compiled = compiler.compile(
            question="Where is the reimbursement folder?",
            question_time=None,
            route=route,
            hits=(RetrievalHit("s1:t0", 1.0, 1, "lexical_bm25"),),
            evidence_turns=(
                Turn(
                    source_id="s1:t0",
                    session_id="s1",
                    turn_index=0,
                    role="user",
                    text=long_text,
                ),
            ),
        )

        self.assertEqual(compiled.evidence_rows[0].text, long_text)
        self.assertIn("reimbursement folder", compiled.prompt)
        self.assertLess(len(compiled.prompt), len(long_text))

    def test_route_guidance_is_disabled_by_default(self) -> None:
        compiler = EvidenceCompiler(max_evidence_items=1, max_evidence_chars=4000)
        route = RouteResult(information_need="fact_lookup", signals=())
        compiled = compiler.compile(
            question="What degree did Alex earn?",
            question_time=None,
            route=route,
            hits=(RetrievalHit("s1:t0", 1.0, 1, "lexical_bm25"),),
            evidence_turns=(
                Turn(
                    source_id="s1:t0",
                    session_id="s1",
                    turn_index=0,
                    role="user",
                    text="Alex earned a history degree.",
                ),
            ),
        )

        self.assertNotIn("Information-need guidance", compiled.prompt)

    def test_route_guidance_adds_generic_information_need_prompt(self) -> None:
        compiler = EvidenceCompiler(
            max_evidence_items=1,
            max_evidence_chars=4000,
            route_guidance=True,
        )
        route = RouteResult(information_need="fact_lookup", signals=())
        compiled = compiler.compile(
            question="What degree did Alex earn?",
            question_time=None,
            route=route,
            hits=(RetrievalHit("s1:t0", 1.0, 1, "lexical_bm25"),),
            evidence_turns=(
                Turn(
                    source_id="s1:t0",
                    session_id="s1",
                    turn_index=0,
                    role="user",
                    text="Alex earned a history degree.",
                ),
            ),
        )

        self.assertIn("Information-need guidance", compiled.prompt)
        self.assertIn("Ignore unrelated rows", compiled.prompt)
        self.assertLess(
            compiled.prompt.index("Information-need guidance"),
            compiled.prompt.index("Raw evidence table"),
        )

    def test_session_bm25_anchor_can_feed_compiled_raw_evidence(self) -> None:
        config = {
            "retrieval": {
                "top_k": 1,
                "max_top_k": 1,
                "neighbor_window": 0,
                "drop_query_stopwords": False,
                "session_bm25": {
                    "enabled": True,
                    "top_k": 1,
                    "anchor_top_k": 1,
                    "max_anchor_hits": 1,
                    "protect_turn_hits": 0,
                    "drop_query_stopwords": True,
                    "anchor_drop_query_stopwords": True,
                },
            },
            "compiler": {"max_evidence_items": 1, "max_evidence_chars": 1000},
            "answer": {"fallback_answer": "I do not know."},
        }
        request = PredictionRequest(
            question="When did Melanie go camping in July?",
            turns=(
                Turn(
                    source_id="s1:t0",
                    session_id="s1",
                    turn_index=0,
                    role="speaker",
                    text="when did in when did in",
                ),
                Turn(
                    source_id="s2:t0",
                    session_id="s2",
                    turn_index=0,
                    role="speaker",
                    text="Melanie mentioned camping in July.",
                ),
            ),
        )

        result = Stage1Pipeline(config).predict(request)
        rows = result["trace"]["compiled_context"]["evidence_rows"]
        retrieval = result["trace"]["retrieval"]

        self.assertEqual(rows[0]["source_id"], "s2:t0")
        self.assertEqual(retrieval["session_hits"][0]["source_id"], "s2")
        self.assertEqual(retrieval["session_anchor_hits"][0]["source_id"], "s2:t0")

    def test_session_bm25_gating_can_skip_non_matching_routes(self) -> None:
        config = {
            "retrieval": {
                "top_k": 1,
                "max_top_k": 1,
                "neighbor_window": 0,
                "session_bm25": {
                    "enabled": True,
                    "top_k": 1,
                    "anchor_top_k": 1,
                    "enabled_route_signals": ["temporal"],
                },
            },
            "compiler": {"max_evidence_items": 1, "max_evidence_chars": 1000},
            "answer": {"fallback_answer": "I do not know."},
        }
        request = PredictionRequest(
            question="Who supports Caroline when she has a negative experience?",
            turns=(
                Turn(
                    source_id="s1:t0",
                    session_id="s1",
                    turn_index=0,
                    role="speaker",
                    text="Caroline is supported by Maya.",
                ),
            ),
        )

        result = Stage1Pipeline(config).predict(request)
        retrieval = result["trace"]["retrieval"]

        self.assertTrue(retrieval["session_bm25_enabled"])
        self.assertFalse(retrieval["session_bm25_applied"])
        self.assertEqual(retrieval["session_hits"], [])


if __name__ == "__main__":
    unittest.main()
