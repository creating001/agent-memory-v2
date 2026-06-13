# Diagnosis for stage1_evidence_report_detail_v31_locomo_nonadv_full_894c7ee

## Summary

LoCoMo non-adversarial full 已完成 prediction + offline DeepSeek judge。v31 的 source coverage gate 通过，token gate 通过，但 full accuracy 低于 v29，因此这是负向 ablation，不应替代当前 LoCoMo 主线。

核心结果：

- DeepSeek judge accuracy: `0.7551948051948052`
- correct/valid/total: `1163/1540/1540`
- v29 对照: `1173/1540 = 0.7616883116883116`
- v31 vs v29: `-10` correct overall
- v31 token gate: avg build `58386.008` <= `100K`，avg query `4275.424` <= `6K`
- commit: `894c7ee1b6203681d8d5c59d5b79eb12fbd1073e`
- dirty: true，仅包含用户编辑的 `docs/architecture.md` 和 `docs/clean_protocol.md`，以及本次实验输出目录。

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
- avg_context_chars: 12893.451298701299
- avg_query_tokens: 4275.424025974026
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
- evidence_report_max_items: 12
- evidence_report_detail: True
- route_overrides: {}
- enable_recommendation_profile_patterns: True
- temporal_priority_over_recent: False
- answer_max_input_tokens: 131072
- answer_max_output_tokens: 16384
- answer_cache_enabled: True
- answer_cache_path: outputs/cache/qwen3_answer_v31.sqlite
- answer_cache_namespace: stage1_evidence_report_detail_v31_qwen3_30b
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

v31 与 v29 的 judge 差异：

- both_correct: `1118`
- both_wrong: `322`
- gained: `45`
- lost: `55`

按 route：

- fact_lookup: gained `30`, lost `25`
- temporal_lookup: gained `6`, lost `16`
- list_count: gained `8`, lost `10`
- profile_preference: gained `1`, lost `4`
- current_state: unchanged

Evidence recall 没有回退，反而略高：

- v31 evidence_recall: `0.8912760416666666`
- v29 evidence_recall: `0.8893229166666666`
- v31 avg_memory_source_hits: `22.37922077922078`
- v29 avg_memory_source_hits: `22.381168831168832`
- v31 avg_context_chars: `12893.4513`
- v29 avg_context_chars: `11417.0481`

因此失败点不是 retrieval/source activation，而是 answer/compiler。detailed evidence_report 修复了一些 `unknown`、lower-bound、assistant suggestion 和 fact slot 错误，但 prompt 变长并让模型更保守，导致 temporal_lookup、list_count 和 profile_preference 回退。

同答案 judge 翻转：

- same_WRONG_to_CORRECT: `10`
- same_CORRECT_to_WRONG: `7`

答案变化导致的净效应为 `changed_WRONG_to_CORRECT=35`、`changed_CORRECT_to_WRONG=48`，即净少 13 条。整体负向不是单纯 judge 抖动。

## Design Implication

v31 说明“继续堆通用 prompt 规则”不是最有效路径。v29 已经有足够多 evidence-hit wrong，但单次 answer prompt 很难同时兼顾完整列表、宽松 judge、temporal precision 和不过度拒答。

下一步建议：

- 回到 v29 作为主线底座。
- 不跑 v31 LongMemEval full。
- 设计 v32 时避免继续无差别加长主 prompt。
- 优先考虑可消融的 selective repair/verifier：只在模型输出 unknown、list 可能 partial、temporal answer 与 evidence_report 冲突时触发第二步；其他样本保持 v29 简洁 prompt。
- selective repair 必须只看 question、retrieved context 和 draft answer，不看 gold/judge/category/sample id。

## Next Steps

- 记录 v31 为负向 ablation。
- 设计 v32 selective repair，并先做 no-label/token gate。
- 如果 v32 gate 通过，再跑 LoCoMo full；不要基于 v31 跑 LongMemEval full。
