# stage1_operation_workpad_v42_lme_s_full_f7eb076

## 目的

验证 v42 `operation_workpad` 是否能在 LongMemEval-S full 上稳定改善 v36 的 list/count 与 temporal 聚合错误。

v42 不改变 build memory、不改变 retrieval top-k、不新增 query-side LLM 调用。它只允许 `operation_workpad` 与 `evidence_report_contract` 同时生效，并在 `list_count` / `temporal_lookup` 的 prompt 中加入很短的通用操作纪律：先明确问题需要的计数、求和、比较、时间边界和 inclusive alternatives，再聚合证据。

## 范围

- benchmark: `longmemeval_s`
- subset: `full`
- samples: `500`
- experiment_kind: `formal`
- workers: `4`
- input_path: `/data/home_new/wujinqi/agent-memory/outputs/prepare_longmemeval_s_cleaned/prediction_input.jsonl`
- config_path: `/data/home_new/wujinqi/agent-memory/configs/stage1_operation_workpad_v42_cached.json`
- answer model: `Qwen/Qwen3-30B-A3B-Instruct-2507`
- answer base_url: `http://127.0.0.1:8000/v1`
- answer temperature: `0`
- answer max input/output: `131072/16384`

## Git

- commit: `f7eb0761216ef6038b04c2405b1f183c4241a095`
- dirty: `True`
- dirty_note: prediction 和 judge 时有用户修改的 `docs/architecture.md`、`docs/clean_protocol.md` 未提交；预测代码和 v42 config 已提交。实验目录为本次运行新生成。

## 指标

- DeepSeek judge accuracy: `0.774`
- DeepSeek judge correct/valid/samples: `387/500/500`
- DeepSeek judge invalid: `0`
- current LME baseline v36: `0.772`, `386/500`
- delta_vs_v36: `+1` correct
- v40 reader-side detail 对照: `0.742`, `371/500`
- delta_vs_v40: `+16` correct
- target_status: 距 `0.80` baseline target 还差 `13` correct
- f1/bleu/exact: 不作为方法选择依据
- avg_build_tokens: `80346.246`
- total_build_tokens: `40173123`
- build_token_accounting: logical cold-build LLM tokens；cache hit 只减少本机重复 API 调用，不把方法成本记为 0。
- avg_query_tokens: `5865.644`
- total_query_tokens: `2932822`
- max_query_tokens: `8842`
- DeepSeek judge total_tokens: `119138`
- avg_compiled_evidence_items: `34.062`
- avg_context_chars: `19665.61`
- avg_build_memory_records: `129.662`
- avg_active_build_memory_records: `116.456`
- avg_memory_hits: `8.236`
- avg_memory_source_hits: `7.924`
- build cache hits/misses/writes: `3341/0/0`
- embedding cache hits/misses/writes: `247238/0/0`
- answer cache hits/misses/writes: `20/480/480`
- answer finalizer applied: `1`
- answer output format: `json_answer`

## 分桶表现

按 information_need:

- current_state: `12/22 = 0.5455`
- fact_lookup: `150/183 = 0.8197`
- list_count: `95/119 = 0.7983`
- profile_preference: `10/15 = 0.6667`
- temporal_lookup: `120/161 = 0.7453`

按 question_type:

- knowledge-update: `64/78 = 0.8205`
- multi-session: `87/133 = 0.6541`
- single-session-assistant: `53/56 = 0.9464`
- single-session-preference: `13/30 = 0.4333`
- single-session-user: `65/70 = 0.9286`
- temporal-reasoning: `105/133 = 0.7895`

Route token audit:

- current_state: `n=22`, avg query `6200.045`, p90 `6807`, max `7138`, workpad `0/22`
- fact_lookup: `n=183`, avg query `5355.738`, p90 `5764`, max `6875`, workpad `0/183`
- list_count: `n=119`, avg query `5683.218`, p90 `6022`, max `6903`, workpad `119/119`
- profile_preference: `n=15`, avg query `5108.933`, p90 `5597`, max `5788`, workpad `0/15`
- temporal_lookup: `n=161`, avg query `6604.87`, p90 `7296`, max `8842`, workpad `161/161`

平均 query token 仍在 `6000` 预算内，但 temporal_lookup 有单样本超过 `8000`。本次是 formal 可报告结果，不应把 v42 继续扩写成更长 prompt。

## v36 对比

Offline judge comparison against `stage1_lme_token_safe_format_guard_v36_lme_s_full_4af3244`:

- both_correct: `361`
- both_wrong: `88`
- gained: `26`
- lost: `25`
- net: `+1`
- changed_answer_count: `150/500`
- same_answer_judge_flip_count: `4`

按 information_need 的净变化:

- current_state: gained `1`, lost `4`, net `-3`
- fact_lookup: gained `9`, lost `6`, net `+3`
- list_count: gained `5`, lost `6`, net `-1`
- profile_preference: gained `2`, lost `0`, net `+2`
- temporal_lookup: gained `9`, lost `9`, net `0`

解释：v42 是 close-margin 小幅正向，不是方法突破。它比 v40 的详细 reader rule 稳定得多，但相对 v36 只多 1 条，且 changed-answer 很多、gain/loss 基本相抵。不能继续靠堆 prompt 期待大幅提升。

## 离线诊断

Evidence recall:

- evidence_recall: `1.0`
- n_with_evidence_labels: `500`
- by question_type: 全部 `1.0`

这里的 LME evidence label 是 `answer_session_ids` 级别，说明目标 session 基本都进入 context；剩余错误更可能来自证据组织、跨证据聚合、时间/状态边界、计数和 reader 选择。

v42 wrong total: `113`。

badcase digest tag counts:

- temporal: `59`
- large_context: `56`
- count_or_quantity: `54`
- gold_string_in_rows: `33`
- over_abstain: `22`
- update_or_state: `19`
- should_abstain: `15`
- other: `11`

典型问题:

- temporal_lookup 仍会把 mention date、event date 和相对时间窗口混淆。
- list_count 仍有漏计、误排除和边界不一致，例如 inclusive alternatives 虽有改善但不稳定。
- profile/current_state 的个性化建议仍弱，常给出通用建议或过窄事实。
- 一些 wrong case 的关键字符串已在 top rows 中，说明不是单纯 retrieval miss。

## 决策

保留 v42 为当前 LongMemEval-S full 最好结果，但只视为小幅正向 ablation。它可以作为 LME 当前候选配置保留，不应直接宣称达到目标。

下一步不能再随手加 prompt 规则。需要先基于 v42/v36 badcase 和外部方法代码，设计 build 到 query 都更强的 memory organization，例如更好的 event/state/profile 单元、跨 session candidate aggregation、冲突/缺失信息处理和多视图索引。若只想判断迁移性，可以跑 v42 LoCoMo full，但应明确其只是迁移验证，不是新方法设计。

## 输出路径

- predictions: `/data/home_new/wujinqi/agent-memory/outputs/formal/stage1_operation_workpad_v42_lme_s_full_f7eb076/predictions.jsonl`
- traces: `/data/home_new/wujinqi/agent-memory/outputs/formal/stage1_operation_workpad_v42_lme_s_full_f7eb076/traces.jsonl`
- metrics: `/data/home_new/wujinqi/agent-memory/experiments/formal/stage1_operation_workpad_v42_lme_s_full_f7eb076/metrics.json`
- judge: `/data/home_new/wujinqi/agent-memory/experiments/formal/stage1_operation_workpad_v42_lme_s_full_f7eb076/deepseek_judge.json`
- judge_metrics_summary: `/data/home_new/wujinqi/agent-memory/experiments/formal/stage1_operation_workpad_v42_lme_s_full_f7eb076/judge_metrics_summary.json`
- evidence_recall: `/data/home_new/wujinqi/agent-memory/experiments/formal/stage1_operation_workpad_v42_lme_s_full_f7eb076/evidence_recall.json`
- judge_comparison: `/data/home_new/wujinqi/agent-memory/experiments/formal/stage1_operation_workpad_v42_lme_s_full_f7eb076/judge_comparison_vs_v36_v40.json`
- badcase_digest: `/data/home_new/wujinqi/agent-memory/experiments/formal/stage1_operation_workpad_v42_lme_s_full_f7eb076/badcase_digest.json`
- manifest: `/data/home_new/wujinqi/agent-memory/experiments/formal/stage1_operation_workpad_v42_lme_s_full_f7eb076/manifest.json`
- config_snapshot: `/data/home_new/wujinqi/agent-memory/experiments/formal/stage1_operation_workpad_v42_lme_s_full_f7eb076/config_snapshot.json`

## Clean Notes

- Prediction pipeline 未读取 gold/reference answer、judge output、benchmark label、sample id、qid、row index、category 或 question_type。
- v42 `operation_workpad` 只由 prediction-time question 和 retrieved context 触发，不读取离线 label 或 judge。
- Build-stage typed memory 只由 raw dialogue 和可见元数据构建；cache 命中仍按 stored logical usage 计入 cold-build token 成本。
- DeepSeek judge、evidence recall、badcase 和 comparison 都是 prediction 完成后的离线诊断，不能被 prediction/retrieval/compiler/answer/verifier 读取。
- v42 没有加入样本级规则，也没有加入 benchmark-specific entity、record key 或测试答案。
