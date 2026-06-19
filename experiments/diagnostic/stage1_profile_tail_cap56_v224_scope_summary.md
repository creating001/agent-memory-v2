# stage1_profile_tail_cap56_v224 rejection summary

## Decision

V224 is rejected and does not replace v222 LTS.

V224 narrows v223's route cap to `profile_preference` only. It keeps v222 source-anchor ordering and raw source rows, but caps profile/preference final evidence at `56` rows. `fact_lookup`, `list_count`, `temporal_lookup`, and `current_state` stay unchanged.

## Clean Boundary

- Prediction uses only question text, raw Memory Context, visible metadata, and build-stage memory generated before the question.
- No gold answer, judge output, benchmark label, sample id, row index, test feedback, or sample-level rule is used by retrieval, compiler, answer, repair, finalizer, cache construction, or the cap.
- Judge is run only offline after prediction on changed answers.

## Full Prediction Diff

| Benchmark | prompt diff | evidence rows diff | retrieval hits diff | answer diff | answer cache |
|---|---:|---:|---:|---:|---:|
| LongMemEval-S full | `0/500` | `0/500` | `0/500` | `0/500` | `500/0/0` |
| LoCoMo non-adversarial full | `40/1540` | `40/1540` | `0/1540` | `18/1540` | `1540/0/0` |

## Risk And Cost

| Benchmark | avg build tokens | avg query tokens | avg evidence rows | row drop |
|---|---:|---:|---:|---:|
| LongMemEval-S full | `85393.566` | `6580.196` | `34.746` | `0` |
| LoCoMo non-adversarial full | `62015.57402597403` | `6089.122727272727` | `54.05194805194805` | `140` rows / `18646` chars |

Compared with v222, LoCoMo avg query tokens drop only from `6095.268181818182` to `6089.122727272727`.

## Changed-Answer Judge

| Benchmark | changed answers | v222 strict/lenient | v224 strict/lenient | delta |
|---|---:|---:|---:|---:|
| LoCoMo non-adversarial full | `18` | `13/18`, `13/18` | `12/18`, `13/18` | `-1 / 0` |

Derived LoCoMo full accuracy would become strict/lenient `0.7928571428571428 / 0.8188311688311688`, compared with v222 `0.793506 / 0.818831`. The token reduction is too small and strict accuracy drops, so v224 fails the LTS requirement.

## Diagnosis

V224 confirms that profile/preference tail rows are safer to compact than fact/list tail rows, but a blind route cap is still not a strong enough signal. The next #2 attempt should protect profile rows with question-term/source-flow coverage and use typed memory as a positive source anchor, not just lower a route cap.

## Artifacts

- Method commit: `bfb5b0470698b4624bc0b5e6af553bd871f73008`
- Config: `configs/stage1_profile_tail_cap56_v224_seeded_qwen36_no_think_build4k_cached.json`
- LME run: `experiments/diagnostic/stage1_profile_tail_cap56_v224_lme_s_full/`
- LoCoMo run: `experiments/diagnostic/stage1_profile_tail_cap56_v224_locomo_nonadv_full/`
- Changed judge outputs: `outputs/diagnostic/stage1_profile_tail_cap56_v224_changed_vs_v222/`
- Git status during runs: LME clean; LoCoMo dirty only because the LME experiment directory was already untracked.
