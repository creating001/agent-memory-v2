# v45 诊断

## 主要发现

v45 是一个正向但预算不稳的 diagnostic。它只改变 `temporal_lookup` 的 context organization：把 evidence 按 session/thread 组织，并加入 1 条 row-linked build memory guide。该改动在 20 条 route-stratified probe 上把 DeepSeek judge 从 v42 的 `15/20` 提到 `16/20`，没有新增错误。

唯一改对的 case 是 temporal exact-date：模型从月份级答案 `February 2023` 变成日期级答案 `2023-02-14`。这说明 session/thread 组织和少量 typed memory guide 对某些 temporal grounding 有帮助。

## Token 诊断

probe 本身通过平均 query token gate：

- avg_query_tokens：`5744.5`
- max_query_tokens：`7352`
- avg_build_tokens：`81690.45`

但 full route-mix 估算未通过：

- v42 full avg query：`5865.644`
- v45 temporal_lookup 相对 v42 probe 增量：`+421.25`
- LongMemEval-S full temporal_lookup 占比：`161/500`
- estimated full avg query：`6001.2865`

这个数只超预算约 `1.29` tokens，但没有安全余量。按项目约束，不能把它作为主线 full 候选。

## Route 审计

`route_feature_audit.json` 显示改动只作用于 temporal route：

- `temporal_lookup`：4/4 启用 session_thread，4/4 启用 memory guide，最终 compiled memory records 平均 `1.0`。
- `current_state`、`fact_lookup`、`list_count`、`profile_preference`：均未启用 session_thread 或 memory guide，最终 compiled memory records 为 `0`。

这说明 v45 是受控消融，不是全局 prompt 膨胀。

## Clean 诊断

`prompt_clean_scan.json` 只扫描实际 `compiled_context.prompt`：

- forbidden prompt counts：`{}`
- benchmark category term hits：`[]`

config snapshot 里出现 forbidden terms 是 clean note 的禁止声明，不是 prediction prompt。judge/gold 只用于 `judge_comparison_vs_v42_same20.json` 的离线分析。

## 取舍

采用：

- xMemory / SimpleMem / Mnemis / Graphiti/Zep 的共同思路：typed memory 只作为指向 raw evidence 的 guide，最终仍回到 raw dialogue。
- temporal route 的 session ordering，降低 answer 阶段把月份、事件时间和提及时间混在一起的概率。

舍弃：

- 不把 typed memory 当唯一事实来源。
- 不增加新的 build schema 或额外 LLM call。
- 不用 benchmark label、sample id、gold、judge 或样本级规则。

## 决策

不跑 LongMemEval-S full。v45 证明方向有价值，但 token 预算太贴边。下一步应做更小的 v46 gate：保留 temporal session ordering，关闭或进一步压缩 memory guide，观察是否还能保留 exact-date gain，同时让 estimated full avg query tokens 明确低于 `6000`。
