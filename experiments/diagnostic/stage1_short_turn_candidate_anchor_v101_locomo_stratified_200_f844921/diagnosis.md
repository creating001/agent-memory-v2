# Diagnosis for stage1_short_turn_candidate_anchor_v101_locomo_stratified_200_f844921

## Summary

This is a negative diagnostic. V101 adds a short-turn source-anchor evidence order and compact candidate map for `fact_lookup`, `list_count`, and `temporal_lookup`, while leaving the v98 long-turn precision branch unchanged. On LoCoMo stratified-200, it drops from v98 same-subset `151/200 = 0.755000` to `144/200 = 0.720000`.

Do not promote v101 and do not run it on full benchmarks. The method is clean and general, but it makes the answerer more conservative on open-domain inference and loses too many fact/list answers. The temporal route improves slightly, but the net result is negative and avg query tokens rise above the 6K main budget.

Comparison vs v98 on the same 200 examples:

- Overall: `-7` correct answers.
- Category delta: Multi-Hop `-3`, Temporal Reasoning `+2`, Open-Domain `-5`, Single-Hop `-1`.
- Route delta: `fact_lookup -8`, `list_count -1`, `temporal_lookup +2`, `profile_preference 0`.
- Token cost: avg build `57779.145`, avg query `6161.570`.

Badcase pattern: candidate maps help some temporal endpoint selection, but they also encourage unsupported caution or over-narrowing. Losses include inference questions that v98 answered correctly, entity/place substitutions, and list answers where v101 drops valid items or over-includes adjacent activity details.

## Observations

- samples_processed: 200
- avg_compiled_evidence_items: 54.925
- avg_build_tokens: 57779.145
- build_token_accounting: logical cold-build LLM tokens; cached build chunks count from stored usage, while cache hits only avoid repeated local API calls.
- avg_build_memory_records: 135.135
- avg_active_build_memory_records: 123.645
- build_memory_temporal_fields: False
- build_memory_prompt_profile: typed_compact
- build_memory_manage_facts: True
- build_memory_overlap_turns: 0
- build_memory_cache_hits: 1596
- build_memory_cache_misses: 0
- build_memory_cache_writes: 0
- build_memory_source_alignment: {}
- build_memory_source_alignment_changed_records: 0
- build_memory_source_alignment_added_sources: 0
- avg_build_memory_source_alignment_changed_records: 0.0
- avg_build_memory_source_alignment_added_sources: 0.0
- avg_memory_hits: 19.82
- avg_memory_source_hits: 22.275
- build_memory_include_superseded: False
- build_memory_include_superseded_information_needs: ['temporal_lookup', 'list_count']
- avg_context_chars: 18227.615
- avg_query_tokens: 6161.57
- retrieval_route_overrides: {'temporal_lookup': {'top_k': 40, 'max_top_k': 40, 'dense_top_k': 40, 'lexical_protect_top_n': 0, 'dense_protect_top_n': 32}}
- avg_effective_top_k: 55.2
- avg_effective_dense_top_k: 55.2
- avg_effective_dense_protect_top_n: 44.16
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
- selected_context_applied_count: 152
- selected_context_applied_rate: 0.76
- avg_selected_context_materialized_rows: 4.56
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
- embedding_cache_hits: 6082
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
- enable_recommendation_profile_patterns: True
- enable_advice_profile_patterns: False
- temporal_priority_over_recent: False
- answer_max_input_tokens: 131072
- answer_max_output_tokens: 16384
- answer_cache_enabled: True
- answer_cache_path: outputs/cache/qwen3_answer_v101_short_turn_candidate_anchor.sqlite
- answer_cache_namespace: stage1_short_turn_candidate_anchor_v101_qwen3_30b
- answer_cache_hits: 0
- answer_cache_misses: 200
- answer_cache_writes: 200
- answer_finalizer_enabled: True
- answer_finalizer_mode: structured_evidence_mechanical
- answer_finalizer_enable_count_correction: False
- answer_finalizer_enable_evidence_report_count_correction: False
- answer_finalizer_enable_money_sum_correction: False
- answer_finalizer_enable_duration_rounding_correction: True
- answer_finalizer_enable_missing_detail: False
- answer_finalizer_enable_relative_time_calculation: True
- answer_finalizer_applied_count: 0
- answer_finalizer_applied_rate: 0.0
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

- Preserve this run as a negative diagnostic only.
- Do not use broad candidate maps for `fact_lookup` or `list_count` without a stronger gating signal.
- The next candidate should focus on the real LoCoMo gap with lower-risk changes, likely answer/finalizer behavior or a narrower temporal-only diagnostic rather than adding more prompt text.

## Outputs

- comparison_vs_v98: `/data/home_new/wujinqi/agent-memory/experiments/diagnostic/stage1_short_turn_candidate_anchor_v101_locomo_stratified_200_f844921/judge_comparison_vs_v98_same200.json`
- badcases_vs_v98: `/data/home_new/wujinqi/agent-memory/experiments/diagnostic/stage1_short_turn_candidate_anchor_v101_locomo_stratified_200_f844921/badcases_vs_v98_same200.md`
- deepseek_judge: `/data/home_new/wujinqi/agent-memory/experiments/diagnostic/stage1_short_turn_candidate_anchor_v101_locomo_stratified_200_f844921/deepseek_judge.json`
- predictions: `/data/home_new/wujinqi/agent-memory/outputs/diagnostic/stage1_short_turn_candidate_anchor_v101_locomo_stratified_200_f844921/predictions.jsonl`
- traces: `/data/home_new/wujinqi/agent-memory/outputs/diagnostic/stage1_short_turn_candidate_anchor_v101_locomo_stratified_200_f844921/traces.jsonl`
