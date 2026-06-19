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
from memory.answer import (
    CachedAnswerer,
    OpenAICompatibleAnswerer,
    _message_text,
    _parse_answer_content,
)
from memory.build import BuiltMemory, MemoryRecord
from memory.compiler import EvidenceCompiler
from memory.finalize import (
    finalize_structured_answer,
    guard_source_grounded_answer,
    raw_response_content,
)
from memory.repair import (
    _lifecycle_slot_trigger_reasons,
    build_repair_prompt,
    repair_trigger_reasons,
)
from memory.rerank import RerankResult, rerank_hits_filter_preserve_order
from memory.retrieval import (
    MemoryHit,
    TurnWindowBM25Retriever,
    build_turn_window_documents,
    turn_window_hits_to_source_hits,
)
from data.io import load_prediction_jsonl
from memory.pipeline import (
    Stage1Pipeline,
    _align_build_memory_sources,
    _compiler_memory_records,
    _context_manifest,
    _memory_lifecycle_manifest,
    _memory_slot_chain_source_hits,
    _memory_records_by_source,
    _neighbor_turns_for_rerank,
    _rerank_exchange_guard,
    _selected_context_content_terms,
    _selected_context_source_grounded_match,
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
        self.assertTrue(result["trace"]["memory_lifecycle_manifest"]["trace_only"])

    def test_context_manifest_tracks_source_backed_memory_activation(self) -> None:
        turns = (
            Turn(
                source_id="s1:t0",
                session_id="s1",
                turn_index=0,
                role="user",
                text="Alex asked about tea.",
            ),
            Turn(
                source_id="s1:t1",
                session_id="s1",
                turn_index=1,
                role="assistant",
                text="Alex prefers jasmine tea.",
            ),
            Turn(
                source_id="s1:t2",
                session_id="s1",
                turn_index=2,
                role="user",
                text="Alex later bought coffee.",
            ),
        )
        store = RawEvidenceStore(turns)
        record = MemoryRecord(
            memory_id="m1",
            memory_type="preference",
            text="Alex prefers jasmine tea.",
            source_ids=("s1:t1", "s1:t2"),
            subject="Alex",
            predicate="prefers",
            value="jasmine tea",
        )
        route = RouteResult("profile_preference", ("profile",))
        manifest = _context_manifest(
            store=store,
            route=route,
            lexical_hits=(
                RetrievalHit(
                    source_id="s1:t1",
                    score=1.0,
                    rank=1,
                    retriever="lexical",
                    matched_terms=("jasmine", "tea"),
                ),
            ),
            dense_hits=(),
            memory_hits=(MemoryHit(record=record, score=2.0, rank=1),),
            memory_source_hits=(
                RetrievalHit(
                    source_id="s1:t2",
                    score=2.0,
                    rank=1,
                    retriever="memory_source",
                ),
            ),
            memory_slot_chain_source_hits=(),
            turn_window_source_hits=(),
            pre_context_budget_hits=(
                RetrievalHit("s1:t1", 1.0, 1, "lexical"),
                RetrievalHit("s1:t2", 2.0, 2, "memory_source"),
            ),
            retrieval_hits=(RetrievalHit("s1:t1", 1.0, 1, "lexical"),),
            context_budget_trace={
                "applied": True,
                "dropped_count": 1,
                "dropped_source_ids": ["s1:t2"],
            },
            context_budget_audit={"safe_for_current_prompt": True},
            evidence_turns=(turns[1],),
            selected_context={
                "materialized_count": 1,
                "materialized_source_ids": ["s1:t1"],
                "enabled": True,
                "applied": True,
                "eligible": True,
                "question_reference": False,
                "risk_audit": {
                    "applied": True,
                    "safe_source_ids": [],
                    "risk_source_ids": ["s1:t1"],
                    "risk_reasons": {"s1:t1": "insufficient_slot_coverage"},
                    "text_source": "prompt_visible_materialized_context",
                    "materialized_text_audit_count": 1,
                    "raw_center_text_audit_count": 0,
                },
            },
            built_memory_records=(record,),
            compiler_memory_records=(record,),
            evidence_rows=(
                EvidenceRow(
                    source_id="s1:t1",
                    session_id="s1",
                    turn_index=1,
                    role="assistant",
                    text="Alex prefers jasmine tea.",
                    timestamp=None,
                    retrieval_rank=1,
                    retrieval_score=1.0,
                ),
            ),
            compiled_context_chars=1234,
        )

        self.assertTrue(manifest["trace_only"])
        self.assertEqual(manifest["information_need"], "profile_preference")
        self.assertEqual(
            manifest["source_flow"]["context_budget_dropped_source_ids"],
            ["s1:t2"],
        )
        self.assertEqual(
            manifest["typed_memory"]["retrieved"]["type_counts"],
            {"preference": 1},
        )
        self.assertEqual(
            manifest["typed_memory"]["compiler"]["visible_source_count"], 1
        )
        self.assertEqual(
            manifest["coverage"]["final_evidence_from_typed_memory_source_count"],
            1,
        )
        self.assertEqual(
            manifest["coverage"]["selected_context_final_row_count"], 1
        )
        organization = manifest["context_organization"]
        self.assertTrue(organization["trace_only"])
        self.assertEqual(organization["prompt_context_chars"], 1234)
        self.assertEqual(organization["context_budget"]["dropped_count"], 1)
        selected_context_ledger = organization["selected_context"]
        self.assertTrue(selected_context_ledger["trace_only"])
        self.assertEqual(selected_context_ledger["risk_count"], 1)
        self.assertEqual(
            selected_context_ledger["risk_reason_counts"],
            {"insufficient_slot_coverage": 1},
        )
        self.assertEqual(
            selected_context_ledger["risk_from_typed_memory_source_count"],
            1,
        )
        self.assertEqual(selected_context_ledger["risk_not_final_row_count"], 0)
        severity = selected_context_ledger["source_flow_severity"]
        self.assertTrue(severity["trace_only"])
        self.assertEqual(severity["counts"]["raw_evidence_backed"], 1)
        self.assertEqual(severity["counts"]["not_final_evidence"], 0)
        self.assertEqual(severity["counts"]["typed_memory_backed"], 1)
        self.assertEqual(severity["counts"]["memory_projected_backed"], 0)
        self.assertEqual(severity["guarded_rerank_eligible_count"], 0)
        self.assertEqual(
            severity["guarded_rerank_blocked_by_final_evidence_count"], 1
        )
        self.assertEqual(
            selected_context_ledger["risk_details"][0]["source_id"], "s1:t1"
        )

    def test_context_manifest_tracks_evidence_pressure(self) -> None:
        turns = (
            Turn("s1:t0", "s1", 0, "user", "Alex booked the cafe."),
            Turn("s1:t1", "s1", 1, "assistant", "The cafe booking is for Tuesday."),
            Turn("s2:t0", "s2", 0, "user", "Alex also mentioned tea."),
        )
        store = RawEvidenceStore(turns)
        route = RouteResult("fact_lookup", ("fact",))
        manifest = _context_manifest(
            store=store,
            route=route,
            lexical_hits=(),
            dense_hits=(),
            memory_hits=(),
            memory_source_hits=(),
            memory_slot_chain_source_hits=(),
            turn_window_source_hits=(),
            pre_context_budget_hits=(),
            retrieval_hits=(),
            context_budget_trace={"applied": False},
            context_budget_audit={},
            evidence_turns=turns,
            selected_context={
                "materialized_source_ids": [],
                "risk_audit": {"applied": False},
            },
            built_memory_records=(),
            compiler_memory_records=(),
            evidence_rows=(
                EvidenceRow(
                    source_id="s1:t0",
                    session_id="s1",
                    turn_index=0,
                    role="user",
                    text="Alex booked the cafe.",
                    timestamp=None,
                    retrieval_rank=1,
                    retrieval_score=1.0,
                ),
                EvidenceRow(
                    source_id="s1:t1",
                    session_id="s1",
                    turn_index=1,
                    role="assistant",
                    text="The cafe booking is for Tuesday.",
                    timestamp=None,
                    retrieval_rank=33,
                    retrieval_score=0.4,
                ),
                EvidenceRow(
                    source_id="s2:t0",
                    session_id="s2",
                    turn_index=0,
                    role="user",
                    text="Alex also mentioned tea.",
                    timestamp=None,
                    retrieval_rank=41,
                    retrieval_score=0.2,
                ),
            ),
            compiled_context_chars=900,
        )

        pressure = manifest["context_organization"]["evidence_pressure"]
        self.assertTrue(pressure["trace_only"])
        self.assertEqual(pressure["row_count"], 3)
        self.assertEqual(pressure["session_count"], 2)
        self.assertEqual(pressure["max_rows_per_session"], 2)
        self.assertEqual(pressure["adjacent_turn_pair_count"], 1)
        self.assertEqual(pressure["tail_after_rank_32"]["row_count"], 2)
        self.assertEqual(pressure["tail_after_rank_40"]["row_count"], 1)
        self.assertEqual(
            pressure["tail_after_rank_40"]["source_ids"],
            ["s2:t0"],
        )

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

    def test_pipeline_selected_context_compact_format_preserves_evidence(
        self,
    ) -> None:
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
                    "max_center_chars": 0,
                    "context_format": "compact",
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
        row_text = "\n".join(
            row["text"]
            for row in result["trace"]["compiled_context"]["evidence_rows"]
        )

        self.assertTrue(trace["applied"])
        self.assertEqual(trace["context_format"], "compact")
        self.assertIn("Same-session context:", row_text)
        self.assertIn("- center (2024-01-01) | assistant:", row_text)
        self.assertIn("- near (2024-01-01) | user:", row_text)
        self.assertNotIn("Local dialogue context from the same session", row_text)
        self.assertIn("Nothing is Impossible", row_text)

    def test_selected_context_can_require_question_reference(self) -> None:
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
                    "require_question_reference": True,
                    "information_needs": ["fact_lookup"],
                },
            },
            "compiler": {
                "prompt_mode": "external_naive",
                "max_evidence_items": 2,
                "max_evidence_chars": 4000,
            },
            "answer": {"fallback_answer": "unknown"},
        }
        turns = (
            Turn(
                source_id="s1:t0",
                session_id="s1",
                turn_index=0,
                role="user",
                text='Alex read "Nothing is Impossible" last year.',
            ),
            Turn(
                source_id="s1:t1",
                session_id="s1",
                turn_index=1,
                role="assistant",
                text="This book inspired Alex to keep training.",
            ),
        )

        plain_result = Stage1Pipeline(config).predict(
            PredictionRequest(question="What inspired Alex?", turns=turns)
        )
        plain_trace = plain_result["trace"]["retrieval"]["selected_context"]
        plain_row_text = "\n".join(
            row["text"]
            for row in plain_result["trace"]["compiled_context"]["evidence_rows"]
        )

        self.assertFalse(plain_trace["applied"])
        self.assertFalse(plain_trace["question_reference"])
        self.assertEqual(plain_trace["skip_reason"], "question_reference_required")
        self.assertNotIn("Local dialogue context from the same session", plain_row_text)

        relative_that_result = Stage1Pipeline(config).predict(
            PredictionRequest(
                question="What detail that would help Alex?",
                turns=turns,
            )
        )
        relative_that_trace = relative_that_result["trace"]["retrieval"][
            "selected_context"
        ]

        self.assertFalse(relative_that_trace["applied"])
        self.assertFalse(relative_that_trace["question_reference"])

        referenced_result = Stage1Pipeline(config).predict(
            PredictionRequest(
                question="What else inspired Alex about that book?",
                turns=turns,
            )
        )
        referenced_trace = referenced_result["trace"]["retrieval"]["selected_context"]
        referenced_row_text = "\n".join(
            row["text"]
            for row in referenced_result["trace"]["compiled_context"]["evidence_rows"]
        )

        self.assertTrue(referenced_trace["applied"])
        self.assertTrue(referenced_trace["question_reference"])
        self.assertIn(
            "Local dialogue context from the same session",
            referenced_row_text,
        )

    def test_selected_context_can_require_question_reference_for_long_centers(
        self,
    ) -> None:
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
                    "max_center_chars": 400,
                    "require_anaphora": True,
                    "require_question_reference_min_center_chars": 80,
                    "information_needs": ["fact_lookup"],
                },
            },
            "compiler": {
                "prompt_mode": "external_naive",
                "max_evidence_items": 2,
                "max_evidence_chars": 4000,
            },
            "answer": {"fallback_answer": "unknown"},
        }
        short_turns = (
            Turn(
                source_id="s1:t0",
                session_id="s1",
                turn_index=0,
                role="user",
                text='Alex read "Nothing is Impossible" last year.',
            ),
            Turn(
                source_id="s1:t1",
                session_id="s1",
                turn_index=1,
                role="assistant",
                text="This book inspired Alex to keep training.",
            ),
        )
        short_result = Stage1Pipeline(config).predict(
            PredictionRequest(question="What inspired Alex?", turns=short_turns)
        )
        short_trace = short_result["trace"]["retrieval"]["selected_context"]

        self.assertTrue(short_trace["applied"])
        self.assertFalse(short_trace["question_reference"])
        self.assertEqual(short_trace["skipped_question_reference_center_count"], 0)

        long_center_text = (
            "This book inspired Alex to keep training because the story connected "
            "to Alex's marathon preparation, weekly practice routine, and long-term "
            "goal of staying disciplined."
        )
        long_turns = (
            short_turns[0],
            Turn(
                source_id="s1:t1",
                session_id="s1",
                turn_index=1,
                role="assistant",
                text=long_center_text,
            ),
        )
        plain_result = Stage1Pipeline(config).predict(
            PredictionRequest(question="What inspired Alex?", turns=long_turns)
        )
        plain_trace = plain_result["trace"]["retrieval"]["selected_context"]
        plain_row_text = "\n".join(
            row["text"]
            for row in plain_result["trace"]["compiled_context"]["evidence_rows"]
        )

        self.assertFalse(plain_trace["applied"])
        self.assertFalse(plain_trace["question_reference"])
        self.assertEqual(plain_trace["skipped_question_reference_center_count"], 1)
        self.assertEqual(
            plain_trace["skipped_question_reference_center_source_ids"], ["s1:t1"]
        )
        self.assertNotIn("Local dialogue context from the same session", plain_row_text)

        referenced_result = Stage1Pipeline(config).predict(
            PredictionRequest(
                question="What else inspired Alex about that book?",
                turns=long_turns,
            )
        )
        referenced_trace = referenced_result["trace"]["retrieval"][
            "selected_context"
        ]

        self.assertTrue(referenced_trace["applied"])
        self.assertTrue(referenced_trace["question_reference"])
        self.assertEqual(
            referenced_trace["skipped_question_reference_center_count"], 0
        )

    def test_selected_context_source_grounded_gate_keeps_self_event(
        self,
    ) -> None:
        config = {
            "retrieval": {
                "top_k": 3,
                "max_top_k": 3,
                "neighbor_window": 0,
                "selected_context": {
                    "enabled": True,
                    "window_before": 1,
                    "window_after": 1,
                    "max_rows": 3,
                    "max_neighbor_chars": 120,
                    "require_anaphora": True,
                    "require_source_grounded_self_reference": True,
                    "source_grounded_min_terms": 2,
                    "source_grounded_min_coverage": 0.6,
                    "information_needs": ["temporal_lookup"],
                },
            },
            "compiler": {
                "prompt_mode": "external_naive",
                "max_evidence_items": 3,
                "max_evidence_chars": 4000,
            },
            "answer": {"fallback_answer": "unknown"},
        }
        turns = (
            Turn(
                source_id="s1:t0",
                session_id="s1",
                turn_index=0,
                role="Joanna",
                text="Any plans for the weekend?",
                timestamp="10:57 am on 22 August, 2022",
            ),
            Turn(
                source_id="s1:t1",
                session_id="s1",
                turn_index=1,
                role="Nate",
                text="I'm taking some time off this weekend to chill with my pets.",
                timestamp="10:57 am on 22 August, 2022",
            ),
            Turn(
                source_id="s1:t2",
                session_id="s1",
                turn_index=2,
                role="Joanna",
                text="That sounds relaxing.",
                timestamp="10:57 am on 22 August, 2022",
            ),
        )

        result = Stage1Pipeline(config).predict(
            PredictionRequest(
                question="When did Nate take time off to chill with his pets?",
                turns=turns,
            )
        )
        trace = result["trace"]["retrieval"]["selected_context"]
        row_text = "\n".join(
            row["text"] for row in result["trace"]["compiled_context"]["evidence_rows"]
        )

        self.assertTrue(trace["applied"])
        self.assertIn("s1:t1", trace["materialized_source_ids"])
        self.assertEqual(trace["skipped_source_grounded_count"], 0)
        self.assertIn("Local dialogue context from the same session", row_text)

    def test_selected_context_source_grounded_gate_blocks_second_person_binding(
        self,
    ) -> None:
        config = {
            "retrieval": {
                "top_k": 3,
                "max_top_k": 3,
                "neighbor_window": 0,
                "selected_context": {
                    "enabled": True,
                    "window_before": 1,
                    "window_after": 1,
                    "max_rows": 3,
                    "max_neighbor_chars": 120,
                    "require_anaphora": True,
                    "require_source_grounded_self_reference": True,
                    "source_grounded_min_terms": 2,
                    "source_grounded_min_coverage": 0.6,
                    "information_needs": ["temporal_lookup"],
                },
            },
            "compiler": {
                "prompt_mode": "external_naive",
                "max_evidence_items": 3,
                "max_evidence_chars": 4000,
            },
            "answer": {"fallback_answer": "unknown"},
        }
        turns = (
            Turn(
                source_id="s1:t0",
                session_id="s1",
                turn_index=0,
                role="James",
                text=(
                    "That's my sister and my dogs. We were chilling together "
                    "yesterday."
                ),
                timestamp="9:49 am on 22 July, 2022",
            ),
            Turn(
                source_id="s1:t1",
                session_id="s1",
                turn_index=1,
                role="John",
                text=(
                    "Wow, they look so happy! It's awesome that you get to spend "
                    "time with your sister and your furry friends."
                ),
                timestamp="9:49 am on 22 July, 2022",
            ),
            Turn(
                source_id="s1:t2",
                session_id="s1",
                turn_index=2,
                role="James",
                text="I'm blessed to have a close bond with my sister and pets.",
                timestamp="9:49 am on 22 July, 2022",
            ),
        )

        result = Stage1Pipeline(config).predict(
            PredictionRequest(
                question="When did John spend time with his sister and dogs?",
                turns=turns,
            )
        )
        trace = result["trace"]["retrieval"]["selected_context"]
        row_text = "\n".join(
            row["text"] for row in result["trace"]["compiled_context"]["evidence_rows"]
        )

        self.assertFalse(trace["applied"])
        self.assertIn("s1:t1", trace["skipped_source_grounded_source_ids"])
        self.assertEqual(
            trace["skipped_source_grounded_reasons"]["s1:t1"],
            "missing_self_reference",
        )
        self.assertNotIn("Local dialogue context from the same session", row_text)

    def test_selected_context_materialized_source_gate_keeps_grounded_context(
        self,
    ) -> None:
        config = {
            "retrieval": {
                "top_k": 3,
                "max_top_k": 3,
                "neighbor_window": 0,
                "selected_context": {
                    "enabled": True,
                    "window_before": 1,
                    "window_after": 0,
                    "max_rows": 3,
                    "max_neighbor_chars": 120,
                    "require_anaphora": True,
                    "require_materialized_source_grounded": True,
                    "materialized_source_grounded_min_terms": 2,
                    "materialized_source_grounded_min_coverage": 0.6,
                    "information_needs": ["fact_lookup"],
                },
            },
            "compiler": {
                "prompt_mode": "external_naive",
                "max_evidence_items": 3,
                "max_evidence_chars": 4000,
            },
            "answer": {"fallback_answer": "unknown"},
        }
        turns = (
            Turn(
                source_id="s1:t0",
                session_id="s1",
                turn_index=0,
                role="Dana",
                text="The dessert came from Bell Bakery.",
                timestamp="10:00 am on 1 May, 2024",
            ),
            Turn(
                source_id="s1:t1",
                session_id="s1",
                turn_index=1,
                role="Dana",
                text="That's where I picked up dessert.",
                timestamp="10:01 am on 1 May, 2024",
            ),
        )

        result = Stage1Pipeline(config).predict(
            PredictionRequest(
                question=(
                    "Where did Dana say she picked up dessert from Bell Bakery?"
                ),
                turns=turns,
            )
        )
        trace = result["trace"]["retrieval"]["selected_context"]
        row_text = "\n".join(
            row["text"] for row in result["trace"]["compiled_context"]["evidence_rows"]
        )

        self.assertTrue(trace["applied"])
        self.assertIn("s1:t1", trace["materialized_source_ids"])
        self.assertEqual(trace["skipped_materialized_source_grounded_count"], 0)
        self.assertIn("Local dialogue context from the same session", row_text)

    def test_selected_context_materialized_source_gate_blocks_low_coverage_context(
        self,
    ) -> None:
        config = {
            "retrieval": {
                "top_k": 3,
                "max_top_k": 3,
                "neighbor_window": 0,
                "selected_context": {
                    "enabled": True,
                    "window_before": 1,
                    "window_after": 0,
                    "max_rows": 3,
                    "max_neighbor_chars": 120,
                    "require_anaphora": True,
                    "require_materialized_source_grounded": True,
                    "materialized_source_grounded_min_terms": 2,
                    "materialized_source_grounded_min_coverage": 0.6,
                    "information_needs": ["fact_lookup"],
                },
            },
            "compiler": {
                "prompt_mode": "external_naive",
                "max_evidence_items": 3,
                "max_evidence_chars": 4000,
            },
            "answer": {"fallback_answer": "unknown"},
        }
        turns = (
            Turn(
                source_id="s1:t0",
                session_id="s1",
                turn_index=0,
                role="Dana",
                text="We talked about a museum exhibit.",
                timestamp="10:00 am on 1 May, 2024",
            ),
            Turn(
                source_id="s1:t1",
                session_id="s1",
                turn_index=1,
                role="Dana",
                text="That's where I picked up dessert.",
                timestamp="10:01 am on 1 May, 2024",
            ),
        )

        result = Stage1Pipeline(config).predict(
            PredictionRequest(
                question=(
                    "Where did Dana say she picked up dessert from Bell Bakery?"
                ),
                turns=turns,
            )
        )
        trace = result["trace"]["retrieval"]["selected_context"]
        row_text = "\n".join(
            row["text"] for row in result["trace"]["compiled_context"]["evidence_rows"]
        )

        self.assertFalse(trace["applied"])
        self.assertIn("s1:t1", trace["skipped_materialized_source_grounded_source_ids"])
        self.assertEqual(
            trace["skipped_materialized_source_grounded_reasons"]["s1:t1"],
            "insufficient_slot_coverage",
        )
        self.assertNotIn("Local dialogue context from the same session", row_text)

    def test_selected_context_timestamp_policy_keeps_only_center_timestamp(
        self,
    ) -> None:
        config = {
            "retrieval": {
                "top_k": 3,
                "max_top_k": 3,
                "neighbor_window": 0,
                "selected_context": {
                    "enabled": True,
                    "window_before": 1,
                    "window_after": 0,
                    "max_rows": 3,
                    "max_neighbor_chars": 120,
                    "timestamp_policy": "center_only",
                    "require_anaphora": True,
                    "information_needs": ["temporal_lookup"],
                },
            },
            "compiler": {
                "prompt_mode": "external_naive",
                "max_evidence_items": 3,
                "max_evidence_chars": 4000,
            },
            "answer": {"fallback_answer": "unknown"},
        }
        turns = (
            Turn(
                source_id="s1:t0",
                session_id="s1",
                turn_index=0,
                role="Alex",
                text="I visited the art museum on Monday.",
                timestamp="9:00 am on 1 May, 2024",
            ),
            Turn(
                source_id="s1:t1",
                session_id="s1",
                turn_index=1,
                role="Alex",
                text="That was a great trip.",
                timestamp="9:05 am on 1 May, 2024",
            ),
        )

        result = Stage1Pipeline(config).predict(
            PredictionRequest(
                question="When was Alex's great trip?",
                turns=turns,
            )
        )
        trace = result["trace"]["retrieval"]["selected_context"]
        row_text = "\n".join(
            row["text"] for row in result["trace"]["compiled_context"]["evidence_rows"]
        )

        self.assertTrue(trace["applied"])
        self.assertEqual(trace["timestamp_policy"], "center_only")
        self.assertIn("I visited the art museum on Monday.", row_text)
        self.assertIn(
            "- selected turn (9:05 am on 1 May, 2024) | Alex: That was a great trip.",
            row_text,
        )
        self.assertIn(
            "- nearby turn | Alex: I visited the art museum on Monday.",
            row_text,
        )
        self.assertNotIn(
            "- nearby turn (9:00 am on 1 May, 2024)",
            row_text,
        )

    def test_selected_context_source_grounded_match_normalizes_query_terms(
        self,
    ) -> None:
        ferrari_question_terms = _selected_context_content_terms(
            "How many Ferraris does Calvin own?"
        )
        self.assertIn("ferrari", ferrari_question_terms)
        self.assertNotIn("ferraris", ferrari_question_terms)
        self.assertNotIn("many", ferrari_question_terms)
        self.assertNotIn("own", ferrari_question_terms)

        mom_question_terms = _selected_context_content_terms(
            "How did Deborah's mom support her yoga practice when she first started?"
        )
        self.assertIn("mom", mom_question_terms)
        self.assertIn("mum", mom_question_terms)
        self.assertIn("support", mom_question_terms)

        match = _selected_context_source_grounded_match(
            question=(
                "How did Deborah's mom support her yoga practice when she "
                "first started?"
            ),
            turn=Turn(
                source_id="s1:t0",
                session_id="s1",
                turn_index=0,
                role="Deborah",
                text=(
                    "When I first started doing yoga, my mum was my biggest "
                    "fan and source of motivation. She often came to classes."
                ),
                timestamp="2:14 pm on 3 September, 2023",
            ),
            min_terms=2,
            min_coverage=0.6,
            role_sensitive=False,
        )
        self.assertTrue(match["matched"])

    def test_selected_context_risk_audit_is_trace_only(self) -> None:
        config = {
            "retrieval": {
                "top_k": 3,
                "max_top_k": 3,
                "neighbor_window": 0,
                "selected_context": {
                    "enabled": True,
                    "window_before": 1,
                    "window_after": 1,
                    "max_rows": 3,
                    "max_neighbor_chars": 120,
                    "require_anaphora": True,
                    "information_needs": ["temporal_lookup"],
                    "risk_audit": {
                        "enabled": True,
                        "information_needs": ["temporal_lookup"],
                        "source_grounded_min_terms": 2,
                        "source_grounded_min_coverage": 0.6,
                    },
                },
            },
            "compiler": {
                "prompt_mode": "external_naive",
                "max_evidence_items": 3,
                "max_evidence_chars": 4000,
            },
            "answer": {"fallback_answer": "unknown"},
        }
        turns = (
            Turn(
                source_id="s1:t0",
                session_id="s1",
                turn_index=0,
                role="James",
                text=(
                    "That's my sister and my dogs. We were chilling together "
                    "yesterday."
                ),
                timestamp="9:49 am on 22 July, 2022",
            ),
            Turn(
                source_id="s1:t1",
                session_id="s1",
                turn_index=1,
                role="John",
                text=(
                    "Wow, they look so happy! It's awesome that you get to spend "
                    "time with your sister and your furry friends."
                ),
                timestamp="9:49 am on 22 July, 2022",
            ),
            Turn(
                source_id="s1:t2",
                session_id="s1",
                turn_index=2,
                role="James",
                text="I'm blessed to have a close bond with my sister and pets.",
                timestamp="9:49 am on 22 July, 2022",
            ),
        )
        request = PredictionRequest(
            question="When did John spend time with his sister and dogs?",
            turns=turns,
        )

        audited_result = Stage1Pipeline(config).predict(request)
        audit_off_config = {
            **config,
            "retrieval": {
                **config["retrieval"],
                "selected_context": {
                    **config["retrieval"]["selected_context"],
                    "risk_audit": {
                        **config["retrieval"]["selected_context"]["risk_audit"],
                        "enabled": False,
                    },
                },
            },
        }
        plain_result = Stage1Pipeline(audit_off_config).predict(request)

        audited_trace = audited_result["trace"]["retrieval"]["selected_context"]
        risk_audit = audited_trace["risk_audit"]
        row_text = "\n".join(
            row["text"]
            for row in audited_result["trace"]["compiled_context"]["evidence_rows"]
        )

        self.assertTrue(audited_trace["applied"])
        self.assertIn("s1:t1", audited_trace["materialized_source_ids"])
        self.assertIn("Local dialogue context from the same session", row_text)
        self.assertTrue(risk_audit["trace_only"])
        self.assertTrue(risk_audit["applied"])
        self.assertEqual(risk_audit["text_source"], "prompt_visible_materialized_context")
        self.assertIn("s1:t1", risk_audit["safe_source_ids"])
        self.assertNotIn("s1:t1", risk_audit["risk_source_ids"])
        self.assertEqual(
            risk_audit["materialized_text_audit_count"],
            risk_audit["audited_count"],
        )
        self.assertEqual(risk_audit["raw_center_text_audit_count"], 0)
        self.assertEqual(
            audited_result["trace"]["compiled_context"]["prompt"],
            plain_result["trace"]["compiled_context"]["prompt"],
        )
        self.assertEqual(audited_result["answer"], plain_result["answer"])

    def test_selected_context_route_override_is_scoped(self) -> None:
        config = {
            "retrieval": {
                "top_k": 2,
                "max_top_k": 2,
                "neighbor_window": 0,
                "selected_context": {
                    "enabled": True,
                    "window_before": 0,
                    "window_after": 0,
                    "max_rows": 1,
                    "max_neighbor_chars": 80,
                    "require_anaphora": True,
                    "information_needs": ["list_count"],
                    "route_overrides": {
                        "temporal_lookup": {
                            "enabled": True,
                            "window_before": 1,
                            "window_after": 0,
                            "max_rows": 1,
                            "max_neighbor_chars": 80,
                            "require_anaphora": True,
                            "information_needs": ["temporal_lookup"],
                        }
                    },
                },
            },
            "compiler": {
                "prompt_mode": "external_naive",
                "max_evidence_items": 2,
                "max_evidence_chars": 4000,
            },
            "answer": {"fallback_answer": "unknown"},
        }
        turns = (
            Turn(
                source_id="s1:t0",
                session_id="s1",
                turn_index=0,
                role="user",
                text="Alex visited the museum.",
            ),
            Turn(
                source_id="s1:t1",
                session_id="s1",
                turn_index=1,
                role="assistant",
                text="That museum visit happened on Monday.",
            ),
        )

        temporal_result = Stage1Pipeline(config).predict(
            PredictionRequest(question="When did Alex visit the museum?", turns=turns)
        )
        temporal_trace = temporal_result["trace"]["retrieval"]["selected_context"]
        temporal_row_text = "\n".join(
            row["text"]
            for row in temporal_result["trace"]["compiled_context"]["evidence_rows"]
        )

        self.assertTrue(temporal_trace["applied"])
        self.assertEqual(temporal_trace["route_override"], "temporal_lookup")
        self.assertIn("Local dialogue context from the same session", temporal_row_text)
        self.assertIn("Alex visited the museum", temporal_row_text)

        fact_result = Stage1Pipeline(config).predict(
            PredictionRequest(question="What did Alex visit?", turns=turns)
        )
        fact_trace = fact_result["trace"]["retrieval"]["selected_context"]

        self.assertFalse(fact_trace["applied"])
        self.assertIsNone(fact_trace["route_override"])

    def test_grounded_inference_contract_is_question_gated(self) -> None:
        compiler = EvidenceCompiler(
            max_evidence_items=2,
            max_evidence_chars=4000,
            prompt_mode="external_naive",
            evidence_report_contract=True,
            grounded_inference_contract=True,
        )
        rows = (
            Turn(
                source_id="s1:t0",
                session_id="s1",
                turn_index=0,
                role="user",
                text="Alex has collected classic children's books for years.",
                timestamp="2024-01-01",
            ),
        )
        hits = (
            RetrievalHit(
                source_id="s1:t0",
                score=1.0,
                rank=1,
                retriever="test",
            ),
        )
        route = RouteResult("fact_lookup", ("generic",), 4)

        inference_context = compiler.compile(
            question="Would Alex likely have Dr. Seuss books on the shelf?",
            question_time=None,
            route=route,
            hits=hits,
            evidence_turns=rows,
        )
        fact_context = compiler.compile(
            question="What books does Alex collect?",
            question_time=None,
            route=route,
            hits=hits,
            evidence_turns=rows,
        )

        self.assertIn("Grounded Inference Discipline", inference_context.prompt)
        self.assertIn("memory-grounded inference", inference_context.prompt)
        self.assertNotIn("Grounded Inference Discipline", fact_context.prompt)
        self.assertNotIn("question_type", inference_context.prompt)
        self.assertNotIn("sample_id", inference_context.prompt)

    def test_grounded_inference_modal_gate_excludes_plain_advice(self) -> None:
        compiler = EvidenceCompiler(
            max_evidence_items=2,
            max_evidence_chars=4000,
            prompt_mode="external_naive",
            evidence_report_contract=True,
            grounded_inference_contract=True,
            grounded_inference_gate="modal_only",
        )
        rows = (
            Turn(
                source_id="s1:t0",
                session_id="s1",
                turn_index=0,
                role="user",
                text="Alex has a cat that sheds in the living room.",
                timestamp="2024-01-01",
            ),
        )
        hits = (RetrievalHit("s1:t0", 1.0, 1, "test"),)
        route = RouteResult("fact_lookup", ("generic",), 4)

        modal_context = compiler.compile(
            question="Do you think it might be my living room?",
            question_time=None,
            route=route,
            hits=hits,
            evidence_turns=rows,
        )
        advice_context = compiler.compile(
            question="I am trying to decide whether to buy now or wait. What do you think?",
            question_time=None,
            route=route,
            hits=hits,
            evidence_turns=rows,
        )

        self.assertIn("Grounded Inference Discipline", modal_context.prompt)
        self.assertNotIn("Grounded Inference Discipline", advice_context.prompt)
        self.assertNotIn("question_type", modal_context.prompt)

    def test_selected_context_skips_long_center_turns(self) -> None:
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
                    "max_center_chars": 80,
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
        long_anaphoric_text = " ".join(
            [
                "This book was excellent and Alex kept returning to its ideas"
                " during training."
            ]
            * 4
        )
        request = PredictionRequest(
            question="What books has Alex read?",
            turns=(
                Turn(
                    source_id="s1:t0",
                    session_id="s1",
                    turn_index=0,
                    role="user",
                    text='Alex read "Nothing is Impossible" last year.',
                ),
                Turn(
                    source_id="s1:t1",
                    session_id="s1",
                    turn_index=1,
                    role="assistant",
                    text=long_anaphoric_text,
                ),
            ),
        )

        result = Stage1Pipeline(config).predict(request)
        trace = result["trace"]["retrieval"]["selected_context"]
        rows = result["trace"]["compiled_context"]["evidence_rows"]
        row_by_source = {row["source_id"]: row for row in rows}

        self.assertFalse(trace["applied"])
        self.assertEqual(trace["materialized_count"], 0)
        self.assertEqual(trace["skipped_long_center_count"], 1)
        self.assertEqual(trace["skipped_long_center_source_ids"], ["s1:t1"])
        self.assertNotIn(
            "Local dialogue context from the same session",
            row_by_source["s1:t1"]["text"],
        )

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

    def test_granularity_profile_audit_is_trace_only(self) -> None:
        config = {
            "retrieval": {
                "top_k": 4,
                "max_top_k": 4,
                "neighbor_window": 0,
                "granularity_profile_audit": {"enabled": True},
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
                        "retrieval": {"top_k": 1, "max_top_k": 1},
                        "selected_context": {"enabled": False},
                        "compiler": {"operation_workpad": True},
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
                "operation_workpad": False,
            },
            "answer": {"fallback_answer": "unknown"},
        }
        request = PredictionRequest(
            question="How many books has Alex read?",
            turns=(
                Turn("s:t0", "s", 0, "user", " ".join(["Alex read Dune."] * 20)),
                Turn(
                    "s:t1",
                    "s",
                    1,
                    "assistant",
                    " ".join(["This book was excellent."] * 20),
                ),
            ),
        )

        audited_result = Stage1Pipeline(config).predict(request)
        audit_off_config = {
            **config,
            "retrieval": {
                **config["retrieval"],
                "granularity_profile_audit": {"enabled": False},
            },
        }
        plain_result = Stage1Pipeline(audit_off_config).predict(request)

        audit = audited_result["trace"]["retrieval"]["granularity_profile_audit"]
        self.assertTrue(audit["trace_only"])
        self.assertTrue(audit["applied"])
        self.assertTrue(audit["selected"])
        self.assertEqual(audit["selected_profile_name"], "long_turn_precision")
        self.assertTrue(audit["behavior_affecting"])
        self.assertIn("retrieval", audit["behavior_sections"])
        self.assertIn("selected_context", audit["behavior_sections"])
        self.assertIn("compiler", audit["behavior_sections"])
        self.assertIn(
            "avg_turn_length_selected_profile",
            audit["risk_reasons"],
        )
        self.assertEqual(
            audited_result["trace"]["compiled_context"]["prompt"],
            plain_result["trace"]["compiled_context"]["prompt"],
        )
        self.assertEqual(audited_result["answer"], plain_result["answer"])

    def test_granularity_profile_can_select_by_total_context_pressure(self) -> None:
        config = {
            "retrieval": {
                "top_k": 4,
                "max_top_k": 4,
                "neighbor_window": 0,
                "granularity_profile_audit": {"enabled": True},
                "granularity_profiles": [
                    {
                        "name": "long_context_pressure",
                        "min_total_chars": 500,
                        "retrieval": {"top_k": 1, "max_top_k": 1},
                        "compiler": {"operation_workpad": True},
                    }
                ],
            },
            "compiler": {
                "prompt_mode": "external_naive",
                "max_evidence_items": 4,
                "max_evidence_chars": 4000,
                "operation_workpad": False,
            },
            "answer": {"fallback_answer": "unknown"},
        }
        short_request = PredictionRequest(
            question="What did Alex read?",
            turns=(
                Turn("s:t0", "s", 0, "user", "Alex read Dune."),
                Turn("s:t1", "s", 1, "assistant", "It was excellent."),
            ),
        )
        long_request = PredictionRequest(
            question="What did Alex read?",
            turns=(
                Turn("s:t0", "s", 0, "user", " ".join(["Alex read Dune."] * 40)),
                Turn("s:t1", "s", 1, "assistant", "It was excellent."),
            ),
        )

        short_result = Stage1Pipeline(config).predict(short_request)
        long_result = Stage1Pipeline(config).predict(long_request)

        self.assertIsNone(short_result["trace"]["retrieval"]["granularity_profile"])
        audit = long_result["trace"]["retrieval"]["granularity_profile_audit"]
        self.assertEqual(
            long_result["trace"]["retrieval"]["granularity_profile"]["name"],
            "long_context_pressure",
        )
        self.assertEqual(audit["selected_profile_name"], "long_context_pressure")
        self.assertGreaterEqual(audit["total_turn_chars"], 500)
        self.assertIn(
            "total_context_pressure_selected_profile",
            audit["risk_reasons"],
        )
        self.assertNotIn(
            "avg_turn_length_selected_profile",
            audit["risk_reasons"],
        )
        self.assertEqual(
            long_result["trace"]["retrieval"]["compiler_profile"],
            "long_context_pressure",
        )

    def test_context_budget_filters_long_tail_hits_without_granularity_profile(self) -> None:
        config = {
            "retrieval": {
                "top_k": 4,
                "max_top_k": 4,
                "neighbor_window": 0,
                "context_budget": {
                    "enabled": True,
                    "max_chars": 95,
                    "min_hits": 1,
                    "protect_top_n": 1,
                },
            },
            "compiler": {"max_evidence_items": 4, "max_evidence_chars": 4000},
            "answer": {"fallback_answer": "unknown"},
        }
        request = PredictionRequest(
            question="anchor beta gamma target",
            turns=(
                Turn(
                    source_id="anchor",
                    session_id="s1",
                    turn_index=0,
                    role="user",
                    text="anchor beta gamma target",
                ),
                Turn(
                    source_id="long",
                    session_id="s1",
                    turn_index=1,
                    role="user",
                    text="target " + "noise " * 80,
                ),
                Turn(
                    source_id="beta",
                    session_id="s1",
                    turn_index=2,
                    role="user",
                    text="beta target short evidence",
                ),
                Turn(
                    source_id="gamma",
                    session_id="s1",
                    turn_index=3,
                    role="user",
                    text="gamma target short evidence",
                ),
            ),
        )

        result = Stage1Pipeline(config).predict(request)
        retrieval = result["trace"]["retrieval"]
        hit_ids = [hit["source_id"] for hit in retrieval["hits"]]
        row_ids = [
            row["source_id"]
            for row in result["trace"]["compiled_context"]["evidence_rows"]
        ]

        self.assertIsNone(retrieval["granularity_profile"])
        self.assertTrue(retrieval["context_budget_applied"])
        self.assertEqual(retrieval["context_budget_candidate_count"], 4)
        self.assertEqual(retrieval["context_budget_returned_count"], 3)
        self.assertIn("long", retrieval["context_budget_dropped_source_ids"])
        self.assertNotIn("long", hit_ids)
        self.assertNotIn("long", row_ids)

    def test_context_budget_audit_is_trace_only(self) -> None:
        base_config = {
            "retrieval": {
                "top_k": 4,
                "max_top_k": 4,
                "neighbor_window": 0,
            },
            "compiler": {"max_evidence_items": 4, "max_evidence_chars": 4000},
            "answer": {"fallback_answer": "unknown"},
        }
        audited_config = {
            **base_config,
            "retrieval": {
                **base_config["retrieval"],
                "context_budget_audit": {
                    "enabled": True,
                    "max_chars": 95,
                    "min_hits": 1,
                    "protect_top_n": 1,
                },
            },
        }
        request = PredictionRequest(
            question="anchor beta gamma target",
            turns=(
                Turn(
                    source_id="anchor",
                    session_id="s1",
                    turn_index=0,
                    role="user",
                    text="anchor beta gamma target",
                ),
                Turn(
                    source_id="long",
                    session_id="s1",
                    turn_index=1,
                    role="user",
                    text="target " + "noise " * 80,
                ),
                Turn(
                    source_id="beta",
                    session_id="s1",
                    turn_index=2,
                    role="user",
                    text="beta target short evidence",
                ),
                Turn(
                    source_id="gamma",
                    session_id="s1",
                    turn_index=3,
                    role="user",
                    text="gamma target short evidence",
                ),
            ),
        )

        plain_result = Stage1Pipeline(base_config).predict(request)
        audited_result = Stage1Pipeline(audited_config).predict(request)
        audit = audited_result["trace"]["retrieval"]["context_budget_audit"]
        audited_retrieval = audited_result["trace"]["retrieval"]

        self.assertTrue(audit["trace_only"])
        self.assertTrue(audit["applied"])
        self.assertEqual(audit["candidate_count"], 4)
        self.assertEqual(audit["projected_returned_count"], 3)
        self.assertIn("long", audit["projected_dropped_source_ids"])
        self.assertEqual(audit["prompt_rows_missing_source_ids"], ["long"])
        self.assertFalse(audit["safe_for_current_prompt"])
        self.assertFalse(audited_retrieval["context_budget_applied"])
        self.assertIn(
            "long",
            [hit["source_id"] for hit in audited_retrieval["hits"]],
        )
        self.assertEqual(
            audited_result["trace"]["compiled_context"]["prompt"],
            plain_result["trace"]["compiled_context"]["prompt"],
        )
        self.assertEqual(audited_result["answer"], plain_result["answer"])

    def test_selected_context_respects_context_budget_headroom(self) -> None:
        config = {
            "retrieval": {
                "top_k": 1,
                "max_top_k": 1,
                "neighbor_window": 0,
                "context_budget": {
                    "enabled": True,
                    "max_chars": 30,
                    "min_hits": 1,
                    "protect_top_n": 1,
                },
                "selected_context": {
                    "enabled": True,
                    "window_before": 1,
                    "window_after": 1,
                    "max_rows": 2,
                    "max_neighbor_chars": 120,
                    "max_center_chars": 120,
                    "require_anaphora": True,
                    "min_context_budget_headroom_chars": 20,
                    "information_needs": ["fact_lookup"],
                },
            },
            "compiler": {"max_evidence_items": 1, "max_evidence_chars": 4000},
            "answer": {"fallback_answer": "unknown"},
        }
        request = PredictionRequest(
            question="target alpha beta",
            turns=(
                Turn(
                    source_id="before",
                    session_id="s1",
                    turn_index=0,
                    role="user",
                    text="before row with useful context",
                ),
                Turn(
                    source_id="anchor",
                    session_id="s1",
                    turn_index=1,
                    role="user",
                    text="that target alpha beta",
                ),
                Turn(
                    source_id="after",
                    session_id="s1",
                    turn_index=2,
                    role="assistant",
                    text="after row with useful context",
                ),
            ),
        )

        result = Stage1Pipeline(config).predict(request)
        selected_context = result["trace"]["retrieval"]["selected_context"]
        row = result["trace"]["compiled_context"]["evidence_rows"][0]

        self.assertTrue(selected_context["budget_gate_applied"])
        self.assertFalse(selected_context["budget_gate_allowed"])
        self.assertEqual(
            selected_context["budget_gate_reason"], "insufficient_headroom"
        )
        self.assertFalse(selected_context["applied"])
        self.assertEqual(selected_context["materialized_count"], 0)
        self.assertEqual(row["text"], "that target alpha beta")

    def test_compiler_context_pressure_tightens_evidence_budget(self) -> None:
        config = {
            "retrieval": {
                "top_k": 3,
                "max_top_k": 3,
                "neighbor_window": 0,
                "context_budget": {
                    "enabled": True,
                    "max_chars": 30,
                    "min_hits": 1,
                    "protect_top_n": 1,
                },
            },
            "compiler": {
                "max_evidence_items": 3,
                "max_evidence_chars": 4000,
                "context_pressure": {
                    "enabled": True,
                    "max_headroom_chars": 10,
                    "compiler": {
                        "max_evidence_items": 1,
                        "max_evidence_chars": 4000,
                    },
                },
            },
            "answer": {"fallback_answer": "unknown"},
        }
        request = PredictionRequest(
            question="target",
            turns=(
                Turn(
                    source_id="a",
                    session_id="s1",
                    turn_index=0,
                    role="user",
                    text="target " + "a" * 28,
                ),
                Turn(
                    source_id="b",
                    session_id="s1",
                    turn_index=1,
                    role="user",
                    text="target beta",
                ),
                Turn(
                    source_id="c",
                    session_id="s1",
                    turn_index=2,
                    role="user",
                    text="target gamma",
                ),
            ),
        )

        result = Stage1Pipeline(config).predict(request)
        pressure = result["trace"]["compiler_context_pressure"]
        rows = result["trace"]["compiled_context"]["evidence_rows"]

        self.assertTrue(pressure["applied"])
        self.assertEqual(pressure["reason"], "low_headroom")
        self.assertEqual(len(rows), 1)

    def test_compiler_context_pressure_can_be_route_gated(self) -> None:
        config = {
            "retrieval": {
                "top_k": 3,
                "max_top_k": 3,
                "neighbor_window": 0,
                "context_budget": {
                    "enabled": True,
                    "max_chars": 60,
                    "min_hits": 1,
                    "protect_top_n": 1,
                },
            },
            "compiler": {
                "max_evidence_items": 3,
                "max_evidence_chars": 4000,
                "context_pressure": {
                    "enabled": True,
                    "max_headroom_chars": 10,
                    "information_needs": ["current_state"],
                    "compiler": {
                        "max_evidence_items": 1,
                        "max_evidence_chars": 4000,
                    },
                },
            },
            "answer": {"fallback_answer": "unknown"},
        }
        request = PredictionRequest(
            question="target",
            turns=(
                Turn(
                    source_id="a",
                    session_id="s1",
                    turn_index=0,
                    role="user",
                    text="target " + "a" * 28,
                ),
                Turn(
                    source_id="b",
                    session_id="s1",
                    turn_index=1,
                    role="user",
                    text="target beta",
                ),
                Turn(
                    source_id="c",
                    session_id="s1",
                    turn_index=2,
                    role="user",
                    text="target gamma",
                ),
            ),
        )

        result = Stage1Pipeline(config).predict(request)
        pressure = result["trace"]["compiler_context_pressure"]
        rows = result["trace"]["compiled_context"]["evidence_rows"]

        self.assertFalse(pressure["applied"])
        self.assertEqual(pressure["reason"], "route_not_enabled")
        self.assertEqual(len(rows), 3)

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

    def test_pipeline_rerank_min_effective_top_k_blocks_pool_expansion(self) -> None:
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
                    "min_effective_top_k": 2,
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

        self.assertEqual(retrieval_trace["candidate_top_k"], 1)
        self.assertFalse(retrieval_trace["rerank_applied"])
        self.assertEqual(
            retrieval_trace["rerank_skipped_reason"],
            "top_k_below_min_effective_top_k",
        )
        self.assertEqual(retrieval_trace["rerank_min_effective_top_k"], 2)
        self.assertEqual(retrieval_trace["hits"][0]["source_id"], "bad")
        self.assertEqual(rows[0]["source_id"], "bad")

    def test_rerank_filter_preserves_retrieval_order_after_selection(self) -> None:
        hits = (
            RetrievalHit("anchor", 0.9, 1, "hybrid"),
            RetrievalHit("best", 0.8, 2, "hybrid"),
            RetrievalHit("second", 0.7, 3, "hybrid"),
        )

        filtered = rerank_hits_filter_preserve_order(
            hits=hits,
            scores=(0.7, 1.0, 0.95),
            top_k=2,
            anchor_keep=1,
        )

        self.assertEqual([hit.source_id for hit in filtered], ["anchor", "best"])
        self.assertTrue(all("rerank_filter" in hit.retriever for hit in filtered))

    def test_rerank_exchange_guard_blocks_protected_tail(self) -> None:
        store = RawEvidenceStore(
            (
                Turn("anchor", "s1", 0, "user", "Coupon anchor."),
                Turn("memory", "s2", 0, "user", "Memory backed detail."),
                Turn("candidate", "s3", 0, "user", "Low risk candidate."),
            )
        )
        hits = (
            RetrievalHit("anchor", 0.9, 1, "hybrid"),
            RetrievalHit("memory", 0.8, 2, "hybrid"),
            RetrievalHit("candidate", 0.7, 3, "hybrid"),
        )

        reason, trace = _rerank_exchange_guard(
            store=store,
            question="Where was the coupon redeemed?",
            hits=hits,
            top_k=3,
            return_top_k=2,
            selection_mode="filter_preserve_order",
            anchor_keep=1,
            protected_source_ids=("memory",),
            enabled=True,
            protect_memory_sources=True,
            protect_adjacent_session=True,
            question_overlap_min_terms=1,
        )

        self.assertEqual(reason, "exchange_tail_protected_memory_source")
        self.assertEqual(trace["protected_memory_source_ids"], ("memory",))

    def test_rerank_exchange_guard_blocks_adjacent_tail(self) -> None:
        store = RawEvidenceStore(
            (
                Turn("anchor", "s1", 0, "user", "Coupon anchor."),
                Turn("tail", "s1", 1, "assistant", "Bridge detail."),
                Turn("candidate", "s2", 0, "user", "Low risk candidate."),
            )
        )
        hits = (
            RetrievalHit("anchor", 0.9, 1, "hybrid"),
            RetrievalHit("tail", 0.8, 2, "hybrid"),
            RetrievalHit("candidate", 0.7, 3, "hybrid"),
        )

        reason, trace = _rerank_exchange_guard(
            store=store,
            question="Where was the coupon redeemed?",
            hits=hits,
            top_k=3,
            return_top_k=2,
            selection_mode="filter_preserve_order",
            anchor_keep=1,
            protected_source_ids=(),
            enabled=True,
            protect_memory_sources=True,
            protect_adjacent_session=True,
            question_overlap_min_terms=0,
        )

        self.assertEqual(reason, "exchange_tail_protected_adjacent_session")
        self.assertEqual(
            trace["adjacent_session_pairs"][0]["neighbor_source_id"],
            "anchor",
        )

    def test_pipeline_rerank_filter_selects_tail_without_reordering_anchor(self) -> None:
        config = {
            "retrieval": {
                "top_k": 2,
                "max_top_k": 2,
                "neighbor_window": 0,
                "drop_query_stopwords": True,
                "rerank": {
                    "enabled": True,
                    "base_url": "http://127.0.0.1:8002/v1",
                    "model": "fake-reranker",
                    "pool_k": 3,
                    "anchor_keep": 1,
                    "anchor_after_top": 0,
                    "selection_mode": "filter_preserve_order",
                },
            },
            "compiler": {"max_evidence_items": 2, "max_evidence_chars": 4000},
            "answer": {"fallback_answer": "unknown"},
        }
        request = PredictionRequest(
            question="Where did Alex redeem the coupon?",
            turns=(
                Turn(
                    source_id="anchor",
                    session_id="s1",
                    turn_index=0,
                    role="user",
                    text="Where redeem coupon where redeem coupon.",
                ),
                Turn(
                    source_id="target",
                    session_id="s1",
                    turn_index=1,
                    role="user",
                    text="Alex redeemed the coupon at Target.",
                ),
                Turn(
                    source_id="tail",
                    session_id="s1",
                    turn_index=2,
                    role="user",
                    text="Coupon reminder.",
                ),
            ),
        )

        with patch("memory.pipeline.OpenAICompatibleRerankClient", _FakeReranker):
            result = Stage1Pipeline(config).predict(request)

        retrieval_trace = result["trace"]["retrieval"]
        rows = result["trace"]["compiled_context"]["evidence_rows"]

        self.assertEqual(retrieval_trace["candidate_top_k"], 3)
        self.assertTrue(retrieval_trace["rerank_applied"])
        self.assertEqual(retrieval_trace["rerank_selection_mode"], "filter_preserve_order")
        self.assertEqual(
            [hit["source_id"] for hit in retrieval_trace["hits"]],
            ["anchor", "target"],
        )
        self.assertEqual([row["source_id"] for row in rows], ["anchor", "target"])

    def test_pipeline_rerank_exchange_guard_allows_return_top_k_tail_exchange(
        self,
    ) -> None:
        config = {
            "retrieval": {
                "top_k": 3,
                "max_top_k": 3,
                "neighbor_window": 0,
                "drop_query_stopwords": True,
                "rerank": {
                    "enabled": True,
                    "base_url": "http://127.0.0.1:8002/v1",
                    "model": "fake-reranker",
                    "pool_k": 4,
                    "return_top_k": 2,
                    "anchor_keep": 1,
                    "anchor_after_top": 0,
                    "selection_mode": "filter_preserve_order",
                    "exchange_guard": {
                        "enabled": True,
                        "protect_memory_sources": True,
                        "protect_adjacent_session": True,
                        "protect_question_overlap_min_terms": 2,
                    },
                },
            },
            "compiler": {"max_evidence_items": 3, "max_evidence_chars": 4000},
            "answer": {"fallback_answer": "unknown"},
        }
        request = PredictionRequest(
            question="coupon",
            turns=(
                Turn(
                    source_id="anchor",
                    session_id="s1",
                    turn_index=0,
                    role="user",
                    text="coupon coupon coupon coupon",
                ),
                Turn(
                    source_id="exchangeable",
                    session_id="s2",
                    turn_index=0,
                    role="user",
                    text="coupon coupon coupon",
                ),
                Turn(
                    source_id="middle",
                    session_id="s3",
                    turn_index=0,
                    role="user",
                    text="coupon coupon",
                ),
                Turn(
                    source_id="target",
                    session_id="s4",
                    turn_index=0,
                    role="user",
                    text="coupon Target",
                ),
            ),
        )

        with patch("memory.pipeline.OpenAICompatibleRerankClient", _FakeReranker):
            result = Stage1Pipeline(config).predict(request)

        retrieval_trace = result["trace"]["retrieval"]

        self.assertEqual(retrieval_trace["candidate_top_k"], 4)
        self.assertTrue(retrieval_trace["rerank_applied"])
        self.assertEqual(retrieval_trace["rerank_return_top_k"], 2)
        self.assertEqual(retrieval_trace["rerank_exchange_guard"]["reason"], "allowed")
        self.assertEqual(
            [hit["source_id"] for hit in retrieval_trace["hits"]],
            ["anchor", "target"],
        )

    def test_rerank_neighbors_are_same_session_only(self) -> None:
        store = RawEvidenceStore(
            (
                Turn("s1:t0", "s1", 0, "user", "Before turn."),
                Turn("s1:t1", "s1", 1, "user", "Center turn."),
                Turn("s1:t2", "s1", 2, "assistant", "After turn."),
                Turn("s2:t0", "s2", 0, "user", "Other session turn."),
            )
        )

        neighbors = _neighbor_turns_for_rerank(
            store,
            store.get("s1:t1"),
            window=1,
        )

        self.assertEqual([turn.source_id for turn in neighbors], ["s1:t0", "s1:t2"])

    def test_memory_records_by_source_deduplicates_source_links(self) -> None:
        record = MemoryRecord(
            memory_id="m1",
            memory_type="fact",
            text="Alex redeemed a coupon at Target.",
            source_ids=("s1:t0", "s1:t1", "s1:t0"),
        )
        other = MemoryRecord(
            memory_id="m2",
            memory_type="profile",
            text="Alex likes grocery discounts.",
            source_ids=("s1:t1",),
        )

        by_source = _memory_records_by_source(
            (
                MemoryHit(record=record, score=1.0, rank=1),
                MemoryHit(record=other, score=0.5, rank=2),
                MemoryHit(record=record, score=0.1, rank=3),
            )
        )

        self.assertEqual(by_source["s1:t0"], (record,))
        self.assertEqual(by_source["s1:t1"], (record, other))

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

    def test_retrieval_route_overrides_can_defer_to_granularity_profile(self) -> None:
        config = {
            "retrieval": {
                "top_k": 6,
                "max_top_k": 6,
                "neighbor_window": 0,
                "route_override_precedence": "before_profile",
                "route_overrides": {
                    "profile_preference": {
                        "top_k": 4,
                        "max_top_k": 4,
                    }
                },
                "granularity_profiles": [
                    {
                        "name": "long_context_pressure",
                        "min_total_chars": 1,
                        "retrieval": {"top_k": 1, "max_top_k": 1},
                    }
                ],
            },
            "compiler": {"max_evidence_items": 10, "max_evidence_chars": 4000},
            "answer": {"fallback_answer": "I do not know."},
        }
        result = Stage1Pipeline(config).predict(
            PredictionRequest(
                question="What does Alex like?",
                turns=(
                    Turn("s1:t0", "s1", 0, "user", "Alex likes tea."),
                    Turn("s1:t1", "s1", 1, "user", "Alex likes jazz."),
                ),
            )
        )

        retrieval_trace = result["trace"]["retrieval"]
        self.assertEqual(
            result["trace"]["route"]["information_need"],
            "profile_preference",
        )
        self.assertEqual(
            retrieval_trace["route_override_precedence"],
            "before_profile",
        )
        self.assertEqual(
            retrieval_trace["granularity_profile"]["name"],
            "long_context_pressure",
        )
        self.assertEqual(
            retrieval_trace["route_override"],
            {"max_top_k": 4, "top_k": 4},
        )
        self.assertEqual(retrieval_trace["top_k"], 1)

    def test_retrieval_route_override_precedence_rejects_unknown_value(self) -> None:
        config = {
            "retrieval": {
                "top_k": 1,
                "max_top_k": 1,
                "route_override_precedence": "benchmark_first",
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

    def test_memory_lifecycle_manifest_is_trace_only_and_source_grounded(self) -> None:
        old_record = MemoryRecord(
            memory_id="old-location",
            memory_type="state",
            text="Alex lived in Austin.",
            source_ids=("s1:t0",),
            subject="Alex",
            predicate="home city",
            value="Austin",
            status="superseded",
        )
        active_record = MemoryRecord(
            memory_id="active-location",
            memory_type="state",
            text="Alex now lives in Seattle.",
            source_ids=("s2:t0",),
            subject="Alex",
            predicate="home city",
            value="Seattle",
            status="active",
        )
        manifest = _memory_lifecycle_manifest(
            question="Where does Alex currently live?",
            route=RouteResult("current_state", ("current_state",)),
            built_memory_records=(old_record, active_record),
            compiler_memory_records=(old_record, active_record),
            evidence_rows=(
                EvidenceRow(
                    source_id="s2:t0",
                    session_id="s2",
                    turn_index=0,
                    role="user",
                    text="I now live in Seattle.",
                    timestamp=None,
                    retrieval_rank=None,
                    retrieval_score=None,
                ),
            ),
        )

        self.assertTrue(manifest["trace_only"])
        self.assertEqual(manifest["built_records"]["total"], 2)
        self.assertEqual(manifest["activated_records"]["visible_source_linked"], 1)
        self.assertEqual(manifest["conflict_slot_count"], 1)
        self.assertEqual(manifest["activated_conflict_slot_count"], 1)
        self.assertEqual(manifest["slots"][0]["active_values"], ["Seattle"])
        self.assertEqual(manifest["slots"][0]["superseded_values"], ["Austin"])
        self.assertEqual(manifest["activated_slots"][0]["active_values"], ["Seattle"])
        state_updates = manifest["state_update_organization"]
        self.assertTrue(state_updates["trace_only"])
        self.assertEqual(
            state_updates["built"]["state_update_candidate_slot_count"], 1
        )
        self.assertEqual(
            state_updates["activated"]["state_update_candidate_slot_count"], 1
        )
        self.assertEqual(
            state_updates["activated"]["state_update_missing_active_source_count"],
            0,
        )
        self.assertEqual(
            state_updates["activated"][
                "state_update_missing_superseded_source_count"
            ],
            1,
        )
        self.assertTrue(
            state_updates["activated"]["items"][0]["state_update_candidate"]
        )

    def test_memory_lifecycle_manifest_separates_fact_multivalue_from_update(self) -> None:
        first_record = MemoryRecord(
            memory_id="first-book",
            memory_type="fact",
            text="Alex read Dune.",
            source_ids=("s1:t0",),
            subject="Alex",
            predicate="read",
            value="Dune",
            status="active",
        )
        second_record = MemoryRecord(
            memory_id="second-book",
            memory_type="fact",
            text="Alex read Foundation.",
            source_ids=("s2:t0",),
            subject="Alex",
            predicate="read",
            value="Foundation",
            status="active",
        )
        manifest = _memory_lifecycle_manifest(
            question="Which books did Alex read?",
            route=RouteResult("list_count", ("list",)),
            built_memory_records=(first_record, second_record),
            compiler_memory_records=(first_record, second_record),
            evidence_rows=(
                EvidenceRow(
                    source_id="s1:t0",
                    session_id="s1",
                    turn_index=0,
                    role="user",
                    text="I read Dune.",
                    timestamp=None,
                    retrieval_rank=None,
                    retrieval_score=None,
                ),
            ),
        )

        organization = manifest["state_update_organization"]["activated"]
        self.assertEqual(organization["state_update_candidate_slot_count"], 0)
        self.assertEqual(organization["non_stateful_multi_value_slot_count"], 1)
        self.assertEqual(
            organization["non_stateful_multi_value_visible_slot_count"], 1
        )
        self.assertTrue(organization["items"][0]["non_stateful_multi_value"])
        self.assertFalse(organization["items"][0]["state_update_candidate"])

    def test_memory_slot_chain_source_hits_expand_active_and_superseded_sources(self) -> None:
        old_record = MemoryRecord(
            memory_id="old",
            memory_type="state",
            text="Alex lives in Austin.",
            source_ids=("s1:t0",),
            subject="Alex",
            predicate="lives_in",
            value="Austin",
            timestamp="2024-01-01",
            status="superseded",
            superseded_by="new",
        )
        new_record = MemoryRecord(
            memory_id="new",
            memory_type="state",
            text="Alex lives in Seattle.",
            source_ids=("s1:t1",),
            subject="Alex",
            predicate="lives_in",
            value="Seattle",
            timestamp="2024-05-01",
            status="active",
        )
        unrelated_record = MemoryRecord(
            memory_id="other",
            memory_type="state",
            text="Alex drives a hybrid car.",
            source_ids=("s1:t2",),
            subject="Alex",
            predicate="drives",
            value="hybrid car",
        )

        hits, trace = _memory_slot_chain_source_hits(
            memory_hits=(MemoryHit(record=old_record, score=2.0, rank=1),),
            built_memory_records=(old_record, new_record, unrelated_record),
            route=RouteResult("current_state", ("current_state",)),
            available_source_ids={"s1:t0", "s1:t1", "s1:t2"},
            max_chains=2,
            max_sources_per_chain=4,
            memory_types=("state",),
        )

        self.assertTrue(trace["applied"])
        self.assertEqual([hit.source_id for hit in hits], ["s1:t1", "s1:t0"])
        self.assertEqual(
            {hit.retriever for hit in hits},
            {"build_memory_slot_chain"},
        )
        self.assertEqual(trace["chains"][0]["matched_memory_id"], "old")
        self.assertEqual(trace["chains"][0]["source_ids"], ("s1:t1", "s1:t0"))
        self.assertNotIn("s1:t2", trace["chains"][0]["source_ids"])

    def test_memory_slot_chain_query_scope_current_adds_active_source_only(self) -> None:
        old_record = MemoryRecord(
            memory_id="old",
            memory_type="state",
            text="Alex lives in Austin.",
            source_ids=("s1:t0",),
            subject="Alex",
            predicate="lives_in",
            value="Austin",
            timestamp="2024-01-01",
            status="superseded",
            superseded_by="new",
        )
        new_record = MemoryRecord(
            memory_id="new",
            memory_type="state",
            text="Alex lives in Seattle.",
            source_ids=("s1:t1",),
            subject="Alex",
            predicate="lives_in",
            value="Seattle",
            timestamp="2024-05-01",
            status="active",
        )

        hits, trace = _memory_slot_chain_source_hits(
            memory_hits=(MemoryHit(record=old_record, score=2.0, rank=1),),
            built_memory_records=(old_record, new_record),
            route=RouteResult("current_state", ("current_state",)),
            question="Where does Alex live now?",
            available_source_ids={"s1:t0", "s1:t1"},
            max_chains=2,
            max_sources_per_chain=4,
            memory_types=("state",),
            question_scope_gate=True,
            source_policy="query_scope",
        )

        self.assertTrue(trace["applied"])
        self.assertEqual(trace["question_scope"], "current")
        self.assertEqual([hit.source_id for hit in hits], ["s1:t1"])
        self.assertEqual(trace["chains"][0]["source_ids"], ("s1:t1",))

    def test_memory_slot_chain_query_scope_gate_skips_unspecified_question(self) -> None:
        old_record = MemoryRecord(
            memory_id="old",
            memory_type="preference",
            text="Alex prefers chocolate cake.",
            source_ids=("s1:t0",),
            subject="Alex",
            predicate="prefers",
            value="chocolate cake",
            timestamp="2024-01-01",
            status="superseded",
            superseded_by="new",
        )
        new_record = MemoryRecord(
            memory_id="new",
            memory_type="preference",
            text="Alex prefers lemon tart.",
            source_ids=("s1:t1",),
            subject="Alex",
            predicate="prefers",
            value="lemon tart",
            timestamp="2024-05-01",
            status="active",
        )

        hits, trace = _memory_slot_chain_source_hits(
            memory_hits=(MemoryHit(record=old_record, score=2.0, rank=1),),
            built_memory_records=(old_record, new_record),
            route=RouteResult("profile_preference", ("profile_or_preference",)),
            question="What dessert does Alex prefer?",
            available_source_ids={"s1:t0", "s1:t1"},
            max_chains=2,
            max_sources_per_chain=4,
            memory_types=("preference",),
            question_scope_gate=True,
            source_policy="query_scope",
        )

        self.assertFalse(trace["applied"])
        self.assertEqual(trace["question_scope"], "unspecified")
        self.assertEqual(trace["skipped_reason"], "question_scope_unspecified")
        self.assertEqual(hits, ())

    def test_memory_slot_chain_query_scope_requires_slot_overlap_beyond_subject(self) -> None:
        old_record = MemoryRecord(
            memory_id="old",
            memory_type="profile",
            text="Andrew volunteered at an animal shelter.",
            source_ids=("s1:t0",),
            subject="Andrew",
            predicate="volunteers_at",
            value="animal shelter",
            timestamp="2024-01-01",
            status="superseded",
            superseded_by="new",
        )
        new_record = MemoryRecord(
            memory_id="new",
            memory_type="profile",
            text="Andrew owns a dog named Toby.",
            source_ids=("s1:t1",),
            subject="Andrew",
            predicate="owns",
            value="dog named Toby",
            timestamp="2024-05-01",
            status="active",
        )

        hits, trace = _memory_slot_chain_source_hits(
            memory_hits=(MemoryHit(record=old_record, score=2.0, rank=1),),
            built_memory_records=(old_record, new_record),
            route=RouteResult("current_state", ("current_state",)),
            question="How does Andrew feel about his current work?",
            available_source_ids={"s1:t0", "s1:t1"},
            max_chains=2,
            max_sources_per_chain=4,
            memory_types=("profile",),
            question_scope_gate=True,
            source_policy="query_scope",
        )

        self.assertFalse(trace["applied"])
        self.assertEqual(hits, ())

    def test_memory_slot_chain_query_scope_ignores_temporal_operation_terms(self) -> None:
        old_record = MemoryRecord(
            memory_id="old",
            memory_type="state",
            text="The user was considering a 50GB monthly phone plan.",
            source_ids=("s1:t0",),
            subject="user",
            predicate="has",
            value="50GB monthly phone plan",
            timestamp="2024-01-01",
            status="superseded",
            superseded_by="new",
        )
        new_record = MemoryRecord(
            memory_id="new",
            memory_type="state",
            text="The user chose a 200GB monthly phone plan.",
            source_ids=("s1:t1",),
            subject="user",
            predicate="has",
            value="200GB monthly phone plan",
            timestamp="2024-05-01",
            status="active",
        )

        hits, trace = _memory_slot_chain_source_hits(
            memory_hits=(MemoryHit(record=old_record, score=2.0, rank=1),),
            built_memory_records=(old_record, new_record),
            route=RouteResult("current_state", ("current_state",)),
            question=(
                "What is the order of the three sports events I participated "
                "in during the past month, from earliest to latest?"
            ),
            available_source_ids={"s1:t0", "s1:t1"},
            max_chains=2,
            max_sources_per_chain=4,
            memory_types=("state",),
            question_scope_gate=True,
            source_policy="query_scope",
        )

        self.assertFalse(trace["applied"])
        self.assertEqual(hits, ())

    def test_pipeline_memory_slot_chain_can_supply_raw_rows_without_lexical_or_dense(self) -> None:
        old_record = MemoryRecord(
            memory_id="old",
            memory_type="state",
            text="Alex lives in Austin.",
            source_ids=("s1:t0",),
            subject="Alex",
            predicate="lives_in",
            value="Austin",
            timestamp="2024-01-01",
            status="superseded",
            superseded_by="new",
        )
        new_record = MemoryRecord(
            memory_id="new",
            memory_type="state",
            text="Alex lives in Seattle.",
            source_ids=("s2:t0",),
            subject="Alex",
            predicate="lives_in",
            value="Seattle",
            timestamp="2024-05-01",
            status="active",
        )

        class FakeBuilder:
            def build(self, turns: tuple[Turn, ...]) -> BuiltMemory:
                del turns
                return BuiltMemory(
                    records=(new_record, old_record),
                    token_usage=TokenUsage(),
                )

        config = {
            "build_memory": {
                "enabled": True,
                "mode": "openai_compatible",
                "model": "fake",
                "top_k": 1,
                "max_sources_per_record": 1,
                "include_superseded": True,
            },
            "retrieval": {
                "top_k": 2,
                "max_top_k": 2,
                "neighbor_window": 0,
                "lexical": {"enabled": False},
                "memory_slot_chain": {
                    "enabled": True,
                    "information_needs": ["current_state"],
                    "memory_types": ["state"],
                    "max_chains": 2,
                    "max_sources_per_chain": 4,
                },
            },
            "compiler": {
                "prompt_mode": "external_naive",
                "max_evidence_items": 2,
                "max_evidence_chars": 4000,
            },
            "answer": {"fallback_answer": "unknown"},
        }
        pipeline = Stage1Pipeline(config)
        pipeline._memory_builder = FakeBuilder()
        request = PredictionRequest(
            question="Where does Alex live now?",
            turns=(
                Turn(
                    source_id="s1:t0",
                    session_id="s1",
                    turn_index=0,
                    role="user",
                    text="I live in Austin.",
                    timestamp="2024-01-01",
                ),
                Turn(
                    source_id="s2:t0",
                    session_id="s2",
                    turn_index=0,
                    role="user",
                    text="I moved to Seattle.",
                    timestamp="2024-05-01",
                ),
            ),
        )

        result = pipeline.predict(request)
        retrieval = result["trace"]["retrieval"]
        row_ids = [
            row["source_id"]
            for row in result["trace"]["compiled_context"]["evidence_rows"]
        ]

        self.assertTrue(retrieval["memory_slot_chain_applied"])
        self.assertEqual(
            [hit["source_id"] for hit in retrieval["memory_slot_chain_source_hits"]],
            ["s2:t0", "s1:t0"],
        )
        self.assertEqual(row_ids, ["s2:t0", "s1:t0"])
        self.assertIn("I moved to Seattle.", result["trace"]["compiled_context"]["prompt"])
        self.assertIn("I live in Austin.", result["trace"]["compiled_context"]["prompt"])

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

    def test_openai_answerer_sends_chat_template_kwargs(self) -> None:
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
                            {"message": {"content": '{"answer":"jasmine tea"}'}}
                        ],
                        "usage": {"prompt_tokens": 10, "completion_tokens": 2},
                    }
                ).encode("utf-8")

        class FakeOpener:
            def open(self, request: object, timeout: float) -> FakeResponse:
                del timeout
                captured["payload"] = json.loads(request.data.decode("utf-8"))
                return FakeResponse()

        answerer = OpenAICompatibleAnswerer(
            base_url="http://unused.local/v1",
            model="fake-model",
            temperature=0.0,
            max_tokens=16,
            timeout=1.0,
            output_format="json_answer",
            chat_template_kwargs={"enable_thinking": False},
        )
        context = CompiledContext(
            question="What tea?",
            question_time=None,
            route=RouteResult("fact_lookup", (), 1),
            evidence_rows=(),
            prompt="Answer from evidence.",
            context_chars=21,
        )

        with patch("memory.answer.urllib.request.build_opener", return_value=FakeOpener()):
            answerer.answer(context)

        self.assertEqual(
            captured["payload"]["chat_template_kwargs"],
            {"enable_thinking": False},
        )

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

    def test_json_answer_output_salvages_scalar_answer_field_from_malformed_json(self) -> None:
        raw = '{"reasoning":"bad quote " here","answer": 7}'

        self.assertEqual(
            _parse_answer_content(raw, output_format="json_answer"),
            "7",
        )

    def test_json_answer_output_salvages_final_answer_marker_from_malformed_json(self) -> None:
        raw = (
            '{"reasoning":"The model kept reasoning and never closed JSON. '
            'Answer: 7\\nMore reasoning repeats here."'
        )

        self.assertEqual(
            _parse_answer_content(raw, output_format="json_answer"),
            "7",
        )

    def test_json_answer_output_salvages_i_will_output_marker(self) -> None:
        raw = (
            '{"reasoning":"After comparing the evidence I will output 5. '
            'If a stricter interpretation is used, it could differ."'
        )

        self.assertEqual(
            _parse_answer_content(raw, output_format="json_answer"),
            "5",
        )

    def test_json_answer_output_strips_wrapper_quote_from_salvaged_marker(self) -> None:
        raw = "{\"reasoning\":\"I would answer 'at least 2 completed'.\""

        self.assertEqual(
            _parse_answer_content(raw, output_format="json_answer"),
            "at least 2 completed",
        )

    def test_json_answer_output_does_not_salvage_conditional_marker(self) -> None:
        raw = (
            '{"reasoning":"The candidate is not a final answer. '
            'Answer: if the missing evidence is available then use 5."'
        )

        self.assertEqual(
            _parse_answer_content(raw, output_format="json_answer"),
            "The provided information is not enough.",
        )

    def test_json_answer_output_converts_structured_insufficient_without_answer(self) -> None:
        raw = json.dumps(
            {
                "reasoning": "No direct evidence.",
                "sufficient": False,
                "answer_type": "unknown",
                "missing": "specific date",
            }
        )

        self.assertEqual(
            _parse_answer_content(raw, output_format="json_answer"),
            "The provided information is not enough.",
        )

    def test_json_answer_output_converts_unknown_placeholder_answer(self) -> None:
        raw = json.dumps(
            {
                "reasoning": "No direct evidence.",
                "sufficient": False,
                "answer_type": "unknown",
                "missing": "specific date",
                "answer": "unknown",
            }
        )

        self.assertEqual(
            _parse_answer_content(raw, output_format="json_answer"),
            "The provided information is not enough.",
        )

    def test_json_answer_output_converts_malformed_structured_insufficient(self) -> None:
        raw = '{"reasoning":"bad quote " here","sufficient":false,"missing":"date"}'

        self.assertEqual(
            _parse_answer_content(raw, output_format="json_answer"),
            "The provided information is not enough.",
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

        order_reasons = repair_trigger_reasons(
            question="Which book did Alex finish first, Dune or Foundation?",
            route_information_need="list_count",
            draft_answer="Dune",
            raw_response=json.dumps(
                {"content": json.dumps({"sufficient": True, "answer_type": "fact"})}
            ),
            enable_uncertain_trigger=False,
            enable_short_list_trigger=True,
            enable_temporal_conflict_trigger=False,
        )

        self.assertNotIn("short_collection_answer", order_reasons)

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

    def test_answer_repair_profile_advice_abstention_trigger_is_narrow(self) -> None:
        enabled_reasons = repair_trigger_reasons(
            question="Can you suggest some useful accessories for my phone?",
            route_information_need="profile_preference",
            draft_answer="There is not enough information.",
            raw_response=json.dumps({"content": json.dumps({"answer": "unknown"})}),
            enable_uncertain_trigger=False,
            enable_short_list_trigger=False,
            enable_temporal_conflict_trigger=False,
            enable_profile_advice_abstention_trigger=True,
        )
        non_abstention_reasons = repair_trigger_reasons(
            question="Can you suggest some useful accessories for my phone?",
            route_information_need="profile_preference",
            draft_answer="A case and screen protector would fit your phone needs.",
            raw_response=json.dumps({"content": json.dumps({"answer": "case"})}),
            enable_uncertain_trigger=False,
            enable_short_list_trigger=False,
            enable_temporal_conflict_trigger=False,
            enable_profile_advice_abstention_trigger=True,
        )
        raw_payload_only_reasons = repair_trigger_reasons(
            question="Can you suggest some useful accessories for my phone?",
            route_information_need="profile_preference",
            draft_answer="A case and screen protector would fit your phone needs.",
            raw_response=json.dumps(
                {
                    "content": json.dumps(
                        {"sufficient": False, "answer": "unknown"}
                    )
                }
            ),
            enable_uncertain_trigger=False,
            enable_short_list_trigger=False,
            enable_temporal_conflict_trigger=False,
            enable_profile_advice_abstention_trigger=True,
        )
        fact_route_reasons = repair_trigger_reasons(
            question="Can you suggest some useful accessories for my phone?",
            route_information_need="fact_lookup",
            draft_answer="There is not enough information.",
            raw_response=json.dumps({"content": json.dumps({"answer": "unknown"})}),
            enable_uncertain_trigger=False,
            enable_short_list_trigger=False,
            enable_temporal_conflict_trigger=False,
            enable_profile_advice_abstention_trigger=True,
        )
        non_advice_reasons = repair_trigger_reasons(
            question="What color did I say my phone case was?",
            route_information_need="profile_preference",
            draft_answer="There is not enough information.",
            raw_response=json.dumps({"content": json.dumps({"answer": "unknown"})}),
            enable_uncertain_trigger=False,
            enable_short_list_trigger=False,
            enable_temporal_conflict_trigger=False,
            enable_profile_advice_abstention_trigger=True,
        )

        self.assertIn("profile_advice_abstention_review", enabled_reasons)
        self.assertNotIn(
            "profile_advice_abstention_review", non_abstention_reasons
        )
        self.assertNotIn(
            "profile_advice_abstention_review", raw_payload_only_reasons
        )
        self.assertNotIn("profile_advice_abstention_review", fact_route_reasons)
        self.assertNotIn("profile_advice_abstention_review", non_advice_reasons)

    def test_answer_repair_cross_route_profile_advice_trigger_is_narrow(self) -> None:
        raw_supported = json.dumps(
            {
                "content": json.dumps(
                    {
                        "evidence_report": [
                            {
                                "status": "support",
                                "slot": "bedroom style preference",
                                "value": "mid-century modern bedroom dresser",
                                "reason": "The user is looking for bedroom furniture inspiration in this style.",
                            }
                        ]
                    }
                )
            }
        )
        fact_advice_reasons = repair_trigger_reasons(
            question="I was thinking about rearranging my bedroom. Any tips?",
            route_information_need="fact_lookup",
            draft_answer="There is not enough information.",
            raw_response=raw_supported,
            enable_uncertain_trigger=False,
            enable_short_list_trigger=False,
            enable_temporal_conflict_trigger=False,
            enable_cross_route_profile_advice_abstention_trigger=True,
        )
        list_advice_reasons = repair_trigger_reasons(
            question="I've got guests coming over, any cocktail suggestions?",
            route_information_need="list_count",
            draft_answer="There is not enough information.",
            raw_response=raw_supported,
            enable_uncertain_trigger=False,
            enable_short_list_trigger=False,
            enable_temporal_conflict_trigger=False,
            enable_cross_route_profile_advice_abstention_trigger=True,
        )
        unsupported_reasons = repair_trigger_reasons(
            question="I was thinking about rearranging my bedroom. Any tips?",
            route_information_need="fact_lookup",
            draft_answer="There is not enough information.",
            raw_response=json.dumps({"content": json.dumps({"evidence_report": []})}),
            enable_uncertain_trigger=False,
            enable_short_list_trigger=False,
            enable_temporal_conflict_trigger=False,
            enable_cross_route_profile_advice_abstention_trigger=True,
        )
        external_name_reasons = repair_trigger_reasons(
            question="What is a Star Wars book that Tim might enjoy?",
            route_information_need="fact_lookup",
            draft_answer="There is not enough information.",
            raw_response=raw_supported,
            enable_uncertain_trigger=False,
            enable_short_list_trigger=False,
            enable_temporal_conflict_trigger=False,
            enable_cross_route_profile_advice_abstention_trigger=True,
        )
        disabled_reasons = repair_trigger_reasons(
            question="I was thinking about rearranging my bedroom. Any tips?",
            route_information_need="fact_lookup",
            draft_answer="There is not enough information.",
            raw_response=raw_supported,
            enable_uncertain_trigger=False,
            enable_short_list_trigger=False,
            enable_temporal_conflict_trigger=False,
            enable_cross_route_profile_advice_abstention_trigger=False,
        )

        self.assertIn("profile_advice_abstention_review", fact_advice_reasons)
        self.assertIn("profile_advice_abstention_review", list_advice_reasons)
        self.assertNotIn("profile_advice_abstention_review", unsupported_reasons)
        self.assertNotIn("profile_advice_abstention_review", external_name_reasons)
        self.assertNotIn("profile_advice_abstention_review", disabled_reasons)

    def test_answer_repair_modal_abstention_trigger_is_opt_in(self) -> None:
        disabled_reasons = repair_trigger_reasons(
            question="Would Alex enjoy the book club?",
            route_information_need="fact_lookup",
            draft_answer="There is not enough information.",
            raw_response=json.dumps({"content": json.dumps({"answer": "unknown"})}),
            enable_uncertain_trigger=False,
            enable_short_list_trigger=False,
            enable_temporal_conflict_trigger=False,
        )
        enabled_reasons = repair_trigger_reasons(
            question="Would Alex enjoy the book club?",
            route_information_need="fact_lookup",
            draft_answer="There is not enough information.",
            raw_response=json.dumps({"content": json.dumps({"answer": "unknown"})}),
            enable_uncertain_trigger=False,
            enable_short_list_trigger=False,
            enable_temporal_conflict_trigger=False,
            enable_modal_abstention_trigger=True,
        )
        advice_reasons = repair_trigger_reasons(
            question="What do you think Alex should try next?",
            route_information_need="profile_preference",
            draft_answer="There is not enough information.",
            raw_response=json.dumps({"content": json.dumps({"answer": "unknown"})}),
            enable_uncertain_trigger=False,
            enable_short_list_trigger=False,
            enable_temporal_conflict_trigger=False,
            enable_modal_abstention_trigger=True,
        )
        raw_payload_only_reasons = repair_trigger_reasons(
            question="Would Alex enjoy the book club?",
            route_information_need="fact_lookup",
            draft_answer="Likely yes, because Alex likes quiet reading groups.",
            raw_response=json.dumps(
                {"content": json.dumps({"sufficient": False, "answer": "unknown"})}
            ),
            enable_uncertain_trigger=False,
            enable_short_list_trigger=False,
            enable_temporal_conflict_trigger=False,
            enable_modal_abstention_trigger=True,
        )

        self.assertNotIn("modal_abstention_review", disabled_reasons)
        self.assertIn("modal_abstention_review", enabled_reasons)
        self.assertNotIn("modal_abstention_review", advice_reasons)
        self.assertNotIn("modal_abstention_review", raw_payload_only_reasons)

    def test_answer_repair_source_grounded_modal_inference_trigger_is_narrow(
        self,
    ) -> None:
        raw_supported = json.dumps(
            {
                "content": json.dumps(
                    {
                        "evidence_report": [
                            {
                                "status": "support",
                                "slot": "preference for performing",
                                "value": "Performing live fuels my soul.",
                                "reason": "Calvin explicitly says he loves the rush and connection with the crowd.",
                            },
                            {
                                "status": "support",
                                "slot": "large-stage experience",
                                "value": "A big stage was a dream come true.",
                                "reason": "This is a directly relevant positive anchor for a large venue.",
                            },
                        ]
                    }
                )
            }
        )
        supported_reasons = repair_trigger_reasons(
            question="Would Calvin enjoy performing at the Hollywood Bowl?",
            route_information_need="fact_lookup",
            draft_answer="The provided information is not enough.",
            raw_response=raw_supported,
            enable_uncertain_trigger=False,
            enable_short_list_trigger=False,
            enable_temporal_conflict_trigger=False,
            enable_source_grounded_modal_inference_trigger=True,
        )

        raw_weak = json.dumps(
            {
                "content": json.dumps(
                    {
                        "evidence_report": [
                            {
                                "status": "support",
                                "slot": "origin",
                                "value": "home country",
                                "reason": "Establishes where Caroline moved from.",
                            },
                            {
                                "status": "support",
                                "slot": "home country identity",
                                "value": "Sweden",
                                "reason": "Identifies the home country.",
                            },
                        ]
                    }
                )
            }
        )
        weak_reasons = repair_trigger_reasons(
            question="Would Caroline want to move back to her home country soon?",
            route_information_need="fact_lookup",
            draft_answer="The provided information is not enough.",
            raw_response=raw_weak,
            enable_uncertain_trigger=False,
            enable_short_list_trigger=False,
            enable_temporal_conflict_trigger=False,
            enable_source_grounded_modal_inference_trigger=True,
        )
        advice_reasons = repair_trigger_reasons(
            question="Do you think it would be a good idea to attend my reunion?",
            route_information_need="profile_preference",
            draft_answer="The provided information is not enough.",
            raw_response=raw_supported,
            enable_uncertain_trigger=False,
            enable_short_list_trigger=False,
            enable_temporal_conflict_trigger=False,
            enable_source_grounded_modal_inference_trigger=True,
        )
        external_name_reasons = repair_trigger_reasons(
            question="Which outdoor gear company likely signed John?",
            route_information_need="fact_lookup",
            draft_answer="The provided information is not enough.",
            raw_response=raw_supported,
            enable_uncertain_trigger=False,
            enable_short_list_trigger=False,
            enable_temporal_conflict_trigger=False,
            enable_source_grounded_modal_inference_trigger=True,
        )
        sensitive_reasons = repair_trigger_reasons(
            question="Would Caroline be considered religious?",
            route_information_need="fact_lookup",
            draft_answer="The provided information is not enough.",
            raw_response=raw_supported,
            enable_uncertain_trigger=False,
            enable_short_list_trigger=False,
            enable_temporal_conflict_trigger=False,
            enable_source_grounded_modal_inference_trigger=True,
        )

        self.assertIn(
            "source_grounded_modal_inference_review", supported_reasons
        )
        self.assertNotIn(
            "source_grounded_modal_inference_review", weak_reasons
        )
        self.assertNotIn(
            "source_grounded_modal_inference_review", advice_reasons
        )
        self.assertNotIn(
            "source_grounded_modal_inference_review", external_name_reasons
        )
        self.assertNotIn(
            "source_grounded_modal_inference_review", sensitive_reasons
        )

    def test_answer_repair_source_grounded_temporal_calculation_trigger_is_narrow(
        self,
    ) -> None:
        raw_started_date = json.dumps(
            {
                "content": json.dumps(
                    {
                        "evidence_report": [
                            {
                                "status": "support",
                                "slot": "cashback app start date",
                                "value": "2023/04/16",
                                "reason": "The memory says Alex started using the app on this date.",
                            }
                        ]
                    }
                )
            }
        )
        weeks_ago_reasons = repair_trigger_reasons(
            question="How many weeks ago did I start using the cashback app?",
            route_information_need="fact_lookup",
            draft_answer="The provided information is not enough.",
            raw_response=raw_started_date,
            enable_uncertain_trigger=False,
            enable_short_list_trigger=False,
            enable_temporal_conflict_trigger=False,
            enable_source_grounded_temporal_calculation_trigger=True,
        )

        raw_age_duration = json.dumps(
            {
                "content": json.dumps(
                    {
                        "evidence_report": [
                            {
                                "status": "support",
                                "slot": "current_age",
                                "value": "32",
                                "reason": "Alex is currently age 32.",
                            },
                            {
                                "status": "support",
                                "slot": "duration_in_us",
                                "value": "5 years",
                                "reason": "Alex has lived in the United States for 5 years.",
                            },
                        ]
                    }
                )
            }
        )
        age_reasons = repair_trigger_reasons(
            question="How old was I when I moved to the United States?",
            route_information_need="current_state",
            draft_answer="The provided information is not enough.",
            raw_response=raw_age_duration,
            enable_uncertain_trigger=False,
            enable_short_list_trigger=False,
            enable_temporal_conflict_trigger=False,
            enable_source_grounded_temporal_calculation_trigger=True,
        )

        raw_two_dates = json.dumps(
            {
                "content": json.dumps(
                    {
                        "evidence_report": [
                            {
                                "status": "support",
                                "slot": "started practice",
                                "event_time": "2022-07-22",
                                "value": "started chess practice",
                            },
                            {
                                "status": "support",
                                "slot": "won tournament",
                                "event_time": "2022-11-05",
                                "value": "won the tournament",
                            },
                        ]
                    }
                )
            }
        )
        duration_reasons = repair_trigger_reasons(
            question="How long did John practice chess before winning?",
            route_information_need="temporal_lookup",
            draft_answer="The provided information is not enough.",
            raw_response=raw_two_dates,
            enable_uncertain_trigger=False,
            enable_short_list_trigger=False,
            enable_temporal_conflict_trigger=False,
            enable_source_grounded_temporal_calculation_trigger=True,
        )

        multi_part_reasons = repair_trigger_reasons(
            question=(
                "What schools did John play basketball in and how many years "
                "did he play?"
            ),
            route_information_need="temporal_lookup",
            draft_answer="The provided information is not enough.",
            raw_response=raw_two_dates,
            enable_uncertain_trigger=False,
            enable_short_list_trigger=False,
            enable_temporal_conflict_trigger=False,
            enable_source_grounded_temporal_calculation_trigger=True,
        )
        choice_reasons = repair_trigger_reasons(
            question="Which project did I start first before moving?",
            route_information_need="fact_lookup",
            draft_answer="The provided information is not enough.",
            raw_response=raw_two_dates,
            enable_uncertain_trigger=False,
            enable_short_list_trigger=False,
            enable_temporal_conflict_trigger=False,
            enable_source_grounded_temporal_calculation_trigger=True,
        )
        unsupported_reasons = repair_trigger_reasons(
            question="How long did Alex practice chess before winning?",
            route_information_need="temporal_lookup",
            draft_answer="The provided information is not enough.",
            raw_response=json.dumps({"content": json.dumps({"evidence_report": []})}),
            enable_uncertain_trigger=False,
            enable_short_list_trigger=False,
            enable_temporal_conflict_trigger=False,
            enable_source_grounded_temporal_calculation_trigger=True,
        )

        self.assertIn(
            "source_grounded_temporal_calculation_review", weeks_ago_reasons
        )
        self.assertIn("source_grounded_temporal_calculation_review", age_reasons)
        self.assertIn(
            "source_grounded_temporal_calculation_review", duration_reasons
        )
        self.assertNotIn(
            "source_grounded_temporal_calculation_review", multi_part_reasons
        )
        self.assertNotIn(
            "source_grounded_temporal_calculation_review", choice_reasons
        )
        self.assertNotIn(
            "source_grounded_temporal_calculation_review", unsupported_reasons
        )

    def test_answer_repair_source_grounded_temporal_order_trigger_is_narrow(
        self,
    ) -> None:
        raw_order = json.dumps(
            {
                "content": json.dumps(
                    {
                        "sufficient": True,
                        "answer_type": "order",
                        "evidence_report": [
                            {
                                "status": "support",
                                "slot": "visit_date",
                                "event_time": "2024-01-10",
                                "value": "visited the archive",
                            },
                            {
                                "status": "support",
                                "slot": "visit_date",
                                "event_time": "2024-02-15",
                                "value": "visited the studio",
                            },
                            {
                                "status": "support",
                                "slot": "visit_date",
                                "event_time": "2024-03-20",
                                "value": "visited the lab",
                            },
                        ],
                    }
                )
            }
        )
        supported_reasons = repair_trigger_reasons(
            question="What is the order of the places I visited from earliest to latest?",
            route_information_need="current_state",
            draft_answer="1. the studio, 2. the archive, 3. the lab",
            raw_response=raw_order,
            enable_uncertain_trigger=False,
            enable_short_list_trigger=False,
            enable_temporal_conflict_trigger=False,
            enable_source_grounded_temporal_order_trigger=True,
        )
        disabled_reasons = repair_trigger_reasons(
            question="What is the order of the places I visited from earliest to latest?",
            route_information_need="current_state",
            draft_answer="1. the studio, 2. the archive, 3. the lab",
            raw_response=raw_order,
            enable_uncertain_trigger=False,
            enable_short_list_trigger=False,
            enable_temporal_conflict_trigger=False,
            enable_source_grounded_temporal_order_trigger=False,
        )
        choice_reasons = repair_trigger_reasons(
            question="Which place did I visit first before the lab?",
            route_information_need="current_state",
            draft_answer="the studio",
            raw_response=raw_order,
            enable_uncertain_trigger=False,
            enable_short_list_trigger=False,
            enable_temporal_conflict_trigger=False,
            enable_source_grounded_temporal_order_trigger=True,
        )
        weak_support_reasons = repair_trigger_reasons(
            question="What is the order of the places I visited from earliest to latest?",
            route_information_need="current_state",
            draft_answer="1. the archive, 2. the studio",
            raw_response=json.dumps(
                {
                    "content": json.dumps(
                        {
                            "sufficient": True,
                            "answer_type": "order",
                            "evidence_report": [
                                {
                                    "status": "support",
                                    "event_time": "2024-01-10",
                                    "value": "visited the archive",
                                },
                                {
                                    "status": "support",
                                    "event_time": "2024-02-15",
                                    "value": "visited the studio",
                                },
                            ],
                        }
                    )
                }
            ),
            enable_uncertain_trigger=False,
            enable_short_list_trigger=False,
            enable_temporal_conflict_trigger=False,
            enable_source_grounded_temporal_order_trigger=True,
        )
        fact_answer_reasons = repair_trigger_reasons(
            question="What is the order of the places I visited from earliest to latest?",
            route_information_need="current_state",
            draft_answer="the archive",
            raw_response=json.dumps(
                {"content": json.dumps({"answer_type": "fact"})}
            ),
            enable_uncertain_trigger=False,
            enable_short_list_trigger=False,
            enable_temporal_conflict_trigger=False,
            enable_source_grounded_temporal_order_trigger=True,
        )
        refusal_reasons = repair_trigger_reasons(
            question="What is the order of the places I visited from earliest to latest?",
            route_information_need="current_state",
            draft_answer="The provided information is not enough.",
            raw_response=raw_order,
            enable_uncertain_trigger=False,
            enable_short_list_trigger=False,
            enable_temporal_conflict_trigger=False,
            enable_source_grounded_temporal_order_trigger=True,
        )

        self.assertIn(
            "source_grounded_temporal_order_review", supported_reasons
        )
        self.assertNotIn(
            "source_grounded_temporal_order_review", disabled_reasons
        )
        self.assertNotIn("source_grounded_temporal_order_review", choice_reasons)
        self.assertNotIn(
            "source_grounded_temporal_order_review", weak_support_reasons
        )
        self.assertNotIn(
            "source_grounded_temporal_order_review", fact_answer_reasons
        )
        self.assertNotIn("source_grounded_temporal_order_review", refusal_reasons)

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

    def test_answer_repair_prompt_adds_surface_profile_advice_rules(self) -> None:
        context = CompiledContext(
            question="Can you suggest a hotel for my upcoming trip?",
            question_time="2026-01-01",
            route=RouteResult(information_need="profile_preference", signals=()),
            evidence_rows=(
                EvidenceRow(
                    source_id="s1:t1",
                    session_id="s1",
                    turn_index=1,
                    role="user",
                    text="Alex likes hotels with city views and rooftop pools.",
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
            reasons=("profile_advice_abstention_review",),
            max_context_chars=1000,
            max_row_text_chars=200,
        )
        generic_prompt, _ = build_repair_prompt(
            compiled=context,
            draft=draft,
            reasons=("profile_preference_review",),
            max_context_chars=1000,
            max_row_text_chars=200,
        )

        self.assertIn("same-domain anchors", prompt)
        self.assertIn("search criteria", prompt)
        self.assertIn("do not invent live facts", prompt)
        self.assertIn("Do not write parenthetical examples", prompt)
        self.assertIn("generic subfields", prompt)
        self.assertNotIn("same-domain anchors", generic_prompt)

    def test_answer_repair_prompt_adds_cross_route_profile_advice_rules(
        self,
    ) -> None:
        context = CompiledContext(
            question="I was thinking about rearranging my bedroom. Any tips?",
            question_time="2026-01-01",
            route=RouteResult(information_need="fact_lookup", signals=()),
            evidence_rows=(
                EvidenceRow(
                    source_id="s1:t1",
                    session_id="s1",
                    turn_index=1,
                    role="user",
                    text="Alex wants a mid-century modern dresser for the bedroom.",
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
            reasons=("profile_advice_abstention_review",),
            max_context_chars=1000,
            max_row_text_chars=200,
        )

        self.assertIn("extract user-specific anchors", prompt)
        self.assertIn("same-domain anchors", prompt)
        self.assertIn("no-new-names rule", prompt)
        self.assertIn("generic subfields", prompt)
        self.assertIn("Alex wants a mid-century modern dresser", prompt)

    def test_answer_repair_prompt_adds_current_state_duration_rules(self) -> None:
        context = CompiledContext(
            question="How long has Alex been in the current role?",
            question_time="2025-06-01",
            route=RouteResult(information_need="current_state", signals=()),
            evidence_rows=(
                EvidenceRow(
                    source_id="s1:t1",
                    session_id="s1",
                    turn_index=1,
                    role="user",
                    text="Alex started the current role in January 2024.",
                    timestamp="2024-01-15",
                    retrieval_rank=1,
                    retrieval_score=1.0,
                ),
            ),
            prompt="original prompt",
            context_chars=0,
        )
        draft = AnswerResult(
            answer="The provided information is not enough.",
            model="draft",
            token_usage=TokenUsage(query_tokens=3),
            raw_response=json.dumps(
                {
                    "content": json.dumps(
                        {
                            "sufficient": False,
                            "answer_type": "unknown",
                            "missing": "duration",
                        }
                    )
                }
            ),
        )

        prompt, _ = build_repair_prompt(
            compiled=context,
            draft=draft,
            reasons=("uncertain_or_missing",),
            max_context_chars=1000,
            max_row_text_chars=200,
        )

        self.assertIn("current-state duration or tenure", prompt)
        self.assertIn("Question Time", prompt)
        self.assertIn("state relation", prompt)
        self.assertIn("Alex started the current role in January 2024.", prompt)

    def test_answer_repair_lifecycle_ledger_is_config_gated(self) -> None:
        context = CompiledContext(
            question="What is Alex's current role?",
            question_time="2025-06-01",
            route=RouteResult(information_need="current_state", signals=()),
            evidence_rows=(
                EvidenceRow(
                    source_id="s1:t1",
                    session_id="s1",
                    turn_index=1,
                    role="user",
                    text="Alex worked as a data analyst in 2023.",
                    timestamp="2023-06-01",
                    retrieval_rank=1,
                    retrieval_score=1.0,
                ),
                EvidenceRow(
                    source_id="s2:t1",
                    session_id="s2",
                    turn_index=1,
                    role="user",
                    text="Alex is now a product manager.",
                    timestamp="2024-06-01",
                    retrieval_rank=2,
                    retrieval_score=0.9,
                ),
            ),
            prompt="original prompt",
            context_chars=0,
        )
        draft = AnswerResult(
            answer="data analyst",
            model="draft",
            token_usage=TokenUsage(query_tokens=3),
            raw_response=json.dumps(
                {"content": '{"sufficient":true,"answer":"data analyst"}'}
            ),
        )

        disabled_prompt, _ = build_repair_prompt(
            compiled=context,
            draft=draft,
            reasons=("uncertain_or_missing",),
            max_context_chars=1000,
            max_row_text_chars=200,
        )
        enabled_prompt, _ = build_repair_prompt(
            compiled=context,
            draft=draft,
            reasons=("uncertain_or_missing",),
            max_context_chars=1000,
            max_row_text_chars=200,
            enable_lifecycle_ledger=True,
        )

        self.assertNotIn("Current-State Lifecycle Ledger:", disabled_prompt)
        self.assertIn("Current-State Lifecycle Ledger:", enabled_prompt)
        self.assertIn("memory=Memory 1", enabled_prompt)
        self.assertIn("source_id=s2:t1", enabled_prompt)
        self.assertIn("newest_candidate", enabled_prompt)

    def test_answer_repair_lifecycle_ledger_skips_generic_duration_slot(self) -> None:
        context = CompiledContext(
            question="How long have I been working in my current role?",
            question_time="2023-06-01",
            route=RouteResult(information_need="current_state", signals=()),
            evidence_rows=(
                EvidenceRow(
                    source_id="s1:t1",
                    session_id="s1",
                    turn_index=1,
                    role="user",
                    text="I worked my way up to Senior Marketing Specialist after 2 years and 4 months.",
                    timestamp="2023-05-27",
                    retrieval_rank=1,
                    retrieval_score=1.0,
                ),
                EvidenceRow(
                    source_id="s2:t1",
                    session_id="s2",
                    turn_index=1,
                    role="user",
                    text="I have 3 years and 9 months experience in the company.",
                    timestamp="2023-05-29",
                    retrieval_rank=2,
                    retrieval_score=0.9,
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

        prompt, _ = build_repair_prompt(
            compiled=context,
            draft=draft,
            reasons=("uncertain_or_missing",),
            max_context_chars=1000,
            max_row_text_chars=200,
            enable_lifecycle_ledger=True,
        )

        self.assertNotIn("Current-State Lifecycle Ledger:", prompt)

    def test_lifecycle_slot_trigger_is_state_slot_gated(self) -> None:
        def context_for(question: str) -> CompiledContext:
            return CompiledContext(
                question=question,
                question_time="2025-06-01",
                route=RouteResult(information_need="current_state", signals=()),
                evidence_rows=(
                    EvidenceRow(
                        source_id="s1:t1",
                        session_id="s1",
                        turn_index=1,
                        role="user",
                        text="Alex led 4 engineers when the role started.",
                        timestamp="2024-01-01",
                        retrieval_rank=1,
                        retrieval_score=1.0,
                    ),
                    EvidenceRow(
                        source_id="s2:t1",
                        session_id="s2",
                        turn_index=1,
                        role="user",
                        text="Alex now leads 5 engineers.",
                        timestamp="2025-01-01",
                        retrieval_rank=2,
                        retrieval_score=0.9,
                    ),
                ),
                prompt="original prompt",
                context_chars=0,
            )

        draft = AnswerResult(
            answer="5 engineers",
            model="draft",
            token_usage=TokenUsage(query_tokens=3),
            raw_response=json.dumps(
                {
                    "content": json.dumps(
                        {
                            "sufficient": True,
                            "answer_type": "fact",
                            "evidence_report": [
                                {"status": "support", "value": "4 engineers"},
                                {"status": "support", "value": "5 engineers"},
                            ],
                            "answer": "5 engineers",
                        }
                    )
                }
            ),
        )

        self.assertEqual(
            _lifecycle_slot_trigger_reasons(
                compiled=context_for("How many engineers do I lead now?"),
                draft=draft,
            ),
            ("current_state_lifecycle_review",),
        )

        blocked_questions = (
            "Can you suggest accessories that complement my current setup?",
            "What is the order of airlines I flew with from earliest to latest before today?",
            "What percentage of the property's price is the renovation cost of my current house?",
            "What did Mel and her kids paint in their latest project in July 2023?",
        )
        for question in blocked_questions:
            with self.subTest(question=question):
                self.assertEqual(
                    _lifecycle_slot_trigger_reasons(
                        compiled=context_for(question),
                        draft=draft,
                    ),
                    (),
                )

    def test_answer_repair_prompt_adds_modal_abstention_rules(self) -> None:
        context = CompiledContext(
            question="Would Alex enjoy the book club?",
            question_time="2026-01-01",
            route=RouteResult(information_need="fact_lookup", signals=()),
            evidence_rows=(
                EvidenceRow(
                    source_id="s1:t1",
                    session_id="s1",
                    turn_index=1,
                    role="user",
                    text="Alex says she likes quiet weekend reading groups.",
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

        for reason in (
            "modal_abstention_review",
            "source_grounded_modal_inference_review",
        ):
            with self.subTest(reason=reason):
                prompt, _ = build_repair_prompt(
                    compiled=context,
                    draft=draft,
                    reasons=(reason,),
                    max_context_chars=1000,
                    max_row_text_chars=200,
                )

                self.assertIn("modal or inference questions", prompt)
                self.assertIn("directly relevant anchors", prompt)
                self.assertIn("do not infer from stereotypes", prompt)
                self.assertIn(
                    "Alex says she likes quiet weekend reading groups.", prompt
                )

    def test_answer_repair_prompt_adds_temporal_calculation_rules(self) -> None:
        context = CompiledContext(
            question="How many weeks ago did Alex start using the cashback app?",
            question_time="2023-05-06",
            route=RouteResult(information_need="fact_lookup", signals=()),
            evidence_rows=(
                EvidenceRow(
                    source_id="s1:t1",
                    session_id="s1",
                    turn_index=1,
                    role="user",
                    text="Alex started using the cashback app on 2023/04/16.",
                    timestamp="2023-04-16",
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
            reasons=("source_grounded_temporal_calculation_review",),
            max_context_chars=1000,
            max_row_text_chars=200,
        )

        self.assertIn("temporal, age, or duration review", prompt)
        self.assertIn("do not require the final elapsed-time", prompt)
        self.assertIn("If all operands are directly supported", prompt)
        self.assertIn("Question Time minus a supported event date", prompt)
        self.assertIn("Use mention_time only to resolve", prompt)
        self.assertIn("Question Time", prompt)
        self.assertIn("missing, ambiguous, conflicting, unknown", prompt)
        self.assertIn("Alex started using the cashback app on 2023/04/16.", prompt)

    def test_answer_repair_prompt_adds_temporal_order_rules(self) -> None:
        context = CompiledContext(
            question="What is the order of the places I visited from earliest to latest?",
            question_time="2024-04-01",
            route=RouteResult(information_need="current_state", signals=()),
            evidence_rows=(
                EvidenceRow(
                    source_id="s1:t1",
                    session_id="s1",
                    turn_index=1,
                    role="user",
                    text="I visited the archive on 2024-01-10.",
                    timestamp="2024-01-10",
                    retrieval_rank=1,
                    retrieval_score=1.0,
                ),
                EvidenceRow(
                    source_id="s2:t1",
                    session_id="s2",
                    turn_index=1,
                    role="user",
                    text="I visited the studio on 2024-02-15.",
                    timestamp="2024-02-15",
                    retrieval_rank=2,
                    retrieval_score=0.9,
                ),
            ),
            prompt="original prompt",
            context_chars=0,
        )
        draft = AnswerResult(
            answer="1. studio, 2. archive",
            model="draft",
            token_usage=TokenUsage(query_tokens=3),
            raw_response=json.dumps({"content": '{"answer_type":"order"}'}),
        )

        prompt, _ = build_repair_prompt(
            compiled=context,
            draft=draft,
            reasons=("source_grounded_temporal_order_review",),
            max_context_chars=1000,
            max_row_text_chars=200,
        )

        self.assertIn("temporal order review", prompt)
        self.assertIn("Do not sort by Memory number", prompt)
        self.assertIn("source-backed event dates", prompt)
        self.assertIn("I visited the archive on 2024-01-10.", prompt)

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

    def test_source_grounded_guard_adds_only_missing_detail(self) -> None:
        content = json.dumps(
            {
                "sufficient": False,
                "missing": "No row states the start date.",
                "answer": "The provided information is not enough.",
            }
        )
        raw_response = json.dumps({"content": content})

        finalization = guard_source_grounded_answer(
            draft_answer="The provided information is not enough.",
            raw_response=raw_response,
            enable_missing_detail=True,
        )

        self.assertTrue(finalization.applied)
        self.assertEqual(finalization.reason, "source_grounded_missing_detail")
        self.assertIn("No row states the start date", finalization.answer)

    def test_source_grounded_guard_does_not_compute_count(self) -> None:
        content = json.dumps(
            {
                "sufficient": True,
                "answer_type": "count",
                "evidence_report": [
                    {
                        "status": "support",
                        "canonical_item": "first plant",
                        "count_increment": "1",
                    },
                    {
                        "status": "support",
                        "canonical_item": "second plant",
                        "count_increment": "1",
                    },
                ],
                "answer": "1",
            }
        )
        raw_response = json.dumps({"content": content})

        finalization = guard_source_grounded_answer(
            draft_answer="1",
            raw_response=raw_response,
            enable_missing_detail=True,
        )

        self.assertFalse(finalization.applied)
        self.assertEqual(finalization.reason, "source_grounded_guard_consistent")
        self.assertEqual(finalization.answer, "1")

    def test_source_grounded_guard_preserves_numeric_level_slot_when_enabled(self) -> None:
        content = json.dumps(
            {
                "sufficient": True,
                "answer_type": "count",
                "evidence_report": [
                    {
                        "status": "support",
                        "slot": "previous goal level",
                        "value": "100",
                        "reason": "The user previously wanted to reach level 100.",
                    },
                    {
                        "status": "support",
                        "slot": "updated goal level",
                        "value": "150",
                        "reason": "The user later updated the goal to level 150.",
                    },
                ],
                "answer": "100",
            }
        )
        raw_response = json.dumps({"content": content})

        finalization = guard_source_grounded_answer(
            question=(
                "What was my previous goal for my Apex Legends level before I "
                "updated my goal?"
            ),
            draft_answer="100",
            raw_response=raw_response,
            enable_numeric_slot_label_preservation=True,
        )

        self.assertTrue(finalization.applied)
        self.assertEqual(finalization.reason, "numeric_slot_label_preservation")
        self.assertEqual(finalization.answer, "level 100")

    def test_source_grounded_guard_does_not_label_count_question(self) -> None:
        content = json.dumps(
            {
                "sufficient": True,
                "answer_type": "count",
                "evidence_report": [
                    {
                        "status": "support",
                        "slot": "completed levels",
                        "value": "100",
                        "reason": "The user completed 100 levels.",
                    },
                ],
                "answer": "100",
            }
        )
        raw_response = json.dumps({"content": content})

        finalization = guard_source_grounded_answer(
            question="How many levels did I complete?",
            draft_answer="100",
            raw_response=raw_response,
            enable_numeric_slot_label_preservation=True,
        )

        self.assertFalse(finalization.applied)
        self.assertEqual(finalization.reason, "source_grounded_guard_consistent")
        self.assertEqual(finalization.answer, "100")

    def test_source_grounded_guard_preserves_specific_support_value(self) -> None:
        content = json.dumps(
            {
                "sufficient": True,
                "answer_type": "fact",
                "evidence_report": [
                    {
                        "status": "support",
                        "slot": "test",
                        "value": "military aptitude test",
                        "reason": "John took the military aptitude test more than once.",
                    },
                ],
                "answer": "aptitude test",
            }
        )
        raw_response = json.dumps({"content": content})

        finalization = guard_source_grounded_answer(
            question="What test has John taken multiple times?",
            draft_answer="aptitude test",
            raw_response=raw_response,
            enable_source_value_specificity_preservation=True,
        )

        self.assertTrue(finalization.applied)
        self.assertEqual(
            finalization.reason, "source_value_specificity_preservation"
        )
        self.assertEqual(finalization.answer, "military aptitude test")

    def test_source_grounded_guard_does_not_expand_or_question(self) -> None:
        content = json.dumps(
            {
                "sufficient": True,
                "answer_type": "fact",
                "evidence_report": [
                    {
                        "status": "support",
                        "slot": "country",
                        "value": "Japan (Tokyo)",
                    },
                ],
                "answer": "Japan",
            }
        )
        raw_response = json.dumps({"content": content})

        finalization = guard_source_grounded_answer(
            question="Which country did Calvin pick, Japan or the United States?",
            draft_answer="Japan",
            raw_response=raw_response,
            enable_source_value_specificity_preservation=True,
        )

        self.assertFalse(finalization.applied)
        self.assertEqual(finalization.answer, "Japan")

    def test_source_grounded_guard_requires_unique_specific_support_value(self) -> None:
        content = json.dumps(
            {
                "sufficient": True,
                "answer_type": "fact",
                "evidence_report": [
                    {
                        "status": "support",
                        "slot": "activity",
                        "value": "painting classes",
                    },
                    {
                        "status": "support",
                        "slot": "activity",
                        "value": "painting session",
                    },
                ],
                "answer": "painting",
            }
        )
        raw_response = json.dumps({"content": content})

        finalization = guard_source_grounded_answer(
            question="Which activity did Evan mention?",
            draft_answer="painting",
            raw_response=raw_response,
            enable_source_value_specificity_preservation=True,
        )

        self.assertFalse(finalization.applied)
        self.assertEqual(finalization.answer, "painting")

    def test_source_grounded_guard_allows_previous_occupation_specificity(self) -> None:
        content = json.dumps(
            {
                "sufficient": True,
                "answer_type": "fact",
                "evidence_report": [
                    {
                        "status": "support",
                        "slot": "previous occupation",
                        "value": "marketing specialist at a small startup",
                    },
                    {
                        "status": "support",
                        "slot": "previous occupation",
                        "value": "managing a team of interns at a startup",
                    },
                ],
                "answer": "Marketing specialist",
            }
        )
        raw_response = json.dumps({"content": content})

        finalization = guard_source_grounded_answer(
            question="What was my previous occupation?",
            draft_answer="Marketing specialist",
            raw_response=raw_response,
            enable_source_value_specificity_preservation=True,
        )

        self.assertTrue(finalization.applied)
        self.assertEqual(
            finalization.reason, "source_value_specificity_preservation"
        )
        self.assertEqual(
            finalization.answer, "marketing specialist at a small startup"
        )

    def test_source_grounded_guard_still_blocks_generic_previous_event(self) -> None:
        content = json.dumps(
            {
                "sufficient": True,
                "answer_type": "fact",
                "evidence_report": [
                    {
                        "status": "support",
                        "slot": "previous trip",
                        "value": "Hawaii beach trip",
                    }
                ],
                "answer": "Hawaii",
            }
        )
        raw_response = json.dumps({"content": content})

        finalization = guard_source_grounded_answer(
            question="What was my previous trip?",
            draft_answer="Hawaii",
            raw_response=raw_response,
            enable_source_value_specificity_preservation=True,
        )

        self.assertFalse(finalization.applied)
        self.assertEqual(finalization.answer, "Hawaii")

    def test_source_grounded_guard_preserves_profile_preference_value(self) -> None:
        content = json.dumps(
            {
                "sufficient": False,
                "answer_type": "unknown",
                "missing": "No explicit favorite is stated.",
                "evidence_report": [
                    {
                        "status": "support",
                        "slot": "food preference",
                        "value": "ginger snaps",
                    },
                    {
                        "status": "support",
                        "slot": "food preference",
                        "value": "ginger snaps",
                    },
                ],
                "answer": "The provided information is not enough.",
            }
        )
        raw_response = json.dumps({"content": content})

        finalization = guard_source_grounded_answer(
            question="What is Evan's favorite food?",
            draft_answer="The provided information is not enough.",
            raw_response=raw_response,
            enable_profile_preference_value_preservation=True,
        )

        self.assertTrue(finalization.applied)
        self.assertEqual(
            finalization.reason, "profile_preference_value_preservation"
        )
        self.assertEqual(finalization.answer, "ginger snaps")

    def test_source_grounded_guard_blocks_vague_profile_preference_value(self) -> None:
        content = json.dumps(
            {
                "sufficient": False,
                "answer_type": "unknown",
                "evidence_report": [
                    {
                        "status": "support",
                        "slot": "favorite movie",
                        "value": "It",
                    }
                ],
                "answer": "The provided information is not enough.",
            }
        )
        raw_response = json.dumps({"content": content})

        finalization = guard_source_grounded_answer(
            question="What is one of Joanna's favorite movies?",
            draft_answer="The provided information is not enough.",
            raw_response=raw_response,
            enable_profile_preference_value_preservation=True,
        )

        self.assertFalse(finalization.applied)

    def test_source_grounded_guard_blocks_advice_preference_value(self) -> None:
        content = json.dumps(
            {
                "sufficient": False,
                "answer_type": "unknown",
                "evidence_report": [
                    {
                        "status": "support",
                        "slot": "topic preference",
                        "value": "politics",
                    }
                ],
                "answer": "The provided information is not enough.",
            }
        )
        raw_response = json.dumps({"content": content})

        finalization = guard_source_grounded_answer(
            question="Can you recommend a show or movie for me to watch tonight?",
            draft_answer="The provided information is not enough.",
            raw_response=raw_response,
            enable_profile_preference_value_preservation=True,
        )

        self.assertFalse(finalization.applied)

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

    def test_cached_answerer_repairs_malformed_json_answer_residue(self) -> None:
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

        self.assertEqual(first.answer, "jasmine tea")
        self.assertEqual(second.answer, "jasmine tea")
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

    def test_profile_activation_guide_uses_visible_source_backlinks(self) -> None:
        turns = (
            Turn(
                source_id="s1:t0",
                session_id="s1",
                turn_index=0,
                role="user",
                text="I prefer hotels with water views and quiet rooftop lounges.",
                timestamp="2024-01-01",
            ),
        )
        compiler = EvidenceCompiler(
            max_evidence_items=1,
            max_evidence_chars=4000,
            max_memory_records=2,
            memory_order="question_overlap",
            prompt_mode="external_naive",
            profile_activation_guide=True,
            profile_activation_guide_max_records=2,
            evidence_report_contract=True,
            evidence_report_information_needs=("profile_preference",),
        )

        context = compiler.compile(
            question="Can you suggest a hotel style for my Miami trip?",
            question_time=None,
            route=RouteResult(information_need="profile_preference", signals=()),
            hits=(RetrievalHit("s1:t0", 1.0, 1, "lexical_bm25"),),
            evidence_turns=turns,
            memory_records=(
                MemoryRecord(
                    memory_id="hotel-view",
                    memory_type="preference",
                    text="User prefers hotels with water views and quiet rooftops.",
                    source_ids=("s1:t0",),
                    subject="User",
                    predicate="hotel preference",
                    value="water views and quiet rooftop lounges",
                    status="active",
                ),
                MemoryRecord(
                    memory_id="invisible",
                    memory_type="preference",
                    text="User prefers unrelated desert resorts.",
                    source_ids=("s2:t0",),
                    subject="User",
                    predicate="hotel preference",
                    value="desert resorts",
                    status="active",
                ),
            ),
        )

        self.assertIn("Profile Memory Activation Guide:", context.prompt)
        self.assertIn("sources=Memory 1", context.prompt)
        self.assertIn("water views", context.prompt)
        self.assertNotIn("desert resorts", context.prompt)
        self.assertIn("not independent evidence", context.prompt)
        self.assertNotIn("sample id", context.prompt.lower())
        self.assertNotIn("judge output", context.prompt.lower())

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
                "memory_state_guide": True,
                "memory_state_guide_information_needs": ["current_state"],
                "memory_state_guide_record_source": "evidence_rows",
                "memory_state_guide_candidate_records": 12,
                "memory_state_guide_require_conflict": True,
                "memory_state_guide_require_active_superseded_pair": True,
                "memory_state_guide_require_slot_overlap": True,
                "memory_state_guide_require_stateful_slot": True,
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
        self.assertTrue(result["trace"]["compiler"]["memory_state_guide"])
        self.assertTrue(
            result["trace"]["compiler"]["memory_state_guide_require_conflict"]
        )
        self.assertTrue(
            result["trace"]["compiler"][
                "memory_state_guide_require_active_superseded_pair"
            ]
        )
        self.assertTrue(
            result["trace"]["compiler"]["memory_state_guide_require_slot_overlap"]
        )
        self.assertTrue(
            result["trace"]["compiler"]["memory_state_guide_require_stateful_slot"]
        )
        self.assertEqual(
            result["trace"]["compiler"]["memory_state_guide_record_source"],
            "evidence_rows",
        )
        self.assertEqual(
            result["trace"]["retrieval"]["compiler_memory_state_guide_record_source"],
            "evidence_rows",
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

    def test_event_timeline_marks_vague_recent_as_low_precision(self) -> None:
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
            Turn(
                source_id="s2:t0",
                session_id="s2",
                turn_index=0,
                role="user",
                text="I saw the exhibit at the Metropolitan Museum on February 10th.",
                timestamp="2023-02-10",
            ),
        )
        baseline = EvidenceCompiler(
            max_evidence_items=3,
            max_evidence_chars=5000,
            prompt_mode="external_naive",
            event_timeline=False,
        ).compile(
            question="What is the order of the museums I visited from earliest to latest?",
            question_time=None,
            route=RouteResult(information_need="current_state", signals=()),
            hits=(),
            evidence_turns=turns,
        )
        compiled = EvidenceCompiler(
            max_evidence_items=3,
            max_evidence_chars=5000,
            prompt_mode="external_naive",
            event_timeline=True,
            event_timeline_information_needs=("current_state",),
            event_timeline_max_rows=5,
            event_timeline_snippet_chars=120,
        ).compile(
            question="What is the order of the museums I visited from earliest to latest?",
            question_time=None,
            route=RouteResult(information_need="current_state", signals=()),
            hits=(),
            evidence_turns=turns,
        )
        choice_question = EvidenceCompiler(
            max_evidence_items=3,
            max_evidence_chars=5000,
            prompt_mode="external_naive",
            event_timeline=True,
            event_timeline_information_needs=("current_state",),
        ).compile(
            question="Which museum did I visit first before moving?",
            question_time=None,
            route=RouteResult(information_need="current_state", signals=()),
            hits=(),
            evidence_turns=turns,
        )

        self.assertNotIn("Source Event Timeline:", baseline.prompt)
        self.assertIn("Source Event Timeline:", compiled.prompt)
        self.assertIn("time_kind=exact_today", compiled.prompt)
        self.assertIn("time_kind=vague_relative_recent", compiled.prompt)
        self.assertIn("not a strict before/after fact", compiled.prompt)
        self.assertLess(
            compiled.prompt.index("Memory 1(2023-01-15, exact_today)"),
            compiled.prompt.index(
                "Memory 2(near_or_before 2023-01-15, vague_relative_recent)"
            ),
        )
        self.assertNotIn("Source Event Timeline:", choice_question.prompt)

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

    def test_memory_source_interleave_preserves_memory_source_retrieval_order(self) -> None:
        compiler = EvidenceCompiler(
            max_evidence_items=4,
            max_evidence_chars=4000,
            evidence_order="memory_source_interleave",
            source_anchor_keep=1,
            source_anchor_memory_rows=2,
            source_anchor_per_session=0,
            max_memory_records=0,
        )
        route = RouteResult(information_need="profile_preference", signals=())
        low_score_memory = MemoryRecord(
            memory_id="m1",
            memory_type="fact",
            text="The user mentioned turbinado sugar.",
            source_ids=("s2:t0",),
            value="turbinado sugar",
        )
        high_score_memory = MemoryRecord(
            memory_id="m2",
            memory_type="preference",
            text="The user prefers almond flour and maple syrup.",
            source_ids=("s3:t0",),
            value="almond flour maple syrup",
        )

        compiled = compiler.compile(
            question="What would improve my cookies?",
            question_time=None,
            route=route,
            hits=(
                RetrievalHit("s1:t0", 1.0, 1, "dense_embedding"),
                RetrievalHit("s2:t0", 0.8, 2, "build_memory_bm25"),
                RetrievalHit("s1:t1", 0.7, 3, "dense_embedding"),
                RetrievalHit("s3:t0", 0.6, 4, "build_memory_bm25"),
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
                    source_id="s2:t0",
                    session_id="s2",
                    turn_index=0,
                    role="user",
                    text="I found turbinado sugar adds a richer flavor.",
                ),
                Turn(
                    source_id="s1:t1",
                    session_id="s1",
                    turn_index=1,
                    role="user",
                    text="Almond flour worked well in a dessert.",
                ),
                Turn(
                    source_id="s3:t0",
                    session_id="s3",
                    turn_index=0,
                    role="user",
                    text="Maple syrup made my cookies more balanced.",
                ),
            ),
            memory_records=(high_score_memory, low_score_memory),
        )

        self.assertEqual(
            [row.source_id for row in compiled.evidence_rows],
            ["s1:t0", "s2:t0", "s3:t0", "s1:t1"],
        )
        self.assertEqual(compiled.memory_records, ())
        self.assertNotIn("The user prefers almond flour", compiled.prompt)

    def test_scoped_memory_version_chain_prefers_active_current_source(self) -> None:
        compiler = EvidenceCompiler(
            max_evidence_items=4,
            max_evidence_chars=4000,
            evidence_order="scoped_memory_version_chain_interleave",
            source_anchor_keep=1,
            source_anchor_memory_rows=2,
            source_anchor_per_session=0,
            max_memory_records=0,
        )
        route = RouteResult(information_need="current_state", signals=())
        old_memory = MemoryRecord(
            memory_id="m_old",
            memory_type="state",
            text="The user used to live in Shibuya.",
            source_ids=("s2:t0",),
            subject="user",
            predicate="live location",
            value="Shibuya",
            status="superseded",
        )
        active_memory = MemoryRecord(
            memory_id="m_active",
            memory_type="state",
            text="The user currently lives in Harajuku.",
            source_ids=("s3:t0",),
            subject="user",
            predicate="live location",
            value="Harajuku",
            status="active",
        )

        compiled = compiler.compile(
            question="Where do I currently live?",
            question_time=None,
            route=route,
            hits=(
                RetrievalHit("s1:t0", 1.0, 1, "dense_embedding"),
                RetrievalHit("s2:t0", 0.8, 2, "build_memory_bm25"),
                RetrievalHit("s3:t0", 0.7, 3, "build_memory_bm25"),
            ),
            evidence_turns=(
                Turn(
                    source_id="s1:t0",
                    session_id="s1",
                    turn_index=0,
                    role="user",
                    text="I asked about apartment paperwork.",
                ),
                Turn(
                    source_id="s2:t0",
                    session_id="s2",
                    turn_index=0,
                    role="user",
                    text="I used to live in Shibuya.",
                    timestamp="2024-01-10",
                ),
                Turn(
                    source_id="s3:t0",
                    session_id="s3",
                    turn_index=0,
                    role="user",
                    text="I currently live in Harajuku.",
                    timestamp="2024-05-10",
                ),
            ),
            memory_records=(old_memory, active_memory),
        )

        self.assertEqual(
            [row.source_id for row in compiled.evidence_rows],
            ["s1:t0", "s3:t0", "s2:t0"],
        )
        self.assertEqual(compiled.memory_records, ())
        self.assertNotIn("The user currently lives in Harajuku", compiled.prompt)

    def test_scoped_memory_version_chain_prefers_superseded_historical_source(self) -> None:
        compiler = EvidenceCompiler(
            max_evidence_items=4,
            max_evidence_chars=4000,
            evidence_order="scoped_memory_version_chain_interleave",
            source_anchor_keep=1,
            source_anchor_memory_rows=2,
            source_anchor_per_session=0,
            max_memory_records=0,
        )
        route = RouteResult(information_need="current_state", signals=())
        old_memory = MemoryRecord(
            memory_id="m_old",
            memory_type="state",
            text="The user previously lived in Shibuya.",
            source_ids=("s2:t0",),
            subject="user",
            predicate="live location",
            value="Shibuya",
            status="superseded",
        )
        active_memory = MemoryRecord(
            memory_id="m_active",
            memory_type="state",
            text="The user currently lives in Harajuku.",
            source_ids=("s3:t0",),
            subject="user",
            predicate="live location",
            value="Harajuku",
            status="active",
        )

        compiled = compiler.compile(
            question="Where did I previously live?",
            question_time=None,
            route=route,
            hits=(
                RetrievalHit("s1:t0", 1.0, 1, "dense_embedding"),
                RetrievalHit("s3:t0", 0.8, 2, "build_memory_bm25"),
                RetrievalHit("s2:t0", 0.7, 3, "build_memory_bm25"),
            ),
            evidence_turns=(
                Turn(
                    source_id="s1:t0",
                    session_id="s1",
                    turn_index=0,
                    role="user",
                    text="I asked about apartment paperwork.",
                ),
                Turn(
                    source_id="s3:t0",
                    session_id="s3",
                    turn_index=0,
                    role="user",
                    text="I currently live in Harajuku.",
                    timestamp="2024-05-10",
                ),
                Turn(
                    source_id="s2:t0",
                    session_id="s2",
                    turn_index=0,
                    role="user",
                    text="I previously lived in Shibuya.",
                    timestamp="2024-01-10",
                ),
            ),
            memory_records=(active_memory, old_memory),
        )

        self.assertEqual(
            [row.source_id for row in compiled.evidence_rows],
            ["s1:t0", "s2:t0", "s3:t0"],
        )
        self.assertEqual(compiled.memory_records, ())
        self.assertNotIn("The user previously lived in Shibuya", compiled.prompt)

    def test_scoped_memory_version_chain_ignores_unmatched_slot(self) -> None:
        compiler = EvidenceCompiler(
            max_evidence_items=4,
            max_evidence_chars=4000,
            evidence_order="scoped_memory_version_chain_interleave",
            source_anchor_keep=1,
            source_anchor_memory_rows=2,
            source_anchor_per_session=0,
            max_memory_records=0,
        )
        route = RouteResult(information_need="current_state", signals=())
        old_memory = MemoryRecord(
            memory_id="m_old",
            memory_type="state",
            text="The user used to live in Shibuya.",
            source_ids=("s2:t0",),
            subject="user",
            predicate="live location",
            value="Shibuya",
            status="superseded",
        )
        active_memory = MemoryRecord(
            memory_id="m_active",
            memory_type="state",
            text="The user currently lives in Harajuku.",
            source_ids=("s3:t0",),
            subject="user",
            predicate="live location",
            value="Harajuku",
            status="active",
        )

        compiled = compiler.compile(
            question="What is my current favorite dessert?",
            question_time=None,
            route=route,
            hits=(
                RetrievalHit("s1:t0", 1.0, 1, "dense_embedding"),
                RetrievalHit("s2:t0", 0.8, 2, "build_memory_bm25"),
                RetrievalHit("s3:t0", 0.7, 3, "build_memory_bm25"),
            ),
            evidence_turns=(
                Turn(
                    source_id="s1:t0",
                    session_id="s1",
                    turn_index=0,
                    role="user",
                    text="I love lemon tart.",
                ),
                Turn(
                    source_id="s2:t0",
                    session_id="s2",
                    turn_index=0,
                    role="user",
                    text="I used to live in Shibuya.",
                ),
                Turn(
                    source_id="s3:t0",
                    session_id="s3",
                    turn_index=0,
                    role="user",
                    text="I currently live in Harajuku.",
                ),
            ),
            memory_records=(old_memory, active_memory),
        )

        self.assertEqual(
            [row.source_id for row in compiled.evidence_rows],
            ["s1:t0", "s2:t0", "s3:t0"],
        )

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

    def test_temporal_text_normalization_skips_this_weekend_by_default(self) -> None:
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
                    text="Alex visited the museum this weekend.",
                    timestamp="2023-06-09",
                ),
            ),
        )

        self.assertIn(
            'phrase="the week before" normalized="2023-06-02 to 2023-06-08"',
            compiled.prompt,
        )
        self.assertNotIn('phrase="this weekend"', compiled.prompt)
        self.assertNotIn("2023-06-10 to 2023-06-11", compiled.prompt)

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
