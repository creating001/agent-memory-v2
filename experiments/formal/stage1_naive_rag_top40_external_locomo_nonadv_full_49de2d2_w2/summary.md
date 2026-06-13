# formal/stage1_naive_rag_top40_external_locomo_nonadv_full_49de2d2_w2

## Purpose

Stage-1 clean skeleton run: validate raw evidence storage, lexical retrieval, neighbor expansion, evidence compilation, answer generation, trace output, and experiment bookkeeping.

## Scope

- benchmark: locomo
- subset: non-adversarial-full
- experiment_kind: formal
- limit: None
- workers: 2
- input_path: /data/home_new/wujinqi/agent-memory/outputs/prepare_locomo_non_adversarial/prediction_input.jsonl
- config_path: /data/home_new/wujinqi/agent-memory/configs/stage1_naive_rag_top40_external.json
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0.0, max_input_tokens 131072, and max_output_tokens 16384.

## Git

- inside_work_tree: True
- commit: 49de2d2e9e6eb6cd1eb50d69e651dce3f50aa20d
- dirty: False
- note: None

## Metrics

- n_samples: 1540
- accuracy: None
- f1: None
- bleu: None
- avg_build_tokens: 0.0
- avg_query_tokens: 2650.6435064935067
- avg_compiled_evidence_items: 40.0
- build_memory_enabled: False
- build_memory_model: None
- build_memory_cache_enabled: False
- build_memory_cache_path: None
- build_memory_cache_hits: 0
- build_memory_cache_misses: 0
- build_memory_cache_writes: 0
- avg_build_memory_records: 0.0
- avg_active_build_memory_records: 0.0
- avg_memory_hits: 0.0
- avg_memory_source_hits: 0.0
- build_memory_include_superseded: False
- build_memory_include_superseded_information_needs: None
- neighbor_order: hit_priority
- drop_query_stopwords: False
- lexical_enabled: False
- dense_enabled: True
- lexical_protect_top_n: 0
- dense_document_text_mode: external_naive
- dense_query_text_mode: external_naive
- embedding_cache_enabled: True
- embedding_cache_path: outputs/cache/qwen3_embedding.sqlite
- embedding_cache_hits: 1540
- embedding_cache_misses: 5882
- embedding_cache_writes: 5882
- session_bm25_enabled: False
- session_bm25_top_k: None
- session_anchor_top_k: None
- session_max_anchor_hits: None
- session_protect_turn_hits: None
- session_enabled_route_signals: None
- session_enabled_information_needs: None
- session_enabled_query_patterns: None
- session_bm25_applied_count: 0
- session_bm25_applied_rate: 0.0
- avg_embedding_tokens: 196.98311688311688
- avg_context_chars: 8214.93051948052
- compiler_prompt_mode: external_naive
- answer_mode: openai_compatible
- answer_model: Qwen/Qwen3-30B-A3B-Instruct-2507
- answer_max_input_tokens: 131072
- answer_max_output_tokens: 16384
- answer_output_format: json_answer
- answer_style: concise
- evidence_order: retrieval
- memory_order: retrieval
- memory_layout: flat
- row_text_mode: full
- max_row_text_chars: 0
- evidence_row_labels: False
- final_answer_checklist: False
- max_memory_records: 0
- route_guidance: False
- temporal_grounding: False
- temporal_hints: False
- temporal_workpad: False
- temporal_text_normalization: False
- temporal_workpad_scope: route
- temporal_workpad_max_rows: 10
- temporal_workpad_max_pairs: 12
- route_overrides: {}
- enable_broad_list_patterns: False
- enable_recommendation_profile_patterns: False
- temporal_priority_over_recent: False

## DeepSeek Judge

- accuracy_valid_only: 1075/1539 = 0.698506
- accuracy_invalid_as_wrong: 1075/1540 = 0.698052
- n_valid: 1539
- n_invalid: 1
- judge_model: deepseek-v4-flash
- judge_prompt_tokens: 496353
- judge_completion_tokens: 159077
- judge_total_tokens: 655430

## DeepSeek Judge By Category

- category 1: 183/282 = 0.648936
- category 2: 152/321 = 0.473520
- category 3: 58/96 = 0.604167
- category 4: 682/840 = 0.811905, invalid 1

## DeepSeek Judge By Route

- current_state: 3/4 = 0.750000
- fact_lookup: 788/1017 = 0.774828, invalid 1
- list_count: 69/131 = 0.526718
- profile_preference: 34/49 = 0.693878
- temporal_lookup: 181/338 = 0.535503

## Diagnostic Evidence Recall

- note: evidence recall is diagnostic only; method selection is based on judge accuracy.
- overall: 0.858073 over 1536 labeled samples
- category 1: 0.875887
- category 2: 0.875389
- category 3: 0.641304
- category 4: 0.869203

## Comparison

- v4 LoCoMo previous best: 1071/1539 = 0.695906
- external-aligned naive RAG: 1075/1539 = 0.698506
- vs v4: net_correct=+4 (plus=171, minus=167)
- vs v7 memory validity: net_correct=+25 (plus=185, minus=160)
- interpretation: faithfully reproducing external clean naive RAG details fixes the earlier underestimation and becomes the new LoCoMo best, though the gain over v4 is small.
- decision: LoCoMo baseline to beat is now 0.698506; the earlier pure dense-only 0.555 run was deleted and is not a formal conclusion.

## Outputs

- predictions: /data/home_new/wujinqi/agent-memory/outputs/formal/stage1_naive_rag_top40_external_locomo_nonadv_full_49de2d2_w2/predictions.jsonl
- traces: /data/home_new/wujinqi/agent-memory/outputs/formal/stage1_naive_rag_top40_external_locomo_nonadv_full_49de2d2_w2/traces.jsonl
- metrics: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_naive_rag_top40_external_locomo_nonadv_full_49de2d2_w2/metrics.json
- manifest: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_naive_rag_top40_external_locomo_nonadv_full_49de2d2_w2/manifest.json
- deepseek_judge: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_naive_rag_top40_external_locomo_nonadv_full_49de2d2_w2/deepseek_judge.json
- deepseek_judge_partial: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_naive_rag_top40_external_locomo_nonadv_full_49de2d2_w2/deepseek_judge.json.partial.jsonl
- offline_evidence_recall: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_naive_rag_top40_external_locomo_nonadv_full_49de2d2_w2/evidence_recall.json

## Clean Notes

- No gold/reference/target answer, judge output, benchmark label, sample id, qid, or row index is passed into the prediction pipeline.
- Build-stage typed memory is generated only from raw dialogue and visible metadata; it is recorded separately from offline labels and judge outputs.
- Raw context remains available for fallback and diagnosis; build memory records keep source back-links when produced by the current builder.
- Accuracy is intentionally not computed by the prediction runner; any gold or judge metrics must be produced offline after prediction.
- DeepSeek judge and evidence recall were run offline after predictions were written. Judge labels, gold answers, category, and record_key must not be consumed by prediction, retrieval, compiler, answer, or verifier code.

## Conclusion

External-aligned strict clean naive RAG top-40 reaches 0.698506 LoCoMo non-adversarial full accuracy, slightly above v4. The key correction versus the discarded 0.555 run is faithful alignment with the clean external implementation: Date+role+text document embedding, Current Date+Question query embedding, external-style memory context, and JSON answer extraction. Future LoCoMo methods must beat 0.698506 by adding general memory management on top of this baseline.
