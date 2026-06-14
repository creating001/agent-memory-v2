# 诊断

## 背景

v42 修复控制已经证明 LongMemEval-S full 的 evidence recall 为 1.0，avg query tokens 约 5.86K。v66 将上下文固定压缩到约 5.24K 后 accuracy 明显下降，说明 query token 不是越多越好，但机械截断也会丢失 answer 所需细节。

v69 针对另一类错误：draft 已经有 support evidence，但最终答复仍是 insufficient / unknown / missing。它只在运行时 draft 自己触发 uncertain，并且 evidence_report 里至少有 1 条 support item 时调用 repair，试图把 broad repair 收窄到更可控的子集。

## 方法取舍

采用的部分：

- 使用 draft JSON 的 `answer` 与 `evidence_report` 做运行时 sufficiency 检查。
- repair context 从原 compiled context 中裁剪，不读取任何离线 label 或 judge。
- repair prompt 要求不能引入 context 中没有出现的具体名称，避免 profile/preference hallucination。
- 新 repair cache namespace，避免污染 v42 answer cache。

舍弃的部分：

- 不采用外部实现中依赖 benchmark strategy / hand-written guardrail 的样本级逻辑。
- 不使用 question_type、gold answer、judge label、sample id、row index 或测试反馈来决定 repair。
- 不把 repair 结果作为反向训练或规则记忆写回 prediction pipeline。

## 结果

Full judge：

- v69：380/500 = 0.760。
- v42 修复控制：386/500 = 0.772。
- by type：
  - knowledge-update：64/78 = 0.820513。
  - multi-session：84/133 = 0.631579。
  - single-session-assistant：54/56 = 0.964286。
  - single-session-preference：12/30 = 0.400000。
  - single-session-user：65/70 = 0.928571。
  - temporal-reasoning：101/133 = 0.759398。

对比 v42 修复控制：

- prediction_changed_count：6/500。
- changed predictions：WRONG->CORRECT 2，WRONG->WRONG 4。
- unchanged predictions：CORRECT->WRONG 13，WRONG->CORRECT 5，CORRECT->CORRECT 373，WRONG->WRONG 103。

因此，v69 的 0.760 不能简单解释为 repair 改坏了 6 条。实际改动子集是小正向，但 full judge 重跑在未改答案上有显著 variance。正式结论仍以 full accuracy 为准：v69 没有超过 v42，不能作为主线。

## Badcase 观察

6 条 changed prediction 中：

- 修复了 2 条拒答：
  - preference publication/conference 建议题，从 insufficient 改成医疗影像 AI / explainable AI 方向，judge correct。
  - 年龄差计算题，从 insufficient 改成 `7`，judge correct。
- 仍错误 4 条：
  - 房产数量题回答 `3`，gold 需要 4 个 viewed properties。
  - sculpting duration 回答 `9 weeks`，gold 是 3。
  - cultural events 题给出 Eventbrite / Meetup 等外部平台，未稳定贴合用户语言练习偏好。
  - show/movie 题给出政治/保守倾向类别，偏离 stand-up comedy storytelling preference。

这说明 supported repair 能把少数“有证据但拒答”的 case 拉回来，但 profile/preference 场景仍容易从局部证据泛化成 unsupported recommendation。即使 prompt 禁止具体新名称，模型仍可能输出过宽平台或类别，增加噪声。

## Token 与噪声判断

v69 avg query tokens 为 5981.198，几乎压到 6K 主线预算上限；v42 为 5864.706，v66 为 5235.538。三者合看：

- 继续增加 query token 不可靠，v69 只获得极小局部收益。
- 简单降低 query token 也不可靠，v66 净 -9。
- 当前更需要提高 context precision / evidence density，而不是把上下文长度当目标。

下一阶段方法应让 compiler 更清楚地区分：

- answer-critical rows 与背景 rows。
- event fact 与 profile preference。
- temporal endpoint 与 mention/update rows。
- list/count 的候选集合与排除项。

## 结论

v69 是一个 clean、token-safe、可追溯的负向/弱正向组件实验。它可以作为“不要继续 broad answer repair”的证据，不作为当前主线配置保留。后续要把精力放在 build-stage memory organization 和低噪声 query compiler 上，特别是 event chain、profile/event 双通道、候选聚类和冲突链，而不是继续扩 repair prompt。
