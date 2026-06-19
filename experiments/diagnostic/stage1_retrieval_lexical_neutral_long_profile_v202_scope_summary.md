# stage1_retrieval_lexical_neutral_long_profile_v202 LTS summary

## Decision

V202 replaces v201 as the current local LTS.

V202 inherits v201 and removes one redundant retrieval override from the remaining `long_turn_precision` avg-turn-length profile:

- `retrieval.lexical_protect_top_n = 0`

The global dense retrieval config already sets `lexical_protect_top_n = 0`, so keeping the same zero value inside the long profile adds profile-specific coupling without changing lexical candidate protection. V202 does not change `top_k`, `max_top_k`, `dense_top_k`, or `dense_protect_top_n`.

## Clean Boundary

- Prediction uses only question text, raw Memory Context, visible metadata, and build-stage memory generated before the question.
- No gold answer, judge output, benchmark label, sample id, row index, test feedback, or sample-level rule is used by retrieval, compiler, answer, repair, finalizer, audit, or cache construction.
- Answer cache reuse is valid because v202 answers and compiled contexts are identical to v201 on both full benchmarks.
- The trace normalization below only removes the deleted `granularity_profile.retrieval.lexical_protect_top_n` snapshot key when comparing traces; it is offline audit logic and is not used during prediction.

## Full Verification

| Benchmark | v202 vs v201 answer diff | route diff | compiled context diff | trace note | v202 answer cache | Inherited judge accuracy |
|---|---:|---:|---:|---|---:|---:|
| LongMemEval-S full | `0/500` | `0/500` | `0/500` | raw trace diff `500/500` only because the profile config snapshot no longer contains the redundant key; normalized trace diff `0/500` | `500/0/0` | strict/lenient `0.834000 / 0.846000` |
| LoCoMo non-adversarial full | `0/1540` | `0/1540` | `0/1540` | raw trace diff `2/1540` only from embedding cache hit accounting metadata on two adjacent rows | `1540/0/0` | strict/lenient `0.793506 / 0.818831` |

Token accounting from the run summaries:

| Benchmark | avg build tokens | avg query tokens |
|---|---:|---:|
| LongMemEval-S full | `85393.566` | `6579.622` |
| LoCoMo non-adversarial full | `62015.57402597403` | `6095.268181818182` |

## Audit Coverage

| Benchmark | profile selected | selected profile | behavior status |
|---|---:|---|---|
| LongMemEval-S full | `500/500` | `long_turn_precision` | retrieval profile remains active, but its redundant lexical-protect subkey is removed |
| LoCoMo non-adversarial full | `0/1540` | none | unchanged; long profile is not selected |

Selected-context risk audit is unchanged:

| Benchmark | selected-context audit applied | risk rows |
|---|---:|---:|
| LongMemEval-S full | `0/500` | `0` |
| LoCoMo non-adversarial full | `329/1540` | `1083` |

Activation probe:

- Answer/route/compiled context/raw trace diff vs v201: `0/3`.
- Answer cache: `3/0/0`.
- Granularity audit selected no profile on `3/3` rows.

## Why This Is LTS

V202 is a cleaner LTS than v201 because it removes a redundant profile-specific retrieval knob while preserving full behavior and judge accuracy. This is a small but real reduction of the #1/#3 profile design-risk surface: fewer remaining `long_turn_precision` settings now need to be justified as behavior-changing.

This does not solve the remaining avg-turn profile. The next LTS should replace the remaining retrieval top-k cap, selected-context settings, and compiler controls with general query/context-pressure or route-scoped mechanisms. Direct selected-context defaultization remains rejected because v200 offline simulation expanded LME materialized selected-context rows from `3/500` to `317/500`.

## Artifacts

- Config: `configs/stage1_retrieval_lexical_neutral_long_profile_v202_seeded_qwen36_no_think_build4k_cached.json`
- Method commit: `edd9c8bd25daa3ec3b4ac5df8e56f0cedd8246db`
- Activation probe: `experiments/diagnostic/stage1_retrieval_lexical_neutral_long_profile_v202_activation_probe/`
- LME full: `experiments/diagnostic/stage1_retrieval_lexical_neutral_long_profile_v202_lme_s_full/`
- LoCoMo full: `experiments/diagnostic/stage1_retrieval_lexical_neutral_long_profile_v202_locomo_nonadv_full/`
- Outputs: `outputs/diagnostic/stage1_retrieval_lexical_neutral_long_profile_v202_*`

## Next

- Test route-scoped or context-pressure replacements for the remaining `long_turn_precision` retrieval top-k cap.
- Design a narrow selected-context gate before changing prompt-visible selected context.
- Continue #5 lifecycle/state/conflict/query-time reasoning with build memory as a managed, query-activated view rather than a benchmark-specific evidence shortcut.
