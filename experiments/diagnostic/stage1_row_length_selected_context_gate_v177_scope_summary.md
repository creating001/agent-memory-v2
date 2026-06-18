# V177 Row-Length Selected-Context Gate Rejected

## Decision

Do not promote v177. Current LTS remains v176.

v177 is a clean/general attempt to reduce #1/#3 risk by moving selected-context
question-reference gating from a whole-corpus granularity profile toward a
row-local length gate. The mechanism is source-backed and uses only question
text, route, raw turn text length, and same-session neighbors, but the LME
result shows the gate is still too broad.

## Method

- Parent LTS: v176 (`b38e6ad`).
- Algorithm commit: `94eb2a7`.
- Config: `configs/stage1_row_length_selected_context_gate_v177_qwen36_no_think_build4k_cached.json`.
- Change:
  - add `require_question_reference_min_center_chars` to selected-context;
  - short center turns may still materialize local same-session context when
    the center row itself has anaphora;
  - longer center turns require local-reference language in the question before
    neighbor materialization.

## LME Result

| Item | v176 | v177 |
|---|---:|---:|
| selected-context applied | `3/500` | `37/500` |
| answer diff vs v176 | - | `15/500` |
| avg query tokens | `6291.590` | `6318.580` |
| changed-answer strict/lenient | `12/15` | `7/15` |

Paired-delta patched LME full would drop from v176 `417/500` strict and
`423/500` lenient to approximately `412/500` strict and `418/500` lenient.
Because LME changed-answer dual judge is negative and query tokens also
increase, LoCoMo full was not run.

## Badcase Pattern

The row-local gate still expands too many long-turn profile/current rows that
contain center-row anaphora but where the question does not actually need local
dialogue expansion. This introduces extra context and causes the answerer to
over-abstain or drift on profile/advice/current-state questions.

## Next Step

- Do not broaden selected-context by only checking center-row anaphora.
- For #3, require stronger question-side local-reference or build a compact
  source-backed candidate map that does not inject neighbor turns into Memory
  Context by default.
- For #2, continue toward coverage-preserving organization/grouping rather than
  row expansion or hard pruning.

## Artifacts

- LME full run: `experiments/diagnostic/stage1_row_length_selected_context_gate_v177_lme_s_full/`
- Changed-answer judge: `experiments/diagnostic/stage1_row_length_selected_context_gate_v177_changed_vs_v176/`
- Paired comparison: `experiments/diagnostic/stage1_row_length_selected_context_gate_v177_changed_vs_v176/paired_judge_comparison_vs_v176.json`
- Predictions/traces: `outputs/diagnostic/stage1_row_length_selected_context_gate_v177_lme_s_full/`
- Changed subset: `outputs/diagnostic/stage1_row_length_selected_context_gate_v177_changed_vs_v176/`
