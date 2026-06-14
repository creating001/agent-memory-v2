# stage1_profile_uncertain_repair_v52_lme_s_full_9a04884

## Purpose

Stage-1 clean skeleton run: validate raw evidence storage, lexical retrieval, neighbor expansion, evidence compilation, answer generation, trace output, and experiment bookkeeping.

## Scope

- benchmark: longmemeval_s
- subset: full
- experiment_kind: formal
- limit: None
- workers: 8
- input_path: /data/home_new/wujinqi/agent-memory/outputs/prepare_longmemeval_s_cleaned/prediction_input.jsonl
- config_path: /data/home_new/wujinqi/agent-memory/configs/stage1_profile_uncertain_repair_v52_cached.json
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0, max_input_tokens 131072, and max_output_tokens 16384.

## Git

- inside_work_tree: True
- commit: 9a0488437ce6dffcfd09330055b6c5e4a3dd55d1
- dirty: True
- note: None

## Metrics

- n_samples: 500
- accuracy: None
- f1: None
- bleu: None
- avg_build_tokens: 80346.246
- build_token_accounting: logical cold-build LLM tokens; cached build chunks count from stored usage, while cache hits only avoid repeated local API calls.
- avg_query_tokens: 5929.072
- question_analysis_enabled: False
- question_analysis_model: None
- question_analysis_avg_query_tokens: 0.0
- question_analysis_route_changed_count: 0
- question_analysis_cache_hits: 0
- question_analysis_cache_misses: 0
- question_analysis_cache_writes: 0
- avg_compiled_evidence_items: 34.062
- retrieval_route_overrides: {}
- avg_effective_top_k: 40.0
- avg_effective_dense_top_k: 40.0
- avg_effective_dense_protect_top_n: 32.0
- build_memory_enabled: True
- build_memory_model: Qwen/Qwen3-30B-A3B-Instruct-2507
- build_memory_temporal_fields: False
- build_memory_cache_enabled: True
- build_memory_cache_path: outputs/cache/qwen3_build_memory.sqlite
- build_memory_cache_hits: 3341
- build_memory_cache_misses: 0
- build_memory_cache_writes: 0
- avg_build_memory_records: 129.662
- avg_active_build_memory_records: 116.456
- avg_memory_hits: 8.23
- avg_memory_source_hits: 7.918
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
- embedding_cache_hits: 247238
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
- avg_context_chars: 19706.834
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
- answer_cache_misses: 470
- answer_cache_writes: 470
- answer_finalizer_enabled: True
- answer_finalizer_mode: structured_evidence_mechanical
- answer_finalizer_enable_count_correction: False
- answer_finalizer_enable_evidence_report_count_correction: False
- answer_finalizer_enable_money_sum_correction: False
- answer_finalizer_enable_duration_rounding_correction: True
- answer_finalizer_applied_count: 2
- answer_finalizer_applied_rate: 0.004
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
- answer_repair_cache_hits: 6
- answer_repair_cache_misses: 0
- answer_repair_cache_writes: 0
- answer_repair_triggered_count: 6
- answer_repair_triggered_rate: 0.012
- answer_repair_applied_count: 5
- answer_repair_applied_rate: 0.01
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

- predictions: /data/home_new/wujinqi/agent-memory/outputs/formal/stage1_profile_uncertain_repair_v52_lme_s_full_9a04884/predictions.jsonl
- traces: /data/home_new/wujinqi/agent-memory/outputs/formal/stage1_profile_uncertain_repair_v52_lme_s_full_9a04884/traces.jsonl
- metrics: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_profile_uncertain_repair_v52_lme_s_full_9a04884/metrics.json
- manifest: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_profile_uncertain_repair_v52_lme_s_full_9a04884/manifest.json

## Clean Notes

- No gold/reference/target answer, judge output, benchmark label, sample id, qid, or row index is passed into the prediction pipeline.
- Build-stage typed memory is generated only from raw dialogue and visible metadata; it is recorded separately from offline labels and judge outputs.
- Raw context remains available for fallback and diagnosis; build memory records keep source back-links when produced by the current builder.
- Accuracy is intentionally not computed by the prediction runner; any gold or judge metrics must be produced offline after prediction.

## 人工结论

v52 full 验证失败，不能作为当前 LongMemEval 主线。

方法：

- 底座是 v42 operation workpad。
- 保留通用 advice/tips/should-I -> `profile_preference` route。
- 只在 `profile_preference` draft answer 自己表现出 unknown / insufficient / missing 时触发第二阶段 profile repair。
- repair 输入只包含 question、question_time、route、retrieved Memory Context 和 draft answer。

DeepSeek judge：

- v52 full：`385/500 = 0.770000`。
- v42 full：`387/500 = 0.774000`。
- v36 full：`386/500 = 0.772000`。
- v52 vs v42：gain/loss `19/21`，net `-2`。

成本：

- avg_build_tokens：`80346.246`，build cache 全命中但按 logical cold-build usage 计入成本。
- avg_query_tokens：`5929.072`，通过 6K 预算。
- repair triggered：`6/500`。
- repair applied：`5/500`。
- answer max input/output：`131072/16384`。

诊断：

- same30 诊断正向没有泛化到 full。
- full 中 answer_changed_vs_v42 为 `106`，远大于 repair 触发的 `6` 条；说明损失主要来自重跑 answer 的大范围输出波动和 advice route 扩展扰动，而不是 repair 本身。
- prompt clean scan 有 `2` 个 raw-context phrase finding，人工复核均为原始对话中自然出现的 “correct answer” 字样，不是 gold/judge/label/id 泄漏。

决策：

- 不保留顶层 v52 config；本目录保留 `config_snapshot.json` 作为复现入口。
- 不跑 LoCoMo。
- 下一步若继续 profile/advice，应设计 build-side profile/event anchor 或 query-side anchor table，减少 full 重跑 variance；不要再只靠 answer repair prompt 扩大覆盖。

离线结果文件：

- DeepSeek judge：`experiments/formal/stage1_profile_uncertain_repair_v52_lme_s_full_9a04884/deepseek_judge.json`
- comparison：`experiments/formal/stage1_profile_uncertain_repair_v52_lme_s_full_9a04884/judge_comparison_vs_v42_v36.json`
- prompt clean scan：`experiments/formal/stage1_profile_uncertain_repair_v52_lme_s_full_9a04884/prompt_clean_scan.json`
