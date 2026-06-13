# v46 诊断

## 主要发现

v46 关闭了 v45 的 typed memory guide，只保留 temporal session-thread raw evidence layout。结果说明：

- session ordering 本身足以把 animal shelter fundraising dinner 从月份级答案修到 `February 14, 2023`。
- typed memory guide 不是该 badcase 的必要条件。
- memory prompt records 为 `0`，因此 v46 比 v45 更 clean、更轻。

但 raw DeepSeek same-20 accuracy 只有 `15/20`，与 v42 持平。新增的 loss 是 same-answer judge variance：photography recommendation 的 v42/v46 answer 完全相同，但 judge label 从 correct 变 wrong。因此不能把 raw judge 结果解释为方法实质回退，也不能把 v46 说成通过质量 gate。

## Token 诊断

probe token：

- avg_query_tokens：`5722.5`
- max_query_tokens：`7274`
- avg_build_tokens：`81690.45`

full route-mix 估算：

- v42 full avg query：`5865.644`
- v46 temporal_lookup 相对 v42 probe 增量：`+311.25`
- LongMemEval-S full temporal_lookup 占比：`161/500`
- estimated full avg query：`5965.8665`

v46 明确低于 `6000`，比 v45 的 `6001.2865` 更稳。

## Route 审计

`route_feature_audit.json` 显示：

- `temporal_lookup`：4/4 启用 session_thread，0/4 启用 memory guide，compiled memory records 平均 `0`。
- 其他 route：未启用 session_thread 或 memory guide，compiled memory records 为 `0`。

这说明 v46 是一个干净的 query-side context organization 消融。

## Clean 诊断

`prompt_clean_scan.json` 只扫描实际 `compiled_context.prompt`：

- forbidden prompt counts：`{}`
- benchmark category term hits：`[]`

config snapshot 中的 forbidden terms 只出现在 clean prohibition note 中，不是 prompt 或规则。

## 决策

不直接跑 LongMemEval-S full。理由是 strict DeepSeek same-20 未净增，尽管 changed-answer delta 为正。下一步优先做更系统的 temporal badcase 诊断：检查 v42 full 的 temporal wrong cases 中，哪些属于同 session 后续 turn 精确化、mention date/event date 混淆、或相对日期解析缺失，再决定是扩大 session-thread、还是改 build-side temporal/event schema。
