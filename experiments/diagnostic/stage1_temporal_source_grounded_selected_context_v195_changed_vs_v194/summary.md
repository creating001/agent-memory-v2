# V195 source-grounded temporal selected-context rejection

## Decision

V195 is rejected and does not replace v194 LTS.

V195 inherits v194 and turns on a source-grounded self-reference gate for temporal selected-context expansion. The gate is clean and general: it uses only question text, speaker role, selected row text, and source-local term coverage. It does not use labels, judge output, benchmark tags, sample ids, row ids, test feedback, gold answers, or sample-level rules.

## Why It Was Tried

V190 previously showed that this gate can reduce wrong-speaker and context-noise risk, but it lost the Nate temporal gain before v194's `mention_time_fallback` existed. V195 retests the same general gate on top of v194.

## Full Diff

| Benchmark | v195 vs v194 prompt diff | v195 vs v194 answer diff | Cache | Result |
|---|---:|---:|---:|---|
| LongMemEval-S full | `0/500` | `0/500` | inherited via cache | no behavior change |
| LoCoMo non-adversarial full | `324/1540` | `105/1540` | `1435/105/105` answer cache | needs changed-answer judge |

LoCoMo selected-context did become cheaper and narrower:

| Metric | v194 | v195 |
|---|---:|---:|
| selected-context applied | `1536/1540` | `1398/1540` |
| materialized rows | `8540` | `7572` |
| avg materialized rows | `5.545` | `4.917` |
| avg query tokens | `6089.272` | `5996.258` |

## Changed-Answer Judge

Dual `deepseek-v4-flash` judge on the 105 changed LoCoMo answers:

| Version | strict correct | lenient correct |
|---|---:|---:|
| v194 changed subset | `76/105` | `79/105` |
| v195 changed subset | `67/105` | `68/105` |
| Delta | `-9` | `-11` |

Derived LoCoMo full if v195 replaced v194:

| Metric | Value |
|---|---:|
| strict correct | `1213/1540` |
| lenient correct | `1250/1540` |
| strict accuracy | `0.787662` |
| lenient accuracy | `0.811688` |

This is worse than v194 (`1222/1540`, `1261/1540`; strict/lenient `0.793506/0.818831`), so v195 is not LTS.

## Diagnosis

The gate reduces context noise, but hard blocking temporal selected-context removes useful local evidence on too many LoCoMo temporal rows. The correct lesson is not to use this as a prompt-time hard filter. The next safer direction is trace-only selected-context risk auditing or a much narrower conflict-aware activation that can flag weak/wrong-speaker local context without removing broadly useful neighboring evidence.

## Artifacts

- Config: `configs/stage1_temporal_source_grounded_selected_context_v195_seeded_qwen36_no_think_build4k_cached.json`
- Method commit: `2da314b981e7ab04ee5c6808ff971a1c78842791`
- Activation probe: `experiments/diagnostic/stage1_temporal_source_grounded_selected_context_v195_activation_probe/`
- LME full: `experiments/diagnostic/stage1_temporal_source_grounded_selected_context_v195_lme_s_full/`
- LoCoMo full: `experiments/diagnostic/stage1_temporal_source_grounded_selected_context_v195_locomo_nonadv_full/`
- Changed subset outputs: `outputs/diagnostic/stage1_temporal_source_grounded_selected_context_v195_changed_vs_v194/`
- Judge comparison: `experiments/diagnostic/stage1_temporal_source_grounded_selected_context_v195_changed_vs_v194/paired_judge_comparison_vs_v194.json`
