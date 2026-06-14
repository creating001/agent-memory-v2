# Diagnosis for stage1_profile_uncertain_repair_v52_lme_s_full_9a04884

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
- build_memory_cache_hits: 3341
- build_memory_cache_misses: 0
- build_memory_cache_writes: 0
- avg_memory_hits: 8.23
- avg_memory_source_hits: 7.918
- build_memory_include_superseded: False
- build_memory_include_superseded_information_needs: ['temporal_lookup', 'list_count']
- avg_context_chars: 19706.834
- avg_query_tokens: 5929.072
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
- enable_advice_profile_patterns: True
- temporal_priority_over_recent: False
- answer_max_input_tokens: 131072
- answer_max_output_tokens: 16384
- answer_cache_enabled: True
- answer_cache_path: outputs/cache/qwen3_answer_v42_operation_workpad.sqlite
- answer_cache_namespace: stage1_operation_workpad_v42_qwen3_30b
- answer_cache_hits: 30
- answer_cache_misses: 470
- answer_cache_writes: 470
- answer_finalizer_enabled: True
- answer_finalizer_mode: structured_evidence_mechanical
- answer_finalizer_enable_count_correction: False
- answer_finalizer_enable_evidence_report_count_correction: False
- answer_finalizer_enable_money_sum_correction: False
- answer_finalizer_enable_duration_rounding_correction: True
- answer_finalizer_applied_count: 2
- answer_finalizer_applied_rate: 0.004
- answer_repair_enabled: True
- answer_repair_mode: openai_compatible
- answer_repair_model: Qwen/Qwen3-30B-A3B-Instruct-2507
- answer_repair_max_input_tokens: 131072
- answer_repair_max_output_tokens: 16384
- answer_repair_information_needs: ['profile_preference']
- answer_repair_enable_profile_preference_trigger: False
- answer_repair_triggered_count: 6
- answer_repair_triggered_rate: 0.012
- answer_repair_applied_count: 5
- answer_repair_applied_rate: 0.01
- answer_repair_total_query_tokens: 23651
- answer_repair_avg_query_tokens_when_triggered: 3941.8333333333335
- answer_repair_cache_hits: 6
- answer_repair_cache_misses: 0
- answer_repair_cache_writes: 0
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0, max_input_tokens 131072, and max_output_tokens 16384.

## Next Steps

- Use offline lexical, judge, and evidence-recall scripts to diagnose quality after prediction is complete.
- Compare typed build memory on/off before adding more expensive answer-time reasoning.
- Keep each new method behind explicit config toggles for ablation.

## v52 Full 结论

v52 不是有效主线。它在 `single-session-preference_30` 诊断上比 v42 净 `+2`，但 full 结果为 `385/500 = 0.770000`，低于 v42 的 `387/500 = 0.774000` 和 v36 的 `386/500 = 0.772000`。

关键指标：

- avg_build_tokens：`80346.246`。
- avg_query_tokens：`5929.072`，通过 6K 预算。
- repair triggered：`6/500`。
- repair applied：`5/500`。
- answer_changed_vs_v42：`106/500`。
- route_changed_vs_v42：`15/500`。
- v52 vs v42：gain/loss `19/21`，net `-2`。

失败原因：

- profile/advice repair 的局部收益真实存在，但 full 重跑引入了更大范围的 answer variance；`106` 条答案变动远超 `6` 条 repair。
- advice route 扩展影响 `15` 条问题，局部能修正拒答，但也会让部分原本正确的 fact/list answer 变窄。
- 仅靠 answer-side repair 无法稳定提升 LME；它没有改善 build-stage profile/event memory 的组织，也没有更可靠地选择 profile anchors。

Clean 复核：

- prediction 阶段不读取 gold answer、judge output、benchmark label、question_type/category、sample id、row index 或 test feedback。
- prompt clean scan：`2` findings，均为 raw Memory Context 中原始对话自然包含 “correct answer” 字样；人工复核为 benign raw-context hit。

后续方向：

- 删除顶层 v52 config，只保留 formal `config_snapshot.json`。
- 不跑 v52 LoCoMo。
- 下一轮应转向 build/query 结合的 profile-anchor 方法：build 阶段抽取 profile/event/preference anchors，query 阶段只把 anchor table 用于 evidence selection 或 compact repair context，不让 40 条 raw rows 直接进入第二阶段 repair。
- 需要重点参考 `creating001` 的 query evidence extraction 思路，但必须去掉其不 clean 的 target/finalizer；同时继续读 SimpleMem、Memobase、MIRIX、xMemory 的 profile/event/multi-view source 回链实现。
