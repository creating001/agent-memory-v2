# stage1_workspace_policy_safe_pack_v324_locomo_full_changed_vs_v288

## Purpose

Offline changed-answer judge for all LoCoMo non-adversarial full answers changed by v324 relative to v288.

Clean note: labels and judge outputs are evaluation-only and are not used by prediction, retrieval, compiler, answer, verifier, memory build, or cache construction.

## Result

DeepSeek dual `deepseek-v4-flash`, temperature `0`, default thinking.

| Prediction set | strict | lenient |
|---|---:|---:|
| old v288 changed subset | `505/691` | `530/691` |
| new v324 changed subset | `488/691` | `507/691` |

Win/loss on changed subset:

| Metric | Wins | Losses |
|---|---:|---:|
| strict | `50` | `67` |
| lenient | `44` | `67` |

Projected LoCoMo full, inheriting unchanged v288 answers:

| Metric | v288 LTS | projected v324 |
|---|---:|---:|
| strict | `1223/1540` (`0.794156`) | `1206/1540` (`0.783117`) |
| lenient | `1262/1540` (`0.819481`) | `1239/1540` (`0.804545`) |

## Decision

V324 should not be promoted to LTS. It improves query token cost but regresses LoCoMo full accuracy.
