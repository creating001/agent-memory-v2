# stage1_narrow_question_gated_selected_context_v158 LTS summary

## Purpose

V158 promotes the safer selected-context policy from the v156/v157 diagnostics.

It inherits v154 LTS and keeps build memory, retrieval top-k, compiler, answer prompt, lifecycle-ledger repair, and source-grounded guard unchanged. The only method change is in long-turn selected context:

- v154: `long_turn_precision.selected_context.enabled=false`
- v156: route + evidence-row anaphora enabled, but too noisy
- v157: added question-level reference gate, but bare relative-clause `that` was too broad
- v158: keeps question-level gate and removes bare `that`; only clearer local references trigger long-turn adjacent context

This reduces #3 selected-context long/short-turn heuristic risk without using gold answer, judge output, benchmark label, sample id, row index, test feedback, or sample-level shortcuts.

## Config

- Config: `configs/stage1_narrow_question_gated_selected_context_v158_qwen36_no_think_build4k_cached.json`
- Parent LTS: `configs/stage1_current_state_lifecycle_ledger_v154_qwen36_no_think_build4k_cached.json`
- Code change: `retrieval.selected_context.require_question_reference` plus narrower question-reference pattern
- Tests: selected-context question-reference, granularity profile, and route override unit tests passed
- Prediction commit recorded by runs: `572d9e6`
- Dirty state in run manifests: expected; v158 source/config/diagnostic files were uncommitted during prediction

## LongMemEval-S Full

| Metric | v154 | v158 |
|---|---:|---:|
| selected-context applied | `0/500` | `3/500` |
| selected materialized rows avg | `0.000` | `0.024` |
| avg context chars | `19769.610` | `19772.962` |
| avg query tokens | `6179.012` | `6200.690` |
| answer changed | - | `2/500` |

Route scope:

| Route | n | blocked by question gate | selected applied |
|---|---:|---:|---:|
| `current_state` | `22` | `21` | `1` |
| `profile_preference` | `15` | `13` | `2` |
| other routes | `463` | `0` | `0` |

Changed-answer paired dual judge on the `2` changed LME rows:

| Subset | strict | lenient |
|---|---:|---:|
| v154 changed keys | `2/2` | `2/2` |
| v158 changed keys | `2/2` | `2/2` |
| paired delta | `0` | `0` |

Therefore v158 inherits v154 LME full accuracy: strict/lenient `411/500 = 0.822000` and `417/500 = 0.834000`.

## LoCoMo Non-Adversarial Full

LoCoMo prediction is answer-identical to v154:

- answer diff: `0/1540`
- selected-context applied: `1536/1540`
- avg query tokens: `6047.909`

Therefore v158 inherits v154 LoCoMo full accuracy: strict/lenient `1216/1540 = 0.789610` and `1256/1540 = 0.815584`.

## Decision

Promote v158 to current local LTS.

Reasoning:

- Risk reduction: long-turn selected context is no longer a blanket profile disable; it is a question-gated local context mechanism.
- Clean/general: the gate uses only question text, question-derived route, raw same-session turns, and visible metadata.
- Performance: LME changed-answer paired judge is strict/lenient neutral, and LoCoMo answers are unchanged.
- Cost: LME avg query tokens increases by about `21.678` tokens versus v154 and remains under the 8K hard budget; LoCoMo cost is unchanged.

Remaining risks:

- #1 granularity/profile is still partly average-turn-profile based.
- #2 top-k/context noise and route-aware context organization still need a coverage-preserving solution.
- #5 lifecycle/state management is improved by v154's ledger, but typed memory lifecycle/query-time management is not complete.

## Outputs

- LME predictions: `outputs/diagnostic/stage1_narrow_question_gated_selected_context_v158_lme_s_full/predictions.jsonl`
- LME traces: `outputs/diagnostic/stage1_narrow_question_gated_selected_context_v158_lme_s_full/traces.jsonl`
- LME metrics: `experiments/diagnostic/stage1_narrow_question_gated_selected_context_v158_lme_s_full/metrics.json`
- LoCoMo predictions: `outputs/diagnostic/stage1_narrow_question_gated_selected_context_v158_locomo_nonadv_full/predictions.jsonl`
- LoCoMo traces: `outputs/diagnostic/stage1_narrow_question_gated_selected_context_v158_locomo_nonadv_full/traces.jsonl`
- LoCoMo metrics: `experiments/diagnostic/stage1_narrow_question_gated_selected_context_v158_locomo_nonadv_full/metrics.json`
- Changed subset and paired judge: `outputs/diagnostic/stage1_narrow_question_gated_selected_context_v158_lme_changed_vs_v154/`
