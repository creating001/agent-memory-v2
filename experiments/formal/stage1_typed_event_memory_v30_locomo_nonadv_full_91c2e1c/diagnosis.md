# Diagnosis for stage1_typed_event_memory_v30_locomo_nonadv_full_91c2e1c

## Summary

LoCoMo non-adversarial full 已完成 prediction + offline DeepSeek judge。v30 的 stateful validity 修正是 clean 的，并且 token gate 通过，但 full accuracy 低于 v29，因此这是负向 ablation，不应替代当前 LoCoMo 主线。

核心结果：

- DeepSeek judge accuracy: `0.755685510071475`
- correct/valid/total: `1163/1539/1540`
- invalid judge outputs: `1`
- v29 对照: `1173/1540 = 0.7616883116883116`
- v30 vs v29: `-10` correct overall
- v30 token gate: avg build `61047.409` <= `100K`，avg query `4047.905` <= `6K`
- commit: `91c2e1c2b73dde4f8372ac20400725d205582263`
- dirty: true，仅包含用户编辑的 `docs/architecture.md` 和 `docs/clean_protocol.md`，以及本次实验输出目录。

## Observations

- samples_processed: 1540
- avg_compiled_evidence_items: 40.0
- avg_build_tokens: 61047.40909090909
- build_token_accounting: logical cold-build LLM tokens; cached build chunks count from stored usage, while cache hits only avoid repeated local API calls.
- avg_build_memory_records: 94.45454545454545
- avg_active_build_memory_records: 89.79935064935064
- build_memory_temporal_fields: True
- build_memory_cache_hits: 11784
- build_memory_cache_misses: 627
- build_memory_cache_writes: 627
- avg_memory_hits: 19.822727272727274
- avg_memory_source_hits: 21.43896103896104
- build_memory_include_superseded: False
- build_memory_include_superseded_information_needs: ['temporal_lookup', 'list_count']
- avg_context_chars: 11771.485064935065
- avg_query_tokens: 4047.9045454545453
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
- route_overrides: {'temporal_lookup': {'max_memory_records': 8, 'structured_guide_include_memory': True}, 'current_state': {'max_memory_records': 6, 'structured_guide_include_memory': True}}
- enable_recommendation_profile_patterns: True
- temporal_priority_over_recent: False
- answer_max_input_tokens: 131072
- answer_max_output_tokens: 16384
- answer_cache_enabled: True
- answer_cache_path: outputs/cache/qwen3_answer_v30.sqlite
- answer_cache_namespace: stage1_typed_event_memory_v30_qwen3_30b
- answer_cache_hits: 11
- answer_cache_misses: 1529
- answer_cache_writes: 1529
- answer_finalizer_enabled: False
- answer_finalizer_mode: structured_evidence_mechanical
- answer_finalizer_enable_count_correction: False
- answer_finalizer_enable_money_sum_correction: True
- answer_finalizer_applied_count: 0
- answer_finalizer_applied_rate: 0.0
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0, max_input_tokens 131072, and max_output_tokens 16384.

## Offline Accuracy Diagnosis

v30 与 v29 的 judge 差异：

- both_correct: `1106`
- both_wrong_or_invalid: `310`
- gained: `57`
- lost: `67`

按 route 看，v30 没有形成稳定优势：

- fact_lookup: gained `33`, lost `34`
- temporal_lookup: gained `15`, lost `21`
- list_count: gained `6`, lost `9`
- profile_preference: gained `3`, lost `3`
- current_state: unchanged, only 4 samples

DeepSeek judge 有一定抖动：v29/v30 答案完全相同的样本有 `932` 条，其中 `15` 条 judge 标签翻转。只看答案变化样本，v30 是 `+51/-58`，净少约 7 条正确。因此 v30 不是大幅灾难性退化，但也没有达到可接受提升。

Evidence recall 下降是主要风险信号：

- v30 evidence_recall: `0.8802083333333334`
- v29 evidence_recall: `0.8893229166666666`
- v30 avg_memory_source_hits: `21.43896103896104`
- v29 avg_memory_source_hits: `22.381168831168832`
- v30 avg_records: `94.45454545454545`
- v29 avg_records: `136.65974025974026`

lost 的 67 条里，`50` 条 v29/v30 都有 evidence hit，说明 compiler/answer 仍然是大头；但 `10` 条从 v29 evidence hit 变成 v30 miss，说明 typed memory 记录数下降确实伤到了 source activation 覆盖。gained 的 57 条里有 `39` 条 v29/v30 都 hit，说明 v30 的 temporal fields 有局部帮助，但收益不足以抵消回退。

## Design Implication

v30 的字段语义更合理：一次性 event/fact/plan 不再被强行赋予 validity interval，state/profile/preference/relationship 才参与 valid_from/valid_to 和 supersede。这个代码能力应该保留。

但当前 v30 config 把 build prompt 改得过窄，导致记录数和 source activation 降低。下一步 v31 应该：

- 保留 stateful validity 语义。
- 恢复或提升 v29 级别的 source activation 覆盖，避免 typed temporal memory 减少 raw evidence recall。
- 把 event_time/mention_time 作为 compiler 辅助视图，而不是让它改变 raw retrieval 覆盖。
- 优先改通用 source activation / compiler aggregation，不写 category、sample id、具体题目或实体规则。
- 新方法先做 LoCoMo full 前的字段/coverage gate，再决定是否跑 full；不要基于这版 v30 直接跑 LongMemEval full。

## Next Steps

- 设计 v31：typed temporal sidecar + source activation coverage preservation。
- 重点参考外部实现的通用机制：creating001 的两阶段 evidence table、SimpleMem 的 lossless memory + hybrid retrieval、Graphiti/Zep 的 temporal validity/provenance、MIRIX episodic schema。
- 做一个不读 label/judge/category/sample id 的 coverage diagnostic，确认 avg records/source hits 不低于 v29，再跑 full。
