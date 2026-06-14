# v86_chronological_context_lme_qtext311_d7bd5e2

## Purpose

Stage-1 clean skeleton run: validate raw evidence storage, lexical retrieval, neighbor expansion, evidence compilation, answer generation, trace output, and experiment bookkeeping.

本次诊断测试 v86 chronological session-thread layout：在 v83 基础上不改变 build/retrieval/answer 主体，只对 question-text router 得到的 `list_count`、`temporal_lookup`、`current_state` 开启按 session/date/turn 展示的 Memory Context。设计参考 LongMemEval 官方 generation 的 retrieved turn chronological formatting，以及 EverOS/SimpleMem/xMemory 的 source episode/thread 回链思想；取舍是只改变已选中证据的组织顺序，不引入额外 LLM、gold、judge、benchmark 标签、sample id 或样本级规则。

## Scope

- benchmark: LongMemEval-S
- subset: qtext_agg_time_current_311
- experiment_kind: diagnostic
- limit: None
- workers: 8
- input_path: /data/home_new/wujinqi/agent-memory/outputs/diagnostic_inputs/lme_qtext_agg_time_current.jsonl
- config_path: /data/home_new/wujinqi/agent-memory/configs/stage1_chronological_context_v86_diag.json
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0, max_input_tokens 131072, and max_output_tokens 16384.

## Git

- inside_work_tree: True
- commit: d7bd5e2ef2ad4059c9bd7b4dd289a07e72c983a7
- dirty: False
- note: None

## Metrics

- n_samples: 311
- accuracy: None
- f1: None
- bleu: None
- avg_build_tokens: 80023.63344051447
- build_token_accounting: logical cold-build LLM tokens; cached build chunks count from stored usage, while cache hits only avoid repeated local API calls.
- avg_query_tokens: 6464.823151125402
- avg_compiled_evidence_items: 33.79421221864952
- retrieval_route_overrides: {}
- avg_effective_top_k: 40.0
- avg_effective_dense_top_k: 40.0
- avg_effective_dense_protect_top_n: 32.0
- build_memory_enabled: True
- build_memory_model: Qwen/Qwen3-30B-A3B-Instruct-2507
- build_memory_temporal_fields: False
- build_memory_prompt_profile: typed_compact
- build_memory_manage_facts: True
- build_memory_overlap_turns: 0
- build_memory_cache_enabled: True
- build_memory_cache_path: outputs/cache/qwen3_build_memory.sqlite
- build_memory_cache_hits: 2068
- build_memory_cache_misses: 0
- build_memory_cache_writes: 0
- build_memory_source_alignment: {}
- build_memory_source_alignment_changed_records: 0
- build_memory_source_alignment_added_sources: 0
- avg_build_memory_source_alignment_changed_records: 0.0
- avg_build_memory_source_alignment_added_sources: 0.0
- avg_build_memory_records: 129.02250803858522
- avg_active_build_memory_records: 116.36977491961414
- avg_memory_hits: 8.27331189710611
- avg_memory_source_hits: 7.80064308681672
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
- embedding_cache_hits: 153045
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
- avg_context_chars: 21394.797427652735
- compiler_prompt_mode: external_naive
- compiler_memory_record_source: retrieval
- avg_compiled_memory_records: 0.0
- answer_mode: openai_compatible
- answer_model: Qwen/Qwen3-30B-A3B-Instruct-2507
- answer_max_input_tokens: 131072
- answer_max_output_tokens: 16384
- answer_output_format: json_answer
- answer_cache_enabled: True
- answer_cache_path: outputs/cache/qwen3_answer_v42_operation_workpad.sqlite
- answer_cache_namespace: stage1_chronological_context_v86_qwen3_30b
- answer_cache_hits: 0
- answer_cache_misses: 311
- answer_cache_writes: 311
- answer_finalizer_enabled: True
- answer_finalizer_mode: structured_evidence_mechanical
- answer_finalizer_enable_count_correction: False
- answer_finalizer_enable_evidence_report_count_correction: False
- answer_finalizer_enable_money_sum_correction: False
- answer_finalizer_enable_duration_rounding_correction: False
- answer_finalizer_enable_missing_detail: True
- answer_finalizer_applied_count: 17
- answer_finalizer_applied_rate: 0.05466237942122187
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
- temporal_event_contract: False
- temporal_workpad_scope: route
- temporal_workpad_max_rows: 12
- temporal_workpad_max_pairs: 12
- operation_workpad_question_gate: False
- personalized_advice_contract: True
- personalized_advice_contract_applied: 4
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
- update_conflict_guide: True
- update_conflict_guide_information_needs: ['current_state', 'fact_lookup']
- update_conflict_guide_max_rows: 6
- update_conflict_guide_snippet_chars: 180
- update_conflict_guide_applied: 37
- current_state_update_contract: False
- dialogue_inference_contract: False
- temporal_order_contract: False
- source_anchor_keep: 0
- source_anchor_memory_rows: 0
- source_anchor_per_session: 0
- source_anchor_session_rows: 0
- route_overrides: {'current_state': {'context_layout': 'chronological_session_thread'}, 'list_count': {'context_layout': 'chronological_session_thread'}, 'temporal_lookup': {'context_layout': 'chronological_session_thread'}}
- enable_broad_list_patterns: False
- enable_recommendation_profile_patterns: True
- enable_advice_profile_patterns: False
- temporal_priority_over_recent: False

## Outputs

- predictions: /data/home_new/wujinqi/agent-memory/outputs/diagnostic/v86_chronological_context_lme_qtext311_d7bd5e2/predictions.jsonl
- traces: /data/home_new/wujinqi/agent-memory/outputs/diagnostic/v86_chronological_context_lme_qtext311_d7bd5e2/traces.jsonl
- metrics: /data/home_new/wujinqi/agent-memory/experiments/diagnostic/v86_chronological_context_lme_qtext311_d7bd5e2/metrics.json
- manifest: /data/home_new/wujinqi/agent-memory/experiments/diagnostic/v86_chronological_context_lme_qtext311_d7bd5e2/manifest.json

## Clean Notes

- No gold/reference/target answer, judge output, benchmark label, sample id, qid, or row index is passed into the prediction pipeline.
- Build-stage typed memory is generated only from raw dialogue and visible metadata; it is recorded separately from offline labels and judge outputs.
- Raw context remains available for fallback and diagnosis; build memory records keep source back-links when produced by the current builder.
- Accuracy is intentionally not computed by the prediction runner; any gold or judge metrics must be produced offline after prediction.

## Offline Judge

- judge: DeepSeek `deepseek-v4-flash`
- accuracy: `230/311 = 0.7395498392`
- invalid: `0`
- judge_tokens: `72347`

## Same-Subset Comparison

- vs v83 `stage1_personalized_advice_contract_v83_lme_s_full_65eebda`: `239/311 -> 230/311`, delta `-9`; transitions `WRONG->CORRECT 18`, `CORRECT->WRONG 27`; prediction_changed `102/311`.
- vs v80 `stage1_update_conflict_guide_v80_lme_s_full_152b0e5`: `236/311 -> 230/311`, delta `-6`; transitions `WRONG->CORRECT 21`, `CORRECT->WRONG 27`; prediction_changed `112/311`.

## Conclusion

不跑 full。v86 有局部收益，例如项目数、医生前一天睡觉时间、旧球鞋 current state、Starbucks stars、omelette eggs 等；但全局 route-scoped chronological layout 引入更多 list/count 回退，尤其在模型需要保留检索 rank 中多个分散证据时，会漏掉高相关 items。query token 也从 v83 same-311 `6216.273` 增加到 `6464.823`，不适合作为主线。
