# stage1_workspace_policy_profile_tier_v327_lme_full_changed_vs_v288

## Purpose

Offline changed-answer judge for the single LongMemEval-S full answer changed by v327 relative to v288.

Clean note: labels and judge outputs are evaluation-only and are not used by prediction, retrieval, compiler, answer, verifier, memory build, or cache construction.

## Result

DeepSeek dual `deepseek-v4-flash`, temperature `0`, default thinking.

| Prediction set | strict | lenient |
|---|---:|---:|
| old v288 changed subset | `1/1` | `1/1` |
| new v327 changed subset | `1/1` | `1/1` |

Projected LongMemEval-S full, inheriting unchanged v288 answers:

| Metric | v288 LTS | projected v327 |
|---|---:|---:|
| strict | `417/500` (`0.834000`) | `417/500` (`0.834000`) |
| lenient | `423/500` (`0.846000`) | `423/500` (`0.846000`) |

## Decision

V327 passes LongMemEval-S full. LoCoMo full remains required before any LTS promotion.
