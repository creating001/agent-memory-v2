# stage1_guide_compact_answer_safe_v330_locomo_probe50_changed_vs_v288

## Purpose

Offline changed-answer judge comparing v330 against current LTS v288 on LoCoMo probe50 rows whose final answers changed.

## Scope

- benchmark: locomo
- changed samples: 21 / 50
- base predictions: outputs/diagnostic/stage1_memory_object_index_v288_locomo_full/predictions.jsonl
- new predictions: outputs/diagnostic/stage1_guide_compact_answer_safe_v330_locomo_probe50/predictions.jsonl
- judge: deepseek-v4-flash, two independent temperature 0 runs

## Metrics

- old v288 changed subset: strict 16/21, lenient 17/21
- new v330 changed subset: strict 18/21, lenient 20/21
- strict delta on changed subset: +2
- lenient delta on changed subset: +3

## Diagnosis

v330 keeps the safer detailed answer contract and improves the LoCoMo probe50 changed subset while still reducing prompt size versus v288 first50. This is a better query-token candidate than v329.

## Clean Notes

Judge outputs are offline-only and are not used by prediction, retrieval, memory build, answer generation, verifier logic, or caches.
