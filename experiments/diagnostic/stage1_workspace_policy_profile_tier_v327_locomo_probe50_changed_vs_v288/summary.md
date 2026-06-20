# stage1_workspace_policy_profile_tier_v327_locomo_probe50_changed_vs_v288

## Purpose

Offline changed-answer judge for LoCoMo probe50 answers changed by v327 relative to v288.

Clean note: labels and judge outputs are evaluation-only and are not used by prediction, retrieval, compiler, answer, verifier, memory build, or cache construction.

## Result

DeepSeek dual `deepseek-v4-flash`, temperature `0`, default thinking.

| Prediction set | strict | lenient |
|---|---:|---:|
| old v288 changed subset | `18/21` | `19/21` |
| new v327 changed subset | `18/21` | `20/21` |

Win/loss on changed subset:

| Metric | Wins | Losses |
|---|---:|---:|
| strict | `2` | `2` |
| lenient | `2` | `1` |

Token cost on probe50:

| Run | avg query |
|---|---:|
| v288 | `6544.92` |
| v327 | `5931.48` |

## Decision

V327 passes probe50: query tokens drop below 6K and changed-answer judge does not regress strict accuracy. Proceed to full LongMemEval-S and LoCoMo validation before LTS decision.
