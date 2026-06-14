# Diagnosis for v51_profile_repair_lme_pref_79b1424

## Summary

The run validates pipeline shape, clean traceability, and answerer integration under the configured experiment kind.

## Observations

- samples_processed: 30
- avg_compiled_evidence_items: 37.733333333333334
- avg_build_tokens: 79618.66666666667
- build_token_accounting: logical cold-build LLM tokens; cached build chunks count from stored usage, while cache hits only avoid repeated local API calls.
- avg_build_memory_records: 129.03333333333333
- avg_active_build_memory_records: 111.7
- build_memory_temporal_fields: False
- build_memory_cache_hits: 199
- build_memory_cache_misses: 0
- build_memory_cache_writes: 0
- avg_memory_hits: 6.966666666666667
- avg_memory_source_hits: 6.3
- build_memory_include_superseded: False
- build_memory_include_superseded_information_needs: ['temporal_lookup', 'list_count']
- avg_context_chars: 16780.566666666666
- avg_query_tokens: 8382.666666666666
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
- embedding_cache_hits: 14764
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
- answer_cache_hits: 7
- answer_cache_misses: 23
- answer_cache_writes: 23
- answer_finalizer_enabled: True
- answer_finalizer_mode: structured_evidence_mechanical
- answer_finalizer_enable_count_correction: False
- answer_finalizer_enable_evidence_report_count_correction: False
- answer_finalizer_enable_money_sum_correction: False
- answer_finalizer_enable_duration_rounding_correction: True
- answer_finalizer_applied_count: 0
- answer_finalizer_applied_rate: 0.0
- answer_repair_enabled: True
- answer_repair_mode: openai_compatible
- answer_repair_model: Qwen/Qwen3-30B-A3B-Instruct-2507
- answer_repair_max_input_tokens: 131072
- answer_repair_max_output_tokens: 16384
- answer_repair_information_needs: ['profile_preference']
- answer_repair_enable_profile_preference_trigger: True
- answer_repair_triggered_count: 23
- answer_repair_triggered_rate: 0.7666666666666667
- answer_repair_applied_count: 6
- answer_repair_applied_rate: 0.2
- answer_repair_total_query_tokens: 96495
- answer_repair_avg_query_tokens_when_triggered: 4195.434782608696
- answer_repair_cache_hits: 0
- answer_repair_cache_misses: 23
- answer_repair_cache_writes: 23
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0, max_input_tokens 131072, and max_output_tokens 16384.

## Next Steps

- Use offline lexical, judge, and evidence-recall scripts to diagnose quality after prediction is complete.
- Compare typed build memory on/off before adding more expensive answer-time reasoning.
- Keep each new method behind explicit config toggles for ablation.

## v51 诊断结论

v51 验证了一个有价值但过贵的信号：profile/advice 类问题中，answer draft 经常已经拿到相关 raw context，却没有把用户偏好、资源、约束和当前问题组合成可接受的 personalized answer。第二阶段 repair 能修复这类“拒答/泛答”错误。

准确率：

- v51 same30 DeepSeek judge：`16/30 = 0.533333`。
- v42 same30：`13/30 = 0.433333`。
- v50 same30：`12/30 = 0.400000`。
- v51 vs v42：gain/loss `6/3`，net `+3`。

repair 直接贡献：

- repair triggered：`23/30`。
- repair applied：`6/30`。
- 对 applied 的 6 条单独 judge draft：draft `0/6`，final `3/6`。
- repair 直接净增益 `+3`，没有把 draft-correct 改成 final-wrong。
- 典型修复：medical imaging publications/conferences、Miami hotel preference、phone battery/power bank。

主要问题：

- avg_query_tokens `8382.667`，超过 8K diagnostic 边界；repair 每次平均 `4195.435` query tokens。
- triggered_keep 有 `17` 条，说明当前“所有 profile_preference 都 repair”的触发过宽，浪费了大量 query token。
- v51 仍有 loss：部分 advice route 改写后答案变窄或不够覆盖，例如 baking/guitar/cultural events；这说明 route 扩展和 repair 都需要更好的 evidence selection，而不是更长 prompt。

Clean 判断：

- prediction 只读取 question、question_time、raw dialogue、build memory、retrieval result、route、draft answer 和 Memory Context。
- 不读取 gold answer、judge output、benchmark label、question_type/category、sample id、row index 或 test feedback。
- prompt clean scan：`0` findings。

下一步不跑 full。先做 token-safe v52：

- 只在 draft 是 insufficient/unknown 或 answer 过短且 Memory Context 有 profile anchors 时触发 repair。
- repair context 不再直接塞 40 条 raw rows；先用轻量 profile-anchor extractor 或 compiler-side anchor table 压到 2K-3K prompt tokens。
- 保留 v51 的 repair prompt 方向，但把 applied/triggered 比例从 `6/23` 提高，目标是 full route mix 下 avg query <= 6K。
