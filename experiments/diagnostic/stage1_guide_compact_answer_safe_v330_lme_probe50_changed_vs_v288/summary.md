# stage1_guide_compact_answer_safe_v330_lme_probe50_changed_vs_v288

## Purpose

Offline changed-answer judge comparing v330 against current LTS v288 on LongMemEval probe50 rows whose final answers changed.

## Scope

- benchmark: longmemeval
- changed samples: 7 / 50
- base predictions: outputs/diagnostic/stage1_memory_object_index_v288_lme_full/predictions.jsonl
- new predictions: outputs/diagnostic/stage1_guide_compact_answer_safe_v330_lme_probe50/predictions.jsonl
- judge: deepseek-v4-flash, two independent temperature 0 runs

## Metrics

- old v288 changed subset: strict 5/7, lenient 5/7
- new v330 changed subset: strict 5/7, lenient 5/7
- strict delta on changed subset: 0
- lenient delta on changed subset: 0

## Diagnosis

v330 restores the detailed answer/output contract removed by v329 while keeping compact guide and temporal aid blocks. On LME probe50, answer changes are much smaller than v329 and changed-answer accuracy is neutral.

## Clean Notes

Judge outputs are offline-only and are not used by prediction, retrieval, memory build, answer generation, verifier logic, or caches.
