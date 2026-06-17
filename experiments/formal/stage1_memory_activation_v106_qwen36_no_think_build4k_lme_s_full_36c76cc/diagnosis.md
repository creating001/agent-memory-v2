# Diagnosis for stage1_memory_activation_v106_qwen36_no_think_build4k_lme_s_full_36c76cc

## Summary

This formal LongMemEval-S full run evaluates v106 typed memory activation without changing v102 raw-row ordering. It is a negative result and is not an LTS candidate.

Dual `deepseek-v4-flash` judge:

- strict: `403/500 = 0.806000`
- lenient: `410/500 = 0.820000`
- flash_1: `406/500 = 0.812000`
- flash_2: `407/500 = 0.814000`
- judge agreement: `0.986000`

Compared with current qwen3.6 v102 LTS LongMemEval-S strict/lenient `0.814000 / 0.830000`, v106 is still worse. LoCoMo full should not be run for this candidate.

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
- avg_context_chars: 20927.638
- avg_query_tokens: 6638.526
- avg_query_think_tokens: 0.0
- avg_query_total_tokens: 6638.526
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
- avg_compiled_memory_records: 4.532
- memory_order: question_overlap
- memory_layout: flat
- row_text_mode: full
- max_row_text_chars: 0
- evidence_row_labels: False
- final_answer_checklist: False
- max_memory_records: 4
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
- route_overrides: {'temporal_lookup': {'max_evidence_items': 40, 'max_evidence_chars': 18000, 'max_memory_records': 6}, 'list_count': {'max_memory_records': 6}, 'profile_preference': {'max_memory_records': 6}, 'current_state': {'max_memory_records': 6}}
- enable_recommendation_profile_patterns: True
- enable_advice_profile_patterns: False
- temporal_priority_over_recent: False
- answer_max_input_tokens: 131072
- answer_max_output_tokens: 16384
- answer_chat_template_kwargs: {'enable_thinking': False}
- answer_cache_enabled: True
- answer_cache_path: outputs/cache/qwen36_no_think_build4k_answer_v106_memory_activation.sqlite
- answer_cache_namespace: stage1_memory_activation_v106_qwen36_no_think_build4k
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
- answer_finalizer_applied_count: 60
- answer_finalizer_applied_rate: 0.12
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
| knowledge-update | `67/78 = 0.858974` | `68/78 = 0.871795` | 78 |
| multi-session | `100/133 = 0.751880` | `102/133 = 0.766917` | 133 |
| single-session-assistant | `52/56 = 0.928571` | `53/56 = 0.946429` | 56 |
| single-session-preference | `12/30 = 0.400000` | `15/30 = 0.500000` | 30 |
| single-session-user | `65/70 = 0.928571` | `65/70 = 0.928571` | 70 |
| temporal-reasoning | `107/133 = 0.804511` | `107/133 = 0.804511` | 133 |

## Comparison With v102

Lenient dual-judge comparison against current qwen3.6 v102 LTS:

- gain: `19`
- loss: `24`
- net: `-5`

Gain distribution:

- knowledge-update: `6`
- single-session-preference: `4`
- multi-session: `3`
- temporal-reasoning: `3`
- single-session-assistant: `2`
- single-session-user: `1`

Loss distribution:

- temporal-reasoning: `8`
- multi-session: `7`
- single-session-preference: `3`
- single-session-user: `2`
- knowledge-update: `2`
- single-session-assistant: `2`

Main diagnosis:

- Removing `memory_aware` ordering fixed the largest v105 failure: avg evidence rows returned to v102 level (`34.752`).
- Activation-only still raises avg context chars from v102 `19759.110` to `20927.638` and avg query tokens from `6137.344` to `6638.526`.
- The typed memory guide gives localized gains on knowledge-update and preference questions, but it also introduces enough competing abstraction/noise to hurt temporal and multi-session examples.
- Current conclusion: do not expose typed memory guide directly in the answer prompt for LME. Build memory should remain a retrieval/control signal unless the next design can use it without increasing reader noise.

## Next Steps

- Do not run LoCoMo full for v106; it already underperforms v102 on LongMemEval-S full.
- Stop direct activated-memory prompt experiments for now.
- Next direction should use build memory outside the final reader prompt, for example evidence-unit retrieval/rerank with raw-row coverage guarantees, or conflict/coverage diagnostics that decide whether to keep v102 context unchanged.
