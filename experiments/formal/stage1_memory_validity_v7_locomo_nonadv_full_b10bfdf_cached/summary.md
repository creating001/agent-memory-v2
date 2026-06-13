# formal/stage1_memory_validity_v7_locomo_nonadv_full_b10bfdf_cached

## Purpose

Stage-1 clean skeleton run: validate raw evidence storage, lexical retrieval, neighbor expansion, evidence compilation, answer generation, trace output, and experiment bookkeeping.

## Scope

- benchmark: locomo
- subset: non-adversarial-full
- experiment_kind: formal
- limit: None
- workers: 8
- input_path: /data/home_new/wujinqi/agent-memory/outputs/prepare_locomo_non_adversarial/prediction_input.jsonl
- config_path: /data/home_new/wujinqi/agent-memory/configs/stage1_memory_validity_v7_cached.json
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0.0, max_input_tokens 131072, and max_output_tokens 16384.

## Git

- inside_work_tree: True
- commit: b10bfdf5e5ba96eaeefa5a84b653edefcfe8a43d
- dirty: False
- note: None

## Metrics

- n_samples: 1540
- accuracy: None
- f1: None
- bleu: None
- avg_build_tokens: 0.0
- avg_query_tokens: 4715.416883116883
- avg_compiled_evidence_items: 33.044155844155846
- build_memory_enabled: True
- build_memory_model: Qwen/Qwen3-30B-A3B-Instruct-2507
- build_memory_cache_enabled: True
- build_memory_cache_path: outputs/cache/qwen3_build_memory.sqlite
- build_memory_cache_hits: 12411
- build_memory_cache_misses: 0
- build_memory_cache_writes: 0
- avg_build_memory_records: 136.65974025974026
- avg_active_build_memory_records: 125.21103896103897
- avg_memory_hits: 19.84155844155844
- avg_memory_source_hits: 22.381168831168832
- build_memory_include_superseded: False
- build_memory_include_superseded_information_needs: ['temporal_lookup', 'list_count']
- neighbor_order: hit_priority
- drop_query_stopwords: True
- dense_enabled: True
- lexical_protect_top_n: 2
- embedding_cache_enabled: True
- embedding_cache_path: outputs/cache/qwen3_embedding.sqlite
- embedding_cache_hits: 927698
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
- session_bm25_applied_count: 522
- session_bm25_applied_rate: 0.33896103896103896
- avg_embedding_tokens: 0.0
- avg_context_chars: 14577.615584415584
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
- route_overrides: {}
- enable_broad_list_patterns: False
- enable_recommendation_profile_patterns: True
- temporal_priority_over_recent: False

## DeepSeek Judge

- accuracy_valid_only: 1050/1540 = 0.681818
- accuracy_invalid_as_wrong: 1050/1540 = 0.681818
- n_valid: 1540
- n_invalid: 0
- judge_model: deepseek-v4-flash
- judge_prompt_tokens: 497751
- judge_completion_tokens: 157496
- judge_total_tokens: 655247

## DeepSeek Judge By Category

- category 1: 169/282 = 0.599291
- category 2: 130/321 = 0.404984
- category 3: 53/96 = 0.552083
- category 4: 698/841 = 0.829964

## DeepSeek Judge By Route

- current_state: 2/4 = 0.500000
- fact_lookup: 797/1018 = 0.782908
- list_count: 71/131 = 0.541985
- profile_preference: 32/49 = 0.653061
- temporal_lookup: 148/338 = 0.437870

## Evidence Recall

- overall: 0.830729 over 1536 labeled samples
- category 1: 0.734043
- category 2: 0.856698
- category 3: 0.500000
- category 4: 0.889417

## Comparison

- v4 LoCoMo current best accuracy_valid_only: 1071/1539 = 0.695906
- v7 LoCoMo accuracy_valid_only: 1050/1540 = 0.681818
- v7 vs v4: net_correct=-21 (plus=30, minus=51)
- v7 vs v6: net_correct=+1 (plus=43, minus=42)
- interpretation: v7 validity/superseded retrieval does not improve LoCoMo full; it is effectively tied with the negative v6 run and clearly below v4.
- decision: LoCoMo current best remains v4. This build-memory branch should not be extended before a strong clean naive RAG baseline is established.

## Outputs

- predictions: /data/home_new/wujinqi/agent-memory/outputs/formal/stage1_memory_validity_v7_locomo_nonadv_full_b10bfdf_cached/predictions.jsonl
- traces: /data/home_new/wujinqi/agent-memory/outputs/formal/stage1_memory_validity_v7_locomo_nonadv_full_b10bfdf_cached/traces.jsonl
- metrics: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_memory_validity_v7_locomo_nonadv_full_b10bfdf_cached/metrics.json
- manifest: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_memory_validity_v7_locomo_nonadv_full_b10bfdf_cached/manifest.json
- deepseek_judge: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_memory_validity_v7_locomo_nonadv_full_b10bfdf_cached/deepseek_judge.json
- deepseek_judge_partial: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_memory_validity_v7_locomo_nonadv_full_b10bfdf_cached/deepseek_judge.json.partial.jsonl
- offline_evidence_recall: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_memory_validity_v7_locomo_nonadv_full_b10bfdf_cached/evidence_recall.json

## Clean Notes

- No gold/reference/target answer, judge output, benchmark label, sample id, qid, or row index is passed into the prediction pipeline.
- Build-stage typed memory is generated only from raw dialogue and visible metadata; it is recorded separately from offline labels and judge outputs.
- Raw context remains available for fallback and diagnosis; build memory records keep source back-links when produced by the current builder.
- Accuracy is intentionally not computed by the prediction runner; any gold or judge metrics must be produced offline after prediction.
- DeepSeek judge and evidence recall were run offline after predictions were written. Judge labels, gold answers, category, and record_key must not be consumed by prediction, retrieval, compiler, answer, or verifier code.

## Conclusion

v7 在 LoCoMo non-adversarial full 上不是提升：DeepSeek judge accuracy 为 0.681818，低于 v4 的 0.695906，只比已知负向的 v6 多 1 个正确。该结果说明当前 typed build-memory validity 分支不能作为 LoCoMo 主线；下一步应先建立严格 clean 的 naive RAG full baseline，再围绕强 baseline 做 general 的 memory/retrieval 改进。
