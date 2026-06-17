# v116 LongMemEval-S 诊断

## 主要观察

LongMemEval-S 在 v116 下没有触发 selected context：

- selected context applied `0/500`
- answer cache hits `500/500`
- answer text changed vs v110 `0/500`
- inherited dual flash strict/lenient `0.812000 / 0.834000`

这说明 v116 的短 turn 邻域扩展没有影响 LongMemEval-S 长 turn 分支；同一配置可以同时用于 LME 和 LoCoMo。

## 约束检查

- build token: avg `85393.566`，按 logical cold-build visible tokens 统计。
- query token: avg `6140.218`，略高于 6K normal target，但低于 8K hard ceiling。
- thinking token: `0`。
- rerank token: `0`。
- build memory cache hits `3341`、misses `0`；cache 命中不改变 logical cold-build token 统计。

## 风险与下一步

v116 没有解决 LME query token 略高的问题，也没有提升 LME strict；它的价值主要是补齐 LoCoMo baseline target，同时保持 LME lenient `0.834000`。下一步若要冲 minimum target，需要更系统地利用 build memory 做 evidence planning、entity/time/conflict organization 或 answer consistency verification，而不是继续对 LME 长 turn 分支简单扩大上下文。
