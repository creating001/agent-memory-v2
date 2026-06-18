# V149 Answer Slot Checklist 诊断

## 目的

V149 继续处理 goal 风险 #5，但不再扩大 memory row ordering。它继承 v127，只在 `current_state` / `profile_preference` routes 打开现有 `final_answer_checklist`，要求 answer model 私下确认最终答案槽位必须被 raw Memory Context 支撑。

机制边界：

- 不改 build memory、retrieval、row ordering、selected context、answer model 和 finalizer；
- 不把 typed memory text 作为 reader evidence，`compiler.max_memory_records=0`；
- checklist 只做通用 raw-source support guard，不读取 gold、judge、benchmark 标签、sample id、row index、test feedback 或样本级规则；
- 借鉴方向是 Graphiti/Zep 式 temporal provenance 和 source-aware verifier 思路，但本版只做轻量 prompt-side guard。

## Scope

- Config: `configs/stage1_answer_slot_checklist_v149_qwen36_no_think_build4k_cached.json`
- Parent/LTS: `configs/stage1_superseded_source_chain_v127_qwen36_no_think_build4k_cached.json`
- Code/run base before v149 commit: `3ca8cf5`

Compile-only diff vs v127:

| Benchmark | prompt changed | row order changed | row set changed | route changed | avg context delta |
|---|---:|---:|---:|---:|---:|
| LME-S full | `37/500` | `0/500` | `0/500` | `0/500` | `+92.020` chars/sample |
| LoCoMo non-adv full | `50/1540` | `0/1540` | `0/1540` | `0/1540` | `+38.252` chars/sample |

Full cached prediction:

| Benchmark | answer cache | actual answer changes |
|---|---|---:|
| LME-S full | hits `463`, misses/writes `37` | `21/500` |
| LoCoMo non-adv full | hits `1491`, misses/writes `49` | `22/1540` |

Cache seed used only v127 prediction-time traces/predictions; no labels, judge outputs, benchmark categories, sample ids, or test feedback.

## Changed-Answer Judge

Paired dual `deepseek-v4-flash` judge on actual changed-answer subsets:

| Benchmark | v127 strict/lenient | v149 strict/lenient | delta |
|---|---:|---:|---:|
| LME-S changed answers | `13/21` / `13/21` | `9/21` / `10/21` | strict `-4`, lenient `-3` |
| LoCoMo changed answers | `11/22` / `15/22` | `13/22` / `13/22` | strict `+2`, lenient `-2` |

## 决策

拒绝 v149，不升 LTS。

原因：v149 确实降低了一些 wrong-slot / under-specified answer 风险，但 LME 明显负向，且 LoCoMo lenient 也负向。典型损失不是 retrieval 变坏，而是 prompt-side checklist 让模型过度保守或缩短答案：

- `2a18e972b47c27c2c1f2fdb8`：需要用 raw rows 做简单 duration 差值，v149 因“未直接给出”拒答。
- `5110d0ed1a7cb0fefd131e4d`：推荐题从基于兴趣的活动类型建议变成要求具体周末事件，过度拒答。
- `076e0ce5f5d89aac0a37b3e3`：偏好推断题从 Dodge Charger 变成信息不足。
- `9d706fdbac17028f653f49c5`：把具体 hiking trails 缩成 generic walks，丢掉关键答案槽位。

正向样例也有价值：

- `a1e403c5b6ee9c67eceee109`：current-role duration 从拒答修到 `1 year and 5 months`。
- `6658015006384a53816e150c`：LoCoMo favorite food 从拒答修到 `Ginger snaps`。
- `b57d80e054140e2fed87606b` / `e9ab2e88d287f2949bce371b`：favorite books 从单项补成 `Sapiens, Avalanche`。

## 下一步

不要继续加 broad checklist。V150 更合理的方向：

- 把 answer-slot guard 从 broad prompt discipline 改成 typed trigger：只在 draft answer 与 evidence report 出现 `unknown/refusal`、过短 collection answer、或 current/profile value 槽位冲突时触发；
- 区分 question intent：recommendation/advice 允许基于 raw preference anchors 给类型/标准建议，不要求具体外部活动名称；duration/current-state 允许从 raw rows 做明确的简单计算；
- verifier 只允许 `keep` 或 `revise to supported raw answer`，不能因没有“直接写成最终答案”就拒绝可计算、可推断的 clean answer；
- trace 中应显式记录 route override 后的 effective compiler settings，避免 top-level `final_answer_checklist=false` 掩盖实际 route override。

## 证据路径

- Compile outputs: `outputs/diagnostic/stage1_answer_slot_checklist_v149_lme_s_full_compile/`，`outputs/diagnostic/stage1_answer_slot_checklist_v149_locomo_nonadv_full_compile/`
- Prediction outputs: `outputs/diagnostic/stage1_answer_slot_checklist_v149_lme_s_full/`，`outputs/diagnostic/stage1_answer_slot_checklist_v149_locomo_nonadv_full/`
- Scope diff: `experiments/diagnostic/stage1_answer_slot_checklist_v149_scope_diff.json`
- Changed-answer inputs: `outputs/diagnostic/stage1_answer_slot_checklist_v149_lme_changed_answers/`，`outputs/diagnostic/stage1_answer_slot_checklist_v149_locomo_changed_answers/`
- Paired judge: `experiments/diagnostic/stage1_answer_slot_checklist_v149_lme_changed_answers/`，`experiments/diagnostic/stage1_answer_slot_checklist_v149_locomo_changed_answers/`
