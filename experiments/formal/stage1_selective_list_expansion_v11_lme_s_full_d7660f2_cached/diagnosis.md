# Diagnosis for formal/stage1_selective_list_expansion_v11_lme_s_full_d7660f2_cached

## Summary

v11 是一个 clean 的 query-side selective expansion 消融：默认保持 v7，只对通用 `list_count` information need 使用受限 role-aware snippet 扩展。DeepSeek judge accuracy 为 0.594（297/500），低于 v7/v6 的 0.606；avg_query_tokens=5824.768，低于 6K 主线预算。该实验 cost-positive 但 accuracy-negative，不进入主线。

## Observations

- samples_processed: 500
- avg_compiled_evidence_items: 15.498
- avg_build_memory_records: 129.662
- avg_active_build_memory_records: 116.492
- build_memory_cache_hits: 3341
- build_memory_cache_misses: 0
- build_memory_cache_writes: 0
- avg_memory_hits: 8.208
- avg_memory_source_hits: 7.894
- build_memory_include_superseded: False
- build_memory_include_superseded_information_needs: ['temporal_lookup', 'list_count']
- avg_context_chars: 20844.396
- avg_query_tokens: 5824.768
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
- evidence_row_labels: False
- final_answer_checklist: False
- max_memory_records: 16
- route_guidance: True
- temporal_workpad: True
- temporal_text_normalization: False
- temporal_workpad_scope: route
- temporal_workpad_max_rows: 10
- temporal_workpad_max_pairs: 12
- route_overrides: {'list_count': {'max_evidence_items': 24, 'max_evidence_chars': 15000, 'row_text_mode': 'role_query_snippet', 'max_row_text_chars': 500, 'evidence_row_labels': False, 'final_answer_checklist': False}}
- enable_recommendation_profile_patterns: True
- temporal_priority_over_recent: False
- answer_max_input_tokens: 131072
- answer_max_output_tokens: 16384
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0.0, max_input_tokens 131072, and max_output_tokens 16384.

## Next Steps

- 不要继续只靠调大或调小 evidence 行数探索。v10 证明全局扩展会引入噪声，v11 证明只给 list_count 做受限 snippet 也不能稳定提升 accuracy。
- list_count 是核心短板：v11 为 61/119，低于 v7 的 63/119。下一步更应做 build-stage list/event aggregation 或 query-time rerank，而不是让 answer model 自己从更多 raw rows 中归纳。
- multi-session 仍需关注：v11 为 51/133，高于 v7 的 49/133 但远低于 v10 的 58/133，说明 compact evidence 有局部价值，但缺少可靠选择机制。
- 保持 6K query token 约束。v11 证明 selective snippet 可以降低成本，后续方法应在此成本水平内做更精确的 evidence selection。
- 若引入 rerank/verifier，必须只使用 question text、raw evidence、build memory 和 visible metadata，不能读取 judge output、question_type、sample id 或样本级反馈。

## Offline Metrics

- DeepSeek judge accuracy: 297/500 = 0.594
- invalid judgments: 0
- evidence_recall: 0.978
- avg_build_tokens: 0.0
- avg_query_tokens: 5824.768
- judge_tokens: prompt=78066, completion=36157, total=114223
- build_cache: hits=3341, misses=0, writes=0
- answer_max_input_tokens: 131072
- answer_max_output_tokens: 16384
