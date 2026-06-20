# stage1_workspace_policy_profile_cap_v326_scope_summary

## Purpose

Test whether v325's build-owned selected-context pack can be consumed as a cap rather than an unconditional override.

## Change

- Added `selected_context_pack_policy=profile_cap_no_widen`.
- Added `selected_context_no_widen_existing_profile=true`.
- Retrieval applies numeric selected-context policy values only when they do not widen an existing positive profile value.
- Final answer evidence remains raw Memory rows.

## Smoke Result

| Benchmark | n | avg query | Answer diff |
|---|---:|---:|---:|
| LongMemEval-S smoke5 vs v288 | 5 | `5567.2` | `0/5` |
| LoCoMo smoke5 vs v288 | 5 | `5659.6` | `2/5` |
| LoCoMo smoke5 vs v325 | 5 | `5659.6` vs `5807.6` | `1/5` |

## Diagnosis

V326 reduces LoCoMo smoke query tokens below v325, but it worsens the small smoke answer diff relative to v288. The reason is that v325/v326 configs no longer carry the old query-side rows/chars profile, so no-widen only preserves `window_after=1`; it does not recover the old rows/chars behavior.

This confirms the next step: source-pressure-aware policy must use explicit build-owned profile tiers or source coverage signals. A cap-only guard over missing query config defaults is not enough.

## Decision

Do not run v326 full and do not promote to LTS. Keep the no-widen guard as a useful safety primitive, but build v327 around explicit source-pressure/profile tiers.
