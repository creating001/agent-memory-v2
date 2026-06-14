# v52_profile_uncertain_repair_lme_pref_aa0f67c

## Purpose

Stage-1 clean skeleton run: validate raw evidence storage, lexical retrieval, neighbor expansion, evidence compilation, answer generation, trace output, and experiment bookkeeping.

## Scope

- benchmark: longmemeval_s
- subset: single_session_preference_30
- experiment_kind: diagnostic
- limit: None
- workers: 4
- input_path: /data/home_new/wujinqi/agent-memory/outputs/diagnostic/v50_lme_single_session_preference_input/prediction_input.jsonl
- config_path: /data/home_new/wujinqi/agent-memory/configs/stage1_profile_uncertain_repair_v52_cached.json
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0, max_input_tokens 131072, and max_output_tokens 16384.

## Git

- inside_work_tree: True
- commit: aa0f67c1bcee70433013f497a237d4166495f230
- dirty: True
- note: None

## Metrics

- n_samples: 30
- accuracy: None
- f1: None
- bleu: None
- avg_build_tokens: 79618.66666666667
- build_token_accounting: logical cold-build LLM tokens; cached build chunks count from stored usage, while cache hits only avoid repeated local API calls.
- avg_query_tokens: 5954.533333333334
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
- answer_cache_hits: 30
- answer_cache_misses: 0
- answer_cache_writes: 0
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
- answer_repair_enable_uncertain_trigger: True
- answer_repair_enable_short_list_trigger: False
- answer_repair_enable_temporal_conflict_trigger: False
- answer_repair_enable_profile_preference_trigger: False
- answer_repair_max_context_chars: 14000
- answer_repair_max_row_text_chars: 700
- answer_repair_cache_enabled: True
- answer_repair_cache_path: outputs/cache/qwen3_profile_repair_v52.sqlite
- answer_repair_cache_namespace: stage1_profile_uncertain_repair_v52_qwen3_30b
- answer_repair_cache_hits: 0
- answer_repair_cache_misses: 6
- answer_repair_cache_writes: 6
- answer_repair_triggered_count: 6
- answer_repair_triggered_rate: 0.2
- answer_repair_applied_count: 5
- answer_repair_applied_rate: 0.16666666666666666
- answer_repair_total_query_tokens: 23651
- answer_repair_avg_query_tokens_when_triggered: 3941.8333333333335
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

- predictions: /data/home_new/wujinqi/agent-memory/outputs/diagnostic/v52_profile_uncertain_repair_lme_pref_aa0f67c/predictions.jsonl
- traces: /data/home_new/wujinqi/agent-memory/outputs/diagnostic/v52_profile_uncertain_repair_lme_pref_aa0f67c/traces.jsonl
- metrics: /data/home_new/wujinqi/agent-memory/experiments/diagnostic/v52_profile_uncertain_repair_lme_pref_aa0f67c/metrics.json
- manifest: /data/home_new/wujinqi/agent-memory/experiments/diagnostic/v52_profile_uncertain_repair_lme_pref_aa0f67c/manifest.json

## Clean Notes

- No gold/reference/target answer, judge output, benchmark label, sample id, qid, or row index is passed into the prediction pipeline.
- Build-stage typed memory is generated only from raw dialogue and visible metadata; it is recorded separately from offline labels and judge outputs.
- Raw context remains available for fallback and diagnosis; build memory records keep source back-links when produced by the current builder.
- Accuracy is intentionally not computed by the prediction runner; any gold or judge metrics must be produced offline after prediction.

## 人工结论

v52 是 v51 的 token-safe 收窄版。它保留通用 advice/tips/should-I -> `profile_preference` route，但不再对所有 profile/preference 问题调用第二阶段 repair；只有 draft answer 自己表现出 `unknown / insufficient / missing` 时才触发 repair。

设计依据：

- v51 repair applied 的 6 条中，draft 全部是拒答/信息不足；单独 judge 显示 draft `0/6` -> repair final `3/6`。
- v51 的主要问题是 `23/30` 都触发 repair，其中大量 `triggered_keep` 白白增加 query tokens。
- 因此 v52 不是新方向，而是对 v51 已验证信号做成本收敛。

离线 DeepSeek judge 结果：

- v52：`15/30 = 0.500000`。
- v42 same30：`13/30 = 0.433333`。
- v51 same30：`16/30 = 0.533333`。
- v52 vs v42：gain/loss `6/4`，net `+2`。
- v52 vs v51：少 `1` 条 correct，但 avg_query_tokens 降低 `2428.133`。

成本：

- avg_build_tokens：`79618.667`，build cache 全命中但按 logical cold-build usage 计入成本。
- avg_query_tokens：`5954.533`，低于 6K 预算。
- repair triggered：`6/30`，repair applied：`5/30`。
- answer cache：`30/30` hit；repair cache：`0/6` hit，本次写入 `6` 条。

诊断：

- v52 保住了主要正向，同时把 v51 的 query token 从 `8382.667` 降到 `5954.533`。
- 回退点包括 Miami hotel：v51 用 profile repair 修对，v52 repair 被触发但选择 keep refusal；说明仅靠 uncertain reason 还不如 v51 的 profile-preference review prompt 稳定。
- 有一条 phone accessory 与 v51 answer 完全相同但 judge label 翻转，属于 same-answer judge variance，应在 full 或复评时标注。

决策：

- v52 是当前值得进一步验证的 token-safe profile repair 候选。
- 因为 full route audit 显示 profile/advice 影响范围约 `30/500`，且 v52 same30 成本合格，可以进入 LongMemEval-S full 预测/评测；但预期 full 只会小幅改善 v42，不能视为达到 baseline target。

离线诊断文件：

- DeepSeek judge：`experiments/diagnostic/v52_profile_uncertain_repair_lme_pref_aa0f67c/deepseek_judge.json`
- vs v42/v51 comparison：`experiments/diagnostic/v52_profile_uncertain_repair_lme_pref_aa0f67c/judge_comparison_vs_v42_v51_same30.json`
- prompt clean scan：`experiments/diagnostic/v52_profile_uncertain_repair_lme_pref_aa0f67c/prompt_clean_scan.json`
