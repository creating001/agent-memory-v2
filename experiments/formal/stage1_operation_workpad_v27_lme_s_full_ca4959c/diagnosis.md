# Diagnosis for stage1_operation_workpad_v27_lme_s_full_ca4959c

## 诊断结论

v27 是一个中性偏负的 query-side 消融，不应扩展到 LoCoMo full，也不应作为当前主线。它满足 clean 和 token 预算，但 DeepSeek judge accuracy 只有 `0.742`，低于 v26 的 `0.746`，距离 LongMemEval-S baseline target `0.800` 还有 `29/500` correct 的缺口。

## 关键观察

- v27 vs v18: both_correct `346`，v18_only `20`，v27_only `25`，both_wrong `109`。
- v27 vs v26: both_correct `345`，v26_only `28`，v27_only `26`，both_wrong `101`。
- 与 v26 相比，v27 的 changed-answer 净收益为 `-2`；同答案 judge 差异只有 `3` 条，不足以解释整体结论。
- source/session coverage diagnostic 为 `1.0`，说明 LME 上大多数错误不是“完全没召回参考 session”，而是召回后读错、漏聚合、错误拒答或把相邻事实当成答案。
- avg query tokens `5259.276`，仍在 6K 预算内；本次不是靠超预算换分，也不是因为 query token 太低导致明显不可比。

## 分类型变化

- `multi-session`: v26 `0.654` -> v27 `0.571`。这是最重要的回退，说明 v26 的结构化答案契约虽然有副作用，但对多证据/列表类聚合确实有帮助。
- `temporal-reasoning`: v26 `0.789` -> v27 `0.767`。私有 workpad 没有完全保住结构化契约的时间题收益。
- `single-session-preference`: v26 `0.300` -> v27 `0.500`。v26 的结构化契约会干扰偏好类回答，v27 在这里恢复明显。
- `knowledge-update`: v26 `0.731` -> v27 `0.808`，但仍略低于 v18 `0.821`。
- `single-session-user`: v18 `0.943` -> v27 `0.871`，出现了一些不必要的 insufficient 或错槽位答案。

## 示例错误模式

- 错槽位：问题问“在哪里 redeem coupon”，v27 回答 “from email inbox”，而 gold 是 `Target`。说明 workpad 没能稳定区分动作来源和执行地点。
- 过度保守：问题问最近使用的 music streaming service，v27 回答信息不足，而 v18/v26 能答 `Spotify`。
- 计数漏项：model kits 题 v26 答 `5`，v27 答 `4`。这说明仅给私有计数纪律不如显式结构化收集候选项稳定。
- 粒度不足：日期题只答 `February`，而 gold 需要 `February 14th`；说明日期/事件 slot 的抽取仍不够稳。

## Clean 与成本检查

- prediction commit clean: `ca4959ce3a589ef8e077b7040960ace434e8543e`
- prediction dirty: `false`
- DeepSeek judge 和 evidence/source diagnostic 只在预测完成后离线读取 labels，不进入预测流程。
- build token 统计为 cold-build logical LLM cost，即使 build cache hit 也计入新环境构建 memory 的逻辑成本。
- avg build tokens `80346.246`，avg query tokens `5259.276`，均满足主线预算。
- answer LLM 配置符合协议：max input `131072`，max output `16384`。

## 下一步

不要继续做“只换 prompt 语气”的小消融。下一轮需要能同时保留 v26 的 multi-session/list 收益和 v27/v18 在 preference/KU 上的稳健性。更合理的方向是：

- 保留 v26 的显式候选收集思想，但只作为 reader 内部证据组织，不改变最终答案 schema。
- 引入更强的 source-aware evidence table 或 typed view，让模型先对候选 evidence 做 slot 对齐、去重和冲突检查。
- 如果做 build-side 改动，必须重新跑完整预测，并记录 cold-build logical tokens；但收益目标应至少瞄准 LME `>=0.80` 和 LoCoMo `>=0.78`。
- 下一次 full run 前必须先基于 badcase 和外部实现设计清楚，不再为单个小 prompt 变化浪费全量评测。
