# v238 State/Profile Operation Guide Probe50

## Purpose

Test whether the source-backed Memory Operations Guide is safe when scoped to state/profile style questions only, after v236 list_count and v237 temporal_lookup activation proved too broad.

## Setup

- parent LTS: v235 `configs/stage1_no_finalizer_v235_seeded_qwen36_no_think_build4k_cached.json`
- candidate: v238 `configs/stage1_state_profile_operation_guide_v238_seeded_qwen36_no_think_build4k_cached.json`
- prediction commit: `f2f3b8a7a52bbd56255e679dd10c94587ec40f22`
- changed-answer judge: DeepSeek dual `deepseek-v4-flash`, temperature `0`, default thinking, `--no-resume`
- clean note: answer cache was seeded from v235 prediction traces only; labels and judge outputs were used only after prediction for offline evaluation.

## Probe Metrics

| Benchmark | answer diff vs v235 | avg build tokens | avg query tokens | answer cache | guide applied |
|---|---:|---:|---:|---:|---:|
| LongMemEval-S probe50 | `0/50` | `86398.54` | `5696.18` | `48` hit / `2` miss | `2/50` |
| LoCoMo non-adversarial probe50 | `1/50` | `45868.0` | `6555.8` | `48` hit / `2` miss | `2/50` |

## Changed-Answer Judge

| Benchmark | v235 strict/lenient | v238 strict/lenient | Decision |
|---|---:|---:|---|
| LongMemEval-S changed answers | no changed answers | no changed answers | inherit v235 for probe |
| LoCoMo changed answers | `1/1` / `1/1` | `1/1` / `1/1` | tie |

## Diagnosis

v238 removes the two observed unsafe scopes: v236 list_count over-collected activity records, and v237 temporal_lookup over-included a July 15 camping record. In probe50, the remaining state/profile guide activates only `2/50` examples on each benchmark. The single LoCoMo answer change is `6b6d09d7e82567bbb2a34cf0` ("What do Melanie's kids like?"); v238 shifts toward source-backed dinosaurs/nature wording, and dual judge remains correct.

## Decision

v238 passes probe but is not promoted to LTS from probe evidence alone. Next step is a full prediction/changed-answer evaluation if we want to claim it as the new LTS; otherwise keep v235 as current LTS and v238 as a safer operation-guide candidate.

## Outputs

- LME probe: `outputs/diagnostic/stage1_state_profile_operation_guide_v238_lme_probe50/`
- LoCoMo probe: `outputs/diagnostic/stage1_state_profile_operation_guide_v238_locomo_probe50/`
- changed judge files: `experiments/diagnostic/stage1_state_profile_operation_guide_v238_probe50_changed_vs_v235/`
