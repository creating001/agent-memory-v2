# stage1_granularity_profile_audit_v197 LTS summary

## Decision

V197 replaces v196 as the current local LTS.

V197 inherits v196 and adds a trace-only granularity profile audit. The audit records when avg-turn-length granularity profiles select behavior-changing route, retrieval, selected-context, compiler, or finalizer overrides. It never changes retrieval, prompts, answers, repair, finalizer, or cache keys.

## Clean Boundary

- Prediction uses only question text, raw Memory Context, visible metadata, and build-stage memory generated before the question.
- No gold answer, judge output, benchmark label, sample id, row index, test feedback, or sample-level rule is used by retrieval, compiler, answer, repair, finalizer, audit, or cache construction.
- Answer cache reuse is valid because v197 prompt and answer are identical to v196 on both full benchmarks.
- The granularity profile audit is trace-only and is not included in the answer prompt.

## Full Verification

| Benchmark | v197 vs v196 prompt diff | v197 vs v196 answer diff | v197 answer cache | Inherited judge accuracy |
|---|---:|---:|---:|---:|
| LongMemEval-S full | `0/500` | `0/500` | `500/0/0` | strict/lenient `0.834000 / 0.846000` |
| LoCoMo non-adversarial full | `0/1540` | `0/1540` | `1540/0/0` | strict/lenient `0.793506 / 0.818831` |

## Audit Coverage

| Benchmark | profile selected | selected profile | behavior-risk rows |
|---|---:|---|---:|
| LongMemEval-S full | `500/500` | `long_turn_precision` | `500` |
| LoCoMo non-adversarial full | `1540/1540` | `short_turn_v96_spacing` | `1540` |

V197 also preserves v196 selected-context risk audit coverage:

| Benchmark | selected-context audit applied | risk rows |
|---|---:|---:|
| LongMemEval-S full | `0/500` | `0` |
| LoCoMo non-adversarial full | `329/1540` | `1083` |

Activation probe:

- Prompt/answer diff vs v196: `0/3`.
- Answer cache: `3/0/0`.
- Granularity audit selected `short_turn_v96_spacing` on `3/3` rows and recorded behavior risk on `3/3`.
- Selected-context risk audit remains unchanged: `3/3` applied, `6` risk rows.

## Why This Is LTS

V197 reduces hidden #1 granularity/profile and #3 selected-context risk by making the avg-turn-length profile selector measurable on full benchmarks while preserving v196 accuracy. The result shows the current LTS behavior still depends heavily on coarse dataset-level conversation granularity: LongMemEval-S full always selects the long-turn profile, while LoCoMo non-adversarial full always selects the short-turn profile.

This is not a final fix for granularity. It is a safer LTS than v196 because the risk is now explicit, measurable, and tied to full-run traces without changing the answer surface. The next LTS should replace this avg-turn selector with a more general query/context-pressure or route-scoped mechanism, then verify changed answers with paired judge if any answer changes.

## Artifacts

- Config: `configs/stage1_granularity_profile_audit_v197_seeded_qwen36_no_think_build4k_cached.json`
- Method commit: `56e165bf3f59d7fbd901760bf853b8eba5667528`
- Activation probe: `experiments/diagnostic/stage1_granularity_profile_audit_v197_activation_probe/`
- LME full: `experiments/diagnostic/stage1_granularity_profile_audit_v197_lme_s_full/`
- LoCoMo full: `experiments/diagnostic/stage1_granularity_profile_audit_v197_locomo_nonadv_full/`
- Outputs: `outputs/diagnostic/stage1_granularity_profile_audit_v197_*`

## Next

- Replace avg-turn-length granularity profiles with a general query/context-pressure or route-scoped strategy.
- Preserve v196 selected-context risk audit, but avoid v195-style hard deletion unless changed-answer judge proves it helps.
- Continue #5 lifecycle/state/conflict/query-time reasoning with source-backed typed memory plus raw evidence verification.
