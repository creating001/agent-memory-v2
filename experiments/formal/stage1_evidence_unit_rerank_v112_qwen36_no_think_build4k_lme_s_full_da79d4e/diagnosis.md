# Diagnosis for stage1_evidence_unit_rerank_v112_qwen36_no_think_build4k_lme_s_full_da79d4e

## Summary

The run validates pipeline shape, clean traceability, and answerer integration under the configured experiment kind.

## Observations

- samples_processed: 500
- avg_compiled_evidence_items: 33.274
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
- build_memory_source_alignment: {}
- build_memory_source_alignment_changed_records: 0
- build_memory_source_alignment_added_sources: 0
- avg_build_memory_source_alignment_changed_records: 0.0
- avg_build_memory_source_alignment_added_sources: 0.0
- avg_memory_hits: 8.424
- avg_memory_source_hits: 9.684
- build_memory_include_superseded: False
- build_memory_include_superseded_information_needs: ['temporal_lookup', 'list_count']
- avg_context_chars: 19997.066
- avg_query_tokens: 6210.196
- avg_query_think_tokens: 0.0
- avg_query_total_tokens: 6210.196
- token_accounting_note: avg_build_tokens / avg_query_tokens exclude explicit reasoning tokens when the provider reports them; avg_*_total_tokens include visible plus think tokens.
- retrieval_route_overrides: {'temporal_lookup': {'top_k': 40, 'max_top_k': 40, 'dense_top_k': 40, 'lexical_protect_top_n': 0, 'dense_protect_top_n': 32}}
- avg_effective_top_k: 40.0
- avg_effective_dense_top_k: 48.8
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
- avg_selected_context_skipped_long_center_rows: 0.0
- rerank_enabled: True
- rerank_model: Qwen/Qwen3-Reranker-0.6B
- rerank_pool_k: 60
- rerank_document_text_mode: turn_with_neighbors_and_memory
- rerank_document_neighbor_window: 1
- rerank_document_max_memory_records: 3
- rerank_anchor_keep: 32
- rerank_anchor_after_top: 8
- rerank_applied_count: 220
- rerank_applied_rate: 0.44
- avg_rerank_candidate_count: 60.0
- avg_rerank_returned_count: 40.0
- avg_rerank_tokens_when_applied: 22933.1
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
- update_conflict_guide_applied: 42
- current_state_update_contract: False
- dialogue_inference_contract: False
- temporal_order_contract: False
- source_anchor_keep: 0
- source_anchor_memory_rows: 0
- source_anchor_per_session: 0
- source_anchor_session_rows: 0
- route_overrides: {'temporal_lookup': {'max_evidence_items': 40, 'max_evidence_chars': 18000}, 'fact_lookup': {'grounded_inference_contract': True, 'grounded_inference_gate': 'modal_only'}, 'profile_preference': {'grounded_inference_contract': True, 'grounded_inference_gate': 'modal_only'}, 'current_state': {'grounded_inference_contract': True, 'grounded_inference_gate': 'modal_only'}}
- enable_recommendation_profile_patterns: True
- enable_advice_profile_patterns: False
- temporal_priority_over_recent: False
- answer_max_input_tokens: 131072
- answer_max_output_tokens: 16384
- answer_chat_template_kwargs: {'enable_thinking': False}
- answer_cache_enabled: True
- answer_cache_path: outputs/cache/qwen36_no_think_build4k_answer_v112_evidence_unit_rerank.sqlite
- answer_cache_namespace: stage1_evidence_unit_rerank_v112_qwen36_no_think_build4k
- answer_cache_hits: 280
- answer_cache_misses: 220
- answer_cache_writes: 220
- answer_finalizer_enabled: True
- answer_finalizer_mode: structured_evidence_mechanical
- answer_finalizer_enable_count_correction: False
- answer_finalizer_enable_evidence_report_count_correction: False
- answer_finalizer_enable_money_sum_correction: False
- answer_finalizer_enable_duration_rounding_correction: True
- answer_finalizer_enable_missing_detail: False
- answer_finalizer_enable_relative_time_calculation: True
- answer_finalizer_applied_count: 21
- answer_finalizer_applied_rate: 0.042
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

## Offline Dual Flash Judge Result

v112 is negative on LongMemEval-S full:

- strict `405/500 = 0.810000`
- lenient `414/500 = 0.828000`
- v102 LTS lenient: `415/500 = 0.830000`
- v110 candidate lenient: `417/500 = 0.834000`
- judge agreement: `0.982`; no invalid judgments.

By question type, lenient counts are:

- knowledge-update: `71/78 = 0.910256`
- multi-session: `104/133 = 0.781955`
- single-session-assistant: `52/56 = 0.928571`
- single-session-preference: `14/30 = 0.466667`
- single-session-user: `65/70 = 0.928571`
- temporal-reasoning: `108/133 = 0.812030`

Compared with v110, v112 has lenient gain/loss `12/15`, net `-3`. True answer text changed `82/500`; all changed answers are from rerank-applied samples. Within changed answers, lenient gain/loss is `11/12`; unchanged answers still show `1/3` gain/loss from dual-judge variance.

Changed-answer gain/loss by type:

- knowledge-update: `+6 / -0`
- multi-session: `+1 / -3`
- single-session-assistant: `+0 / -1`
- single-session-preference: `+2 / -2`
- single-session-user: `+0 / -1`
- temporal-reasoning: `+2 / -5`

Interpretation:

- The rerank document is cleaner than v103's single-turn document, but rerank still changes enough row order to hurt multi-session and temporal coverage.
- The strongest positive signal is knowledge-update, but it is not enough to offset temporal/multi-session losses.
- Keeping `anchor_keep=32` was not sufficient as a coverage guarantee; future rerank should either rerank only inside already selected coverage groups or operate as a secondary compiler signal instead of changing final raw-row order.
- Do not run LoCoMo full for v112.
