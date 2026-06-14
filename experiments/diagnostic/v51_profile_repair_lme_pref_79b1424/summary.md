# v51_profile_repair_lme_pref_79b1424

## Purpose

Stage-1 clean skeleton run: validate raw evidence storage, lexical retrieval, neighbor expansion, evidence compilation, answer generation, trace output, and experiment bookkeeping.

## Scope

- benchmark: longmemeval_s
- subset: single_session_preference_30
- experiment_kind: diagnostic
- limit: None
- workers: 4
- input_path: /data/home_new/wujinqi/agent-memory/outputs/diagnostic/v50_lme_single_session_preference_input/prediction_input.jsonl
- config_path: /data/home_new/wujinqi/agent-memory/configs/stage1_profile_repair_v51_cached.json
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0, max_input_tokens 131072, and max_output_tokens 16384.

## Git

- inside_work_tree: True
- commit: 79b1424e5f50727dc4b30a0e6e722de771dc45ad
- dirty: True
- note: None

## Metrics

- n_samples: 30
- accuracy: None
- f1: None
- bleu: None
- avg_build_tokens: 79618.66666666667
- build_token_accounting: logical cold-build LLM tokens; cached build chunks count from stored usage, while cache hits only avoid repeated local API calls.
- avg_query_tokens: 8382.666666666666
- question_analysis_enabled: False
- question_analysis_model: None
- question_analysis_avg_query_tokens: 0.0
- question_analysis_route_changed_count: 0
- question_analysis_cache_hits: 0
- question_analysis_cache_misses: 0
- question_analysis_cache_writes: 0
- avg_compiled_evidence_items: 37.733333333333334
- retrieval_route_overrides: {}
- avg_effective_top_k: 40.0
- avg_effective_dense_top_k: 40.0
- avg_effective_dense_protect_top_n: 32.0
- build_memory_enabled: True
- build_memory_model: Qwen/Qwen3-30B-A3B-Instruct-2507
- build_memory_temporal_fields: False
- build_memory_cache_enabled: True
- build_memory_cache_path: outputs/cache/qwen3_build_memory.sqlite
- build_memory_cache_hits: 199
- build_memory_cache_misses: 0
- build_memory_cache_writes: 0
- avg_build_memory_records: 129.03333333333333
- avg_active_build_memory_records: 111.7
- avg_memory_hits: 6.966666666666667
- avg_memory_source_hits: 6.3
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
- embedding_cache_hits: 14764
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
- avg_context_chars: 16780.566666666666
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
- answer_cache_namespace: stage1_operation_workpad_v42_qwen3_30b
- answer_cache_hits: 7
- answer_cache_misses: 23
- answer_cache_writes: 23
- answer_finalizer_enabled: True
- answer_finalizer_mode: structured_evidence_mechanical
- answer_finalizer_enable_count_correction: False
- answer_finalizer_enable_evidence_report_count_correction: False
- answer_finalizer_enable_money_sum_correction: False
- answer_finalizer_enable_duration_rounding_correction: True
- answer_finalizer_applied_count: 0
- answer_finalizer_applied_rate: 0.0
- answer_repair_enabled: True
- answer_repair_mode: openai_compatible
- answer_repair_model: Qwen/Qwen3-30B-A3B-Instruct-2507
- answer_repair_max_input_tokens: 131072
- answer_repair_max_output_tokens: 16384
- answer_repair_output_format: json_answer
- answer_repair_information_needs: ['profile_preference']
- answer_repair_enable_uncertain_trigger: False
- answer_repair_enable_short_list_trigger: False
- answer_repair_enable_temporal_conflict_trigger: False
- answer_repair_enable_profile_preference_trigger: True
- answer_repair_max_context_chars: 14000
- answer_repair_max_row_text_chars: 700
- answer_repair_cache_enabled: True
- answer_repair_cache_path: outputs/cache/qwen3_profile_repair_v51.sqlite
- answer_repair_cache_namespace: stage1_profile_repair_v51_qwen3_30b
- answer_repair_cache_hits: 0
- answer_repair_cache_misses: 23
- answer_repair_cache_writes: 23
- answer_repair_triggered_count: 23
- answer_repair_triggered_rate: 0.7666666666666667
- answer_repair_applied_count: 6
- answer_repair_applied_rate: 0.2
- answer_repair_total_query_tokens: 96495
- answer_repair_avg_query_tokens_when_triggered: 4195.434782608696
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
- aggregation_report_contract: False
- aggregation_report_information_needs: None
- candidate_guide: False
- candidate_guide_information_needs: None
- candidate_guide_max_rows: 6
- candidate_guide_snippet_chars: 160
- route_overrides: {}
- enable_broad_list_patterns: False
- enable_recommendation_profile_patterns: True
- enable_advice_profile_patterns: True
- temporal_priority_over_recent: False

## Outputs

- predictions: /data/home_new/wujinqi/agent-memory/outputs/diagnostic/v51_profile_repair_lme_pref_79b1424/predictions.jsonl
- traces: /data/home_new/wujinqi/agent-memory/outputs/diagnostic/v51_profile_repair_lme_pref_79b1424/traces.jsonl
- metrics: /data/home_new/wujinqi/agent-memory/experiments/diagnostic/v51_profile_repair_lme_pref_79b1424/metrics.json
- manifest: /data/home_new/wujinqi/agent-memory/experiments/diagnostic/v51_profile_repair_lme_pref_79b1424/manifest.json

## Clean Notes

- No gold/reference/target answer, judge output, benchmark label, sample id, qid, or row index is passed into the prediction pipeline.
- Build-stage typed memory is generated only from raw dialogue and visible metadata; it is recorded separately from offline labels and judge outputs.
- Raw context remains available for fallback and diagnosis; build memory records keep source back-links when produced by the current builder.
- Accuracy is intentionally not computed by the prediction runner; any gold or judge metrics must be produced offline after prediction.

## 人工结论

v51 是一个 query-side 诊断候选，不是可直接 full 的主线候选。它基于 v42，不改变 build/retrieval/compiler evidence context，只做两点可消融改动：

- 把通用 advice/tips/should-I 类问题路由到 `profile_preference`。
- 只对 `profile_preference` 启用第二阶段 answer repair，让模型从已检索 Memory Context 中重新抽取偏好、约束、已有资源、当前问题和过往经验。

方法参考：

- `external/creating001-agent-memory` 的 query 侧 evidence extraction -> answer 思路，以及 preference requirement 中对 preferences / dislikes / constraints / owned resources / prior experiences 的覆盖；不迁移其中任何 benchmark label、answer、target support、sample id 或样本级 finalizer/guardrail。
- `external/SimpleMem` 的 multi-view context + concise JSON answer。
- `external/MIRIX` / `external/memobase` 的 profile/event/provenance 组织思想。

离线 DeepSeek judge 结果：

- v51：`16/30 = 0.533333`。
- v42 same30：`13/30 = 0.433333`。
- v50 same30：`12/30 = 0.400000`。
- v51 vs v42：gain/loss `6/3`，net `+3`。
- repair applied：`6/30`；这 6 条 draft judge 为 `0/6`，repair final judge 为 `3/6`，repair 净 `+3`，没有 draft-correct -> final-wrong。

成本和决策：

- avg_build_tokens：`79618.667`，build cache 全命中但按 logical cold-build usage 计入成本。
- avg_query_tokens：`8382.667`，超过 8K diagnostic 边界，主要来自 `23` 次 repair，repair triggered 平均 `4195.435` query tokens。
- 因此 v51 不跑 LongMemEval full，不进入主线配置；下一步要保留“repair 确实有效”的信号，但必须做 token-safe 版本，例如更窄触发、先做轻量 profile-anchor extraction、或压缩 repair Memory Context。

离线诊断文件：

- DeepSeek judge：`experiments/diagnostic/v51_profile_repair_lme_pref_79b1424/deepseek_judge.json`
- vs v42/v50 comparison：`experiments/diagnostic/v51_profile_repair_lme_pref_79b1424/judge_comparison_vs_v42_v50_same30.json`
- repair draft vs final：`experiments/diagnostic/v51_profile_repair_lme_pref_79b1424/repair_applied_draft_vs_final.json`
- prompt clean scan：`experiments/diagnostic/v51_profile_repair_lme_pref_79b1424/prompt_clean_scan.json`
