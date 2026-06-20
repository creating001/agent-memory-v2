# stage1_workspace_policy_relaxed_pack_v325_locomo_full_changed_vs_v288

## Purpose

Offline changed-answer judge for all LoCoMo non-adversarial full answers changed by v325 relative to the v288 LTS.

Clean note: labels and judge outputs are evaluation-only and are not used by prediction, retrieval, compiler, answer, verifier, memory build, or cache construction.

## Result

DeepSeek dual `deepseek-v4-flash`, temperature `0`, default thinking.

| Prediction set | strict | lenient |
|---|---:|---:|
| old v288 changed subset | `499/673` | `521/673` |
| new v325 changed subset | `481/673` | `503/673` |

Old v288 judge reuse:

| Source | Count |
|---|---:|
| reused from v324 changed subset | `552` |
| new supplement judge | `121` |

Win/loss on changed subset:

| Metric | Wins | Losses |
|---|---:|---:|
| strict | `36` | `54` |
| lenient | `34` | `52` |

Projected LoCoMo full, inheriting unchanged v288 answers:

| Metric | v288 LTS | projected v325 |
|---|---:|---:|
| strict | `1223/1540` (`0.794156`) | `1205/1540` (`0.782468`) |
| lenient | `1262/1540` (`0.819481`) | `1244/1540` (`0.807792`) |

Token cost:

| Run | avg build | avg query |
|---|---:|---:|
| v288 LTS | `62015.57402597403` | `6093.962337662338` |
| v324 safe pack | `62015.57402597403` | `5547.798051948052` |
| v325 relaxed pack | `62015.57402597403` | `5787.902597402597` |

Judge token cost:

| Judge set | total tokens |
|---|---:|
| new v325 changed subset | `663383` |
| old v288 supplement | `110579` |

## Diagnosis

v325 partially relaxes v324's over-tight selected-context pack and reduces answer drift from `691/1540` to `673/1540`, while LoCoMo avg query tokens remain below the 6K target. However, the changed-answer judge still shows more losses than wins, and projected LoCoMo full accuracy remains below v288.

The method direction remains useful because selected-context pack ownership is moved into the build-time `memory_workspace_policy_v1` instead of query config constants. The current policy is still too lossy for LoCoMo: it trims enough context to save tokens, but loses answer-critical evidence on a substantial subset.

## Decision

Do not promote v325 to LTS. Keep v288 as LTS. The next iteration should keep build-owned memory workspace policy, but make context packing source-pressure-aware instead of relying on fixed rows/chars/window values.
