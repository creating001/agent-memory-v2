# stage1_selected_context_v95_lme_s_full_790975f

## Purpose

Stage-1 clean skeleton run: validate raw evidence storage, lexical retrieval, neighbor expansion, evidence compilation, answer generation, trace output, and experiment bookkeeping.

## Scope

- benchmark: LongMemEval-S
- subset: full
- experiment_kind: formal
- limit: None
- workers: 8
- input_path: /data/home_new/wujinqi/agent-memory/outputs/prepare_longmemeval_s_cleaned/prediction_input.jsonl
- config_path: /data/home_new/wujinqi/agent-memory/configs/stage1_selected_context_v95_cached.json
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0, max_input_tokens 131072, and max_output_tokens 16384.

## Git

- inside_work_tree: True
- commit: 790975f88869979e4964f657895fb28251a88809
- dirty: False
- note: None

## Metrics

- n_samples: 500
- accuracy: None
- f1: None
- bleu: None
- avg_build_tokens: 80346.246
- build_token_accounting: logical cold-build LLM tokens; cached build chunks count from stored usage, while cache hits only avoid repeated local API calls.
- avg_query_tokens: 7441.176
- avg_compiled_evidence_items: 42.714
- retrieval_route_overrides: {'temporal_lookup': {'top_k': 40, 'max_top_k': 40, 'dense_top_k': 40, 'lexical_protect_top_n': 0, 'dense_protect_top_n': 32}}
- avg_effective_top_k: 53.56
- avg_effective_dense_top_k: 53.56
- avg_effective_dense_protect_top_n: 42.848
- build_memory_enabled: True
- build_memory_model: Qwen/Qwen3-30B-A3B-Instruct-2507
- build_memory_temporal_fields: False
- build_memory_prompt_profile: typed_compact
- build_memory_manage_facts: True
- build_memory_overlap_turns: 0
- build_memory_cache_enabled: True
- build_memory_cache_path: outputs/cache/qwen3_build_memory.sqlite
- build_memory_cache_hits: 3341
- build_memory_cache_misses: 0
- build_memory_cache_writes: 0
- build_memory_source_alignment: {}
- build_memory_source_alignment_changed_records: 0
- build_memory_source_alignment_added_sources: 0
- avg_build_memory_source_alignment_changed_records: 0.0
- avg_build_memory_source_alignment_added_sources: 0.0
- avg_build_memory_records: 129.662
- avg_active_build_memory_records: 116.456
- avg_memory_hits: 8.236
- avg_memory_source_hits: 7.924
- build_memory_include_superseded: False
- build_memory_include_superseded_information_needs: ['temporal_lookup', 'list_count']
- neighbor_order: hit_priority
- drop_query_stopwords: True
- lexical_enabled: True
- dense_enabled: True
- lexical_protect_top_n: 0
- dense_protect_top_n: 48
- dense_document_text_mode: external_naive
- dense_query_text_mode: external_naive
- embedding_cache_enabled: True
- embedding_cache_path: outputs/cache/qwen3_embedding.sqlite
- embedding_cache_hits: 247238
- embedding_cache_misses: 0
- embedding_cache_writes: 0
- turn_window_bm25_enabled: False
- turn_window_top_k: None
- turn_window_window_before: None
- turn_window_window_after: None
- turn_window_max_sources_per_window: None
- turn_window_max_chars_per_turn: None
- turn_window_enabled_route_signals: None
- turn_window_enabled_information_needs: None
- turn_window_enabled_query_patterns: None
- turn_window_bm25_applied_count: 0
- turn_window_bm25_applied_rate: 0.0
- avg_turn_window_hits: 0.0
- avg_turn_window_source_hits: 0.0
- selected_context_enabled: True
- selected_context_window_before: 1
- selected_context_window_after: 1
- selected_context_max_rows: 10
- selected_context_max_neighbor_chars: 160
- selected_context_information_needs: ['fact_lookup', 'list_count', 'profile_preference']
- selected_context_require_anaphora: True
- selected_context_applied_count: 317
- selected_context_applied_rate: 0.634
- avg_selected_context_materialized_rows: 6.34
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
- rerank_token_accounting: rerank model tokens are reported separately and are not included in build/query LLM token budgets.
- avg_embedding_tokens: 0.0
- avg_context_chars: 24269.166
- compiler_prompt_mode: external_naive
- compiler_memory_record_source: retrieval
- avg_compiled_memory_records: 0.0
- answer_mode: openai_compatible
- answer_model: Qwen/Qwen3-30B-A3B-Instruct-2507
- answer_max_input_tokens: 131072
- answer_max_output_tokens: 16384
- answer_output_format: json_answer
- answer_cache_enabled: True
- answer_cache_path: outputs/cache/qwen3_answer_v95_selected_context.sqlite
- answer_cache_namespace: stage1_selected_context_v95_qwen3_30b
- answer_cache_hits: 0
- answer_cache_misses: 500
- answer_cache_writes: 500
- answer_finalizer_enabled: True
- answer_finalizer_mode: structured_evidence_mechanical
- answer_finalizer_enable_count_correction: False
- answer_finalizer_enable_evidence_report_count_correction: False
- answer_finalizer_enable_money_sum_correction: False
- answer_finalizer_enable_duration_rounding_correction: True
- answer_finalizer_enable_missing_detail: False
- answer_finalizer_enable_relative_time_calculation: True
- answer_finalizer_applied_count: 1
- answer_finalizer_applied_rate: 0.002
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
- answer_repair_enable_profile_preference_trigger: False
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
- scoped_evidence_enabled: False
- scoped_evidence_information_needs: None
- scoped_evidence_max_rows: None
- scoped_evidence_max_row_chars: None
- scoped_evidence_applied_count: 0
- scoped_evidence_applied_rate: 0.0
- scoped_evidence_total_extraction_query_tokens: 0
- scoped_evidence_avg_extraction_query_tokens_when_applied: None
- scoped_evidence_total_answer_query_tokens: 0
- scoped_evidence_avg_answer_query_tokens_when_applied: None
- scoped_evidence_avg_extraction_prompt_chars_when_applied: None
- scoped_evidence_avg_answer_prompt_chars_when_applied: None
- scoped_evidence_avg_evidence_json_chars_when_applied: None
- scoped_evidence_extraction_cache_hits: 0
- scoped_evidence_extraction_cache_misses: 0
- scoped_evidence_extraction_cache_writes: 0
- scoped_evidence_answer_cache_hits: 0
- scoped_evidence_answer_cache_misses: 0
- scoped_evidence_answer_cache_writes: 0
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
- enable_broad_list_patterns: True
- enable_recommendation_profile_patterns: True
- enable_advice_profile_patterns: False
- temporal_priority_over_recent: False

## Outputs

- predictions: /data/home_new/wujinqi/agent-memory/outputs/formal/stage1_selected_context_v95_lme_s_full_790975f/predictions.jsonl
- traces: /data/home_new/wujinqi/agent-memory/outputs/formal/stage1_selected_context_v95_lme_s_full_790975f/traces.jsonl
- metrics: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_selected_context_v95_lme_s_full_790975f/metrics.json
- manifest: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_selected_context_v95_lme_s_full_790975f/manifest.json

## Clean Notes

- No gold/reference/target answer, judge output, benchmark label, sample id, qid, or row index is passed into the prediction pipeline.
- Build-stage typed memory is generated only from raw dialogue and visible metadata; it is recorded separately from offline labels and judge outputs.
- Raw context remains available for fallback and diagnosis; build memory records keep source back-links when produced by the current builder.
- Accuracy is intentionally not computed by the prediction runner; any gold or judge metrics must be produced offline after prediction.

## DeepSeek Judge

- accuracy: `386/500 = 0.772`
- invalid judgments: `0`
- judge model: `deepseek-v4-flash`
- judge tokens: `118960`
- judge output: `/data/home_new/wujinqi/agent-memory/experiments/formal/stage1_selected_context_v95_lme_s_full_790975f/deepseek_judge.json`

## Token Gate

- avg_query_tokens: `7441.176`
- avg_build_tokens: `80346.246`
- verdict: over mainline budget. This run is useful as diagnostic evidence, but it cannot replace the current LME mainline result because it exceeds the `<= 6K` avg query-token budget.

## 对比 v88

- baseline: `stage1_evidence_answer_detail_v88_lme_s_full_55b8177`
- v88 accuracy: `400/500 = 0.800`
- v95 delta: `-14` correct
- prediction_changed: `184/500`
- changed-prediction subset: `WRONG->CORRECT 18`，`CORRECT->WRONG 34`，净 `-16`
- overall transitions: `WRONG->CORRECT 20`，`CORRECT->WRONG 34`，`CORRECT->CORRECT 366`，`WRONG->WRONG 80`
- comparison file: `/data/home_new/wujinqi/agent-memory/experiments/formal/stage1_selected_context_v95_lme_s_full_790975f/judge_comparison_vs_v88.json`

## Evidence Recall

- evidence_recall: `1.0`
- evidence recall output: `/data/home_new/wujinqi/agent-memory/experiments/formal/stage1_selected_context_v95_lme_s_full_790975f/evidence_recall.json`

## 结论

v95 在 LongMemEval-S full 上明显负向且超预算：accuracy 只有 `0.772`，低于 v88 的 `0.800`，avg_query_tokens `7441.176` 超过 6K 主线预算。evidence recall 仍为 `1.0`，说明主要问题不是召回缺失，而是 selected local context / top60 budget 增加了 reader 噪声，导致 LME 的答案使用稳定性下降。

因此，v95 只能作为 LoCoMo 正向、LME 负向的分叉诊断，不能作为统一主线方法。下一步应做 token-safe 收窄：例如回到 LME top40/evidence budget，减少 `selected_context.max_rows`，或将 broad collection routing 与 selected_context 拆开消融。
