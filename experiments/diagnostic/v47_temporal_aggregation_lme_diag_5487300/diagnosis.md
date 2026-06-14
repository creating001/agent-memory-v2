# v47 诊断

## 失败原因

v47 的目标是修复 v42 在 temporal aggregation / count 类问题上的 answer-stage 计算错误，但实际失败点有两个：

1. `aggregation_report_contract` 让每条 prompt 多输出更复杂 schema，诊断子集 avg query tokens 从 v42 同集 `6729.821` 增到 `7209.038`。
2. `evidence_report_count_increment_consistency` 过度相信 answer model 自己填的 `count_increment`，没有可靠去重和 item scope 判定，导致多条重复计数。

典型错误：

- `How many fitness classes do I attend in a typical week?`：v42=`5` 正确，v47=`8`，把重复课程再次计数。
- `How many pieces of jewelry did I acquire in the last two months?`：v42=`3` 正确，v47=`4`，重复 emerald earrings。
- `How many different cuisines have I learned to cook or tried out in the past few months?`：v42=`4` 正确，v47=`7`，把同一 cuisine 多次出现重复计数。
- `How many graduation ceremonies have I attended in the past three months?`：v42=`3` 正确，v47=`4`，重复 Emma's preschool graduation ceremony。

这说明“让 answer model 在 evidence_report 里声明 count_increment，再由机械 finalizer 求和”不是稳定方案。它 clean，但不够 robust，也不够 general。

## 离线对比

文件：`judge_comparison_vs_v42_same106.json`

- n_shared: `106`
- v42 correct: `81`
- v47 correct: `75`
- gains: `5`
- losses: `11`
- answer_changed: `37`
- finalizer_applied: `11`

v47 有一个局部正向信号：offline temporal-reasoning 子类从 `49/56` 到 `51/56`。但 multi-session 从 `23/40` 降到 `17/40`，说明 schema 和 finalizer 对跨会话 list/count 的副作用更大。

## Token 与成本

文件：`full_query_token_estimate.json`

v47 只在 106 条 temporal aggregation 诊断样本上改变 prompt，按 v42 full 500 条估算：

- v42 full avg query tokens: `5865.644`
- selected weighted delta: `+101.594`
- estimated full avg query tokens: `5967.238`

这个估算勉强低于 6K，但没有运行 full 的价值。build tokens 使用 v42 cache 的 cached usage 计入冷构建逻辑成本，不把 cache hit 当成 0。

## Clean 复核

文件：`prompt_clean_scan.json`

scan 命中 `correct answer` 一次，但上下文来自 raw dialogue：

`assistant: As an AI language model, I would need to know which movie you are referring to, so I could provide the correct answer.`

这不是 benchmark 正确答案、gold、judge 或标签泄漏。v47 的失败是方法质量问题，不是 clean 问题。

## 取舍

保留的启发：

- aggregation/count/list 的确是 v42 LongMemEval temporal wrong 的重要来源。
- temporal-reasoning 上 v47 有局部正向，说明更明确的 operation guidance 不是完全无效。
- count/list 不能只靠 answer-stage 字段自报，需要更早的 candidate item 管理和去重。

舍弃：

- 不保留 `enable_evidence_report_count_correction` 作为主线。
- 不保留顶层 v47 config。
- 不把更长 evidence_report schema 继续扩展到 full。

## 下一步建议

下一版应该更像一个 general Agent Memory system，而不是 answer finalizer：

- build/query 侧先形成 source-preserving candidate item set，每个候选带 raw source、时间、canonical text、dedup key 和 include/exclude reason。
- compiler 只给 answer model 一个短的候选表，而不是要求它在长 JSON 里重新构造计数贡献。
- typed memory 继续只作为 source selection / coverage signal，不能替代 raw evidence。
- 参考外部代码时优先看 `creating001-agent-memory` query 组织、`SimpleMem` structured context、`xMemory` episode expansion、`EverOS` atomic fact -> episode parent retrieval，并明确舍弃其中不 clean 或过重的部分。
