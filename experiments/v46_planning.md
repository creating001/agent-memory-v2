# v46 规划：Temporal Session Thread Only

## 背景

v45 在 LongMemEval-S route-stratified 20 条上相对 v42 净增 `+1`，修复了 animal shelter fundraising dinner 的 exact-date case，且无新增错误。但 v45 的 full route-mix avg query token 估算为 `6001.2865`，略超 `6000` 主线预算，不能直接跑 full。

badcase 对比显示：

- v42 按 retrieval score 排序，先看到同一事件的 `back in February`，后面才看到 `Valentine's Day`。
- v45 按 session/thread 顺序把同一会话连起来，`Valentine's Day` 出现在同一 episode 的后续 turn，更容易被 answer model 作为精确化证据使用。
- v45 同时加入了 1 条 typed memory guide，因此还不能判断收益来自 session ordering 还是 memory guide。

v46 只隔离 session ordering：保留 temporal route 的 `session_thread` raw evidence layout，关闭 typed memory guide。

## 方法设计

底座：v42 operation workpad。

配置：`configs/stage1_temporal_session_thread_v46_cached.json`

只对 `temporal_lookup` 开启：

- `context_layout=session_thread`
- `structured_guide_include_memory=false`
- `max_memory_records=0`

保持不变：

- retrieval/build/evidence_report/operation_workpad 与 v42 等价。
- non-temporal route prompt 与 v42 等价。
- answer cache 复用 v42 exact-prompt cache；cache hit 仍按 stored usage 计入 logical query tokens。
- answer max input/output：`131072/16384`。

## 外部方法参考

- xMemory：episode/thread 视角能让同一会话内的分散线索按原始顺序呈现。
- SimpleMem：typed memory 可以做 structured context guide，但 v46 刻意关闭它，做消融。
- Mnemis：selected memory node 应回链 episode；v46 只验证回链后的 episode ordering。
- Graphiti/Zep：temporal/provenance 思路保留为 source-aware ordering，不引入图数据库或 graph rule。

取舍：v46 不新增 build schema、不新增 LLM call、不把 typed memory 当事实来源；它只验证一个通用 memory context organization 能力。

## Clean 边界

- 只读取 question text、visible question_time、raw dialogue、retrieval result 和 build-stage memory source links。
- 不使用 gold/reference answer、judge output、benchmark hidden labels、sample id、qid、row index、test feedback 或样本级规则。
- DeepSeek judge 仅用于 prediction 完成后的离线评测。

## Gate 计划

先跑 LongMemEval-S route-stratified 20 条 diagnostic：

- input：`outputs/diagnostic/v35_lme_route_stratified_probe/prediction_input.jsonl`
- config：`configs/stage1_temporal_session_thread_v46_cached.json`
- workers：`4`

通过条件：

- 20/20 prediction 成功。
- answer max input/output = `131072/16384`。
- avg query tokens <= `6000`，max query tokens < `8000`。
- estimated full avg query <= `6000`，并且要有明确安全余量。
- session_thread 只在 `temporal_lookup` 生效，compiled memory records 应为 `0`。
- 同子集 DeepSeek judge 相对 v42 净正向，且不引入 regression；重点看是否保留 exact-date 修复。

## 预期决策

如果 v46 保留 v45 的 exact-date gain，并且 full token estimate 明确低于 `6000`，再考虑 LongMemEval-S full。若 v46 丢失 gain，说明 v45 的收益主要来自 typed memory guide；下一步不能继续加 prompt，而应转向 build-side temporal memory schema 或更轻的 evidence-side date normalization。
