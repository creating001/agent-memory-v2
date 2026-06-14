# v47 Temporal Aggregation Contract 诊断

## 结论

v47 不进入 LongMemEval-S full，也不作为主线方法保留。

同 106 条 question-derived temporal aggregation 诊断集上，v47 DeepSeek judge accuracy 为 `75/106 = 0.707547`，低于 v42 同集 `81/106 = 0.764151`。净变化为 `+5 / -11`，answer changed `37/106`。主要问题是 aggregation schema 增加了 prompt 长度，同时 mechanical count finalizer 对模型输出的 `count_increment` 过度信任，出现重复计数和聚合行二次计数。

## 范围

- run_id: `v47_temporal_aggregation_lme_diag_5487300`
- benchmark: `longmemeval_s`
- subset: `temporal_aggregation_106`
- experiment_kind: `diagnostic`
- input: `outputs/diagnostic/v47_lme_temporal_aggregation_input/prediction_input.jsonl`
- outputs: `outputs/diagnostic/v47_temporal_aggregation_lme_diag_5487300/`
- experiment dir: `experiments/diagnostic/v47_temporal_aggregation_lme_diag_5487300/`
- workers: `4`

## 方法

底座是 v42 operation workpad。v47 只在 question text 触发 temporal aggregation information need 时启用更强的 `evidence_report` schema：

- `canonical_item`
- `count_increment`
- `operand_value`
- `calculation`

同时打开 `answer.finalizer.enable_evidence_report_count_correction=true`，试图只用当前 answer JSON 中的 `count_increment` 做机械一致性修正。

外部参考：

- `creating001-agent-memory` 的 scoped aggregation / evidence-first query 组织，只取通用 include/exclude/operand 思想，舍弃 target phrase、category、sample-level guardrail 和不 clean 逻辑。
- `SimpleMem` 的 structured context 与 typed evidence 思路，但不让 summary 替代 raw evidence。
- `Memary` 的 entity/count/date aggregation 管理思想，但不迁移固定 entity 规则。
- `Graphiti/Zep` 的 temporal/provenance 思路，不引入图数据库。

## Git

- commit: `5487300bce34290d04a721fcb564d261184eb169`
- dirty: `true`
- dirty note: 运行时用户修改的 `docs/architecture.md`、`docs/clean_protocol.md` 未纳入本次方法代码；v47 诊断结果目录为新增 artifact。

## 预测指标

- n_samples: `106`
- avg_build_tokens: `79953.094340`
- total_build_tokens: `8475028`
- avg_query_tokens: `7209.037736`
- total_query_tokens: `764158`
- answer max input/output: `131072 / 16384`
- build cache hits/misses/writes: `703 / 0 / 0`
- answer cache hits/misses/writes: `0 / 106 / 106`
- avg_build_memory_records: `128.358491`
- avg_active_build_memory_records: `115.084906`
- avg_compiled_evidence_items: `34.764151`
- answer_finalizer_applied_count: `11`

Token 口径：build tokens 是新环境冷构建 memory 的逻辑 LLM token，即使本机 cache 命中，也按 cached usage 计入方法成本；query tokens 是 answer/query LLM token。

## Judge 结果

- current accuracy: `0.707547` (`75/106`)
- v42 same-106 accuracy: `0.764151` (`81/106`)
- gain/loss: `5 / 11`
- same correct / same wrong: `70 / 20`
- answer changed: `37`
- DeepSeek judge usage: `42864` total tokens

离线 question_type 诊断只用于复盘，不进入 prediction：

- temporal-reasoning: v42 `49/56` -> v47 `51/56`
- multi-session: v42 `23/40` -> v47 `17/40`
- knowledge-update: v42 `4/5` -> v47 `3/5`
- single-session-user: v42 `5/5` -> v47 `4/5`

v47 对部分 temporal-reasoning 有帮助，但在 multi-session / count/list 上引入更多错误，整体净负。

## Token Gate

对 full 的估算：

- selected avg base query tokens: `6729.820755`
- selected avg current query tokens: `7209.037736`
- selected avg delta: `479.216981`
- weighted full avg delta: `101.594`
- estimated full avg query tokens: `5967.238`

虽然估算没有超过 6K 主线预算，但 accuracy 净负和 finalizer 误修已经足够否决 full。

## Clean 检查

- prediction pipeline 未使用 gold/reference answer、judge output、benchmark label、sample id、qid 或 row index。
- prompt clean scan 有 1 个 literal hit：原始对话里 assistant 说过 “provide the correct answer”。这是 raw dialogue 内容，不是 benchmark/gold/judge 泄漏。
- judge 和 `question_type` 只在预测完成后用于离线诊断。

## 输出文件

- `metrics.json`
- `deepseek_judge.json`
- `judge_comparison_vs_v42_same106.json`
- `full_query_token_estimate.json`
- `prompt_clean_scan.json`
- `config_snapshot.json`
- predictions: `outputs/diagnostic/v47_temporal_aggregation_lme_diag_5487300/predictions.jsonl`
- traces: `outputs/diagnostic/v47_temporal_aggregation_lme_diag_5487300/traces.jsonl`

顶层候选配置 `configs/stage1_temporal_aggregation_contract_v47_cached.json` 已删除，只保留本目录 `config_snapshot.json` 供复盘。

## 下一步

不要继续扩大 mechanical count finalizer。下一版应回到更 general 的 memory organization：在 build/retrieval/compile 侧做 source-preserving scoped evidence selection 和去重，而不是让 answer prompt 输出更长的计数字段后再机械修正。
