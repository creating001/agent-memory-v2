# v30_stateful_validity_probe_3525934

## 中文结论

本次是 v30 typed temporal/event build memory 的字段质量门禁，不是正式 accuracy 结果。输入为 20 条 question-text route 分层诊断样本，覆盖 LongMemEval/LoCoMo 与 `fact_lookup`、`temporal_lookup`、`list_count`、`profile_preference`、`current_state` 五类 information need。抽样只来自 prediction input 和本地 question router，没有使用 gold、judge、category、question_type、sample id 或 evidence 标签。

门禁结论：通过字段质量与 token 预算检查，但还不足以直接全量跑正式实验。v30 现在能稳定生成 `mention_time` 与一部分 `event_time`，并且 manager 后处理已把 `valid_from/valid_to` 限制在持续性 memory 类型上，避免一次性 event/fact/plan 被误当成状态区间。

关键字段统计：

- build records: `1711`
- `mention_time`: `1711/1711`
- `event_time`: `424/1711`
- `valid_from`: `458/1711`
- `valid_to`: `97/1711`
- non-stateful validity records: `0`
- 有 validity 的类型只剩 `preference/profile/relationship/state`

Token 与服务设置：

- avg build tokens: `65592.3`
- avg query tokens: `4984.55`
- build cache: `128/0/0` hit/miss/write，但 build token 仍按冷启动逻辑成本计入。
- answer max input/output: `131072/16384`
- worker: `4`

外部方法依据与取舍：

- 借鉴 Graphiti/Zep 的 temporal validity + episode provenance，但不用图数据库和图边作为最终答案。
- 借鉴 SimpleMem 的 lossless temporal memory unit 和 multi-view retrieval 思路，但不使用其 benchmark/category override。
- 借鉴 LangMem/Memobase/MIRIX 的 profile/event/episodic schema，但当前只落地轻量 typed record。
- 参考 creating001 的 evidence-first temporal query 结构，但不迁移 target phrase、category、sample-level guardrail 或 finalizer。

下一步建议：在提交当前 v30 validity 修正后，可以跑正式 full 之前的最后一次小型预测门禁或直接规划 full。考虑到字段质量已过，下一步更有价值的是先跑 LoCoMo full 验证 v30 是否保留 v29 temporal 收益；LongMemEval full 也必须随后跑，因为 v29 在 LME 有回退。

## Purpose

Stage-1 clean skeleton run: validate raw evidence storage, lexical retrieval, neighbor expansion, evidence compilation, answer generation, trace output, and experiment bookkeeping.

## Scope

- benchmark: mixed
- subset: route_stratified_probe
- experiment_kind: diagnostic
- limit: None
- workers: 4
- input_path: /data/home_new/wujinqi/agent-memory/outputs/diagnostic/v30_route_stratified_probe/prediction_input.jsonl
- config_path: /data/home_new/wujinqi/agent-memory/configs/stage1_typed_event_memory_v30_cached.json
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0, max_input_tokens 131072, and max_output_tokens 16384.

## Git

- inside_work_tree: True
- commit: 3525934b5deb3173f126f2c61d1b7617217c5dfa
- dirty: True
- note: None

## Metrics

- n_samples: 20
- accuracy: None
- f1: None
- bleu: None
- avg_build_tokens: 65592.3
- build_token_accounting: logical cold-build LLM tokens; cached build chunks count from stored usage, while cache hits only avoid repeated local API calls.
- avg_query_tokens: 4984.55
- avg_compiled_evidence_items: 36.7
- build_memory_enabled: True
- build_memory_model: Qwen/Qwen3-30B-A3B-Instruct-2507
- build_memory_temporal_fields: True
- build_memory_cache_enabled: True
- build_memory_cache_path: outputs/cache/qwen3_build_memory.sqlite
- build_memory_cache_hits: 128
- build_memory_cache_misses: 0
- build_memory_cache_writes: 0
- avg_build_memory_records: 85.55
- avg_active_build_memory_records: 80.7
- avg_memory_hits: 12.25
- avg_memory_source_hits: 15.2
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
- avg_context_chars: 15788.3
- compiler_prompt_mode: external_naive
- answer_mode: openai_compatible
- answer_model: Qwen/Qwen3-30B-A3B-Instruct-2507
- answer_max_input_tokens: 131072
- answer_max_output_tokens: 16384
- answer_output_format: json_answer
- answer_cache_enabled: True
- answer_cache_path: outputs/cache/qwen3_answer_v30.sqlite
- answer_cache_namespace: stage1_typed_event_memory_v30_qwen3_30b
- answer_cache_hits: 17
- answer_cache_misses: 3
- answer_cache_writes: 3
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
- evidence_report_max_items: 8
- route_overrides: {'temporal_lookup': {'max_memory_records': 8, 'structured_guide_include_memory': True}, 'current_state': {'max_memory_records': 6, 'structured_guide_include_memory': True}}
- enable_broad_list_patterns: False
- enable_recommendation_profile_patterns: True
- temporal_priority_over_recent: False

## Outputs

- predictions: /data/home_new/wujinqi/agent-memory/outputs/diagnostic/v30_stateful_validity_probe_3525934/predictions.jsonl
- traces: /data/home_new/wujinqi/agent-memory/outputs/diagnostic/v30_stateful_validity_probe_3525934/traces.jsonl
- metrics: /data/home_new/wujinqi/agent-memory/experiments/diagnostic/v30_stateful_validity_probe_3525934/metrics.json
- manifest: /data/home_new/wujinqi/agent-memory/experiments/diagnostic/v30_stateful_validity_probe_3525934/manifest.json

## Clean Notes

- No gold/reference/target answer, judge output, benchmark label, sample id, qid, or row index is passed into the prediction pipeline.
- Build-stage typed memory is generated only from raw dialogue and visible metadata; it is recorded separately from offline labels and judge outputs.
- Raw context remains available for fallback and diagnosis; build memory records keep source back-links when produced by the current builder.
- Accuracy is intentionally not computed by the prediction runner; any gold or judge metrics must be produced offline after prediction.
