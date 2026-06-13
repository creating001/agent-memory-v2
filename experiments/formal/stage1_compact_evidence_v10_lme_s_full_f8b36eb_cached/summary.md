# formal/stage1_compact_evidence_v10_lme_s_full_f8b36eb_cached

## Purpose

Stage-1 clean skeleton run: validate raw evidence storage, lexical retrieval, neighbor expansion, evidence compilation, answer generation, trace output, and experiment bookkeeping.

## Scope

- benchmark: longmemeval_s
- subset: full
- experiment_kind: formal
- limit: None
- workers: 8
- input_path: /data/home_new/wujinqi/agent-memory/outputs/prepare_longmemeval_s_cleaned/prediction_input.jsonl
- config_path: /data/home_new/wujinqi/agent-memory/configs/stage1_compact_evidence_v10_cached.json
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0.0, max_input_tokens 131072, and max_output_tokens 16384.

## Git

- inside_work_tree: True
- commit: f8b36eb3749285ef88fe5df4723462d774efe586
- dirty: False
- note: None

## Metrics

- n_samples: 500
- accuracy: None
- f1: None
- bleu: None
- avg_build_tokens: 0.0
- avg_query_tokens: 6519.668
- avg_compiled_evidence_items: 30.622
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
- avg_context_chars: 20901.034
- answer_mode: openai_compatible
- answer_model: Qwen/Qwen3-30B-A3B-Instruct-2507
- answer_max_input_tokens: 131072
- answer_max_output_tokens: 16384
- answer_style: concise
- evidence_order: question_overlap
- memory_order: question_overlap
- memory_layout: typed_sections
- row_text_mode: role_query_snippet
- max_row_text_chars: 500
- evidence_row_labels: False
- final_answer_checklist: False
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

- predictions: /data/home_new/wujinqi/agent-memory/outputs/formal/stage1_compact_evidence_v10_lme_s_full_f8b36eb_cached/predictions.jsonl
- traces: /data/home_new/wujinqi/agent-memory/outputs/formal/stage1_compact_evidence_v10_lme_s_full_f8b36eb_cached/traces.jsonl
- metrics: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_compact_evidence_v10_lme_s_full_f8b36eb_cached/metrics.json
- manifest: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_compact_evidence_v10_lme_s_full_f8b36eb_cached/manifest.json

## Clean Notes

- No gold/reference/target answer, judge output, benchmark label, sample id, qid, or row index is passed into the prediction pipeline.
- Build-stage typed memory is generated only from raw dialogue and visible metadata; it is recorded separately from offline labels and judge outputs.
- Raw context remains available for fallback and diagnosis; build memory records keep source back-links when produced by the current builder.
- Accuracy is intentionally not computed by the prediction runner; any gold or judge metrics must be produced offline after prediction.

## Offline Evaluation

- DeepSeek judge accuracy: 295/500 = 0.590
- invalid judgments: 0
- evidence_recall: 0.998
- judge_tokens: prompt=77701, completion=37832, total=115533
- answer_tokens: avg_build=0.0, avg_query=6519.668
- budget_status: budget-warning，avg_query_tokens 超过 6K 主线目标但低于 8K diagnostic 上限
- build_cache: hits=3341, misses=0, writes=0
- outputs: predictions=see Outputs section above, judge=/data/home_new/wujinqi/agent-memory/experiments/formal/stage1_compact_evidence_v10_lme_s_full_f8b36eb_cached/deepseek_judge.json, evidence=/data/home_new/wujinqi/agent-memory/experiments/formal/stage1_compact_evidence_v10_lme_s_full_f8b36eb_cached/evidence_recall.json

### Accuracy By Question Type

- knowledge-update: 56/78 = 0.717949
- multi-session: 58/133 = 0.436090
- single-session-assistant: 41/56 = 0.732143
- single-session-preference: 6/30 = 0.200000
- single-session-user: 62/70 = 0.885714
- temporal-reasoning: 72/133 = 0.541353

### Accuracy By Route

- current_state: 11/22 = 0.500000
- fact_lookup: 130/183 = 0.710383
- list_count: 67/119 = 0.563025
- profile_preference: 2/15 = 0.133333
- temporal_lookup: 85/161 = 0.527950

### Comparison

- vs v4_temporal_preference: delta_accuracy=-0.006000, net_correct=-3 (plus=28, minus=31)
- vs v7_memory_validity: delta_accuracy=-0.016000, net_correct=-8 (plus=21, minus=29)
- vs v9_evidence_arbitration: delta_accuracy=0.008000, net_correct=4 (plus=26, minus=22)

### Method Notes

v10 是 clean 的 query-side compact evidence 消融，基于 v7 memory validity，不改变 build cache。它借鉴 `docs/method.md` 推荐的 evidence-first、multi-view retrieval 和 query-time compiler 思路，并吸收 v9 诊断中 multi-session 正向信号；具体取舍是保留 role-aware snippet 和更多 evidence row，但关闭 v9 的 evidence row labels / final answer checklist，避免 checklist 拉高输出成本。

### Conclusion

v10 将 evidence_recall 提到 0.998，multi-session 从 v7 的 49/133 提到 58/133，但整体 DeepSeek judge accuracy 只有 0.590，低于 v7/v6 的 0.606 和 v4 的 0.596；同时 avg_query_tokens=6519.668，超过 6K 主线预算。该结果说明“更多紧凑 evidence”提升了覆盖，却让 answer model 在 assistant、preference、temporal 等题型中更容易被噪声干扰。v10 不进入主线，只作为后续 multi-session/list_count 的局部线索；下一步应优先做更精确的 evidence selection 或 query-time rerank，而不是继续扩大上下文。
