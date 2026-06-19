# stage1_finalizer_neutral_long_profile_v200 LTS summary

## Decision

V200 replaces v199 as the current local LTS.

V200 inherits v199 and removes the `answer_finalizer` override from the remaining `long_turn_precision` avg-turn-length profile. V199 and v200 full runs both show `finalizer_applied_count = 0`, so the profile-specific missing-detail finalizer setting is unnecessary behavior surface.

## Clean Boundary

- Prediction uses only question text, raw Memory Context, visible metadata, and build-stage memory generated before the question.
- No gold answer, judge output, benchmark label, sample id, row index, test feedback, or sample-level rule is used by retrieval, compiler, answer, repair, finalizer, audit, or cache construction.
- Answer cache reuse is valid because v200 prompt and answer are identical to v199 on both full benchmarks.
- The selected-context defaultization diagnostic is offline trace simulation only; it is not used by prediction.

## Full Verification

| Benchmark | v200 vs v199 prompt diff | v200 vs v199 answer diff | v200 vs v199 route diff | v200 answer cache | Inherited judge accuracy |
|---|---:|---:|---:|---:|---:|
| LongMemEval-S full | `0/500` | `0/500` | `0/500` | `500/0/0` | strict/lenient `0.834000 / 0.846000` |
| LoCoMo non-adversarial full | `0/1540` | `0/1540` | `0/1540` | `1540/0/0` | strict/lenient `0.793506 / 0.818831` |

Token accounting from the run summaries:

| Benchmark | avg build tokens | avg query tokens |
|---|---:|---:|
| LongMemEval-S full | `85393.566` | `6579.622` |
| LoCoMo non-adversarial full | `62015.574` | `6095.268` |

## Audit Coverage

| Benchmark | profile selected | selected profile | behavior sections | risk count |
|---|---:|---|---|---:|
| LongMemEval-S full | `500/500` | `long_turn_precision` | retrieval, selected_context, compiler | `4` |
| LoCoMo non-adversarial full | `0/1540` | none | none | `0` |

Compared with v199, LME profile behavior sections drop from 4 to 3 because finalizer is no longer profile-controlled. LoCoMo remains profile-free after v198.

V200 also preserves the selected-context risk audit inherited from v196/v199:

| Benchmark | selected-context audit applied | risk rows |
|---|---:|---:|
| LongMemEval-S full | `0/500` | `0` |
| LoCoMo non-adversarial full | `329/1540` | `1083` |

Activation probe:

- Prompt/answer diff vs v199: `0/3`.
- Answer cache: `3/0/0`.
- Granularity audit selected no profile on `3/3` rows and recorded `0` behavior-risk rows.

## Negative Diagnostic

Directly deleting the `selected_context` override from `long_turn_precision` is not safe. Offline simulation on v199 LME traces showed:

- Current profile selected-context materialized rows: `3/500`.
- Default selected-context materialized rows if the profile override is removed: `317/500`.
- Changed materialized-id rows: `318/500`.
- New default materialized source ids: `1894`.

This matches the earlier v177 lesson: selected-context must not be widened by default. The next selected-context change needs a narrower, source-grounded or query-reference gate before entering the prompt.

## Why This Is LTS

V200 is a safer LTS than v199 because it removes one more behavior-changing surface from the avg-turn profile without changing any full prompt, route, or answer. It also reduces #4 finalizer coupling by keeping the source-grounded consistency guard in the global answer configuration instead of profile-specific finalizer overrides.

The remaining risk is explicit: LongMemEval-S still selects `long_turn_precision` for retrieval, selected_context, and compiler settings on every row. The next LTS should replace those remaining settings with general query/context-pressure or route-scoped mechanisms, then verify any changed answers with paired judge.

## Artifacts

- Config: `configs/stage1_finalizer_neutral_long_profile_v200_seeded_qwen36_no_think_build4k_cached.json`
- Method commit: `0f265583b83a95fa4487519cd296d52c6479d5d0`
- Git dirty during runs: true; dirty state was the newly generated v200 experiment directories.
- Activation probe: `experiments/diagnostic/stage1_finalizer_neutral_long_profile_v200_activation_probe/`
- LME full: `experiments/diagnostic/stage1_finalizer_neutral_long_profile_v200_lme_s_full/`
- LoCoMo full: `experiments/diagnostic/stage1_finalizer_neutral_long_profile_v200_locomo_nonadv_full/`
- Outputs: `outputs/diagnostic/stage1_finalizer_neutral_long_profile_v200_*`

## Next

- Split `long_turn_precision` retrieval/top-k behavior into route-scoped or context-pressure settings.
- Replace selected-context and compiler profile settings with general pressure gates, preserving the v196/v200 risk audit.
- Continue #5 lifecycle/state/conflict/query-time reasoning with build memory as a managed, query-activated view rather than a benchmark-specific evidence shortcut.
