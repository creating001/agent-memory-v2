# stage1_profile_compact_repair_v75_lme_s_full_f21f16b

## Purpose

Stage-1 clean skeleton run: validate raw evidence storage, lexical retrieval, neighbor expansion, evidence compilation, answer generation, trace output, and experiment bookkeeping.

## Scope

- benchmark: LongMemEval-S
- subset: full
- experiment_kind: formal
- limit: None
- workers: 8
- input_path: /data/home_new/wujinqi/agent-memory/outputs/prepare_longmemeval_s_cleaned/prediction_input.jsonl
- config_path: /data/home_new/wujinqi/agent-memory/configs/stage1_profile_compact_repair_v75_cached.json
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0, max_input_tokens 131072, and max_output_tokens 16384.

## Git

- inside_work_tree: True
- commit: f21f16bbf3a3f92d7c690b802bd8a985b84d4262
- dirty: False
- note: None

## Metrics

- n_samples: 500
- accuracy: 0.766 (DeepSeek judge, offline fresh full judge)
- evidence_recall: 1.0 (offline diagnostic)
- f1: None
- bleu: None
- avg_build_tokens: 80346.246
- build_token_accounting: logical cold-build LLM tokens; cached build chunks count from stored usage, while cache hits only avoid repeated local API calls.
- avg_query_tokens: 5985.758
- avg_compiled_evidence_items: 34.062
- retrieval_route_overrides: {}
- avg_effective_top_k: 40.0
- avg_effective_dense_top_k: 40.0
- avg_effective_dense_protect_top_n: 32.0
- build_memory_enabled: True
- build_memory_model: Qwen/Qwen3-30B-A3B-Instruct-2507
- build_memory_temporal_fields: False
- build_memory_prompt_profile: typed_compact
- build_memory_manage_facts: True
- build_memory_overlap_turns: 0
- build_memory_cache_enabled: True
- build_memory_cache_path: outputs/cache/qwen3_build_memory.sqlite
- build_memory_cache_hits: 3341
- build_memory_cache_misses: 0
- build_memory_cache_writes: 0
- build_memory_source_alignment: {}
- build_memory_source_alignment_changed_records: 0
- build_memory_source_alignment_added_sources: 0
- avg_build_memory_source_alignment_changed_records: 0.0
- avg_build_memory_source_alignment_added_sources: 0.0
- avg_build_memory_records: 129.662
- avg_active_build_memory_records: 116.456
- avg_memory_hits: 8.23
- avg_memory_source_hits: 7.918
- build_memory_include_superseded: False
- build_memory_include_superseded_information_needs: ['temporal_lookup', 'list_count']
- neighbor_order: hit_priority
- drop_query_stopwords: True
- lexical_enabled: True
- dense_enabled: True
- lexical_protect_top_n: 0
- dense_protect_top_n: 32
- dense_document_text_mode: external_naive
- dense_query_text_mode: external_naive
- embedding_cache_enabled: True
- embedding_cache_path: outputs/cache/qwen3_embedding.sqlite
- embedding_cache_hits: 247238
- embedding_cache_misses: 0
- embedding_cache_writes: 0
- turn_window_bm25_enabled: False
- turn_window_top_k: None
- turn_window_window_before: None
- turn_window_window_after: None
- turn_window_max_sources_per_window: None
- turn_window_max_chars_per_turn: None
- turn_window_enabled_route_signals: None
- turn_window_enabled_information_needs: None
- turn_window_enabled_query_patterns: None
- turn_window_bm25_applied_count: 0
- turn_window_bm25_applied_rate: 0.0
- avg_turn_window_hits: 0.0
- avg_turn_window_source_hits: 0.0
- rerank_enabled: False
- rerank_model: None
- rerank_pool_k: None
- rerank_anchor_keep: None
- rerank_anchor_after_top: None
- rerank_applied_count: 0
- rerank_applied_rate: 0.0
- avg_rerank_candidate_count: None
- avg_rerank_returned_count: None
- avg_rerank_tokens_when_applied: None
- rerank_token_accounting: rerank model tokens are reported separately and are not included in build/query LLM token budgets.
- avg_embedding_tokens: 0.0
- avg_context_chars: 19628.346
- compiler_prompt_mode: external_naive
- compiler_memory_record_source: retrieval
- avg_compiled_memory_records: 0.0
- answer_mode: openai_compatible
- answer_model: Qwen/Qwen3-30B-A3B-Instruct-2507
- answer_max_input_tokens: 131072
- answer_max_output_tokens: 16384
- answer_output_format: json_answer
- answer_cache_enabled: True
- answer_cache_path: outputs/cache/qwen3_answer_profile_compact_repair_v75.sqlite
- answer_cache_namespace: stage1_profile_compact_repair_v75_qwen3_30b
- answer_cache_hits: 485
- answer_cache_misses: 15
- answer_cache_writes: 15
- answer_finalizer_enabled: True
- answer_finalizer_mode: structured_evidence_mechanical
- answer_finalizer_enable_count_correction: False
- answer_finalizer_enable_evidence_report_count_correction: False
- answer_finalizer_enable_money_sum_correction: False
- answer_finalizer_enable_duration_rounding_correction: False
- answer_finalizer_applied_count: 0
- answer_finalizer_applied_rate: 0.0
- answer_repair_enabled: True
- answer_repair_mode: openai_compatible
- answer_repair_model: Qwen/Qwen3-30B-A3B-Instruct-2507
- answer_repair_max_input_tokens: 131072
- answer_repair_max_output_tokens: 16384
- answer_repair_output_format: json_answer
- answer_repair_information_needs: ['profile_preference']
- answer_repair_enable_uncertain_trigger: False
- answer_repair_enable_short_list_trigger: False
- answer_repair_enable_temporal_conflict_trigger: False
- answer_repair_enable_profile_preference_trigger: True
- answer_repair_max_context_chars: 4500
- answer_repair_max_row_text_chars: 320
- answer_repair_cache_enabled: True
- answer_repair_cache_path: outputs/cache/qwen3_profile_compact_repair_v75.sqlite
- answer_repair_cache_namespace: stage1_profile_compact_repair_v75_qwen3_30b
- answer_repair_cache_hits: 0
- answer_repair_cache_misses: 29
- answer_repair_cache_writes: 29
- answer_repair_triggered_count: 29
- answer_repair_triggered_rate: 0.058
- answer_repair_applied_count: 8
- answer_repair_applied_rate: 0.016
- answer_repair_total_query_tokens: 67318
- answer_repair_avg_query_tokens_when_triggered: 2321.310344827586
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
- operation_workpad_question_gate: False
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
- current_state_update_contract: False
- dialogue_inference_contract: False
- temporal_order_contract: False
- source_anchor_keep: 0
- source_anchor_memory_rows: 0
- source_anchor_per_session: 0
- source_anchor_session_rows: 0
- route_overrides: {}
- enable_broad_list_patterns: False
- enable_recommendation_profile_patterns: True
- enable_advice_profile_patterns: True
- temporal_priority_over_recent: False

## Outputs

- predictions: /data/home_new/wujinqi/agent-memory/outputs/formal/stage1_profile_compact_repair_v75_lme_s_full_f21f16b/predictions.jsonl
- traces: /data/home_new/wujinqi/agent-memory/outputs/formal/stage1_profile_compact_repair_v75_lme_s_full_f21f16b/traces.jsonl
- metrics: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_profile_compact_repair_v75_lme_s_full_f21f16b/metrics.json

## Offline Evaluation

- judge: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_profile_compact_repair_v75_lme_s_full_f21f16b/deepseek_judge.json
- evidence_recall: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_profile_compact_repair_v75_lme_s_full_f21f16b/evidence_recall.json
- comparison_vs_v73: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_profile_compact_repair_v75_lme_s_full_f21f16b/judge_comparison_vs_v73.json
- delta_badcases: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_profile_compact_repair_v75_lme_s_full_f21f16b/delta_badcases.md

## 结论

v75 fresh full judge accuracy 为 0.766，低于 v73 的 0.778，不进入主线。由于本实验使用 v73 trace seed cache，`prediction_changed=19/500`；changed-prediction 子集为 `WRONG->CORRECT 6`、`CORRECT->WRONG 5`、`WRONG->WRONG 5`、`CORRECT->CORRECT 3`，受控净 +1。如果未改 prediction 沿用 v73 judge，controlled accuracy 为 `390/500 = 0.780`。这说明 profile repair 有局部信号，但 all-profile repair 会把已正确的 personalized answer 压短或漏掉关键约束，并误伤含 `favorite` 修饰语的 fact/discount 问题。

下一步如果继续 profile 方向，应只修 draft 自己拒答/unknown/missing 的 profile/advice 样本，而不是对所有 `profile_preference` 做二次改写；同时需要修正 profile route 不能把 quantity/fact slot 题仅因出现 `favorite` 就当偏好题。
- manifest: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_profile_compact_repair_v75_lme_s_full_f21f16b/manifest.json

## Clean Notes

- No gold/reference/target answer, judge output, benchmark label, sample id, qid, or row index is passed into the prediction pipeline.
- Build-stage typed memory is generated only from raw dialogue and visible metadata; it is recorded separately from offline labels and judge outputs.
- Raw context remains available for fallback and diagnosis; build memory records keep source back-links when produced by the current builder.
- Accuracy is intentionally not computed by the prediction runner; any gold or judge metrics must be produced offline after prediction.
