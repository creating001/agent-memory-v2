# Diagnosis for stage1_selective_row_guide_v17_lme_s_full_68b671b

## 结论

v17 在 LongMemEval-S full 上达到 361/500 = 0.722，是当前 LME 最好结果。它没有改变 build memory，也没有增加 answer token 上限；增益来自 query/compiler 侧更稳的 profile-safe context organization。

## 关键观察

- prediction gate 通过：500/500 predictions 和 traces 完整。
- commit clean：prediction 使用 `68b671b`，dirty=false。
- token gate 通过：avg_build_tokens 80346.246，avg_query_tokens 5022.590。
- answer max input/output 正确：131072 / 16384。
- build cache 全命中：hits 3341，misses 0；但 avg_build_tokens 按 logical cold-build cost 计入。
- structured guide 触发 492/500；8 条 personalized recommendation 关闭 guide。
- evidence recall 为 1.000，说明主要瓶颈不是 gold evidence 是否进入 trace，而是 answer 使用和 context organization。

## 错误与收益形态

- single-session-preference 从 v16 的 8/30 提升到 11/30，是本次核心收益。
- multi-session 从 71/133 提升到 75/133，说明关闭 recommendation guide 没有只带来局部单类收益。
- temporal-reasoning 从 97/133 降到 95/133，需要后续在 temporal/source organization 上补回来。
- v17 相比 v13 净 +4，说明 selective compiler 比单纯 temporal aid 更适合作为 LME 下一轮基线。

## 下一步

- 不继续堆 benchmark-specific route；优先做外部实现支持的 general hybrid retrieval / source expansion。
- 重点分析 v14/v17 在 LoCoMo 的差异，决定是否做 selective memory source map 或 dense+BM25 RRF。
- 对 LME temporal 回退做 badcase 分析，但规则必须仍然只基于 question text、timestamps、roles 和 retrieved memory metadata。
