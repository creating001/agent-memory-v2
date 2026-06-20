# stage1_workspace_policy_pack_v323 scope summary

## Purpose

V323 extends `memory_workspace_policy_v1` from selected-context format control to selected-context pack control. The build-owned policy now emits max rows, neighbor chars, center chars, and window size; query-time selected context executes that policy instead of carrying duplicated pack constants.

This directly targets risk 1 and risk 5: memory acts more like a system-level context manager, and query token reduction is handled through a general workspace policy rather than benchmark rules.

## Config

- Config: `configs/stage1_workspace_policy_pack_v323_seeded_qwen36_no_think_build4k_cached.json`
- Based on v322.
- New pressure policy keys: `selected_context_max_rows=4`, `selected_context_max_neighbor_chars=140`, `selected_context_max_center_chars=260`, `selected_context_window_before=1`, `selected_context_window_after=1`.
- The same selected-context pack keys are removed from query config base, route override, and long-context granularity profile.
- Answer cache uses v323 namespace/path and was seeded from v322 prediction traces only. Changed prompts miss the cache and are answered fresh; unchanged prompts reuse cached answers.

Clean note: no gold answer, judge output, benchmark label, sample id, test feedback, or sample-level rule is used by prediction, retrieval, compiler, answer, verifier, memory build, or cache construction. Final answer evidence remains raw Memory rows.

## Diagnostics

| Scope | avg build/query tokens | avg context chars | workspace policy context | selected context | context pressure | consistency risk | cache |
|---|---:|---:|---:|---:|---:|---:|---:|
| LME smoke5 | `92386.0 / 5417.2` | `16902.2` | `5/5` applied | `0/5` applied | `2/5` | `0` samples / `0` flags | `5/0` hit/miss |
| LoCoMo smoke5 | `45868.0 / 5355.2` | `15456.2` | `5/5` applied | `5/5` applied, avg rows `4.0` | `0/5` | `2` samples / `4` flags | `2/3` hit/miss |
| LME op21 | `87656.19 / 5376.67` | `17263.71` | `21/21` applied | `0/21` applied | `14/21` | `1` sample / `2` flags | `21/0` hit/miss |

Compared with v322:

- LME smoke5: prompt/evidence/source-order/route/answer diff all `0/5`; query tokens unchanged.
- LME op21: prompt/evidence/source-order/route/answer diff all `0/21`; query tokens unchanged.
- LoCoMo smoke5: prompt/evidence diff `3/5`, source-order/route diff `0/5`, answer diff `2/5`; avg query tokens `5596.2 -> 5355.2`, avg context chars `16455.4 -> 15456.2`, avg selected-context rows `5.2 -> 4.0`.

Changed LoCoMo answers:

- `628d9b1436fa405b91ee2820`: v322 `Counseling and mental health (specifically working with trans people)` -> v323 `Counseling and mental health`.
- `0ef0216553b4eeff9be57e45`: v322 `Caroline is a trans woman who has transitioned and is part of the transgender community.` -> v323 `Caroline is a transgender woman.`

## Changed-Answer Judge

Changed-answer dual DeepSeek flash judge was run only for the 2 changed LoCoMo answers.

| Prediction set | strict | lenient | Judge outputs |
|---|---:|---:|---|
| v322 old | `2/2` | `2/2` | `experiments/diagnostic/stage1_workspace_policy_pack_v323_changed_vs_v322/old_v322_dual_judge.json` |
| v323 new | `2/2` | `2/2` | `experiments/diagnostic/stage1_workspace_policy_pack_v323_changed_vs_v322/new_v323_dual_judge.json` |

Judge temperature is `0`; both runs use `deepseek-v4-flash` twice with default thinking. Labels and judge outputs are offline evaluation only and are not used by prediction or cache construction.

## Decision

V323 is a stronger candidate than v322 for the current goal: it keeps LME behavior unchanged, reduces LoCoMo smoke query tokens by about `241` tokens/sample, and has no changed-answer judge regression on the changed LoCoMo subset.

It is still not promoted to LTS because only smoke/op diagnostics have been run. Next step is a broader/full diff against the current candidate/LTS path, then changed-answer judge only where answers change.

Version commit: this local commit (`method: add v323 workspace policy pack`).
