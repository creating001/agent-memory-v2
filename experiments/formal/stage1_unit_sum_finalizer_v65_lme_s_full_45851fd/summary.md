# stage1_unit_sum_finalizer_v65_lme_s_full_45851fd

## 结论

v65 失败，不作为主线候选。

LongMemEval-S full DeepSeek judge accuracy 为 `379/500 = 0.758000`，低于原 v42 `387/500 = 0.774000`。相对 v42 的离线比较为 gain/loss `20/28`，net `-8`，answer changed `120/500`。

这次结果不能解释为“纯 finalizer 消融”：v65 跑在 commit `45851fd`，原 v42 跑在 `f7eb076`，中间 compiler/answer 解析代码已有漂移，导致即使 finalizer 只 applied `16/500`，最终 prediction 仍有 `120` 条与原 v42 不同。因此本实验只作为负向候选记录，不继续扩展，也不跑 LoCoMo。

## 方法

v65 基于 v42 配置，只新增两个 prediction-time 机械 finalizer 开关：

- `enable_unit_completion=true`：当 answer 是裸数字，且 question / answer JSON 支持单位时补全单位。
- `enable_additive_quantity_correction=true`：当 question 是通用 total / combined 类问题，且 answer JSON 的 `evidence_report` 暴露同单位 support 数值时做加法一致性修正。

借鉴来源是 creating001 的 evidence extraction + narrow finalizer 思路，但没有迁移其 missing-target、relative-time、benchmark-shaped guardrail 或样本级规则。所有触发只读 question、answer model 的 raw JSON 和 prediction-time trace。

## 关键指标

- benchmark/subset: `longmemeval_s / full`
- git commit: `45851fda371d58eff3d68eec5da1fed933793f2a`
- prediction dirty: `false`
- judge/evidence_recall dirty: `true`，原因是 judge/evidence 文件写入时实验目录已是未跟踪输出；prediction manifest 记录的正式运行状态是 clean。
- n_samples: `500`
- DeepSeek judge: `379/500 = 0.758000`
- judge invalid: `0`
- judge tokens: prompt `93768`, completion `41375`, total `135143`
- evidence recall: `1.0`
- avg_build_tokens: `80346.246`
- total_build_tokens: `40173123`
- avg_query_tokens: `5924.318`
- total_query_tokens: `2962159`
- answer max input/output: `131072 / 16384`
- build cache hits/misses/writes: `3341 / 0 / 0`
- answer cache hits/misses/writes: `500 / 0 / 0`
- embedding cache hits/misses/writes: `247238 / 0 / 0`
- finalizer applied: `16/500 = 0.032`

## 对比

离线比较文件：`judge_comparison_vs_v42.json`

- v42 correct: `387`
- v65 correct: `379`
- transition: `CORRECT->CORRECT 359`, `WRONG->WRONG 93`, `WRONG->CORRECT 20`, `CORRECT->WRONG 28`
- net: `-8`
- answer_changed_count: `120`

主要损失集中在 multi-session 和 temporal-reasoning。部分数值单位修正确实修复了 `3000 -> 3,000 miles`、`2,000 -> 1998` 等 case，但整体被更大的 answer/parser drift 和若干 over-abstain / wrong aggregation 回退抵消。

## 输出

- predictions: `/data/home_new/wujinqi/agent-memory/outputs/formal/stage1_unit_sum_finalizer_v65_lme_s_full_45851fd/predictions.jsonl`
- traces: `/data/home_new/wujinqi/agent-memory/outputs/formal/stage1_unit_sum_finalizer_v65_lme_s_full_45851fd/traces.jsonl`
- metrics: `experiments/formal/stage1_unit_sum_finalizer_v65_lme_s_full_45851fd/metrics.json`
- judge: `experiments/formal/stage1_unit_sum_finalizer_v65_lme_s_full_45851fd/deepseek_judge.json`
- evidence recall: `experiments/formal/stage1_unit_sum_finalizer_v65_lme_s_full_45851fd/evidence_recall.json`
- comparison: `experiments/formal/stage1_unit_sum_finalizer_v65_lme_s_full_45851fd/judge_comparison_vs_v42.json`

## 下一步

删除顶层 v65 config，并撤掉负向 finalizer 源码，保持代码简洁。后续继续从 v42 的 badcase 出发，优先设计 build-to-query memory organization，而不是扩大机械 finalizer。
