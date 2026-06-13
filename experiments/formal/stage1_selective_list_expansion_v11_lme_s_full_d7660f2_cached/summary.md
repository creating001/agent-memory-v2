# formal/stage1_selective_list_expansion_v11_lme_s_full_d7660f2_cached

## Purpose

Stage-1 clean skeleton run: validate raw evidence storage, lexical retrieval, neighbor expansion, evidence compilation, answer generation, trace output, and experiment bookkeeping.

## Scope

- benchmark: longmemeval_s
- subset: full
- experiment_kind: formal
- limit: None
- workers: 8
- input_path: /data/home_new/wujinqi/agent-memory/outputs/prepare_longmemeval_s_cleaned/prediction_input.jsonl
- config_path: /data/home_new/wujinqi/agent-memory/configs/stage1_selective_list_expansion_v11_cached.json
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0.0, max_input_tokens 131072, and max_output_tokens 16384.

## Git

- inside_work_tree: True
- commit: d7660f21755e8060b941555499b1f6c28a3b9475
- dirty: False
- note: None

## Metrics

- n_samples: 500
- accuracy: None
- f1: None
- bleu: None
- avg_build_tokens: 0.0
- avg_query_tokens: 5824.768
- avg_compiled_evidence_items: 15.498
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
- avg_context_chars: 20844.396
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
- route_overrides: {'list_count': {'max_evidence_items': 24, 'max_evidence_chars': 15000, 'row_text_mode': 'role_query_snippet', 'max_row_text_chars': 500, 'evidence_row_labels': False, 'final_answer_checklist': False}}
- enable_broad_list_patterns: False
- enable_recommendation_profile_patterns: True
- temporal_priority_over_recent: False

## Outputs

- predictions: /data/home_new/wujinqi/agent-memory/outputs/formal/stage1_selective_list_expansion_v11_lme_s_full_d7660f2_cached/predictions.jsonl
- traces: /data/home_new/wujinqi/agent-memory/outputs/formal/stage1_selective_list_expansion_v11_lme_s_full_d7660f2_cached/traces.jsonl
- metrics: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_selective_list_expansion_v11_lme_s_full_d7660f2_cached/metrics.json
- manifest: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_selective_list_expansion_v11_lme_s_full_d7660f2_cached/manifest.json

## Clean Notes

- No gold/reference/target answer, judge output, benchmark label, sample id, qid, or row index is passed into the prediction pipeline.
- Build-stage typed memory is generated only from raw dialogue and visible metadata; it is recorded separately from offline labels and judge outputs.
- Raw context remains available for fallback and diagnosis; build memory records keep source back-links when produced by the current builder.
- Accuracy is intentionally not computed by the prediction runner; any gold or judge metrics must be produced offline after prediction.

## Offline Evaluation

- DeepSeek judge accuracy: 297/500 = 0.594
- invalid judgments: 0
- evidence_recall: 0.978
- judge_tokens: prompt=78066, completion=36157, total=114223
- answer_tokens: avg_build=0.0, avg_query=5824.768
- budget_status: mainline-budget-ok，avg_query_tokens 低于 6K 主线目标
- build_cache: hits=3341, misses=0, writes=0
- outputs: predictions=see Outputs section above, judge=/data/home_new/wujinqi/agent-memory/experiments/formal/stage1_selective_list_expansion_v11_lme_s_full_d7660f2_cached/deepseek_judge.json, evidence=/data/home_new/wujinqi/agent-memory/experiments/formal/stage1_selective_list_expansion_v11_lme_s_full_d7660f2_cached/evidence_recall.json

### Accuracy By Question Type

- knowledge-update: 56/78 = 0.717949
- multi-session: 51/133 = 0.383459
- single-session-assistant: 46/56 = 0.821429
- single-session-preference: 10/30 = 0.333333
- single-session-user: 60/70 = 0.857143
- temporal-reasoning: 74/133 = 0.556391

### Accuracy By Route

- current_state: 12/22 = 0.545455
- fact_lookup: 129/183 = 0.704918
- list_count: 61/119 = 0.512605
- profile_preference: 6/15 = 0.400000
- temporal_lookup: 89/161 = 0.552795

### Comparison

- vs v4_temporal_preference: delta_accuracy=-0.002000, net_correct=-1 (plus=18, minus=19)
- vs v7_memory_validity: delta_accuracy=-0.012000, net_correct=-6 (plus=11, minus=17)
- vs v10_compact_evidence: delta_accuracy=0.004000, net_correct=2 (plus=26, minus=24)

### Method Notes

v11 是 clean 的 query-side selective expansion 消融：默认保持 v7 compiler，只对 question-text router 得到的通用 `list_count` information need 覆盖 evidence budget 和 row_text_mode。这个设计借鉴 `docs/method.md` 的 evidence-first/query-time compiler 和 Mnemis/SimpleMem 的聚合覆盖与 token-density 思路，但没有使用 gold、judge、benchmark 标签、sample id 或样本级规则。

### Conclusion

v11 成本达标：avg_query_tokens=5824.768，低于 v7 的 5858.762 和 6K 主线目标；但 DeepSeek judge accuracy 只有 0.594，低于 v7/v6 的 0.606 和 v4 的 0.596。关键失败点是 list_count 没有按预期提升，反而从 v7 的 63/119 降到 61/119。该结果说明受限 snippet 扩展会压缩成本，但丢失了部分完整 raw context 的可用性，不应作为主线。后续不应继续只调 evidence 行数，而应考虑更可靠的 build-stage list/event aggregation 或轻量 query-time rerank。
