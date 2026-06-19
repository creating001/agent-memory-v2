# stage1_route_tail_cap56_v223 rejection summary

## Decision

V223 is rejected and does not replace v222 LTS.

V223 keeps source rows and retrieval order intact, but caps `fact_lookup`, `list_count`, and `profile_preference` final evidence at `56` rows. It protects `temporal_lookup` at the existing `40` rows and leaves `current_state` at `60` rows.

## Clean Boundary

- Prediction uses only question text, raw Memory Context, visible metadata, and build-stage memory generated before the question.
- No gold answer, judge output, benchmark label, sample id, row index, test feedback, or sample-level rule is used by retrieval, compiler, answer, repair, finalizer, cache construction, or the cap.
- Judge is run only offline after prediction on changed answers.

## Full Prediction Diff

| Benchmark | prompt diff | evidence rows diff | retrieval hits diff | answer diff | answer cache |
|---|---:|---:|---:|---:|---:|
| LongMemEval-S full | `0/500` | `0/500` | `0/500` | `0/500` | `500/0/0` |
| LoCoMo non-adversarial full | `927/1540` | `927/1540` | `0/1540` | `369/1540` | `622/918/918` |

## Risk And Cost

| Benchmark | avg build tokens | avg query tokens | avg evidence rows | row drop |
|---|---:|---:|---:|---:|
| LongMemEval-S full | `85393.566` | `6580.196` | `34.746` | `0` |
| LoCoMo non-adversarial full | `62015.57402597403` | `5980.044155844156` | `51.98376623376623` | `3325` rows / `428988` chars |

Compared with v222, LoCoMo avg query tokens drop from `6095.268181818182` to `5980.044155844156`, but the answer drift is too wide.

## Changed-Answer Judge

| Benchmark | changed answers | v222 strict/lenient | v223 strict/lenient | delta |
|---|---:|---:|---:|---:|
| LoCoMo non-adversarial full | `369` | `258/369`, `273/369` | `245/369`, `261/369` | `-13 / -12` |

Derived LoCoMo full accuracy would become strict/lenient `0.785064935064935 / 0.811038961038961`, down from v222 `0.793506 / 0.818831`. This fails the LTS requirement.

## Diagnosis

The route-scoped cap is clean and source/span-preserving, but it is still too broad: dropping only low-rank final evidence rows changes many fact/list/profile answers. V223 confirms that final evidence row count alone is not a safe pruning signal. The next #2 attempt should use v222's pressure ledger to identify redundant rows with stronger protection for question-term coverage, selected-context source flow, memory/source anchors, and local temporal/session chains.

## Artifacts

- Method commit: `908b8ccd1b6cc5704143b59fd4c2a1dbba11287f`
- Config: `configs/stage1_route_tail_cap56_v223_seeded_qwen36_no_think_build4k_cached.json`
- LME run: `experiments/diagnostic/stage1_route_tail_cap56_v223_lme_s_full/`
- LoCoMo run: `experiments/diagnostic/stage1_route_tail_cap56_v223_locomo_nonadv_full/`
- Changed judge outputs: `outputs/diagnostic/stage1_route_tail_cap56_v223_changed_vs_v222/`
- Git status during runs: LME clean; LoCoMo dirty only because the LME experiment directory was already untracked.
