# v335_answer_contract_compact_lme_probe50_changed_vs_v288

## Purpose

Offline changed-answer judge comparing v335 against v288 on LongMemEval probe50 rows whose final answers changed.

## Scope

- benchmark: longmemeval
- changed samples: 8 / 50
- old predictions: `experiments/diagnostic/v335_answer_contract_compact_lme_probe50_changed_vs_v288/old_v288_changed_predictions.jsonl`
- new predictions: `experiments/diagnostic/v335_answer_contract_compact_lme_probe50_changed_vs_v288/new_v335_changed_predictions.jsonl`
- labels: `experiments/diagnostic/v335_answer_contract_compact_lme_probe50_changed_vs_v288/changed_labels.jsonl`
- judge: `deepseek-v4-flash`, two independent temperature 0 runs, default thinking

## Metrics

- old v288 changed subset: strict `6/8`, lenient `6/8`
- new v335 changed subset: strict `5/8`, lenient `5/8`
- strict delta on changed subset: `-1`
- lenient delta on changed subset: `-1`
- v288 first50 avg query tokens: `5677.4`
- v335 probe50 avg query tokens: `5530.18`

## Diagnosis

v335 reduces fixed answer/rules/output prompt overhead, but LongMemEval still regresses on changed answers. The two new wrong cases are general slot-completeness failures: a named studio answer is treated as insufficient because no street address is present, and a previous-occupation answer drops the workplace qualifier.

## Decision

Do not promote v335. Keep the answer-contract compaction direction, but v336 should add narrow general compact-contract safeguards for venue/studio/store names and role/employer qualifiers before any wider run.

## Clean Notes

Judge outputs are offline-only and are not used by prediction, retrieval, memory build, answer generation, verifier logic, or caches.
