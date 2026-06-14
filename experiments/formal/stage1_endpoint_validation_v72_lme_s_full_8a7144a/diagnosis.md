# v72 诊断

## 关键观察

v72 是一个窄改动：只给排序/比较类问题加 endpoint validation。它没有改变 retrieval、build memory、row text、top-k 或 answer 输出上限，因此 changed prediction 只有 15/500。

结果显示该约束没有带来净收益：

- Full judge：383/500 = 0.766。
- v42 修复对照：386/500 = 0.772。
- unchanged prediction 的 judge variance：CORRECT->WRONG 7，WRONG->CORRECT 7，净 0。
- changed prediction 的净变化：CORRECT->WRONG 4，WRONG->CORRECT 1，净 -3。

## 为什么负向

从 changed subset 看，endpoint validation 在 temporal_lookup 上影响最大：

- temporal_lookup：CORRECT->WRONG 3，WRONG->CORRECT 1，WRONG->WRONG 2，CORRECT->CORRECT 2。
- list_count：CORRECT->WRONG 1，CORRECT->CORRECT 6。

这说明当前错误主要不是“缺端点仍强答”一个问题。对于不少样本，v42 已能在完整 raw rows 中做出正确判断；新增规则会让模型更关注 missing endpoint 或 close-but-wrong endpoint，导致过度拒答、答得更绕，或把原本简洁正确的答案变成 judge 不认可的形式。

## 对用户 query-token 假设的反馈

本轮支持“更多 query token 不一定更好”的方向，但也说明单纯加读者约束不是答案：

- v70 试图减少上下文长度，accuracy 从 0.772 掉到 0.758。
- v72 几乎不增加 token，avg query 从 5864.706 到 5884.82，但 accuracy 仍掉到 0.766。

所以当前瓶颈更像是 evidence organization 的质量，而不是 token 数量本身。下一步需要让候选组织更可操作，而不是继续堆 prompt 纪律。

## 后续建议

- 不保留 v72 顶层 config。
- 不保留未被主线使用的 endpoint validation 源码开关，避免代码冗余。
- 下一轮从 v42 出发，先做 badcase 分析，重点看 changed wrong、v42 wrong 但 evidence_recall=1 的样本。
- 新方法应优先考虑 source-preserving candidate organization：保留完整 raw rows，同时用轻量候选表组织 distinct items、time endpoints、newer/older state，而不是用更强拒答规则替代证据组织。
