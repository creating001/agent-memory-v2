# stage1_answer_format_guard_v35_locomo_nonadv_full_80158a9

## Purpose

Validate v35 answer format guard on top of v34 route-budgeted retrieval.

v35 keeps v34 build/retrieval/compiler unchanged, then adds two query-side answer stability fixes: robust `json_answer` salvage from raw_response/cache and a narrow duration rounding finalizer for `how many days/weeks/months/years` decimal answers.

## Scope

- benchmark: locomo
- subset: non_adversarial_full
- experiment_kind: formal
- limit: None
- workers: 8
- input_path: /data/home_new/wujinqi/agent-memory/outputs/prepare_locomo_non_adversarial/prediction_input.jsonl
- config_path: /data/home_new/wujinqi/agent-memory/configs/stage1_answer_format_guard_v35_cached.json
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0, max_input_tokens 131072, and max_output_tokens 16384.

## Git

- inside_work_tree: True
- commit: 80158a98f86d408e46ea3aa4de9c6e187fb0c808
- dirty: True
- dirty_note: prediction run started with only user-edited `docs/architecture.md` and `docs/clean_protocol.md` dirty. Prediction code and v35 config were committed.

## Metrics

- n_samples: 1540
- DeepSeek judge accuracy_valid_only: 0.7803768680961664
- DeepSeek judge accuracy_invalid_as_wrong: 1201/1540 = 0.7798701298701298
- DeepSeek judge n_correct/n_valid/n_samples: 1201/1539/1540
- DeepSeek judge n_invalid: 1
- baseline_vs_v34: +1 correct, v34 was 1200/1540
- baseline_vs_v33: +13 correct, v33 was 1188/1540
- baseline_vs_v29: +28 correct, v29 was 1173/1540
- target_status: valid-only DeepSeek accuracy reaches 0.78; conservative invalid-as-wrong accounting is still 1 correct short of 1202/1540.
- f1/bleu/exact: not used for method selection
- avg_build_tokens: 58386.00779220779
- build_token_accounting: logical cold-build LLM tokens; cached build chunks count from stored usage, while cache hits only avoid repeated local API calls.
- avg_query_tokens: 4920.572727272727
- total_build_tokens: 89914452
- total_query_tokens: 7577682
- DeepSeek judge total_tokens: 664038
- avg_compiled_evidence_items: 55.61038961038961
- retrieval_route_overrides: {'temporal_lookup': {'top_k': 40, 'max_top_k': 40, 'dense_top_k': 40, 'lexical_protect_top_n': 0, 'dense_protect_top_n': 32}}
- avg_effective_top_k: 55.61038961038961
- avg_effective_dense_top_k: 55.61038961038961
- avg_effective_dense_protect_top_n: 44.48831168831169
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
- answer_cache_path: outputs/cache/qwen3_answer_v35_format_guard.sqlite
- answer_cache_namespace: stage1_answer_format_guard_v35_qwen3_30b
- answer_cache_hits: 1540
- answer_cache_misses: 0
- answer_cache_writes: 0
- answer_finalizer_enabled: True
- answer_finalizer_mode: structured_evidence_mechanical
- answer_finalizer_enable_count_correction: False
- answer_finalizer_enable_money_sum_correction: False
- answer_finalizer_enable_duration_rounding_correction: True
- answer_finalizer_applied_count: 2
- answer_finalizer_applied_rate: 0.0012987012987012987
- changed_predictions_vs_v34: 6
- json_like_final_answers: 1
- decimal_duration_answers: 0
- finalizer_reasons: {'duration_decimal_rounding': 2}
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

Retrieval/compile context is unchanged from v34, so evidence recall matches v34.

## Comparison

Against v34:

- changed predictions: 6
- both_correct: 1174
- both_wrong: 313
- gained: 27
- lost: 26
- net: +1
- changed WRONG_to_CORRECT: 3
- changed both_correct: 2
- changed both_wrong: 1
- same-answer gained/lost are judge variance: same WRONG_to_CORRECT 24, same CORRECT_to_WRONG 26

Against v33:

- both_correct: 1159
- both_wrong: 310
- gained: 42
- lost: 29
- net: +13
- temporal_lookup net +13

Against v29:

- both_correct: 1120
- both_wrong: 286
- gained: 81
- lost: 53
- net: +28

## Outputs

- predictions: /data/home_new/wujinqi/agent-memory/outputs/formal/stage1_answer_format_guard_v35_locomo_nonadv_full_80158a9/predictions.jsonl
- traces: /data/home_new/wujinqi/agent-memory/outputs/formal/stage1_answer_format_guard_v35_locomo_nonadv_full_80158a9/traces.jsonl
- metrics: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_answer_format_guard_v35_locomo_nonadv_full_80158a9/metrics.json
- manifest: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_answer_format_guard_v35_locomo_nonadv_full_80158a9/manifest.json

## Clean Notes

- No gold/reference/target answer, judge output, benchmark label, sample id, qid, or row index is passed into the prediction pipeline.
- Build-stage typed memory is generated only from raw dialogue and visible metadata; it is recorded separately from offline labels and judge outputs.
- Raw context remains available for fallback and diagnosis; build memory records keep source back-links when produced by the current builder.
- Accuracy is intentionally not computed by the prediction runner; any gold or judge metrics must be produced offline after prediction.

## Decision

v35 is the first LoCoMo run to reach the 0.78 baseline target under valid-only DeepSeek accuracy. Because only 6 predictions changed and same-answer judge variance is visible, treat the result as positive but close-margin. For conservative reporting, also state invalid-as-wrong remains 1 correct short.

Next step: do not keep tuning LoCoMo only. Run a LongMemEval-S token gate for the v35/v34 route-budgeted method before any LME full run, and separately inspect whether a single invalid DeepSeek judgment can be reduced through judge retry policy in the evaluation script without changing predictions.
