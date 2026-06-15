# stage1_granularity_adaptive_v99_locomo_route_stratified_200_6c5bdf4

## Purpose

Diagnostic gate for v99 short-answer boundary on LoCoMo route-stratified 200.

The diagnostic set is stratified by the project route inferred from v98 prediction traces: `fact_lookup=50`, `temporal_lookup=50`, `list_count=50`, `profile_preference=46`, `current_state=4`. Selection uses question-derived route only; labels are used only for offline judge after prediction.

## Scope

- benchmark: LoCoMo
- subset: route_stratified_200
- experiment_kind: diagnostic
- limit: None
- workers: 12
- input_path: /data/home_new/wujinqi/agent-memory/outputs/diagnostic/stage1_granularity_adaptive_v99_locomo_route_stratified_200_6c5bdf4/prediction_input.jsonl
- config_path: /data/home_new/wujinqi/agent-memory/configs/stage1_granularity_adaptive_v99_cached.json
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0, max_input_tokens 131072, and max_output_tokens 16384.

## Git

- inside_work_tree: True
- commit: 6c5bdf4e212b7089e0d3413f373718a20629fd31
- dirty: False
- note: None

## Metrics

- n_samples: 200
- accuracy: None
- f1: None
- bleu: None
- avg_build_tokens: 48600.53
- build_token_accounting: logical cold-build LLM tokens; cached build chunks count from stored usage, while cache hits only avoid repeated local API calls.
- avg_query_tokens: 5583.205
- avg_compiled_evidence_items: 54.61
- retrieval_route_overrides: {'temporal_lookup': {'top_k': 40, 'max_top_k': 40, 'dense_top_k': 40, 'lexical_protect_top_n': 0, 'dense_protect_top_n': 32}}
- avg_effective_top_k: 55.0
- avg_effective_dense_top_k: 55.0
- avg_effective_dense_protect_top_n: 44.0
- build_memory_enabled: True
- build_memory_model: Qwen/Qwen3-30B-A3B-Instruct-2507
- build_memory_temporal_fields: False
- build_memory_prompt_profile: typed_compact
- build_memory_manage_facts: True
- build_memory_overlap_turns: 0
- build_memory_cache_enabled: True
- build_memory_cache_path: outputs/cache/qwen3_build_memory.sqlite
- build_memory_cache_hits: 1347
- build_memory_cache_misses: 0
- build_memory_cache_writes: 0
- build_memory_source_alignment: {}
- build_memory_source_alignment_changed_records: 0
- build_memory_source_alignment_added_sources: 0
- avg_build_memory_source_alignment_changed_records: 0.0
- avg_build_memory_source_alignment_added_sources: 0.0
- avg_build_memory_records: 112.085
- avg_active_build_memory_records: 102.195
- avg_memory_hits: 19.6
- avg_memory_source_hits: 23.79
- build_memory_include_superseded: False
- build_memory_include_superseded_information_needs: ['temporal_lookup', 'list_count']
- neighbor_order: hit_priority
- drop_query_stopwords: True
- lexical_enabled: True
- dense_enabled: True
- lexical_protect_top_n: 0
- dense_protect_top_n: 48
- dense_document_text_mode: external_naive
- dense_query_text_mode: external_naive
- embedding_cache_enabled: True
- embedding_cache_path: outputs/cache/qwen3_embedding.sqlite
- embedding_cache_hits: 6082
- embedding_cache_misses: 0
- embedding_cache_writes: 0
- turn_window_bm25_enabled: False
- turn_window_top_k: None
- turn_window_window_before: None
- turn_window_window_after: None
- turn_window_max_sources_per_window: None
- turn_window_max_chars_per_turn: None
- turn_window_enabled_route_signals: None
- turn_window_enabled_information_needs: None
- turn_window_enabled_query_patterns: None
- turn_window_bm25_applied_count: 0
- turn_window_bm25_applied_rate: 0.0
- avg_turn_window_hits: 0.0
- avg_turn_window_source_hits: 0.0
- selected_context_enabled: True
- selected_context_window_before: 1
- selected_context_window_after: 1
- selected_context_max_rows: 6
- selected_context_max_neighbor_chars: 120
- selected_context_information_needs: ['fact_lookup', 'list_count', 'profile_preference']
- selected_context_require_anaphora: True
- selected_context_applied_count: 146
- selected_context_applied_rate: 0.73
- avg_selected_context_materialized_rows: 4.38
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
- avg_context_chars: 17146.955
- compiler_prompt_mode: external_naive
- compiler_memory_record_source: retrieval
- avg_compiled_memory_records: 0.0
- answer_mode: openai_compatible
- answer_model: Qwen/Qwen3-30B-A3B-Instruct-2507
- answer_max_input_tokens: 131072
- answer_max_output_tokens: 16384
- answer_output_format: json_answer
- answer_cache_enabled: True
- answer_cache_path: outputs/cache/qwen3_answer_v99_granularity_adaptive.sqlite
- answer_cache_namespace: stage1_granularity_adaptive_v99_qwen3_30b
- answer_cache_hits: 0
- answer_cache_misses: 200
- answer_cache_writes: 200
- answer_finalizer_enabled: True
- answer_finalizer_mode: structured_evidence_mechanical
- answer_finalizer_enable_count_correction: False
- answer_finalizer_enable_evidence_report_count_correction: False
- answer_finalizer_enable_money_sum_correction: False
- answer_finalizer_enable_duration_rounding_correction: True
- answer_finalizer_enable_missing_detail: False
- answer_finalizer_enable_relative_time_calculation: True
- answer_finalizer_applied_count: 3
- answer_finalizer_applied_rate: 0.015
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
- temporal_event_contract: True
- temporal_workpad_scope: route
- temporal_workpad_max_rows: 12
- temporal_workpad_max_pairs: 12
- operation_workpad_question_gate: False
- personalized_advice_contract: False
- personalized_advice_contract_applied: 0
- short_answer_contract: True
- short_answer_contract_applied: 200
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
- update_conflict_guide: False
- update_conflict_guide_information_needs: None
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
- route_overrides: {'temporal_lookup': {'max_evidence_items': 40, 'max_evidence_chars': 18000}}
- enable_broad_list_patterns: True
- enable_recommendation_profile_patterns: True
- enable_advice_profile_patterns: False
- temporal_priority_over_recent: False

## Offline Judge / Diagnosis

- v99 DeepSeek judge on same200: `155/200 = 0.775000`
- v98 same200 from full judge: `165/200 = 0.825000`
- v96 same200 from full judge: `166/200 = 0.830000`
- delta vs v98: `-10`
- transitions vs v98: `CORRECT->CORRECT 153`, `CORRECT->WRONG 12`, `WRONG->CORRECT 2`, `WRONG->WRONG 33`
- changed-prediction transitions vs v98: `CORRECT->CORRECT 61`, `CORRECT->WRONG 12`, `WRONG->CORRECT 2`, `WRONG->WRONG 20`
- by route delta vs v98: `fact_lookup -4`, `list_count -2`, `profile_preference -4`, `temporal_lookup 0`, `current_state 0`

Conclusion: v99 short-answer boundary is negative. It over-constrains answer style and loses necessary explanation/details more often than it fixes over-broad answers. Do not run full.

## Outputs

- predictions: /data/home_new/wujinqi/agent-memory/outputs/diagnostic/stage1_granularity_adaptive_v99_locomo_route_stratified_200_6c5bdf4/predictions.jsonl
- traces: /data/home_new/wujinqi/agent-memory/outputs/diagnostic/stage1_granularity_adaptive_v99_locomo_route_stratified_200_6c5bdf4/traces.jsonl
- metrics: /data/home_new/wujinqi/agent-memory/experiments/diagnostic/stage1_granularity_adaptive_v99_locomo_route_stratified_200_6c5bdf4/metrics.json
- manifest: /data/home_new/wujinqi/agent-memory/experiments/diagnostic/stage1_granularity_adaptive_v99_locomo_route_stratified_200_6c5bdf4/manifest.json
- deepseek_judge: /data/home_new/wujinqi/agent-memory/experiments/diagnostic/stage1_granularity_adaptive_v99_locomo_route_stratified_200_6c5bdf4/deepseek_judge.json
- comparison_vs_v98_same200: /data/home_new/wujinqi/agent-memory/experiments/diagnostic/stage1_granularity_adaptive_v99_locomo_route_stratified_200_6c5bdf4/judge_comparison_vs_v98_same200.json
- badcases_vs_v98_same200: /data/home_new/wujinqi/agent-memory/experiments/diagnostic/stage1_granularity_adaptive_v99_locomo_route_stratified_200_6c5bdf4/badcases_vs_v98_same200.md

## Clean Notes

- No gold/reference/target answer, judge output, benchmark label, sample id, qid, or row index is passed into the prediction pipeline.
- Build-stage typed memory is generated only from raw dialogue and visible metadata; it is recorded separately from offline labels and judge outputs.
- Raw context remains available for fallback and diagnosis; build memory records keep source back-links when produced by the current builder.
- Accuracy is intentionally not computed by the prediction runner; any gold or judge metrics must be produced offline after prediction.
