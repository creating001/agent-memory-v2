# v289 memory workspace reboot full summary

## 结论

v289 不升 LTS，记录为 rejected diagnostic。

v289 的 build 方向是对的：在 v288 `memory_object_index_v1` 之上新增 `memory_workspace_manifest_v1`，把 source-backed activation group、memory tier、lifecycle state、conflict state、operation hints 和 context-pack policy 收敛成统一的 build-owned memory workspace。该 manifest 在 LME 和 LoCoMo full 上均 applied `100%`。

问题出在 query 使用方式：v289 直接关闭 v288 的 `memory_state_guide` / `memory_value_slot_guide`，改用 compact `Memory Workspace Plan`。LME accuracy 明显回退，LoCoMo query tokens 上升且 accuracy 也回退。因此新 workspace manifest 保留为下一版 build artifact，但 compact workspace plan 不能直接替代 v288 已验证 query path。

## 方法

- 算法 commit：`c1b879a3846d2fe37082c047016b9d5de2e508a5`
- 配置：`configs/stage1_memory_workspace_v289_reboot_seeded_qwen36_no_think_build4k_cached.json`
- 主要改动：
  - build 阶段新增 `memory_workspace_manifest_v1`。
  - workspace group 统一表达 working / long-term / archival / quarantine tier。
  - workspace group 统一表达 create / update / merge / supersede / retrieve / expand / verify / audit / context_pack 操作。
  - query compiler 新增 `Memory Workspace Plan`，只渲染 source ids 已出现在 Memory Context 的 source-backed group。
  - query plan 默认跳过 `quarantine_memory`。
  - v289 配置关闭 v288 的 state/value guide pair，改由 workspace plan 负责 compact activation。
- Clean 边界：prediction 不使用 gold answer、judge output、benchmark label、sample id、test feedback 或样本级规则；workspace plan 不是独立证据，最终答案仍以 raw Memory rows 为准。

## Full Metrics

| Benchmark | n | strict/lenient accuracy | avg build/query tokens | workspace manifest | workspace plan | answer diff vs v288 |
|---|---:|---:|---:|---:|---:|---:|
| LongMemEval-S full | 500 | `0.804000 / 0.834000` | `85393.566 / 6310.966` | `500/500` | `202/500` | `129/500` |
| LoCoMo non-adversarial full | 1540 | `0.785714 / 0.813636` | `62015.57402597403 / 6294.091558441559` | `1540/1540` | `930/1540` | `632/1540` |

DeepSeek dual judge: `deepseek-v4-flash` independent two-pass, temperature `0`, default thinking, strict = both correct, lenient = either correct.

## Diagnosis

- LME v289 strict/lenient `0.804 / 0.834` 回退明显，不能升 LTS。
- LoCoMo v289 strict/lenient `0.785714 / 0.813636` 回退，且 avg query tokens 从 v288 的约 `6093.962` 增至 `6294.092`。
- LME answer diff `129/500`，其中 `62` 个 diff 触发 workspace plan；strict badcase `98` 个，其中 `38` 个触发 workspace plan。
- LME diff 样本中新答案包含 “not enough” 的有 `51/129`，旧答案为 `45/129`；strict badcase中新答案 “not enough” 为 `40/98`。这说明 v289 的 source discipline 和 compact plan 让答案更保守，但没有带来 accuracy 收益。
- LoCoMo workspace plan 触发 `930/1540`，覆盖面过宽，query token 反而上升。

## 决策

v289 不升 LTS。下一版应拆开处理：

1. 保留 `memory_workspace_manifest_v1` 作为 build-side Agent Memory system artifact。
2. 恢复 v288 query behavior，先验证 answer/prompt/evidence diff 是否回到 `0`，争取得到“系统风险下降、性能不退”的新 LTS。
3. 后续 query 使用 workspace plan 时必须 guarded/additive：只在小范围 source-backed conflict/current-state 场景辅助 context organization，不能直接替换已验证 guide。

## Output Paths

- LME full run: `outputs/diagnostic/stage1_memory_workspace_v289_reboot_lme_full/`
- LoCoMo full run: `outputs/diagnostic/stage1_memory_workspace_v289_reboot_locomo_full/`
- LME experiment record: `experiments/diagnostic/stage1_memory_workspace_v289_reboot_lme_full/`
- LoCoMo experiment record: `experiments/diagnostic/stage1_memory_workspace_v289_reboot_locomo_full/`
- LME judge: `experiments/diagnostic/stage1_memory_workspace_v289_reboot_lme_full/deepseek_dual_judge.json`
- LoCoMo judge: `experiments/diagnostic/stage1_memory_workspace_v289_reboot_locomo_full/deepseek_dual_judge.json`
