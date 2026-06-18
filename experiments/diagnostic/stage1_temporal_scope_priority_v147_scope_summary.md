# V147 Temporal Scope Priority 诊断

## 目的

V147 继承当前 LTS v127，仅打开 `route.temporal_priority_over_recent=true`。目标是检查当问题同时包含 `current/latest/recent` 和明显 temporal/duration/order 信号时，优先 temporal route 能否减少 #5/#3 中的 as-of state 路由歧义。

这个版本仍保持 clean：prediction 只读 question text、raw Memory Context、由 dialogue 构建的 typed memory、source backpointers 和 prediction-time route；不读 gold answer、judge output、benchmark 标签、sample id、row index、test feedback 或样本级规则。Typed memory 只作为 source-backed activation/organization signal，最终 reader evidence 仍是 raw-source-first。

## Scope

- Config: `configs/stage1_temporal_scope_priority_v147_qwen36_no_think_build4k_cached.json`
- Parent/LTS: `configs/stage1_superseded_source_chain_v127_qwen36_no_think_build4k_cached.json`
- Code/run commit before v147 docs commit: `108b5fa`
- LME compile-only: route changed `9/500`，prompt changed `9/500`，row-set changed `2/500`
- LoCoMo compile-only: route changed `1/1540`，prompt changed `1/1540`，row-set changed `1/1540`
- Full cached prediction: LME answer changed `6/500`；LoCoMo answer changed `0/1540`

## Changed-Answer Judge

只对 LME 6 条实际 changed-answer 样本跑 paired dual `deepseek-v4-flash` judge；LoCoMo 无 answer change，因此不跑 judge。

| 对照 | strict | lenient |
|---|---:|---:|
| v127 changed-answer subset | `5/6 = 0.833333` | `5/6 = 0.833333` |
| v147 changed-answer subset | `3/6 = 0.500000` | `3/6 = 0.500000` |
| delta | `-2/6` | `-2/6` |

关键损失：

- `2a18e972b47c27c2c1f2fdb8`：v127 正确 `4 years and 9 months`，v147 输出 malformed `this answer`。
- `a3e4c89a8fdf800fa3b2676f`：v127 正确三次旅行顺序，v147 把第三项换成 `John Muir Wilderness (May 15, 2023)`，偏离 gold。
- `a1e403c5b6ee9c67eceee109`：v127/v147 都错；v147 给出错误 duration `3 years and 9 months`。

## 决策

拒绝 v147，不升 LTS。

原因：把 temporal 信号全局置于 recent/current 之前，虽然更像一个 general route rule，但会把某些“current state 的起点/持续时间”问题过度改成 temporal_lookup，从而丢失或弱化当前状态证据。#5 风险没有实质降低，accuracy 还在 changed-answer 子集上下降。

## 下一步

不要继续做全局 temporal priority。下一版应改成更细的 source-backed state interpretation：

- 区分 `current state duration`、`historical before current state`、`pure event order/list`、`unsupported wrong-current-location/entity`。
- Typed memory 只做 source-backed activation，用 active/superseded/conflict chain 帮助选择 raw rows。
- Compiler 需要 answer-slot-aware source selection：先确定问题要的是状态值、起点、终点、历史链还是枚举顺序，再组织 raw evidence。
- 对冲突链做 pruning，避免同 slot 扩展把非答案状态、错误地点或同名事件带入 prompt。

## 证据路径

- Prediction outputs: `outputs/diagnostic/stage1_temporal_scope_priority_v147_lme_s_full/`，`outputs/diagnostic/stage1_temporal_scope_priority_v147_locomo_nonadv_full/`
- Compile outputs: `outputs/diagnostic/stage1_temporal_scope_priority_v147_lme_s_full_compile/`，`outputs/diagnostic/stage1_temporal_scope_priority_v147_locomo_nonadv_full_compile/`
- Changed-answer inputs: `outputs/diagnostic/stage1_temporal_scope_priority_v147_lme_changed_answers/`
- Paired judge: `experiments/diagnostic/stage1_temporal_scope_priority_v147_lme_changed_answers/`
- Comparison JSON: `experiments/diagnostic/stage1_temporal_scope_priority_v147_lme_changed_answers/paired_judge_comparison_vs_v127.json`
