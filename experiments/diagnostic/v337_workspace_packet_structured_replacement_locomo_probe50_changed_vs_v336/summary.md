# v337_workspace_packet_structured_replacement_locomo_probe50_changed_vs_v336

## Purpose

Offline changed-answer judge comparing v337 against v336 on LoCoMo non-adversarial probe50 rows whose final answers changed.

## Scope

- benchmark: locomo
- changed samples: 23 / 50
- old predictions: `experiments/diagnostic/v337_workspace_packet_structured_replacement_locomo_probe50_changed_vs_v336/old_v336_changed_predictions.jsonl`
- new predictions: `experiments/diagnostic/v337_workspace_packet_structured_replacement_locomo_probe50_changed_vs_v336/new_v337_changed_predictions.jsonl`
- labels: `experiments/diagnostic/v337_workspace_packet_structured_replacement_locomo_probe50_changed_vs_v336/changed_labels.jsonl`
- judge: `deepseek-v4-flash`, two independent temperature 0 runs, default thinking

## Metrics

- old v336 changed subset: strict `20/23`, lenient `21/23`
- new v337 changed subset: strict `19/23`, lenient `20/23`
- strict delta on changed subset: `-1`
- lenient delta on changed subset: `-1`
- v336 probe50 avg query tokens: `5700.88`
- v337 probe50 avg query tokens: `5761.54`
- avg query token delta: `+60.66`

## Diagnosis

v337 replaces the fact/profile/current_state Structured Evidence Guide with the build-owned `memory_system_state` Working Memory Packet. The replacement increases query tokens and loses one LoCoMo relationship/status case where the packet over-activates a related friendship fact instead of the requested relationship-status slot.

## Decision

Do not promote v337. The build-owned workspace replacement direction remains valid, but the packet must become shorter and more slot-conservative before it can replace legacy guide text.

## Clean Notes

Judge outputs are offline-only and are not used by prediction, retrieval, memory build, answer generation, verifier logic, or caches.
