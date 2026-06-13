# Diagnosis for stage1_selective_repair_v32_locomo_nonadv_full_a80816a

## Summary

The run validates pipeline shape, clean traceability, and answerer integration under the configured experiment kind.

## Observations

- samples_processed: 1540
- avg_compiled_evidence_items: 40.0
- avg_build_tokens: 58386.00779220779
- build_token_accounting: logical cold-build LLM tokens; cached build chunks count from stored usage, while cache hits only avoid repeated local API calls.
- avg_build_memory_records: 136.65974025974026
- avg_active_build_memory_records: 125.11233766233767
- build_memory_temporal_fields: False
- build_memory_cache_hits: 12411
- build_memory_cache_misses: 0
- build_memory_cache_writes: 0
- avg_memory_hits: 19.84155844155844
- avg_memory_source_hits: 22.37922077922078
- build_memory_include_superseded: False
- build_memory_include_superseded_information_needs: ['temporal_lookup', 'list_count']
- avg_context_chars: 11416.253896103895
- avg_query_tokens: 4466.223376623377
- dense_protect_top_n: 32
- session_bm25_enabled: False
- session_bm25_top_k: None
- session_anchor_top_k: None
- session_enabled_route_signals: None
- session_bm25_applied_count: 0
- session_bm25_applied_rate: 0.0
- embedding_cache_enabled: True
- embedding_cache_hits: 7422
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
- evidence_report_detail: False
- route_overrides: {}
- enable_recommendation_profile_patterns: True
- temporal_priority_over_recent: False
- answer_max_input_tokens: 131072
- answer_max_output_tokens: 16384
- answer_cache_enabled: True
- answer_cache_path: outputs/cache/qwen3_answer_v29.sqlite
- answer_cache_namespace: stage1_temporal_event_contract_v29_qwen3_30b
- answer_cache_hits: 1540
- answer_cache_misses: 0
- answer_cache_writes: 0
- answer_finalizer_enabled: False
- answer_finalizer_mode: structured_evidence_mechanical
- answer_finalizer_enable_count_correction: False
- answer_finalizer_enable_money_sum_correction: True
- answer_finalizer_applied_count: 0
- answer_finalizer_applied_rate: 0.0
- answer_repair_enabled: True
- answer_repair_mode: openai_compatible
- answer_repair_model: Qwen/Qwen3-30B-A3B-Instruct-2507
- answer_repair_max_input_tokens: 131072
- answer_repair_max_output_tokens: 16384
- answer_repair_information_needs: ['current_state', 'fact_lookup', 'list_count', 'profile_preference', 'temporal_lookup']
- answer_repair_triggered_count: 263
- answer_repair_triggered_rate: 0.17077922077922078
- answer_repair_applied_count: 11
- answer_repair_applied_rate: 0.007142857142857143
- answer_repair_total_query_tokens: 819828
- answer_repair_avg_query_tokens_when_triggered: 3117.216730038023
- answer_repair_cache_hits: 263
- answer_repair_cache_misses: 0
- answer_repair_cache_writes: 0
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0, max_input_tokens 131072, and max_output_tokens 16384.

## Next Steps

- Use offline lexical, judge, and evidence-recall scripts to diagnose quality after prediction is complete.
- Compare typed build memory on/off before adding more expensive answer-time reasoning.
- Keep each new method behind explicit config toggles for ablation.

## Offline Accuracy Diagnosis

LoCoMo non-adversarial full 已完成严格 draft-cache 对照版 prediction + offline DeepSeek judge。

核心结果：

- DeepSeek judge accuracy: `0.7616883116883116`
- correct/valid/total: `1173/1540/1540`
- v29 reference: `1173/1540 = 0.7616883116883116`
- avg build tokens: `58386.00779220779`
- avg query tokens: `4466.223376623377`
- evidence recall: `0.8912760416666666`
- answer max input/output: `131072/16384`
- repair max input/output: `131072/16384`

v32 与 v29 持平，没有达到 LoCoMo `0.78` target，也没有超过 v29。因此 v32 是 neutral ablation，不应作为新主线，也不值得继续跑 LongMemEval-S full。

## Repair Behavior

v32 的工程口径是 clean 且 token 合格：

- draft answer cache 从 v29 prediction traces seed，脚本只读取 prediction-time prompt/answer/usage，不读取 labels、judge、category、sample id 或 test feedback。
- draft answer cache hits/misses/writes: `1540/0/0`
- repair triggered: `263/1540 = 0.17077922077922078`
- repair applied: `11/1540 = 0.007142857142857143`
- repair total query tokens: `819828`
- repair avg query tokens when triggered: `3117.216730038023`
- repair cache hits/misses/writes: `263/0/0`

repair-applied 子集单独 judge：

- fixed: `3`
- broken: `1`
- both_correct: `2`
- both_wrong: `5`

说明 repair prompt 在少数 unknown/temporal type mismatch 上有正向信号，但触发后绝大多数 decision=keep，实际修改率只有 `0.7%`，不足以推动 full accuracy。

## Comparison Notes

`judge_comparison_vs_v29.json` 显示：

- both_correct: `1143`
- both_wrong: `337`
- gained: `30`
- lost: `30`

同答案 judge flip 基本抵消：

- same WRONG->CORRECT: `16`
- same CORRECT->WRONG: `17`

因此不能把局部 gained 解释成方法提升。真正的方法差异主要来自 11 条 repair-applied 样本，净收益小但不够。

## Design Implication

v32 证实了一个方向：answer-side verifier 可以修复少数拒答和 yes/no temporal mismatch，但当前“只读同一 context 的保守 repair”太弱。下一步不应继续扩大二次读取触发率来硬换分，因为这会增加 query tokens 且容易引入 temporal/list 误改。

更值得做的 v33 方向：

- 回到 v29/v32 badcase，区分 retrieval miss、context 内证据未用、draft refusal、temporal conflict、list boundary。
- 参考外部代码实现更强的 query-side evidence expansion，而不是只让 repair 重读同一 context。
- build-side 继续设计更好的 memory management：event/profile/state 分通道、更新事实的 temporal validity、source-linked compact memory，但必须先保证 source activation 不下降。
- 如果做 verifier，应让它输出可审计的 error type 和 required evidence gap，并只在 gap 可由运行时检索补全时二次检索；不要无差别重写答案。
