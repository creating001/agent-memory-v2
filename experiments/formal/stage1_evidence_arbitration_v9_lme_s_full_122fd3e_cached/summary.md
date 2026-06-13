# formal/stage1_evidence_arbitration_v9_lme_s_full_122fd3e_cached

## Purpose

Stage-1 clean skeleton run: validate raw evidence storage, lexical retrieval, neighbor expansion, evidence compilation, answer generation, trace output, and experiment bookkeeping.

## Scope

- benchmark: longmemeval_s
- subset: full
- experiment_kind: formal
- limit: None
- workers: 4
- input_path: /data/home_new/wujinqi/agent-memory/outputs/prepare_longmemeval_s_cleaned/prediction_input.jsonl
- config_path: /data/home_new/wujinqi/agent-memory/configs/stage1_evidence_arbitration_v9_cached.json
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0.0, max_input_tokens 131072, and max_output_tokens 16384.

## Git

- inside_work_tree: True
- commit: 122fd3ec75f67ea01bf603a84dd052ffcb96e981
- dirty: False
- note: None

## Metrics

- n_samples: 500
- accuracy: None
- f1: None
- bleu: None
- avg_build_tokens: 0.0
- avg_query_tokens: 6744.762
- avg_compiled_evidence_items: 26.642
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
- avg_context_chars: 22383.794
- answer_mode: openai_compatible
- answer_model: Qwen/Qwen3-30B-A3B-Instruct-2507
- answer_max_input_tokens: 131072
- answer_max_output_tokens: 16384
- answer_style: concise
- evidence_order: question_overlap
- memory_order: question_overlap
- memory_layout: typed_sections
- row_text_mode: role_query_snippet
- max_row_text_chars: 700
- evidence_row_labels: True
- final_answer_checklist: True
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

- predictions: /data/home_new/wujinqi/agent-memory/outputs/formal/stage1_evidence_arbitration_v9_lme_s_full_122fd3e_cached/predictions.jsonl
- traces: /data/home_new/wujinqi/agent-memory/outputs/formal/stage1_evidence_arbitration_v9_lme_s_full_122fd3e_cached/traces.jsonl
- metrics: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_evidence_arbitration_v9_lme_s_full_122fd3e_cached/metrics.json
- manifest: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_evidence_arbitration_v9_lme_s_full_122fd3e_cached/manifest.json

## Clean Notes

- No gold/reference/target answer, judge output, benchmark label, sample id, qid, or row index is passed into the prediction pipeline.
- Build-stage typed memory is generated only from raw dialogue and visible metadata; it is recorded separately from offline labels and judge outputs.
- Raw context remains available for fallback and diagnosis; build memory records keep source back-links when produced by the current builder.
- Accuracy is intentionally not computed by the prediction runner; any gold or judge metrics must be produced offline after prediction.

## Offline Evaluation

- DeepSeek judge accuracy: 291/500 = 0.582
- invalid judgments: 0
- evidence_recall: 0.996
- judge_tokens: prompt=91933, completion=41940, total=133873
- answer_tokens: avg_build=0.0, avg_query=6744.762
- budget_warning: avg_query_tokens 超过 6K 目标；88 条 total tokens > 8K；max_completion_tokens=16384。
- build_cache: hits=3341, misses=0, writes=0
- outputs: predictions=/data/home_new/wujinqi/agent-memory/outputs/formal/stage1_evidence_arbitration_v9_lme_s_full_122fd3e_cached/predictions.jsonl, judge=/data/home_new/wujinqi/agent-memory/experiments/formal/stage1_evidence_arbitration_v9_lme_s_full_122fd3e_cached/deepseek_judge.json, evidence=/data/home_new/wujinqi/agent-memory/experiments/formal/stage1_evidence_arbitration_v9_lme_s_full_122fd3e_cached/evidence_recall.json

### Accuracy By Question Type

- knowledge-update: 55/78 = 0.705128
- multi-session: 56/133 = 0.421053
- single-session-assistant: 43/56 = 0.767857
- single-session-preference: 6/30 = 0.200000
- single-session-user: 59/70 = 0.842857
- temporal-reasoning: 72/133 = 0.541353

### Accuracy By Route

- current_state: 10/22 = 0.454545
- fact_lookup: 128/183 = 0.699454
- list_count: 61/119 = 0.512605
- profile_preference: 6/15 = 0.400000
- temporal_lookup: 86/161 = 0.534161

### Comparison

- vs v6_route_priority: delta_accuracy=-0.024000, net_correct=-12 (plus=30, minus=42)
- vs v7_memory_validity: delta_accuracy=-0.024000, net_correct=-12 (plus=26, minus=38)
- vs v8_route_validity: delta_accuracy=-0.018000, net_correct=-9 (plus=28, minus=37)

### Conclusion

v9 的 role-aware snippets、证据行标号和末尾 checklist 没有带来整体收益：accuracy 0.582，低于 v6/v7 的 0.606。唯一明显正向是 multi-session 提升到 56/133，但 single-session-assistant、preference、user 和 temporal 均退化。同时 avg_query_tokens=6744.762，超过 6K 目标，且出现 max_completion_tokens=16384 的长输出。该版本只作为 budget-warning diagnostic，不进入主线；下一步若继续利用该思路，应做 route-specific/compact v9.1，只保留 multi-session/list 受益部分并强约束输出长度。
