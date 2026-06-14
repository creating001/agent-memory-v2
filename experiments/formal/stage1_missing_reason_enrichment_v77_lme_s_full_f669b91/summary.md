# v77 missing reason enrichment LongMemEval-S full

## 目的

v73 badcase 显示部分拒答只输出 generic insufficient answer，而 draft JSON 的 `missing` 字段已经说明缺少什么。v77 基于 v73，只验证一个零额外 token 的后处理：当 final answer 是 insufficient/unknown 且 draft JSON 有 `missing` 时，把缺失原因拼进最终拒答。

## Clean 记录

- 预测阶段未使用 gold answer、judge output、benchmark label、sample id、row index、test feedback 或样本级规则。
- finalizer 只读取 prediction-time question、draft answer 和 draft answer JSON。
- 不新增 LLM 调用，不重算答案，不根据评测结果改具体样本。
- answer/build cache hit 仍按 cached usage 计入 token 成本。

## 配置与运行

- benchmark/subset：LongMemEval-S full。
- config：预测时为 `configs/stage1_missing_reason_enrichment_v77_cached.json`；负向结论后顶层配置和源码分支已删除，复现以本目录 `config_snapshot.json` 和 commit 为准。
- git commit：`f669b91`。
- prediction dirty：false。
- workers：8。
- answer max input/output：131072 / 16384。

## 结果

- DeepSeek judge accuracy：0.772，386/500，invalid=0。
- v73 fresh accuracy：0.778，389/500。
- fresh delta vs v73：-0.006。
- evidence recall：1.0，500/500。
- prediction_changed vs v73：42/500。
- changed subset：WRONG->CORRECT 4，CORRECT->WRONG 4，WRONG->WRONG 23，CORRECT->CORRECT 11。
- controlled accuracy using v73 judgments for unchanged predictions：389/500 = 0.778。

## Token 成本

- avg build tokens：80346.246。
- total build tokens：40173123。
- avg query tokens：5864.706。
- total query tokens：2932353。
- build cache：3341 hit / 0 miss / 0 write。
- answer cache：500 hit / 0 miss / 0 write。
- finalizer applied：42/500。

## 输出路径

- predictions：`outputs/formal/stage1_missing_reason_enrichment_v77_lme_s_full_f669b91/predictions.jsonl`
- traces：`outputs/formal/stage1_missing_reason_enrichment_v77_lme_s_full_f669b91/traces.jsonl`
- metrics：`experiments/formal/stage1_missing_reason_enrichment_v77_lme_s_full_f669b91/metrics.json`
- judge：`experiments/formal/stage1_missing_reason_enrichment_v77_lme_s_full_f669b91/deepseek_judge.json`
- evidence recall：`experiments/formal/stage1_missing_reason_enrichment_v77_lme_s_full_f669b91/evidence_recall.json`
- comparison：`experiments/formal/stage1_missing_reason_enrichment_v77_lme_s_full_f669b91/judge_comparison_vs_v73.json`
- badcases：`experiments/formal/stage1_missing_reason_enrichment_v77_lme_s_full_f669b91/delta_badcases.md`

## 结论

v77 不进入主线。更具体的拒答能修复少数缺失说明类样本，但也让部分原本被接受的拒答被判错；changed subset 净 0，fresh full 低于 v73。该代码分支不值得保留，后续应继续面向 multi-session/temporal 的证据聚合和 reader 稳定性，而不是继续做拒答措辞微调。
