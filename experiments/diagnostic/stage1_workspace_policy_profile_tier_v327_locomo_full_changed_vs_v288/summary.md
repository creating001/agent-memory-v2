# stage1_workspace_policy_profile_tier_v327_locomo_full_changed_vs_v288

## Purpose

Offline changed-answer judge for all LoCoMo non-adversarial full answers changed by v327 relative to the v288 LTS.

Clean note: labels and judge outputs are evaluation-only and are not used by prediction, retrieval, compiler, answer, verifier, memory build, or cache construction.

## Result

DeepSeek dual `deepseek-v4-flash`, temperature `0`, default thinking.

| Prediction set | strict | lenient |
|---|---:|---:|
| old v288 changed subset | `511/684` | `534/684` |
| new v327 changed subset | `490/684` | `509/684` |

Win/loss on changed subset:

| Metric | Wins | Losses |
|---|---:|---:|
| strict | `45` | `66` |
| lenient | `43` | `68` |

Projected LoCoMo full, inheriting unchanged v288 answers:

| Metric | v288 LTS | projected v327 |
|---|---:|---:|
| strict | `1223/1540` (`0.794156`) | `1202/1540` (`0.780519`) |
| lenient | `1262/1540` (`0.819481`) | `1237/1540` (`0.803247`) |

Token cost:

| Run | avg build | avg query |
|---|---:|---:|
| v288 LTS | `62015.57402597403` | `6093.962337662338` |
| v325 relaxed pack | `62015.57402597403` | `5787.902597402597` |
| v327 profile tiers | `62015.57402597403` | `5755.87987012987` |

Judge reuse:

| Source | Count |
|---|---:|
| old v288 reused from v324 changed subset | `576` |
| old v288 reused from v325 supplement | `49` |
| old v288 reused from v327 probe | `3` |
| old v288 supplement judged | `56` |
| new v327 reused from probe | `21` |
| new v327 supplement judged | `663` |

## Diagnosis

V327 improves query token cost and makes selected-context profile selection build-owned and explicit, but the LoCoMo changed-answer judge regresses more than v324/v325. Preserving row/source count while changing selected-context presentation to compact/center-only is still enough to perturb answers on many samples.

This means the next iteration should not keep searching only within selected-context formatting. The safer direction is to reduce query token by removing or shortening guide text and redundant query-side compatibility layers while keeping raw evidence presentation closer to v288 for LoCoMo.

## Decision

Do not promote v327 to LTS. Keep v288 as LTS.
