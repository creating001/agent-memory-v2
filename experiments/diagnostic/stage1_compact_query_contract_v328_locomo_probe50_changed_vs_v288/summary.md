# stage1_compact_query_contract_v328_locomo_probe50_changed_vs_v288

## Purpose

Offline changed-answer judge comparing v328 against the current LTS v288 on the LoCoMo probe50 rows whose final answers changed.

## Scope

- benchmark: locomo
- changed samples: 28
- base predictions: outputs/diagnostic/stage1_memory_object_index_v288_locomo_full/predictions.jsonl
- new predictions: outputs/diagnostic/stage1_compact_query_contract_v328_locomo_probe50/predictions.jsonl
- judge: deepseek-v4-flash, two independent temperature 0 runs

## Metrics

- old v288 changed subset: strict 21/28, lenient 24/28
- new v328 changed subset: strict 24/28, lenient 26/28
- strict delta on changed subset: +3
- lenient delta on changed subset: +2

## Diagnosis

v328 improved the LoCoMo probe50 changed subset and reduced query tokens. It remained a stepping-stone because compact answer instructions sometimes dropped necessary item subtype or profile qualifiers; v329 supersedes it.

## Clean Notes

Judge outputs are offline-only and are not used by prediction, retrieval, memory build, answer generation, verifier logic, or caches.
