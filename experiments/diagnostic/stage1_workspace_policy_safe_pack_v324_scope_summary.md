# stage1_workspace_policy_safe_pack_v324 scope summary

## Purpose

V324 keeps the v288 LTS global evidence/context budgets and state/value guide behavior, while consuming build-owned `memory_workspace_policy_v1` only for selected-context pack control. It is a safety correction after v323 showed that aggressive global context pressure can reduce query tokens but regress LongMemEval-S full accuracy.

The intended system move is narrow: query no longer owns selected-context rows/window/chars; build memory policy emits that pack contract. Final answer evidence remains raw Memory rows.

## Config

- Config: `configs/stage1_workspace_policy_safe_pack_v324_seeded_qwen36_no_think_build4k_cached.json`
- Based on v288 LTS, not v323 pressure budgets.
- Keeps v288 global `max_evidence_items=60`, `max_evidence_chars=18000`, temporal `40/18000`, context budget `60/22000`, and state/value guide behavior.
- Adds `retrieval.workspace_policy_context.enabled=true`.
- Removes selected-context `max_rows`, `max_neighbor_chars`, `max_center_chars`, `window_before`, and `window_after` from query config, route override, and long-context granularity profile so these come from build-owned `memory_workspace_policy.pressure_policy`.
- Does not enable `compiler.context_pressure`.

Clean note: no gold answer, judge output, benchmark label, sample id, test feedback, or sample-level rule is used by prediction, retrieval, compiler, answer, verifier, memory build, or cache construction.

## Diagnostics

| Scope | avg build/query tokens | workspace policy context | selected context | context pressure | answer diff vs v288 | cache |
|---|---:|---:|---:|---:|---:|---:|
| LME smoke5 | `92386.0 / 5567.2` | `5/5` | `0/5` | `0/5` | `0/5` | `5/0` hit/miss |
| LME op21 | `87656.19 / 5611.38` | `21/21` | `0/21` | `0/21` | `0/21` | `21/0` hit/miss |
| LoCoMo smoke5 | `45868.0 / 5520.8` | `5/5` | `5/5`, avg rows `4.0` | `0/5` | `2/5` | `0/5` hit/miss |

Compared with v288:

- LME smoke5: prompt/evidence/route/answer/query-token diff all `0/5`.
- LME op21: prompt/evidence/route/answer/query-token diff all `0/21`.
- LoCoMo smoke5: prompt/evidence/query-token diff `5/5`, answer diff `2/5`, avg query tokens `6048.2 -> 5520.8`, avg context chars `17405.0 -> 15788.8`.

Compared with v323:

- V324 removes aggressive context pressure: LME smoke context pressure `2/5 -> 0/5`; LME op21 `14/21 -> 0/21`.
- It gives back some tokens relative to v323 but restores the v288-safe LME evidence surface on the checked scopes.

## Changed-Answer Judge

LoCoMo smoke5 changed-answer dual DeepSeek flash judge was run only for the 2 answers changed vs v288.

| Prediction set | strict | lenient | Judge outputs |
|---|---:|---:|---|
| old v288 | `2/2` | `2/2` | `experiments/diagnostic/stage1_workspace_policy_safe_pack_v324_locomo_smoke5_changed_vs_v288/old_v288_dual_judge.json` |
| new v324 | `2/2` | `2/2` | `experiments/diagnostic/stage1_workspace_policy_safe_pack_v324_locomo_smoke5_changed_vs_v288/new_v324_dual_judge.json` |

## Decision

V324 is a safer candidate than v323, not a new LTS yet. It keeps the system improvement that selected-context packing is build-policy-owned, avoids v323's broad evidence compression, and shows no regression on LME smoke/op or LoCoMo smoke changed-answer judge.

Next step: run LME full diff against v288 to verify only selected-context cases can change, then decide whether LoCoMo full prediction/judge is worth the cost.
