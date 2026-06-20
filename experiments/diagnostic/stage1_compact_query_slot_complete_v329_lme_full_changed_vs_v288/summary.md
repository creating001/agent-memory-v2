# stage1_compact_query_slot_complete_v329_lme_full_changed_vs_v288

## Purpose

Offline changed-answer judge comparing v329 against current LTS v288 on LongMemEval full rows whose final answers changed.

## Scope

- benchmark: longmemeval
- changed samples: 175 / 500
- base predictions: outputs/diagnostic/stage1_memory_object_index_v288_lme_full/predictions.jsonl
- new predictions: outputs/diagnostic/stage1_compact_query_slot_complete_v329_lme_full/predictions.jsonl
- labels: outputs/prepare_longmemeval_s_cleaned/labels.jsonl
- judge: deepseek-v4-flash, two independent temperature 0 runs

## Metrics

- old v288 changed subset: strict 125/175, lenient 127/175
- new v329 changed subset: strict 105/175, lenient 117/175
- strict delta on changed subset: -20
- lenient delta on changed subset: -10
- projected v329 full accuracy from v288 baseline: strict 397/500 = 0.794000, lenient 413/500 = 0.826000
- avg query tokens: v288 6455.588, v329 5947.404

## Diagnosis

v329 reduces query tokens but regresses LongMemEval full too much to become LTS. Losses are mostly from compact prompt behavior: dropped role/scope qualifiers, insufficient explanations that are too terse for negative questions, and list/count/arithmetic answers that omit or add items.

## Decision

Do not run LoCoMo full for v329 and do not promote v329. Keep v288 as LTS. The next version should preserve v288-style answer/output constraints and only compact lower-risk guide sections.

## Clean Notes

Judge outputs are offline-only and are not used by prediction, retrieval, memory build, answer generation, verifier logic, or caches.
