# 诊断

## 背景

v70 证明，对 `list_count/current_state` 直接做 query snippet 会破坏 list/count 候选细节。进一步 badcase 发现，当前 route 中裸 `which` 会把很多顺序比较题归入 `list_count`，例如“Which project did I start first...”。这类题更像 temporal order，而不是列表计数。

v71 因此尝试一个更小的 route 修正：只用 question text 中的 `first/earliest/latest/order` 等顺序信号把问题路由到 `temporal_lookup`。

## 实验控制

正式 run 使用 seeded answer cache：

- 从 v42 clean prediction traces seed v71 新 answer cache namespace。
- seed 只读 prediction-time prompt、answer、raw_response 和 token usage。
- v71 prediction 中 answer cache hits/misses 为 462/38。
- prediction changed 只有 11 条，因此对比主要反映 route change，而不是重新生成噪声。

## 结果

Full judge：

- v71：385/500 = 0.770。
- v42 修复控制：386/500 = 0.772。
- evidence_recall：1.0。
- avg query tokens：5912.454，仍在 6K 预算内。

Changed prediction：

- CORRECT->CORRECT：6。
- CORRECT->WRONG：1。
- WRONG->CORRECT：1。
- WRONG->WRONG：3。

典型变化：

- 修复：`Who did I meet first, Mark and Sarah or Tom?` 从 `Mark and Sarah` 改为 `Tom`。
- 回退：`Which project did I start first, the Ferrari model or the Porsche 991 Turbo S model?` 从正确拒答改为 `The Ferrari model`。这说明 route 改成 temporal 后，answer model 更愿意基于相邻相似项目做过度推断。
- 多个 order-list 题只是格式变长，judge 仍 correct 或仍 wrong。

## 判断

v71 的问题不是 clean，而是收益不足。顺序 route 确实更符合部分问题的信息需求，但仅改变 route 不足以让 answer 稳定处理“缺少其中一个候选端点”的 abstention，也不能修复完整 order-list 排序。它需要更强的 candidate endpoint validation，而不是只换 route。

因此：

- 不保留 v71 顶层 config。
- 不保留 v71 route code 作为当前主线默认行为。
- formal 记录保留，用于说明单独 router 修正中性。

## 下一步

下一阶段应做 endpoint/candidate validation：

- order/comparison：明确列出候选 A/B 的 source row、event time、missing endpoint。
- list/count：保留完整 raw rows，额外提供 dedup candidate set。
- current-state：提供 newer/older conflict chain。

这些都应是 source-preserving compiler organization，而不是 route-only 或 snippet-only。
