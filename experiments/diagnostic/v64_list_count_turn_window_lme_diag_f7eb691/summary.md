# v64_list_count_turn_window_lme_diag_f7eb691

## Purpose

诊断 v64 list_count-only adjacent-turn window BM25：在 v42 operation workpad 底座上，仅对 question-derived `list_count` 启用相邻 turn window BM25，并回链到原始 raw source turns。目标是验证 v54 在 list_count 子集上出现的局部正向信号是否能扩展到 LongMemEval-S 全部 119 条 list_count 问题。

设计参考 creating001-agent-memory 的 turn-pair/source-turn materialization，以及 v54 的 adjacent-turn window BM25 诊断；不使用 gold、judge、benchmark label、sample id、row index、test feedback 或样本级规则。

## Scope

- benchmark: longmemeval_s
- subset: list_count_119
- experiment_kind: diagnostic
- limit: None
- workers: 8
- input_path: /data/home_new/wujinqi/agent-memory/outputs/diagnostic/v64_lme_list_count_input/prediction_input.jsonl
- config_path: /data/home_new/wujinqi/agent-memory/configs/stage1_list_count_turn_window_v64_cached.json
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0, max_input_tokens 131072, and max_output_tokens 16384.

## Git

- inside_work_tree: True
- commit: f7eb69161cee5c0d9043089c1fed4ab9e474e0df
- dirty: False
- note: None

## Metrics

- n_samples: 119
- DeepSeek judge accuracy: 0.781513 (93/119)
- v42 same119 accuracy: 0.798319 (95/119)
- vs v42 same119: gained 5, lost 7, net -2
- changed_answer_count: 17
- f1: None
- bleu: None
- avg_build_tokens: 80050.49579831933
- build_token_accounting: logical cold-build LLM tokens; cached build chunks count from stored usage, while cache hits only avoid repeated local API calls.
- avg_query_tokens: 5648.55462184874
- token decision: within the 6K LongMemEval query budget
- avg_compiled_evidence_items: 29.92436974789916
- retrieval_route_overrides: {}
- avg_effective_top_k: 40.0
- avg_effective_dense_top_k: 40.0
- avg_effective_dense_protect_top_n: 28.0
- build_memory_enabled: True
- build_memory_model: Qwen/Qwen3-30B-A3B-Instruct-2507
- build_memory_temporal_fields: False
- build_memory_prompt_profile: typed_compact
- build_memory_manage_facts: True
- build_memory_overlap_turns: 0
- build_memory_cache_enabled: True
- build_memory_cache_path: outputs/cache/qwen3_build_memory.sqlite
- build_memory_cache_hits: 797
- build_memory_cache_misses: 0
- build_memory_cache_writes: 0
- build_memory_source_alignment: {}
- build_memory_source_alignment_changed_records: 0
- build_memory_source_alignment_added_sources: 0
- avg_build_memory_source_alignment_changed_records: 0.0
- avg_build_memory_source_alignment_added_sources: 0.0
- avg_build_memory_records: 129.94117647058823
- avg_active_build_memory_records: 117.72268907563026
- avg_memory_hits: 8.831932773109244
- avg_memory_source_hits: 8.117647058823529
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
- embedding_cache_hits: 58482
- embedding_cache_misses: 0
- embedding_cache_writes: 0
- turn_window_bm25_enabled: True
- turn_window_top_k: 24
- turn_window_window_before: 1
- turn_window_window_after: 1
- turn_window_max_sources_per_window: 3
- turn_window_max_chars_per_turn: 500
- turn_window_enabled_route_signals: None
- turn_window_enabled_information_needs: ['list_count']
- turn_window_enabled_query_patterns: None
- turn_window_bm25_applied_count: 119
- turn_window_bm25_applied_rate: 1.0
- avg_turn_window_hits: 24.0
- avg_turn_window_source_hits: 35.285714285714285
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
- avg_context_chars: 19931.991596638654
- compiler_prompt_mode: external_naive
- compiler_memory_record_source: retrieval
- avg_compiled_memory_records: 0.0
- answer_mode: openai_compatible
- answer_model: Qwen/Qwen3-30B-A3B-Instruct-2507
- answer_max_input_tokens: 131072
- answer_max_output_tokens: 16384
- answer_output_format: json_answer
- answer_cache_enabled: True
- answer_cache_path: outputs/cache/qwen3_answer_v64_list_count_turn_window.sqlite
- answer_cache_namespace: stage1_list_count_turn_window_v64_qwen3_30b
- answer_cache_hits: 0
- answer_cache_misses: 119
- answer_cache_writes: 119
- answer_finalizer_enabled: True
- answer_finalizer_mode: structured_evidence_mechanical
- answer_finalizer_enable_count_correction: False
- answer_finalizer_enable_evidence_report_count_correction: False
- answer_finalizer_enable_money_sum_correction: False
- answer_finalizer_enable_duration_rounding_correction: True
- answer_finalizer_applied_count: 0
- answer_finalizer_applied_rate: 0.0
- evidence_recall: 1.000000 (offline diagnostic only)
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
- enable_advice_profile_patterns: False
- temporal_priority_over_recent: False

## Outputs

- predictions: /data/home_new/wujinqi/agent-memory/outputs/diagnostic/v64_list_count_turn_window_lme_diag_f7eb691/predictions.jsonl
- traces: /data/home_new/wujinqi/agent-memory/outputs/diagnostic/v64_list_count_turn_window_lme_diag_f7eb691/traces.jsonl
- metrics: /data/home_new/wujinqi/agent-memory/experiments/diagnostic/v64_list_count_turn_window_lme_diag_f7eb691/metrics.json
- manifest: /data/home_new/wujinqi/agent-memory/experiments/diagnostic/v64_list_count_turn_window_lme_diag_f7eb691/manifest.json
- judge: /data/home_new/wujinqi/agent-memory/experiments/diagnostic/v64_list_count_turn_window_lme_diag_f7eb691/deepseek_judge.json
- evidence recall: /data/home_new/wujinqi/agent-memory/experiments/diagnostic/v64_list_count_turn_window_lme_diag_f7eb691/evidence_recall.json
- comparison vs v42: /data/home_new/wujinqi/agent-memory/experiments/diagnostic/v64_list_count_turn_window_lme_diag_f7eb691/judge_comparison_vs_v42_same119.json

## Conclusion

v64 是负向诊断：token 合格，但 same119 accuracy 低于 v42，gain/loss `5/7`，net `-2`。adjacent-turn window 确实修复了少量 multi-session count 漏召回/漏聚合样本，但也引入噪声和过度保守回退；不扩 full，顶层 config 删除，只保留本诊断快照。

## Clean Notes

- No gold/reference/target answer, judge output, benchmark label, sample id, qid, or row index is passed into the prediction pipeline.
- Build-stage typed memory is generated only from raw dialogue and visible metadata; it is recorded separately from offline labels and judge outputs.
- Raw context remains available for fallback and diagnosis; build memory records keep source back-links when produced by the current builder.
- Accuracy is intentionally not computed by the prediction runner; any gold or judge metrics must be produced offline after prediction.
