# Diagnosis for v54_turn_window_lme_weakroute_fc48b22

## Summary

v54 adds adjacent-turn window BM25 retrieval and projects window hits back to raw source turns. On LongMemEval-S `weak_route_87`, DeepSeek judge accuracy is `59/87 = 0.678161`, equal to v42 same87. It does not pass the gate for full LongMemEval.

Key comparison vs v42 same87:

- v42 correct: `59/87`
- v54 correct: `59/87`
- gain/loss: `7/7`
- answer_changed: `25/87`
- by information_need: `list_count +1`, `profile_preference -1`, `current_state 0`, `temporal_lookup 0`

The useful signal is real but unstable. Some gains come from better local continuation and adjacent-slot activation, while several losses show v54 dropping v42 evidence rows after dense hard-protect was relaxed from 32 to 28. Because avg_query_tokens is `5959.874`, there is no budget room to accept noisy replacement without clear accuracy gain.

## Observations

- samples_processed: 87
- avg_compiled_evidence_items: 30.977011494252874
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
- avg_context_chars: 20180.954022988506
- avg_query_tokens: 5959.873563218391
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
- avg_effective_dense_protect_top_n: 28.0
- dense_protect_top_n: 28
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
- answer_cache_path: outputs/cache/qwen3_answer_v54_turn_window.sqlite
- answer_cache_namespace: stage1_turn_window_retrieval_v54_qwen3_30b
- answer_cache_hits: 87
- answer_cache_misses: 0
- answer_cache_writes: 0
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

- Do not run v54 full.
- Run v55 only as a narrow ablation: restore dense `protect_top_n=32` while keeping turn-window retrieval unchanged.
- If v55 is not above v42 same87, stop the current turn-window parameter direction and move back to build-side memory organization.
