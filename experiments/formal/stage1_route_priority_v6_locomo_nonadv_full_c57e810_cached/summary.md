# formal/stage1_route_priority_v6_locomo_nonadv_full_c57e810_cached

## Purpose

Stage-1 clean skeleton run: validate raw evidence storage, lexical retrieval, neighbor expansion, evidence compilation, answer generation, trace output, and experiment bookkeeping.

## Scope

- benchmark: locomo
- subset: non-adversarial
- experiment_kind: formal
- limit: None
- workers: 8
- input_path: /data/home_new/wujinqi/agent-memory/outputs/prepare_locomo_non_adversarial/prediction_input.jsonl
- config_path: /data/home_new/wujinqi/agent-memory/configs/stage1_route_priority_v6_cached.json
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0.0 and max_tokens 16384.

## Git

- inside_work_tree: True
- commit: c57e8103b683e163d71f7d71211c9f1874e496b2
- dirty: False
- note: None

## Metrics

- n_samples: 1540
- accuracy: None
- f1: None
- bleu: None
- avg_build_tokens: 0.0
- avg_query_tokens: 4419.401298701298
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
- avg_memory_hits: 19.835064935064935
- avg_memory_source_hits: 22.58051948051948
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
- avg_context_chars: 13917.034415584416
- answer_mode: openai_compatible
- answer_model: Qwen/Qwen3-30B-A3B-Instruct-2507
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

## DeepSeek Judge

- accuracy_valid_only: 1049/1539 = 0.681611
- accuracy_invalid_as_wrong: 1049/1540 = 0.681169
- n_valid: 1539
- n_invalid: 1
- judge_model: deepseek-v4-flash
- judge_prompt_tokens: 497156
- judge_completion_tokens: 158459
- judge_total_tokens: 655615

## DeepSeek Judge By Category

- category 1: 169/282 = 0.599291
- category 2: 129/321 = 0.401869
- category 3: 52/96 = 0.541667
- category 4: 699/840 = 0.832143, invalid 1

## DeepSeek Judge By Route

- current_state: 1/3 = 0.333333
- fact_lookup: 804/1017 = 0.790560, invalid 1
- list_count: 67/131 = 0.511450
- profile_preference: 33/49 = 0.673469
- temporal_lookup: 144/339 = 0.424779

## Evidence Recall

- overall: 0.830078 over 1536 labeled samples
- category 1: 0.737589
- category 2: 0.856698
- category 3: 0.500000
- category 4: 0.887039

## Comparison

- v4 LoCoMo accuracy_valid_only: 0.695906
- v6 LoCoMo accuracy_valid_only: 0.681611
- v6 vs v4: -22 valid correct
- route changes vs v4: 1 sample, correct in both v4 and v6
- interpretation: v6 route priority is useful for LME but does not transfer to LoCoMo; the LoCoMo change is effectively a negative full-run validation.
- decision: LoCoMo current best remains v4.

## Outputs

- predictions: /data/home_new/wujinqi/agent-memory/outputs/formal/stage1_route_priority_v6_locomo_nonadv_full_c57e810_cached/predictions.jsonl
- traces: /data/home_new/wujinqi/agent-memory/outputs/formal/stage1_route_priority_v6_locomo_nonadv_full_c57e810_cached/traces.jsonl
- metrics: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_route_priority_v6_locomo_nonadv_full_c57e810_cached/metrics.json
- manifest: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_route_priority_v6_locomo_nonadv_full_c57e810_cached/manifest.json
- deepseek_judge: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_route_priority_v6_locomo_nonadv_full_c57e810_cached/deepseek_judge.json
- deepseek_judge_partial: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_route_priority_v6_locomo_nonadv_full_c57e810_cached/deepseek_judge.json.partial.jsonl
- offline_evidence_recall: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_route_priority_v6_locomo_nonadv_full_c57e810_cached/evidence_recall.json

## Clean Notes

- No gold/reference/target answer, judge output, benchmark label, sample id, qid, or row index is passed into the prediction pipeline.
- Build-stage typed memory is generated only from raw dialogue and visible metadata; it is recorded separately from offline labels and judge outputs.
- Raw context remains available for fallback and diagnosis; build memory records keep source back-links when produced by the current builder.
- Accuracy is intentionally not computed by the prediction runner; any gold or judge metrics must be produced offline after prediction.
- DeepSeek judge and evidence recall were run offline after predictions were written. Judge labels, gold answers, category, and record_key must not be consumed by prediction, retrieval, compiler, answer, or verifier code.

## Conclusion

v6 is not a LoCoMo improvement. The route-priority change only changes one LoCoMo route and that sample was already correct in v4, while the full valid accuracy drops from 0.695906 to 0.681611. The next LoCoMo-focused method should address build-stage memory state/list management and evidence organization, not this route priority alone.
