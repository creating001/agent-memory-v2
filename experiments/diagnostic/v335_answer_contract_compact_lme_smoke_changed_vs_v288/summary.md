# v335_answer_contract_compact_lme_smoke_changed_vs_v288

## Purpose

Offline changed-answer judge for the one LongMemEval smoke5 row whose v335 answer differs from v288.

## Scope

- benchmark: longmemeval
- changed samples: 1 / 5
- old predictions: `experiments/diagnostic/v335_answer_contract_compact_lme_smoke_changed_vs_v288/old_v288_changed_predictions.jsonl`
- new predictions: `experiments/diagnostic/v335_answer_contract_compact_lme_smoke_changed_vs_v288/new_v335_changed_predictions.jsonl`
- labels: `experiments/diagnostic/v335_answer_contract_compact_lme_smoke_changed_vs_v288/changed_labels.jsonl`
- judge: `deepseek-v4-flash`, two independent temperature 0 runs, default thinking

## Metrics

- old v288 changed subset: strict `0/1`, lenient `0/1`
- new v335 changed subset: strict `1/1`, lenient `1/1`
- strict delta on changed subset: `+1`
- lenient delta on changed subset: `+1`

## Diagnosis

v335 reduces fixed answer-contract prompt text without compacting guide blocks or raw Memory Context. In this smoke slice it changes one insufficient-answer case into the judged correct answer `Target`.

## Clean Notes

Judge outputs are offline-only and are not used by prediction, retrieval, memory build, answer generation, verifier logic, or caches.
