# v338_compact_workspace_packet_locomo_probe50_changed_vs_v336

## Purpose

Offline changed-answer judge comparing v338 against v336 on LoCoMo non-adversarial probe50 rows whose final answers changed.

## Scope

- benchmark: locomo
- changed samples: 23 / 50
- old predictions: `experiments/diagnostic/v338_compact_workspace_packet_locomo_probe50_changed_vs_v336/old_v336_changed_predictions.jsonl`
- new predictions: `experiments/diagnostic/v338_compact_workspace_packet_locomo_probe50_changed_vs_v336/new_v338_changed_predictions.jsonl`
- labels: `experiments/diagnostic/v338_compact_workspace_packet_locomo_probe50_changed_vs_v336/changed_labels.jsonl`
- judge: `deepseek-v4-flash`, two independent temperature 0 runs, default thinking

## Metrics

- old v336 changed subset: strict `20/23`, lenient `22/23`
- new v338 changed subset: strict `21/23`, lenient `21/23`
- strict delta on changed subset: `+1`
- lenient delta on changed subset: `-1`
- v336 probe50 avg query tokens: `5700.88`
- v338 probe50 avg query tokens: `5575.84`
- avg query token delta: `-125.04`

## Diagnosis

v338 reduces query tokens and improves strict accuracy on the changed subset, mainly by making career-path and grounded counterfactual answers more slot-complete. It still has two important risks: a relationship-status question abstains despite source support, and a family-activities list over-expands to unsupported or less central details, causing a lenient regression.

## Decision

Keep v338 as a candidate but do not promote to LTS. The next version should keep compact workspace packets but add general slot-conservative controls for relationship/status facts and list answers before any full run.

## Clean Notes

Judge outputs are offline-only and are not used by prediction, retrieval, memory build, answer generation, verifier logic, or caches. The LoCoMo prediction run was completed after the general long-integer JSON parser fix; the prompt/config remained v338.
