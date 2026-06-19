# stage1_route_neutral_long_profile_v199 LTS summary

## Decision

V199 replaces v198 as the current local LTS.

V199 inherits v198 and removes the `route` override from the remaining `long_turn_precision` avg-turn-length profile. Offline route simulation showed that default routing and long-profile routing are identical on LongMemEval-S full (`0/500` route diff). LoCoMo does not select the profile after v198, so this change cannot affect LoCoMo routing.

## Clean Boundary

- Prediction uses only question text, raw Memory Context, visible metadata, and build-stage memory generated before the question.
- No gold answer, judge output, benchmark label, sample id, row index, test feedback, or sample-level rule is used by retrieval, compiler, answer, repair, finalizer, audit, or cache construction.
- Answer cache reuse is valid because v199 prompt and answer are identical to v198 on both full benchmarks.
- The route simulation was offline analysis using question text only; it is not used by prediction.

## Full Verification

| Benchmark | v199 vs v198 prompt diff | v199 vs v198 answer diff | v199 vs v198 route diff | v199 answer cache | Inherited judge accuracy |
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
| LongMemEval-S full | `500/500` | `long_turn_precision` | retrieval, selected_context, compiler, answer_finalizer | `5` |
| LoCoMo non-adversarial full | `0/1540` | none | none | `0` |

Compared with v198, LME profile behavior sections drop from 5 to 4 because route is no longer profile-controlled. LoCoMo remains profile-free after v198.

V199 also preserves the selected-context risk audit inherited from v196/v198:

| Benchmark | selected-context audit applied | risk rows |
|---|---:|---:|
| LongMemEval-S full | `0/500` | `0` |
| LoCoMo non-adversarial full | `329/1540` | `1083` |

Activation probe:

- Prompt/answer diff vs v198: `0/3`.
- Answer cache: `3/0/0`.
- Granularity audit selected no profile on `3/3` rows and recorded `0` behavior-risk rows.

## Why This Is LTS

V199 is a safer LTS than v198 because it removes one more behavior-changing surface from the avg-turn profile without changing any full prompt, route, or answer. It is a narrow but real reduction of #1 granularity/profile risk and #3 selected-context-adjacent profile coupling.

The remaining risk is explicit: LongMemEval-S still selects `long_turn_precision` for retrieval, selected_context, compiler, and answer_finalizer settings on every row. The next LTS should replace those remaining settings with general query/context-pressure or route-scoped mechanisms, then verify any changed answers with paired judge.

## Artifacts

- Config: `configs/stage1_route_neutral_long_profile_v199_seeded_qwen36_no_think_build4k_cached.json`
- Method commit: `df06cf40966e624d38a4114b2de331930c3cc8f6`
- Git dirty during runs: true; dirty state was the newly generated v199 experiment directories.
- Activation probe: `experiments/diagnostic/stage1_route_neutral_long_profile_v199_activation_probe/`
- LME full: `experiments/diagnostic/stage1_route_neutral_long_profile_v199_lme_s_full/`
- LoCoMo full: `experiments/diagnostic/stage1_route_neutral_long_profile_v199_locomo_nonadv_full/`
- Outputs: `outputs/diagnostic/stage1_route_neutral_long_profile_v199_*`

## Next

- Split `long_turn_precision` retrieval/top-k behavior into route-scoped or context-pressure settings.
- Replace selected-context and compiler profile settings with general pressure gates, preserving v196/v199 risk audit.
- Continue #5 lifecycle/state/conflict/query-time reasoning with build memory as a managed, query-activated view rather than a benchmark-specific evidence shortcut.
