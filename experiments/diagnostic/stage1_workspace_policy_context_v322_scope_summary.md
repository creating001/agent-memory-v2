# stage1_workspace_policy_context_v322 scope summary

## Purpose

V322 moves selected-context pressure decisions from duplicated query config into the build-owned `memory_workspace_policy_v1`. The goal is to reduce risk 1/5: memory becomes a system-level workspace controller, and query no longer owns ad hoc compact/timestamp policy for selected context.

## Config

- Config: `configs/stage1_workspace_policy_context_v322_seeded_qwen36_no_think_build4k_cached.json`
- Based on v321.
- `retrieval.workspace_policy_context.enabled=true`.
- `retrieval.selected_context.context_format` and `timestamp_policy` are removed from base, route override, and long-context granularity profile. Runtime selected-context `compact` and `center_only` now come from `memory_workspace_policy.pressure_policy`.
- `compiler.context_pressure` remains unchanged: low-headroom-only, `36` rows / `16000` chars.
- Answer cache intentionally reuses v321 namespace/path for prompt-equivalent diagnostics; unchanged prompts should not trigger fresh answer sampling.

Clean note: no gold answer, judge output, benchmark label, sample id, test feedback, or sample-level rule is used. Final answer evidence remains raw Memory rows.

## Diagnostics

| Scope | avg build/query tokens | workspace policy context | selected context | context pressure | consistency risk | cache |
|---|---:|---:|---:|---:|---:|---:|
| LME smoke5 | `92386.0 / 5417.2` | `5/5` applied | `0/5` applied | `2/5` | `0` samples / `0` flags | `5/0` hit/miss |
| LoCoMo smoke5 | `45868.0 / 5596.2` | `5/5` applied | `5/5` applied | `0/5` | `2` samples / `4` flags | `5/0` hit/miss |
| LME op21 | `87656.19 / 5376.67` | `21/21` applied | `0/21` applied | `14/21` | `1` sample / `2` flags | `21/0` hit/miss |

Output paths:

- `outputs/diagnostic/stage1_workspace_policy_context_v322_lme_smoke5/`
- `outputs/diagnostic/stage1_workspace_policy_context_v322_locomo_smoke5/`
- `outputs/diagnostic/stage1_workspace_policy_context_v322_lme_op_smoke21/`

## Diff vs v321

Prompt/evidence/route/source-order diff:

- LME smoke5: prompt `0/5`, evidence `0/5`, source order `0/5`, route `0/5`.
- LoCoMo smoke5: prompt `0/5`, evidence `0/5`, source order `0/5`, route `0/5`.
- LME op21: prompt `0/21`, evidence `0/21`, source order `0/21`, route `0/21`.

Answer diff:

- LoCoMo smoke5: `0/5`.
- LME op21: `0/21`.
- LME smoke5: `1/5`, only `ea4e66b0d90b6834b4168cfe`. This is a cache timing artifact: v321 smoke had `The provided information is not enough.`, while v321 op21, v322 smoke, and v322 op21 all have `email inbox` for the identical prompt/evidence. The v321 changed-answer judge had already marked the old/new variants for this record wrong, so this is not treated as a v322 algorithm regression.

No changed-answer judge was run for v322 because the behavior-affecting prompt/evidence surface is unchanged; the only LME smoke answer difference is inherited cache nondeterminism on an already-known wrong->wrong case.

## Decision

V322 is a system-risk reduction candidate, not a new LTS yet. It reduces query ownership of selected-context pressure policy and makes `memory_workspace_policy_v1` an actual runtime controller. It does not by itself improve answer accuracy or solve the `ea4e...` wrong->wrong badcase.

Next step: use the same workspace policy surface to reduce query tokens without adding benchmark-specific rules. The most conservative next target is to make policy drive low-headroom context packing or retire a redundant query compatibility layer that is now covered by workspace policy.

Version commit: this local commit (`method: add v322 workspace policy context`).
