# Diagnosis for stage1_route_scoped_memory_activation_v107_qwen36_no_think_build4k_lme_s_full_12a80f2

## Summary

This formal LongMemEval-S full run evaluates v107 route-scoped typed memory activation. It ties v102 on the main lenient metric but does not improve LME.

Dual `deepseek-v4-flash` judge:

- strict: `405/500 = 0.810000`
- lenient: `415/500 = 0.830000`
- flash_1: `410/500 = 0.820000`
- flash_2: `410/500 = 0.820000`
- judge agreement: `0.980000`

Compared with current qwen3.6 v102 LTS LongMemEval-S strict/lenient `0.814000 / 0.830000`, v107 keeps lenient unchanged but loses 2 strict-correct examples. Because lenient is the main metric and LoCoMo is the current target gap, v107 should still be evaluated on LoCoMo before final rejection.

## Observations

- samples_processed: 500
- avg_compiled_evidence_items: 34.752
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
- avg_context_chars: 20116.74
- avg_query_tokens: 6308.482
- avg_query_think_tokens: 0.0
- avg_query_total_tokens: 6308.482
- token_accounting_note: avg_build_tokens / avg_query_tokens exclude explicit reasoning tokens when the provider reports them; avg_*_total_tokens include visible plus think tokens.
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
- avg_selected_context_skipped_long_center_rows: 0.0
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
- embedding_cache_hits: 247238
- embedding_cache_misses: 0
- evidence_order: retrieval
- memory_record_source: retrieval
- avg_compiled_memory_records: 1.374
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
- personalized_advice_contract_applied: 29
- structured_guide: True
- structured_guide_max_rows: 12
- structured_guide_include_rows: True
- structured_guide_include_memory: True
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
- route_overrides: {'temporal_lookup': {'max_evidence_items': 40, 'max_evidence_chars': 18000}, 'fact_lookup': {'max_memory_records': 4}, 'profile_preference': {'max_memory_records': 6}}
- enable_recommendation_profile_patterns: True
- enable_advice_profile_patterns: False
- temporal_priority_over_recent: False
- answer_max_input_tokens: 131072
- answer_max_output_tokens: 16384
- answer_chat_template_kwargs: {'enable_thinking': False}
- answer_cache_enabled: True
- answer_cache_path: outputs/cache/qwen36_no_think_build4k_answer_v107_route_scoped_memory_activation.sqlite
- answer_cache_namespace: stage1_route_scoped_memory_activation_v107_qwen36_no_think_build4k
- answer_cache_hits: 2
- answer_cache_misses: 498
- answer_cache_writes: 498
- answer_finalizer_enabled: True
- answer_finalizer_mode: structured_evidence_mechanical
- answer_finalizer_enable_count_correction: False
- answer_finalizer_enable_evidence_report_count_correction: False
- answer_finalizer_enable_money_sum_correction: False
- answer_finalizer_enable_duration_rounding_correction: True
- answer_finalizer_enable_missing_detail: False
- answer_finalizer_enable_relative_time_calculation: True
- answer_finalizer_applied_count: 57
- answer_finalizer_applied_rate: 0.114
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

## Dual Judge By Type

| question_type | strict | lenient | n |
|---|---:|---:|---:|
| knowledge-update | `66/78 = 0.846154` | `67/78 = 0.858974` | 78 |
| multi-session | `101/133 = 0.759398` | `104/133 = 0.781955` | 133 |
| single-session-assistant | `50/56 = 0.892857` | `51/56 = 0.910714` | 56 |
| single-session-preference | `10/30 = 0.333333` | `13/30 = 0.433333` | 30 |
| single-session-user | `66/70 = 0.942857` | `68/70 = 0.971429` | 70 |
| temporal-reasoning | `112/133 = 0.842105` | `112/133 = 0.842105` | 133 |

## Comparison With v102

Lenient dual-judge comparison against current qwen3.6 v102 LTS:

- gain: `17`
- loss: `17`
- net: `0`

Route-level deltas:

- current_state: `+1`
- fact_lookup: `-3`
- list_count: `+1`
- profile_preference: `0`
- temporal_lookup: `+1`

Main diagnosis:

- Route-scoped activation removed the large temporal/list losses from v106 and reduced avg query tokens to `6308.482`.
- The expected fact/profile improvement did not hold on the full run; `fact_lookup` is net `-3`, while temporal/list/current changed only via downstream answer variation despite no activation on those routes.
- LME main lenient metric is unchanged, so the candidate is not an LME improvement. Its only remaining reason to continue is possible LoCoMo gain, especially because LoCoMo is currently just below the baseline target.

## Next Steps

- Run LoCoMo non-adversarial full for v107 because LME lenient is tied with v102 and LoCoMo is the current target gap.
- If LoCoMo does not improve enough to offset the LME strict/token cost, reject v107.
- For future memory use, prefer source-selection or evidence-unit rerank with coverage guarantees over direct reader prompt memory guides.
