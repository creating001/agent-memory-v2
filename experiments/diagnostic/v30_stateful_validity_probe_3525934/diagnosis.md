# Diagnosis for v30_stateful_validity_probe_3525934

## 中文诊断结论

本次诊断解决了前一版 v30 probe 暴露的核心问题：LLM build 输出会把 `valid_from/valid_to` 过度填到一次性 fact/event/plan 上，容易让 answer 阶段把历史事实误当当前状态。当前代码在 `temporal_fields=true` 时只对 `state/profile/preference/relationship` 做 validity/supersede 管理；`event/fact/plan` 只保留 `event_time`，不再携带 validity interval。

字段门禁结果：

- `record_total=1711`
- `mention_time=1711`
- `event_time=424`
- `valid_from=458`
- `valid_to=97`
- `non_stateful_validity_records=0`

按类型看，`event/fact/plan/unknown` 都没有 `valid_from/valid_to`；`preference/profile/relationship/state` 保留 validity。这个行为符合通用 agent memory 设计：事件时间和状态有效期分离，避免把一次性事件升级成长期状态。

Token 与运行稳定性：

- avg build tokens `65592.3`，在 LME/LoCoMo 主线预算趋势内。
- avg query tokens `4984.55`，低于 6K。
- build cache 全命中 `128/0/0`，但 token 成本按 cached usage 计入，代表新环境冷构建成本。
- answer max input/output 为 `131072/16384`。
- 20/20 预测完成，无 JSON 输出格式崩坏。

质量风险：

- 这 20 条没有运行 DeepSeek judge；它只验证字段和流程，不作为 accuracy 结论。
- 一些示例答案仍显示 list/count 和 insufficient-evidence 风险，例如 LME coupon/location、LoCoMo children count。这说明 v30 build-side typed memory 可能还不能解决所有 compiler/aggregation 问题。
- v30 当前只把 typed memory 暴露给 `temporal_lookup/current_state`，因此 full run 的主要预期收益仍应来自 temporal/current，不应期待 list_count 大幅提升。

Full run gate 判断：

- 字段质量：通过。
- token 预算：通过。
- clean：通过；dirty 只包含用户 docs 修改和当前 v30 代码改动，预测 pipeline 未使用 gold/judge/category/sample id/evidence 标签。
- 建议：先提交 v30 validity 修正，再跑 LoCoMo non-adversarial full；如果 LoCoMo 接近或超过 v29，再跑 LongMemEval-S full。若 LoCoMo 不升，优先回到 compiler/list aggregation 和 retrieval miss 诊断，而不是继续扩大 temporal prompt。

## Summary

The run validates pipeline shape, clean traceability, and answerer integration under the configured experiment kind.

## Observations

- samples_processed: 20
- avg_compiled_evidence_items: 36.7
- avg_build_tokens: 65592.3
- build_token_accounting: logical cold-build LLM tokens; cached build chunks count from stored usage, while cache hits only avoid repeated local API calls.
- avg_build_memory_records: 85.55
- avg_active_build_memory_records: 80.7
- build_memory_temporal_fields: True
- build_memory_cache_hits: 128
- build_memory_cache_misses: 0
- build_memory_cache_writes: 0
- avg_memory_hits: 12.25
- avg_memory_source_hits: 15.2
- build_memory_include_superseded: False
- build_memory_include_superseded_information_needs: ['temporal_lookup', 'list_count']
- avg_context_chars: 15788.3
- avg_query_tokens: 4984.55
- dense_protect_top_n: 32
- session_bm25_enabled: False
- session_bm25_top_k: None
- session_anchor_top_k: None
- session_enabled_route_signals: None
- session_bm25_applied_count: 0
- session_bm25_applied_rate: 0.0
- embedding_cache_enabled: True
- embedding_cache_hits: 5440
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
- temporal_event_contract: True
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
- route_overrides: {'temporal_lookup': {'max_memory_records': 8, 'structured_guide_include_memory': True}, 'current_state': {'max_memory_records': 6, 'structured_guide_include_memory': True}}
- enable_recommendation_profile_patterns: True
- temporal_priority_over_recent: False
- answer_max_input_tokens: 131072
- answer_max_output_tokens: 16384
- answer_cache_enabled: True
- answer_cache_path: outputs/cache/qwen3_answer_v30.sqlite
- answer_cache_namespace: stage1_typed_event_memory_v30_qwen3_30b
- answer_cache_hits: 17
- answer_cache_misses: 3
- answer_cache_writes: 3
- answer_finalizer_enabled: False
- answer_finalizer_mode: structured_evidence_mechanical
- answer_finalizer_enable_count_correction: False
- answer_finalizer_enable_money_sum_correction: True
- answer_finalizer_applied_count: 0
- answer_finalizer_applied_rate: 0.0
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0, max_input_tokens 131072, and max_output_tokens 16384.

## Next Steps

- Use offline lexical, judge, and evidence-recall scripts to diagnose quality after prediction is complete.
- Compare typed build memory on/off before adding more expensive answer-time reasoning.
- Keep each new method behind explicit config toggles for ablation.
