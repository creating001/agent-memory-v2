# stage1_compact_query_slot_complete_v329_lme_probe50_changed_vs_v288

## Purpose

Offline changed-answer judge comparing v329 against the current LTS v288 on the LongMemEval probe50 rows whose final answers changed.

## Scope

- benchmark: longmemeval
- changed samples: 11
- base predictions: outputs/diagnostic/stage1_memory_object_index_v288_lme_full/predictions.jsonl
- new predictions: outputs/diagnostic/stage1_compact_query_slot_complete_v329_lme_probe50/predictions.jsonl
- judge: deepseek-v4-flash, two independent temperature 0 runs

## Metrics

- old v288 changed subset: strict 9/11, lenient 9/11
- new v329 changed subset: strict 9/11, lenient 9/11
- strict delta on changed subset: 0
- lenient delta on changed subset: 0

## Diagnosis

v329 keeps LongMemEval probe50 accuracy neutral on changed answers while reducing average query tokens versus v288 first50. This supports moving v329 to full validation, but does not alone justify an LTS change.

## Clean Notes

Judge outputs are offline-only and are not used by prediction, retrieval, memory build, answer generation, verifier logic, or caches.
