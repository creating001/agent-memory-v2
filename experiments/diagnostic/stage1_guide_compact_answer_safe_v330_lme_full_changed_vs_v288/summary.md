# stage1_guide_compact_answer_safe_v330_lme_full_changed_vs_v288

## Purpose

Offline changed-answer judge comparing v330 against current LTS v288 on LongMemEval full rows whose final answers changed.

## Scope

- benchmark: longmemeval
- changed samples: 134 / 500
- base predictions: outputs/diagnostic/stage1_memory_object_index_v288_lme_full/predictions.jsonl
- new predictions: outputs/diagnostic/stage1_guide_compact_answer_safe_v330_lme_full/predictions.jsonl
- labels: outputs/prepare_longmemeval_s_cleaned/labels.jsonl
- judge: deepseek-v4-flash, two independent temperature 0 runs

## Metrics

- old v288 changed subset: strict 86/134, lenient 89/134
- new v330 changed subset: strict 68/134, lenient 78/134
- strict delta on changed subset: -18
- lenient delta on changed subset: -11
- projected v330 full accuracy: strict 399/500 = 0.798000, lenient 412/500 = 0.824000
- avg query tokens: v288 6455.588, v330 6189.544

## Diagnosis

v330 is safer than v329 on probe and reduces query tokens, but LongMemEval full still regresses too much. Restoring the detailed answer/output contract was not sufficient; compacting guide/temporal-aid content still changes answer behavior.

## Decision

Do not run LoCoMo full for v330 and do not promote v330. Keep v288 as LTS. Next query-token work should be more conservative: avoid semantic guide compression and test format-preserving overhead reductions only.

## Clean Notes

Judge outputs are offline-only and are not used by prediction, retrieval, memory build, answer generation, verifier logic, or caches.
