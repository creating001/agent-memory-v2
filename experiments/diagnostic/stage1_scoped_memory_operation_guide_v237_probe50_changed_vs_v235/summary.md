# v237 Scoped Memory Operation Guide Probe50

## Purpose

Evaluate whether v237 can keep the source-backed Memory Operations Guide while removing the v236 list_count over-broad collection risk.

## Setup

- parent LTS: v235 `configs/stage1_no_finalizer_v235_seeded_qwen36_no_think_build4k_cached.json`
- candidate: v237 `configs/stage1_scoped_memory_operation_guide_v237_seeded_qwen36_no_think_build4k_cached.json`
- prediction commit: `fe37190e6988a30e4e62baff1c0de3606694197f`
- prediction dirty note: LoCoMo probe was run after the LME probe directory existed untracked; no code/config edits were present.
- changed-answer judge: DeepSeek dual `deepseek-v4-flash`, temperature `0`, default thinking, `--no-resume`
- clean note: labels and judge outputs were used only after prediction for offline evaluation.

## Probe Metrics

| Benchmark | v237 answer diff vs v235 | avg build tokens | avg query tokens | answer cache | guide applied |
|---|---:|---:|---:|---:|---:|
| LongMemEval-S probe50 | `3/50` | `86398.54` | `5780.74` | `36` hit / `14` miss | `14/50` |
| LoCoMo non-adversarial probe50 | `11/50` | `45868.0` | `6718.52` | `24` hit / `26` miss | `26/50` |

## Changed-Answer Judge

| Benchmark | v235 strict/lenient | v237 strict/lenient | Decision |
|---|---:|---:|---|
| LongMemEval-S changed answers | `3/3` / `3/3` | `3/3` / `3/3` | tie |
| LoCoMo changed answers | `10/11` / `10/11` | `9/11` / `10/11` | strict regression |

## Diagnosis

v237 fixes the v236 list_count failure mode, but temporal_lookup operation-guide activation is still too broad. The LoCoMo strict regression is `c2f37be687257b36c7101ac4`: the question asks when Melanie went camping in July; v235 answers `July 8-9, 2023`, while v237 answers `July 8-9, 2023 and July 15, 2023`. The guide exposed a source-backed July 15 camping collection record, but the activation did not distinguish the target event from a nearby same-month camping mention.

## Decision

Do not promote v237 to LTS. Keep it as a useful method step because source-backed operation records are cleaner than query-time patching, but the next version should remove or sharply gate temporal_lookup guide activation before any full run.

## Outputs

- LME probe: `outputs/diagnostic/stage1_scoped_memory_operation_guide_v237_lme_probe50/`
- LoCoMo probe: `outputs/diagnostic/stage1_scoped_memory_operation_guide_v237_locomo_probe50/`
- changed judge files: `experiments/diagnostic/stage1_scoped_memory_operation_guide_v237_probe50_changed_vs_v235/`
