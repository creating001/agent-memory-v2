# Diagnosis for v31_evidence_report_detail_probe_b913567

## Summary

v31 no-label gate 通过。该诊断只使用 route-stratified prediction input，不读取 labels/gold/judge/category/sample id。目的不是评估 accuracy，而是确认 v31 query-side detailed evidence_report 可以正常运行、token 不超预算、prompt 规则可追溯。

## Observations

- samples_processed: 20
- avg_compiled_evidence_items: 36.85
- avg_build_tokens: 63177.1
- build_token_accounting: logical cold-build LLM tokens; cached build chunks count from stored usage, while cache hits only avoid repeated local API calls.
- avg_build_memory_records: 116.75
- avg_active_build_memory_records: 106.65
- build_memory_temporal_fields: False
- build_memory_cache_hits: 104
- build_memory_cache_misses: 24
- build_memory_cache_writes: 24
- avg_memory_hits: 11.95
- avg_memory_source_hits: 13.7
- build_memory_include_superseded: False
- build_memory_include_superseded_information_needs: ['temporal_lookup', 'list_count']
- avg_context_chars: 16852.6
- avg_query_tokens: 5152.6
- dense_protect_top_n: 32
- session_bm25_enabled: False
- session_bm25_top_k: None
- session_anchor_top_k: None
- session_enabled_route_signals: None
- session_bm25_applied_count: 0
- session_bm25_applied_rate: 0.0
- embedding_cache_enabled: True
- embedding_cache_hits: 5440
- embedding_cache_misses: 0
- evidence_order: retrieval
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
- evidence_report_max_items: 12
- evidence_report_detail: True
- route_overrides: {}
- enable_recommendation_profile_patterns: True
- temporal_priority_over_recent: False
- answer_max_input_tokens: 131072
- answer_max_output_tokens: 16384
- answer_cache_enabled: True
- answer_cache_path: outputs/cache/qwen3_answer_v31.sqlite
- answer_cache_namespace: stage1_evidence_report_detail_v31_qwen3_30b
- answer_cache_hits: 0
- answer_cache_misses: 20
- answer_cache_writes: 20
- answer_finalizer_enabled: False
- answer_finalizer_mode: structured_evidence_mechanical
- answer_finalizer_enable_count_correction: False
- answer_finalizer_enable_money_sum_correction: True
- answer_finalizer_applied_count: 0
- answer_finalizer_applied_rate: 0.0
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0, max_input_tokens 131072, and max_output_tokens 16384.

## Gate Checks

- prediction rows: `20/20`
- trace rows: `20/20`
- `evidence_report_detail`: `True`
- detailed evidence rules present: `20/20` prompts
- plural/list slot rules present: `7/20` prompts
- avg query tokens: `5152.6`, below 6K budget
- answer max input/output: `131072/16384`
- build_memory_temporal_fields: `False`, intentionally reusing v29 build memory semantics
- build memory namespace: v29 source-preserving namespace from config
- build token accounting: logical cold-build usage, cache hits do not make method cost zero

The diagnostic includes LME and LoCoMo samples, so build cache misses (`24`) are expected and do not imply LoCoMo full will rebuild everything. The key check is that v31 does not reduce retrieval/source activation by changing build memory; the only intended method change is query-side evidence discipline.

## Decision

Proceed to LoCoMo non-adversarial full v31 prediction. This is a query-side method, so running LoCoMo full first is the right expensive validation. LongMemEval full should follow only if LoCoMo shows a positive or at least non-regressive signal, because v31 primarily targets LoCoMo evidence-hit wrong cases.

## Next Steps

- Run LoCoMo non-adversarial full with `configs/stage1_evidence_report_detail_v31_cached.json`.
- After prediction completes, run offline DeepSeek judge and evidence recall.
- Compare primarily to v29, because v31 preserves v29 build/retrieval and changes compiler discipline only.
