# v210 role-aware tail snippet rejection

## 结论

v210 不升 LTS，不跑 LoCoMo full。它在 LongMemEval-S full 上把平均 query tokens 从 v209 的 `6580.196` 降到 `6122.956`，但 changed-answer paired dual judge 明显负向：strict `55/96 -> 41/96`，lenient `62/96 -> 53/96`。

这说明即使 retrieval hits、compiled evidence rows 和 source 顺序完全不变，低 rank 长行的 role-aware snippet 仍会破坏 reader 对答案槽位的判断。当前 LTS 保持 v209。

## 方法

- 父配置：`configs/stage1_conservative_context_budget_v209_seeded_qwen36_no_think_build4k_cached.json`
- v210 配置：`configs/stage1_role_aware_tail_snippet_v210_seeded_qwen36_no_think_build4k_cached.json`
- 只改 prompt rendering：rank `>32` 的 tail row 使用 `role_query_snippet`，`tail_max_row_text_chars=700`。
- assistant tail row 压缩为 query-focused snippet；user row 默认保留全文，只在超过 `2 * tail_max_row_text_chars` 时走既有 role-aware 截断。
- retrieval、evidence row selection、source ordering、build memory、answer model、repair/finalizer 和 cache namespace 不变。

## LME full 结果

| 项目 | v209 | v210 | 变化 |
|---|---:|---:|---:|
| avg build tokens | `85393.566` | `85393.566` | `0` |
| avg query tokens | `6580.196` | `6122.956` | `-457.240` |
| avg prompt chars | `19775.056` | `18358.496` | `-1416.560` |
| route diff | - | `0/500` | unchanged |
| retrieval hits diff | - | `0/500` | unchanged |
| evidence rows text/source diff | - | `0/500` | unchanged |
| effective selected-context diff | - | `0/500` | unchanged |
| prompt diff | - | `320/500` | changed |
| answer diff | - | `96/500` | changed |
| answer cache | - | `180/320/320` | hit/miss/write |

Prediction manifest was clean at method commit `2fbdeee21b2a5b7f713a0677691414fbe4577d10`.

## Changed-answer judge

Scope: only the `96` answers changed between v209 and v210. Both sides were judged with dual `deepseek-v4-flash`, temperature `0`, default thinking.

| Metric | v209 changed subset | v210 changed subset | Delta |
|---|---:|---:|---:|
| strict correct | `55/96` | `41/96` | `-14` |
| lenient correct | `62/96` | `53/96` | `-9` |
| judge agreement | `0.927083` | `0.875000` | `-0.052083` |

Strict transitions:

| Transition | Count |
|---|---:|
| CORRECT -> CORRECT | `31` |
| CORRECT -> WRONG | `24` |
| WRONG -> CORRECT | `10` |
| WRONG -> WRONG | `31` |

Lenient transitions:

| Transition | Count |
|---|---:|
| CORRECT -> CORRECT | `43` |
| CORRECT -> WRONG | `19` |
| WRONG -> CORRECT | `10` |
| WRONG -> WRONG | `24` |

Judge usage on the changed subset:

| Side | Prompt tokens | Completion tokens | Total tokens |
|---|---:|---:|---:|
| v209 | `36062` | `25057` | `61119` |
| v210 | `34030` | `25988` | `60018` |

## 风险判断

- #2 top-k/context noise/token risk: query tokens 有实质下降，但没有通过 accuracy gate。
- #3 selected-context/long-short heuristic risk: row set 和 selected-context effect 未变，说明问题来自 tail text compression 对 reader 的信息损失，而不是检索集合。
- #5 memory organization risk: 未改善；v210 不改变 memory activation、state/conflict 或 query-time organization。

后续 #2/#3 不能继续走无保护的 tail text 截断。更合理的方向是 source-backed span preservation、query-side context organization 或 answer-bearing span protection，但必须仍然只使用 raw evidence、question、route、rank 和 source-backed typed memory，不能使用 gold、judge、benchmark label、sample id 或样本级规则。

## 产物

- LME run record: `experiments/diagnostic/stage1_role_aware_tail_snippet_v210_lme_s_full/`
- LME predictions/traces: `outputs/diagnostic/stage1_role_aware_tail_snippet_v210_lme_s_full/`
- changed-answer judge artifacts: `outputs/diagnostic/stage1_role_aware_tail_snippet_v210_lme_changed_vs_v209/`

