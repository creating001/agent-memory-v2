# v39 gate diagnosis

## 诊断结论

v39 gate 的工程条件成立：answer max `131072/16384` 正确，logical build token 统计存在，cache hit 未把 build cost 记成 0，trace/prediction 均为 20 行，route-scoped override 生效。

这次 gate 不判断方法性能，因为没有离线 judge accuracy。它只回答一个问题：是否值得花时间跑 LongMemEval-S full。答案是可以，但必须把 full 结果和 v36/v38 做净 correct 对比。

## 方法取舍

保留：

- v36 的 answer guard、structured guide、temporal workpad 和 evidence report contract。
- raw evidence 作为最终 answer context。
- build-stage typed memory 的 source/provenance，用于 source-linked selector。

避免：

- v37 的 typed memory prompt 化。
- v38 的 final top60 prompt 暴露。
- 基于 benchmark label、sample id、question_type 或 badcase 实体的规则。

## 关键指标

| 指标 | 值 |
|---|---:|
| n_samples | 20 |
| avg_build_tokens | 81690.45 |
| total_build_tokens | 1633809 |
| avg_query_tokens | 5607.8 |
| total_query_tokens | 112156 |
| weighted_full_avg_query_estimate | 5566.583 |
| avg_compiled_evidence_items | 34.65 |
| avg_context_chars | 18938.4 |
| avg_build_memory_records | 130.95 |
| avg_active_build_memory_records | 117.5 |
| avg_compiled_memory_records | 0.0 |
| build_cache_hits / misses / writes | 137 / 0 / 0 |
| embedding_cache_hits / misses / writes | 10079 / 0 / 0 |
| answer_cache_hits / misses / writes | 8 / 12 / 12 |

## Route 观察

- `current_state`、`fact_lookup`、`profile_preference` 没有进入 memory-aware order，保持 v36 风格 top40。
- `list_count`、`temporal_lookup` 使用 top60 retrieval candidate 和 top40 compiler cap，平均 rows 分别为 `36.0` 和 `35.5`，没有重现第一次 gate 的 row coverage 过低问题。
- `temporal_lookup` 单 route query token 略高，需要在 full 中观察整体平均和 p90/p95；如果 full 平均超过 6K，则只能标成 expensive/diagnostic，不能作为主线。

## 下一步

1. 提交本 gate 记录，保持 full run 的 git 状态可追溯。
2. 跑 LongMemEval-S full，不先跑 LoCoMo。
3. full 后做 DeepSeek judge，并比较 v39 vs v36/v38 的 correct set、wrong by information_need、avg build/query token。
4. 只有当 LME full 相比 v36 不明显负向，才安排 LoCoMo non-adversarial full。
