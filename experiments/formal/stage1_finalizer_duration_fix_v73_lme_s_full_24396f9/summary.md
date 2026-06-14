# v73 duration finalizer fix LongMemEval-S full

## 目的

修复 v42 中一个明确的 query-side 后处理问题：机械 duration decimal rounding finalizer 在 LongMemEval-S full 中唯一一次触发时，把 answer model 草稿中的正确答案 `3.5 weeks` 改成了 `4 weeks`。v73 从 v42 出发，只关闭这个 rounding finalizer，不改 retrieval、build memory、prompt、answer model 或 answer cache。

## Clean 记录

- 预测阶段未使用 gold answer、judge output、benchmark label、sample id、row index、test feedback 或样本级规则。
- 改动只基于 prediction-time trace 中的 finalizer 行为和 raw answer JSON；评测标签只用于离线诊断。
- answer cache 使用 v42 原 cache namespace；cache hit 仍按 cached usage 计入 query token，表示新环境真实 query LLM 成本。

## 配置与运行

- benchmark/subset：LongMemEval-S full。
- config：`configs/stage1_finalizer_duration_fix_v73_cached.json`。
- git commit：`24396f94cd336f5c1edc020bda8d769465197622`。
- prediction dirty：false。
- workers：4。
- answer model：Qwen/Qwen3-30B-A3B-Instruct-2507。
- answer max input/output：131072 / 16384。

## 结果

- DeepSeek judge accuracy：0.778，389/500，invalid=0。
- v42 修复复现对照：0.772，386/500。
- delta：+0.006。
- evidence recall：1.0，500/500。
- prediction changed：1/500。
- changed subset：WRONG->CORRECT 1。
- unchanged prediction judge variance：WRONG->CORRECT 8，CORRECT->WRONG 6，净 +2。

## Token 成本

- avg build tokens：80346.246。
- total build tokens：40173123。
- avg query tokens：5864.706。
- total query tokens：2932353。
- build cache：3341 hit / 0 miss / 0 write。
- answer cache：500 hit / 0 miss / 0 write。
- finalizer_applied_count：0。

## 输出路径

- predictions：`outputs/formal/stage1_finalizer_duration_fix_v73_lme_s_full_24396f9/predictions.jsonl`
- traces：`outputs/formal/stage1_finalizer_duration_fix_v73_lme_s_full_24396f9/traces.jsonl`
- metrics：`experiments/formal/stage1_finalizer_duration_fix_v73_lme_s_full_24396f9/metrics.json`
- judge：`experiments/formal/stage1_finalizer_duration_fix_v73_lme_s_full_24396f9/deepseek_judge.json`
- evidence recall：`experiments/formal/stage1_finalizer_duration_fix_v73_lme_s_full_24396f9/evidence_recall.json`
- v42 对比：`experiments/formal/stage1_finalizer_duration_fix_v73_lme_s_full_24396f9/judge_comparison_vs_v42_repro.json`

## 结论

v73 是正向小修复，应保留为当前 LongMemEval-S 主线配置。它不解决主要剩余错误，但去掉了一个确定有害的机械后处理，且不增加 token 成本。下一步应继续从 v73 出发，重点处理 multi-session temporal/list/count 的候选覆盖、去重和算术组织问题。
