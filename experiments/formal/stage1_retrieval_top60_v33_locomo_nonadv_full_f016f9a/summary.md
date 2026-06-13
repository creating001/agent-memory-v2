# stage1_retrieval_top60_v33_locomo_nonadv_full_f016f9a

## Purpose

验证 v33 clean top-60 retrieval expansion 是否能在 LoCoMo non-adversarial full 上提升 DeepSeek judge accuracy。

v33 不改 build memory 和 answer repair，只把 v29 底座的 raw-turn dense+BM25 retrieval、dense protect 和 compiler evidence budget 从 top-40 扩到 top-60，用于隔离 source coverage 扩展的收益和代价。

## Scope

- benchmark: locomo
- subset: non_adversarial_full
- experiment_kind: formal
- limit: None
- workers: 8
- input_path: /data/home_new/wujinqi/agent-memory/outputs/prepare_locomo_non_adversarial/prediction_input.jsonl
- config_path: /data/home_new/wujinqi/agent-memory/configs/stage1_retrieval_top60_v33_cached.json
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0, max_input_tokens 131072, and max_output_tokens 16384.

## Git

- inside_work_tree: True
- commit: f016f9a7233172a6d3bb75f247a68cd1e8ec9556
- dirty: True
- dirty_note: prediction run 开始时仅有用户修改的 `docs/architecture.md` 和 `docs/clean_protocol.md` 处于 dirty；未发现预测代码或本 run config 的未提交修改。judge 阶段额外出现本实验目录未提交，这是输出记录本身。

## Metrics

- n_samples: 1540
- DeepSeek judge accuracy_valid_only: 0.7719298245614035
- DeepSeek judge accuracy_invalid_as_wrong: 0.7714285714285715
- DeepSeek judge n_correct/n_valid/n_samples: 1188/1539/1540
- DeepSeek judge n_invalid: 1
- baseline_vs_v29: +15 correct, v29/v32 were 1173/1540
- target_gap: LoCoMo 0.78 target requires 1202/1540; v33 is 14 correct short under invalid-as-wrong accounting.
- f1/bleu/exact: not used for method selection
- avg_build_tokens: 58386.00779220779
- build_token_accounting: logical cold-build LLM tokens; cached build chunks count from stored usage, while cache hits only avoid repeated local API calls.
- avg_query_tokens: 5191.105844155844
- total_build_tokens: 89914452
- total_query_tokens: 7994303
- DeepSeek judge total_tokens: 666030
- avg_compiled_evidence_items: 60.0
- build_memory_enabled: True
- build_memory_model: Qwen/Qwen3-30B-A3B-Instruct-2507
- build_memory_temporal_fields: False
- build_memory_cache_enabled: True
- build_memory_cache_path: outputs/cache/qwen3_build_memory.sqlite
- build_memory_cache_hits: 12411
- build_memory_cache_misses: 0
- build_memory_cache_writes: 0
- avg_build_memory_records: 136.65974025974026
- avg_active_build_memory_records: 125.11233766233767
- avg_memory_hits: 19.84155844155844
- avg_memory_source_hits: 22.37922077922078
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
- embedding_cache_hits: 7422
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
- avg_context_chars: 15325.005844155845
- compiler_prompt_mode: external_naive
- answer_mode: openai_compatible
- answer_model: Qwen/Qwen3-30B-A3B-Instruct-2507
- answer_max_input_tokens: 131072
- answer_max_output_tokens: 16384
- answer_output_format: json_answer
- answer_cache_enabled: True
- answer_cache_path: outputs/cache/qwen3_answer_v33_top60.sqlite
- answer_cache_namespace: stage1_retrieval_top60_v33_qwen3_30b
- answer_cache_hits: 31
- answer_cache_misses: 1509
- answer_cache_writes: 1509
- answer_finalizer_enabled: False
- answer_finalizer_mode: structured_evidence_mechanical
- answer_finalizer_enable_count_correction: False
- answer_finalizer_enable_money_sum_correction: True
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
- evidence_report_detail: False
- route_overrides: {}
- enable_broad_list_patterns: False
- enable_recommendation_profile_patterns: True
- temporal_priority_over_recent: False

## Offline Evidence Recall

- evidence_recall: 0.91796875 over 1536 examples with evidence labels
- by_type_1: 0.925531914893617, n=282
- by_type_2: 0.9190031152647975, n=321
- by_type_3: 0.6956521739130435, n=92
- by_type_4: 0.93935790725327, n=841

Compared with top-40 v29/v32 evidence recall 0.8912760416666666, v33 improves source coverage clearly, but extra context is not uniformly helpful for answer accuracy.

## Comparison With v29

- both_correct: 1112
- both_wrong: 291
- gained: 76
- lost: 61
- net: +15 correct

By question-derived route:

- fact_lookup: gained 50, lost 34, net +16
- list_count: gained 12, lost 7, net +5
- profile_preference: gained 5, lost 3, net +2
- current_state: gained 1, lost 0, net +1
- temporal_lookup: gained 8, lost 17, net -9

结论：top-60 对普通 fact/list/profile/source coverage 有明确收益，但 temporal_lookup 因更大 context 引入旧时间或相邻事实干扰，整体回退。下一轮不能继续无差别加 evidence，应做 question-route 条件化的 retrieval/compile budget。

## Outputs

- predictions: /data/home_new/wujinqi/agent-memory/outputs/formal/stage1_retrieval_top60_v33_locomo_nonadv_full_f016f9a/predictions.jsonl
- traces: /data/home_new/wujinqi/agent-memory/outputs/formal/stage1_retrieval_top60_v33_locomo_nonadv_full_f016f9a/traces.jsonl
- metrics: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_retrieval_top60_v33_locomo_nonadv_full_f016f9a/metrics.json
- manifest: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_retrieval_top60_v33_locomo_nonadv_full_f016f9a/manifest.json

## Clean Notes

- No gold/reference/target answer, judge output, benchmark label, sample id, qid, or row index is passed into the prediction pipeline.
- Build-stage typed memory is generated only from raw dialogue and visible metadata; it is recorded separately from offline labels and judge outputs.
- Raw context remains available for fallback and diagnosis; build memory records keep source back-links when produced by the current builder.
- Accuracy is intentionally not computed by the prediction runner; any gold or judge metrics must be produced offline after prediction.

## Decision

v33 是 LoCoMo 正向主线候选，超过 v29/v32，但仍未达 0.78 target。暂不直接跑 LongMemEval-S full；LME 的 mixed gate 显示 top-60 可能超过 6K query token，必须先做 LME 单独 gate 或更细的 route budget。

下一步 v34 应保留 v33 对 fact/list/profile/current 的 top-60 收益，同时对 temporal_lookup 回到更窄的 retrieval/compile budget，或增加通用 temporal conflict control。这个设计来自当前 badcase 对照和外部方法的 completeness-before-answering 思路，不使用 benchmark label、sample id、gold、judge 或样本级规则。
