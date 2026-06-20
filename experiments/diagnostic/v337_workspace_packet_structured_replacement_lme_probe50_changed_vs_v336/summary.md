# v337_workspace_packet_structured_replacement_lme_probe50_changed_vs_v336

## Purpose

Offline changed-answer judge comparing v337 against v336 on LongMemEval probe50 rows whose final answers changed.

## Scope

- benchmark: longmemeval
- changed samples: 9 / 50
- old predictions: `experiments/diagnostic/v337_workspace_packet_structured_replacement_lme_probe50_changed_vs_v336/old_v336_changed_predictions.jsonl`
- new predictions: `experiments/diagnostic/v337_workspace_packet_structured_replacement_lme_probe50_changed_vs_v336/new_v337_changed_predictions.jsonl`
- labels: `experiments/diagnostic/v337_workspace_packet_structured_replacement_lme_probe50_changed_vs_v336/changed_labels.jsonl`
- judge: `deepseek-v4-flash`, two independent temperature 0 runs, default thinking

## Metrics

- old v336 changed subset: strict `6/9`, lenient `6/9`
- new v337 changed subset: strict `6/9`, lenient `6/9`
- strict delta on changed subset: `0`
- lenient delta on changed subset: `0`
- v336 probe50 avg query tokens: `5555.76`
- v337 probe50 avg query tokens: `5724.16`
- avg query token delta: `+168.40`

## Diagnosis

v337 is a useful negative lesson. It proves that a build-owned Working Memory Packet can replace Structured Evidence Guide for fact/profile/current_state routes without changing raw Memory Context, but the existing packet is too verbose. It increases prompt size and reintroduces a slot-completeness failure on the previous-occupation case by dropping the workplace qualifier.

## Decision

Do not promote v337. Keep the route-level `structured_guide` override mechanism because it is a clean control surface, but replace the verbose Working Memory Packet with a shorter workspace packet before testing this direction again.

## Clean Notes

Judge outputs are offline-only and are not used by prediction, retrieval, memory build, answer generation, verifier logic, or caches.
