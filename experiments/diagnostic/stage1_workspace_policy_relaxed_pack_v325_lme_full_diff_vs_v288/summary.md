# stage1_workspace_policy_relaxed_pack_v325_lme_full_diff_vs_v288

## Purpose

Audit v325 relaxed build-owned workspace policy pack against the v288 LTS on LongMemEval-S full.

## Runs

- baseline: `outputs/diagnostic/stage1_memory_object_index_v288_lme_full`
- candidate: `outputs/diagnostic/stage1_workspace_policy_relaxed_pack_v325_lme_full`
- comparison: `outputs/diagnostic/stage1_workspace_policy_relaxed_pack_v325_lme_full_diff_vs_v288/comparison.json`
- candidate git commit: `b3d75235cb16183e28dead4122078dde454b81c1`
- candidate dirty at run start: `False`

## Result

- shared samples: 500
- answer diff: 0
- prompt diff: 3
- evidence diff: 2
- route diff: 0
- v288 avg build/query tokens: 85393.566 / 6455.588
- v325 avg build/query tokens: 85393.566 / 6454.864
- v325 selected-context applications: 3 / 500
- v325 workspace policy applications: 500 / 500

## Diagnosis

v325 does not change any LongMemEval-S full answers relative to v288, so it inherits the v288 full DeepSeek dual flash judge accuracy on this benchmark: strict 0.834000, lenient 0.846000.

The relaxed pack behaves as intended: build-time `memory_workspace_policy_v1` owns the selected-context pack constants, while query config does not hard-code rows/chars/window values. LongMemEval-S selected-context activation is rare, so the token effect is intentionally small.

## Decision

LongMemEval-S full passes the v325 gate. LoCoMo full remains required before any LTS promotion decision.
