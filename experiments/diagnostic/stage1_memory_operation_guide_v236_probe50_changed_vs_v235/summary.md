# stage1_memory_operation_guide_v236_probe50_changed_vs_v235

## Purpose

Evaluate v236 Memory Operations Guide on controlled probe50 runs against current v235 LTS. The v236 answer cache was seeded from v235 full prediction traces before the final probe rerun, so prompt-identical rows reuse v235 answers and only prompt-changed rows contribute to answer diff.

## Inputs

- v236 config: `configs/stage1_memory_operation_guide_v236_seeded_qwen36_no_think_build4k_cached.json`
- LME probe: `experiments/diagnostic/stage1_memory_operation_guide_v236_lme_probe50`
- LoCoMo probe: `experiments/diagnostic/stage1_memory_operation_guide_v236_locomo_probe50`
- parent: `configs/stage1_no_finalizer_v235_seeded_qwen36_no_think_build4k_cached.json`

## Results

| Benchmark | Probe n | Answer diff vs v235 | v236 changed strict/lenient | v235 changed strict/lenient | Token note |
|---|---:|---:|---:|---:|---|
| LongMemEval-S | 50 | 4 | `4/4` / `4/4` | `4/4` / `4/4` | avg build/query `86398.54 / 5831.0` |
| LoCoMo non-adversarial | 50 | 17 | `11/17` / `13/17` | `11/17` / `14/17` | avg build/query `45868.0 / 6795.34` |

## Diagnosis

- v236 is clean and source-backed, but it is not a new LTS candidate yet: LoCoMo changed-answer lenient count regresses by `1/17`.
- The main badcase is `d5068b3c68a955ba6cdfe705`, a LoCoMo list-count question about Melanie family activities. The operation guide over-emphasized visible camping/Grand Canyon activity records and the answer dropped gold-relevant family activities such as painting/museum.
- The next version should keep the general Memory Operations Guide idea but disable or tighten `list_count` activation before any full run.

## Clean Notes

- Judge was run offline after predictions using `deepseek-v4-flash` dual judge, temperature `0`.
- Changed-only labels were read only by judge scripts, never by prediction, retrieval, compiler, answer, verifier, or cache seeding.
- v236 cache seeding used only v235 prediction traces/predictions and no labels, judge output, benchmark categories, sample ids, test feedback, or gold answers.
