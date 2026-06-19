# stage1_object_slot_tail_rescue_v250_full_summary

## 目的

验证 v250 object-slot tail rescue 是否能作为 v248 trace-only object graph 的低风险 LTS 后继：让 build memory object slot 具备 source-backed retrieval activation 能力，但不通过 RRF 抢占原 evidence。

## 配置

- config: `configs/stage1_object_slot_tail_rescue_v250_seeded_qwen36_no_think_build4k_cached.json`
- method commit: `88c3d20`
- experiment parent commit: `a640f4d`
- answer cache: `outputs/cache/qwen36_no_think_build4k_answer_v250_object_slot_tail_rescue_seeded.sqlite`
- cache seed: v248 full prediction-time traces/predictions only; no labels or judge outputs.

## Clean 口径

- prediction pipeline 不读 gold answer、judge output、benchmark label、sample id、test feedback 或样本级规则。
- changed judge 仅用于 LoCoMo `1` 条 changed-answer offline evaluation，不回流到 retrieval、compiler、answer 或 cache。

## Full 结果

| Benchmark | Scope | object-slot audited | answer diff vs v248 | prompt/retrieval diff | changed judge | strict/lenient |
|---|---:|---:|---:|---:|---|---:|
| LongMemEval-S | `500` | `89/500` | `0/500` | `0/500` / `0/500` | not needed | `0.832000 / 0.844000` |
| LoCoMo non-adversarial | `1540` | `198/1540` | `1/1540` | `1/1540` / `1/1540` | v248 `1/1`, v250 `1/1` strict+lenient | `0.794156 / 0.819481` |

Token / context:

| Benchmark | avg build tokens | avg query tokens | avg context chars | avg evidence |
|---|---:|---:|---:|---:|
| LongMemEval-S | `85393.566` | `6579.782` | `19771.722` | `34.742` |
| LoCoMo non-adversarial | `62015.57402597403` | `6094.0084415584415` | `17401.61103896104` | `54.137662337662334` |

## 诊断

- v250 修复了 v249 的主要风险：object-slot source hits 不再作为强 RRF 信号，不进入 protected rerank source，只作为 tail rescue。
- LME full 完全继承 v248 行为。
- LoCoMo full 唯一变化样本是 `27baf30e807665dacb4ec386`，问题为 “Who is Anthony?”；object-slot 未触发，retrieval 只在 rank `53` 将 `D9:14` 换成 `D11:4`。v248/v250 dual judge 均为 strict+lenient correct，因此不影响 derived full accuracy。
- v250 仍未带来 accuracy 提升；它的 LTS 价值是让 build object graph 从 trace-only 变成有安全 activation 边界的系统能力，并避免 v249 的排序抢占问题。

## 决策

v250 升为当前 LTS。它相对 v248 不回退 accuracy/token，且相对 v249 显著降低 object-slot activation 风险。下一步继续做更实质的 build memory management / evidence utility selection，而不是把 collection slot 作为强检索信号。

## 输出

- LME predictions/traces: `outputs/diagnostic/stage1_object_slot_tail_rescue_v250_lme_full/`
- LoCoMo predictions/traces: `outputs/diagnostic/stage1_object_slot_tail_rescue_v250_locomo_full/`
- full run records: `experiments/diagnostic/stage1_object_slot_tail_rescue_v250_lme_full/`
- full run records: `experiments/diagnostic/stage1_object_slot_tail_rescue_v250_locomo_full/`
- changed judge: `experiments/diagnostic/stage1_object_slot_tail_rescue_v250_full_changed_vs_v248/`
