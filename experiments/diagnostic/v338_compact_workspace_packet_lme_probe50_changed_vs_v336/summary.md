# v338_compact_workspace_packet_lme_probe50_changed_vs_v336

## Purpose

Offline changed-answer judge comparing v338 against v336 on LongMemEval probe50 rows whose final answers changed.

## Scope

- benchmark: longmemeval
- changed samples: 7 / 50
- old predictions: `experiments/diagnostic/v338_compact_workspace_packet_lme_probe50_changed_vs_v336/old_v336_changed_predictions.jsonl`
- new predictions: `experiments/diagnostic/v338_compact_workspace_packet_lme_probe50_changed_vs_v336/new_v338_changed_predictions.jsonl`
- labels: `experiments/diagnostic/v338_compact_workspace_packet_lme_probe50_changed_vs_v336/changed_labels.jsonl`
- judge: `deepseek-v4-flash`, two independent temperature 0 runs, default thinking

## Metrics

- old v336 changed subset: strict `4/7`, lenient `4/7`
- new v338 changed subset: strict `5/7`, lenient `5/7`
- strict delta on changed subset: `+1`
- lenient delta on changed subset: `+1`
- v336 probe50 avg query tokens: `5555.76`
- v338 probe50 avg query tokens: `5395.32`
- avg query token delta: `-160.44`

## Diagnosis

v338 keeps the build-owned workspace replacement idea from v337 but uses a compact packet: slot/type/focus/decision/status/hint/source only, with packet values labeled as activation hints rather than final facts. This fixes v337's token increase and improves LongMemEval changed-answer accuracy on the sports-store location case without observed changed-subset regressions.

## Decision

Keep v338 as the current build-owned workspace packet candidate. Do not promote to LTS from probe50 alone; validate the LoCoMo mixed result and tighten slot-conservative behavior before any full run.

## Clean Notes

Judge outputs are offline-only and are not used by prediction, retrieval, memory build, answer generation, verifier logic, or caches.
