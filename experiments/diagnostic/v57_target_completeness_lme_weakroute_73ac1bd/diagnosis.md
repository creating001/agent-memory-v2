# Diagnosis for v57_target_completeness_lme_weakroute_73ac1bd

## Summary

The run validates pipeline shape, clean traceability, and answerer integration under the configured experiment kind.

## Observations

- samples_processed: 87
- avg_compiled_evidence_items: 33.91954022988506
- avg_build_tokens: 80991.86206896552
- build_token_accounting: logical cold-build LLM tokens; cached build chunks count from stored usage, while cache hits only avoid repeated local API calls.
- avg_build_memory_records: 130.98850574712642
- avg_active_build_memory_records: 117.41379310344827
- build_memory_temporal_fields: False
- build_memory_prompt_profile: typed_compact
- build_memory_manage_facts: True
- build_memory_overlap_turns: 0
- build_memory_cache_hits: 585
- build_memory_cache_misses: 0
- build_memory_cache_writes: 0
- avg_memory_hits: 8.620689655172415
- avg_memory_source_hits: 8.298850574712644
- build_memory_include_superseded: False
- build_memory_include_superseded_information_needs: ['temporal_lookup', 'list_count']
- avg_context_chars: 21466.080459770114
- avg_query_tokens: 6270.574712643678
- question_analysis_enabled: False
- question_analysis_model: None
- question_analysis_avg_query_tokens: 0.0
- question_analysis_route_changed_count: 0
- question_analysis_cache_hits: 0
- question_analysis_cache_misses: 0
- question_analysis_cache_writes: 0
- retrieval_route_overrides: {}
- avg_effective_top_k: 40.0
- avg_effective_dense_top_k: 40.0
- avg_effective_dense_protect_top_n: 32.0
- dense_protect_top_n: 32
- session_bm25_enabled: False
- session_bm25_top_k: None
- session_anchor_top_k: None
- session_enabled_route_signals: None
- session_bm25_applied_count: 0
- session_bm25_applied_rate: 0.0
- turn_window_bm25_enabled: False
- turn_window_top_k: None
- turn_window_window_before: None
- turn_window_window_after: None
- turn_window_max_sources_per_window: None
- turn_window_bm25_applied_count: 0
- turn_window_bm25_applied_rate: 0.0
- avg_turn_window_hits: 0.0
- avg_turn_window_source_hits: 0.0
- embedding_cache_enabled: True
- embedding_cache_hits: 43433
- embedding_cache_misses: 0
- evidence_order: retrieval
- memory_record_source: retrieval
- avg_compiled_memory_records: 0.0
- memory_order: retrieval
- memory_layout: flat
- row_text_mode: full
- max_row_text_chars: 0
- evidence_row_labels: False
- final_answer_checklist: True
- max_memory_records: 0
- route_guidance: False
- temporal_workpad: True
- temporal_text_normalization: True
- temporal_event_contract: False
- temporal_workpad_scope: route
- temporal_workpad_max_rows: 12
- temporal_workpad_max_pairs: 12
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
- route_overrides: {}
- enable_recommendation_profile_patterns: True
- enable_advice_profile_patterns: False
- temporal_priority_over_recent: False
- answer_max_input_tokens: 131072
- answer_max_output_tokens: 16384
- answer_cache_enabled: True
- answer_cache_path: outputs/cache/qwen3_answer_v57_target_completeness.sqlite
- answer_cache_namespace: stage1_target_completeness_v57_qwen3_30b
- answer_cache_hits: 0
- answer_cache_misses: 87
- answer_cache_writes: 87
- answer_finalizer_enabled: True
- answer_finalizer_mode: structured_evidence_mechanical
- answer_finalizer_enable_count_correction: False
- answer_finalizer_enable_evidence_report_count_correction: False
- answer_finalizer_enable_money_sum_correction: False
- answer_finalizer_enable_duration_rounding_correction: True
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

## Offline Judge Result

- judge_model: deepseek-v4-flash
- accuracy: 59/87 = 0.678161
- v42_same87_accuracy: 59/87 = 0.678161
- v56_same87_accuracy: 57/87 = 0.655172
- gain_loss_vs_v42: 5/5
- answer_changed_vs_v42: 28
- query_token_delta_avg_vs_v42: +260.333
- current_query_over_6000_count: 53
- current_query_over_8000_count: 0
- judge_output: /data/home_new/wujinqi/agent-memory/experiments/diagnostic/v57_target_completeness_lme_weakroute_73ac1bd/deepseek_judge.json
- comparison_output: /data/home_new/wujinqi/agent-memory/experiments/diagnostic/v57_target_completeness_lme_weakroute_73ac1bd/judge_comparison_vs_v42_same87.json

## Gate Conclusion

v57 does not pass the diagnostic gate. The target-completeness checklist changed 28 answers but ended exactly tied with v42 on accuracy, with symmetric gain/loss and higher query cost. Because avg query tokens rose above the 6K budget and there is no net accuracy gain, do not run full; keep only the experiment snapshot and delete the top-level candidate config.

## Next Steps

- Analyze the v57 gain/loss cases before adding any new answer-side discipline.
- Prioritize external-code-backed retrieval or memory organization changes that can improve evidence precision without increasing answer prompt length.
- Keep each new method behind explicit config toggles for ablation and run diagnostic only after the design is justified.
