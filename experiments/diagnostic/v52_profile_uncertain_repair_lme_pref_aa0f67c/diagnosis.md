# Diagnosis for v52_profile_uncertain_repair_lme_pref_aa0f67c

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
- avg_query_tokens: 5954.533333333334
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
- answer_cache_hits: 30
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
- answer_repair_enabled: True
- answer_repair_mode: openai_compatible
- answer_repair_model: Qwen/Qwen3-30B-A3B-Instruct-2507
- answer_repair_max_input_tokens: 131072
- answer_repair_max_output_tokens: 16384
- answer_repair_information_needs: ['profile_preference']
- answer_repair_enable_profile_preference_trigger: False
- answer_repair_triggered_count: 6
- answer_repair_triggered_rate: 0.2
- answer_repair_applied_count: 5
- answer_repair_applied_rate: 0.16666666666666666
- answer_repair_total_query_tokens: 23651
- answer_repair_avg_query_tokens_when_triggered: 3941.8333333333335
- answer_repair_cache_hits: 0
- answer_repair_cache_misses: 6
- answer_repair_cache_writes: 6
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0, max_input_tokens 131072, and max_output_tokens 16384.

## Next Steps

- Use offline lexical, judge, and evidence-recall scripts to diagnose quality after prediction is complete.
- Compare typed build memory on/off before adding more expensive answer-time reasoning.
- Keep each new method behind explicit config toggles for ablation.

## v52 诊断结论

v52 的核心结论是：v51 的 profile repair 思路有效，但只有在 draft 明确拒答/unknown/missing 时才值得付出第二阶段 LLM 成本。这个收窄把 repair 触发从 `23/30` 降到 `6/30`，query token 从 `8382.667` 降到 `5954.533`，同时仍比 v42 same30 净 `+2`。

准确率：

- v42 same30：`13/30 = 0.433333`。
- v51 same30：`16/30 = 0.533333`。
- v52 same30：`15/30 = 0.500000`。
- v52 vs v42：gain/loss `6/4`，net `+2`。
- v52 vs v51：少 1 条 correct，但平均 query token 少 `2428.133`。

成本：

- avg_build_tokens：`79618.667`。
- avg_query_tokens：`5954.533`，通过 6K 预算。
- repair triggered：`6/30`。
- repair applied：`5/30`。
- repair_avg_query_tokens_when_triggered：`3941.833`。

主要收益：

- 继续修复 phone battery / power bank、medical imaging publications/conferences 等拒答型 profile advice badcase。
- 额外修复 bedroom furniture case：同样是 mid-century modern profile anchor，但 v52 prompt 输出更贴合 dresser/layout。

主要风险：

- Miami hotel case 回退：repair 被触发但 keep 了拒答，说明 `uncertain_or_missing` 这个 trigger reason 对 profile advice 的动作约束不如 v51 的 `profile_preference_review` 稳。
- Baking/guitar 等 route 扩展仍可能让 answer 变窄；后续如果 full 出现 regression，需要把 advice route 与 repair trigger 解耦，或者加 profile-anchor evidence selection，而不是扩大 prompt。
- 有 same-answer judge variance：phone accessory case v51/v52 answer 相同，但 judge label 从 CORRECT 变 WRONG。

Clean 判断：

- prediction 只读取 question、question_time、raw dialogue、build memory、retrieval result、route、draft answer 和 Memory Context。
- 不读取 gold answer、judge output、benchmark label、question_type/category、sample id、row index 或 test feedback。
- prompt clean scan：`0` findings。

下一步：

- 运行 LongMemEval-S full，使用 v52 config；由于 full 中 profile/advice 影响范围小且 cache 已热，运行成本可控。
- full 结果如果只是小幅正向，应记录为 current-best incremental，不宣称达到 baseline target。
- 若 full regression 明显，则转 v53：新增“profile trigger requires uncertain”配置，让触发仍窄，但 repair prompt reason 保持 v51 的 `profile_preference_review`。
