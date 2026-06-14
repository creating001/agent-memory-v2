# 诊断

## 背景

v42 复现控制的离线统计显示，LongMemEval-S full 的 query token 与准确率不是单调关系：

- 5200-5799 token 桶 accuracy 约 0.828。
- 5800-5999 token 桶 accuracy 约 0.825。
- 6000-6499 token 桶 accuracy 约 0.670。
- 6500+ token 桶 accuracy 约 0.745。

按 route 看，`list_count` 和 `current_state` 在高 token 区间更容易错；`temporal_lookup` 不是单调关系，仍需要保留端点链。因此 v70 只压缩 `list_count/current_state` 的 row text，避免触碰 temporal route。

## 实验控制

初次 v70 full 使用全新 answer cache，导致未改 prompt 的 fact/temporal/profile 也被重新生成，混入本地 LLM 再生成波动。该结果未提交，已删除。

正式 v70 使用如下控制：

- 从 v42 clean prediction traces seed v70 新 answer cache namespace。
- seed 只包含 prompt、answer、raw_response、token usage，不读取 gold、judge、question_type、sample id、row index 或 test feedback。
- v70 rerun 中 answer cache hits 为 359，misses 为 141；misses 对应 prompt 真正受 `current_state/list_count` route override 影响的样本。
- 因此 changed prediction 从未控制时的 88 条降到 26 条，更适合作为 prompt 消融。

## 改动

在 v42 基础上仅增加：

```json
"route_overrides": {
  "current_state": {
    "row_text_mode": "role_query_snippet",
    "max_row_text_chars": 520
  },
  "list_count": {
    "row_text_mode": "role_query_snippet",
    "max_row_text_chars": 640
  }
}
```

其他保持不变：

- build-stage typed memory 不变。
- dense + BM25 retrieval top40 不变。
- temporal workpad / evidence_report 不变。
- answer model 仍为 Qwen/Qwen3-30B-A3B-Instruct-2507，max input/output 仍为 131072 / 16384。

## 结果

Full judge：

- v70：379/500 = 0.758。
- v42 修复控制：386/500 = 0.772。
- evidence_recall：1.0。
- avg query tokens：5859.174，几乎没有低于 v42 的 5864.706。

Changed prediction 对比：

- prediction_changed_count：26/500。
- CORRECT->WRONG：13。
- WRONG->CORRECT：3。
- CORRECT->CORRECT：2。
- WRONG->WRONG：8。

按 information need：

- `list_count`：CORRECT->WRONG 10，WRONG->CORRECT 2。
- `current_state`：CORRECT->WRONG 3，WRONG->CORRECT 1。

未改 prediction 的 judge variance：

- CORRECT->WRONG 3。
- WRONG->CORRECT 6。

## 判断

v70 直接否定了“把高噪声 route 的长行变成 query snippet”这个简单方案。它没有显著降低 query tokens，却明显破坏了 list/count 的候选覆盖。原因很可能是：

- list/count 需要完整枚举 in-scope、out-of-scope、重复项和上下文边界。
- query-focused snippet 会保留与问题词最接近的片段，但被计数的候选有时不共享显式问题词。
- current_state 需要旧事实、新事实和更新语境，snippet 容易丢掉冲突关系。
- evidence_recall=1.0 只能说明正确 session/turn 进入了 context，不能说明 answer 所需的细节完整。

## 后续取舍

不继续调 `max_row_text_chars` 或对 list/count 做更激进 snippet。下一步应保留 raw rows 的可读完整性，同时在 raw rows 之上增加结构化 candidate organization：

- list/count：先构造候选集合、重复/排除理由和计数边界，再让 answer 基于完整 raw rows 定案。
- current_state：构造 update/conflict chain，明确 newer/older 和 active/superseded 候选。
- temporal：保留 endpoint chain，不走 snippet 压缩。

这比继续压 query tokens 更符合当前错误形态，也更接近外部方法里“typed/semantic memory 做索引，raw episode 做最终证据”的通用方向。
