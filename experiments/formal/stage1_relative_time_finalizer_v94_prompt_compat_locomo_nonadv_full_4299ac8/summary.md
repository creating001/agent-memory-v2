# stage1_relative_time_finalizer_v94_prompt_compat_locomo_nonadv_full_4299ac8

## Purpose

Stage-1 clean skeleton run: validate raw evidence storage, lexical retrieval, neighbor expansion, evidence compilation, answer generation, trace output, and experiment bookkeeping.

## Scope

- benchmark: LoCoMo
- subset: non-adversarial-full
- experiment_kind: formal
- limit: None
- workers: 8
- input_path: /data/home_new/wujinqi/agent-memory/outputs/prepare_locomo_non_adversarial/prediction_input.jsonl
- config_path: /data/home_new/wujinqi/agent-memory/configs/stage1_relative_time_finalizer_v94_cached.json
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0, max_input_tokens 131072, and max_output_tokens 16384.

## Git

- inside_work_tree: True
- commit: 4299ac81cc7ed2df31d7006047cfbb6f8dc912ba
- dirty: False
- note: None

## Metrics

- n_samples: 1540
- accuracy: None
- f1: None
- bleu: None
- avg_build_tokens: 58386.00779220779
- build_token_accounting: logical cold-build LLM tokens; cached build chunks count from stored usage, while cache hits only avoid repeated local API calls.
- avg_query_tokens: 4920.572727272727
- avg_compiled_evidence_items: 55.61038961038961
- retrieval_route_overrides: {'temporal_lookup': {'top_k': 40, 'max_top_k': 40, 'dense_top_k': 40, 'lexical_protect_top_n': 0, 'dense_protect_top_n': 32}}
- avg_effective_top_k: 55.61038961038961
- avg_effective_dense_top_k: 55.61038961038961
- avg_effective_dense_protect_top_n: 44.48831168831169
- build_memory_enabled: True
- build_memory_model: Qwen/Qwen3-30B-A3B-Instruct-2507
- build_memory_temporal_fields: False
- build_memory_prompt_profile: typed_compact
- build_memory_manage_facts: True
- build_memory_overlap_turns: 0
- build_memory_cache_enabled: True
- build_memory_cache_path: outputs/cache/qwen3_build_memory.sqlite
- build_memory_cache_hits: 12411
- build_memory_cache_misses: 0
- build_memory_cache_writes: 0
- build_memory_source_alignment: {}
- build_memory_source_alignment_changed_records: 0
- build_memory_source_alignment_added_sources: 0
- avg_build_memory_source_alignment_changed_records: 0.0
- avg_build_memory_source_alignment_added_sources: 0.0
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
- avg_context_chars: 14478.938311688311
- compiler_prompt_mode: external_naive
- compiler_memory_record_source: retrieval
- avg_compiled_memory_records: 0.0
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
- answer_finalizer_enable_evidence_report_count_correction: False
- answer_finalizer_enable_money_sum_correction: False
- answer_finalizer_enable_duration_rounding_correction: True
- answer_finalizer_enable_missing_detail: False
- answer_finalizer_enable_relative_time_calculation: True
- answer_finalizer_applied_count: 8
- answer_finalizer_applied_rate: 0.005194805194805195
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
- temporal_event_contract: True
- temporal_workpad_scope: route
- temporal_workpad_max_rows: 12
- temporal_workpad_max_pairs: 12
- operation_workpad_question_gate: False
- personalized_advice_contract: False
- personalized_advice_contract_applied: 0
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
- update_conflict_guide: False
- update_conflict_guide_information_needs: None
- update_conflict_guide_max_rows: 6
- update_conflict_guide_snippet_chars: 180
- update_conflict_guide_applied: 0
- current_state_update_contract: False
- dialogue_inference_contract: False
- temporal_order_contract: False
- source_anchor_keep: 0
- source_anchor_memory_rows: 0
- source_anchor_per_session: 0
- source_anchor_session_rows: 0
- route_overrides: {'temporal_lookup': {'max_evidence_items': 40, 'max_evidence_chars': 18000}}
- enable_broad_list_patterns: False
- enable_recommendation_profile_patterns: True
- enable_advice_profile_patterns: False
- temporal_priority_over_recent: False

## Offline Judge

- judge_model: deepseek-v4-flash
- fresh_full_accuracy: `0.7831168831168831`
- fresh_full_correct: `1206/1540`
- fresh_full_invalid: `0`
- fresh_full_judge_tokens: `663960`
- controlled_accuracy_invalid_as_wrong: `0.7818181818181819`
- controlled_correct: `1204/1540`
- controlled_changed_predictions: `6/1540`
- controlled_changed_transitions_vs_v35: `WRONG->CORRECT 4`, `CORRECT->CORRECT 1`, `CORRECT->WRONG 1`
- baseline_v35_historical: `1201/1540 = 0.779870` invalid-as-wrong; valid-only `0.780377`

## Conclusion

This is the current LoCoMo best run. The fresh full judge is `+5` correct over historical v35, while the controlled changed-prediction comparison is `+3`; the remaining `+2` comes from judge rerun variance on unchanged predictions.

## Outputs

- predictions: /data/home_new/wujinqi/agent-memory/outputs/formal/stage1_relative_time_finalizer_v94_prompt_compat_locomo_nonadv_full_4299ac8/predictions.jsonl
- traces: /data/home_new/wujinqi/agent-memory/outputs/formal/stage1_relative_time_finalizer_v94_prompt_compat_locomo_nonadv_full_4299ac8/traces.jsonl
- metrics: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_relative_time_finalizer_v94_prompt_compat_locomo_nonadv_full_4299ac8/metrics.json
- manifest: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_relative_time_finalizer_v94_prompt_compat_locomo_nonadv_full_4299ac8/manifest.json
- deepseek_judge: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_relative_time_finalizer_v94_prompt_compat_locomo_nonadv_full_4299ac8/deepseek_judge.json
- controlled_comparison_vs_v35: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_relative_time_finalizer_v94_prompt_compat_locomo_nonadv_full_4299ac8/controlled_comparison_vs_v35.json
- judge_comparison_vs_v35: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_relative_time_finalizer_v94_prompt_compat_locomo_nonadv_full_4299ac8/judge_comparison_vs_v35.json

## Clean Notes

- No gold/reference/target answer, judge output, benchmark label, sample id, qid, or row index is passed into the prediction pipeline.
- Build-stage typed memory is generated only from raw dialogue and visible metadata; it is recorded separately from offline labels and judge outputs.
- Raw context remains available for fallback and diagnosis; build memory records keep source back-links when produced by the current builder.
- Accuracy is intentionally not computed by the prediction runner; any gold or judge metrics must be produced offline after prediction.
