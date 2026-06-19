# stage1_default_short_context_layout_v198 LTS summary

## Decision

V198 replaces v197 as the current local LTS.

V198 inherits v197, removes the `short_turn_v96_spacing` avg-turn-length profile, and moves that profile's only prompt-affecting behavior, `compiler.memory_context_newlines_after_blocks = 4`, into the default compiler layout. The remaining `long_turn_precision` profile keeps its explicit newline setting so LongMemEval-S prompts stay identical to v197.

## Clean Boundary

- Prediction uses only question text, raw Memory Context, visible metadata, and build-stage memory generated before the question.
- No gold answer, judge output, benchmark label, sample id, row index, test feedback, or sample-level rule is used by retrieval, compiler, answer, repair, finalizer, audit, or cache construction.
- Answer cache reuse is valid because v198 prompt and answer are identical to v197 on both full benchmarks.
- The granularity profile audit is trace-only and is not included in the answer prompt.

## Full Verification

| Benchmark | v198 vs v197 prompt diff | v198 vs v197 answer diff | v198 answer cache | Inherited judge accuracy |
|---|---:|---:|---:|---:|
| LongMemEval-S full | `0/500` | `0/500` | `500/0/0` | strict/lenient `0.834000 / 0.846000` |
| LoCoMo non-adversarial full | `0/1540` | `0/1540` | `1540/0/0` | strict/lenient `0.793506 / 0.818831` |

Token accounting from the run summaries:

| Benchmark | avg build tokens | avg query tokens |
|---|---:|---:|
| LongMemEval-S full | `85393.566` | `6579.622` |
| LoCoMo non-adversarial full | `62015.574` | `6095.268` |

## Audit Coverage

| Benchmark | profile selected | selected profile | behavior-risk rows |
|---|---:|---|---:|
| LongMemEval-S full | `500/500` | `long_turn_precision` | `500` |
| LoCoMo non-adversarial full | `0/1540` | none | `0` |

V198 also preserves the selected-context risk audit inherited from v196/v197:

| Benchmark | selected-context audit applied | risk rows |
|---|---:|---:|
| LongMemEval-S full | `0/500` | `0` |
| LoCoMo non-adversarial full | `329/1540` | `1083` |

Activation probe:

- Prompt/answer diff vs v197: `0/3`.
- Answer cache: `3/0/0`.
- Granularity audit selected no profile on `3/3` rows and recorded `0` behavior-risk rows.

## Why This Is LTS

V198 is a safer LTS than v197 because it removes the short-turn avg-turn profile from the behavioral path without changing full prompts or answers. This directly reduces #1 granularity/profile and #3 selected-context risk on LoCoMo while preserving full judge accuracy.

The remaining risk is explicit: LongMemEval-S still selects `long_turn_precision` on every row. The next LTS should replace that remaining avg-turn selector with a general query/context-pressure or route-scoped mechanism, then verify any changed answers with paired judge.

## Artifacts

- Config: `configs/stage1_default_short_context_layout_v198_seeded_qwen36_no_think_build4k_cached.json`
- Method commit: `b89c18b728494bba4b0d8d84acfc0792c343d88e`
- Git dirty during runs: true; dirty state was the newly generated v198 experiment directories.
- Activation probe: `experiments/diagnostic/stage1_default_short_context_layout_v198_activation_probe/`
- LME full: `experiments/diagnostic/stage1_default_short_context_layout_v198_lme_s_full/`
- LoCoMo full: `experiments/diagnostic/stage1_default_short_context_layout_v198_locomo_nonadv_full/`
- Outputs: `outputs/diagnostic/stage1_default_short_context_layout_v198_*`

## Next

- Replace `long_turn_precision` with a general context-pressure or route-scoped strategy.
- Preserve selected-context risk tracing, but avoid v195-style hard deletion unless changed-answer judge proves it helps.
- Continue #5 lifecycle/state/conflict/query-time reasoning with source-backed typed memory plus raw evidence verification.
