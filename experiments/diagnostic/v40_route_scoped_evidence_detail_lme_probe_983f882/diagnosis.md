# Diagnosis for v40_route_scoped_evidence_detail_lme_probe_983f882

## Summary

The run validates pipeline shape, clean traceability, and answerer integration under the configured experiment kind.

Gate decision: pass. v40 keeps v36 retrieval budget and only enables detailed evidence_report rules for question-derived `list_count` and `temporal_lookup`. It is ready for LongMemEval-S full; LoCoMo should wait until LME full is not clearly negative.

## Observations

- samples_processed: 20
- avg_compiled_evidence_items: 33.9
- avg_build_tokens: 81690.45
- build_token_accounting: logical cold-build LLM tokens; cached build chunks count from stored usage, while cache hits only avoid repeated local API calls.
- avg_build_memory_records: 130.95
- avg_active_build_memory_records: 117.5
- build_memory_temporal_fields: False
- build_memory_cache_hits: 137
- build_memory_cache_misses: 0
- build_memory_cache_writes: 0
- avg_memory_hits: 5.5
- avg_memory_source_hits: 5.35
- build_memory_include_superseded: False
- build_memory_include_superseded_information_needs: ['temporal_lookup', 'list_count']
- avg_context_chars: 19421.0
- avg_query_tokens: 5714.0
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
- embedding_cache_enabled: True
- embedding_cache_hits: 10079
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
- route_overrides: {'list_count': {'evidence_report_detail': True}, 'temporal_lookup': {'evidence_report_detail': True}}
- enable_recommendation_profile_patterns: True
- temporal_priority_over_recent: False
- answer_max_input_tokens: 131072
- answer_max_output_tokens: 16384
- answer_cache_enabled: True
- answer_cache_path: outputs/cache/qwen3_answer_v40_route_scoped_evidence_detail.sqlite
- answer_cache_namespace: stage1_route_scoped_evidence_detail_v40_qwen3_30b
- answer_cache_hits: 15
- answer_cache_misses: 5
- answer_cache_writes: 5
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
- answer_repair_information_needs: None
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

## Route Audit

| information_need | n | top_k | dense_top_k | avg query tokens | max query tokens | avg rows | avg build tokens | detail prompts |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| current_state | 4 | 40 | 40 | 6086.25 | 6253 | 28.75 | 75279.75 | 0/4 |
| fact_lookup | 4 | 40 | 40 | 5125.75 | 5301 | 37.00 | 88507.25 | 0/4 |
| list_count | 4 | 40 | 40 | 5627.00 | 5867 | 33.75 | 81862.00 | 4/4 |
| profile_preference | 4 | 40 | 40 | 5286.75 | 5575 | 36.00 | 81177.75 | 0/4 |
| temporal_lookup | 4 | 40 | 40 | 6444.25 | 6888 | 34.00 | 81625.50 | 4/4 |

Additional checks:

- total_build_tokens: `1633809`
- total_query_tokens: `114280`
- max_query_tokens: `6888`
- weighted LME full avg query estimate: `5716.6965`
- compiled memory records: `0.0`
- answer finalizer applied: `0/20`
- answer repair triggered: `0/20`
- prompt clean scan: `question_type=0`, `sample_id=0`, `qid=0`, `row index=0`, `gold answer=0`, `judge output=0`
- v40 detail rule does not contain the word `category`; any remaining occurrence is raw dialogue text, not hidden benchmark metadata.

## Next Steps

- Run LongMemEval-S full with the same config and commit lineage.
- Use DeepSeek judge accuracy as the main quality metric.
- Do not run LoCoMo full unless LME full is not clearly negative versus v36.
