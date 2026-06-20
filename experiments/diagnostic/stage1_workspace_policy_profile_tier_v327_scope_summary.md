# stage1_workspace_policy_profile_tier_v327_scope_summary

## Purpose

Move selected-context organization from fixed query constants into build-owned workspace policy profile tiers.

## Change

- `compact_source_coverage`: temporal/question-reference profile, rows `4`, neighbor chars `140`, center chars `260`, window `1/1`.
- `balanced_source_coverage`: default fact/list/profile profile, rows `6`, neighbor chars `180`, center chars `320`, window `1/2`.
- Retrieval selects the profile from `memory_workspace_policy_v1` by route/settings.
- Existing tighter positive selected-context settings still cannot be widened.
- Final answer evidence remains raw Memory rows.

## Smoke Result

| Benchmark | n | avg query | Answer diff vs v288 |
|---|---:|---:|---:|
| LongMemEval-S smoke5 | 5 | `5567.2` | `0/5` |
| LoCoMo smoke5 | 5 | `5664.8` | `0/5` |

LoCoMo smoke profile selection:

| Route | Profile | Rows/chars/window |
|---|---|---|
| temporal_lookup | `compact_source_coverage` | `4 / 140 / 260 / 1/1` |
| fact_lookup | `balanced_source_coverage` | `6 / 180 / 320 / 1/2` |

## Decision

V327 passes smoke and is worth larger validation. Next run LoCoMo probe/full and LongMemEval-S full diff before any LTS decision.
