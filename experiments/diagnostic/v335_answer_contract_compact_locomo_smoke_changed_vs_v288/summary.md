# v335_answer_contract_compact_locomo_smoke_changed_vs_v288

## Purpose

Offline changed-answer judge for the two LoCoMo smoke5 rows whose v335 answers differ from v288.

## Scope

- benchmark: locomo
- changed samples: 2 / 5
- old predictions: `experiments/diagnostic/v335_answer_contract_compact_locomo_smoke_changed_vs_v288/old_v288_changed_predictions.jsonl`
- new predictions: `experiments/diagnostic/v335_answer_contract_compact_locomo_smoke_changed_vs_v288/new_v335_changed_predictions.jsonl`
- labels: `experiments/diagnostic/v335_answer_contract_compact_locomo_smoke_changed_vs_v288/changed_labels.jsonl`
- judge: `deepseek-v4-flash`, two independent temperature 0 runs, default thinking

## Metrics

- old v288 changed subset: strict `2/2`, lenient `2/2`
- new v335 changed subset: strict `2/2`, lenient `2/2`
- strict delta on changed subset: `0`
- lenient delta on changed subset: `0`

## Diagnosis

v335 changes answer wording on two smoke rows but does not regress the changed subset judge. Prompt tokens decrease because only the fixed answer/rules/output contract is compacted; guide blocks and raw Memory Context remain v334/v288-style.

## Clean Notes

Judge outputs are offline-only and are not used by prediction, retrieval, memory build, answer generation, verifier logic, or caches.
