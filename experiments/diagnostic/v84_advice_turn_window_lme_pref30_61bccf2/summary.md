# v84_advice_turn_window_lme_pref30_61bccf2

## Purpose

Stage-1 clean skeleton run: validate raw evidence storage, lexical retrieval, neighbor expansion, evidence compilation, answer generation, trace output, and experiment bookkeeping.

## Scope

- benchmark: LongMemEval-S
- subset: single-session-preference_30
- experiment_kind: diagnostic
- limit: None
- workers: 8
- input_path: /data/home_new/wujinqi/agent-memory/outputs/diagnostic_inputs/lme_single_session_preference_30.jsonl
- config_path: /data/home_new/wujinqi/agent-memory/configs/stage1_advice_turn_window_v84_diag.json
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0, max_input_tokens 131072, and max_output_tokens 16384.

## Git

- inside_work_tree: True
- commit: 61bccf2a72b3cde8bc6238a51d8280ebad6cf567
- dirty: False
- note: None

## Metrics

- n_samples: 30
- accuracy: None
- f1: None
- bleu: None
- avg_build_tokens: 79618.66666666667
- build_token_accounting: logical cold-build LLM tokens; cached build chunks count from stored usage, while cache hits only avoid repeated local API calls.
- avg_query_tokens: 5552.733333333334
- avg_compiled_evidence_items: 36.96666666666667
- retrieval_route_overrides: {}
- avg_effective_top_k: 40.0
- avg_effective_dense_top_k: 40.0
- avg_effective_dense_protect_top_n: 32.0
- build_memory_enabled: True
- build_memory_model: Qwen/Qwen3-30B-A3B-Instruct-2507
- build_memory_temporal_fields: False
- build_memory_prompt_profile: typed_compact
- build_memory_manage_facts: True
- build_memory_overlap_turns: 0
- build_memory_cache_enabled: True
- build_memory_cache_path: outputs/cache/qwen3_build_memory.sqlite
- build_memory_cache_hits: 199
- build_memory_cache_misses: 0
- build_memory_cache_writes: 0
- build_memory_source_alignment: {}
- build_memory_source_alignment_changed_records: 0
- build_memory_source_alignment_added_sources: 0
- avg_build_memory_source_alignment_changed_records: 0.0
- avg_build_memory_source_alignment_added_sources: 0.0
- avg_build_memory_records: 129.03333333333333
- avg_active_build_memory_records: 111.7
- avg_memory_hits: 7.066666666666666
- avg_memory_source_hits: 6.4
- build_memory_include_superseded: False
- build_memory_include_superseded_information_needs: ['temporal_lookup', 'list_count']
- neighbor_order: hit_priority
- drop_query_stopwords: True
- lexical_enabled: True
- dense_enabled: True
- lexical_protect_top_n: 0
- dense_protect_top_n: 32
- dense_document_text_mode: external_naive
- dense_query_text_mode: external_naive
- embedding_cache_enabled: True
- embedding_cache_path: outputs/cache/qwen3_embedding.sqlite
- embedding_cache_hits: 14764
- embedding_cache_misses: 0
- embedding_cache_writes: 0
- turn_window_bm25_enabled: True
- turn_window_top_k: 24
- turn_window_window_before: 1
- turn_window_window_after: 1
- turn_window_max_sources_per_window: 3
- turn_window_max_chars_per_turn: 700
- turn_window_enabled_route_signals: None
- turn_window_enabled_information_needs: None
- turn_window_enabled_query_patterns: ['\\b(recommend|recommendation|suggest|suggestion|advice|tips?|ideas?)\\b', '\\b(should\\s+i|should\\s+we|what\\s+should\\s+i|what\\s+do\\s+you\\s+think|do\\s+you\\s+think)\\b', '\\b(help\\s+me\\s+choose|best\\s+way)\\b']
- turn_window_bm25_applied_count: 22
- turn_window_bm25_applied_rate: 0.7333333333333333
- avg_turn_window_hits: 17.6
- avg_turn_window_source_hits: 29.1
- rerank_enabled: False
- rerank_model: None
- rerank_pool_k: None
- rerank_anchor_keep: None
- rerank_anchor_after_top: None
- rerank_applied_count: 0
- rerank_applied_rate: 0.0
- avg_rerank_candidate_count: None
- avg_rerank_returned_count: None
- avg_rerank_tokens_when_applied: None
- rerank_token_accounting: rerank model tokens are reported separately and are not included in build/query LLM token budgets.
- avg_embedding_tokens: 0.0
- avg_context_chars: 18309.066666666666
- compiler_prompt_mode: external_naive
- compiler_memory_record_source: retrieval
- avg_compiled_memory_records: 0.0
- answer_mode: openai_compatible
- answer_model: Qwen/Qwen3-30B-A3B-Instruct-2507
- answer_max_input_tokens: 131072
- answer_max_output_tokens: 16384
- answer_output_format: json_answer
- answer_cache_enabled: True
- answer_cache_path: outputs/cache/qwen3_answer_v42_operation_workpad.sqlite
- answer_cache_namespace: stage1_operation_workpad_v42_qwen3_30b
- answer_cache_hits: 10
- answer_cache_misses: 20
- answer_cache_writes: 20
- answer_finalizer_enabled: True
- answer_finalizer_mode: structured_evidence_mechanical
- answer_finalizer_enable_count_correction: False
- answer_finalizer_enable_evidence_report_count_correction: False
- answer_finalizer_enable_money_sum_correction: False
- answer_finalizer_enable_duration_rounding_correction: False
- answer_finalizer_enable_missing_detail: True
- answer_finalizer_applied_count: 0
- answer_finalizer_applied_rate: 0.0
- answer_repair_enabled: False
- answer_repair_mode: openai_compatible
- answer_repair_model: Qwen/Qwen3-30B-A3B-Instruct-2507
- answer_repair_max_input_tokens: 131072
- answer_repair_max_output_tokens: 16384
- answer_repair_output_format: json_answer
- answer_repair_information_needs: None
- answer_repair_enable_uncertain_trigger: True
- answer_repair_enable_short_list_trigger: True
- answer_repair_enable_temporal_conflict_trigger: True
- answer_repair_enable_profile_preference_trigger: False
- answer_repair_max_context_chars: 14000
- answer_repair_max_row_text_chars: 700
- answer_repair_cache_enabled: False
- answer_repair_cache_path: None
- answer_repair_cache_namespace: None
- answer_repair_cache_hits: 0
- answer_repair_cache_misses: 0
- answer_repair_cache_writes: 0
- answer_repair_triggered_count: 0
- answer_repair_triggered_rate: 0.0
- answer_repair_applied_count: 0
- answer_repair_applied_rate: 0.0
- answer_repair_total_query_tokens: 0
- answer_repair_avg_query_tokens_when_triggered: None
- scoped_evidence_enabled: False
- scoped_evidence_information_needs: None
- scoped_evidence_max_rows: None
- scoped_evidence_max_row_chars: None
- scoped_evidence_applied_count: 0
- scoped_evidence_applied_rate: 0.0
- scoped_evidence_total_extraction_query_tokens: 0
- scoped_evidence_avg_extraction_query_tokens_when_applied: None
- scoped_evidence_total_answer_query_tokens: 0
- scoped_evidence_avg_answer_query_tokens_when_applied: None
- scoped_evidence_avg_extraction_prompt_chars_when_applied: None
- scoped_evidence_avg_answer_prompt_chars_when_applied: None
- scoped_evidence_avg_evidence_json_chars_when_applied: None
- scoped_evidence_extraction_cache_hits: 0
- scoped_evidence_extraction_cache_misses: 0
- scoped_evidence_extraction_cache_writes: 0
- scoped_evidence_answer_cache_hits: 0
- scoped_evidence_answer_cache_misses: 0
- scoped_evidence_answer_cache_writes: 0
- answer_style: concise
- evidence_order: retrieval
- memory_order: retrieval
- memory_layout: flat
- row_text_mode: full
- max_row_text_chars: 0
- evidence_row_labels: False
- final_answer_checklist: False
- max_memory_records: 0
- route_guidance: False
- temporal_grounding: False
- temporal_hints: False
- temporal_workpad: True
- temporal_text_normalization: True
- temporal_event_contract: False
- temporal_workpad_scope: route
- temporal_workpad_max_rows: 12
- temporal_workpad_max_pairs: 12
- operation_workpad_question_gate: False
- personalized_advice_contract: True
- personalized_advice_contract_applied: 29
- structured_guide: True
- structured_guide_max_rows: 12
- structured_guide_include_rows: True
- structured_guide_include_memory: False
- structured_guide_disabled_signals: ['personalized_recommendation']
- structured_answer_contract: False
- structured_answer_contract_information_needs: None
- structured_answer_contract_max_items: 10
- evidence_report_contract: True
- evidence_report_information_needs: ['current_state', 'fact_lookup', 'list_count', 'profile_preference', 'temporal_lookup']
- evidence_report_max_items: 8
- evidence_report_detail: False
- aggregation_report_contract: False
- aggregation_report_information_needs: None
- candidate_guide: False
- candidate_guide_information_needs: None
- candidate_guide_max_rows: 6
- candidate_guide_snippet_chars: 160
- update_conflict_guide: True
- update_conflict_guide_information_needs: ['current_state', 'fact_lookup']
- update_conflict_guide_max_rows: 6
- update_conflict_guide_snippet_chars: 180
- update_conflict_guide_applied: 0
- current_state_update_contract: False
- dialogue_inference_contract: False
- temporal_order_contract: False
- source_anchor_keep: 0
- source_anchor_memory_rows: 0
- source_anchor_per_session: 0
- source_anchor_session_rows: 0
- route_overrides: {}
- enable_broad_list_patterns: False
- enable_recommendation_profile_patterns: True
- enable_advice_profile_patterns: False
- temporal_priority_over_recent: False

## Outputs

- predictions: /data/home_new/wujinqi/agent-memory/outputs/diagnostic/v84_advice_turn_window_lme_pref30_61bccf2/predictions.jsonl
- traces: /data/home_new/wujinqi/agent-memory/outputs/diagnostic/v84_advice_turn_window_lme_pref30_61bccf2/traces.jsonl
- metrics: /data/home_new/wujinqi/agent-memory/experiments/diagnostic/v84_advice_turn_window_lme_pref30_61bccf2/metrics.json
- manifest: /data/home_new/wujinqi/agent-memory/experiments/diagnostic/v84_advice_turn_window_lme_pref30_61bccf2/manifest.json

## Clean Notes

- No gold/reference/target answer, judge output, benchmark label, sample id, qid, or row index is passed into the prediction pipeline.
- Build-stage typed memory is generated only from raw dialogue and visible metadata; it is recorded separately from offline labels and judge outputs.
- Raw context remains available for fallback and diagnosis; build memory records keep source back-links when produced by the current builder.
- Accuracy is intentionally not computed by the prediction runner; any gold or judge metrics must be produced offline after prediction.

## Offline Judge

- judge_model: deepseek-v4-flash
- judge_accuracy: 0.466667
- judge_correct: 14/30
- judge_invalid: 0
- judge_workers: 8
- judge_total_tokens: 11526

## Comparison

- comparison_vs_v83_same30: `judge_comparison_vs_v83_same30.json`
- changed_badcases_vs_v83_same30: `delta_badcases_vs_v83_same30.md`

## Diagnostic Conclusion

- v84 在 v83 上为 advice/recommend/suggest/tips/should/what-do-you-think 类问题开启 adjacent-turn BM25 window，window 只作为检索文档，最终仍投影到 raw source turns。
- 30 条 preference diagnostic 中 turn_window_bm25_applied `22/30`，avg_query_tokens `5552.733`，answer cache miss `20/30`。
- 相对 v83 same30，accuracy `13/30 -> 14/30`；prediction changed subset `WRONG->CORRECT 2`、`CORRECT->WRONG 1`，净 `+1`，unchanged judge variance `0`。
- 结论：有真实信号但太弱，且 prediction_changed `17/30` 说明窗口补召回会扰动很多答案。暂不扩 full；下一步应尝试更窄的 source-anchor ordering，把 build memory 命中的 source rows 提前，而不是扩大 raw window。
