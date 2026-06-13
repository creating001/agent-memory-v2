# Diagnosis for stage1_source_expansion_v12_lme_s_full_9ad6e03

## Summary

v12 在 LongMemEval-S full 上达到 357/500 = 0.714 DeepSeek judge accuracy，高于 clean naive RAG top-40 的 0.688。token gate 通过：avg_build_tokens 80346.246，avg_query_tokens 4303.392。

该结果说明 build-stage typed memory 作为 raw source expansion 是正向的，但不是最终方案。evidence recall 已经达到 1.0，剩余错误更多来自答案阶段对多证据、更新事实、时间关系和偏好信息的组织与选择。

## Observations

- samples_processed: 500
- avg_compiled_evidence_items: 35.318
- avg_build_tokens: 80346.246
- build_token_accounting: logical cold-build LLM tokens; cached build chunks count from stored usage, while cache hits only avoid repeated local API calls.
- avg_build_memory_records: 129.662
- avg_active_build_memory_records: 116.492
- build_memory_cache_hits: 3341
- build_memory_cache_misses: 0
- build_memory_cache_writes: 0
- avg_memory_hits: 8.208
- avg_memory_source_hits: 7.894
- build_memory_include_superseded: False
- build_memory_include_superseded_information_needs: ['temporal_lookup', 'list_count']
- avg_context_chars: 15010.518
- avg_query_tokens: 4303.392
- dense_protect_top_n: 32
- session_bm25_enabled: False
- session_bm25_top_k: None
- session_anchor_top_k: None
- session_enabled_route_signals: None
- session_bm25_applied_count: 0
- session_bm25_applied_rate: 0.0
- embedding_cache_enabled: True
- embedding_cache_hits: 247238
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
- temporal_workpad: False
- temporal_text_normalization: False
- temporal_workpad_scope: route
- temporal_workpad_max_rows: 10
- temporal_workpad_max_pairs: 12
- route_overrides: {}
- enable_recommendation_profile_patterns: False
- temporal_priority_over_recent: False
- answer_max_input_tokens: 131072
- answer_max_output_tokens: 16384
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0, max_input_tokens 131072, and max_output_tokens 16384.

## Judge Diagnosis

- accuracy: 357/500 = 0.714
- evidence_recall: 500/500 = 1.0
- vs_naive_external_top40: v12-only 32, naive-only 19, net +13
- positive_delta: multi-session net +10; knowledge-update net +4
- negative_delta: temporal-reasoning net -2; single-session-preference net -1
- main_risk: context 已覆盖证据，但 answer/compiler 没有稳定抽取最终答案，尤其偏好题和时间/更新冲突题。
- dirty_note: prediction manifest 记录 commit 9ad6e03 且 dirty False；后续 judge/diagnosis 的 git dirty 来自 untracked experiment artifacts，不代表 prediction pipeline 有未提交代码改动。

## Next Steps

- 设计下一版时优先研究 general 的 memory-aware compiler/answer strategy：让 build memory 帮助定位主题、实体、时间线和冲突候选，但最终仍回到 raw evidence。
- 不优先扩大 top-k 或 context token；当前 evidence recall 已满，继续堆 context 很可能浪费 query budget。
- preference 和 temporal 改动必须保持 benchmark-agnostic，不使用 question_type/category/sample id/judge feedback。
