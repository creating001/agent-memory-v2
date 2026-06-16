# Diagnosis for stage1_prompt_discipline_v100_lme_stratified_120_f844921

## Summary

This is a negative diagnostic. V100 enables detailed evidence reporting and inference/checklist contracts across all routes, but drops LongMemEval-S stratified-120 DeepSeek judge accuracy from v98 same-subset `94/120 = 0.783333` to `89/120 = 0.741667`. Do not promote v100 and do not run this broad prompt-discipline setting on full benchmarks.

The change is clean and general, but too broad: it makes the answerer over-select stale precise values, become more conservative on calculational questions, and over-explain cases where v98 gave the benchmark-preferred concise value.

Route-level comparison vs v98 on the same 120 examples:

- `current_state`: net `-1` (`CORRECT->WRONG 1`, no gains).
- `fact_lookup`: net `-3` (`CORRECT->WRONG 4`, `WRONG->CORRECT 1`).
- `list_count`: net `+1` (`CORRECT->WRONG 1`, `WRONG->CORRECT 2`).
- `profile_preference`: net `+1` (`WRONG->CORRECT 1`, no losses).
- `temporal_lookup`: net `-3` (`CORRECT->WRONG 3`, no gains).

Next candidates should be narrower and route-aware. Do not apply the detailed prompt contract to `fact_lookup` or `temporal_lookup` without a separate positive diagnostic.

## Observations

- samples_processed: 120
- avg_compiled_evidence_items: 34.583333333333336
- avg_build_tokens: 80445.16666666667
- build_token_accounting: logical cold-build LLM tokens; cached build chunks count from stored usage, while cache hits only avoid repeated local API calls.
- avg_build_memory_records: 129.91666666666666
- avg_active_build_memory_records: 116.075
- build_memory_temporal_fields: False
- build_memory_prompt_profile: typed_compact
- build_memory_manage_facts: True
- build_memory_overlap_turns: 0
- build_memory_cache_hits: 805
- build_memory_cache_misses: 0
- build_memory_cache_writes: 0
- build_memory_source_alignment: {}
- build_memory_source_alignment_changed_records: 0
- build_memory_source_alignment_added_sources: 0
- avg_build_memory_source_alignment_changed_records: 0.0
- avg_build_memory_source_alignment_added_sources: 0.0
- avg_memory_hits: 7.466666666666667
- avg_memory_source_hits: 7.541666666666667
- build_memory_include_superseded: False
- build_memory_include_superseded_information_needs: ['temporal_lookup', 'list_count']
- avg_context_chars: 22275.458333333332
- avg_query_tokens: 6506.341666666666
- retrieval_route_overrides: {'temporal_lookup': {'top_k': 40, 'max_top_k': 40, 'dense_top_k': 40, 'lexical_protect_top_n': 0, 'dense_protect_top_n': 32}}
- avg_effective_top_k: 40.0
- avg_effective_dense_top_k: 40.0
- avg_effective_dense_protect_top_n: 32.0
- dense_protect_top_n: 48
- turn_window_bm25_enabled: False
- turn_window_top_k: None
- turn_window_window_before: None
- turn_window_window_after: None
- turn_window_max_sources_per_window: None
- turn_window_bm25_applied_count: 0
- turn_window_bm25_applied_rate: 0.0
- avg_turn_window_hits: 0.0
- avg_turn_window_source_hits: 0.0
- selected_context_enabled: True
- selected_context_applied_count: 0
- selected_context_applied_rate: 0.0
- avg_selected_context_materialized_rows: 0.0
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
- embedding_cache_enabled: True
- embedding_cache_hits: 59481
- embedding_cache_misses: 0
- evidence_order: retrieval
- memory_record_source: retrieval
- avg_compiled_memory_records: 0.0
- memory_order: retrieval
- memory_layout: flat
- row_text_mode: full
- max_row_text_chars: 0
- evidence_row_labels: False
- final_answer_checklist: False
- max_memory_records: 0
- route_guidance: False
- temporal_workpad: True
- temporal_text_normalization: True
- temporal_event_contract: True
- temporal_workpad_scope: route
- temporal_workpad_max_rows: 12
- temporal_workpad_max_pairs: 12
- operation_workpad_question_gate: False
- personalized_advice_contract: False
- personalized_advice_contract_applied: 19
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
- update_conflict_guide_applied: 9
- current_state_update_contract: False
- dialogue_inference_contract: False
- temporal_order_contract: False
- source_anchor_keep: 0
- source_anchor_memory_rows: 0
- source_anchor_per_session: 0
- source_anchor_session_rows: 0
- route_overrides: {'temporal_lookup': {'max_evidence_items': 40, 'max_evidence_chars': 18000, 'evidence_report_detail': True, 'dialogue_inference_contract': True, 'temporal_order_contract': True, 'final_answer_checklist': True}, 'fact_lookup': {'evidence_report_detail': True, 'dialogue_inference_contract': True}, 'list_count': {'evidence_report_detail': True, 'dialogue_inference_contract': True, 'final_answer_checklist': True}, 'profile_preference': {'evidence_report_detail': True, 'dialogue_inference_contract': True, 'final_answer_checklist': True}, 'current_state': {'evidence_report_detail': True, 'dialogue_inference_contract': True, 'current_state_update_contract': True, 'final_answer_checklist': True}}
- enable_recommendation_profile_patterns: True
- enable_advice_profile_patterns: False
- temporal_priority_over_recent: False
- answer_max_input_tokens: 131072
- answer_max_output_tokens: 16384
- answer_cache_enabled: True
- answer_cache_path: outputs/cache/qwen3_answer_v100_prompt_discipline.sqlite
- answer_cache_namespace: stage1_prompt_discipline_v100_qwen3_30b
- answer_cache_hits: 0
- answer_cache_misses: 120
- answer_cache_writes: 120
- answer_finalizer_enabled: True
- answer_finalizer_mode: structured_evidence_mechanical
- answer_finalizer_enable_count_correction: False
- answer_finalizer_enable_evidence_report_count_correction: False
- answer_finalizer_enable_money_sum_correction: False
- answer_finalizer_enable_duration_rounding_correction: True
- answer_finalizer_enable_missing_detail: False
- answer_finalizer_enable_relative_time_calculation: True
- answer_finalizer_applied_count: 11
- answer_finalizer_applied_rate: 0.09166666666666666
- answer_repair_enabled: False
- answer_repair_mode: openai_compatible
- answer_repair_model: Qwen/Qwen3-30B-A3B-Instruct-2507
- answer_repair_max_input_tokens: 131072
- answer_repair_max_output_tokens: 16384
- answer_repair_information_needs: None
- answer_repair_enable_profile_preference_trigger: False
- answer_repair_triggered_count: 0
- answer_repair_triggered_rate: 0.0
- answer_repair_applied_count: 0
- answer_repair_applied_rate: 0.0
- answer_repair_total_query_tokens: 0
- answer_repair_avg_query_tokens_when_triggered: None
- answer_repair_cache_hits: 0
- answer_repair_cache_misses: 0
- answer_repair_cache_writes: 0
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0, max_input_tokens 131072, and max_output_tokens 16384.

## Next Steps

- Preserve this run as a diagnostic only.
- Use the badcase file to design a narrower candidate, likely avoiding broad `fact_lookup` and `temporal_lookup` prompt-discipline changes.
- Validate any next candidate on stratified LongMemEval-S and LoCoMo diagnostics before full runs.

## Outputs

- comparison_vs_v98: `/data/home_new/wujinqi/agent-memory/experiments/diagnostic/stage1_prompt_discipline_v100_lme_stratified_120_f844921/judge_comparison_vs_v98_same120.json`
- badcases_vs_v98: `/data/home_new/wujinqi/agent-memory/experiments/diagnostic/stage1_prompt_discipline_v100_lme_stratified_120_f844921/badcases_vs_v98_same120.md`
- deepseek_judge: `/data/home_new/wujinqi/agent-memory/experiments/diagnostic/stage1_prompt_discipline_v100_lme_stratified_120_f844921/deepseek_judge.json`
- predictions: `/data/home_new/wujinqi/agent-memory/outputs/diagnostic/stage1_prompt_discipline_v100_lme_stratified_120_f844921/predictions.jsonl`
- traces: `/data/home_new/wujinqi/agent-memory/outputs/diagnostic/stage1_prompt_discipline_v100_lme_stratified_120_f844921/traces.jsonl`
