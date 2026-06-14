# v53 Scoped Evidence 诊断

## 结论

v53 不进入 LongMemEval-S full，也不作为当前主线配置保留。

同 106 条 LongMemEval-S temporal/list 聚合诊断集上，v53 DeepSeek judge accuracy 为 `63/106 = 0.594340`，显著低于 v42 same-106 的 `81/106 = 0.764151`，也低于 v47 的 `75/106 = 0.707547`。相对 v42，v53 为 `+5 / -23`，answer changed `68/106`。

这次失败不是 token 或 clean 问题，而是方法质量问题：两阶段 scoped evidence 能修少数 operand coverage，但把 extracted JSON 作为第二阶段唯一事实输入后，extractor 的 include/exclude 错误会被放大，answer 失去 raw evidence 兜底。

## 范围

- run_id: `v53_scoped_evidence_lme_diag_4db0bde`
- benchmark: `longmemeval_s`
- subset: `temporal_aggregation_106`
- experiment_kind: `diagnostic`
- input: `outputs/diagnostic/v47_lme_temporal_aggregation_input/prediction_input.jsonl`
- outputs: `outputs/diagnostic/v53_scoped_evidence_lme_diag_4db0bde/`
- experiment dir: `experiments/diagnostic/v53_scoped_evidence_lme_diag_4db0bde/`
- workers: `4`

## 方法

底座是 v42 operation workpad。v53 在 `list_count` / `temporal_lookup` 上启用两阶段 query-time evidence compiler：

- stage 1: 从 top-40 Memory Context 中抽取 `included_items`、`excluded_items`、`canonical_item`、`event_time`、`value`、`calculation`。
- stage 2: 只基于 extracted evidence JSON 输出最终 answer。

外部参考：

- `creating001-agent-memory` 的 query 侧 included/excluded/canonical evidence 组织；舍弃 target phrase、category、sample-level guardrail、gold/judge 相关逻辑。
- `SimpleMem` 的 structured context 和 lossless memory unit 思路；v53 不引入额外 planner。
- `docs/method.md` 中推荐的 `retrieve + evidence table + answer` 主线。

## Git

- commit: `4db0bdeea526792cc045d68cd398382e21dd3679`
- dirty: `true`
- dirty note: 运行时用户修改的 `docs/architecture.md`、`docs/clean_protocol.md` 未纳入本次方法代码；v53 诊断结果目录为新增 artifact。

## 预测指标

- n_samples: `106`
- avg_build_tokens: `79953.094340`
- total_build_tokens: `8475028`
- avg_query_tokens: `5113.226415`
- total_query_tokens: `542002`
- answer max input/output: `131072 / 16384`
- build cache hits/misses/writes: `703 / 0 / 0`
- avg_build_memory_records: `128.358491`
- avg_active_build_memory_records: `115.084906`
- avg_compiled_evidence_items: `34.764151`
- answer_finalizer_applied_count: `1`
- scoped_evidence_applied_count: `106`
- scoped extraction avg query tokens: `4025.603774`
- scoped answer avg query tokens: `1087.622642`
- scoped extraction cache hits/misses/writes: `0 / 106 / 106`
- scoped answer cache hits/misses/writes: `3 / 103 / 103`

Token 口径：build tokens 是新环境冷构建 memory 的逻辑 LLM token；本机 cache 命中只避免重复 API 调用，不把方法成本记为 0。query tokens 包含 scoped extraction + scoped answer 两个 LLM 阶段。

## Judge 结果

- v53 current accuracy: `0.594340` (`63/106`)
- v42 same-106 accuracy: `0.764151` (`81/106`)
- v47 same-106 accuracy: `0.707547` (`75/106`)
- vs v42 gain/loss: `5 / 23`
- same correct / same wrong vs v42: `58 / 20`
- answer changed vs v42: `68`
- DeepSeek judge usage: `27184` total tokens

离线 question_type 诊断只用于复盘，不进入 prediction：

- temporal-reasoning: v42 `49/56` -> v53 `42/56`
- multi-session: v42 `23/40` -> v53 `15/40`
- knowledge-update: v42 `4/5` -> v53 `2/5`
- single-session-user: v42 `5/5` -> v53 `4/5`

## Clean 检查

- prediction pipeline 未使用 gold/reference answer、judge output、benchmark label、sample id、qid、真实 dataset row index 或 test feedback。
- prompt clean scan 扫描 `530` 个文本块，包括 compiled prompt、重建 scoped extraction prompt、scoped answer prompt 和 scoped outputs。
- literal findings: `2`，均为 raw dialogue 中普通助手句子里的 `correct answer`，分类为 `false_positive_raw_dialogue_text`。
- judge、gold、`question_type` 只在预测完成后用于离线评测和诊断。

## 输出文件

- `metrics.json`
- `deepseek_judge.json`
- `judge_comparison_vs_v42_v47_same106.json`
- `prompt_clean_scan.json`
- `config_snapshot.json`
- predictions: `outputs/diagnostic/v53_scoped_evidence_lme_diag_4db0bde/predictions.jsonl`
- traces: `outputs/diagnostic/v53_scoped_evidence_lme_diag_4db0bde/traces.jsonl`

顶层候选配置 `configs/stage1_scoped_evidence_v53_cached.json` 删除，只保留本目录 `config_snapshot.json` 供复盘。

## 下一步

不要把 extracted evidence JSON 作为唯一事实输入来替代 raw evidence。后续应把 scoped evidence 改成 advisory/verification signal，或者转向 build-side typed temporal/entity/profile memory management；任何新方法必须先基于 badcase 和外部代码再设计，不能直接 full。
