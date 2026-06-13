# Diagnosis for stage1_temporal_event_contract_v29_locomo_nonadv_full_c7b8390

## 诊断结论

v29 是当前 LoCoMo non-adversarial full 最好结果：DeepSeek judge accuracy `0.761688`，比 v28 `0.737662` 净增 `37/1540`。这次提升足够说明 temporal event contract 是 LoCoMo 上的重要方向。

但 v29 仍没有达到 LoCoMo baseline target `0.780`，且 LongMemEval-S full 低于 v28。因此它不是最终主线，只能作为下一轮 build-side typed temporal/event memory 的依据。

## 为什么有效

v28 的 LoCoMo badcase 里，很多证据已经召回，但 answer model 把 row/session date 当成事件日期。v29 把 temporal route 的证据报告改成：

- `mention_time`: Memory Date
- `time_phrase`: row text 中的显式或相对时间短语
- `event_time`: 目标事件时间

这使模型更容易把 “last week / weekend before / Friday before / Tuesday before” 归到事件本身，而不是归到记录日期。

最主要收益：

- category 2: `0.619938 -> 0.732087`，净 `+36`
- temporal_lookup: `0.647929 -> 0.754438`，净 `+36`
- overall: v29 only `74`，v28 only `37`

## 仍然失败在哪里

- baseline target 仍差约 `28/1540` correct。
- category 4 从 `0.829964` 降到 `0.826397`，说明通用事实/开放问答受到轻微干扰。
- profile_preference 从 `0.795918` 降到 `0.775510`，说明 temporal contract 对偏好推荐没有帮助，甚至可能让回答更啰嗦或偏离核心偏好。
- 部分 temporal case 被过度归一化，例如原本可接受的具体日期/范围被替换成错误相邻时间。
- list_count 只净 `+2`，说明列表/计数问题的主要瓶颈不是 mention/event time，而是候选覆盖、去重和 scope 判断。

## Clean 与成本

- 方法没有使用 gold answer、judge output、benchmark label、category、sample id、row index 或 test feedback 参与预测。
- prediction manifest dirty 为 `true`，因为用户在 run 期间修改了 `docs/architecture.md` 和 `docs/clean_protocol.md`；prediction code/config 启动时为 clean `c7b8390`。
- build token 统计为 cold-start logical LLM cost；cache hit 只减少实际重复调用，不把方法成本记为 0。
- avg build tokens `58386.0078`，avg query tokens `3932.5604`，满足 LoCoMo 主线预算。
- answer LLM max input/output: `131072/16384`。
- answer finalizer disabled。

## 对方法设计的含义

v29 验证了一个关键判断：LoCoMo 的主要缺口之一不是单纯召回不足，而是 memory context 中时间语义组织不足。尤其是用户说 “last week / weekend before” 时，系统要知道该短语描述的是事件时间，而不是对话记录时间。

但 query-side prompt contract 不是最稳的长期方案。它依赖 answer model 遵守字段语义，且会让非 temporal 问题受到 prompt 形态变化影响。更稳的方向是让 build-stage LLM 直接构建 typed event/state memory：

- 每条 event/state 记录 `mention_time` 和 `event_time`。
- 对持续状态记录 `valid_from` / `valid_to`。
- 对更新类事实记录 supersedes / updated_by。
- 保留 source_ids，query 时回链 raw turn 定案。
- 对 profile/preference 与 one-off event 分通道管理。

## 下一步计划

下一轮不应再直接全量跑一个小 prompt 改动。应先做：

- 从 v29 LoCoMo both_wrong 和 v28_only 中抽样分析，确认剩余错误是 retrieval miss、event_time 误归一化、profile/event 混淆、list dedup，还是 answer slot 错误。
- 继续读外部 build-side 实现：LangMem profile update、Memobase event/profile delta、MIRIX episodic/semantic/core memory、Graphiti temporal validity、SimpleMem lossless memory。
- 设计 v30 typed temporal/event build schema，并明确 ablation：
  - v28 baseline
  - v29 query-side temporal contract
  - typed-event build on/off
  - typed-event context on/off
  - profile/event separation on/off

只有当设计能同时解释 LoCoMo temporal 提升和 LME 不回退时，才值得再次跑 LongMemEval-S full 与 LoCoMo full。
