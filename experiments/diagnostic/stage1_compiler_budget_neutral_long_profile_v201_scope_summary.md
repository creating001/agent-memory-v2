# stage1_compiler_budget_neutral_long_profile_v201 LTS summary

## Decision

V201 replaces v200 as the current local LTS.

V201 inherits v200 and removes two redundant compiler budget overrides from the remaining `long_turn_precision` avg-turn-length profile:

- `compiler.max_evidence_items = 40`
- `compiler.max_evidence_chars = 18000`

The profile retrieval path already limits LME to `top_k = 40`, and v200 full traces show final evidence rows never exceed 40. `max_evidence_chars = 18000` is also the global compiler default, so keeping it inside the profile adds unnecessary coupling without changing behavior.

## Clean Boundary

- Prediction uses only question text, raw Memory Context, visible metadata, and build-stage memory generated before the question.
- No gold answer, judge output, benchmark label, sample id, row index, test feedback, or sample-level rule is used by retrieval, compiler, answer, repair, finalizer, audit, or cache construction.
- Answer cache reuse is valid because v201 prompt and answer are identical to v200 on both full benchmarks.
- The evidence-row budget diagnostic is offline trace analysis only; it is not used by prediction.

## Full Verification

| Benchmark | v201 vs v200 prompt diff | v201 vs v200 answer diff | v201 vs v200 route diff | v201 vs v200 compiler trace diff | v201 answer cache | Inherited judge accuracy |
|---|---:|---:|---:|---:|---:|---:|
| LongMemEval-S full | `0/500` | `0/500` | `0/500` | `0/500` | `500/0/0` | strict/lenient `0.834000 / 0.846000` |
| LoCoMo non-adversarial full | `0/1540` | `0/1540` | `0/1540` | `0/1540` | `1540/0/0` | strict/lenient `0.793506 / 0.818831` |

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

The coarse profile audit risk count stays the same as v200 because the compiler section still has behavior-changing settings. V201 still reduces risk by removing two redundant profile-specific compiler keys; remaining compiler settings are now only those that materially affect prompts.

V201 preserves the selected-context risk audit inherited from v196/v200:

| Benchmark | selected-context audit applied | risk rows |
|---|---:|---:|
| LongMemEval-S full | `0/500` | `0` |
| LoCoMo non-adversarial full | `329/1540` | `1083` |

Activation probe:

- Prompt/answer diff vs v200: `0/3`.
- Answer cache: `3/0/0`.
- Granularity audit selected no profile on `3/3` rows and recorded `0` behavior-risk rows.

## Why This Is LTS

V201 is a cleaner LTS than v200 because it removes redundant compiler budget knobs from the avg-turn profile while preserving full behavior. This does not solve the remaining avg-turn profile, but it makes the remaining risk smaller and easier to reason about: retrieval, selected_context, and three compiler prompt controls are the actual remaining surfaces.

The next LTS should replace the remaining retrieval, selected_context, and compiler profile settings with general query/context-pressure or route-scoped mechanisms. Direct selected-context defaultization remains rejected because v200 offline simulation expanded LME materialized selected-context rows from `3/500` to `317/500`.

## Artifacts

- Config: `configs/stage1_compiler_budget_neutral_long_profile_v201_seeded_qwen36_no_think_build4k_cached.json`
- Method commit: `32ac67cbbe8ef1da27b87332b3f4e125d8ffa06e`
- Git dirty during runs: true; dirty state was the newly generated v201 experiment directories.
- Activation probe: `experiments/diagnostic/stage1_compiler_budget_neutral_long_profile_v201_activation_probe/`
- LME full: `experiments/diagnostic/stage1_compiler_budget_neutral_long_profile_v201_lme_s_full/`
- LoCoMo full: `experiments/diagnostic/stage1_compiler_budget_neutral_long_profile_v201_locomo_nonadv_full/`
- Outputs: `outputs/diagnostic/stage1_compiler_budget_neutral_long_profile_v201_*`

## Next

- Test route-scoped or context-pressure replacements for `long_turn_precision` retrieval top-k.
- Design a narrow selected-context gate before changing the prompt; do not defaultize selected_context directly.
- Continue #5 lifecycle/state/conflict/query-time reasoning with build memory as a managed, query-activated view rather than a benchmark-specific evidence shortcut.
