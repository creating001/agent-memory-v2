# Diagnosis for v36_lme_token_safe_probe_e7ca9e5

## Summary

v36 token-safe format guard passes the LongMemEval-S no-label token gate.

- samples: `20`, route-stratified by question-derived information_need
- avg query tokens: `5579.7`
- query token distribution: min `4810`, p50 `5484`, p90 `6463`, p95 `6528`, max `6622`
- avg build tokens: `81690.45`
- answer max input/output: `131072/16384`

Decision: eligible for LongMemEval-S full. This fixes the v35 LME gate failure by using top40/evidence budget while preserving answer format guard.

## Observations

- samples_processed: 20
- avg_compiled_evidence_items: 33.9
- avg_build_tokens: 81690.45
- build_token_accounting: logical cold-build LLM tokens; cached build chunks count from stored usage, while cache hits only avoid repeated local API calls.
- avg_build_memory_records: 130.95
- avg_active_build_memory_records: 117.5
- build_memory_temporal_fields: False
- build_memory_cache_hits: 137
- build_memory_cache_misses: 0
- build_memory_cache_writes: 0
- avg_memory_hits: 5.5
- avg_memory_source_hits: 5.35
- build_memory_include_superseded: False
- build_memory_include_superseded_information_needs: ['temporal_lookup', 'list_count']
- avg_context_chars: 18790.75
- avg_query_tokens: 5579.7
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
- embedding_cache_enabled: True
- embedding_cache_hits: 10079
- embedding_cache_misses: 0
- evidence_order: retrieval
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
- route_overrides: {}
- enable_recommendation_profile_patterns: True
- temporal_priority_over_recent: False
- answer_max_input_tokens: 131072
- answer_max_output_tokens: 16384
- answer_cache_enabled: True
- answer_cache_path: outputs/cache/qwen3_answer_v36_lme_token_safe.sqlite
- answer_cache_namespace: stage1_lme_token_safe_format_guard_v36_qwen3_30b
- answer_cache_hits: 0
- answer_cache_misses: 20
- answer_cache_writes: 20
- answer_finalizer_enabled: True
- answer_finalizer_mode: structured_evidence_mechanical
- answer_finalizer_enable_count_correction: False
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

- Seed the v36 answer cache from v28 LongMemEval-S full traces, since prompt budget and compiler are v28-compatible and the cache reparse logic can apply v35 parser improvements.
- Run LongMemEval-S full prediction and DeepSeek judge.
- Record valid-only and invalid-as-wrong accuracy, token costs, cache hits, and any answer finalizer applications.
