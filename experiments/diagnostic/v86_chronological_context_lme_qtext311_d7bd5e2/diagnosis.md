# Diagnosis for v86_chronological_context_lme_qtext311_d7bd5e2

## Summary

The run validates pipeline shape, clean traceability, and answerer integration under the configured experiment kind.

## Observations

- samples_processed: 311
- avg_compiled_evidence_items: 33.79421221864952
- avg_build_tokens: 80023.63344051447
- build_token_accounting: logical cold-build LLM tokens; cached build chunks count from stored usage, while cache hits only avoid repeated local API calls.
- avg_build_memory_records: 129.02250803858522
- avg_active_build_memory_records: 116.36977491961414
- build_memory_temporal_fields: False
- build_memory_prompt_profile: typed_compact
- build_memory_manage_facts: True
- build_memory_overlap_turns: 0
- build_memory_cache_hits: 2068
- build_memory_cache_misses: 0
- build_memory_cache_writes: 0
- build_memory_source_alignment: {}
- build_memory_source_alignment_changed_records: 0
- build_memory_source_alignment_added_sources: 0
- avg_build_memory_source_alignment_changed_records: 0.0
- avg_build_memory_source_alignment_added_sources: 0.0
- avg_memory_hits: 8.27331189710611
- avg_memory_source_hits: 7.80064308681672
- build_memory_include_superseded: False
- build_memory_include_superseded_information_needs: ['temporal_lookup', 'list_count']
- avg_context_chars: 21394.797427652735
- avg_query_tokens: 6464.823151125402
- retrieval_route_overrides: {}
- avg_effective_top_k: 40.0
- avg_effective_dense_top_k: 40.0
- avg_effective_dense_protect_top_n: 32.0
- dense_protect_top_n: 32
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
- embedding_cache_hits: 153045
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
- operation_workpad_question_gate: False
- personalized_advice_contract: True
- personalized_advice_contract_applied: 4
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
- update_conflict_guide_applied: 37
- current_state_update_contract: False
- dialogue_inference_contract: False
- temporal_order_contract: False
- source_anchor_keep: 0
- source_anchor_memory_rows: 0
- source_anchor_per_session: 0
- source_anchor_session_rows: 0
- route_overrides: {'current_state': {'context_layout': 'chronological_session_thread'}, 'list_count': {'context_layout': 'chronological_session_thread'}, 'temporal_lookup': {'context_layout': 'chronological_session_thread'}}
- enable_recommendation_profile_patterns: True
- enable_advice_profile_patterns: False
- temporal_priority_over_recent: False
- answer_max_input_tokens: 131072
- answer_max_output_tokens: 16384
- answer_cache_enabled: True
- answer_cache_path: outputs/cache/qwen3_answer_v42_operation_workpad.sqlite
- answer_cache_namespace: stage1_chronological_context_v86_qwen3_30b
- answer_cache_hits: 0
- answer_cache_misses: 311
- answer_cache_writes: 311
- answer_finalizer_enabled: True
- answer_finalizer_mode: structured_evidence_mechanical
- answer_finalizer_enable_count_correction: False
- answer_finalizer_enable_evidence_report_count_correction: False
- answer_finalizer_enable_money_sum_correction: False
- answer_finalizer_enable_duration_rounding_correction: False
- answer_finalizer_enable_missing_detail: True
- answer_finalizer_applied_count: 17
- answer_finalizer_applied_rate: 0.05466237942122187
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

- DeepSeek accuracy: `230/311 = 0.7395498392`
- invalid: `0`
- judge total tokens: `72347`
- avg build tokens: `80023.633`
- avg query tokens: `6464.823`
- answer max input/output: `131072 / 16384`
- build cache: `2068` hits, `0` misses; build tokens are logical cold-build cost from cached usage.
- answer cache: `0` hits, `311` misses, `311` writes.

## Comparison

- vs v83 same-311: `239/311 -> 230/311`, delta `-9`; `WRONG->CORRECT 18`, `CORRECT->WRONG 27`, prediction_changed `102/311`.
- vs v80 same-311: `236/311 -> 230/311`, delta `-6`; `WRONG->CORRECT 21`, `CORRECT->WRONG 27`, prediction_changed `112/311`.

## Diagnosis Conclusion

v86 不扩 full。chronological session-thread layout 修复了一些真实问题：时间线推理、current-state 更新和部分 count/sum 题在按时间顺序阅读时更稳定。但把该布局 route-scoped 地应用到所有 `list_count`、`temporal_lookup`、`current_state` 会让模型在聚合题里过度依赖时间线，削弱原本 retrieval rank 对高相关证据的优先级，导致更多漏项或把缺失信息误当作可算。

下一步不应继续全局改 row layout。更合理的方向是保留 retrieval-rank-first context，并只为 order/duration/update 子类提供一个短的 chronological aid 或 conflict chain；list/count 仍应优先保持高相关证据覆盖，避免把完整 context 重新排序。
