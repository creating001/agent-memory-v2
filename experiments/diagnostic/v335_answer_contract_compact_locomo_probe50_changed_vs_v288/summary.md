# v335_answer_contract_compact_locomo_probe50_changed_vs_v288

## Purpose

Offline changed-answer judge comparing v335 against v288 on LoCoMo probe50 rows whose final answers changed.

## Scope

- benchmark: locomo
- changed samples: 28 / 50
- old predictions: `experiments/diagnostic/v335_answer_contract_compact_locomo_probe50_changed_vs_v288/old_v288_changed_predictions.jsonl`
- new predictions: `experiments/diagnostic/v335_answer_contract_compact_locomo_probe50_changed_vs_v288/new_v335_changed_predictions.jsonl`
- labels: `experiments/diagnostic/v335_answer_contract_compact_locomo_probe50_changed_vs_v288/changed_labels.jsonl`
- judge: `deepseek-v4-flash`, two independent temperature 0 runs, default thinking

## Metrics

- old v288 changed subset: strict `21/28`, lenient `22/28`
- new v335 changed subset: strict `26/28`, lenient `26/28`
- strict delta on changed subset: `+5`
- lenient delta on changed subset: `+4`
- v288 first50 avg query tokens: `5916.36`
- v335 probe50 avg query tokens: `5695.24`

## Diagnosis

v335 improves LoCoMo probe50 changed-answer accuracy while reducing query tokens. The improvement suggests fixed answer-contract compaction can help the reader stay concise and direct when raw evidence remains unchanged.

## Decision

Do not promote v335 by itself because LongMemEval probe50 regresses. Use the LoCoMo gains as evidence that answer-contract compaction is worth repairing rather than discarding.

## Clean Notes

Judge outputs are offline-only and are not used by prediction, retrieval, memory build, answer generation, verifier logic, or caches.
