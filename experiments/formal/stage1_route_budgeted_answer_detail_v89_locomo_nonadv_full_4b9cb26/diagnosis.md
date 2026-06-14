# Diagnosis for stage1_route_budgeted_answer_detail_v89_locomo_nonadv_full_4b9cb26

## 正式结论

- benchmark/subset: `LoCoMo / non-adversarial full`
- commit: `4b9cb26f436aca58be53334d84f520139dd9d9dd`
- dirty at prediction: `False`
- DeepSeek judge accuracy: `0.752597` (`1159/1540`)
- invalid judgments: `0`
- avg_build_tokens: `58386.008`
- avg_query_tokens: `4922.037`
- build_memory_cache_hits/misses: `12411/0`
- answer_cache_hits/misses: `11/1529`
- answer_finalizer_applied_count: `55/1540`

v89 将 v35/v34 的 route-budgeted top60 retrieval budget 合入 v88，但 LoCoMo full 结果低于 v35 和 v88。相对 v35：`WRONG->CORRECT 36`、`CORRECT->WRONG 79`、`INVALID->CORRECT 1`，净 `-43`；相对 v88 净 `-5`。

结论：v89 是负向 ablation，不作为主线，也不保留顶层 config。简单增加 LoCoMo top60 context 不能和 v88 的 LME reader/prompt stack 直接相容；下一步应回到 v35 LoCoMo 底座，做更小的 finalizer-only 或 compiler-only 消融，或者针对 LoCoMo badcase 设计独立的 evidence organization，而不是继续扩大 context。

Clean 检查：prediction pipeline 不读取 gold answer、judge output、benchmark category、sample id、row index 或 test feedback。

## Summary

The run validates pipeline shape, clean traceability, and answerer integration under the configured experiment kind.

## Observations

- samples_processed: 1540
- avg_compiled_evidence_items: 55.61038961038961
- avg_build_tokens: 58386.00779220779
- build_token_accounting: logical cold-build LLM tokens; cached build chunks count from stored usage, while cache hits only avoid repeated local API calls.
- avg_build_memory_records: 136.65974025974026
- avg_active_build_memory_records: 125.11233766233767
- build_memory_temporal_fields: False
- build_memory_prompt_profile: typed_compact
- build_memory_manage_facts: True
- build_memory_overlap_turns: 0
- build_memory_cache_hits: 12411
- build_memory_cache_misses: 0
- build_memory_cache_writes: 0
- build_memory_source_alignment: {}
- build_memory_source_alignment_changed_records: 0
- build_memory_source_alignment_added_sources: 0
- avg_build_memory_source_alignment_changed_records: 0.0
- avg_build_memory_source_alignment_added_sources: 0.0
- avg_memory_hits: 19.84155844155844
- avg_memory_source_hits: 22.37922077922078
- build_memory_include_superseded: False
- build_memory_include_superseded_information_needs: ['temporal_lookup', 'list_count']
- avg_context_chars: 14613.587662337663
- avg_query_tokens: 4922.037012987013
- retrieval_route_overrides: {}
- avg_effective_top_k: 60.0
- avg_effective_dense_top_k: 60.0
- avg_effective_dense_protect_top_n: 48.0
- dense_protect_top_n: 48
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
- embedding_cache_hits: 7422
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
- personalized_advice_contract_applied: 58
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
- route_overrides: {'temporal_lookup': {'max_evidence_items': 40, 'max_evidence_chars': 18000}}
- enable_recommendation_profile_patterns: True
- enable_advice_profile_patterns: False
- temporal_priority_over_recent: False
- answer_max_input_tokens: 131072
- answer_max_output_tokens: 16384
- answer_cache_enabled: True
- answer_cache_path: outputs/cache/qwen3_answer_v42_operation_workpad.sqlite
- answer_cache_namespace: stage1_operation_workpad_v42_qwen3_30b
- answer_cache_hits: 11
- answer_cache_misses: 1529
- answer_cache_writes: 1529
- answer_finalizer_enabled: True
- answer_finalizer_mode: structured_evidence_mechanical
- answer_finalizer_enable_count_correction: False
- answer_finalizer_enable_evidence_report_count_correction: False
- answer_finalizer_enable_money_sum_correction: False
- answer_finalizer_enable_duration_rounding_correction: False
- answer_finalizer_enable_missing_detail: True
- answer_finalizer_applied_count: 55
- answer_finalizer_applied_rate: 0.03571428571428571
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
