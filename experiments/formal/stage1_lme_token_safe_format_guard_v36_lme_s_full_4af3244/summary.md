# stage1_lme_token_safe_format_guard_v36_lme_s_full_4af3244

## 目的

验证 v36 在 LongMemEval-S full 上是否能保留 v28 的 token-safe top40 evidence budget，同时吸收 v35 的 answer format guard。

v36 不改变 build memory 和主检索框架：它沿用 v28 的 top40 retrieval / evidence_report contract，只加入通用的 `json_answer` 解析稳定性和小数 duration 机械修正。该实验用于判断这类 query-side 稳定性改动是否能在 LME 上形成正向收益。

## 范围

- benchmark: `longmemeval_s`
- subset: `full`
- samples: `500`
- experiment_kind: `formal`
- workers: `8`
- input_path: `/data/home_new/wujinqi/agent-memory/outputs/prepare_longmemeval_s_cleaned/prediction_input.jsonl`
- config_path: `/data/home_new/wujinqi/agent-memory/configs/stage1_lme_token_safe_format_guard_v36_cached.json`
- answer model: `Qwen/Qwen3-30B-A3B-Instruct-2507`
- answer base_url: `http://127.0.0.1:8000/v1`
- answer temperature: `0`
- answer max input/output: `131072/16384`

## Git

- commit: `4af32444a58fff4e7b86c44906ec7da448a68e7c`
- dirty: `True`
- dirty_note: prediction 和 judge 开始时只有用户修改的 `docs/architecture.md`、`docs/clean_protocol.md` 处于 dirty；预测代码和 v36 config 已提交。

## 指标

- DeepSeek judge accuracy: `0.772`
- DeepSeek judge correct/valid/samples: `386/500/500`
- DeepSeek judge invalid: `0`
- previous LME best v28: `0.766`, `383/500`
- delta_vs_v28: `+3` correct
- target_status: 距 `0.80` baseline target 还差 `14` correct
- f1/bleu/exact: 不作为方法选择依据
- avg_build_tokens: `80346.246`
- total_build_tokens: `40173123`
- build_token_accounting: logical cold-build LLM tokens；cache hit 只减少本机重复 API 调用，不把方法成本记为 0。
- avg_query_tokens: `5715.468`
- total_query_tokens: `2857734`
- DeepSeek judge total_tokens: `119844`
- avg_compiled_evidence_items: `34.062`
- avg_context_chars: `18861.108`
- avg_build_memory_records: `129.662`
- avg_active_build_memory_records: `116.456`
- avg_memory_hits: `8.236`
- avg_memory_source_hits: `7.924`
- build cache hits/misses/writes: `3341/0/0`
- embedding cache hits/misses/writes: `247238/0/0`
- answer cache hits/misses/writes: `412/88/88`
- answer finalizer applied: `1`, reason `duration_decimal_rounding`
- answer output format: `json_answer`

## 方法配置摘要

- build memory: enabled，本地 Qwen 从 raw dialogue 构建 typed memory。
- build memory temporal fields: `False`
- build memory include superseded: `False`
- include superseded information needs: `temporal_lookup`, `list_count`
- retrieval: lexical + dense hybrid
- retrieval top_k / dense_top_k / max_top_k: `40/40/40`
- dense protect top_n: `32`
- dense document/query text mode: `external_naive`
- compiler prompt mode: `external_naive`
- evidence_report_contract: `True`
- evidence_report information needs: `current_state`, `fact_lookup`, `list_count`, `profile_preference`, `temporal_lookup`
- evidence_report max items: `8`
- structured_guide: `True`
- temporal_workpad: `True`
- temporal_text_normalization: `True`
- temporal_event_contract: `False`
- answer finalizer duration rounding: `True`
- answer repair/verifier: `False`

## 离线诊断

Evidence recall:

- evidence_recall: `1.0`
- n_with_evidence_labels: `500`
- by question_type: 全部 `1.0`

这里的 LME evidence label 是 `answer_session_ids` 级别，说明 answer session 基本都进入 context；剩余错误更可能来自 evidence 组织、跨证据聚合、时间推理、计数和 reader 选择，而不是完全没有召回到目标 session。

v36 vs v28 judge comparison:

- v28 correct: `383`
- v36 correct: `386`
- gained: `15`
- lost: `12`
- both_correct: `371`
- both_wrong: `102`
- answer_changed: `24`
- gained_answer_changed: `7`
- lost_answer_changed: `5`
- changed_answer_net: `+2`
- gained_answer_same: `8`
- lost_answer_same: `7`
- same_answer_judge_flip_net: `+1`

解释：v36 是有效的 full formal 结果，但收益较小。方法本身带来的答案变化净收益约 `+2`，其余 `+1` 来自同答案 judge 重判波动；因此不能把 v36 解读为大幅方法突破。

剩余错误分布:

- total wrong: `114`
- by question_type: multi-session `47`, temporal-reasoning `28`, single-session-preference `18`, knowledge-update `15`, single-session-user `4`, single-session-assistant `2`
- by information_need: temporal_lookup `41`, fact_lookup `36`, list_count `23`, profile_preference `7`, current_state `7`

下一步应优先处理 multi-session 的跨证据聚合、temporal_lookup 的时间选择、list_count 的边界控制，以及 fact_lookup 中更新事实的选择。

## 输出路径

- predictions: `/data/home_new/wujinqi/agent-memory/outputs/formal/stage1_lme_token_safe_format_guard_v36_lme_s_full_4af3244/predictions.jsonl`
- traces: `/data/home_new/wujinqi/agent-memory/outputs/formal/stage1_lme_token_safe_format_guard_v36_lme_s_full_4af3244/traces.jsonl`
- metrics: `/data/home_new/wujinqi/agent-memory/experiments/formal/stage1_lme_token_safe_format_guard_v36_lme_s_full_4af3244/metrics.json`
- judge: `/data/home_new/wujinqi/agent-memory/experiments/formal/stage1_lme_token_safe_format_guard_v36_lme_s_full_4af3244/deepseek_judge.json`
- evidence_recall: `/data/home_new/wujinqi/agent-memory/experiments/formal/stage1_lme_token_safe_format_guard_v36_lme_s_full_4af3244/evidence_recall.json`
- v28_comparison: `/data/home_new/wujinqi/agent-memory/experiments/formal/stage1_lme_token_safe_format_guard_v36_lme_s_full_4af3244/judge_comparison_vs_v28.json`
- manifest: `/data/home_new/wujinqi/agent-memory/experiments/formal/stage1_lme_token_safe_format_guard_v36_lme_s_full_4af3244/manifest.json`
- config_snapshot: `/data/home_new/wujinqi/agent-memory/experiments/formal/stage1_lme_token_safe_format_guard_v36_lme_s_full_4af3244/config_snapshot.json`

## Clean Notes

- Prediction pipeline 未读取 gold/reference answer、judge output、benchmark label、sample id、qid、row index、category 或 question_type。
- Build-stage typed memory 只由 raw dialogue 和可见元数据构建。
- Answer format guard 只使用 prediction-time 的 raw response、cache raw response、draft answer 和 question text。
- DeepSeek judge、evidence recall 和 v28 comparison 都是 prediction 完成后的离线诊断，不能被 prediction/retrieval/compiler/answer/verifier 读取。
- v36 没有加入样本级规则，也没有加入 benchmark-specific entity 或测试答案。
