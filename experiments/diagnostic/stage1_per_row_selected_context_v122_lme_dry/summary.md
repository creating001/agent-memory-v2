# stage1_per_row_selected_context_v122_lme_dry

## 目的

诊断 v116/v121 中长 turn profile 关闭 `selected_context` 是否只是数据集 heuristic。v122 继承 v121 的 build、retrieval、compiler、answer guard 和 backbone，只移除 long-turn profile 的 `selected_context.enabled=false` 覆盖，让全局 per-row selected context 条件在 LongMemEval 上也生效。

该诊断只做 dry-run 编译统计，不调用 answer LLM，不使用 gold answer、judge 输出、benchmark 标签、sample id、row index 或测试反馈。

## 配置

- config: `configs/stage1_per_row_selected_context_v122_qwen36_no_think_build4k_cached.json`
- benchmark/subset: LongMemEval-S full dry-run, 500 samples
- changed module: retrieval selected-context policy only
- inherited from: v121 source-grounded guard, v116 retrieval/compiler/build cache

## Dry-Run 结果

- selected_context applied: `317/500`
- selected_context materialized rows: `1902`
- skipped long center rows: `3668`
- changed_context rows: `317/500`
- avg context char delta vs v116 trace: `+528.594`
- max context char delta: `+5494`
- min context char delta: `-2744`
- avg evidence row delta vs v116 trace: `-2.738`
- changed evidence row count: `308/500`

按 route：

| route | n | selected_context applied |
| --- | ---: | ---: |
| current_state | 22 | 0 |
| fact_lookup | 183 | 183 |
| list_count | 119 | 119 |
| profile_preference | 15 | 15 |
| temporal_lookup | 161 | 0 |

## 诊断结论

不推进 v122 full answer。虽然 per-row selected context 比全样本长/短 turn profile 更 general，但在 LME 上会改变 `317/500` 个 prompt，并因为固定 evidence budget 导致平均 evidence rows 下降。这属于高成本、高噪声风险改动，和历史 v95/v98 selected-context 在 LME 上的负向经验一致。

后续如果要解决长/短 turn profile 风险，应优先把 profile 从 benchmark 形态改成更通用的 token-budget / evidence-density policy，而不是直接把 short-turn selected context 全量搬到 long-turn 场景。
