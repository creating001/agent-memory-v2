# stage1_route_budgeted_retrieval_v34_locomo_nonadv_full_fb6c703

## Purpose

Validate v34 route-budgeted retrieval on LoCoMo non-adversarial full.

v34 keeps v33 top-60 retrieval/compile expansion for non-temporal information needs, but uses v29-style top-40 retrieval/compile budget for question-derived `temporal_lookup`. The goal is to keep source coverage gains while reducing temporal context noise.

## Scope

- benchmark: locomo
- subset: non_adversarial_full
- experiment_kind: formal
- limit: None
- workers: 8
- input_path: /data/home_new/wujinqi/agent-memory/outputs/prepare_locomo_non_adversarial/prediction_input.jsonl
- config_path: /data/home_new/wujinqi/agent-memory/configs/stage1_route_budgeted_retrieval_v34_cached.json
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0, max_input_tokens 131072, and max_output_tokens 16384.

## Git

- inside_work_tree: True
- commit: fb6c703356a60e8c7d4b5ea1a2ded9e37a21419c
- dirty: True
- dirty_note: prediction run started with only user-edited `docs/architecture.md` and `docs/clean_protocol.md` dirty. Prediction code, config, and v34 gate record were committed.

## Metrics

- n_samples: 1540
- DeepSeek judge accuracy_valid_only: 0.7797270955165692
- DeepSeek judge accuracy_invalid_as_wrong: 1200/1540 = 0.7792207792207793
- DeepSeek judge n_correct/n_valid/n_samples: 1200/1539/1540
- DeepSeek judge n_invalid: 1
- baseline_vs_v33: +12 correct, v33 was 1188/1540
- baseline_vs_v29: +27 correct, v29 was 1173/1540
- target_gap: LoCoMo 0.78 target needs 1202/1540 under invalid-as-wrong accounting; v34 is 2 correct short.
- f1/bleu/exact: not used for method selection
- avg_build_tokens: 58386.00779220779
- build_token_accounting: logical cold-build LLM tokens; cached build chunks count from stored usage, while cache hits only avoid repeated local API calls.
- avg_query_tokens: 4920.3266233766235
- total_build_tokens: 89914452
- total_query_tokens: 7577303
- DeepSeek judge total_tokens: 662954
- avg_compiled_evidence_items: 55.61038961038961
- retrieval_route_overrides: {'temporal_lookup': {'top_k': 40, 'max_top_k': 40, 'dense_top_k': 40, 'lexical_protect_top_n': 0, 'dense_protect_top_n': 32}}
- avg_effective_top_k: 55.61038961038961
- avg_effective_dense_top_k: 55.61038961038961
- avg_effective_dense_protect_top_n: 44.48831168831169
- route_effective_budget_check: temporal_lookup `40/40/32/40`; non-temporal routes `60/60/48/60` for top_k/dense_top_k/dense_protect/evidence_items.
- build_memory_enabled: True
- build_memory_model: Qwen/Qwen3-30B-A3B-Instruct-2507
- build_memory_temporal_fields: False
- build_memory_cache_enabled: True
- build_memory_cache_path: outputs/cache/qwen3_build_memory.sqlite
- build_memory_cache_hits: 12411
- build_memory_cache_misses: 0
- build_memory_cache_writes: 0
- avg_build_memory_records: 136.65974025974026
- avg_active_build_memory_records: 125.11233766233767
- avg_memory_hits: 19.84155844155844
- avg_memory_source_hits: 22.37922077922078
- build_memory_include_superseded: False
- build_memory_include_superseded_information_needs: ['temporal_lookup', 'list_count']
- neighbor_order: hit_priority
- drop_query_stopwords: True
- lexical_enabled: True
- dense_enabled: True
- lexical_protect_top_n: 0
- dense_protect_top_n: 48
- dense_document_text_mode: external_naive
- dense_query_text_mode: external_naive
- embedding_cache_enabled: True
- embedding_cache_path: outputs/cache/qwen3_embedding.sqlite
- embedding_cache_hits: 7422
- embedding_cache_misses: 0
- embedding_cache_writes: 0
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
- avg_embedding_tokens: 0.0
- avg_context_chars: 14478.938311688311
- compiler_prompt_mode: external_naive
- answer_mode: openai_compatible
- answer_model: Qwen/Qwen3-30B-A3B-Instruct-2507
- answer_max_input_tokens: 131072
- answer_max_output_tokens: 16384
- answer_output_format: json_answer
- answer_cache_enabled: True
- answer_cache_path: outputs/cache/qwen3_answer_v34_route_budgeted.sqlite
- answer_cache_namespace: stage1_route_budgeted_retrieval_v34_qwen3_30b
- answer_cache_hits: 1207
- answer_cache_misses: 333
- answer_cache_writes: 333
- answer_finalizer_enabled: False
- answer_finalizer_mode: structured_evidence_mechanical
- answer_finalizer_enable_count_correction: False
- answer_finalizer_enable_money_sum_correction: True
- answer_finalizer_applied_count: 0
- answer_finalizer_applied_rate: 0.0
- answer_repair_enabled: False
- answer_repair_mode: openai_compatible
- answer_repair_model: Qwen/Qwen3-30B-A3B-Instruct-2507
- answer_repair_max_input_tokens: 131072
- answer_repair_max_output_tokens: 16384
- answer_repair_output_format: json_answer
- answer_repair_information_needs: None
- answer_repair_enable_uncertain_trigger: True
- answer_repair_enable_short_list_trigger: True
- answer_repair_enable_temporal_conflict_trigger: True
- answer_repair_max_context_chars: 14000
- answer_repair_max_row_text_chars: 700
- answer_repair_cache_enabled: False
- answer_repair_cache_path: None
- answer_repair_cache_namespace: None
- answer_repair_cache_hits: 0
- answer_repair_cache_misses: 0
- answer_repair_cache_writes: 0
- answer_repair_triggered_count: 0
- answer_repair_triggered_rate: 0.0
- answer_repair_applied_count: 0
- answer_repair_applied_rate: 0.0
- answer_repair_total_query_tokens: 0
- answer_repair_avg_query_tokens_when_triggered: None
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
- temporal_workpad: True
- temporal_text_normalization: True
- temporal_event_contract: True
- temporal_workpad_scope: route
- temporal_workpad_max_rows: 12
- temporal_workpad_max_pairs: 12
- structured_guide: True
- structured_guide_max_rows: 12
- structured_guide_include_rows: True
- structured_guide_include_memory: False
- structured_guide_disabled_signals: ['personalized_recommendation']
- structured_answer_contract: False
- structured_answer_contract_information_needs: None
- structured_answer_contract_max_items: 10
- evidence_report_contract: True
- evidence_report_information_needs: ['current_state', 'fact_lookup', 'list_count', 'profile_preference', 'temporal_lookup']
- evidence_report_max_items: 8
- evidence_report_detail: False
- route_overrides: {'temporal_lookup': {'max_evidence_items': 40, 'max_evidence_chars': 18000}}
- enable_broad_list_patterns: False
- enable_recommendation_profile_patterns: True
- temporal_priority_over_recent: False

## Offline Evidence Recall

- evidence_recall: 0.9153645833333334 over 1536 examples with evidence labels
- by_type_1: 0.925531914893617, n=282
- by_type_2: 0.9065420560747663, n=321
- by_type_3: 0.6956521739130435, n=92
- by_type_4: 0.93935790725327, n=841

This is slightly below v33 top-60 evidence recall 0.91796875 because temporal rows use top-40 again, but answer accuracy improves. The result supports the hypothesis that temporal questions need narrower context rather than maximum source coverage.

## Comparison

Against v33 top-60:

- both_correct: 1156
- both_wrong: 308
- gained: 44
- lost: 32
- net: +12
- temporal_lookup: gained 19, lost 12, net +7
- fact_lookup: gained 23, lost 18, net +5
- list_count/profile_preference: each net 0
- current_state: unchanged all correct

Against v29 top-40:

- both_correct: 1118
- both_wrong: 285
- gained: 82
- lost: 55
- net: +27
- fact_lookup net +21
- list_count net +5
- profile_preference net +2
- current_state net +1
- temporal_lookup net -2

## Outputs

- predictions: /data/home_new/wujinqi/agent-memory/outputs/formal/stage1_route_budgeted_retrieval_v34_locomo_nonadv_full_fb6c703/predictions.jsonl
- traces: /data/home_new/wujinqi/agent-memory/outputs/formal/stage1_route_budgeted_retrieval_v34_locomo_nonadv_full_fb6c703/traces.jsonl
- metrics: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_route_budgeted_retrieval_v34_locomo_nonadv_full_fb6c703/metrics.json
- manifest: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_route_budgeted_retrieval_v34_locomo_nonadv_full_fb6c703/manifest.json

## Clean Notes

- No gold/reference/target answer, judge output, benchmark label, sample id, qid, or row index is passed into the prediction pipeline.
- Build-stage typed memory is generated only from raw dialogue and visible metadata; it is recorded separately from offline labels and judge outputs.
- Raw context remains available for fallback and diagnosis; build memory records keep source back-links when produced by the current builder.
- Accuracy is intentionally not computed by the prediction runner; any gold or judge metrics must be produced offline after prediction.

## Decision

v34 is the new LoCoMo best result and is materially better than v33/v29 while staying inside token budgets. It still misses the 0.78 target by 2 correct examples under conservative invalid-as-wrong accounting, so the next step should not be another blind full run.

Recommended next direction: inspect the remaining v34 lost/gained badcases, especially same-answer judge flips and fact/list errors, then design a small general answer formatting/final extraction fix or evidence compiler refinement. LongMemEval-S should wait for a separate LME token gate.
