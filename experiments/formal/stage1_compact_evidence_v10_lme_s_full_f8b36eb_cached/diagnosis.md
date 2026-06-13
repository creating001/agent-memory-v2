# Diagnosis for formal/stage1_compact_evidence_v10_lme_s_full_f8b36eb_cached

## Summary

v10 是一个 clean 的 query-side compact evidence 消融：复用 v7 的 build-stage typed memory 和 validity/superseded retrieval，只改变 compiler 的证据组织。DeepSeek judge accuracy 为 0.590（295/500），低于 v6/v7 的 0.606；avg_query_tokens=6519.668，超过 6K 主线目标，因此标为 budget-warning diagnostic，不进入主线。

## Observations

- samples_processed: 500
- avg_compiled_evidence_items: 30.622
- avg_build_memory_records: 129.662
- avg_active_build_memory_records: 116.492
- build_memory_cache_hits: 3341
- build_memory_cache_misses: 0
- build_memory_cache_writes: 0
- avg_memory_hits: 8.208
- avg_memory_source_hits: 7.894
- build_memory_include_superseded: False
- build_memory_include_superseded_information_needs: ['temporal_lookup', 'list_count']
- avg_context_chars: 20901.034
- avg_query_tokens: 6519.668
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
- row_text_mode: role_query_snippet
- max_row_text_chars: 500
- evidence_row_labels: False
- final_answer_checklist: False
- max_memory_records: 16
- route_guidance: True
- temporal_workpad: True
- temporal_text_normalization: False
- temporal_workpad_scope: route
- temporal_workpad_max_rows: 10
- temporal_workpad_max_pairs: 12
- enable_recommendation_profile_patterns: True
- temporal_priority_over_recent: False
- answer_max_input_tokens: 131072
- answer_max_output_tokens: 16384
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0.0, max_input_tokens 131072, and max_output_tokens 16384.

## Next Steps

- 不要继续沿着“单纯增加 evidence row / context 宽度”的方向加码；v10 的 evidence_recall=0.998，但 accuracy 下降，说明主要瓶颈已经从召回转向证据选择和答案阶段抗噪。
- multi-session 是唯一明确正向信号：v10 为 58/133，高于 v7 的 49/133 和 v9 的 56/133。后续可以做更窄的 multi-view selection / rerank，但必须由 question text 和 memory metadata 驱动，不能使用 question_type、sample id、gold 或 judge feedback。
- assistant、preference、temporal 都出现退化：single-session-assistant 41/56，single-session-preference 6/30，temporal-reasoning 72/133。下一步需要分析这些类型的 wrong-to-correct / correct-to-wrong 样例，找通用错误机制，如 wrong speaker、stale fact、profile/event 混淆和 temporal conflict，而不是写样本规则。
- 若继续做 query-side 改进，应先控制 avg_query_tokens 回到 6K 内；超过 6K 的实验必须继续标为 budget-warning，不作为主线结果。
- build-stage 方向仍重要：当前 best 的 v7 validity 说明 memory management 有正向价值。下一阶段更值得做的是 build-time profile/event/state 分离、conflict chain 与更可靠的 valid_from/valid_to 管理，而不是扩大 answer context。

## Offline Metrics

- DeepSeek judge accuracy: 295/500 = 0.590
- invalid judgments: 0
- evidence_recall: 0.998
- avg_build_tokens: 0.0
- avg_query_tokens: 6519.668
- judge_tokens: prompt=77701, completion=37832, total=115533
- build_cache: hits=3341, misses=0, writes=0
- answer_max_input_tokens: 131072
- answer_max_output_tokens: 16384
