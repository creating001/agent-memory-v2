# Diagnosis for formal/stage1_temporal_preference_v4_1_lme_s_full_c5e6276_cached

## Summary

v4.1 是 v4 的 cost/compactness 消融：只在 temporal/current 且明确需要 duration / ago / between / order 计算的问题上启用紧凑 workpad。DeepSeek judge accuracy 为 0.584（292/500），低于 v4 的 0.596，但仍高于 v3 的 0.558。

## Observations

- samples_processed: 500
- avg_compiled_evidence_items: 12.522
- avg_build_memory_records: 129.662
- avg_active_build_memory_records: 116.492
- build_memory_cache_hits: 3341
- build_memory_cache_misses: 0
- build_memory_cache_writes: 0
- avg_memory_hits: 7.756
- avg_memory_source_hits: 7.528
- avg_context_chars: 20801.958
- avg_query_tokens: 5468.818
- session_bm25_enabled: True
- session_bm25_top_k: 8
- session_anchor_top_k: 2
- session_enabled_route_signals: ['temporal', 'recent_or_current']
- session_bm25_applied_count: 193
- session_bm25_applied_rate: 0.386
- embedding_cache_enabled: True
- embedding_cache_hits: 247238
- embedding_cache_misses: 0
- evidence_order: question_overlap
- memory_order: question_overlap
- memory_layout: typed_sections
- row_text_mode: full
- max_row_text_chars: 0
- max_memory_records: 16
- route_guidance: True
- temporal_workpad: True
- temporal_workpad_scope: calculation_route
- temporal_workpad_max_rows: 6
- temporal_workpad_max_pairs: 8
- enable_recommendation_profile_patterns: True
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0.0 and max_tokens 16384.
- deepseek_judge_accuracy: 0.584
- deepseek_judge_correct: 292
- deepseek_judge_wrong: 208
- deepseek_judge_usage_total_tokens: 114572
- offline_evidence_recall: 0.978
- offline_evidence_recall_n: 500

## DeepSeek Judge By Type

| type | correct | total | accuracy |
|---|---:|---:|---:|
| knowledge-update | 55 | 78 | 0.7051 |
| multi-session | 47 | 133 | 0.3534 |
| single-session-assistant | 46 | 56 | 0.8214 |
| single-session-preference | 9 | 30 | 0.3000 |
| single-session-user | 62 | 70 | 0.8857 |
| temporal-reasoning | 73 | 133 | 0.5489 |

## Offline Evidence Recall

| type | n | evidence_recall |
|---|---:|---:|
| knowledge-update | 78 | 1.0000 |
| multi-session | 133 | 0.9624 |
| single-session-assistant | 56 | 1.0000 |
| single-session-preference | 30 | 0.9667 |
| single-session-user | 70 | 0.9857 |
| temporal-reasoning | 133 | 0.9699 |

## Diagnosis

- v4.1 降低了成本：workpad prompts 从 v4 的 198 降到 120，avg query tokens 从 5760.424 降到 5468.818。
- 但 accuracy 从 0.596 降到 0.584，v4.1 vs v4 为 10 improved、16 regressed、-6 net correct。
- offline evidence recall 仍为 0.978，说明负向变化不是召回缺失，而是 compact/gated workpad 少给了一部分 answer LLM 能利用的时间组织信号。
- temporal-reasoning 仍显著高于 v3（73/133 vs 51/133），但低于 v4（74/133）；更大的降幅来自 knowledge-update、assistant 和 preference。
- 该结果说明 v4 的 full workpad 虽然接近 token 上限，但包含有用 signal；下一步不应继续简单缩短 workpad，而应从 build-stage memory management 或更智能的 evidence compiler 入手。

## Next Steps

- 保留 v4 为当前 LME mainline best；v4.1 仅作为成本消融。
- 下一步优先做 build-side v5：profile/event/state 分离、temporal validity、conflict/supersede chain 和 source-backed aggregation。
- 如果继续 query-side，只做针对 multi-session 的 evidence aggregation，不再无差别压缩 temporal workpad。
