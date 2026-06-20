# v336_answer_contract_slot_guard_lme_probe50_changed_vs_v288

## Purpose

Offline changed-answer judge comparing v336 against v288 on LongMemEval probe50 rows whose final answers changed.

## Scope

- benchmark: longmemeval
- changed samples: 8 / 50
- old predictions: `experiments/diagnostic/v336_answer_contract_slot_guard_lme_probe50_changed_vs_v288/old_v288_changed_predictions.jsonl`
- new predictions: `experiments/diagnostic/v336_answer_contract_slot_guard_lme_probe50_changed_vs_v288/new_v336_changed_predictions.jsonl`
- labels: `experiments/diagnostic/v336_answer_contract_slot_guard_lme_probe50_changed_vs_v288/changed_labels.jsonl`
- judge: `deepseek-v4-flash`, two independent temperature 0 runs, default thinking

## Metrics

- old v288 changed subset: strict `6/8`, lenient `6/8`
- new v336 changed subset: strict `6/8`, lenient `6/8`
- strict delta on changed subset: `0`
- lenient delta on changed subset: `0`
- v288 first50 avg query tokens: `5677.4`
- v336 probe50 avg query tokens: `5555.76`
- avg query token delta: `-121.64`

## Diagnosis

v336 keeps the v335 answer-contract compaction but adds general slot-completeness guards for named place answers and occupation/role qualifiers. The v335 LongMemEval regression is repaired on the changed subset: the venue/studio case no longer changes from v288, and the previous-occupation answer preserves the workplace qualifier. One store/coupon case remains wrong under both v288 and v336, so this is not a performance gain on LongMemEval probe50, but it removes the observed v335 regression while still reducing query tokens.

## Decision

Keep v336 as the current compact answer-contract candidate. Do not promote to LTS from probe50 alone; use it as the safe query-token baseline for the next build-owned workspace replacement step or for a full changed-answer validation if the next version remains stable.

## Clean Notes

Judge outputs are offline-only and are not used by prediction, retrieval, memory build, answer generation, verifier logic, or caches.
