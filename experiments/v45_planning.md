# v45 规划：Temporal Session Guide Token-Safe

## 背景

v44 在 20 条 route-stratified gate 上相对 v42 净 `+1`，修复了 animal shelter fundraising dinner 的 exact-date case：

- v42：`February 2023`
- v44：`2023-02-14`

但 v44 full token estimate 为 `6064.479` avg query tokens，略超 `6000` 目标。根因是 temporal_lookup 的 session-thread + 3 条 row-linked memory guide 开销偏高。

v45 只做必要收窄：保留 session-thread 和 row-linked memory guide 的机制，把 `max_memory_records` 从 `3` 降到 `1`。

## 方法设计

底座：v42/v44。

配置：`configs/stage1_temporal_session_guide_v45_cached.json`

只对 `temporal_lookup` 开启：

- `context_layout=session_thread`
- `structured_guide_include_memory=true`
- `memory_record_source=evidence_rows`
- `memory_order=question_overlap`
- `max_memory_records=1`

与 v44 相同：

- non-temporal route prompt 与 v42 等价。
- answer cache 复用 v42 exact-prompt cache；cache hit 仍按 stored usage 计入 logical query tokens。
- answer max input/output `131072/16384`。

## 外部方法参考

- xMemory：episodic/raw-message 回链。
- SimpleMem：typed memory 只作为 structured context guide。
- Mnemis：selected memory node 回链 episode。
- Graphiti/Zep：temporal/provenance 思路。

v45 的取舍是更保守：不增加 build schema，不做 graph，不新增 LLM call，只验证最小 temporal source-linked guide 是否保留收益。

## Clean 边界

- 只读取 question text、visible question_time、raw dialogue、retrieval result 和 build-stage memory。
- 不使用 gold/reference answer、judge output、benchmark hidden labels、sample id、qid、row index、test feedback 或样本级规则。
- DeepSeek judge 仅用于 prediction 完成后的离线评测。

## Gate 计划

先跑 LongMemEval-S route-stratified 20 条 diagnostic：

- input：`outputs/diagnostic/v35_lme_route_stratified_probe/prediction_input.jsonl`
- config：`configs/stage1_temporal_session_guide_v45_cached.json`
- workers：`4`

通过条件：

- 20/20 prediction 成功。
- answer max input/output = `131072/16384`。
- avg query tokens <= `6000`，max query tokens < `8000`。
- estimated full avg query <= `6000`。
- session_thread 和 activated_build_memory 只在 temporal_lookup prompts 出现。
- 同子集 DeepSeek judge 相对 v42 保持净正向，最好保留 `d823172b5baf1eff81acb20c` 的 exact-date 修复且无 regression。

## 预期决策

如果 v45 过 token 和 accuracy gate，再跑 LongMemEval-S full。若 v45 丢掉 v44 的 exact-date 修复或 full token estimate 仍超预算，则停止 session-thread prompt 方向，转向 build-side memory schema/aggregation 方法。
