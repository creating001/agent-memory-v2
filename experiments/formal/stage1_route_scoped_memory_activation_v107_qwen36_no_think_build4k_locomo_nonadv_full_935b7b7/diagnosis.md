# Diagnosis for stage1_route_scoped_memory_activation_v107_qwen36_no_think_build4k_locomo_nonadv_full_935b7b7

## Summary

This formal LoCoMo non-adversarial full run evaluates v107 route-scoped typed memory activation with the same algorithm used for the v107 LongMemEval-S full run. It ties v102 on lenient accuracy but is not a new LTS.

Dual `deepseek-v4-flash` judge:

- strict: `1193/1540 = 0.774675`
- lenient: `1229/1540 = 0.798052`
- flash_1: `1213/1540 = 0.787662`
- flash_2: `1209/1540 = 0.785065`
- judge agreement: `0.976623`

Compared with current qwen3.6 v102 LTS LoCoMo strict/lenient `0.776623 / 0.798052`, v107 keeps lenient unchanged and loses 3 strict-correct examples. It does not reach the `0.800000` baseline target.

## Observations

- samples_processed: 1540
- avg_compiled_evidence_items: 55.263636363636365
- avg_build_tokens: 62015.57402597403
- avg_build_think_tokens: 0.0
- avg_build_total_tokens: 62015.57402597403
- build_token_accounting: logical cold-build visible LLM tokens; cached build chunks count from stored usage, while cache hits only avoid repeated local API calls.
- avg_build_memory_records: 150.91493506493507
- avg_active_build_memory_records: 141.86818181818182
- build_memory_temporal_fields: False
- build_memory_prompt_profile: typed_compact
- build_memory_manage_facts: True
- build_memory_overlap_turns: 0
- build_memory_cache_hits: 12411
- build_memory_cache_misses: 0
- build_memory_cache_writes: 0
- build_memory_source_alignment: {}
- build_memory_source_alignment_changed_records: 0
- build_memory_source_alignment_added_sources: 0
- avg_build_memory_source_alignment_changed_records: 0.0
- avg_build_memory_source_alignment_added_sources: 0.0
- avg_memory_hits: 19.857792207792208
- avg_memory_source_hits: 25.93831168831169
- build_memory_include_superseded: False
- build_memory_include_superseded_information_needs: ['temporal_lookup', 'list_count']
- avg_context_chars: 16912.448051948053
- avg_query_tokens: 5961.069480519481
- avg_query_think_tokens: 0.0
- avg_query_total_tokens: 5961.069480519481
- token_accounting_note: avg_build_tokens / avg_query_tokens exclude explicit reasoning tokens when the provider reports them; avg_*_total_tokens include visible plus think tokens.
- retrieval_route_overrides: {'temporal_lookup': {'top_k': 40, 'max_top_k': 40, 'dense_top_k': 40, 'lexical_protect_top_n': 0, 'dense_protect_top_n': 32}}
- avg_effective_top_k: 55.61038961038961
- avg_effective_dense_top_k: 55.61038961038961
- avg_effective_dense_protect_top_n: 44.48831168831169
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
- selected_context_applied_count: 1198
- selected_context_applied_rate: 0.7779220779220779
- avg_selected_context_materialized_rows: 4.667532467532467
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
- embedding_cache_hits: 7422
- embedding_cache_misses: 0
- evidence_order: retrieval
- memory_record_source: retrieval
- avg_compiled_memory_records: 2.4603896103896106
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
- update_conflict_guide_applied: 0
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
- answer_cache_hits: 11
- answer_cache_misses: 1529
- answer_cache_writes: 1529
- answer_finalizer_enabled: True
- answer_finalizer_mode: structured_evidence_mechanical
- answer_finalizer_enable_count_correction: False
- answer_finalizer_enable_evidence_report_count_correction: False
- answer_finalizer_enable_money_sum_correction: False
- answer_finalizer_enable_duration_rounding_correction: True
- answer_finalizer_enable_missing_detail: False
- answer_finalizer_enable_relative_time_calculation: True
- answer_finalizer_applied_count: 44
- answer_finalizer_applied_rate: 0.02857142857142857
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

## Dual Judge By Category

| Category | Name | strict | lenient | n |
|---:|---|---:|---:|---:|
| 1 | Multi-Hop | `178/282 = 0.631206` | `202/282 = 0.716312` | 282 |
| 2 | Temporal Reasoning | `239/321 = 0.744548` | `243/321 = 0.757009` | 321 |
| 3 | Open-Domain | `45/96 = 0.468750` | `48/96 = 0.500000` | 96 |
| 4 | Single-Hop | `731/841 = 0.869203` | `736/841 = 0.875149` | 841 |

## Comparison With v102

Lenient dual-judge comparison against current qwen3.6 v102 LTS:

- gain: `51`
- loss: `51`
- net: `0`

Category deltas:

- Multi-Hop: `+7`
- Temporal Reasoning: `-7`
- Open-Domain: `+3`
- Single-Hop: `-3`

Route deltas from gain/loss:

- gains: fact_lookup `28`, list_count `19`, temporal_lookup `3`, profile_preference `1`
- losses: fact_lookup `22`, temporal_lookup `13`, list_count `12`, profile_preference `4`

Main diagnosis:

- Route-scoped activation has real local signal: Multi-Hop and Open-Domain improve.
- The same change creates enough temporal/profile noise to cancel the gains on Temporal Reasoning and Single-Hop.
- Since LoCoMo lenient is tied and strict is lower, v107 should not replace v102.

## Next Steps

- Keep v102 as LTS.
- Use v107 as evidence that route-scoped build memory activation can help Multi-Hop/Open-Domain, but direct reader-prompt activation is too unstable.
- Next candidate should target LoCoMo Temporal/Single-Hop regressions while preserving v107's Multi-Hop/Open-Domain gains, or move build memory use out of the reader prompt into source-selection/evidence-unit rerank with coverage guarantees.
