# v44 规划：Temporal-Only Session Guide

## 背景

v43 session-thread memory guide 的 20 条 gate 失败：

- avg_query_tokens：`6023.95`
- max_query_tokens：`8003`
- DeepSeek judge：`15/20`
- v42 same20：`15/20`
- gained/lost：`1/1`

但 v43 有一个明确正向信号：animal shelter fundraising dinner 从 v42 `February 2023` 改成 `2023-02-14`。这个 case 的关键在于同一 session 内更具体的 later turn 和 row-linked build memory hint。因此，v44 只保留 temporal 侧的有效信号，删除 list_count 侧的额外开销。

## 外部方法参考

- xMemory：参考 episodic/raw-message 回链；v44 只对 temporal_lookup 把 raw rows 按 session thread 组织。
- SimpleMem：参考 typed memory 作为 structured context guide；v44 限制为 row-linked build memory，不让 summary 替代 raw evidence。
- Mnemis：参考 selected memory node 回链 episode；v44 只展示已进入 context 的 raw row 对应 memory hint。
- Graphiti/Zep：参考 temporal/provenance 视角；v44 不引入图数据库，只使用现有 source/provenance。

## 方法设计

底座：v42 `stage1_operation_workpad_v42_cached`。

配置：`configs/stage1_temporal_session_guide_v44_cached.json`

与 v42 相同：

- build memory prompt/cache
- retrieval top-k
- evidence_report contract
- operation_workpad
- answer max input/output `131072/16384`

只对 `temporal_lookup` 开启：

- `context_layout=session_thread`
- `structured_guide_include_memory=true`
- `memory_record_source=evidence_rows`
- `memory_order=question_overlap`
- `max_memory_records=3`

非 temporal route 保持 v42 prompt 等价。answer cache 复用 v42 namespace；完全相同 prompt 会 cache hit，变化后的 temporal prompt 会 miss。cache 命中仍从 stored usage 计入 logical query tokens，不影响成本口径。

## Clean 边界

- 只读取 question text、visible question_time、raw dialogue、retrieval result 和 build-stage memory。
- 不使用 gold/reference answer、judge output、benchmark hidden labels、sample id、qid、row index、test feedback 或样本级规则。
- `temporal_lookup` 来自 question-derived route，不是 LongMemEval question_type 或 LoCoMo category。
- DeepSeek judge 仅用于 prediction 完成后的离线评测。

## Gate 计划

先跑 LongMemEval-S route-stratified 20 条 diagnostic：

- input：`outputs/diagnostic/v35_lme_route_stratified_probe/prediction_input.jsonl`
- config：`configs/stage1_temporal_session_guide_v44_cached.json`
- workers：`4`

通过条件：

- 20/20 prediction 成功。
- answer max input/output = `131072/16384`。
- avg query tokens <= `6000`，max query tokens < `8000`。
- avg build tokens 按 logical cold-build usage 记录。
- `session_thread` 和 `activated_build_memory` 只在 `temporal_lookup` prompts 出现。
- 同子集 DeepSeek judge 相对 v42 有净收益，或至少 temporal_lookup 有明确收益且无非目标 route regression。

## 预期决策

如果 v44 仍然 token 超预算或与 v42 持平，不跑 full，结束这条 session-thread prompt 方向。若 v44 过 token gate 且相对 v42 净正向，再考虑 LME full；LoCoMo 仍需要基于 v35/v34 底座单独设计。

## Gate 结果

Run：`v44_temporal_session_guide_lme_probe_b39687d`

- commit：`b39687d3d8328fe621844805f1d935b29c451361`
- dirty：True，主要是用户修改的 `docs/architecture.md` 和 `docs/clean_protocol.md` 未提交。
- prediction：20/20 成功。
- answer max input/output：`131072/16384`。
- avg_build_tokens：`81690.45`。
- avg_query_tokens：`5783.75`。
- max_query_tokens：`7631`。
- build cache hits/misses/writes：`137/0/0`。
- answer cache hits/misses/writes：`16/4/4`。
- session_thread 生效范围：`temporal_lookup 4/4`，其他 route `0/16`。
- activated_build_memory 生效范围：`temporal_lookup 4/4`，其他 route `0/16`。
- prompt clean scan：无 hidden metadata 命中；`category` 仅来自原始对话普通词。
- DeepSeek judge：`16/20 = 0.80`。
- v42 same20：`15/20 = 0.75`。
- gained/lost vs v42：`1/0`，net `+1`。

关键 gained case：

- `d823172b5baf1eff81acb20c`，animal shelter fundraising dinner，从 v42 `February 2023` 改成 `2023-02-14`。

Full token estimate：

- v42 full avg query：`5865.644`
- v44-v42 temporal delta on gate：`+617.5`
- temporal_lookup full share：`161/500`
- estimated v44 full avg query：`6064.479`

结论：v44 的 20 条 gate 在质量和本地平均 token 上通过，但基于 full route mix 的 avg query 估计超过 `6000`。不直接跑 full。下一步把 `max_memory_records` 从 `3` 降到 `1` 做 v45 token-safe gate；如果 v45 保留正向信号且 full token estimate <= `6000`，再考虑 LongMemEval-S full。
