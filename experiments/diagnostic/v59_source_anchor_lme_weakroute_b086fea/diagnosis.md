# Diagnosis for v59_source_anchor_lme_weakroute_b086fea

## Summary

The run validates pipeline shape, clean traceability, and answerer integration under the configured experiment kind.

## Observations

- samples_processed: 87
- avg_compiled_evidence_items: 31.091954022988507
- avg_build_tokens: 80991.86206896552
- build_token_accounting: logical cold-build LLM tokens; cached build chunks count from stored usage, while cache hits only avoid repeated local API calls.
- avg_build_memory_records: 130.98850574712642
- avg_active_build_memory_records: 117.41379310344827
- build_memory_temporal_fields: False
- build_memory_prompt_profile: typed_compact
- build_memory_manage_facts: True
- build_memory_overlap_turns: 0
- build_memory_cache_hits: 585
- build_memory_cache_misses: 0
- build_memory_cache_writes: 0
- build_memory_source_alignment: {'enabled': True, 'window': 1, 'max_sources_per_record': 4, 'min_score': 2.0, 'min_delta': 1.5}
- build_memory_source_alignment_changed_records: 1621
- build_memory_source_alignment_added_sources: 1975
- avg_build_memory_source_alignment_changed_records: 18.632183908045977
- avg_build_memory_source_alignment_added_sources: 22.701149425287355
- avg_memory_hits: 8.620689655172415
- avg_memory_source_hits: 9.540229885057471
- build_memory_include_superseded: False
- build_memory_include_superseded_information_needs: ['temporal_lookup', 'list_count']
- avg_context_chars: 20485.367816091955
- avg_query_tokens: 6065.919540229885
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
- turn_window_bm25_enabled: False
- turn_window_top_k: None
- turn_window_window_before: None
- turn_window_window_after: None
- turn_window_max_sources_per_window: None
- turn_window_bm25_applied_count: 0
- turn_window_bm25_applied_rate: 0.0
- avg_turn_window_hits: 0.0
- avg_turn_window_source_hits: 0.0
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
- embedding_cache_enabled: True
- embedding_cache_hits: 43433
- embedding_cache_misses: 0
- evidence_order: retrieval
- memory_record_source: evidence_rows
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
- current_state_update_contract: True
- source_anchor_keep: 8
- source_anchor_memory_rows: 10
- source_anchor_per_session: 2
- source_anchor_session_rows: 1
- route_overrides: {'current_state': {'evidence_order': 'source_anchor_coverage'}, 'list_count': {'evidence_order': 'source_anchor_coverage'}, 'profile_preference': {'evidence_order': 'source_anchor_coverage'}, 'temporal_lookup': {'evidence_order': 'source_anchor_coverage'}}
- enable_recommendation_profile_patterns: True
- enable_advice_profile_patterns: False
- temporal_priority_over_recent: False
- answer_max_input_tokens: 131072
- answer_max_output_tokens: 16384
- answer_cache_enabled: True
- answer_cache_path: outputs/cache/qwen3_answer_v59_state_contract.sqlite
- answer_cache_namespace: stage1_state_contract_v59_qwen3_30b
- answer_cache_hits: 2
- answer_cache_misses: 85
- answer_cache_writes: 85
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

- Use offline lexical, judge, and evidence-recall scripts to diagnose quality after prediction is complete.
- Compare typed build memory on/off before adding more expensive answer-time reasoning.
- Keep each new method behind explicit config toggles for ablation.

## Offline Judge Result

- DeepSeek judge accuracy: `55/87 = 0.632184`
- v42 same87 accuracy: `59/87 = 0.678161`
- gain/loss vs v42: `4/8`
- answer_changed: `31/87`
- avg_build_tokens: `80991.862`
- avg_query_tokens: `6065.920`
- query token > 6000: `42/87`
- query token > 8000: `0/87`
- judge output: `experiments/diagnostic/v59_source_anchor_lme_weakroute_b086fea/deepseek_judge.json`
- comparison output: `experiments/diagnostic/v59_source_anchor_lme_weakroute_b086fea/judge_comparison_vs_v42_same87.json`

By information need:

- `current_state`: v42 `12/22` -> v59 `13/22`，gain/loss `1/0`
- `list_count`: v42 `15/20` -> v59 `13/20`，gain/loss `1/3`
- `profile_preference`: v42 `10/15` -> v59 `7/15`，gain/loss `0/3`
- `temporal_lookup`: v42 `22/30` -> v59 `22/30`，gain/loss `2/2`

Conclusion: failed diagnostic. Do not run full. The source-alignment repair fixed a representative current-state provenance issue, but applying source-anchor ordering broadly damaged list/profile evidence coverage and exceeded the 6K average query-token target.
