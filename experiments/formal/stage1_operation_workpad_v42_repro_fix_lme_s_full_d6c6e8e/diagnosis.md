# 诊断

## 修复点

本次修复前，当前代码运行 v42 配置得到 374/500 = 0.748，明显低于原 v42 的 387/500 = 0.774。定位到两个复现漂移来源：

- `CachedAnswerer` 在 cache hit 时重新解析历史 `raw_response`，导致旧缓存答案受当前解析逻辑影响。
- `external_naive` prompt 在关闭可选模块时仍拼入空 block，并且在未开启 aggregation contract 时也加入 `calculation` schema，导致 prompt hash 与原 v42 不一致。

修复后：

- cache hit 直接返回缓存中保存的 `answer`，不再二次解析 `raw_response`。
- 禁用的 optional prompt block 不进入 prompt。
- `calculation` 字段只在 aggregation report contract 启用时出现。
- 新增单测覆盖缓存命中保持 answer、禁用模块不造成 prompt 漂移。

## 复现结果

- prediction_changed_count vs 原 v42：0/500。
- answer finalizer applied：1/500，与原 v42 一致。
- avg compiled evidence items：34.062。
- avg context chars：19665.154。
- evidence recall：1.0。

## Judge 结果解释

本次 DeepSeek judge 重跑 accuracy 是 0.772，原 v42 是 0.774。`reproduction_vs_v42.json` 显示 prediction 完全相同，但 judge label 有 27 条翻转：

- CORRECT -> CORRECT：373
- WRONG -> CORRECT：13
- WRONG -> WRONG：100
- CORRECT -> WRONG：14

因此 0.772 与 0.774 的差异是 judge 重跑波动，不是方法或 prediction 变化。后续正式比较应优先看同一次 judge 或在 prediction 相同时直接标注 judge variance。

## 对后续探索的影响

当前 v42 已恢复为可靠基线。由于 LongMemEval-S evidence recall 已是 1.0，且 avg query tokens 约 5.86K，下一步提升不应依赖继续扩大上下文；更应围绕：

- 降低上下文噪声和无关候选干扰。
- 让 build 阶段产出的 typed memory 更适合 query 侧选择。
- 改进候选组织和 sufficiency 判断，而不是添加样本级规则。
- 所有新方法都必须单独配置、可消融，并记录 build/query token 成本。
