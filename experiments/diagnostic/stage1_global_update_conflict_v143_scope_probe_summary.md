# V143 Global Update-Conflict Scope Probe

## Purpose

Check whether the existing `update_conflict_guide` can be promoted from long-turn-only profile logic into a general #5 memory-management candidate.

The probe used a temporary config derived from v142:

- top-level `compiler.update_conflict_guide=true`
- `update_conflict_guide_information_needs=["current_state","fact_lookup","profile_preference"]`
- answer mode changed to `null_answerer`

No answer LLM calls or judge calls were made. This is a compile/scope diagnostic only.

## Results

| Benchmark | update/conflict guide applied | state guide applied | Decision |
|---|---:|---:|---|
| LongMemEval-S full | `44/500` | `37/500` | same update/conflict scope already seen in v142 long-turn profile; no new behavior |
| LoCoMo non-adversarial full | `0/1540` | `50/1540` | no-op for the short-turn LoCoMo side |

Route breakdown:

- LME update/conflict guide: `fact_lookup=32`, `current_state=12`.
- LoCoMo update/conflict guide: none.
- LoCoMo state guide remains `current_state=4`, `profile_preference=46`.

## Decision

Do not create a formal v143 config from this probe. It is not an algorithmic improvement because it adds no LoCoMo behavior and does not extend LME beyond the already active v142 long-turn profile path.

The next real #5 version needs new logic for conflict/as-of state selection or version-chain retrieval. Simply turning on the old update/conflict prompt globally is not enough.

## Clean Boundary

- Inputs are clean prediction JSONL files.
- The probe uses no gold answers, judge outputs, benchmark labels, sample ids, row indices, or test feedback.
- Generated answers are placeholder null-answerer outputs; accuracy is meaningless.

## Artifacts

- LME scope probe: `experiments/diagnostic/stage1_global_update_conflict_v143_lme_scope_probe/`
- LoCoMo scope probe: `experiments/diagnostic/stage1_global_update_conflict_v143_locomo_scope_probe/`
- Prediction traces: `outputs/diagnostic/stage1_global_update_conflict_v143_lme_scope_probe/traces.jsonl`, `outputs/diagnostic/stage1_global_update_conflict_v143_locomo_scope_probe/traces.jsonl`
