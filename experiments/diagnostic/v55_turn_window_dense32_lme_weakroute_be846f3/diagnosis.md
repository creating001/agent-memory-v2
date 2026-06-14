# Diagnosis for v55_turn_window_dense32_lme_weakroute_be846f3

## Summary

v55 keeps v54's adjacent-turn window BM25 retrieval but restores dense `protect_top_n=32`. This ablation fails on LongMemEval-S `weak_route_87`: DeepSeek judge accuracy is `57/87 = 0.655172`, below both v42 same87 and v54 same87 (`59/87`).

Key comparison:

- vs v42: correct `57/87` vs `59/87`, gain/loss `6/8`, answer_changed `27/87`
- vs v54: correct `57/87` vs `59/87`, gain/loss `2/4`, answer_changed `21/87`
- by information_need vs v42: `current_state +1`, `list_count -1`, `profile_preference -2`, `temporal_lookup 0`
- avg_query_tokens: `6000.310`, slightly over the 6K mainline target

The result rejects the current turn-window retrieval parameterization. Restoring dense protection reduced some v54 replacement noise but did not preserve the useful `list_count` signal and worsened profile/preference. The mechanism is clean and traceable, but it is not accuracy-positive enough to justify a full run.

## Observations

- samples_processed: 87
- avg_compiled_evidence_items: 33.333333333333336
- avg_build_tokens: 80991.86206896552
- build_token_accounting: logical cold-build LLM tokens; cached build chunks count from stored usage, while cache hits only avoid repeated local API calls.
- avg_build_memory_records: 130.98850574712642
- avg_active_build_memory_records: 117.41379310344827
- build_memory_temporal_fields: False
- build_memory_cache_hits: 585
- build_memory_cache_misses: 0
- build_memory_cache_writes: 0
- avg_memory_hits: 8.620689655172415
- avg_memory_source_hits: 8.298850574712644
- build_memory_include_superseded: False
- build_memory_include_superseded_information_needs: ['temporal_lookup', 'list_count']
- avg_context_chars: 20019.379310344826
- avg_query_tokens: 6000.310344827586
- question_analysis_enabled: False
- question_analysis_model: None
- question_analysis_avg_query_tokens: 0.0
- question_analysis_route_changed_count: 0
- question_analysis_cache_hits: 0
- question_analysis_cache_misses: 0
- question_analysis_cache_writes: 0
- retrieval_route_overrides: {}
- avg_effective_top_k: 40.0
- avg_effective_dense_top_k: 40.0
- avg_effective_dense_protect_top_n: 32.0
- dense_protect_top_n: 32
- session_bm25_enabled: False
- session_bm25_top_k: None
- session_anchor_top_k: None
- session_enabled_route_signals: None
- session_bm25_applied_count: 0
- session_bm25_applied_rate: 0.0
- turn_window_bm25_enabled: True
- turn_window_top_k: 24
- turn_window_window_before: 1
- turn_window_window_after: 1
- turn_window_max_sources_per_window: 3
- turn_window_bm25_applied_count: 87
- turn_window_bm25_applied_rate: 1.0
- avg_turn_window_hits: 24.0
- avg_turn_window_source_hits: 36.11494252873563
- embedding_cache_enabled: True
- embedding_cache_hits: 43433
- embedding_cache_misses: 0
- evidence_order: retrieval
- memory_record_source: retrieval
- avg_compiled_memory_records: 0.0
- memory_order: retrieval
- memory_layout: flat
- row_text_mode: full
- max_row_text_chars: 0
- evidence_row_labels: False
- final_answer_checklist: False
- max_memory_records: 0
- route_guidance: False
- temporal_workpad: True
- temporal_text_normalization: True
- temporal_event_contract: False
- temporal_workpad_scope: route
- temporal_workpad_max_rows: 12
- temporal_workpad_max_pairs: 12
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
- route_overrides: {}
- enable_recommendation_profile_patterns: True
- enable_advice_profile_patterns: False
- temporal_priority_over_recent: False
- answer_max_input_tokens: 131072
- answer_max_output_tokens: 16384
- answer_cache_enabled: True
- answer_cache_path: outputs/cache/qwen3_answer_v55_turn_window_dense32.sqlite
- answer_cache_namespace: stage1_turn_window_dense32_v55_qwen3_30b
- answer_cache_hits: 0
- answer_cache_misses: 87
- answer_cache_writes: 87
- answer_finalizer_enabled: True
- answer_finalizer_mode: structured_evidence_mechanical
- answer_finalizer_enable_count_correction: False
- answer_finalizer_enable_evidence_report_count_correction: False
- answer_finalizer_enable_money_sum_correction: False
- answer_finalizer_enable_duration_rounding_correction: True
- answer_finalizer_applied_count: 0
- answer_finalizer_applied_rate: 0.0
- answer_repair_enabled: False
- answer_repair_mode: openai_compatible
- answer_repair_model: Qwen/Qwen3-30B-A3B-Instruct-2507
- answer_repair_max_input_tokens: 131072
- answer_repair_max_output_tokens: 16384
- answer_repair_information_needs: None
- answer_repair_enable_profile_preference_trigger: False
- answer_repair_triggered_count: 0
- answer_repair_triggered_rate: 0.0
- answer_repair_applied_count: 0
- answer_repair_applied_rate: 0.0
- answer_repair_total_query_tokens: 0
- answer_repair_avg_query_tokens_when_triggered: None
- answer_repair_cache_hits: 0
- answer_repair_cache_misses: 0
- answer_repair_cache_writes: 0
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0, max_input_tokens 131072, and max_output_tokens 16384.

## Next Steps

- Do not run v55 full.
- Delete top-level v54/v55 configs; keep only config snapshots in diagnostic directories.
- Stop the current turn-window BM25 tuning direction and move to build-side memory organization with stronger memory management.
