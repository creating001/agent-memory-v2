# v287 state-only value slot guide full summary

## 结论

v287 升为当前本地 LTS。它在 v284 的 build-owned `scalar_value_manifest_v1` 之上，让 query compiler 消费 source-backed value slots，但只在 `current_state` intent 且只对 `state` 类型 slot 生效。最终 evidence 仍回到 raw Memory rows；value slot guide 只做状态组织、冲突提示和 source-backed activation，不作为独立证据。

该版本相对 v284 减少了“typed memory 只是 retrieval hint”的系统风险，同时没有观察到 accuracy 回退。LongMemEval-S full 只产生 2 条 answer diff，LoCoMo non-adversarial full 只产生 1 条 answer diff；changed-answer dual flash judge 中 v284 与 v287 的 changed answers 全部 strict correct。

## 方法

- 算法 commit：`0263a1917804f00e46e9e916949fb41bb5efd34a`
- 配置：`configs/stage1_state_only_value_slot_guide_v287_seeded_qwen36_no_think_build4k_cached.json`
- 主要改动：新增 `memory_value_slot_guide_memory_types=["state"]`，使 compiler 从 build-owned scalar/value manifest 中抽取 state-only value slot guide。
- Clean 边界：prediction 不使用 gold answer、judge output、benchmark label、sample id、test feedback 或样本级规则；dual judge 只用于离线评估。
- 方法来源：延续 evidence-first / source-backed memory view，并吸收 memory tiering、operation ledger、value object/slot、source-backed verify/audit 的有效机制；取舍是把 build 阶段组织出的状态对象作为 query 的轻量 guide，而不是让 typed memory 直接替代 raw evidence。

## v285-v287 迭代链

| 版本 | 改动 | 结论 |
|---|---|---|
| v285 | 对 `current_state/fact_lookup` 启用全类型 value slot guide | 过宽。LME guide applied `186/500`、LoCoMo `884/1540`，answer diff 分别 `55/500`、`422/1540`，主要扰动 fact lookup，不升 LTS。 |
| v286 | 只对 `current_state` intent 启用 value slot guide | 仍过宽。LME changed subset v284 strict/lenient `6/8`、`7/8`，v286 只有 `3/8`、`3/8`；plan/fact/event/profile/preference slot 仍会干扰 current-state focus，不升 LTS。 |
| v287 | `current_state` intent + `state` 类型 slot 双重限制 | LME answer diff `2/500`，LoCoMo `1/1540`；changed-answer dual judge 不回退，升 LTS。 |

## Full run metrics

| Benchmark | n | strict/lenient accuracy | avg build/query tokens | value guide applied | answer diffs vs v284 |
|---|---:|---:|---:|---:|---:|
| LongMemEval-S full | 500 | inherited `0.834000 / 0.846000` | `85393.566 / 6455.588` | `7/500` | `2/500` |
| LoCoMo non-adversarial full | 1540 | inherited `0.794156 / 0.819481` | `62015.57402597403 / 6093.962337662338` | `1/1540` | `1/1540` |

Accuracy is inherited from v284/v283 by full diff plus changed-answer judge, not by a fresh full dual judge. Unchanged predictions inherit existing full judge records; changed predictions were rejudged with explicit DeepSeek dual flash outputs.

## Diff audit vs v284

| Benchmark | route diff | retrieval diff | compiled evidence diff | compiled memory diff | build records diff | build management diff after removing scalar manifest |
|---|---:|---:|---:|---:|---:|---:|
| LongMemEval-S full | 0 | 0 | 0 | 0 | 0 | 0 |
| LoCoMo non-adversarial full | 0 | 0 | 0 | 0 | 0 | 0 |

Raw `build_memory_management` differs on every sample because v287 carries the scalar/value manifest schema. After removing that manifest, build management is identical to v284.

## Changed-answer judge

| Benchmark | v284 changed strict/lenient | v287 changed strict/lenient | Decision |
|---|---:|---:|---|
| LongMemEval-S changed answers | `2/2`, `2/2` | `2/2`, `2/2` | no regression |
| LoCoMo changed answers | `1/1`, `1/1` | `1/1`, `1/1` | no regression |

Judge files:

- `experiments/diagnostic/stage1_state_only_value_slot_guide_v287_changed_vs_v284/lme_v284_changed_dual_judge.json`
- `experiments/diagnostic/stage1_state_only_value_slot_guide_v287_changed_vs_v284/lme_v287_changed_dual_judge.json`
- `experiments/diagnostic/stage1_state_only_value_slot_guide_v287_changed_vs_v284/locomo_v284_changed_dual_judge.json`
- `experiments/diagnostic/stage1_state_only_value_slot_guide_v287_changed_vs_v284/locomo_v287_changed_dual_judge.json`

## Output paths

- LME full run record: `experiments/diagnostic/stage1_state_only_value_slot_guide_v287_lme_full/`
- LoCoMo full run record: `experiments/diagnostic/stage1_state_only_value_slot_guide_v287_locomo_full/`
- Full diff audit: `experiments/diagnostic/stage1_state_only_value_slot_guide_v287_diff_vs_v284.json`
- Predictions/traces:
  - `outputs/diagnostic/stage1_state_only_value_slot_guide_v287_lme_full/predictions.jsonl`
  - `outputs/diagnostic/stage1_state_only_value_slot_guide_v287_lme_full/traces.jsonl`
  - `outputs/diagnostic/stage1_state_only_value_slot_guide_v287_locomo_full/predictions.jsonl`
  - `outputs/diagnostic/stage1_state_only_value_slot_guide_v287_locomo_full/traces.jsonl`

## 下一步

1. 把 `operation_manifest_v1`、`state_conflict_manifest_v1`、`scalar_value_manifest_v1` 进一步合并成 build-owned memory object index，使 query 不再依赖多层兼容 guide。
2. 用 working / long-term / archival / quarantine tier 和 operation ledger 直接决定 activation、conflict resolution、context packing 和 answer audit。
3. 做小范围 `src/` cleanup：优先删除已被 build-owned manifest 覆盖、且没有复现实验依赖的 query-side 兼容分支。
