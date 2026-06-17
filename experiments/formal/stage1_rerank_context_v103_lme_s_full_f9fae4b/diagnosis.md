# Diagnosis for stage1_rerank_context_v103_lme_s_full_f9fae4b

## Summary

This run is a negative result for the v103 rerank-context candidate. Under the
same Qwen/Qwen3.6-35B-A3B no-thinking backbone and default embedding setting,
v103 reduces query tokens but hurts LongMemEval-S full accuracy compared with
the current main-repo qwen3.6 v102 run.

## Judge Result

| Run | Backbone | Judge metric | Accuracy | Avg query tokens |
| --- | --- | --- | ---: | ---: |
| v102 current LTS | Qwen3.6 no-thinking | dual flash lenient | 415/500 = 0.830 | 6137.344 |
| v103 rerank-context | Qwen3.6 no-thinking | single flash diagnostic | 405/500 = 0.810 | 5186.944 |

Although v103 moves the average query tokens back under the 6K budget, the
accuracy regression means it should not be promoted as an LTS candidate. Old
non-current dual-judge artifacts were removed from this run; it is retained as a
negative query-token/rerank diagnostic only.

Decision: reject v103 as a mainline candidate. Full LoCoMo v103 was stopped
after this same-backbone LME regression was found; the aborted run produced only
0-byte prediction/traces files, which were removed.

## Observations

- samples_processed: 500
- avg_compiled_evidence_items: 19.888
- avg_build_tokens: 85393.566
- avg_build_think_tokens: 0.0
- avg_build_total_tokens: 85393.566
- build_token_accounting: logical cold-build visible LLM tokens; cached build chunks count from stored usage, while cache hits only avoid repeated local API calls.
- avg_build_memory_records: 115.818
- avg_active_build_memory_records: 102.2
- build_memory_temporal_fields: False
- build_memory_prompt_profile: typed_compact
- build_memory_manage_facts: True
- build_memory_overlap_turns: 0
- build_memory_cache_hits: 3341
- build_memory_cache_misses: 0
- build_memory_cache_writes: 0
- build_memory_source_alignment: {'enabled': True, 'window': 1, 'max_sources_per_record': 4, 'min_score': 2.0, 'min_delta': 1.5}
- build_memory_source_alignment_changed_records: 9456
- build_memory_source_alignment_added_sources: 12763
- avg_build_memory_source_alignment_changed_records: 18.912
- avg_build_memory_source_alignment_added_sources: 25.526
- avg_memory_hits: 8.424
- avg_memory_source_hits: 11.048
- build_memory_include_superseded: False
- build_memory_include_superseded_information_needs: ['temporal_lookup', 'list_count']
- avg_context_chars: 17774.128
- avg_query_tokens: 5186.944
- avg_query_think_tokens: 0.0
- avg_query_total_tokens: 5186.944
- token_accounting_note: avg_build_tokens / avg_query_tokens exclude explicit reasoning tokens when the provider reports them; avg_*_total_tokens include visible plus think tokens.
- retrieval_route_overrides: {'temporal_lookup': {'top_k': 32, 'max_top_k': 40, 'dense_top_k': 60, 'lexical_protect_top_n': 8, 'dense_protect_top_n': 32}}
- avg_effective_top_k: 37.072
- avg_effective_dense_top_k: 60.0
- avg_effective_dense_protect_top_n: 32.0
- dense_protect_top_n: 32
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
- rerank_enabled: True
- rerank_model: Qwen/Qwen3-Reranker-0.6B
- rerank_pool_k: 60
- rerank_anchor_keep: 8
- rerank_anchor_after_top: 16
- rerank_applied_count: 500
- rerank_applied_rate: 1.0
- avg_rerank_candidate_count: 60.0
- avg_rerank_returned_count: 37.072
- avg_rerank_tokens_when_applied: 14509.316
- embedding_cache_enabled: True
- embedding_cache_hits: 247238
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
- personalized_advice_contract_applied: 29
- structured_guide: True
- structured_guide_max_rows: 10
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
- update_conflict_guide_applied: 44
- current_state_update_contract: False
- dialogue_inference_contract: False
- temporal_order_contract: False
- source_anchor_keep: 0
- source_anchor_memory_rows: 0
- source_anchor_per_session: 0
- source_anchor_session_rows: 0
- route_overrides: {'temporal_lookup': {'max_evidence_items': 40, 'max_evidence_chars': 15000}}
- enable_recommendation_profile_patterns: True
- enable_advice_profile_patterns: False
- temporal_priority_over_recent: False
- answer_max_input_tokens: 131072
- answer_max_output_tokens: 16384
- answer_chat_template_kwargs: {'enable_thinking': False}
- answer_cache_enabled: True
- answer_cache_path: outputs/cache/qwen36_no_think_build4k_answer_v103_rerank_context.sqlite
- answer_cache_namespace: stage1_rerank_context_v103_qwen36_no_think_build4k
- answer_cache_hits: 0
- answer_cache_misses: 500
- answer_cache_writes: 500
- answer_finalizer_enabled: True
- answer_finalizer_mode: structured_evidence_mechanical
- answer_finalizer_enable_count_correction: False
- answer_finalizer_enable_evidence_report_count_correction: False
- answer_finalizer_enable_money_sum_correction: False
- answer_finalizer_enable_duration_rounding_correction: True
- answer_finalizer_enable_missing_detail: False
- answer_finalizer_enable_relative_time_calculation: True
- answer_finalizer_applied_count: 54
- answer_finalizer_applied_rate: 0.108
- answer_repair_enabled: False
- answer_repair_mode: openai_compatible
- answer_repair_model: Qwen/Qwen3.6-35B-A3B
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
- answer: OpenAI-compatible answerer using Qwen/Qwen3.6-35B-A3B at http://127.0.0.1:8000/v1 with temperature 0, max_input_tokens 131072, and max_output_tokens 16384, chat_template_kwargs {'enable_thinking': False}.

## Next Steps

- Use offline lexical, judge, and evidence-recall scripts to diagnose quality after prediction is complete.
- Compare typed build memory on/off before adding more expensive answer-time reasoning.
- Keep each new method behind explicit config toggles for ablation.
