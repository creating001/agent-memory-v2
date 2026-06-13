# Diagnosis for stage1_source_expansion_v12_locomo_nonadv_full_3235553

## Summary

v12 在 LoCoMo non-adversarial full 上达到 1076/1540 = 0.698701 DeepSeek judge accuracy，基本与 clean naive RAG top-40 的 1075/1540 持平。token gate 通过：avg_build_tokens 58386.008，avg_query_tokens 2729.447。

该结果说明 source expansion 在 LoCoMo 上没有形成整体突破。它对 category 4 有净收益，但在 category 2 上明显回退，下一步必须围绕时间/跨事件关系的证据组织和答案策略做 general 改进。

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
- avg_context_chars: 8583.171428571428
- avg_query_tokens: 2729.4474025974027
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

- accuracy: 1076/1540 = 0.698701
- evidence_recall: 1339/1536 = 0.871745
- vs_naive_external_top40: v12-only 76, naive-only 75, net +1
- positive_delta: category 4 net +7; category 1 net +3; category 3 net +1
- negative_delta: category 2 net -10
- main_risk: build memory expansion 带来更多候选证据，但 category 2 需要更稳定的时间锚点、事件顺序和跨证据聚合；当前 compiler 仍是 naive-style flat evidence。
- dirty_note: prediction manifest dirty True 的原因是已有 LME experiment artifacts 未跟踪；没有未提交代码 diff 参与 prediction。

## Next Steps

- 对 LoCoMo 下一版优先研究 general temporal/event compiler，而不是扩大 top-k。
- 需要从外部代码库继续看 Graphiti/Zep/SimpleMem 类 temporal/event organization 的实现细节，再决定轻量化迁移方式。
- category 2 的改动不能读取 category label，只能依赖 question text、question time、raw dialogue、build memory 和 clean trace。
