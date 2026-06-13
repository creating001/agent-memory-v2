# Diagnosis for stage1_temporal_aid_v13_locomo_nonadv_full_8e8f070

## Summary

v13 在 LoCoMo non-adversarial full 上达到 1111/1540 = 0.721429 DeepSeek judge accuracy，超过 v12 的 0.698701 和 clean naive RAG 的 0.698506。token gate 通过：avg_build_tokens 58386.008，avg_query_tokens 2887.880。

主要收益来自通用 temporal aid：它把 retrieved raw rows 中的 yesterday / last Saturday / N days ago 等相对时间按 row timestamp 归一化，帮助 answer model 不再把发言日期误当事件日期。该模块不读取 category/question_type/gold/judge/sample id，不包含样本实体规则。

## Observations

- samples_processed: 1540
- avg_compiled_evidence_items: 40.0
- avg_build_tokens: 58386.00779220779
- build_token_accounting: logical cold-build LLM tokens; cached build chunks count from stored usage, while cache hits only avoid repeated local API calls.
- avg_build_memory_records: 136.65974025974026
- avg_active_build_memory_records: 125.21103896103897
- build_memory_cache_hits: 12411
- build_memory_cache_misses: 0
- build_memory_cache_writes: 0
- avg_memory_hits: 19.84155844155844
- avg_memory_source_hits: 22.381168831168832
- build_memory_include_superseded: False
- build_memory_include_superseded_information_needs: ['temporal_lookup', 'list_count']
- avg_context_chars: 8992.012987012988
- avg_query_tokens: 2887.87987012987
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
- temporal_workpad_scope: route
- temporal_workpad_max_rows: 12
- temporal_workpad_max_pairs: 12
- route_overrides: {}
- enable_recommendation_profile_patterns: False
- temporal_priority_over_recent: False
- answer_max_input_tokens: 131072
- answer_max_output_tokens: 16384
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0, max_input_tokens 131072, and max_output_tokens 16384.

## Judge Diagnosis

- accuracy: 1111/1540 = 0.721429
- evidence_recall: 1339/1536 = 0.871745
- temporal_aid_prompts: 391/1540 = 0.254
- vs_v12: v13-only 85, v12-only 50, net +35
- vs_naive_external_top40: v13-only 116, naive-only 80, net +36
- positive_delta_vs_v12: category 2 net +44
- negative_delta_vs_v12: category 1 net -2; category 3 net -5; category 4 net -2
- main_risk: temporal aid 明显修复 category 2，但对非 temporal 类有轻微扰动；下一版要更精确地把 temporal aid 作为 evidence table 的一列，而不是继续扩规则。
- retry_note: two empty-content DeepSeek judge responses were retried offline and replaced; prediction outputs were unchanged.

## Next Steps

- 保留 v13 作为当前 LoCoMo 主线。
- 下一步优先实现 general evidence table / event-time column，把 row_date、relative_time、source role、memory source expansion 统一组织，减少 category 1/3/4 回退。
- 不增加 benchmark-specific route 或样本级日期规则；继续只依赖 question text、question time、raw dialogue、built memory 和 clean runtime trace。
