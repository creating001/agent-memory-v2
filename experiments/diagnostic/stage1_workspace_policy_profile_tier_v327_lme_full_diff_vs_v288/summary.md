# stage1_workspace_policy_profile_tier_v327_lme_full_diff_vs_v288

## Purpose

Audit v327 build-owned selected-context profile tiers against the v288 LTS on LongMemEval-S full.

## Runs

- baseline: `outputs/diagnostic/stage1_memory_object_index_v288_lme_full`
- candidate: `outputs/diagnostic/stage1_workspace_policy_profile_tier_v327_lme_full`
- comparison: `outputs/diagnostic/stage1_workspace_policy_profile_tier_v327_lme_full_diff_vs_v288/comparison.json`
- candidate git commit: `cd35fcd7f0cc5525bb103ef223e73b5b83ad1d95`
- candidate dirty at run start: `False`

## Result

- shared samples: 500
- answer diff: 1
- prompt diff: 3
- evidence diff: 0
- route diff: 0
- v288 avg query tokens: `6455.588`
- v327 avg query tokens: `6454.482`
- v327 selected-context applications: `3/500`
- v327 workspace profile: `compact_source_coverage` on `500/500`

## Decision

Requires changed-answer judge for the single changed answer before LTS decision.
