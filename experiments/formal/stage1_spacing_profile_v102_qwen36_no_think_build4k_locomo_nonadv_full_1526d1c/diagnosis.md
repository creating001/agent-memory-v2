# Diagnosis for stage1_spacing_profile_v102_qwen36_no_think_build4k_locomo_nonadv_full_1526d1c

## Summary

This is the main-repo qwen3.6 no-thinking v102 LoCoMo non-adversarial full rerun. It uses the same clean raw-memory-granularity adaptive v102 algorithm as LongMemEval-S.

Prediction used commit `1526d1c`. The offline LoCoMo judge uses the current dual flash protocol: two independent `deepseek-v4-flash` runs with temperature `0` and default thinking. No prediction outputs were regenerated for judge-only changes.

DeepSeek dual judge:

- strict: `1196/1540 = 0.776623`
- lenient: `1229/1540 = 0.798052`
- flash run 1 / run 2: `1212/1540 = 0.787013` / `1213/1540 = 0.787662`
- invalid judgments: `0`
- judge agreement: `0.978571`
- judge thinking: flash run 1 default, flash run 2 default
- judge disagreement: run 1 WRONG / run 2 CORRECT `17`; run 1 CORRECT / run 2 WRONG `16`

Judge note: LoCoMo is `4` lenient-correct cases below the current `80%` baseline target under dual flash judge.

Cost:

- avg build tokens: `62015.574`
- avg query tokens: `5768.492`

Category breakdown:

| Category | Name | strict correct / total | strict accuracy | lenient correct / total | lenient accuracy |
|---:|---|---:|---:|---:|---:|
| 1 | Multi-Hop | 177/282 | 0.627660 | 195/282 | 0.691489 |
| 2 | Temporal Reasoning | 246/321 | 0.766355 | 250/321 | 0.778816 |
| 3 | Open-Domain | 43/96 | 0.447917 | 45/96 | 0.468750 |
| 4 | Single-Hop | 730/841 | 0.868014 | 739/841 | 0.878716 |

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
- avg_context_chars: 16309.37987012987
- avg_query_tokens: 5768.4915584415585
- avg_query_think_tokens: 0.0
- avg_query_total_tokens: 5768.4915584415585
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
- answer_chat_template_kwargs: {'enable_thinking': False}
- answer_cache_enabled: True
- answer_cache_path: outputs/cache/qwen36_no_think_build4k_answer_v102_spacing_profile.sqlite
- answer_cache_namespace: stage1_spacing_profile_v102_qwen36_no_think_build4k
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
- answer_finalizer_applied_count: 46
- answer_finalizer_applied_rate: 0.02987012987012987
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
