# Diagnosis for stage1_temporal_event_contract_v29_lme_s_full_23e8b78

## 诊断结论

v29 没有达到预期的 LME 整体提升。DeepSeek judge accuracy 为 `0.762`，低于 v28 `0.766`，距离 LongMemEval-S baseline target `0.800` 仍差 `19/500` correct。

这个结果说明：只在 query-side prompt/report 层区分 `mention_time` 和 `event_time` 不足以稳定提升 LongMemEval；它能修一部分时间题，但会引入新的过度匹配和错误聚合。

## 改对了什么

v29 相对 v28 新增 `20` 条 correct，主要集中在：

- temporal_lookup：更会使用相对时间短语，例如 `last week`、`a week ago`、`month ago`，而不是直接答 Memory Date。
- fact_lookup：部分 slot selection 更具体，例如 coupon redeemed location、recent relocation after update、previous vs latest state。
- single-session-assistant / single-session-user：少数答案因为包含更完整日期或上下文被 judge 通过。

代表性改对：

- volunteered at fundraising dinner: `February` -> `February 14, 2023`
- workshops in last four months: `$500` -> `$720`
- grandma age gap: insufficient -> `43`
- book finished a week ago: insufficient -> `The Nightingale by Kristin Hannah`
- became a parent first: `Rachel` -> `Alex`
- usual gym time after update: `7:00 pm` -> `6:00 pm`

## 改错了什么

v29 相对 v28 新增 `22` 条 wrong，错误集中在：

- current_state：把相关但非当前/最新状态的时间候选当成答案。
- list_count：visible evidence report 加了 temporal 字段后，部分聚合题少算或覆盖了 v28 的候选表收益。
- insufficient evidence：对缺失 endpoint 的时间题更容易给出看似可算的日期/天数。
- preference/profile：答案变长但丢掉关键个性化约束，judge 反而不通过。

代表性新增错误：

- different doctors: `3 different doctors...` -> `3`
- total game hours: `140 hours` -> `90`
- kitchen items: `5` -> `4`
- Hawaii + Seattle travel days: insufficient -> `10`
- museums order: 正确 6 个 museum -> 加入错误的 Children's Museum
- bought iPad before Holiday Market: insufficient -> `7`
- most recent family trip: `Paris` -> `Hawaii`
- parents staying in US: `nine months` -> `97 days`

## 方法判断

v29 的 clean 性没有问题：route 只来自 question text / question_time，compiler 只使用 raw memory context、timestamp 和本地 temporal normalization；没有使用 gold、judge、benchmark labels、sample ids 或 test feedback。

但性能上，v29 不适合作为统一主线：

- temporal_lookup 净 `+2` 说明方向不是完全错。
- current_state 净 `-3`、list_count 净 `-2` 抵消了 temporal/fact 收益。
- avg query tokens 从 v28 的 `5736.928` 上升到 `5807.19`，仍在预算内但压缩空间变小。
- query tail `174/500` 超过 6K，比 v28 的 `147/500` 更重。

## 设计复盘

参考外部方法后的取舍基本合理：

- Graphiti/Zep 的 temporal validity 启发是对的，但仅靠 prompt 字段模拟 `valid_at` 不够稳定。
- SimpleMem 的 lossless timestamp normalization 更适合 build-side typed memory，而不是临时 query-side 提醒。
- xMemory / EverOS 的 episode/source 回链仍重要，v29 没改 retrieval，所以召回侧没有新增收益。
- creating001 的 temporal extraction 思路有参考意义，但继续堆自然语言规则会接近 benchmark prompt tuning，不应作为下一步主路线。

## 下一步建议

不要在 v29 这个 prompt 上继续堆规则。下一轮更值得做：

- build-side typed event/state schema：由 LLM 在 build 阶段抽取 `mention_time`、`event_time`、`valid_from`、`valid_to`、`event_type`、`source_ids`。
- typed record 管理：合并重复 event/state，保留 active/superseded，避免 current_state 被旧事件覆盖。
- query-side 使用 typed records 做候选组织，但最终答案仍回到 raw evidence。
- 做 ablation：v28 raw+typed-source baseline vs typed-event build on/off vs typed-event context on/off。

由于 v29 对 LME 整体为负，是否继续跑 LoCoMo 需要谨慎。考虑到 v29 主要针对 LoCoMo badcase 中的 mention/event time 混淆，并且 LoCoMo v28 与 v18 只差 1 条，仍可跑 LoCoMo full 作为验证；但若 LoCoMo 也不提升，应回到 build-side memory 管理，而不是继续 query prompt ablation。
