# v54_turn_window_lme_weakroute_fc48b22

## 结论

v54 在 LongMemEval-S `weak_route_87` 诊断集上未超过 v42：DeepSeek judge accuracy 为 `59/87 = 0.678161`，与 v42 same87 完全持平。相对 v42 的 gain/loss 为 `7/7`，answer changed `25/87`。

按 question-derived information_need 分桶：`list_count` 从 `15/20` 提升到 `16/20`，但 `profile_preference` 从 `10/15` 降到 `9/15`，`current_state` 与 `temporal_lookup` 均持平且各有互相抵消的 gain/loss。avg_query_tokens 为 `5959.874`，接近 6K 预算。因此 v54 不进入 LongMemEval full。

诊断判断：turn-window retrieval 有局部正向信号，但 v54 同时把 dense hard-protect 从 32 降到 28，造成若干 v42 关键 evidence rows 被替换。下一步只做 v55 消融：保留 turn-window retrieval，但恢复 dense `protect_top_n=32`。

## Purpose

Stage-1 clean skeleton run: validate raw evidence storage, lexical retrieval, neighbor expansion, evidence compilation, answer generation, trace output, and experiment bookkeeping.

## Scope

- benchmark: longmemeval
- subset: weak_route_87
- experiment_kind: diagnostic
- limit: None
- workers: 4
- input_path: /data/home_new/wujinqi/agent-memory/outputs/diagnostic/v48_lme_weak_route_input/prediction_input.jsonl
- config_path: /data/home_new/wujinqi/agent-memory/configs/stage1_turn_window_retrieval_v54_cached.json
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0, max_input_tokens 131072, and max_output_tokens 16384.

## Git

- inside_work_tree: True
- commit: fc48b22013f29bc8c91cd37138b4379732077498
- dirty: True
- note: None

## Metrics

- n_samples: 87
- accuracy: None
- f1: None
- bleu: None
- avg_build_tokens: 80991.86206896552
- build_token_accounting: logical cold-build LLM tokens; cached build chunks count from stored usage, while cache hits only avoid repeated local API calls.
- avg_query_tokens: 5959.873563218391
- question_analysis_enabled: False
- question_analysis_model: None
- question_analysis_avg_query_tokens: 0.0
- question_analysis_route_changed_count: 0
- question_analysis_cache_hits: 0
- question_analysis_cache_misses: 0
- question_analysis_cache_writes: 0
- avg_compiled_evidence_items: 30.977011494252874
- retrieval_route_overrides: {}
- avg_effective_top_k: 40.0
- avg_effective_dense_top_k: 40.0
- avg_effective_dense_protect_top_n: 28.0
- build_memory_enabled: True
- build_memory_model: Qwen/Qwen3-30B-A3B-Instruct-2507
- build_memory_temporal_fields: False
- build_memory_cache_enabled: True
- build_memory_cache_path: outputs/cache/qwen3_build_memory.sqlite
- build_memory_cache_hits: 585
- build_memory_cache_misses: 0
- build_memory_cache_writes: 0
- avg_build_memory_records: 130.98850574712642
- avg_active_build_memory_records: 117.41379310344827
- avg_memory_hits: 8.620689655172415
- avg_memory_source_hits: 8.298850574712644
- build_memory_include_superseded: False
- build_memory_include_superseded_information_needs: ['temporal_lookup', 'list_count']
- neighbor_order: hit_priority
- drop_query_stopwords: True
- lexical_enabled: True
- dense_enabled: True
- lexical_protect_top_n: 0
- dense_protect_top_n: 28
- dense_document_text_mode: external_naive
- dense_query_text_mode: external_naive
- embedding_cache_enabled: True
- embedding_cache_path: outputs/cache/qwen3_embedding.sqlite
- embedding_cache_hits: 43433
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
- turn_window_bm25_enabled: True
- turn_window_top_k: 24
- turn_window_window_before: 1
- turn_window_window_after: 1
- turn_window_max_sources_per_window: 3
- turn_window_max_chars_per_turn: 500
- turn_window_enabled_route_signals: None
- turn_window_enabled_information_needs: None
- turn_window_enabled_query_patterns: None
- turn_window_bm25_applied_count: 87
- turn_window_bm25_applied_rate: 1.0
- avg_turn_window_hits: 24.0
- avg_turn_window_source_hits: 36.11494252873563
- avg_embedding_tokens: 0.0
- avg_context_chars: 20180.954022988506
- compiler_prompt_mode: external_naive
- compiler_memory_record_source: retrieval
- avg_compiled_memory_records: 0.0
- answer_mode: openai_compatible
- answer_model: Qwen/Qwen3-30B-A3B-Instruct-2507
- answer_max_input_tokens: 131072
- answer_max_output_tokens: 16384
- answer_output_format: json_answer
- answer_cache_enabled: True
- answer_cache_path: outputs/cache/qwen3_answer_v54_turn_window.sqlite
- answer_cache_namespace: stage1_turn_window_retrieval_v54_qwen3_30b
- answer_cache_hits: 87
- answer_cache_misses: 0
- answer_cache_writes: 0
- answer_finalizer_enabled: True
- answer_finalizer_mode: structured_evidence_mechanical
- answer_finalizer_enable_count_correction: False
- answer_finalizer_enable_evidence_report_count_correction: False
- answer_finalizer_enable_money_sum_correction: False
- answer_finalizer_enable_duration_rounding_correction: True
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
- answer_repair_enable_profile_preference_trigger: False
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
- scoped_evidence_enabled: False
- scoped_evidence_information_needs: None
- scoped_evidence_max_rows: None
- scoped_evidence_max_row_chars: None
- scoped_evidence_applied_count: 0
- scoped_evidence_applied_rate: 0.0
- scoped_evidence_total_extraction_query_tokens: 0
- scoped_evidence_avg_extraction_query_tokens_when_applied: None
- scoped_evidence_total_answer_query_tokens: 0
- scoped_evidence_avg_answer_query_tokens_when_applied: None
- scoped_evidence_avg_extraction_prompt_chars_when_applied: None
- scoped_evidence_avg_answer_prompt_chars_when_applied: None
- scoped_evidence_avg_evidence_json_chars_when_applied: None
- scoped_evidence_extraction_cache_hits: 0
- scoped_evidence_extraction_cache_misses: 0
- scoped_evidence_extraction_cache_writes: 0
- scoped_evidence_answer_cache_hits: 0
- scoped_evidence_answer_cache_misses: 0
- scoped_evidence_answer_cache_writes: 0
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
- temporal_event_contract: False
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
- aggregation_report_contract: False
- aggregation_report_information_needs: None
- candidate_guide: False
- candidate_guide_information_needs: None
- candidate_guide_max_rows: 6
- candidate_guide_snippet_chars: 160
- route_overrides: {}
- enable_broad_list_patterns: False
- enable_recommendation_profile_patterns: True
- enable_advice_profile_patterns: False
- temporal_priority_over_recent: False

## Outputs

- predictions: /data/home_new/wujinqi/agent-memory/outputs/diagnostic/v54_turn_window_lme_weakroute_fc48b22/predictions.jsonl
- traces: /data/home_new/wujinqi/agent-memory/outputs/diagnostic/v54_turn_window_lme_weakroute_fc48b22/traces.jsonl
- metrics: /data/home_new/wujinqi/agent-memory/experiments/diagnostic/v54_turn_window_lme_weakroute_fc48b22/metrics.json
- manifest: /data/home_new/wujinqi/agent-memory/experiments/diagnostic/v54_turn_window_lme_weakroute_fc48b22/manifest.json

## Clean Notes

- No gold/reference/target answer, judge output, benchmark label, sample id, qid, or row index is passed into the prediction pipeline.
- Build-stage typed memory is generated only from raw dialogue and visible metadata; it is recorded separately from offline labels and judge outputs.
- Raw context remains available for fallback and diagnosis; build memory records keep source back-links when produced by the current builder.
- Accuracy is intentionally not computed by the prediction runner; any gold or judge metrics must be produced offline after prediction.
