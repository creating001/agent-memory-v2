# v41_llm_question_router_lme_probe_243452f

## Purpose

Stage-1 clean skeleton run: validate raw evidence storage, lexical retrieval, neighbor expansion, evidence compilation, answer generation, trace output, and experiment bookkeeping.

## Scope

- benchmark: longmemeval_s
- subset: route_stratified_20
- experiment_kind: diagnostic
- limit: None
- workers: 4
- input_path: /data/home_new/wujinqi/agent-memory/outputs/diagnostic/v35_lme_route_stratified_probe/prediction_input.jsonl
- config_path: /data/home_new/wujinqi/agent-memory/configs/stage1_llm_question_router_v41_cached.json
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0, max_input_tokens 131072, and max_output_tokens 16384.

## Git

- inside_work_tree: True
- commit: 243452f6e5e1664cf04e1a840da990600cf3979e
- dirty: True
- note: None

## Metrics

- n_samples: 20
- accuracy: None
- f1: None
- bleu: None
- avg_build_tokens: 81690.45
- build_token_accounting: logical cold-build LLM tokens; cached build chunks count from stored usage, while cache hits only avoid repeated local API calls.
- avg_query_tokens: 5837.55
- question_analysis_enabled: True
- question_analysis_model: Qwen/Qwen3-30B-A3B-Instruct-2507
- question_analysis_avg_query_tokens: 331.05
- question_analysis_route_changed_count: 6
- question_analysis_cache_hits: 0
- question_analysis_cache_misses: 20
- question_analysis_cache_writes: 20
- avg_compiled_evidence_items: 33.9
- retrieval_route_overrides: {}
- avg_effective_top_k: 40.0
- avg_effective_dense_top_k: 40.0
- avg_effective_dense_protect_top_n: 32.0
- build_memory_enabled: True
- build_memory_model: Qwen/Qwen3-30B-A3B-Instruct-2507
- build_memory_temporal_fields: False
- build_memory_cache_enabled: True
- build_memory_cache_path: outputs/cache/qwen3_build_memory.sqlite
- build_memory_cache_hits: 137
- build_memory_cache_misses: 0
- build_memory_cache_writes: 0
- avg_build_memory_records: 130.95
- avg_active_build_memory_records: 117.5
- avg_memory_hits: 5.55
- avg_memory_source_hits: 5.45
- build_memory_include_superseded: False
- build_memory_include_superseded_information_needs: ['temporal_lookup', 'list_count']
- neighbor_order: hit_priority
- drop_query_stopwords: True
- lexical_enabled: True
- dense_enabled: True
- lexical_protect_top_n: 0
- dense_protect_top_n: 32
- dense_document_text_mode: external_naive
- dense_query_text_mode: external_naive
- embedding_cache_enabled: True
- embedding_cache_path: outputs/cache/qwen3_embedding.sqlite
- embedding_cache_hits: 10079
- embedding_cache_misses: 0
- embedding_cache_writes: 0
- session_bm25_enabled: False
- session_bm25_top_k: None
- session_anchor_top_k: None
- session_max_anchor_hits: None
- session_protect_turn_hits: None
- session_enabled_route_signals: None
- session_enabled_information_needs: None
- session_enabled_query_patterns: None
- session_bm25_applied_count: 0
- session_bm25_applied_rate: 0.0
- avg_embedding_tokens: 0.0
- avg_context_chars: 18731.7
- compiler_prompt_mode: external_naive
- compiler_memory_record_source: retrieval
- avg_compiled_memory_records: 0.0
- answer_mode: openai_compatible
- answer_model: Qwen/Qwen3-30B-A3B-Instruct-2507
- answer_max_input_tokens: 131072
- answer_max_output_tokens: 16384
- answer_output_format: json_answer
- answer_cache_enabled: True
- answer_cache_path: outputs/cache/qwen3_answer_v41_llm_question_router.sqlite
- answer_cache_namespace: stage1_llm_question_router_v41_qwen3_30b
- answer_cache_hits: 0
- answer_cache_misses: 20
- answer_cache_writes: 20
- answer_finalizer_enabled: True
- answer_finalizer_mode: structured_evidence_mechanical
- answer_finalizer_enable_count_correction: False
- answer_finalizer_enable_money_sum_correction: False
- answer_finalizer_enable_duration_rounding_correction: True
- answer_finalizer_applied_count: 0
- answer_finalizer_applied_rate: 0.0
- answer_repair_enabled: False
- answer_repair_mode: openai_compatible
- answer_repair_model: Qwen/Qwen3-30B-A3B-Instruct-2507
- answer_repair_max_input_tokens: 131072
- answer_repair_max_output_tokens: 16384
- answer_repair_output_format: json_answer
- answer_repair_information_needs: None
- answer_repair_enable_uncertain_trigger: True
- answer_repair_enable_short_list_trigger: True
- answer_repair_enable_temporal_conflict_trigger: True
- answer_repair_max_context_chars: 14000
- answer_repair_max_row_text_chars: 700
- answer_repair_cache_enabled: False
- answer_repair_cache_path: None
- answer_repair_cache_namespace: None
- answer_repair_cache_hits: 0
- answer_repair_cache_misses: 0
- answer_repair_cache_writes: 0
- answer_repair_triggered_count: 0
- answer_repair_triggered_rate: 0.0
- answer_repair_applied_count: 0
- answer_repair_applied_rate: 0.0
- answer_repair_total_query_tokens: 0
- answer_repair_avg_query_tokens_when_triggered: None
- answer_style: concise
- evidence_order: retrieval
- memory_order: retrieval
- memory_layout: flat
- row_text_mode: full
- max_row_text_chars: 0
- evidence_row_labels: False
- final_answer_checklist: False
- max_memory_records: 0
- route_guidance: False
- temporal_grounding: False
- temporal_hints: False
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
- route_overrides: {}
- enable_broad_list_patterns: False
- enable_recommendation_profile_patterns: True
- temporal_priority_over_recent: False

## Gate Conclusion

- prediction_gate: passed, 20/20 predictions completed.
- token_gate: passed for diagnostic, avg_query_tokens `5837.55` and max_query_tokens `6959`; answer max input/output was `131072/16384`.
- question_analysis_overhead: avg `331.05` query tokens/sample, route_changed `6/20`.
- same20_judge_vs_v36: v36 `14/20`, v41 `14/20`, delta `0`.
- prompt_clean_scan: only `category` appeared, and both occurrences were ordinary raw dialogue text, not hidden benchmark metadata.
- decision: do not run LongMemEval-S full from this gate; v41 adds token overhead without diagnostic accuracy gain.

## Outputs

- predictions: /data/home_new/wujinqi/agent-memory/outputs/diagnostic/v41_llm_question_router_lme_probe_243452f/predictions.jsonl
- traces: /data/home_new/wujinqi/agent-memory/outputs/diagnostic/v41_llm_question_router_lme_probe_243452f/traces.jsonl
- metrics: /data/home_new/wujinqi/agent-memory/experiments/diagnostic/v41_llm_question_router_lme_probe_243452f/metrics.json
- manifest: /data/home_new/wujinqi/agent-memory/experiments/diagnostic/v41_llm_question_router_lme_probe_243452f/manifest.json
- deepseek_judge: /data/home_new/wujinqi/agent-memory/experiments/diagnostic/v41_llm_question_router_lme_probe_243452f/deepseek_judge.json
- comparison_vs_v36: /data/home_new/wujinqi/agent-memory/experiments/diagnostic/v41_llm_question_router_lme_probe_243452f/judge_comparison_vs_v36_same20.json
- prompt_clean_scan: /data/home_new/wujinqi/agent-memory/experiments/diagnostic/v41_llm_question_router_lme_probe_243452f/prompt_clean_scan.json

## Clean Notes

- No gold/reference/target answer, judge output, benchmark label, sample id, qid, or row index is passed into the prediction pipeline.
- Build-stage typed memory is generated only from raw dialogue and visible metadata; it is recorded separately from offline labels and judge outputs.
- Raw context remains available for fallback and diagnosis; build memory records keep source back-links when produced by the current builder.
- Accuracy is intentionally not computed by the prediction runner; any gold or judge metrics must be produced offline after prediction.
