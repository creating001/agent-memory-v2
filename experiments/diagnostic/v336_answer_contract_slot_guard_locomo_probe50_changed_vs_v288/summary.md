# v336_answer_contract_slot_guard_locomo_probe50_changed_vs_v288

## Purpose

Offline changed-answer judge comparing v336 against v288 on LoCoMo non-adversarial probe50 rows whose final answers changed.

## Scope

- benchmark: locomo
- changed samples: 25 / 50
- old predictions: `experiments/diagnostic/v336_answer_contract_slot_guard_locomo_probe50_changed_vs_v288/old_v288_changed_predictions.jsonl`
- new predictions: `experiments/diagnostic/v336_answer_contract_slot_guard_locomo_probe50_changed_vs_v288/new_v336_changed_predictions.jsonl`
- labels: `experiments/diagnostic/v336_answer_contract_slot_guard_locomo_probe50_changed_vs_v288/changed_labels.jsonl`
- judge: `deepseek-v4-flash`, two independent temperature 0 runs, default thinking

## Metrics

- old v288 changed subset: strict `20/25`, lenient `20/25`
- new v336 changed subset: strict `21/25`, lenient `22/25`
- strict delta on changed subset: `+1`
- lenient delta on changed subset: `+2`
- v288 first50 avg query tokens: `6544.92`
- v336 probe50 avg query tokens: `5700.88`
- avg query token delta: `-844.04`

## Diagnosis

v336 reduces fixed answer/rules/output contract overhead without trimming raw Memory Context rows or the existing guide blocks. On the changed subset, LoCoMo improves mainly on event/list answers where the compact contract encourages slot-complete but concise phrasing. The improvement is not evidence of a new LTS by itself because it is only probe50, but it is a useful query-token reduction that does not show the v335 LongMemEval regression.

## Decision

Keep v336 as the preferred compact answer-contract candidate. The next algorithmic step should move more query-side guide responsibility into build-owned workspace state and operation plans, instead of further compressing raw evidence rows.

## Clean Notes

Judge outputs are offline-only and are not used by prediction, retrieval, memory build, answer generation, verifier logic, or caches.
