# stage1_question_gated_selected_context_v157 diagnostic

## Purpose

V157 tests a safer replacement for the long-turn selected-context blanket disable.

Compared with v156, long-profile selected context also requires a local/deictic reference in the question itself. The goal is to avoid expanding adjacent turns for generic recommendation/current-state questions merely because retrieved evidence rows contain words like "this" or "that".

Prediction remains clean: no gold answer, judge output, benchmark label, sample id, row index, test feedback, or sample-level shortcut is used by retrieval, compiler, answer, repair, or cache construction.

## Config

- Config: `configs/stage1_question_gated_selected_context_v157_qwen36_no_think_build4k_cached.json`
- Parent: v154 LTS, with v156 selected-context idea narrowed by `require_question_reference=true`
- Code change: `retrieval.selected_context.require_question_reference` support in `src/memory/pipeline.py`
- Tests: selected-context question-reference gate and granularity profile tests passed.

## LongMemEval-S Full Prediction

| Metric | v154 | v157 |
|---|---:|---:|
| selected-context applied | `0/500` | `6/500` |
| selected materialized rows avg | `0.000` | `0.048` |
| avg context chars | `19769.610` | `19776.350` |
| avg query tokens | `6179.012` | `6202.070` |
| answer changed | - | `5/500` |

Route scope:

| Route | n | blocked by question gate | selected applied |
|---|---:|---:|---:|
| `current_state` | `22` | `20` | `2` |
| `profile_preference` | `15` | `11` | `4` |
| other routes | `463` | `0` | `0` |

## Offline Paired Judge

Changed-answer subset: `5` LME records.

Dual `deepseek-v4-flash` judge, temperature `0`, default thinking:

| Subset | strict | lenient |
|---|---:|---:|
| v154 changed keys | `3/5` | `4/5` |
| v157 changed keys | `2/5` | `4/5` |
| paired delta | `-1` | `0` |

V157 mostly fixes the v156 failure mode, but it still has a strict regression on one recommendation case. The issue is that the first question-reference pattern treated relative-clause "that" as a local/deictic reference, e.g. "accessories that would complement my current photography setup". That is too broad.

## Decision

Reject v157 as LTS. Current LTS remains v154.

Keep the direction: question-level gating is the right extra safety layer, but the reference detector must be narrower before this can replace the long-turn blanket disable. Next step: refine the gate to avoid bare relative "that" and only trigger on clearer local-reference phrases such as "what else", "that one", "those", "previously", "mentioned", or "above".

## Outputs

- LME predictions: `outputs/diagnostic/stage1_question_gated_selected_context_v157_lme_s_full/predictions.jsonl`
- LME traces: `outputs/diagnostic/stage1_question_gated_selected_context_v157_lme_s_full/traces.jsonl`
- LME metrics: `experiments/diagnostic/stage1_question_gated_selected_context_v157_lme_s_full/metrics.json`
- Changed subset and paired judge: `outputs/diagnostic/stage1_question_gated_selected_context_v157_lme_changed_vs_v154/`
