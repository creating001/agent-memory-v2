# Diagnosis for formal/stage1_temporal_preference_v4_lme_s_full_6c7d51e_cached

## Summary

v4 是一个 clean 的 query-side 正向消融：复用 v1 冷构建 cache，在 v3 typed memory compiler 上增加 temporal calculation workpad 和 personalized recommendation route。DeepSeek judge accuracy 为 0.596（298/500），相对 v3 的 0.558 净增 19 个样本。

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
- avg_context_chars: 21378.516
- avg_query_tokens: 5760.424
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
- enable_recommendation_profile_patterns: True
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0.0 and max_tokens 16384.
- deepseek_judge_accuracy: 0.596
- deepseek_judge_correct: 298
- deepseek_judge_wrong: 202
- deepseek_judge_usage_total_tokens: 117190
- offline_evidence_recall: 0.978
- offline_evidence_recall_n: 500

## DeepSeek Judge By Type

| type | correct | total | accuracy |
|---|---:|---:|---:|
| knowledge-update | 57 | 78 | 0.7308 |
| multi-session | 47 | 133 | 0.3534 |
| single-session-assistant | 48 | 56 | 0.8571 |
| single-session-preference | 11 | 30 | 0.3667 |
| single-session-user | 61 | 70 | 0.8714 |
| temporal-reasoning | 74 | 133 | 0.5564 |

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

- v4 的主要收益来自 temporal-reasoning：相对 v3 净增 23 个 temporal 样本，说明显式日期候选、pairwise gap 和 order workpad 能帮助 answer LLM 正确使用已召回证据。
- personalized recommendation route 对 preference 有帮助：single-session-preference 从 8/30 提到 11/30，但绝对值仍低，说明 build memory 仍没有稳定地区分长期偏好、一次性事件和推荐目标。
- multi-session 从 51/133 降到 47/133，single-session-assistant 也小幅回退；temporal workpad 带来的额外日期候选可能给非纯 temporal/multi-hop 问题增加噪声。
- avg query tokens 5760.424 仍在 6K 主线预算内，但接近上限；下一步不能继续无差别加 context，需要更紧的 gating 和 compact workpad。
- offline evidence recall 0.978，与 v3 基本持平，说明这次收益不是扩大召回，而是更好地组织和使用证据。
- avg build tokens 为 0 是因为本次完全复用 build cache；真实冷构建成本仍应参考 v1 冷构建记录。

## Next Steps

- 保留 v4 作为当前 LME best，但不要直接把完整 workpad 作为长期默认。
- 做 query-side v4.1：只在 duration/order/ago 问题上启用 compact workpad，减少 multi-session 噪声和 token 成本。
- 并行规划 build-side v5：profile/event/state 分离、temporal validity、conflict/supersede chain 和 raw-source backed aggregation，冷构建前先写清消融开关。
