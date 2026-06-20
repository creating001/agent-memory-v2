# stage1_compact_query_slot_complete_v329_locomo_probe50_changed_vs_v288

## Purpose

Offline changed-answer judge comparing v329 against the current LTS v288 on the LoCoMo probe50 rows whose final answers changed.

## Scope

- benchmark: locomo
- changed samples: 29
- base predictions: outputs/diagnostic/stage1_memory_object_index_v288_locomo_full/predictions.jsonl
- new predictions: outputs/diagnostic/stage1_compact_query_slot_complete_v329_locomo_probe50/predictions.jsonl
- judge: deepseek-v4-flash, two independent temperature 0 runs

## Metrics

- old v288 changed subset: strict 23/29, lenient 26/29
- new v329 changed subset: strict 26/29, lenient 27/29
- strict delta on changed subset: +3
- lenient delta on changed subset: +1

## Diagnosis

v329 improves the LoCoMo probe50 changed subset while reducing average query tokens versus v288 first50. The slot-complete compact guard fixed the main v328 drift pattern where compact prompts could omit role, subtype, location, or scope qualifiers.

## Clean Notes

Judge outputs are offline-only and are not used by prediction, retrieval, memory build, answer generation, verifier logic, or caches.
