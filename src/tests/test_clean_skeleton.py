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

from common.clean import CleanProtocolViolation, assert_clean_prediction_payload
from memory.answer import CachedAnswerer, _message_text, _parse_answer_content
from memory.build import MemoryRecord
from memory.compiler import EvidenceCompiler
from memory.finalize import finalize_structured_answer, raw_response_content
from memory.repair import build_repair_prompt, repair_trigger_reasons
from memory.rerank import RerankResult
from memory.retrieval import (
    MemoryHit,
    TurnWindowBM25Retriever,
    build_turn_window_documents,
    turn_window_hits_to_source_hits,
)
from memory.scoped_evidence import (
    build_scoped_evidence_answer_prompt,
    build_scoped_evidence_extraction_prompt,
    extract_evidence_json_text,
    scoped_evidence_answer_result,
    should_apply_scoped_evidence,
)
from data.io import load_prediction_jsonl
from memory.pipeline import (
    Stage1Pipeline,
    _align_build_memory_sources,
    _compiler_memory_records,
)
from memory.store import RawEvidenceStore
from common.schemas import (
    AnswerResult,
    CompiledContext,
    EvidenceRow,
    PredictionRequest,
    RetrievalHit,
    RouteResult,
    TokenUsage,
    Turn,
    llm_usage_to_token_usage,
)


class CleanSkeletonTest(unittest.TestCase):
    def test_llm_usage_to_token_usage_separates_reasoning_tokens(self) -> None:
        usage = {
            "prompt_tokens": 100,
            "completion_tokens": 30,
            "total_tokens": 130,
            "completion_tokens_details": {"reasoning_tokens": 12},
        }

        result = llm_usage_to_token_usage(usage, phase="query")

        self.assertEqual(result.query_tokens, 118)
        self.assertEqual(result.query_think_tokens, 12)
        self.assertEqual(result.query_total_tokens, 130)

    def test_token_usage_from_mapping_preserves_legacy_visible_tokens(self) -> None:
        result = TokenUsage.from_mapping({"query_tokens": 42})

        self.assertEqual(result.query_tokens, 42)
        self.assertEqual(result.query_think_tokens, 0)
        self.assertEqual(result.query_total_tokens, 42)

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

    def test_pipeline_can_disable_lexical_retrieval(self) -> None:
        config = {
            "retrieval": {
                "top_k": 4,
                "max_top_k": 4,
                "neighbor_window": 0,
                "lexical": {"enabled": False},
            },
            "compiler": {"max_evidence_items": 10, "max_evidence_chars": 4000},
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

        self.assertFalse(result["trace"]["retrieval"]["lexical_enabled"])
        self.assertEqual(result["trace"]["retrieval"]["retriever"], "no_retriever")
        self.assertEqual(result["trace"]["compiled_context"]["evidence_rows"], [])

    def test_turn_window_bm25_projects_adjacent_raw_sources(self) -> None:
        turns = (
            Turn(
                source_id="s1:t0",
                session_id="s1",
                turn_index=0,
                role="user",
                text="Alex mentioned redeeming a coupon after work.",
            ),
            Turn(
                source_id="s1:t1",
                session_id="s1",
                turn_index=1,
                role="assistant",
                text="The relevant store was Target.",
            ),
        )

        documents = build_turn_window_documents(
            turns,
            window_before=0,
            window_after=1,
        )
        window_hits = TurnWindowBM25Retriever(
            documents,
            drop_query_stopwords=True,
        ).retrieve("Where did Alex redeem the coupon at Target?", top_k=1)
        source_hits = turn_window_hits_to_source_hits(
            window_hits,
            max_sources_per_window=2,
        )

        self.assertEqual(source_hits[0].source_id, "s1:t0")
        self.assertEqual(source_hits[1].source_id, "s1:t1")
        self.assertEqual(source_hits[0].retriever, "turn_window_bm25")

    def test_pipeline_turn_window_bm25_is_traceable_and_clean(self) -> None:
        config = {
            "retrieval": {
                "top_k": 4,
                "max_top_k": 4,
                "neighbor_window": 0,
                "lexical": {"enabled": False},
                "turn_window_bm25": {
                    "enabled": True,
                    "top_k": 1,
                    "window_before": 0,
                    "window_after": 1,
                    "max_sources_per_window": 2,
                    "drop_query_stopwords": True,
                },
            },
            "compiler": {"max_evidence_items": 4, "max_evidence_chars": 4000},
            "answer": {"fallback_answer": "unknown"},
        }
        request = PredictionRequest(
            question="Where did Alex redeem the coupon at Target?",
            turns=(
                Turn(
                    source_id="s1:t0",
                    session_id="s1",
                    turn_index=0,
                    role="user",
                    text="Alex mentioned redeeming a coupon after work.",
                ),
                Turn(
                    source_id="s1:t1",
                    session_id="s1",
                    turn_index=1,
                    role="assistant",
                    text="The relevant store was Target.",
                ),
            ),
        )

        result = Stage1Pipeline(config).predict(request)
        retrieval_trace = result["trace"]["retrieval"]
        row_source_ids = [
            row["source_id"]
            for row in result["trace"]["compiled_context"]["evidence_rows"]
        ]

        self.assertTrue(retrieval_trace["turn_window_bm25_applied"])
        self.assertTrue(retrieval_trace["turn_window_hits"])
        self.assertEqual(
            [hit["source_id"] for hit in retrieval_trace["turn_window_source_hits"]],
            ["s1:t0", "s1:t1"],
        )
        self.assertEqual(row_source_ids, ["s1:t0", "s1:t1"])

    def test_pipeline_selected_context_materializes_adjacent_turns(self) -> None:
        config = {
            "retrieval": {
                "top_k": 2,
                "max_top_k": 2,
                "neighbor_window": 0,
                "selected_context": {
                    "enabled": True,
                    "window_before": 1,
                    "window_after": 0,
                    "max_rows": 2,
                    "max_neighbor_chars": 80,
                    "require_anaphora": True,
                    "information_needs": ["list_count"],
                },
            },
            "route": {"enable_broad_list_patterns": True},
            "compiler": {
                "prompt_mode": "external_naive",
                "max_evidence_items": 2,
                "max_evidence_chars": 4000,
            },
            "answer": {"fallback_answer": "unknown"},
        }
        request = PredictionRequest(
            question="What books has Alex read?",
            turns=(
                Turn(
                    source_id="s1:t0",
                    session_id="s1",
                    turn_index=0,
                    role="user",
                    text='Alex read "Nothing is Impossible" last year.',
                    timestamp="2024-01-01",
                ),
                Turn(
                    source_id="s1:t1",
                    session_id="s1",
                    turn_index=1,
                    role="assistant",
                    text="This book inspired Alex to keep training.",
                    timestamp="2024-01-01",
                ),
            ),
        )

        result = Stage1Pipeline(config).predict(request)
        trace = result["trace"]["retrieval"]["selected_context"]
        rows = result["trace"]["compiled_context"]["evidence_rows"]
        prompt = result["trace"]["compiled_context"]["prompt"]
        row_text = "\n".join(row["text"] for row in rows)

        self.assertTrue(trace["applied"])
        self.assertEqual(trace["materialized_count"], 1)
        self.assertIn("s1:t1", trace["materialized_source_ids"])
        self.assertIn("Local dialogue context from the same session", row_text)
        self.assertIn("Nothing is Impossible", row_text)
        self.assertIn("Nothing is Impossible", prompt)
        self.assertNotIn("question_type", prompt)

    def test_granularity_profile_switches_context_strategy(self) -> None:
        config = {
            "retrieval": {
                "top_k": 4,
                "max_top_k": 4,
                "neighbor_window": 0,
                "selected_context": {
                    "enabled": True,
                    "window_before": 1,
                    "window_after": 0,
                    "max_rows": 2,
                    "max_neighbor_chars": 80,
                    "require_anaphora": True,
                    "information_needs": ["list_count"],
                },
                "granularity_profiles": [
                    {
                        "name": "long_turn_precision",
                        "min_avg_turn_chars": 100,
                        "route": {"enable_broad_list_patterns": False},
                        "retrieval": {
                            "top_k": 1,
                            "max_top_k": 1,
                            "dense_top_k": 1,
                            "dense_protect_top_n": 0,
                        },
                        "selected_context": {"enabled": False},
                        "compiler": {
                            "temporal_event_contract": False,
                            "operation_workpad": True,
                            "personalized_advice_contract": True,
                            "update_conflict_guide": True,
                        },
                        "answer_finalizer": {
                            "enabled": True,
                            "mode": "structured_evidence_mechanical",
                            "enable_count_answer_detail": True,
                            "enable_relative_time_calculation": False,
                        },
                    }
                ],
            },
            "route": {"enable_broad_list_patterns": True},
            "compiler": {
                "prompt_mode": "external_naive",
                "max_evidence_items": 4,
                "max_evidence_chars": 4000,
                "evidence_report_contract": True,
                "evidence_report_information_needs": ["list_count"],
                "temporal_event_contract": True,
                "operation_workpad": False,
                "personalized_advice_contract": False,
                "update_conflict_guide": False,
            },
            "answer": {
                "fallback_answer": "unknown",
                "finalizer": {
                    "enabled": True,
                    "mode": "structured_evidence_mechanical",
                    "enable_relative_time_calculation": True,
                },
            },
        }
        short_request = PredictionRequest(
            question="How many books has Alex read?",
            turns=(
                Turn("s:t0", "s", 0, "user", "Alex read Dune."),
                Turn("s:t1", "s", 1, "assistant", "This book was excellent."),
            ),
        )
        long_text = " ".join(["Alex read Dune."] * 20)
        long_request = PredictionRequest(
            question="How many books has Alex read?",
            turns=(
                Turn("s:t0", "s", 0, "user", long_text),
                Turn("s:t1", "s", 1, "assistant", " ".join(["This book was excellent."] * 20)),
            ),
        )

        short_result = Stage1Pipeline(config).predict(short_request)
        long_result = Stage1Pipeline(config).predict(long_request)

        self.assertIsNone(short_result["trace"]["retrieval"]["granularity_profile"])
        self.assertEqual(short_result["trace"]["retrieval"]["top_k"], 4)
        self.assertTrue(
            short_result["trace"]["retrieval"]["selected_context"]["enabled"]
        )

        long_retrieval = long_result["trace"]["retrieval"]
        long_finalizer = long_result["trace"]["answer_finalizer"]
        self.assertEqual(long_retrieval["top_k"], 1)
        self.assertEqual(
            long_retrieval["granularity_profile"]["name"],
            "long_turn_precision",
        )
        self.assertFalse(long_retrieval["selected_context"]["enabled"])
        self.assertEqual(long_retrieval["compiler_profile"], "long_turn_precision")
        long_compiler = long_result["trace"]["compiler"]
        self.assertFalse(long_compiler["temporal_event_contract"])
        self.assertTrue(long_compiler["operation_workpad"])
        self.assertTrue(long_compiler["personalized_advice_contract"])
        self.assertTrue(long_compiler["update_conflict_guide"])
        self.assertIn(
            "Private Operation Discipline",
            long_result["trace"]["compiled_context"]["prompt"],
        )
        self.assertNotIn(
            "event_time_candidates",
            long_result["trace"]["compiled_context"]["prompt"],
        )
        self.assertTrue(long_finalizer["enable_count_answer_detail"])
        self.assertFalse(long_finalizer["enable_relative_time_calculation"])

    def test_pipeline_rerank_expands_candidate_pool_and_reorders_hits(self) -> None:
        config = {
            "retrieval": {
                "top_k": 1,
                "max_top_k": 1,
                "neighbor_window": 0,
                "drop_query_stopwords": True,
                "rerank": {
                    "enabled": True,
                    "base_url": "http://127.0.0.1:8002/v1",
                    "model": "fake-reranker",
                    "pool_k": 2,
                    "anchor_keep": 0,
                    "anchor_after_top": 0,
                },
            },
            "compiler": {"max_evidence_items": 1, "max_evidence_chars": 4000},
            "answer": {"fallback_answer": "unknown"},
        }
        request = PredictionRequest(
            question="Where did Alex redeem the coupon?",
            turns=(
                Turn(
                    source_id="bad",
                    session_id="s1",
                    turn_index=0,
                    role="user",
                    text="Where redeem coupon where redeem coupon.",
                ),
                Turn(
                    source_id="good",
                    session_id="s1",
                    turn_index=1,
                    role="user",
                    text="Alex redeemed the coupon at Target.",
                ),
            ),
        )

        with patch("memory.pipeline.OpenAICompatibleRerankClient", _FakeReranker):
            result = Stage1Pipeline(config).predict(request)

        retrieval_trace = result["trace"]["retrieval"]
        rows = result["trace"]["compiled_context"]["evidence_rows"]

        self.assertEqual(retrieval_trace["candidate_top_k"], 2)
        self.assertTrue(retrieval_trace["rerank_applied"])
        self.assertEqual(retrieval_trace["rerank_total_tokens"], 7)
        self.assertEqual(retrieval_trace["hits"][0]["source_id"], "good")
        self.assertEqual(rows[0]["source_id"], "good")
        self.assertNotIn("question_type", result["trace"]["compiled_context"]["prompt"])
        self.assertEqual(result["trace"]["token_cost"]["query_tokens"], 0)

    def test_scoped_evidence_is_disabled_by_default(self) -> None:
        result = Stage1Pipeline(
            {
                "retrieval": {"top_k": 1, "max_top_k": 1},
                "compiler": {"max_evidence_items": 1, "max_evidence_chars": 1000},
                "answer": {"fallback_answer": "fallback"},
            }
        ).predict(
            PredictionRequest(
                question="How many teas does Alex like?",
                turns=(
                    Turn(
                        source_id="s1:t0",
                        session_id="s1",
                        turn_index=0,
                        role="user",
                        text="Alex likes jasmine tea.",
                    ),
                ),
            )
        )

        self.assertFalse(result["trace"]["scoped_evidence"]["enabled"])
        self.assertFalse(result["trace"]["scoped_evidence"]["applied"])

    def test_scoped_evidence_prompts_are_question_and_context_only(self) -> None:
        context = CompiledContext(
            question="How much did Alex spend on bike expenses?",
            question_time="2024-01-10",
            route=RouteResult("list_count", ("list_or_count",), 3),
            evidence_rows=(
                EvidenceRow(
                    source_id="s1:t0",
                    session_id="s1",
                    turn_index=0,
                    role="user",
                    text="Alex bought a helmet for $120 and lights for $40.",
                    timestamp="2024-01-05",
                    retrieval_rank=1,
                    retrieval_score=1.0,
                ),
            ),
            prompt="unused",
            context_chars=0,
        )

        extraction_prompt = build_scoped_evidence_extraction_prompt(
            context,
            max_rows=5,
            max_row_chars=200,
        )
        evidence_json = extract_evidence_json_text(
            'prefix {"sufficient": true, "included_items": []} suffix'
        )
        answer_prompt = build_scoped_evidence_answer_prompt(context, evidence_json)

        self.assertTrue(should_apply_scoped_evidence(context, ("list_count",)))
        self.assertIn("Alex bought a helmet", extraction_prompt)
        self.assertIn('"included_items"', extraction_prompt)
        self.assertIn('"sufficient": true', answer_prompt)
        self.assertNotIn("record_key", extraction_prompt)
        self.assertNotIn("question_type", extraction_prompt)
        self.assertNotIn("sample_id", extraction_prompt)

    def test_scoped_evidence_answer_result_merges_query_tokens(self) -> None:
        extraction = AnswerResult(
            answer='{"sufficient": true}',
            model="model",
            token_usage=TokenUsage(query_tokens=11),
        )
        final = AnswerResult(
            answer="160 dollars",
            model="model",
            token_usage=TokenUsage(query_tokens=13),
            raw_response="raw",
        )

        merged = scoped_evidence_answer_result(
            extraction_result=extraction,
            final_result=final,
        )

        self.assertEqual(merged.answer, "160 dollars")
        self.assertEqual(merged.token_usage.query_tokens, 24)
        self.assertEqual(merged.raw_response, "raw")

    def test_retrieval_route_overrides_use_question_information_need(self) -> None:
        config = {
            "retrieval": {
                "top_k": 3,
                "max_top_k": 3,
                "neighbor_window": 0,
                "route_overrides": {
                    "temporal_lookup": {
                        "top_k": 1,
                        "max_top_k": 1,
                    }
                },
            },
            "compiler": {"max_evidence_items": 10, "max_evidence_chars": 4000},
            "answer": {"fallback_answer": "I do not know."},
        }
        turns = (
            Turn(
                source_id="s1:t0",
                session_id="s1",
                turn_index=0,
                role="user",
                text="Alex visited Paris in 2021.",
            ),
            Turn(
                source_id="s1:t1",
                session_id="s1",
                turn_index=1,
                role="user",
                text="Alex visited Berlin in 2022.",
            ),
            Turn(
                source_id="s1:t2",
                session_id="s1",
                turn_index=2,
                role="user",
                text="Alex visited Rome in 2023.",
            ),
        )

        temporal_result = Stage1Pipeline(config).predict(
            PredictionRequest(question="When did Alex visit Berlin?", turns=turns)
        )
        fact_result = Stage1Pipeline(config).predict(
            PredictionRequest(question="What city did Alex visit?", turns=turns)
        )

        self.assertEqual(temporal_result["trace"]["route"]["information_need"], "temporal_lookup")
        self.assertEqual(temporal_result["trace"]["retrieval"]["top_k"], 1)
        self.assertEqual(
            temporal_result["trace"]["retrieval"]["route_override"],
            {"max_top_k": 1, "top_k": 1},
        )
        self.assertEqual(fact_result["trace"]["route"]["information_need"], "fact_lookup")
        self.assertEqual(fact_result["trace"]["retrieval"]["top_k"], 3)

    def test_retrieval_route_overrides_reject_hidden_label_names(self) -> None:
        config = {
            "retrieval": {
                "top_k": 1,
                "max_top_k": 1,
                "route_overrides": {"question_type": {"top_k": 1}},
            },
            "compiler": {"max_evidence_items": 1, "max_evidence_chars": 1000},
            "answer": {"fallback_answer": "I do not know."},
        }

        with self.assertRaises(ValueError):
            Stage1Pipeline(config)

    def test_compiler_memory_records_can_link_to_evidence_rows(self) -> None:
        row_record = MemoryRecord(
            memory_id="mem-row",
            memory_type="fact",
            text="Alex redeemed the coupon at Target.",
            source_ids=("s1:t1",),
            subject="Alex",
            predicate="redeemed at",
            value="Target",
        )
        retrieval_record = MemoryRecord(
            memory_id="mem-retrieval",
            memory_type="fact",
            text="Alex discussed coupons.",
            source_ids=("s1:t0",),
        )
        memory_hits = (
            MemoryHit(record=retrieval_record, score=1.0, rank=1),
        )
        evidence_turns = (
            Turn(
                source_id="s1:t1",
                session_id="s1",
                turn_index=1,
                role="user",
                text="I redeemed the coupon at Target.",
            ),
        )

        row_linked = _compiler_memory_records(
            source="evidence_rows",
            memory_hits=memory_hits,
            built_memory_records=(retrieval_record, row_record),
            evidence_turns=evidence_turns,
        )
        retrieval_only = _compiler_memory_records(
            source="retrieval",
            memory_hits=memory_hits,
            built_memory_records=(retrieval_record, row_record),
            evidence_turns=evidence_turns,
        )
        combined = _compiler_memory_records(
            source="retrieval_and_evidence_rows",
            memory_hits=memory_hits,
            built_memory_records=(retrieval_record, row_record),
            evidence_turns=evidence_turns,
        )

        self.assertEqual([record.memory_id for record in row_linked], ["mem-row"])
        self.assertEqual(
            [record.memory_id for record in retrieval_only],
            ["mem-retrieval"],
        )
        self.assertEqual(
            [record.memory_id for record in combined],
            ["mem-retrieval", "mem-row"],
        )

    def test_build_memory_source_alignment_adds_adjacent_supporting_turn(self) -> None:
        record = MemoryRecord(
            memory_id="mem-followers",
            memory_type="fact",
            text="The user is nearing 1300 Instagram followers.",
            source_ids=("s1:t0",),
            subject="user",
            predicate="is nearing",
            value="1300 Instagram followers",
        )
        store = RawEvidenceStore(
            (
                Turn(
                    source_id="s1:t0",
                    session_id="s1",
                    turn_index=0,
                    role="user",
                    text="Can you help me write an Instagram caption?",
                ),
                Turn(
                    source_id="s1:t1",
                    session_id="s1",
                    turn_index=1,
                    role="assistant",
                    text=(
                        "Congratulations on nearing 1300 followers. "
                        "Here is a caption draft."
                    ),
                ),
            )
        )

        aligned, trace = _align_build_memory_sources(
            (record,),
            store=store,
            window=1,
            max_sources_per_record=3,
            min_score=2.0,
            min_delta=1.5,
        )

        self.assertEqual(aligned[0].source_ids, ("s1:t1", "s1:t0"))
        self.assertEqual(trace["records_seen"], 1)
        self.assertEqual(trace["records_changed"], 1)
        self.assertEqual(trace["sources_added"], 1)

    def test_compiler_memory_record_source_rejects_unknown_value(self) -> None:
        config = {
            "retrieval": {"top_k": 1, "max_top_k": 1},
            "compiler": {
                "max_evidence_items": 1,
                "max_evidence_chars": 1000,
                "memory_record_source": "question_type",
            },
            "answer": {"fallback_answer": "I do not know."},
        }

        with self.assertRaises(ValueError):
            Stage1Pipeline(config)

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

    def test_pipeline_selective_repair_is_traceable_and_counts_in_answer(self) -> None:
        config = {
            "retrieval": {"top_k": 1, "max_top_k": 1, "neighbor_window": 0},
            "compiler": {"max_evidence_items": 1, "max_evidence_chars": 1000},
            "answer": {
                "fallback_answer": "unknown",
                "repair": {
                    "enabled": True,
                    "mode": "null_answerer",
                    "fallback_answer": "jasmine tea",
                    "information_needs": ["fact_lookup", "profile_preference"],
                    "enable_uncertain_trigger": True,
                    "enable_short_list_trigger": False,
                    "enable_temporal_conflict_trigger": False,
                },
            },
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

        self.assertEqual(result["answer"], "jasmine tea")
        self.assertEqual(result["trace"]["answer_draft"]["answer"], "unknown")
        self.assertTrue(result["trace"]["answer_repair"]["triggered"])
        self.assertTrue(result["trace"]["answer_repair"]["applied"])
        self.assertIn(
            "uncertain_or_missing",
            result["trace"]["answer_repair"]["reasons"],
        )
        self.assertEqual(result["trace"]["token_cost"]["query_tokens"], 0)

    def test_pipeline_traces_context_layout_config(self) -> None:
        config = {
            "retrieval": {"top_k": 2, "max_top_k": 2, "neighbor_window": 0},
            "compiler": {
                "max_evidence_items": 2,
                "max_evidence_chars": 2000,
                "prompt_mode": "external_naive",
                "context_layout": "session_thread",
            },
            "answer": {"fallback_answer": "unknown"},
        }
        request = PredictionRequest(
            question="How many items does Alex need to pick up?",
            turns=(
                Turn(
                    source_id="s1:t1",
                    session_id="s1",
                    turn_index=1,
                    role="user",
                    text="Alex needs to pick up boots.",
                ),
                Turn(
                    source_id="s1:t0",
                    session_id="s1",
                    turn_index=0,
                    role="user",
                    text="Alex needs to pick up dry cleaning.",
                ),
            ),
        )

        result = Stage1Pipeline(config).predict(request)

        self.assertEqual(result["trace"]["compiler"]["context_layout"], "session_thread")
        self.assertIn("### Episode 1", result["trace"]["compiled_context"]["prompt"])

    def test_chronological_session_thread_layout_orders_sessions_and_turns(
        self,
    ) -> None:
        compiler = EvidenceCompiler(
            max_evidence_items=3,
            max_evidence_chars=4000,
            context_layout="chronological_session_thread",
            prompt_mode="external_naive",
        )
        route = RouteResult(information_need="temporal_lookup", signals=())
        compiled = compiler.compile(
            question="What is the order of Alex's visits?",
            question_time=None,
            route=route,
            hits=(
                RetrievalHit("new:t1", 1.0, 1, "dense"),
                RetrievalHit("old:t0", 0.9, 2, "dense"),
                RetrievalHit("new:t0", 0.8, 3, "dense"),
            ),
            evidence_turns=(
                Turn(
                    source_id="new:t1",
                    session_id="new",
                    turn_index=1,
                    role="user",
                    text="Alex visited the library later.",
                    timestamp="2024-03-01",
                ),
                Turn(
                    source_id="old:t0",
                    session_id="old",
                    turn_index=0,
                    role="user",
                    text="Alex visited the museum first.",
                    timestamp="2024-01-01",
                ),
                Turn(
                    source_id="new:t0",
                    session_id="new",
                    turn_index=0,
                    role="user",
                    text="Alex visited the park before the library.",
                    timestamp="2024-03-01",
                ),
            ),
        )

        self.assertEqual(
            [row.source_id for row in compiled.evidence_rows],
            ["old:t0", "new:t0", "new:t1"],
        )
        self.assertIn("sessions and turns are shown in chronological order", compiled.prompt)

    def test_pipeline_rejects_inconsistent_answer_output_token_config(self) -> None:
        config = {
            "retrieval": {"top_k": 1, "max_top_k": 1, "neighbor_window": 0},
            "compiler": {"max_evidence_items": 1, "max_evidence_chars": 1000},
            "answer": {
                "mode": "openai_compatible",
                "base_url": "http://127.0.0.1:65535/v1",
                "model": "test-model",
                "temperature": 0.0,
                "max_output_tokens": 32,
                "max_tokens": 16,
                "timeout": 0.01,
            },
        }

        with self.assertRaises(ValueError):
            Stage1Pipeline(config)

    def test_answer_message_text_accepts_reasoning_field(self) -> None:
        self.assertEqual(_message_text({"content": None, "reasoning": "answer"}), "answer")

    def test_json_answer_output_extracts_answer_field(self) -> None:
        raw = '{"reasoning":"supported by memory","answer":"jasmine tea"}'
        self.assertEqual(
            _parse_answer_content(raw, output_format="json_answer"),
            "jasmine tea",
        )

    def test_json_answer_output_salvages_answer_field_from_malformed_json(self) -> None:
        raw = (
            '{"reasoning":"quoted text broke the JSON: "bad quote"",'
            '"answer":"jasmine tea"}'
        )

        self.assertEqual(
            _parse_answer_content(raw, output_format="json_answer"),
            "jasmine tea",
        )

    def test_answer_repair_trigger_detects_uncertain_and_short_collection(self) -> None:
        raw_response = json.dumps(
            {
                "content": json.dumps(
                    {
                        "sufficient": False,
                        "answer_type": "unknown",
                        "missing": "target value",
                        "answer": "unknown",
                    }
                )
            }
        )

        reasons = repair_trigger_reasons(
            question="What events has Alex attended?",
            route_information_need="fact_lookup",
            draft_answer="unknown",
            raw_response=raw_response,
            enable_uncertain_trigger=True,
            enable_short_list_trigger=True,
            enable_temporal_conflict_trigger=True,
        )

        self.assertIn("uncertain_or_missing", reasons)

        gated_reasons = repair_trigger_reasons(
            question="What events has Alex attended?",
            route_information_need="fact_lookup",
            draft_answer="unknown",
            raw_response=raw_response,
            enable_uncertain_trigger=True,
            enable_short_list_trigger=False,
            enable_temporal_conflict_trigger=False,
            uncertain_min_support_items=1,
        )

        supported_raw_response = json.dumps(
            {
                "content": json.dumps(
                    {
                        "sufficient": False,
                        "answer_type": "unknown",
                        "missing": "target value",
                        "evidence_report": [
                            {
                                "memory": "Memory 1",
                                "status": "support",
                                "value": "conference",
                            }
                        ],
                        "answer": "unknown",
                    }
                )
            }
        )
        supported_reasons = repair_trigger_reasons(
            question="What events has Alex attended?",
            route_information_need="fact_lookup",
            draft_answer="unknown",
            raw_response=supported_raw_response,
            enable_uncertain_trigger=True,
            enable_short_list_trigger=False,
            enable_temporal_conflict_trigger=False,
            uncertain_min_support_items=1,
        )

        self.assertNotIn("uncertain_or_missing", gated_reasons)
        self.assertIn("uncertain_or_missing", supported_reasons)

        short_reasons = repair_trigger_reasons(
            question="What events has Alex attended?",
            route_information_need="fact_lookup",
            draft_answer="conference",
            raw_response=json.dumps(
                {"content": json.dumps({"sufficient": True, "answer_type": "list"})}
            ),
            enable_uncertain_trigger=True,
            enable_short_list_trigger=True,
            enable_temporal_conflict_trigger=True,
        )

        self.assertIn("short_collection_answer", short_reasons)

    def test_answer_repair_profile_preference_trigger_is_opt_in(self) -> None:
        disabled_reasons = repair_trigger_reasons(
            question="What laptop should I buy next?",
            route_information_need="profile_preference",
            draft_answer="There is not enough information.",
            raw_response=json.dumps({"content": json.dumps({"answer": "unknown"})}),
            enable_uncertain_trigger=False,
            enable_short_list_trigger=False,
            enable_temporal_conflict_trigger=False,
        )
        enabled_reasons = repair_trigger_reasons(
            question="What laptop should I buy next?",
            route_information_need="profile_preference",
            draft_answer="There is not enough information.",
            raw_response=json.dumps({"content": json.dumps({"answer": "unknown"})}),
            enable_uncertain_trigger=False,
            enable_short_list_trigger=False,
            enable_temporal_conflict_trigger=False,
            enable_profile_preference_trigger=True,
        )

        self.assertNotIn("profile_preference_review", disabled_reasons)
        self.assertIn("profile_preference_review", enabled_reasons)

    def test_answer_repair_prompt_uses_runtime_context_and_draft(self) -> None:
        context = CompiledContext(
            question="What tea does Alex prefer?",
            question_time="2026-01-01",
            route=RouteResult(information_need="fact_lookup", signals=()),
            evidence_rows=(
                EvidenceRow(
                    source_id="s1:t1",
                    session_id="s1",
                    turn_index=1,
                    role="user",
                    text="Alex prefers jasmine tea.",
                    timestamp="2025-12-31",
                    retrieval_rank=1,
                    retrieval_score=1.0,
                ),
            ),
            prompt="original prompt",
            context_chars=0,
        )
        draft = AnswerResult(
            answer="unknown",
            model="draft",
            token_usage=TokenUsage(query_tokens=3),
            raw_response=json.dumps({"content": '{"answer":"unknown"}'}),
        )

        prompt, context_chars = build_repair_prompt(
            compiled=context,
            draft=draft,
            reasons=("uncertain_or_missing",),
            max_context_chars=1000,
            max_row_text_chars=200,
        )

        self.assertIn("What tea does Alex prefer?", prompt)
        self.assertIn("Draft Answer:", prompt)
        self.assertIn("Alex prefers jasmine tea.", prompt)
        self.assertGreater(context_chars, 0)

    def test_answer_repair_prompt_adds_profile_preference_rules(self) -> None:
        context = CompiledContext(
            question="What laptop should Alex buy next?",
            question_time="2026-01-01",
            route=RouteResult(information_need="profile_preference", signals=()),
            evidence_rows=(
                EvidenceRow(
                    source_id="s1:t1",
                    session_id="s1",
                    turn_index=1,
                    role="user",
                    text="Alex wants a lightweight laptop for travel.",
                    timestamp="2025-12-31",
                    retrieval_rank=1,
                    retrieval_score=1.0,
                ),
            ),
            prompt="original prompt",
            context_chars=0,
        )
        draft = AnswerResult(
            answer="There is not enough information.",
            model="draft",
            token_usage=TokenUsage(query_tokens=3),
            raw_response=json.dumps({"content": '{"answer":"unknown"}'}),
        )

        prompt, _ = build_repair_prompt(
            compiled=context,
            draft=draft,
            reasons=("profile_preference_review",),
            max_context_chars=1000,
            max_row_text_chars=200,
        )

        self.assertIn("extract user-specific anchors", prompt)
        self.assertIn("no-new-names rule", prompt)
        self.assertIn("unless that exact name appears verbatim", prompt)
        self.assertIn("Alex wants a lightweight laptop for travel.", prompt)

    def test_raw_response_content_extracts_answerer_content(self) -> None:
        raw_response = json.dumps(
            {
                "content": '{"answer":"jasmine tea"}',
                "usage": {"total_tokens": 42},
            }
        )

        self.assertEqual(raw_response_content(raw_response), '{"answer":"jasmine tea"}')

    def test_structured_answer_finalizer_repairs_count_mismatch(self) -> None:
        content = json.dumps(
            {
                "sufficient": True,
                "evidence_items": [
                    {
                        "canonical_item": "Tamiya Spitfire",
                        "include": True,
                        "reason": "in scope",
                    },
                    {
                        "canonical_item": "Bandai X-wing",
                        "include": True,
                        "reason": "in scope",
                    },
                    {
                        "canonical_item": "Revell Mustang",
                        "include": True,
                        "reason": "in scope",
                    },
                ],
                "answer": "2",
            }
        )
        raw_response = json.dumps({"content": content})

        finalization = finalize_structured_answer(
            question="How many model kits did Alex mention?",
            draft_answer="2",
            raw_response=raw_response,
            enable_count_correction=True,
        )

        self.assertTrue(finalization.applied)
        self.assertEqual(finalization.expected_value, "3")
        self.assertIn("3:", finalization.answer)
        self.assertIn("Tamiya Spitfire", finalization.answer)

    def test_structured_answer_finalizer_does_not_count_by_default(self) -> None:
        content = json.dumps(
            {
                "sufficient": True,
                "evidence_items": [
                    {"canonical_item": "first kit", "include": True},
                    {"canonical_item": "second kit", "include": True},
                ],
                "answer": "1",
            }
        )
        raw_response = json.dumps({"content": content})

        finalization = finalize_structured_answer(
            question="How many model kits did Alex mention?",
            draft_answer="1",
            raw_response=raw_response,
        )

        self.assertFalse(finalization.applied)
        self.assertEqual(finalization.answer, "1")

    def test_evidence_report_count_increment_finalizer_is_explicit(self) -> None:
        content = json.dumps(
            {
                "sufficient": True,
                "answer_type": "count",
                "evidence_report": [
                    {
                        "status": "support",
                        "canonical_item": "snake plant",
                        "count_increment": "1",
                    },
                    {
                        "status": "support",
                        "canonical_item": "peace lily and succulent",
                        "count_increment": "2",
                    },
                ],
                "answer": "2",
            }
        )
        raw_response = json.dumps({"content": content})

        finalization = finalize_structured_answer(
            question="How many plants did Alex acquire last month?",
            draft_answer="2",
            raw_response=raw_response,
            enable_evidence_report_count_correction=True,
        )

        self.assertTrue(finalization.applied)
        self.assertEqual(
            finalization.reason, "evidence_report_count_increment_consistency"
        )
        self.assertEqual(finalization.expected_value, "3")
        self.assertIn("3:", finalization.answer)
        self.assertIn("snake plant", finalization.answer)

    def test_evidence_report_count_increment_finalizer_ignores_legacy_value(
        self,
    ) -> None:
        content = json.dumps(
            {
                "sufficient": True,
                "answer_type": "count",
                "evidence_report": [
                    {
                        "status": "support",
                        "canonical_item": "small tank",
                        "value": "5-gallon tank",
                    },
                    {
                        "status": "support",
                        "canonical_item": "large tank",
                        "value": "20-gallon tank",
                    },
                ],
                "answer": "2",
            }
        )
        raw_response = json.dumps({"content": content})

        finalization = finalize_structured_answer(
            question="How many tanks does Alex have?",
            draft_answer="2",
            raw_response=raw_response,
            enable_evidence_report_count_correction=True,
        )

        self.assertFalse(finalization.applied)
        self.assertEqual(finalization.reason, "no_structured_evidence_items")

    def test_evidence_report_count_increment_finalizer_skips_duration_counts(
        self,
    ) -> None:
        content = json.dumps(
            {
                "sufficient": True,
                "answer_type": "count",
                "evidence_report": [
                    {"status": "support", "count_increment": "1"},
                    {"status": "support", "count_increment": "1"},
                ],
                "answer": "1 week",
            }
        )
        raw_response = json.dumps({"content": content})

        finalization = finalize_structured_answer(
            question="How many weeks did it take Alex to finish the movies?",
            draft_answer="1 week",
            raw_response=raw_response,
            enable_evidence_report_count_correction=True,
        )

        self.assertFalse(finalization.applied)

    def test_count_answer_detail_finalizer_expands_bare_count(self) -> None:
        content = json.dumps(
            {
                "sufficient": True,
                "answer_type": "count",
                "evidence_report": [
                    {"status": "support", "value": "Dr. Lee"},
                    {"status": "support", "value": "Dr. Patel"},
                    {"status": "support", "value": "Dr. Smith"},
                ],
                "answer": "3",
            }
        )
        raw_response = json.dumps({"content": content})

        finalization = finalize_structured_answer(
            question="How many different doctors did Alex visit?",
            draft_answer="3",
            raw_response=raw_response,
            enable_count_answer_detail=True,
        )

        self.assertTrue(finalization.applied)
        self.assertEqual(finalization.reason, "evidence_report_count_answer_detail")
        self.assertIn("3 different doctors:", finalization.answer)
        self.assertIn("Dr. Lee", finalization.answer)

    def test_count_answer_detail_finalizer_ignores_scalar_values(self) -> None:
        content = json.dumps(
            {
                "sufficient": True,
                "answer_type": "count",
                "evidence_report": [
                    {"status": "support", "value": "125"},
                    {"status": "support", "value": "125"},
                ],
                "answer": "125",
            }
        )
        raw_response = json.dumps({"content": content})

        finalization = finalize_structured_answer(
            question="How many stars does Alex need?",
            draft_answer="125",
            raw_response=raw_response,
            enable_count_answer_detail=True,
        )

        self.assertFalse(finalization.applied)

    def test_average_calculation_finalizer_uses_evidence_report_values(self) -> None:
        content = json.dumps(
            {
                "sufficient": True,
                "answer_type": "fact",
                "evidence_report": [
                    {"status": "support", "slot": "undergraduate GPA", "value": "3.86"},
                    {"status": "support", "slot": "graduate GPA", "value": "3.8"},
                ],
                "answer": "The undergraduate GPA is 3.86 and graduate GPA is 3.8.",
            }
        )
        raw_response = json.dumps({"content": content})

        finalization = finalize_structured_answer(
            question="What is the average GPA of my undergraduate and graduate studies?",
            draft_answer="The undergraduate GPA is 3.86 and graduate GPA is 3.8.",
            raw_response=raw_response,
            enable_average_calculation=True,
        )

        self.assertTrue(finalization.applied)
        self.assertEqual(finalization.reason, "evidence_report_average_calculation")
        self.assertEqual(finalization.expected_value, "3.83")
        self.assertIn("3.83 average", finalization.answer)

    def test_average_calculation_finalizer_skips_average_comparison(self) -> None:
        content = json.dumps(
            {
                "sufficient": True,
                "answer_type": "fact",
                "evidence_report": [
                    {"status": "support", "value": "29.5"},
                    {"status": "support", "value": "32"},
                ],
                "answer": "2.5 years",
            }
        )
        raw_response = json.dumps({"content": content})

        finalization = finalize_structured_answer(
            question="How much older am I than the average age of employees?",
            draft_answer="2.5 years",
            raw_response=raw_response,
            enable_average_calculation=True,
        )

        self.assertFalse(finalization.applied)

    def test_money_difference_finalizer_uses_two_supported_amounts(self) -> None:
        content = json.dumps(
            {
                "sufficient": False,
                "answer_type": "fact",
                "evidence_report": [
                    {"status": "support", "value": "$30 per night"},
                    {"status": "support", "value": "over $300 per night"},
                ],
                "answer": "The provided information is not enough.",
            }
        )
        raw_response = json.dumps({"content": content})

        finalization = finalize_structured_answer(
            question="How much more did Alex spend in Hawaii compared to Tokyo?",
            draft_answer="The provided information is not enough.",
            raw_response=raw_response,
            enable_money_difference_calculation=True,
        )

        self.assertTrue(finalization.applied)
        self.assertEqual(finalization.reason, "evidence_report_money_difference")
        self.assertEqual(finalization.answer, "$270")

    def test_date_endpoint_duration_finalizer_uses_two_supported_dates(self) -> None:
        content = json.dumps(
            {
                "sufficient": True,
                "answer_type": "duration",
                "evidence_report": [
                    {"status": "support", "value": "2023-05-05"},
                    {"status": "support", "value": "2023-04-26"},
                ],
                "answer": "19 days",
            }
        )
        raw_response = json.dumps({"content": content})

        finalization = finalize_structured_answer(
            question="How long had Alex been using the rug when he rearranged the room?",
            draft_answer="19 days",
            raw_response=raw_response,
            enable_date_endpoint_duration_calculation=True,
        )

        self.assertTrue(finalization.applied)
        self.assertEqual(
            finalization.reason,
            "evidence_report_date_endpoint_duration",
        )
        self.assertEqual(finalization.answer, "9 days")

    def test_date_endpoint_duration_finalizer_skips_refusal(self) -> None:
        content = json.dumps(
            {
                "sufficient": True,
                "answer_type": "duration",
                "evidence_report": [
                    {"status": "support", "value": "2023-05-05"},
                    {"status": "support", "value": "2023-04-26"},
                ],
                "answer": "The provided information is not enough.",
            }
        )
        raw_response = json.dumps({"content": content})

        finalization = finalize_structured_answer(
            question="How many days before buying the iPad did Alex attend the market?",
            draft_answer="The provided information is not enough.",
            raw_response=raw_response,
            enable_date_endpoint_duration_calculation=True,
        )

        self.assertFalse(finalization.applied)

    def test_relative_time_finalizer_is_disabled_by_default(self) -> None:
        content = json.dumps(
            {
                "sufficient": True,
                "answer_type": "date",
                "evidence_report": [
                    {
                        "status": "support",
                        "mention_time": "2023-07-15",
                        "time_phrase": "Last Fri",
                    }
                ],
                "answer": "2023-07-15",
            }
        )
        raw_response = json.dumps({"content": content})

        finalization = finalize_structured_answer(
            question="When did Melanie go to the pottery workshop?",
            draft_answer="2023-07-15",
            raw_response=raw_response,
        )

        self.assertFalse(finalization.applied)
        self.assertEqual(finalization.answer, "2023-07-15")

    def test_relative_time_finalizer_resolves_last_weekday(self) -> None:
        content = json.dumps(
            {
                "sufficient": True,
                "answer_type": "date",
                "evidence_report": [
                    {
                        "status": "support",
                        "mention_time": "2023-07-15",
                        "time_phrase": "Last Fri",
                    }
                ],
                "answer": "2023-07-15",
            }
        )
        raw_response = json.dumps({"content": content})

        finalization = finalize_structured_answer(
            question="When did Melanie go to the pottery workshop?",
            draft_answer="2023-07-15",
            raw_response=raw_response,
            enable_relative_time_calculation=True,
        )

        self.assertTrue(finalization.applied)
        self.assertEqual(
            finalization.reason,
            "evidence_report_relative_time_calculation",
        )
        self.assertEqual(finalization.answer, "2023-07-14")

    def test_relative_time_finalizer_resolves_yesterday(self) -> None:
        content = json.dumps(
            {
                "sufficient": True,
                "answer_type": "date",
                "evidence_report": [
                    {
                        "status": "support",
                        "mention_time": "2023-06-21",
                        "time_phrase": "yesterday",
                    }
                ],
                "answer": "2023-06-21",
            }
        )
        raw_response = json.dumps({"content": content})

        finalization = finalize_structured_answer(
            question="What date did Alex visit the florist?",
            draft_answer="2023-06-21",
            raw_response=raw_response,
            enable_relative_time_calculation=True,
        )

        self.assertTrue(finalization.applied)
        self.assertEqual(finalization.answer, "2023-06-20")

    def test_relative_time_finalizer_resolves_day_after_tomorrow(self) -> None:
        content = json.dumps(
            {
                "sufficient": True,
                "answer_type": "date",
                "evidence_report": [
                    {
                        "status": "support",
                        "mention_time": "2022-07-09",
                        "time_phrase": "the day after tomorrow",
                    }
                ],
                "answer": "2022-07-10",
            }
        )
        raw_response = json.dumps({"content": content})

        finalization = finalize_structured_answer(
            question="When did James depart for his trip?",
            draft_answer="2022-07-10",
            raw_response=raw_response,
            enable_relative_time_calculation=True,
        )

        self.assertTrue(finalization.applied)
        self.assertEqual(finalization.answer, "2022-07-11")

    def test_relative_time_finalizer_skips_conflicting_candidates(self) -> None:
        content = json.dumps(
            {
                "sufficient": True,
                "answer_type": "date",
                "evidence_report": [
                    {
                        "status": "support",
                        "mention_time": "2023-10-20",
                        "time_phrase": "yesterday",
                    },
                    {
                        "status": "support",
                        "mention_time": "2023-10-20",
                        "time_phrase": "tomorrow",
                    },
                ],
                "answer": "2023-10-20",
            }
        )
        raw_response = json.dumps({"content": content})

        finalization = finalize_structured_answer(
            question="When did Priya take the trip?",
            draft_answer="2023-10-20",
            raw_response=raw_response,
            enable_relative_time_calculation=True,
        )

        self.assertFalse(finalization.applied)
        self.assertEqual(finalization.answer, "2023-10-20")

    def test_relative_time_finalizer_skips_week_phrase_for_exact_draft(self) -> None:
        content = json.dumps(
            {
                "sufficient": True,
                "answer_type": "date",
                "evidence_report": [
                    {
                        "status": "support",
                        "mention_time": "2023-05-16",
                        "time_phrase": "last week",
                    }
                ],
                "answer": "2023-05-01",
            }
        )
        raw_response = json.dumps({"content": content})

        finalization = finalize_structured_answer(
            question="When did Dave start the shop?",
            draft_answer="2023-05-01",
            raw_response=raw_response,
            enable_relative_time_calculation=True,
        )

        self.assertFalse(finalization.applied)
        self.assertEqual(finalization.answer, "2023-05-01")

    def test_relative_time_finalizer_resolves_week_before_to_iso_range(self) -> None:
        content = json.dumps(
            {
                "sufficient": True,
                "answer_type": "date",
                "evidence_report": [
                    {
                        "status": "support",
                        "mention_time": "2023-06-09",
                        "time_phrase": "the week before",
                    }
                ],
                "answer": "The week before 9 June 2023",
            }
        )
        raw_response = json.dumps({"content": content})

        finalization = finalize_structured_answer(
            question="When did Alex go hiking?",
            draft_answer="The week before 9 June 2023",
            raw_response=raw_response,
            enable_relative_time_calculation=True,
        )

        self.assertTrue(finalization.applied)
        self.assertEqual(finalization.answer, "2023-06-02 to 2023-06-08")

    def test_relative_time_finalizer_keeps_equivalent_iso_range(self) -> None:
        content = json.dumps(
            {
                "sufficient": True,
                "answer_type": "date",
                "evidence_report": [
                    {
                        "status": "support",
                        "mention_time": "2023-06-09",
                        "time_phrase": "the week before",
                    }
                ],
                "answer": "2023-06-02 to 2023-06-08",
            }
        )
        raw_response = json.dumps({"content": content})

        finalization = finalize_structured_answer(
            question="When did Alex go hiking?",
            draft_answer="2023-06-02 to 2023-06-08",
            raw_response=raw_response,
            enable_relative_time_calculation=True,
        )

        self.assertFalse(finalization.applied)
        self.assertEqual(finalization.answer, "2023-06-02 to 2023-06-08")

    def test_relative_time_finalizer_skips_duration_question(self) -> None:
        content = json.dumps(
            {
                "sufficient": True,
                "answer_type": "date",
                "evidence_report": [
                    {
                        "status": "support",
                        "mention_time": "2023-06-21",
                        "time_phrase": "yesterday",
                    }
                ],
                "answer": "2023-06-21",
            }
        )
        raw_response = json.dumps({"content": content})

        finalization = finalize_structured_answer(
            question="How long after the florist visit did Alex buy the vase?",
            draft_answer="2023-06-21",
            raw_response=raw_response,
            enable_relative_time_calculation=True,
        )

        self.assertFalse(finalization.applied)
        self.assertEqual(finalization.answer, "2023-06-21")

    def test_structured_answer_finalizer_repairs_money_sum_mismatch(self) -> None:
        content = json.dumps(
            {
                "sufficient": True,
                "evidence_items": [
                    {
                        "canonical_item": "bike chain",
                        "value": "$25",
                        "include": True,
                        "reason": "expense",
                    },
                    {
                        "canonical_item": "tune-up",
                        "value": "$65",
                        "include": True,
                        "reason": "expense",
                    },
                    {
                        "canonical_item": "rack",
                        "value": "$95",
                        "include": True,
                        "reason": "expense",
                    },
                ],
                "answer": "$65",
            }
        )
        raw_response = json.dumps({"content": content})

        finalization = finalize_structured_answer(
            question="How much did Alex spend on bike expenses in total?",
            draft_answer="$65",
            raw_response=raw_response,
        )

        self.assertTrue(finalization.applied)
        self.assertEqual(finalization.expected_value, "185")
        self.assertIn("$185 total", finalization.answer)

    def test_structured_answer_finalizer_noops_without_content(self) -> None:
        finalization = finalize_structured_answer(
            question="How many model kits did Alex mention?",
            draft_answer="2",
            raw_response='{"usage":{"total_tokens":42}}',
        )

        self.assertFalse(finalization.applied)
        self.assertEqual(finalization.answer, "2")

    def test_missing_detail_finalizer_is_disabled_by_default(self) -> None:
        content = json.dumps(
            {
                "sufficient": False,
                "missing": "no hamster name appears in the memory context",
                "answer": "The provided information is not enough.",
            }
        )
        raw_response = json.dumps({"content": content})

        finalization = finalize_structured_answer(
            question="What is my hamster's name?",
            draft_answer="The provided information is not enough.",
            raw_response=raw_response,
        )

        self.assertFalse(finalization.applied)
        self.assertEqual(finalization.reason, "model_marked_insufficient")

    def test_missing_detail_finalizer_expands_short_refusal_when_enabled(self) -> None:
        content = json.dumps(
            {
                "sufficient": False,
                "missing": "no hamster name appears in the memory context",
                "answer": "The provided information is not enough.",
            }
        )
        raw_response = json.dumps({"content": content})

        finalization = finalize_structured_answer(
            question="What is my hamster's name?",
            draft_answer="The provided information is not enough.",
            raw_response=raw_response,
            enable_missing_detail=True,
        )

        self.assertTrue(finalization.applied)
        self.assertEqual(finalization.reason, "missing_detail_from_structured_answer")
        self.assertIn("no hamster name", finalization.answer)

    def test_answer_finalizer_rounds_decimal_week_duration_when_enabled(self) -> None:
        finalization = finalize_structured_answer(
            question="How many weeks passed between Maria adopting Coco and Shadow?",
            draft_answer="2.29 weeks",
            raw_response=None,
            enable_duration_rounding_correction=True,
        )

        self.assertTrue(finalization.applied)
        self.assertEqual(finalization.reason, "duration_decimal_rounding")
        self.assertEqual(finalization.answer, "2 weeks")

    def test_answer_finalizer_does_not_round_duration_by_default(self) -> None:
        finalization = finalize_structured_answer(
            question="How many weeks passed between Maria adopting Coco and Shadow?",
            draft_answer="2.29 weeks",
            raw_response=None,
        )

        self.assertFalse(finalization.applied)
        self.assertEqual(finalization.answer, "2.29 weeks")

    def test_cached_answerer_reuses_prompt_and_counts_cached_tokens(self) -> None:
        compiler = EvidenceCompiler(max_evidence_items=1, max_evidence_chars=1000)
        route = RouteResult(information_need="fact_lookup", signals=())
        context = compiler.compile(
            question="What tea does Alex prefer?",
            question_time=None,
            route=route,
            hits=(RetrievalHit("s1:t0", 1.0, 1, "lexical_bm25"),),
            evidence_turns=(
                Turn(
                    source_id="s1:t0",
                    session_id="s1",
                    turn_index=0,
                    role="user",
                    text="Alex prefers jasmine tea.",
                ),
            ),
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            inner = _CountingAnswerer()
            answerer = CachedAnswerer(
                inner,
                cache_path=str(Path(tmpdir) / "answer.sqlite"),
                namespace="test",
            )

            first = answerer.answer(context)
            second = answerer.answer(context)

        self.assertEqual(first.answer, "jasmine tea")
        self.assertEqual(second.answer, "jasmine tea")
        self.assertEqual(first.token_usage.query_tokens, 42)
        self.assertEqual(second.token_usage.query_tokens, 42)
        self.assertEqual(inner.calls, 1)
        self.assertEqual(
            answerer.stats().to_dict(),
            {"hits": 1, "misses": 1, "writes": 1},
        )

    def test_cached_answerer_preserves_cached_answer_on_hits(self) -> None:
        compiler = EvidenceCompiler(max_evidence_items=1, max_evidence_chars=1000)
        route = RouteResult(information_need="fact_lookup", signals=())
        context = compiler.compile(
            question="What tea does Alex prefer?",
            question_time=None,
            route=route,
            hits=(RetrievalHit("s1:t0", 1.0, 1, "lexical_bm25"),),
            evidence_turns=(
                Turn(
                    source_id="s1:t0",
                    session_id="s1",
                    turn_index=0,
                    role="user",
                    text="Alex prefers jasmine tea.",
                ),
            ),
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            inner = _MalformedJsonAnswerer()
            answerer = CachedAnswerer(
                inner,
                cache_path=str(Path(tmpdir) / "answer.sqlite"),
                namespace="test",
                output_format="json_answer",
            )

            first = answerer.answer(context)
            second = answerer.answer(context)

        expected_answer = (
            '{"reasoning":"quoted text broke the JSON: "bad quote"",'
            '"answer":"jasmine tea"}'
        )
        self.assertEqual(first.answer, expected_answer)
        self.assertEqual(second.answer, first.answer)
        self.assertEqual(inner.calls, 1)

    def test_cached_answerer_repairs_structured_json_answer_residue(self) -> None:
        compiler = EvidenceCompiler(max_evidence_items=1, max_evidence_chars=1000)
        route = RouteResult(information_need="fact_lookup", signals=())
        context = compiler.compile(
            question="What tea does Alex prefer?",
            question_time=None,
            route=route,
            hits=(RetrievalHit("s1:t0", 1.0, 1, "lexical_bm25"),),
            evidence_turns=(
                Turn(
                    source_id="s1:t0",
                    session_id="s1",
                    turn_index=0,
                    role="user",
                    text="Alex prefers jasmine tea.",
                ),
            ),
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            inner = _StructuredJsonResidueAnswerer()
            answerer = CachedAnswerer(
                inner,
                cache_path=str(Path(tmpdir) / "answer.sqlite"),
                namespace="test",
                output_format="json_answer",
            )

            first = answerer.answer(context)
            second = answerer.answer(context)

        self.assertEqual(first.answer, "jasmine tea")
        self.assertEqual(second.answer, "jasmine tea")
        self.assertEqual(inner.calls, 1)

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

    def test_raw_context_only_prompt_excludes_build_memory_view(self) -> None:
        config = {
            "retrieval": {"top_k": 1, "max_top_k": 1, "neighbor_window": 0},
            "compiler": {
                "max_evidence_items": 1,
                "max_evidence_chars": 1000,
                "prompt_mode": "raw_context_only",
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

        self.assertIn("Memory context:", prompt)
        self.assertIn("shortest direct answer", prompt)
        self.assertIn("Return only the final answer", prompt)
        self.assertNotIn("Build-stage typed memory view", prompt)
        self.assertNotIn("Information need:", prompt)

    def test_external_naive_prompt_matches_json_answer_contract(self) -> None:
        config = {
            "retrieval": {"top_k": 1, "max_top_k": 1, "neighbor_window": 0},
            "compiler": {
                "max_evidence_items": 1,
                "max_evidence_chars": 1000,
                "prompt_mode": "external_naive",
            },
            "answer": {"fallback_answer": "I do not know."},
        }
        request = PredictionRequest(
            question="What tea does Alex prefer?",
            question_time="2024-01-02",
            turns=(
                Turn(
                    source_id="s1:t1",
                    session_id="s1",
                    turn_index=1,
                    role="user",
                    text="Alex prefers jasmine tea.",
                    timestamp="2024-01-01",
                ),
            ),
        )

        result = Stage1Pipeline(config).predict(request)
        prompt = result["trace"]["compiled_context"]["prompt"]

        self.assertIn("Current Date: 2024-01-02", prompt)
        self.assertIn("Memory Context:", prompt)
        self.assertIn("### Memory 1", prompt)
        self.assertIn("Date: 2024-01-01", prompt)
        self.assertIn('"answer": "concise answer"', prompt)
        self.assertNotIn("Build-stage typed memory view", prompt)

    def test_structured_answer_contract_is_route_scoped(self) -> None:
        compiler = EvidenceCompiler(
            max_evidence_items=1,
            max_evidence_chars=4000,
            prompt_mode="external_naive",
            structured_answer_contract=True,
            structured_answer_contract_information_needs=("list_count",),
            structured_answer_contract_max_items=5,
        )
        turns = (
            Turn(
                source_id="s1:t0",
                session_id="s1",
                turn_index=0,
                role="user",
                text="Alex bought a Tamiya Spitfire model kit.",
                timestamp="2024-01-01",
            ),
        )

        fact_context = compiler.compile(
            question="Which model kit did Alex buy?",
            question_time=None,
            route=RouteResult(information_need="fact_lookup", signals=()),
            hits=(),
            evidence_turns=turns,
        )
        list_context = compiler.compile(
            question="How many model kits did Alex buy?",
            question_time=None,
            route=RouteResult(information_need="list_count", signals=("list_or_count",)),
            hits=(),
            evidence_turns=turns,
        )

        self.assertNotIn('"evidence_items"', fact_context.prompt)
        self.assertIn('"evidence_items"', list_context.prompt)
        self.assertIn("Use at most 5 evidence_items", list_context.prompt)

    def test_operation_workpad_keeps_external_naive_output_schema(self) -> None:
        compiler = EvidenceCompiler(
            max_evidence_items=1,
            max_evidence_chars=4000,
            prompt_mode="external_naive",
            operation_workpad=True,
            operation_workpad_information_needs=("list_count",),
        )
        turns = (
            Turn(
                source_id="s1:t0",
                session_id="s1",
                turn_index=0,
                role="user",
                text="Alex bought a Tamiya Spitfire model kit.",
                timestamp="2024-01-01",
            ),
        )

        fact_context = compiler.compile(
            question="Which model kit did Alex buy?",
            question_time=None,
            route=RouteResult(information_need="fact_lookup", signals=()),
            hits=(),
            evidence_turns=turns,
        )
        list_context = compiler.compile(
            question="How many model kits did Alex buy?",
            question_time=None,
            route=RouteResult(information_need="list_count", signals=("list_or_count",)),
            hits=(),
            evidence_turns=turns,
        )

        self.assertNotIn("Private Operation Discipline", fact_context.prompt)
        self.assertIn("Private Operation Discipline", list_context.prompt)
        self.assertNotIn('"evidence_items"', list_context.prompt)
        self.assertIn('"answer": "concise answer"', list_context.prompt)

    def test_operation_workpad_question_gate_allows_fact_operations_only(self) -> None:
        compiler = EvidenceCompiler(
            max_evidence_items=1,
            max_evidence_chars=4000,
            prompt_mode="external_naive",
            operation_workpad=True,
            operation_workpad_information_needs=("fact_lookup", "list_count"),
            operation_workpad_question_gate=True,
        )
        turns = (
            Turn(
                source_id="s1:t0",
                session_id="s1",
                turn_index=0,
                role="user",
                text="Alex spent $20 on tea and $15 on coffee.",
                timestamp="2024-01-01",
            ),
        )

        ordinary_fact = compiler.compile(
            question="Where did Alex buy coffee?",
            question_time=None,
            route=RouteResult(information_need="fact_lookup", signals=()),
            hits=(),
            evidence_turns=turns,
        )
        operation_fact = compiler.compile(
            question="What is the total amount Alex spent on tea and coffee?",
            question_time=None,
            route=RouteResult(information_need="fact_lookup", signals=()),
            hits=(),
            evidence_turns=turns,
        )
        list_context = compiler.compile(
            question="How many drinks did Alex buy?",
            question_time=None,
            route=RouteResult(information_need="list_count", signals=("list_or_count",)),
            hits=(),
            evidence_turns=turns,
        )

        self.assertNotIn("Private Operation Discipline", ordinary_fact.prompt)
        self.assertIn("Private Operation Discipline", operation_fact.prompt)
        self.assertIn("Verify arithmetic", operation_fact.prompt)
        self.assertIn("Private Operation Discipline", list_context.prompt)

    def test_operation_workpad_can_pair_with_evidence_report(self) -> None:
        compiler = EvidenceCompiler(
            max_evidence_items=1,
            max_evidence_chars=4000,
            prompt_mode="external_naive",
            evidence_report_contract=True,
            evidence_report_information_needs=("list_count",),
            operation_workpad=True,
            operation_workpad_information_needs=("list_count",),
        )
        turns = (
            Turn(
                source_id="s1:t0",
                session_id="s1",
                turn_index=0,
                role="user",
                text="Alex completed one project and is currently leading another.",
                timestamp="2024-01-01",
            ),
        )

        context = compiler.compile(
            question="How many projects has Alex led or is currently leading?",
            question_time=None,
            route=RouteResult(information_need="list_count", signals=("list_or_count",)),
            hits=(),
            evidence_turns=turns,
        )

        self.assertIn("Private Operation Discipline", context.prompt)
        self.assertIn(
            "include candidates satisfying any requested alternative",
            context.prompt,
        )
        self.assertIn('"evidence_report"', context.prompt)
        self.assertNotIn('"evidence_items"', context.prompt)

    def test_evidence_report_contract_is_generic_and_route_scoped(self) -> None:
        compiler = EvidenceCompiler(
            max_evidence_items=1,
            max_evidence_chars=4000,
            prompt_mode="external_naive",
            evidence_report_contract=True,
            evidence_report_information_needs=("fact_lookup",),
            evidence_report_max_items=3,
        )
        turns = (
            Turn(
                source_id="s1:t0",
                session_id="s1",
                turn_index=0,
                role="user",
                text="Alex uses Spotify for music streaming.",
                timestamp="2024-01-01",
            ),
        )

        fact_context = compiler.compile(
            question="Which music streaming service does Alex use?",
            question_time=None,
            route=RouteResult(information_need="fact_lookup", signals=()),
            hits=(),
            evidence_turns=turns,
        )
        list_context = compiler.compile(
            question="How many music services does Alex use?",
            question_time=None,
            route=RouteResult(information_need="list_count", signals=("list_or_count",)),
            hits=(),
            evidence_turns=turns,
        )

        self.assertIn('"evidence_report"', fact_context.prompt)
        self.assertIn("Use at most 3 evidence_report items", fact_context.prompt)
        self.assertIn("match the requested slot exactly", fact_context.prompt)
        self.assertNotIn("question_type", fact_context.prompt)
        self.assertNotIn('"evidence_report"', list_context.prompt)
        self.assertIn('"answer": "concise answer"', fact_context.prompt)

    def test_external_naive_structured_guide_keeps_cache_layout(self) -> None:
        compiler = EvidenceCompiler(
            max_evidence_items=1,
            max_evidence_chars=4000,
            prompt_mode="external_naive",
            structured_guide=True,
            evidence_report_contract=True,
            evidence_report_information_needs=("fact_lookup",),
            operation_workpad=False,
            candidate_guide=False,
            final_answer_checklist=False,
            aggregation_report_contract=False,
        )
        context = compiler.compile(
            question="Which music streaming service does Alex use?",
            question_time=None,
            route=RouteResult(information_need="fact_lookup", signals=()),
            hits=(),
            evidence_turns=(
                Turn(
                    source_id="s1:t0",
                    session_id="s1",
                    turn_index=0,
                    role="user",
                    text="Alex uses Spotify for music streaming.",
                    timestamp="2024-01-01",
                ),
            ),
        )

        self.assertIn("Structured Evidence Guide:", context.prompt)
        self.assertIn('"evidence_report"', context.prompt)
        self.assertNotIn("Candidate Evidence Map:", context.prompt)
        self.assertNotIn("Private Operation Discipline:", context.prompt)
        self.assertNotIn("Final Answer Checklist:", context.prompt)
        self.assertNotIn('"calculation"', context.prompt)
        self.assertIn("\n\n\nMemory Context:", context.prompt)
        self.assertNotIn("\n\n\n\nMemory Context:", context.prompt)

    def test_external_naive_memory_context_spacing_is_configurable(self) -> None:
        compiler = EvidenceCompiler(
            max_evidence_items=1,
            max_evidence_chars=4000,
            prompt_mode="external_naive",
            structured_guide=True,
            evidence_report_contract=True,
            evidence_report_information_needs=("fact_lookup",),
            memory_context_newlines_after_blocks=4,
        )
        context = compiler.compile(
            question="Which music streaming service does Alex use?",
            question_time=None,
            route=RouteResult(information_need="fact_lookup", signals=()),
            hits=(),
            evidence_turns=(
                Turn(
                    source_id="s1:t0",
                    session_id="s1",
                    turn_index=0,
                    role="user",
                    text="Alex uses Spotify for music streaming.",
                    timestamp="2024-01-01",
                ),
            ),
        )

        self.assertIn("Structured Evidence Guide:", context.prompt)
        self.assertIn("\n\n\n\nMemory Context:", context.prompt)

    def test_current_state_update_contract_is_config_gated(self) -> None:
        turns = (
            Turn(
                source_id="s1:t0",
                session_id="s1",
                turn_index=0,
                role="assistant",
                text="Congratulations on nearing 1300 followers.",
                timestamp="2024-01-01",
            ),
        )
        route = RouteResult(information_need="current_state", signals=())
        baseline = EvidenceCompiler(
            max_evidence_items=1,
            max_evidence_chars=4000,
            prompt_mode="external_naive",
            evidence_report_contract=True,
            evidence_report_information_needs=("current_state",),
        ).compile(
            question="What is my current follower count?",
            question_time=None,
            route=route,
            hits=(),
            evidence_turns=turns,
        )
        contracted = EvidenceCompiler(
            max_evidence_items=1,
            max_evidence_chars=4000,
            prompt_mode="external_naive",
            evidence_report_contract=True,
            evidence_report_information_needs=("current_state",),
            current_state_update_contract=True,
        ).compile(
            question="What is my current follower count?",
            question_time=None,
            route=route,
            hits=(),
            evidence_turns=turns,
        )

        self.assertNotIn("newer approximate or self-reported state", baseline.prompt)
        self.assertIn("newer approximate or self-reported state", contracted.prompt)

    def test_dialogue_inference_contract_is_route_override_gated(self) -> None:
        turns = (
            Turn(
                source_id="s1:t0",
                session_id="s1",
                turn_index=0,
                role="user",
                text="I redeemed the notebook coupon this morning.",
                timestamp="2024-01-01",
            ),
            Turn(
                source_id="s1:t1",
                session_id="s1",
                turn_index=1,
                role="assistant",
                text="Good use of your Pine Market coupon.",
                timestamp="2024-01-01",
            ),
        )
        route = RouteResult(information_need="fact_lookup", signals=())
        baseline = EvidenceCompiler(
            max_evidence_items=2,
            max_evidence_chars=4000,
            prompt_mode="external_naive",
            evidence_report_contract=True,
            evidence_report_information_needs=("fact_lookup",),
        ).compile(
            question="Where did I redeem the notebook coupon?",
            question_time=None,
            route=route,
            hits=(),
            evidence_turns=turns,
        )
        contracted = EvidenceCompiler(
            max_evidence_items=2,
            max_evidence_chars=4000,
            prompt_mode="external_naive",
            evidence_report_contract=True,
            evidence_report_information_needs=("fact_lookup",),
            route_overrides={
                "fact_lookup": {
                    "dialogue_inference_contract": True,
                }
            },
        ).compile(
            question="Where did I redeem the notebook coupon?",
            question_time=None,
            route=route,
            hits=(),
            evidence_turns=turns,
        )

        self.assertNotIn("Same-session neighboring turns", baseline.prompt)
        self.assertIn("Same-session neighboring turns", contracted.prompt)
        self.assertIn("An assistant row can support an answer", contracted.prompt)
        self.assertNotIn("question_type", contracted.prompt)

    def test_personalized_advice_contract_is_question_derived(self) -> None:
        turns = (
            Turn(
                source_id="s1:t0",
                session_id="s1",
                turn_index=0,
                role="user",
                text="I prefer hotels with water views and a quiet rooftop lounge.",
                timestamp="2024-01-01",
            ),
        )
        compiler = EvidenceCompiler(
            max_evidence_items=1,
            max_evidence_chars=4000,
            prompt_mode="external_naive",
            evidence_report_contract=True,
            evidence_report_information_needs=("profile_preference", "fact_lookup"),
            personalized_advice_contract=True,
        )

        advice_context = compiler.compile(
            question="Can you suggest a hotel style for my Miami trip?",
            question_time=None,
            route=RouteResult(information_need="profile_preference", signals=()),
            hits=(),
            evidence_turns=turns,
        )
        fact_context = compiler.compile(
            question="Which hotel did I book for my Miami trip?",
            question_time=None,
            route=RouteResult(information_need="fact_lookup", signals=()),
            hits=(),
            evidence_turns=turns,
        )

        self.assertIn("Personalized Advice Discipline:", advice_context.prompt)
        self.assertIn("owned resources, and prior successes", advice_context.prompt)
        self.assertNotIn("question_type", advice_context.prompt)
        self.assertNotIn("sample id", advice_context.prompt.lower())
        self.assertNotIn("Personalized Advice Discipline:", fact_context.prompt)

    def test_personalized_advice_contract_skips_assistant_recall(self) -> None:
        turns = (
            Turn(
                source_id="s1:t0",
                session_id="s1",
                turn_index=0,
                role="assistant",
                text="I suggested the harbor-view hotel last time.",
                timestamp="2024-01-01",
            ),
        )
        compiler = EvidenceCompiler(
            max_evidence_items=1,
            max_evidence_chars=4000,
            prompt_mode="external_naive",
            evidence_report_contract=True,
            evidence_report_information_needs=("fact_lookup",),
            personalized_advice_contract=True,
        )

        context = compiler.compile(
            question="Can you remind me what hotel you suggested earlier?",
            question_time=None,
            route=RouteResult(information_need="fact_lookup", signals=()),
            hits=(),
            evidence_turns=turns,
        )

        self.assertNotIn("Personalized Advice Discipline:", context.prompt)

    def test_temporal_order_contract_is_route_override_gated(self) -> None:
        turns = (
            Turn(
                source_id="s1:t0",
                session_id="s1",
                turn_index=0,
                role="user",
                text="I started Spanish classes three months ago.",
                timestamp="2024-04-01",
            ),
        )
        compiler = EvidenceCompiler(
            max_evidence_items=1,
            max_evidence_chars=4000,
            prompt_mode="external_naive",
            evidence_report_contract=True,
            evidence_report_information_needs=("temporal_lookup", "list_count"),
            route_overrides={
                "temporal_lookup": {
                    "temporal_order_contract": True,
                }
            },
        )
        temporal_context = compiler.compile(
            question="Which happened first, Spanish classes or the festival?",
            question_time=None,
            route=RouteResult(information_need="temporal_lookup", signals=()),
            hits=(),
            evidence_turns=turns,
        )
        list_context = compiler.compile(
            question="How many classes did I mention?",
            question_time=None,
            route=RouteResult(information_need="list_count", signals=()),
            hits=(),
            evidence_turns=turns,
        )

        self.assertIn("earlier normalized event time", temporal_context.prompt)
        self.assertIn("started N ago", temporal_context.prompt)
        self.assertNotIn("earlier normalized event time", list_context.prompt)

    def test_external_naive_final_checklist_is_config_gated(self) -> None:
        turns = (
            Turn(
                source_id="s1:t0",
                session_id="s1",
                turn_index=0,
                role="user",
                text="Alex fixed the fence yesterday.",
                timestamp="2024-01-08",
            ),
        )
        route = RouteResult(information_need="temporal_lookup", signals=("temporal",))
        default_compiler = EvidenceCompiler(
            max_evidence_items=1,
            max_evidence_chars=4000,
            prompt_mode="external_naive",
            evidence_report_contract=True,
        )
        checklist_compiler = EvidenceCompiler(
            max_evidence_items=1,
            max_evidence_chars=4000,
            prompt_mode="external_naive",
            evidence_report_contract=True,
            final_answer_checklist=True,
        )

        default_context = default_compiler.compile(
            question="Which happened first, Alex fixing the fence or buying cows?",
            question_time=None,
            route=route,
            hits=(),
            evidence_turns=turns,
        )
        checklist_context = checklist_compiler.compile(
            question="Which happened first, Alex fixing the fence or buying cows?",
            question_time=None,
            route=route,
            hits=(),
            evidence_turns=turns,
        )

        self.assertNotIn("Final Answer Checklist", default_context.prompt)
        self.assertIn("Final Answer Checklist", checklist_context.prompt)
        self.assertIn("multiple compared alternatives", checklist_context.prompt)
        self.assertIn("partial support is not enough", checklist_context.prompt)
        self.assertNotIn("gold answer", checklist_context.prompt)
        self.assertNotIn("judge output", checklist_context.prompt)
        self.assertNotIn("sample id", checklist_context.prompt)

    def test_detailed_evidence_report_rules_are_config_gated(self) -> None:
        turns = (
            Turn(
                source_id="s1:t0",
                session_id="s1",
                turn_index=0,
                role="user",
                text="Alex read Dune and then discussed Foundation.",
                timestamp="2024-01-01",
            ),
        )
        route = RouteResult(information_need="fact_lookup", signals=())
        default_compiler = EvidenceCompiler(
            max_evidence_items=1,
            max_evidence_chars=4000,
            prompt_mode="external_naive",
            evidence_report_contract=True,
            evidence_report_information_needs=("fact_lookup",),
        )
        detailed_compiler = EvidenceCompiler(
            max_evidence_items=1,
            max_evidence_chars=4000,
            prompt_mode="external_naive",
            evidence_report_contract=True,
            evidence_report_information_needs=("fact_lookup",),
            evidence_report_detail=True,
        )

        default_context = default_compiler.compile(
            question="What books has Alex read?",
            question_time=None,
            route=route,
            hits=(),
            evidence_turns=turns,
        )
        detailed_context = detailed_compiler.compile(
            question="What books has Alex read?",
            question_time=None,
            route=route,
            hits=(),
            evidence_turns=turns,
        )

        self.assertNotIn("Do not treat owning, discussing", default_context.prompt)
        self.assertIn("Do not treat owning, discussing", detailed_context.prompt)
        self.assertIn("preserve all distinct in-scope item names", detailed_context.prompt)
        self.assertNotIn("question_type", detailed_context.prompt)

    def test_evidence_report_detail_can_be_route_scoped(self) -> None:
        compiler = EvidenceCompiler(
            max_evidence_items=1,
            max_evidence_chars=4000,
            prompt_mode="external_naive",
            evidence_report_contract=True,
            evidence_report_information_needs=("fact_lookup", "list_count"),
            evidence_report_detail=False,
            route_overrides={"list_count": {"evidence_report_detail": True}},
        )
        turns = (
            Turn(
                source_id="s1:t0",
                session_id="s1",
                turn_index=0,
                role="user",
                text="Alex read Dune and then discussed Foundation.",
                timestamp="2024-01-01",
            ),
        )

        fact_context = compiler.compile(
            question="Which book did Alex read?",
            question_time=None,
            route=RouteResult(information_need="fact_lookup", signals=()),
            hits=(),
            evidence_turns=turns,
        )
        list_context = compiler.compile(
            question="What books has Alex read?",
            question_time=None,
            route=RouteResult(information_need="list_count", signals=("list_or_count",)),
            hits=(),
            evidence_turns=turns,
        )

        self.assertIn('"evidence_report"', fact_context.prompt)
        self.assertNotIn("Do not treat owning, discussing", fact_context.prompt)
        self.assertIn("Do not treat owning, discussing", list_context.prompt)
        self.assertIn("preserve all distinct in-scope item names", list_context.prompt)

    def test_aggregation_report_contract_is_question_derived(self) -> None:
        compiler = EvidenceCompiler(
            max_evidence_items=1,
            max_evidence_chars=1000,
            prompt_mode="external_naive",
            evidence_report_contract=True,
            evidence_report_information_needs=("temporal_lookup",),
            aggregation_report_contract=True,
            aggregation_report_information_needs=("temporal_lookup",),
        )
        rows = (
            Turn(
                source_id="s1:t0",
                session_id="s1",
                turn_index=0,
                role="user",
                text="Alex bought a snake plant and two succulents last month.",
            ),
        )

        count_context = compiler.compile(
            question="How many plants did Alex acquire last month?",
            question_time=None,
            route=RouteResult(
                information_need="temporal_lookup", signals=("temporal",)
            ),
            hits=(RetrievalHit("s1:t0", 1.0, 1, "lexical"),),
            evidence_turns=rows,
        )
        date_context = compiler.compile(
            question="When did Alex acquire the snake plant?",
            question_time=None,
            route=RouteResult(
                information_need="temporal_lookup", signals=("temporal",)
            ),
            hits=(RetrievalHit("s1:t0", 1.0, 1, "lexical"),),
            evidence_turns=rows,
        )

        self.assertIn('"count_increment"', count_context.prompt)
        self.assertIn("Do not put unrelated numeric facts", count_context.prompt)
        self.assertNotIn('"count_increment"', date_context.prompt)

    def test_candidate_guide_is_route_scoped_and_source_preserving(self) -> None:
        compiler = EvidenceCompiler(
            max_evidence_items=3,
            max_evidence_chars=4000,
            prompt_mode="external_naive",
            candidate_guide=True,
            candidate_guide_information_needs=("list_count",),
            candidate_guide_max_rows=2,
            candidate_guide_snippet_chars=120,
        )
        turns = (
            Turn(
                source_id="s1:t0",
                session_id="s1",
                turn_index=0,
                role="user",
                text="Alex discussed the garden.",
                timestamp="2024-01-01",
            ),
            Turn(
                source_id="s1:t1",
                session_id="s1",
                turn_index=1,
                role="user",
                text="Alex bought 2 basil plants and one mint plant last week.",
                timestamp="2024-01-08",
            ),
            Turn(
                source_id="s1:t2",
                session_id="s1",
                turn_index=2,
                role="assistant",
                text="General plant care advice.",
                timestamp="2024-01-08",
            ),
        )

        list_context = compiler.compile(
            question="How many plants did Alex buy?",
            question_time=None,
            route=RouteResult(information_need="list_count", signals=("list_or_count",)),
            hits=(RetrievalHit("s1:t1", 1.0, 1, "lexical_bm25"),),
            evidence_turns=turns,
        )
        fact_context = compiler.compile(
            question="Which plant did Alex buy?",
            question_time=None,
            route=RouteResult(information_need="fact_lookup", signals=()),
            hits=(RetrievalHit("s1:t1", 1.0, 1, "lexical_bm25"),),
            evidence_turns=turns,
        )

        self.assertIn("Candidate Evidence Map:", list_context.prompt)
        self.assertIn("Use Candidate Evidence Map only as a compact index", list_context.prompt)
        self.assertIn("Memory 2: date=2024-01-08 role=user", list_context.prompt)
        self.assertIn("quantities=2", list_context.prompt)
        self.assertIn("last week", list_context.prompt)
        self.assertIn("Alex bought 2 basil plants", list_context.prompt)
        self.assertNotIn("Candidate Evidence Map:", fact_context.prompt)
        self.assertNotIn("question_type", list_context.prompt)

    def test_candidate_guide_fact_lookup_focus_and_diversity(self) -> None:
        compiler = EvidenceCompiler(
            max_evidence_items=4,
            max_evidence_chars=5000,
            prompt_mode="external_naive",
            candidate_guide=True,
            candidate_guide_information_needs=("fact_lookup",),
            candidate_guide_max_rows=2,
            candidate_guide_snippet_chars=120,
        )
        turns = (
            Turn(
                source_id="s1:t0",
                session_id="s1",
                turn_index=0,
                role="user",
                text="Alex bought blue shoes in Paris.",
                timestamp="2024-01-01",
            ),
            Turn(
                source_id="s1:t1",
                session_id="s1",
                turn_index=1,
                role="user",
                text="Alex bought the blue shoes in Paris again.",
                timestamp="2024-01-02",
            ),
            Turn(
                source_id="s2:t0",
                session_id="s2",
                turn_index=0,
                role="user",
                text="Alex bought ceramic figurines at the market.",
                timestamp="2024-02-01",
            ),
            Turn(
                source_id="s3:t0",
                session_id="s3",
                turn_index=0,
                role="assistant",
                text="General shopping advice.",
                timestamp="2024-02-02",
            ),
        )

        context = compiler.compile(
            question="What items did Alex buy?",
            question_time=None,
            route=RouteResult(information_need="fact_lookup", signals=()),
            hits=(
                RetrievalHit("s1:t0", 1.0, 1, "lexical_bm25"),
                RetrievalHit("s1:t1", 0.9, 2, "lexical_bm25"),
                RetrievalHit("s2:t0", 0.8, 3, "lexical_bm25"),
            ),
            evidence_turns=turns,
        )

        self.assertIn("Candidate Evidence Map:", context.prompt)
        self.assertIn("match the requested answer slot exactly", context.prompt)
        self.assertIn("Memory 1: date=2024-01-01 role=user", context.prompt)
        self.assertIn("Memory 3: date=2024-02-01 role=user", context.prompt)
        self.assertNotIn("Memory 2: date=2024-01-02 role=user", context.prompt)
        self.assertNotIn("gold answer", context.prompt)
        self.assertNotIn("judge output", context.prompt)
        self.assertNotIn("sample id", context.prompt)

    def test_pipeline_traces_candidate_guide_config(self) -> None:
        config = {
            "retrieval": {"top_k": 1, "max_top_k": 1, "neighbor_window": 0},
            "compiler": {
                "max_evidence_items": 1,
                "max_evidence_chars": 2000,
                "prompt_mode": "external_naive",
                "candidate_guide": True,
                "candidate_guide_information_needs": ["list_count"],
                "candidate_guide_max_rows": 2,
                "candidate_guide_snippet_chars": 120,
            },
            "answer": {"fallback_answer": "I do not know."},
        }
        request = PredictionRequest(
            question="How many plants did Alex buy?",
            turns=(
                Turn(
                    source_id="s1:t0",
                    session_id="s1",
                    turn_index=0,
                    role="user",
                    text="Alex bought 2 basil plants and one mint plant.",
                    timestamp="2024-01-08",
                ),
            ),
        )

        result = Stage1Pipeline(config).predict(request)

        self.assertTrue(result["trace"]["compiler"]["candidate_guide"])
        self.assertEqual(
            result["trace"]["compiler"]["candidate_guide_information_needs"],
            ("list_count",),
        )
        self.assertIn(
            "Candidate Evidence Map:",
            result["trace"]["compiled_context"]["prompt"],
        )

    def test_update_conflict_guide_is_narrow_and_source_preserving(self) -> None:
        compiler = EvidenceCompiler(
            max_evidence_items=3,
            max_evidence_chars=4000,
            prompt_mode="external_naive",
            update_conflict_guide=True,
            update_conflict_guide_information_needs=("fact_lookup",),
            update_conflict_guide_max_rows=3,
            update_conflict_guide_snippet_chars=140,
        )
        turns = (
            Turn(
                source_id="s1:t0",
                session_id="s1",
                turn_index=0,
                role="user",
                text="Alex said his 5K time was 27:12 at the charity race.",
                timestamp="2024-05-23",
            ),
            Turn(
                source_id="s2:t0",
                session_id="s2",
                turn_index=0,
                role="user",
                text="Alex is hoping to beat his personal best time of 25:50 next month.",
                timestamp="2024-05-30",
            ),
            Turn(
                source_id="s3:t0",
                session_id="s3",
                turn_index=0,
                role="assistant",
                text="General running advice.",
                timestamp="2024-06-01",
            ),
        )

        fact_context = compiler.compile(
            question="What is Alex's personal best 5K time?",
            question_time=None,
            route=RouteResult(information_need="fact_lookup", signals=()),
            hits=(
                RetrievalHit("s1:t0", 1.0, 1, "lexical_bm25"),
                RetrievalHit("s2:t0", 0.9, 2, "lexical_bm25"),
            ),
            evidence_turns=turns,
        )
        profile_context = compiler.compile(
            question="What is Alex's personal best 5K time?",
            question_time=None,
            route=RouteResult(information_need="profile_preference", signals=()),
            hits=(),
            evidence_turns=turns,
        )

        self.assertIn("Update/Conflict Candidate Chain:", fact_context.prompt)
        self.assertIn("Use Update/Conflict Candidate Chain only as a compact index", fact_context.prompt)
        self.assertIn("Memory 1: date=2024-05-23 role=user", fact_context.prompt)
        self.assertIn("values=27:12", fact_context.prompt)
        self.assertIn("Memory 2: date=2024-05-30 role=user", fact_context.prompt)
        self.assertIn("personal_best", fact_context.prompt)
        self.assertIn("values=25:50", fact_context.prompt)
        self.assertNotIn("Update/Conflict Candidate Chain:", profile_context.prompt)
        self.assertNotIn("question_type", fact_context.prompt)

    def test_update_conflict_guide_skips_single_value_rows(self) -> None:
        compiler = EvidenceCompiler(
            max_evidence_items=2,
            max_evidence_chars=3000,
            prompt_mode="external_naive",
            update_conflict_guide=True,
            update_conflict_guide_information_needs=("current_state",),
        )
        compiled = compiler.compile(
            question="What is Alex's current follower count?",
            question_time=None,
            route=RouteResult(information_need="current_state", signals=()),
            hits=(),
            evidence_turns=(
                Turn(
                    source_id="s1:t0",
                    session_id="s1",
                    turn_index=0,
                    role="user",
                    text="Alex is close to 1300 followers now.",
                    timestamp="2024-05-30",
                ),
            ),
        )

        self.assertNotIn("Update/Conflict Candidate Chain:", compiled.prompt)

    def test_update_conflict_guide_skips_non_value_slots(self) -> None:
        compiler = EvidenceCompiler(
            max_evidence_items=3,
            max_evidence_chars=3000,
            prompt_mode="external_naive",
            update_conflict_guide=True,
            update_conflict_guide_information_needs=("current_state",),
        )
        compiled = compiler.compile(
            question="Where did Alex go on his most recent family trip?",
            question_time=None,
            route=RouteResult(information_need="current_state", signals=()),
            hits=(),
            evidence_turns=(
                Turn(
                    source_id="s1:t0",
                    session_id="s1",
                    turn_index=0,
                    role="user",
                    text="Alex took a 10-day family trip to Hawaii.",
                    timestamp="2024-05-20",
                ),
                Turn(
                    source_id="s2:t0",
                    session_id="s2",
                    turn_index=0,
                    role="user",
                    text="Alex recently went to Paris with family last month.",
                    timestamp="2024-05-30",
                ),
            ),
        )

        self.assertNotIn("Update/Conflict Candidate Chain:", compiled.prompt)

    def test_update_conflict_guide_adds_aggregation_operand_rule(self) -> None:
        compiler = EvidenceCompiler(
            max_evidence_items=3,
            max_evidence_chars=4000,
            prompt_mode="external_naive",
            update_conflict_guide=True,
            update_conflict_guide_information_needs=("fact_lookup",),
        )
        compiled = compiler.compile(
            question="What is the total cost of Lola's vet visit and flea medication?",
            question_time=None,
            route=RouteResult(information_need="fact_lookup", signals=()),
            hits=(),
            evidence_turns=(
                Turn(
                    source_id="s1:t0",
                    session_id="s1",
                    turn_index=0,
                    role="user",
                    text="I remember when I took Lola to the vet last week, the consultation fee was $50.",
                    timestamp="2024-05-25",
                ),
                Turn(
                    source_id="s2:t0",
                    session_id="s2",
                    turn_index=0,
                    role="user",
                    text="I got Lola flea medication for $25 today.",
                    timestamp="2024-05-30",
                ),
            ),
        )

        self.assertIn("Update/Conflict Candidate Chain:", compiled.prompt)
        self.assertIn("collect each requested operand", compiled.prompt)
        self.assertIn("older operand is still valid", compiled.prompt)

    def test_pipeline_traces_update_conflict_guide_config(self) -> None:
        config = {
            "retrieval": {"top_k": 2, "max_top_k": 2, "neighbor_window": 0},
            "compiler": {
                "max_evidence_items": 2,
                "max_evidence_chars": 3000,
                "prompt_mode": "external_naive",
                "update_conflict_guide": True,
                "update_conflict_guide_information_needs": ["current_state"],
                "update_conflict_guide_max_rows": 2,
                "update_conflict_guide_snippet_chars": 120,
            },
            "answer": {"fallback_answer": "I do not know."},
        }
        request = PredictionRequest(
            question="What is Alex's current follower count?",
            turns=(
                Turn(
                    source_id="s1:t0",
                    session_id="s1",
                    turn_index=0,
                    role="user",
                    text="Alex had 1250 followers earlier this month.",
                    timestamp="2024-05-20",
                ),
                Turn(
                    source_id="s1:t1",
                    session_id="s1",
                    turn_index=1,
                    role="user",
                    text="Alex is close to 1300 followers now.",
                    timestamp="2024-05-30",
                ),
            ),
        )

        result = Stage1Pipeline(config).predict(request)

        self.assertTrue(result["trace"]["compiler"]["update_conflict_guide"])
        self.assertEqual(
            result["trace"]["compiler"]["update_conflict_guide_information_needs"],
            ("current_state",),
        )
        self.assertIn(
            "Update/Conflict Candidate Chain:",
            result["trace"]["compiled_context"]["prompt"],
        )

    def test_temporal_event_contract_separates_mention_time_from_event_time(self) -> None:
        compiler = EvidenceCompiler(
            max_evidence_items=1,
            max_evidence_chars=4000,
            prompt_mode="external_naive",
            temporal_workpad=True,
            temporal_text_normalization=True,
            temporal_event_contract=True,
            evidence_report_contract=True,
            evidence_report_information_needs=("temporal_lookup",),
        )
        route = RouteResult(information_need="temporal_lookup", signals=("temporal",))
        compiled = compiler.compile(
            question="When did Caroline meet with her mentors?",
            question_time=None,
            route=route,
            hits=(RetrievalHit("s1:t0", 1.0, 1, "lexical_bm25"),),
            evidence_turns=(
                Turn(
                    source_id="s1:t0",
                    session_id="s1",
                    turn_index=0,
                    role="user",
                    text="Here is a photo from when we met with my mentors last week.",
                    timestamp="2023-06-09",
                ),
            ),
        )

        self.assertIn("mention_time is the Memory Date", compiled.prompt)
        self.assertIn(
            'event_time_candidates=phrase="last week" event_time="2023-06-02 to 2023-06-08"',
            compiled.prompt,
        )
        self.assertIn('"mention_time": "Memory Date or empty"', compiled.prompt)
        self.assertIn(
            '"event_time": "date/time/span/duration of the target event or empty"',
            compiled.prompt,
        )
        self.assertIn("use event_time", compiled.prompt)
        self.assertNotIn("question_type", compiled.prompt)

    def test_temporal_event_contract_is_temporal_route_scoped(self) -> None:
        compiler = EvidenceCompiler(
            max_evidence_items=1,
            max_evidence_chars=4000,
            prompt_mode="external_naive",
            temporal_workpad=True,
            temporal_text_normalization=True,
            temporal_event_contract=True,
            evidence_report_contract=True,
            evidence_report_information_needs=("fact_lookup",),
        )
        compiled = compiler.compile(
            question="Which music service does Alex use?",
            question_time=None,
            route=RouteResult(information_need="fact_lookup", signals=()),
            hits=(),
            evidence_turns=(
                Turn(
                    source_id="s1:t0",
                    session_id="s1",
                    turn_index=0,
                    role="user",
                    text="Alex started using Spotify last week.",
                    timestamp="2024-01-08",
                ),
            ),
        )

        self.assertIn('"evidence_report"', compiled.prompt)
        self.assertNotIn('"mention_time": "Memory Date or empty"', compiled.prompt)
        self.assertNotIn("event_time_candidates", compiled.prompt)

    def test_evidence_labels_role_snippets_and_final_checklist_are_added(self) -> None:
        config = {
            "retrieval": {"top_k": 2, "max_top_k": 2, "neighbor_window": 0},
            "compiler": {
                "max_evidence_items": 2,
                "max_evidence_chars": 1000,
                "row_text_mode": "role_query_snippet",
                "max_row_text_chars": 80,
                "evidence_row_labels": True,
                "final_answer_checklist": True,
            },
            "answer": {"fallback_answer": "I do not know."},
        }
        request = PredictionRequest(
            question="Which bike did Alex service?",
            turns=(
                Turn(
                    source_id="s1:t0",
                    session_id="s1",
                    turn_index=0,
                    role="assistant",
                    text=(
                        "General cycling advice. " * 20
                        + "Alex serviced the road bike at the shop."
                        + " More general cycling advice. " * 20
                    ),
                ),
                Turn(
                    source_id="s1:t1",
                    session_id="s1",
                    turn_index=1,
                    role="user",
                    text="Alex asked about bike maintenance.",
                ),
            ),
        )

        result = Stage1Pipeline(config).predict(request)
        prompt = result["trace"]["compiled_context"]["prompt"]

        self.assertIn("- E1 source_id=", prompt)
        self.assertIn("Final answer checklist:", prompt)
        self.assertIn("exact asked entity", prompt)
        self.assertIn("Alex serviced the road bike", prompt)
        self.assertIn("...", prompt)

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

    def test_memory_aware_evidence_order_uses_source_link_without_prompting_memory(self) -> None:
        compiler = EvidenceCompiler(
            max_evidence_items=1,
            max_evidence_chars=4000,
            evidence_order="memory_aware",
            max_memory_records=0,
        )
        route = RouteResult(information_need="fact_lookup", signals=())
        memory = MemoryRecord(
            memory_id="m1",
            memory_type="fact",
            text="The user owns a Korg B1 piano.",
            source_ids=("s1:t1",),
            subject="user",
            predicate="owns",
            value="Korg B1 piano",
            entities=("Korg B1", "piano"),
        )
        compiled = compiler.compile(
            question="Which instrument do I own?",
            question_time=None,
            route=route,
            hits=(
                RetrievalHit("s1:t0", 1.0, 1, "dense_embedding"),
                RetrievalHit("s1:t1", 0.9, 2, "build_memory_bm25"),
            ),
            evidence_turns=(
                Turn(
                    source_id="s1:t0",
                    session_id="s1",
                    turn_index=0,
                    role="user",
                    text="I need advice about music lessons.",
                ),
                Turn(
                    source_id="s1:t1",
                    session_id="s1",
                    turn_index=1,
                    role="user",
                    text="I bought a Korg B1 last year.",
                ),
            ),
            memory_records=(memory,),
        )

        self.assertEqual(compiled.evidence_rows[0].source_id, "s1:t1")
        self.assertEqual(compiled.memory_records, ())
        self.assertIn("I bought a Korg B1 last year.", compiled.prompt)
        self.assertNotIn("The user owns a Korg B1 piano.", compiled.prompt)

    def test_source_anchor_coverage_preserves_anchor_then_source_link(self) -> None:
        compiler = EvidenceCompiler(
            max_evidence_items=4,
            max_evidence_chars=4000,
            evidence_order="source_anchor_coverage",
            source_anchor_keep=1,
            source_anchor_memory_rows=2,
            source_anchor_per_session=1,
            max_memory_records=0,
        )
        route = RouteResult(information_need="profile_preference", signals=())
        memory = MemoryRecord(
            memory_id="m1",
            memory_type="preference",
            text="The user prefers turbinado sugar for richer flavor.",
            source_ids=("s2:t0",),
            subject="user",
            predicate="prefers",
            value="turbinado sugar",
            entities=("turbinado sugar",),
        )

        compiled = compiler.compile(
            question="What would improve my cookies?",
            question_time=None,
            route=route,
            hits=(
                RetrievalHit("s1:t0", 1.0, 1, "dense_embedding"),
                RetrievalHit("s1:t1", 0.9, 2, "dense_embedding"),
                RetrievalHit("s2:t0", 0.4, 3, "build_memory_bm25"),
            ),
            evidence_turns=(
                Turn(
                    source_id="s1:t0",
                    session_id="s1",
                    turn_index=0,
                    role="user",
                    text="I tried a cherry clafoutis recipe.",
                ),
                Turn(
                    source_id="s1:t1",
                    session_id="s1",
                    turn_index=1,
                    role="user",
                    text="Almond flour worked well in a dessert.",
                ),
                Turn(
                    source_id="s2:t0",
                    session_id="s2",
                    turn_index=0,
                    role="user",
                    text="I found turbinado sugar adds a richer flavor.",
                ),
            ),
            memory_records=(memory,),
        )

        self.assertEqual(
            [row.source_id for row in compiled.evidence_rows],
            ["s1:t0", "s2:t0", "s1:t1"],
        )
        self.assertEqual(compiled.memory_records, ())
        self.assertNotIn("The user prefers turbinado sugar", compiled.prompt)

    def test_source_anchor_coverage_without_memory_preserves_order(self) -> None:
        compiler = EvidenceCompiler(
            max_evidence_items=2,
            max_evidence_chars=4000,
            evidence_order="source_anchor_coverage",
            source_anchor_keep=1,
            source_anchor_memory_rows=2,
            max_memory_records=0,
        )
        route = RouteResult(information_need="fact_lookup", signals=())

        compiled = compiler.compile(
            question="Which instrument do I own?",
            question_time=None,
            route=route,
            hits=(
                RetrievalHit("s1:t0", 1.0, 1, "dense_embedding"),
                RetrievalHit("s1:t1", 0.9, 2, "dense_embedding"),
            ),
            evidence_turns=(
                Turn(
                    source_id="s1:t0",
                    session_id="s1",
                    turn_index=0,
                    role="user",
                    text="I need advice about music lessons.",
                ),
                Turn(
                    source_id="s1:t1",
                    session_id="s1",
                    turn_index=1,
                    role="user",
                    text="I bought a Korg B1 last year.",
                ),
            ),
        )

        self.assertEqual(
            [row.source_id for row in compiled.evidence_rows],
            ["s1:t0", "s1:t1"],
        )

    def test_compiler_route_override_can_scope_evidence_order(self) -> None:
        compiler = EvidenceCompiler(
            max_evidence_items=1,
            max_evidence_chars=4000,
            evidence_order="retrieval",
            route_overrides={"list_count": {"evidence_order": "question_overlap"}},
        )
        turns = (
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
        )
        fact_context = compiler.compile(
            question="What fruit was used for the picnic menu?",
            question_time=None,
            route=RouteResult(information_need="fact_lookup", signals=()),
            hits=(RetrievalHit("s1:t0", 1.0, 1, "lexical_bm25"),),
            evidence_turns=turns,
        )
        list_context = compiler.compile(
            question="What fruit was used for the picnic menu?",
            question_time=None,
            route=RouteResult(information_need="list_count", signals=("list_or_count",)),
            hits=(RetrievalHit("s1:t0", 1.0, 1, "lexical_bm25"),),
            evidence_turns=turns,
        )

        self.assertEqual(fact_context.evidence_rows[0].source_id, "s1:t0")
        self.assertEqual(list_context.evidence_rows[0].source_id, "s1:t1")

    def test_compiler_route_override_can_scope_context_layout(self) -> None:
        compiler = EvidenceCompiler(
            max_evidence_items=2,
            max_evidence_chars=4000,
            context_layout="flat",
            route_overrides={
                "list_count": {"context_layout": "chronological_session_thread"}
            },
        )
        turns = (
            Turn(
                source_id="new:t0",
                session_id="new",
                turn_index=0,
                role="user",
                text="Alex bought a second notebook.",
                timestamp="2024-03-01",
            ),
            Turn(
                source_id="old:t0",
                session_id="old",
                turn_index=0,
                role="user",
                text="Alex bought the first notebook.",
                timestamp="2024-01-01",
            ),
        )

        fact_context = compiler.compile(
            question="Which notebook did Alex buy?",
            question_time=None,
            route=RouteResult(information_need="fact_lookup", signals=()),
            hits=(),
            evidence_turns=turns,
        )
        list_context = compiler.compile(
            question="How many notebooks did Alex buy?",
            question_time=None,
            route=RouteResult(information_need="list_count", signals=("list_or_count",)),
            hits=(),
            evidence_turns=turns,
        )

        self.assertEqual(
            [row.source_id for row in fact_context.evidence_rows],
            ["new:t0", "old:t0"],
        )
        self.assertEqual(
            [row.source_id for row in list_context.evidence_rows],
            ["old:t0", "new:t0"],
        )

    def test_compiler_route_overrides_only_apply_to_matching_information_need(self) -> None:
        compiler = EvidenceCompiler(
            max_evidence_items=1,
            max_evidence_chars=4000,
            route_overrides={
                "list_count": {
                    "max_evidence_items": 2,
                    "row_text_mode": "query_snippet",
                    "max_row_text_chars": 60,
                }
            },
        )
        turns = (
            Turn(
                source_id="s1:t0",
                session_id="s1",
                turn_index=0,
                role="user",
                text="Alex joined the photography club and the chess club.",
            ),
            Turn(
                source_id="s2:t0",
                session_id="s2",
                turn_index=0,
                role="user",
                text="Alex also joined the hiking club.",
            ),
        )

        fact_context = compiler.compile(
            question="Which club did Alex join?",
            question_time=None,
            route=RouteResult(information_need="fact_lookup", signals=()),
            hits=(),
            evidence_turns=turns,
        )
        list_context = compiler.compile(
            question="How many clubs did Alex join?",
            question_time=None,
            route=RouteResult(information_need="list_count", signals=("list_or_count",)),
            hits=(),
            evidence_turns=turns,
        )

        self.assertEqual(len(fact_context.evidence_rows), 1)
        self.assertEqual(len(list_context.evidence_rows), 2)
        self.assertIn("Alex also joined the hiking club", list_context.prompt)

    def test_compiler_route_overrides_reject_unknown_information_need(self) -> None:
        with self.assertRaises(ValueError):
            EvidenceCompiler(
                max_evidence_items=1,
                max_evidence_chars=4000,
                route_overrides={"question_type": {"max_evidence_items": 2}},
            )

    def test_compiler_route_overrides_reject_unknown_setting(self) -> None:
        with self.assertRaises(ValueError):
            EvidenceCompiler(
                max_evidence_items=1,
                max_evidence_chars=4000,
                route_overrides={"list_count": {"benchmark_label": "multi-session"}},
            )

    def test_temporal_workpad_is_disabled_by_default(self) -> None:
        compiler = EvidenceCompiler(
            max_evidence_items=2,
            max_evidence_chars=4000,
        )
        route = RouteResult(information_need="temporal_lookup", signals=("temporal",))
        compiled = compiler.compile(
            question="How many days passed between the museum visit and the exhibit?",
            question_time="2023-01-20",
            route=route,
            hits=(
                RetrievalHit("s1:t0", 1.0, 1, "lexical_bm25"),
                RetrievalHit("s2:t0", 0.9, 2, "lexical_bm25"),
            ),
            evidence_turns=(
                Turn(
                    source_id="s1:t0",
                    session_id="s1",
                    turn_index=0,
                    role="user",
                    text="I visited the art museum today.",
                    timestamp="2023-01-08",
                ),
                Turn(
                    source_id="s2:t0",
                    session_id="s2",
                    turn_index=0,
                    role="user",
                    text="I attended the ancient exhibit today.",
                    timestamp="2023-01-15",
                ),
            ),
        )

        self.assertNotIn("Temporal calculation workpad", compiled.prompt)

    def test_temporal_workpad_adds_pairwise_date_gaps(self) -> None:
        compiler = EvidenceCompiler(
            max_evidence_items=2,
            max_evidence_chars=4000,
            temporal_workpad=True,
        )
        route = RouteResult(information_need="temporal_lookup", signals=("temporal",))
        compiled = compiler.compile(
            question="How many days passed between the museum visit and the exhibit?",
            question_time="2023-01-20",
            route=route,
            hits=(
                RetrievalHit("s1:t0", 1.0, 1, "lexical_bm25"),
                RetrievalHit("s2:t0", 0.9, 2, "lexical_bm25"),
            ),
            evidence_turns=(
                Turn(
                    source_id="s1:t0",
                    session_id="s1",
                    turn_index=0,
                    role="user",
                    text="I visited the art museum today.",
                    timestamp="2023-01-08",
                ),
                Turn(
                    source_id="s2:t0",
                    session_id="s2",
                    turn_index=0,
                    role="user",
                    text="I attended the ancient exhibit today.",
                    timestamp="2023-01-15",
                ),
            ),
        )

        self.assertIn("Temporal calculation workpad", compiled.prompt)
        self.assertIn("question_date=2023-01-20", compiled.prompt)
        self.assertIn("7 days (8 inclusive)", compiled.prompt)
        self.assertLess(
            compiled.prompt.index("Temporal calculation workpad"),
            compiled.prompt.index("Raw context table"),
        )

    def test_temporal_text_normalization_adds_relative_mentions_to_workpad(self) -> None:
        compiler = EvidenceCompiler(
            max_evidence_items=1,
            max_evidence_chars=4000,
            temporal_workpad=True,
            temporal_text_normalization=True,
        )
        route = RouteResult(information_need="temporal_lookup", signals=("temporal",))
        compiled = compiler.compile(
            question="When did Alex visit the museum?",
            question_time="2023-01-20",
            route=route,
            hits=(RetrievalHit("s1:t0", 1.0, 1, "lexical_bm25"),),
            evidence_turns=(
                Turn(
                    source_id="s1:t0",
                    session_id="s1",
                    turn_index=0,
                    role="user",
                    text="Alex visited the museum yesterday.",
                    timestamp="2023-05-08",
                ),
            ),
        )

        self.assertIn("relative_time_mentions", compiled.prompt)
        self.assertIn('phrase="yesterday" normalized="2023-05-07"', compiled.prompt)
        self.assertLess(
            compiled.prompt.index("relative_time_mentions"),
            compiled.prompt.index("Raw context table"),
        )

    def test_temporal_text_normalization_parses_numeric_ago(self) -> None:
        compiler = EvidenceCompiler(
            max_evidence_items=1,
            max_evidence_chars=4000,
            temporal_workpad=True,
            temporal_text_normalization=True,
        )
        route = RouteResult(information_need="temporal_lookup", signals=("temporal",))
        compiled = compiler.compile(
            question="When did Alex move?",
            question_time="2023-06-20",
            route=route,
            hits=(RetrievalHit("s1:t0", 1.0, 1, "lexical_bm25"),),
            evidence_turns=(
                Turn(
                    source_id="s1:t0",
                    session_id="s1",
                    turn_index=0,
                    role="user",
                    text="Alex moved two years ago.",
                    timestamp="2023-06-09",
                ),
            ),
        )

        self.assertIn('phrase="two years ago" normalized="2021-06-09"', compiled.prompt)

    def test_temporal_text_normalization_parses_week_before_and_weekend(self) -> None:
        compiler = EvidenceCompiler(
            max_evidence_items=2,
            max_evidence_chars=4000,
            temporal_workpad=True,
            temporal_text_normalization=True,
        )
        route = RouteResult(information_need="temporal_lookup", signals=("temporal",))
        compiled = compiler.compile(
            question="When did Alex meet the mentors and visit the museum?",
            question_time="2023-06-20",
            route=route,
            hits=(
                RetrievalHit("s1:t0", 1.0, 1, "lexical_bm25"),
                RetrievalHit("s1:t1", 0.9, 2, "lexical_bm25"),
            ),
            evidence_turns=(
                Turn(
                    source_id="s1:t0",
                    session_id="s1",
                    turn_index=0,
                    role="user",
                    text="Alex met the mentors the week before.",
                    timestamp="2023-06-09",
                ),
                Turn(
                    source_id="s1:t1",
                    session_id="s1",
                    turn_index=1,
                    role="user",
                    text="Alex visited the museum two weekends ago.",
                    timestamp="2023-06-09",
                ),
            ),
        )

        self.assertIn(
            'phrase="the week before" normalized="2023-06-02 to 2023-06-08"',
            compiled.prompt,
        )
        self.assertIn(
            'phrase="two weekends ago" normalized="2023-05-27 to 2023-05-28"',
            compiled.prompt,
        )

    def test_temporal_text_normalization_skips_unreasonable_ago_span(self) -> None:
        compiler = EvidenceCompiler(
            max_evidence_items=1,
            max_evidence_chars=4000,
            temporal_workpad=True,
            temporal_text_normalization=True,
        )
        route = RouteResult(information_need="temporal_lookup", signals=("temporal",))
        compiled = compiler.compile(
            question="When did Alex discuss the artifact?",
            question_time="2023-06-20",
            route=route,
            hits=(RetrievalHit("s1:t0", 1.0, 1, "lexical_bm25"),),
            evidence_turns=(
                Turn(
                    source_id="s1:t0",
                    session_id="s1",
                    turn_index=0,
                    role="user",
                    text="Alex discussed an artifact from 4000 years ago.",
                    timestamp="2023-06-09",
                ),
            ),
        )

        self.assertIn("Temporal calculation workpad", compiled.prompt)
        self.assertNotIn('phrase="4000 years ago"', compiled.prompt)

    def test_temporal_text_normalization_is_disabled_by_default(self) -> None:
        compiler = EvidenceCompiler(
            max_evidence_items=1,
            max_evidence_chars=4000,
            temporal_workpad=True,
        )
        route = RouteResult(information_need="temporal_lookup", signals=("temporal",))
        compiled = compiler.compile(
            question="When did Alex visit the museum?",
            question_time="2023-01-20",
            route=route,
            hits=(RetrievalHit("s1:t0", 1.0, 1, "lexical_bm25"),),
            evidence_turns=(
                Turn(
                    source_id="s1:t0",
                    session_id="s1",
                    turn_index=0,
                    role="user",
                    text="Alex visited the museum yesterday.",
                    timestamp="2023-05-08",
                ),
            ),
        )

        self.assertNotIn("relative_time_mentions", compiled.prompt)

    def test_temporal_workpad_calculation_scope_skips_plain_when_question(self) -> None:
        compiler = EvidenceCompiler(
            max_evidence_items=1,
            max_evidence_chars=4000,
            temporal_workpad=True,
            temporal_workpad_scope="calculation_route",
        )
        route = RouteResult(information_need="temporal_lookup", signals=("temporal",))
        compiled = compiler.compile(
            question="When did Alex visit the museum?",
            question_time="2023-01-20",
            route=route,
            hits=(RetrievalHit("s1:t0", 1.0, 1, "lexical_bm25"),),
            evidence_turns=(
                Turn(
                    source_id="s1:t0",
                    session_id="s1",
                    turn_index=0,
                    role="user",
                    text="Alex visited the museum today.",
                    timestamp="2023-01-08",
                ),
            ),
        )

        self.assertNotIn("Temporal calculation workpad", compiled.prompt)

    def test_temporal_workpad_calculation_scope_keeps_duration_question(self) -> None:
        compiler = EvidenceCompiler(
            max_evidence_items=2,
            max_evidence_chars=4000,
            temporal_workpad=True,
            temporal_workpad_scope="calculation_route",
            temporal_workpad_max_rows=2,
            temporal_workpad_max_pairs=1,
        )
        route = RouteResult(information_need="temporal_lookup", signals=("temporal",))
        compiled = compiler.compile(
            question="How many days passed between the museum visit and the exhibit?",
            question_time="2023-01-20",
            route=route,
            hits=(
                RetrievalHit("s1:t0", 1.0, 1, "lexical_bm25"),
                RetrievalHit("s2:t0", 0.9, 2, "lexical_bm25"),
            ),
            evidence_turns=(
                Turn(
                    source_id="s1:t0",
                    session_id="s1",
                    turn_index=0,
                    role="user",
                    text="Alex visited the art museum today.",
                    timestamp="2023-01-08",
                ),
                Turn(
                    source_id="s2:t0",
                    session_id="s2",
                    turn_index=0,
                    role="user",
                    text="Alex attended the ancient exhibit today.",
                    timestamp="2023-01-15",
                ),
            ),
        )

        self.assertIn("Temporal calculation workpad", compiled.prompt)
        self.assertEqual(compiled.prompt.count(" <-> "), 1)

    def test_compiler_memory_order_is_default(self) -> None:
        compiler = EvidenceCompiler(
            max_evidence_items=0,
            max_evidence_chars=4000,
            max_memory_records=1,
        )
        route = RouteResult(information_need="profile_preference", signals=())
        compiled = compiler.compile(
            question="What tea does Alex prefer?",
            question_time=None,
            route=route,
            hits=(),
            evidence_turns=(),
            memory_records=(
                MemoryRecord(
                    memory_id="generic",
                    memory_type="fact",
                    text="Alex discussed a calendar reminder.",
                    source_ids=("s1:t0",),
                ),
                MemoryRecord(
                    memory_id="specific",
                    memory_type="preference",
                    text="Alex prefers jasmine tea.",
                    source_ids=("s1:t1",),
                    subject="Alex",
                    predicate="prefers",
                    value="jasmine tea",
                    timestamp="2023-05-02",
                ),
            ),
        )

        self.assertEqual(compiled.memory_records[0].memory_id, "generic")

    def test_question_overlap_memory_order_promotes_typed_memory(self) -> None:
        compiler = EvidenceCompiler(
            max_evidence_items=0,
            max_evidence_chars=4000,
            max_memory_records=1,
            memory_order="question_overlap",
            memory_layout="typed_sections",
        )
        route = RouteResult(information_need="profile_preference", signals=())
        compiled = compiler.compile(
            question="What tea does Alex prefer?",
            question_time=None,
            route=route,
            hits=(),
            evidence_turns=(),
            memory_records=(
                MemoryRecord(
                    memory_id="generic",
                    memory_type="fact",
                    text="Alex discussed a calendar reminder.",
                    source_ids=("s1:t0",),
                ),
                MemoryRecord(
                    memory_id="specific",
                    memory_type="preference",
                    text="Alex prefers jasmine tea.",
                    source_ids=("s1:t1",),
                    subject="Alex",
                    predicate="prefers",
                    value="jasmine tea",
                    timestamp="2023-05-02",
                ),
            ),
        )

        self.assertEqual(compiled.memory_records[0].memory_id, "specific")
        self.assertIn("Profile/preference/state memory:", compiled.prompt)
        self.assertNotIn("calendar reminder", compiled.prompt)

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
            compiled.prompt.index("Raw context table"),
        )

class _FakeReranker:
    def __init__(self, **kwargs: object) -> None:
        del kwargs

    def rerank(self, *, query: str, documents: list[str]) -> RerankResult:
        del query
        scores = tuple(10.0 if "Target" in document else 1.0 for document in documents)
        return RerankResult(
            scores=scores,
            response={
                "results": [
                    {"index": index, "relevance_score": score}
                    for index, score in enumerate(scores)
                ]
            },
            total_tokens=7,
        )


class _CountingAnswerer:
    def __init__(self) -> None:
        self.calls = 0

    def answer(self, context: object) -> AnswerResult:
        del context
        self.calls += 1
        return AnswerResult(
            answer="jasmine tea",
            model="fake",
            token_usage=TokenUsage(query_tokens=42),
            raw_response='{"usage":{"total_tokens":42}}',
        )


class _MalformedJsonAnswerer:
    def __init__(self) -> None:
        self.calls = 0

    def answer(self, context: object) -> AnswerResult:
        del context
        self.calls += 1
        raw_content = (
            '{"reasoning":"quoted text broke the JSON: "bad quote"",'
            '"answer":"jasmine tea"}'
        )
        return AnswerResult(
            answer=raw_content,
            model="fake",
            token_usage=TokenUsage(query_tokens=7),
            raw_response=json.dumps(
                {
                    "content": raw_content,
                    "usage": {"total_tokens": 7},
                }
            ),
        )


class _StructuredJsonResidueAnswerer:
    def __init__(self) -> None:
        self.calls = 0

    def answer(self, context: object) -> AnswerResult:
        del context
        self.calls += 1
        raw_content = (
            '{"reasoning":"ok","sufficient":true,"answer_type":"fact",'
            '"evidence_report":[{"status":"support"}],"answer":"jasmine tea"}'
        )
        return AnswerResult(
            answer=raw_content,
            model="fake",
            token_usage=TokenUsage(query_tokens=7),
            raw_response=json.dumps(
                {
                    "content": raw_content,
                    "usage": {"total_tokens": 7},
                }
            ),
        )


if __name__ == "__main__":
    unittest.main()
