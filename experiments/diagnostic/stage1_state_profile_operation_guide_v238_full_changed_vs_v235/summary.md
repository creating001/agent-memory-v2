# v238 State/Profile Operation Guide Full Evaluation

## Purpose

Evaluate whether v238 can become the new LTS after passing probe50. v238 keeps source-backed Memory Operations Guide only for `current_state` and `profile_preference`, while list_count and temporal_lookup use the v235 path.

## Setup

- parent LTS: v235 `configs/stage1_no_finalizer_v235_seeded_qwen36_no_think_build4k_cached.json`
- candidate: v238 `configs/stage1_state_profile_operation_guide_v238_seeded_qwen36_no_think_build4k_cached.json`
- prediction commit: `2eca3b473515957699d01d8ffcbdd007db4d3bf5`
- LME manifest dirty: false
- LoCoMo manifest dirty: true only because the LME full experiment directory was already untracked during the LoCoMo run
- changed-answer judge: DeepSeek dual `deepseek-v4-flash`, temperature `0`, default thinking, `--no-resume`
- clean note: prediction did not use labels, judge output, benchmark tags, sample ids, test feedback, gold answers, or sample-level rules.

## Full Prediction Metrics

| Benchmark | answer diff vs v235 | avg build tokens | avg query tokens | answer cache | guide applied |
|---|---:|---:|---:|---:|---:|
| LongMemEval-S full | `19/500` | `85393.566` | `6319.564` | `465` hit / `35` miss | `37/500` |
| LoCoMo non-adversarial full | `26/1540` | `62015.57402597403` | `6116.58051948052` | `1493` hit / `47` miss | `50/1540` |

## Changed-Answer Judge

| Benchmark | v235 strict/lenient on changed | v238 strict/lenient on changed | Derived v238 full strict/lenient | Decision |
|---|---:|---:|---:|---|
| LongMemEval-S | `14/19` / `15/19` | `6/19` / `7/19` | `408/500` / `414/500` = `0.816000 / 0.828000` | reject |
| LoCoMo non-adversarial | `19/26` / `19/26` | `18/26` / `18/26` | `1222/1540` / `1261/1540` = `0.793506 / 0.818831` | reject |

## Diagnosis

v238 removes the earlier unsafe scopes from v236 and v237, but the remaining prompt-side guide still changes answer behavior. All full answer diffs occur on examples whose prompt includes `Memory Operations Guide`; LME changed answers split across `current_state` (`10`) and `profile_preference` (`9`), while LoCoMo is mostly `profile_preference` (`23`) with a small `current_state` tail (`3`).

The main LME losses show two recurring patterns:

- profile/advice questions become too narrow or over-refuse, e.g. cultural events, cookie advice, NAS purchase, evening activities, and publications/conferences.
- current-state questions can over-trust the operation view or reorder temporal/state evidence incorrectly, e.g. current role duration, most recent family trip, and trip ordering.

This means the source-backed operation view is clean but too strong as an answer-prompt block. It should not be promoted as LTS. The next method should move memory operations into build-side memory quality, retrieval activation, or trace-only/verifier-side auditing, rather than directly telling the reader to reorganize answers from a compact operation list.

## Decision

Do not promote v238. Current LTS remains v235.

## Outputs

- LME full: `outputs/diagnostic/stage1_state_profile_operation_guide_v238_lme_s_full/`
- LoCoMo full: `outputs/diagnostic/stage1_state_profile_operation_guide_v238_locomo_nonadv_full/`
- changed judge files: `experiments/diagnostic/stage1_state_profile_operation_guide_v238_full_changed_vs_v235/`
