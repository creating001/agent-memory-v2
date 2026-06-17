# v116 LoCoMo 诊断

## 主要观察

v116 的改动是通用对话邻域扩展，不是 LoCoMo 样本级规则：当 question 触发 `fact_lookup`、`list_count` 或 `profile_preference` 且存在代词/指代信号时，把检索命中 turn 的前后邻近 turn 放入 selected context。相较 v110，本轮只把后向窗口从 1 扩到 2，并提高邻近 turn 截断预算。

正式结果显示该方向对 LoCoMo 有净收益：

- strict `1200/1540 = 0.779221`，与 v110 持平。
- lenient `1243/1540 = 0.807143`，比 v110 多 12 题。
- answer text changed `575/1540`；changed-answer lenient gain/loss 为 `46/36`，净 `+10`。
- selected context applied `1198/1540`，avg query tokens `5956.221`，仍在 LoCoMo 6K normal target 内。
- answer finalizer `0` 次触发，本轮收益不来自 mechanical finalizer。

## 按类别

| Category | 名称 | strict | lenient | lenient vs v110 |
|---:|---|---:|---:|---:|
| 1 | Multi-Hop | `174/282 = 0.617021` | `197/282 = 0.698582` | `+5` |
| 2 | Temporal Reasoning | `242/321 = 0.753894` | `248/321 = 0.772586` | `+0` |
| 3 | Open-Domain | `50/96 = 0.520833` | `51/96 = 0.531250` | `-3` |
| 4 | Single-Hop | `734/841 = 0.872771` | `747/841 = 0.888228` | `+10` |

## 约束检查

- build token: avg `62015.574`，按 logical cold-build visible tokens 统计；cache hit 只避免重复本地 API 调用，不把 build 成本记为 0。
- query token: avg `5956.221`，未超过 LoCoMo normal target `6000`。
- thinking token: `0`，因为 qwen3.6 no-thinking 请求级关闭 thinking，且服务端未返回 explicit reasoning tokens。
- rerank token: `0`，本轮未使用 rerank。
- repair/scoped evidence: 未启用。

## 风险与下一步

v116 达到 LoCoMo baseline target，但仍未到 minimum target `0.830000`。继续扩大 selected context 窗口可能带来噪声，当前不应沿这个方向盲目加大窗口。下一步应从更强的 memory organization/query-time reasoning 入手，例如用 build memory 组织候选实体、时间线和冲突状态，再把它作为 evidence planning 或 consistency guardrail，而不是直接把更多 typed memory 文本塞进 reader prompt。
