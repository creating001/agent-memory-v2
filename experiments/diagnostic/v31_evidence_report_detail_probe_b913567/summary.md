# v31_evidence_report_detail_probe_b913567

## Purpose

Stage-1 clean skeleton run: validate raw evidence storage, lexical retrieval, neighbor expansion, evidence compilation, answer generation, trace output, and experiment bookkeeping.

## Scope

- benchmark: mixed
- subset: route_stratified_20
- experiment_kind: diagnostic
- limit: None
- workers: 4
- input_path: /data/home_new/wujinqi/agent-memory/outputs/diagnostic/v30_route_stratified_probe/prediction_input.jsonl
- config_path: /data/home_new/wujinqi/agent-memory/configs/stage1_evidence_report_detail_v31_cached.json
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0, max_input_tokens 131072, and max_output_tokens 16384.

## Git

- inside_work_tree: True
- commit: b9135676074f63181e5b594b6b089682c2f9d7a3
- dirty: True
- note: None

## Metrics

- n_samples: 20
- accuracy: None
- gate_result: pass
- gate_note: no-label route-stratified diagnostic only; no gold/judge/category/sample id used by prediction.
- f1: None
- bleu: None
- avg_build_tokens: 63177.1
- build_token_accounting: logical cold-build LLM tokens; cached build chunks count from stored usage, while cache hits only avoid repeated local API calls.
- avg_query_tokens: 5152.6
- avg_compiled_evidence_items: 36.85
- build_memory_enabled: True
- build_memory_model: Qwen/Qwen3-30B-A3B-Instruct-2507
- build_memory_temporal_fields: False
- build_memory_cache_enabled: True
- build_memory_cache_path: outputs/cache/qwen3_build_memory.sqlite
- build_memory_cache_hits: 104
- build_memory_cache_misses: 24
- build_memory_cache_writes: 24
- avg_build_memory_records: 116.75
- avg_active_build_memory_records: 106.65
- avg_memory_hits: 11.95
- avg_memory_source_hits: 13.7
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
- embedding_cache_hits: 5440
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
- avg_context_chars: 16852.6
- compiler_prompt_mode: external_naive
- answer_mode: openai_compatible
- answer_model: Qwen/Qwen3-30B-A3B-Instruct-2507
- answer_max_input_tokens: 131072
- answer_max_output_tokens: 16384
- answer_output_format: json_answer
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
- prompt_detail_rules_present: 20/20 prompts include detailed evidence_report discipline
- prompt_plural_slot_rules_present: 7/20 prompts include list-style distinct item discipline
- route_overrides: {}
- enable_broad_list_patterns: False
- enable_recommendation_profile_patterns: True
- temporal_priority_over_recent: False

## Outputs

- predictions: /data/home_new/wujinqi/agent-memory/outputs/diagnostic/v31_evidence_report_detail_probe_b913567/predictions.jsonl
- traces: /data/home_new/wujinqi/agent-memory/outputs/diagnostic/v31_evidence_report_detail_probe_b913567/traces.jsonl
- metrics: /data/home_new/wujinqi/agent-memory/experiments/diagnostic/v31_evidence_report_detail_probe_b913567/metrics.json
- manifest: /data/home_new/wujinqi/agent-memory/experiments/diagnostic/v31_evidence_report_detail_probe_b913567/manifest.json

## Gate Conclusion

v31 no-label gate 通过。`compiler.evidence_report_detail=true` 已在 20 条 route-stratified mixed diagnostic 中全部生效，answer max input/output 保持 `131072/16384`，avg query tokens 为 `5152.6`，仍低于 6K 预算。build token 统计为 logical cold-build usage；本次 mixed probe 有 LME 样本导致 24 个 build cache miss，但 LoCoMo full 会复用 v29 build memory namespace，预期不会降低 v29 的 source activation 覆盖。

本诊断不计算 accuracy，也不读取 labels/gold/judge/category/sample id。下一步可以启动 LoCoMo non-adversarial full v31 prediction，然后离线 DeepSeek judge。

## Clean Notes

- No gold/reference/target answer, judge output, benchmark label, sample id, qid, or row index is passed into the prediction pipeline.
- Build-stage typed memory is generated only from raw dialogue and visible metadata; it is recorded separately from offline labels and judge outputs.
- Raw context remains available for fallback and diagnosis; build memory records keep source back-links when produced by the current builder.
- Accuracy is intentionally not computed by the prediction runner; any gold or judge metrics must be produced offline after prediction.
