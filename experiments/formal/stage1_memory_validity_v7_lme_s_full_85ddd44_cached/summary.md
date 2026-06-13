# formal/stage1_memory_validity_v7_lme_s_full_85ddd44_cached

## Purpose

Stage-1 clean skeleton run: validate raw evidence storage, lexical retrieval, neighbor expansion, evidence compilation, answer generation, trace output, and experiment bookkeeping.

## Scope

- benchmark: longmemeval_s
- subset: full
- experiment_kind: formal
- limit: None
- workers: 8
- input_path: /data/home_new/wujinqi/agent-memory/outputs/prepare_longmemeval_s_cleaned/prediction_input.jsonl
- config_path: /data/home_new/wujinqi/agent-memory/configs/stage1_memory_validity_v7_cached.json
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0.0, max_input_tokens 131072, and max_output_tokens 16384.

## Git

- inside_work_tree: True
- commit: 85ddd4401b016f5ad798f327ac196629829beae5
- dirty: False
- note: None

## Metrics

- n_samples: 500
- accuracy: None
- f1: None
- bleu: None
- avg_build_tokens: 0.0
- avg_query_tokens: 5858.762
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
- avg_memory_hits: 8.208
- avg_memory_source_hits: 7.894
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
- avg_context_chars: 21665.218
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
- temporal_priority_over_recent: False

## Outputs

- predictions: /data/home_new/wujinqi/agent-memory/outputs/formal/stage1_memory_validity_v7_lme_s_full_85ddd44_cached/predictions.jsonl
- traces: /data/home_new/wujinqi/agent-memory/outputs/formal/stage1_memory_validity_v7_lme_s_full_85ddd44_cached/traces.jsonl
- metrics: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_memory_validity_v7_lme_s_full_85ddd44_cached/metrics.json
- manifest: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_memory_validity_v7_lme_s_full_85ddd44_cached/manifest.json

## Clean Notes

- No gold/reference/target answer, judge output, benchmark label, sample id, qid, or row index is passed into the prediction pipeline.
- Build-stage typed memory is generated only from raw dialogue and visible metadata; it is recorded separately from offline labels and judge outputs.
- Raw context remains available for fallback and diagnosis; build memory records keep source back-links when produced by the current builder.
- Accuracy is intentionally not computed by the prediction runner; any gold or judge metrics must be produced offline after prediction.

## Offline Evaluation

- DeepSeek judge accuracy: 303/500 = 0.606
- invalid judgments: 0
- evidence_recall: 0.978
- judge_tokens: prompt=77997, completion=36386, total=114383
- answer_tokens: avg_build=0.0, avg_query=5858.762
- build_cache: hits=3341, misses=0, writes=0
- outputs: predictions=see Outputs section above, judge=/data/home_new/wujinqi/agent-memory/experiments/formal/stage1_memory_validity_v7_lme_s_full_85ddd44_cached/deepseek_judge.json, evidence=/data/home_new/wujinqi/agent-memory/experiments/formal/stage1_memory_validity_v7_lme_s_full_85ddd44_cached/evidence_recall.json

### Accuracy By Question Type

- knowledge-update: 58/78 = 0.743590
- multi-session: 49/133 = 0.368421
- single-session-assistant: 50/56 = 0.892857
- single-session-preference: 9/30 = 0.300000
- single-session-user: 63/70 = 0.900000
- temporal-reasoning: 74/133 = 0.556391

### Accuracy By Route

- current_state: 12/22 = 0.545455
- fact_lookup: 132/183 = 0.721311
- list_count: 63/119 = 0.529412
- profile_preference: 7/15 = 0.466667
- temporal_lookup: 89/161 = 0.552795

### Comparison

- vs v4_temporal_preference: delta_accuracy=0.010000, net_correct=5 (plus=16, minus=11)
- vs v5_temporal_text: delta_accuracy=0.016000, net_correct=8 (plus=18, minus=10)
- vs v6_route_priority: delta_accuracy=0.000000, net_correct=0 (plus=12, minus=12)

### Conclusion

v7 的 route 保持 v4 默认优先级，只在 temporal_lookup/list_count 下允许检索 superseded typed memory。LME full accuracy 为 0.606，与 v6 route-priority 并列当前最好，较 v4 提升 0.010；但 avg_query_tokens 增至 5858.762，接近 6K 预算。该结果支持 memory validity 管理是 clean 正向消融，但单独使用尚未超过 v6。下一步应先做 v8 组合消融：v6 temporal route priority + v7 validity retrieval，只在 LME full 证明优于 0.606 后再考虑 LoCoMo full，避免浪费全量实验。
