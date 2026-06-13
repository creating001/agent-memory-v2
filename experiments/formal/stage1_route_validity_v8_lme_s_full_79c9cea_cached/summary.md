# formal/stage1_route_validity_v8_lme_s_full_79c9cea_cached

## Purpose

Stage-1 clean skeleton run: validate raw evidence storage, lexical retrieval, neighbor expansion, evidence compilation, answer generation, trace output, and experiment bookkeeping.

## Scope

- benchmark: longmemeval_s
- subset: full
- experiment_kind: formal
- limit: None
- workers: 8
- input_path: /data/home_new/wujinqi/agent-memory/outputs/prepare_longmemeval_s_cleaned/prediction_input.jsonl
- config_path: /data/home_new/wujinqi/agent-memory/configs/stage1_route_validity_v8_cached.json
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0.0, max_input_tokens 131072, and max_output_tokens 16384.

## Git

- inside_work_tree: True
- commit: 79c9ceaad4a4d8cb5f4408b920a32f87d0fce50e
- dirty: False
- note: None

## Metrics

- n_samples: 500
- accuracy: None
- f1: None
- bleu: None
- avg_build_tokens: 0.0
- avg_query_tokens: 5861.396
- avg_compiled_evidence_items: 12.54
- build_memory_enabled: True
- build_memory_model: Qwen/Qwen3-30B-A3B-Instruct-2507
- build_memory_cache_enabled: True
- build_memory_cache_path: outputs/cache/qwen3_build_memory.sqlite
- build_memory_cache_hits: 3341
- build_memory_cache_misses: 0
- build_memory_cache_writes: 0
- avg_build_memory_records: 129.662
- avg_active_build_memory_records: 116.492
- avg_memory_hits: 8.216
- avg_memory_source_hits: 7.904
- build_memory_include_superseded: False
- build_memory_include_superseded_information_needs: ['temporal_lookup', 'list_count']
- neighbor_order: hit_priority
- drop_query_stopwords: True
- dense_enabled: True
- lexical_protect_top_n: 2
- embedding_cache_enabled: True
- embedding_cache_path: outputs/cache/qwen3_embedding.sqlite
- embedding_cache_hits: 247238
- embedding_cache_misses: 0
- embedding_cache_writes: 0
- session_bm25_enabled: True
- session_bm25_top_k: 8
- session_anchor_top_k: 2
- session_max_anchor_hits: 12
- session_protect_turn_hits: 4
- session_enabled_route_signals: ['temporal', 'recent_or_current']
- session_enabled_information_needs: None
- session_enabled_query_patterns: ['\\b20\\d{2}\\b', '\\b(?:january|february|march|april|june|july|august|september|october|november|december)\\b', '\\bmay\\s+20\\d{2}\\b']
- session_bm25_applied_count: 193
- session_bm25_applied_rate: 0.386
- avg_embedding_tokens: 0.0
- avg_context_chars: 21673.738
- answer_mode: openai_compatible
- answer_model: Qwen/Qwen3-30B-A3B-Instruct-2507
- answer_max_input_tokens: 131072
- answer_max_output_tokens: 16384
- answer_style: concise
- evidence_order: question_overlap
- memory_order: question_overlap
- memory_layout: typed_sections
- row_text_mode: full
- max_row_text_chars: 0
- max_memory_records: 16
- route_guidance: True
- temporal_grounding: True
- temporal_hints: True
- temporal_workpad: True
- temporal_text_normalization: False
- temporal_workpad_scope: route
- temporal_workpad_max_rows: 10
- temporal_workpad_max_pairs: 12
- enable_broad_list_patterns: False
- enable_recommendation_profile_patterns: True
- temporal_priority_over_recent: True

## Outputs

- predictions: /data/home_new/wujinqi/agent-memory/outputs/formal/stage1_route_validity_v8_lme_s_full_79c9cea_cached/predictions.jsonl
- traces: /data/home_new/wujinqi/agent-memory/outputs/formal/stage1_route_validity_v8_lme_s_full_79c9cea_cached/traces.jsonl
- metrics: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_route_validity_v8_lme_s_full_79c9cea_cached/metrics.json
- manifest: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_route_validity_v8_lme_s_full_79c9cea_cached/manifest.json

## Clean Notes

- No gold/reference/target answer, judge output, benchmark label, sample id, qid, or row index is passed into the prediction pipeline.
- Build-stage typed memory is generated only from raw dialogue and visible metadata; it is recorded separately from offline labels and judge outputs.
- Raw context remains available for fallback and diagnosis; build memory records keep source back-links when produced by the current builder.
- Accuracy is intentionally not computed by the prediction runner; any gold or judge metrics must be produced offline after prediction.

## Offline Evaluation

- DeepSeek judge accuracy: 300/500 = 0.600
- invalid judgments: 0
- evidence_recall: 0.978
- judge_tokens: prompt=78053, completion=38523, total=116576
- answer_tokens: avg_build=0.0, avg_query=5861.396
- build_cache: hits=3341, misses=0, writes=0
- outputs: predictions=/data/home_new/wujinqi/agent-memory/outputs/formal/stage1_route_validity_v8_lme_s_full_79c9cea_cached/predictions.jsonl, judge=/data/home_new/wujinqi/agent-memory/experiments/formal/stage1_route_validity_v8_lme_s_full_79c9cea_cached/deepseek_judge.json, evidence=/data/home_new/wujinqi/agent-memory/experiments/formal/stage1_route_validity_v8_lme_s_full_79c9cea_cached/evidence_recall.json

### Accuracy By Question Type

- knowledge-update: 57/78 = 0.730769
- multi-session: 50/133 = 0.375940
- single-session-assistant: 50/56 = 0.892857
- single-session-preference: 9/30 = 0.300000
- single-session-user: 62/70 = 0.885714
- temporal-reasoning: 72/133 = 0.541353

### Accuracy By Route

- current_state: 9/13 = 0.692308
- fact_lookup: 129/183 = 0.704918
- list_count: 64/119 = 0.537815
- profile_preference: 6/15 = 0.400000
- temporal_lookup: 92/170 = 0.541176

### Comparison

- vs v4_temporal_preference: delta_accuracy=0.004000, net_correct=2 (plus=18, minus=16)
- vs v6_route_priority: delta_accuracy=-0.006000, net_correct=-3 (plus=13, minus=16)
- vs v7_memory_validity: delta_accuracy=-0.006000, net_correct=-3 (plus=7, minus=10)

### Conclusion

v8 将 v6 route priority 与 v7 validity/superseded retrieval 合并，但 LME full accuracy 只有 0.600，低于 v6/v7 的 0.606。损失主要来自 temporal-reasoning：v8 为 72/133，低于 v6 的 78/133 和 v7 的 74/133。该组合不是互补改动，不进入主线，也不继续跑 LoCoMo full。下一步应回到方法层面分析 badcase，优先设计更稳健的 build-stage memory 管理和 query-side evidence arbitration，而不是继续叠加路由开关。
