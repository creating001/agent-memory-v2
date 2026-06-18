# V148 Scoped Version Chain Interleave 诊断

## 目的

V148 继续处理 goal 风险 #5，但不沿用 v147 的全局 temporal/current route priority。它继承 v127，只在 `current_state` / `profile_preference` 的 compiler row ordering 中使用 `scoped_memory_version_chain_interleave`。

机制边界：

- typed memory 只作为 source-backed organization signal；
- 只重排已经可见的 raw rows，不额外扩展候选；
- 只有 question 与 memory slot/value/text 有实质重叠时才触发；
- current 问题优先 active source，historical 问题优先 superseded source，change 问题可保留两者；
- `compiler.max_memory_records=0`，final reader evidence 仍是 raw Memory Context。

Clean boundary：prediction 不读取 gold answer、judge output、benchmark 标签、sample id、row index、test feedback 或样本级规则。

## Scope

- Config: `configs/stage1_scoped_version_chain_interleave_v148_qwen36_no_think_build4k_cached.json`
- Parent/LTS: `configs/stage1_superseded_source_chain_v127_qwen36_no_think_build4k_cached.json`
- Code/run base before v148 commit: `52729b6`
- Unit tests: `python -m unittest discover -s src/tests` -> `234` tests OK

Compile-only diff vs v127:

| Benchmark | prompt changed | row order changed | row set changed | changed routes | avg context delta |
|---|---:|---:|---:|---|---:|
| LME-S full | `14/500` | `14/500` | `5/500` | profile `7`, current `7` | `+1.410` chars/sample |
| LoCoMo non-adv full | `50/1540` | `50/1540` | `1/1540` | profile `46`, current `4` | `+0.018` chars/sample |

Full cached prediction:

| Benchmark | answer cache | actual answer changes |
|---|---|---:|
| LME-S full | hits `486`, misses/writes `14` | `10/500` |
| LoCoMo non-adv full | hits `1491`, misses/writes `49` | `18/1540` |

Cache seed used only v127 prediction-time traces/predictions; no labels or judge outputs.

## Changed-Answer Judge

Paired dual `deepseek-v4-flash` judge on actual changed-answer subsets:

| Benchmark | v127 strict/lenient | v148 strict/lenient | delta |
|---|---:|---:|---:|
| LME-S changed answers | `5/10` / `6/10` | `4/10` / `4/10` | strict `-1`, lenient `-2` |
| LoCoMo changed answers | `13/18` / `13/18` | `13/18` / `13/18` | strict `0`, lenient `0` |

## 决策

拒绝 v148，不升 LTS。

原因：scope 和 clean/general 风险边界比 v145/v147 更合理，但 LME changed-answer dual judge 负向。典型损失包括：

- `beb0a3bdb35a23a257132b5e`：most recent family trip 从正确 `Paris` 变成 `Hawaii`。
- `a3e4c89a8fdf800fa3b2676f`：三次旅行顺序变坏。
- `348efb7e44a8722f2b50358a`：LoCoMo 中 `Xenoblade Chronicles` 变成信息不足；LoCoMo 总体被其他收益抵消，但风险仍存在。

结论：仅靠 visible scoped row ordering 仍不够；即使不暴露 typed memory text，也可能把相似但非 answer-slot 的 raw rows提前，导致 answer 阶段用错 evidence。

## 下一步

V149 应避免继续扩大 memory row ordering。更合理的方向是 answer-slot-aware guard：

- 先判断问题要求的是 current value、previous value、both current+previous、duration start/end、event order 还是 preference/advice anchor；
- raw rows 必须同时匹配 entity/topic 与 answer slot，不能只因同一 state chain 或同类 profile memory 被提前；
- 对 `most recent/latest` 类问题保留时间排序，但要检查事件槽是否一致；
- 对 preference/advice 题，不要把缺少具体活动/地点的 profile anchor 误判成可以推荐具体 item；
- verifier/repair 只能检查 draft answer 是否被 raw rows 支持，不能用 typed memory 文本补答案。

## 证据路径

- Compile outputs: `outputs/diagnostic/stage1_scoped_version_chain_interleave_v148_lme_s_full_compile/`，`outputs/diagnostic/stage1_scoped_version_chain_interleave_v148_locomo_nonadv_full_compile/`
- Prediction outputs: `outputs/diagnostic/stage1_scoped_version_chain_interleave_v148_lme_s_full/`，`outputs/diagnostic/stage1_scoped_version_chain_interleave_v148_locomo_nonadv_full/`
- Scope diff: `experiments/diagnostic/stage1_scoped_version_chain_interleave_v148_scope_diff.json`
- Changed-answer inputs: `outputs/diagnostic/stage1_scoped_version_chain_interleave_v148_lme_changed_answers/`，`outputs/diagnostic/stage1_scoped_version_chain_interleave_v148_locomo_changed_answers/`
- Paired judge: `experiments/diagnostic/stage1_scoped_version_chain_interleave_v148_lme_changed_answers/`，`experiments/diagnostic/stage1_scoped_version_chain_interleave_v148_locomo_changed_answers/`
