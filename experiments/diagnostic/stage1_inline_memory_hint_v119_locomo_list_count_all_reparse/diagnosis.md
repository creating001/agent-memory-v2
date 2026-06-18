# Diagnosis for stage1_inline_memory_hint_v119_locomo_list_count_all_reparse

## Summary

The run validates pipeline shape, clean traceability, and answerer integration under the configured experiment kind.

## Observations

- samples_processed: 270
- avg_compiled_evidence_items: 58.403703703703705
- avg_build_tokens: 62924.62222222222
- avg_build_think_tokens: 0.0
- avg_build_total_tokens: 62924.62222222222
- build_token_accounting: logical cold-build visible LLM tokens; cached build chunks count from stored usage, while cache hits only avoid repeated local API calls.
- avg_build_memory_records: 152.77407407407406
- avg_active_build_memory_records: 143.9148148148148
- build_memory_temporal_fields: False
- build_memory_prompt_profile: typed_compact
- build_memory_manage_facts: True
- build_memory_overlap_turns: 0
- build_memory_cache_hits: 2206
- build_memory_cache_misses: 0
- build_memory_cache_writes: 0
- build_memory_source_alignment: {}
- build_memory_source_alignment_changed_records: 0
- build_memory_source_alignment_added_sources: 0
- avg_build_memory_source_alignment_changed_records: 0.0
- avg_build_memory_source_alignment_added_sources: 0.0
- avg_memory_hits: 19.881481481481483
- avg_memory_source_hits: 26.118518518518517
- build_memory_include_superseded: False
- build_memory_include_superseded_information_needs: ['temporal_lookup', 'list_count']
- avg_context_chars: 18217.87037037037
- avg_query_tokens: 6401.966666666666
- avg_query_think_tokens: 0.0
- avg_query_total_tokens: 6401.966666666666
- token_accounting_note: avg_build_tokens / avg_query_tokens exclude explicit reasoning tokens when the provider reports them; avg_*_total_tokens include visible plus think tokens.
- retrieval_route_overrides: {'temporal_lookup': {'top_k': 40, 'max_top_k': 40, 'dense_top_k': 40, 'lexical_protect_top_n': 0, 'dense_protect_top_n': 32}}
- avg_effective_top_k: 60.0
- avg_effective_dense_top_k: 60.0
- avg_effective_dense_protect_top_n: 48.0
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
- selected_context_applied_count: 270
- selected_context_applied_rate: 1.0
- avg_selected_context_materialized_rows: 6.0
- avg_selected_context_skipped_long_center_rows: 0.8518518518518519
- rerank_enabled: False
- rerank_model: None
- rerank_pool_k: None
- rerank_document_text_mode: turn
- rerank_document_neighbor_window: None
- rerank_document_max_memory_records: None
- rerank_anchor_keep: None
- rerank_anchor_after_top: None
- rerank_applied_count: 0
- rerank_applied_rate: 0.0
- avg_rerank_candidate_count: None
- avg_rerank_returned_count: None
- avg_rerank_tokens_when_applied: None
- embedding_cache_enabled: True
- embedding_cache_hits: 6152
- embedding_cache_misses: 0
- evidence_order: retrieval
- memory_record_source: evidence_rows
- avg_compiled_memory_records: 20.633333333333333
- memory_order: question_overlap
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
- route_overrides: {'temporal_lookup': {'max_evidence_items': 40, 'max_evidence_chars': 18000}, 'fact_lookup': {'grounded_inference_contract': True, 'grounded_inference_gate': 'modal_only'}, 'profile_preference': {'grounded_inference_contract': True, 'grounded_inference_gate': 'modal_only'}, 'list_count': {'max_memory_records': 24, 'structured_guide_memory_hints': True, 'structured_guide_max_memory_hints_per_row': 1, 'structured_guide_memory_hint_chars': 60}, 'current_state': {'grounded_inference_contract': True, 'grounded_inference_gate': 'modal_only'}}
- enable_recommendation_profile_patterns: True
- enable_advice_profile_patterns: False
- temporal_priority_over_recent: False
- answer_max_input_tokens: 131072
- answer_max_output_tokens: 16384
- answer_chat_template_kwargs: {'enable_thinking': False}
- answer_cache_enabled: True
- answer_cache_path: outputs/cache/qwen36_no_think_build4k_answer_v119_inline_memory_hint.sqlite
- answer_cache_namespace: stage1_inline_memory_hint_v119_qwen36_no_think_build4k
- answer_cache_hits: 270
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
- answer_finalizer_applied_count: 0
- answer_finalizer_applied_rate: 0.0
- answer_repair_enabled: False
- answer_repair_mode: openai_compatible
- answer_repair_model: Qwen/Qwen3.6-35B-A3B
- answer_repair_max_input_tokens: 131072
- answer_repair_max_output_tokens: 16384
- answer_repair_information_needs: None
- answer_repair_enable_profile_preference_trigger: False
- answer_repair_enable_modal_abstention_trigger: False
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

## Dual Flash Judge Result

- Scope: LoCoMo non-adversarial clean `list_count` route-all diagnostic, 270 samples selected only by current question-text router.
- v116 selected baseline: strict/lenient `0.677778 / 0.729630`.
- v119 inline memory hint: strict/lenient `0.670370 / 0.700000`.
- Answer changed vs v116: `121/270`.
- Strict gain/loss vs v116: `11/13`.
- Lenient gain/loss vs v116: `9/17`.
- Output path: `outputs/diagnostic/stage1_inline_memory_hint_v119_locomo_list_count_all_reparse/`.

Conclusion: rejected. The source-linked inline memory hint is clean but worsens LoCoMo list/count route accuracy and should not be promoted to full evaluation.

## Parser Guard Note

- This reparse run used the generic `json_answer` format guard that salvages only clear short answer markers from malformed JSON/reasoning loops.
- The guard fixed two abnormal long answers in this diagnostic (`d2d34434abced78cb8ad6a26` -> `at least 2 completed`; `a40f38e0cc3f4b0fed43494f` -> insufficient).
- The token usage remains the original cached API usage; parser reparse does not reduce already incurred completion tokens.
