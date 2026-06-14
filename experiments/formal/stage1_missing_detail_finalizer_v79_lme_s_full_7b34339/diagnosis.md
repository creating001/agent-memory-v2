# Diagnosis for stage1_missing_detail_finalizer_v79_lme_s_full_7b34339

## 人工诊断

v79 解决的是一个很窄的问题：Qwen 在 `evidence_report` / JSON 中经常已经识别出缺失目标，但最终答案只输出 `"The provided information is not enough."`。LongMemEval 的 judge 对这类拒答有时要求包含具体缺失对象。v79 将结构化 `missing` 字段透出到最终答案，因此修复了多条 “did not mention X” 类问题。

相对 v73：

- 单次 DeepSeek judge：`0.778 -> 0.784`，`389/500 -> 392/500`。
- prediction 实际改变：`29/500`。
- changed prediction：`WRONG->CORRECT 6`、`CORRECT->WRONG 0`、`WRONG->WRONG 14`、`CORRECT->CORRECT 9`，方法表面净 `+6`。
- unchanged prediction：`WRONG->CORRECT 4`、`CORRECT->WRONG 7`，同答案 judge 方差净 `-3`。
- finalizer reason：`missing_detail_from_structured_answer 29`、`model_marked_insufficient 13`、`no_structured_evidence_items 458`。

改对主要来自 multi-session 的缺失目标拒答，例如 egg tarts、30-gallon tank、iPad case、Sapiens pages、chili peppers，以及一个 temporal-reasoning Sacramento Airbnb 缺失位置。未修复的 14 条大多是 retrieval/reader 真失败：模型拒答但 gold 实际可由多证据计算或聚合得到，例如 bedtime、properties viewed、Rachel age、clinic arrival time、education age gap、novel page count、reading/listening weeks、sculpting class duration 等。

结论：v79 应保留为当前 LME 候选，因为它 clean、零额外 prediction LLM token、changed subset 无回退；但它不是通向 0.80+ 的主引擎。下一步应继续针对 `WRONG->WRONG` 中的多证据计算、list/count、temporal endpoint、profile/advice 做 build/query memory 组织，而不是继续扩大 missing-detail 类 finalizer。

## Summary

The run validates pipeline shape, clean traceability, and answerer integration under the configured experiment kind.

## Observations

- samples_processed: 500
- avg_compiled_evidence_items: 34.062
- avg_build_tokens: 80346.246
- build_token_accounting: logical cold-build LLM tokens; cached build chunks count from stored usage, while cache hits only avoid repeated local API calls.
- avg_build_memory_records: 129.662
- avg_active_build_memory_records: 116.456
- build_memory_temporal_fields: False
- build_memory_prompt_profile: typed_compact
- build_memory_manage_facts: True
- build_memory_overlap_turns: 0
- build_memory_cache_hits: 3341
- build_memory_cache_misses: 0
- build_memory_cache_writes: 0
- build_memory_source_alignment: {}
- build_memory_source_alignment_changed_records: 0
- build_memory_source_alignment_added_sources: 0
- avg_build_memory_source_alignment_changed_records: 0.0
- avg_build_memory_source_alignment_added_sources: 0.0
- avg_memory_hits: 8.236
- avg_memory_source_hits: 7.924
- build_memory_include_superseded: False
- build_memory_include_superseded_information_needs: ['temporal_lookup', 'list_count']
- avg_context_chars: 19665.154
- avg_query_tokens: 5864.706
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
- embedding_cache_hits: 247238
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
- current_state_update_contract: False
- dialogue_inference_contract: False
- temporal_order_contract: False
- source_anchor_keep: 0
- source_anchor_memory_rows: 0
- source_anchor_per_session: 0
- source_anchor_session_rows: 0
- route_overrides: {}
- enable_recommendation_profile_patterns: True
- enable_advice_profile_patterns: False
- temporal_priority_over_recent: False
- answer_max_input_tokens: 131072
- answer_max_output_tokens: 16384
- answer_cache_enabled: True
- answer_cache_path: outputs/cache/qwen3_answer_v42_operation_workpad.sqlite
- answer_cache_namespace: stage1_operation_workpad_v42_qwen3_30b
- answer_cache_hits: 500
- answer_cache_misses: 0
- answer_cache_writes: 0
- answer_finalizer_enabled: True
- answer_finalizer_mode: structured_evidence_mechanical
- answer_finalizer_enable_count_correction: False
- answer_finalizer_enable_evidence_report_count_correction: False
- answer_finalizer_enable_money_sum_correction: False
- answer_finalizer_enable_duration_rounding_correction: False
- answer_finalizer_enable_missing_detail: True
- answer_finalizer_applied_count: 29
- answer_finalizer_applied_rate: 0.058
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
