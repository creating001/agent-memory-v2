# stage1_compact_query_contract_v328_smoke_changed_vs_v288

## Purpose

Offline changed-answer judge comparing v328 against the current LTS v288 on smoke5 changed-answer subsets.

## Scope

- benchmarks: longmemeval smoke5 and locomo smoke5
- changed samples: LongMemEval 1, LoCoMo 2
- judge: deepseek-v4-flash, two independent temperature 0 runs

## Metrics

- LongMemEval old v288 changed subset: strict 0/1, lenient 0/1
- LongMemEval new v328 changed subset: strict 0/1, lenient 0/1
- LoCoMo old v288 changed subset: strict 2/2, lenient 2/2
- LoCoMo new v328 changed subset: strict 2/2, lenient 2/2

## Diagnosis

Smoke changed-answer judge was neutral. Probe50 was needed because the smoke set was too small to evaluate compact query prompt risk.

## Clean Notes

Judge outputs are offline-only and are not used by prediction, retrieval, memory build, answer generation, verifier logic, or caches.
