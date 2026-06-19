# V230 Source-Backed Lifecycle Memory Repair Scope Summary

## Purpose

V230 inherits the v229 LTS retrieval, main compiler prompt, answer cache, finalizer, and guarded fact tail-exchange rerank. The only behavior change is a narrow current-state repair trigger: if a current/previous/now/how-long state question has multiple draft support values, multiple raw lifecycle rows, and a question-aligned source-backed managed-memory ledger, the repair pass receives both the raw lifecycle ledger and a typed-memory ledger.

The typed-memory ledger is only an index into cited raw Memory Context rows. It is not independent evidence. This moves risk #5 from trace-only state/update organization toward source-backed query-time verification without widening temporal/list/profile routes. Prediction uses no gold answer, judge output, benchmark labels, sample id, test feedback, or sample-level rules.

## Runs

| Run | Output path | Git |
|---|---|---|
| LME full | `outputs/diagnostic/stage1_source_backed_lifecycle_memory_repair_v230_lme_s_full` | `f9931ec1919717e13f138b8b2e466cbdca4d10b6`, clean |
| LoCoMo full | `outputs/diagnostic/stage1_source_backed_lifecycle_memory_repair_v230_locomo_nonadv_full` | `f9931ec1919717e13f138b8b2e466cbdca4d10b6`, dirty only from untracked v230 LME experiment dir |

## Full Results

| Benchmark | v230 vs v229 diff | Source-backed state repair | Token accounting | Accuracy |
|---|---|---|---|---|
| LongMemEval-S full | answer/prompt/evidence rows/retrieval hits `0/500` | ledger `14/500`; repair reason `4/500`; applied `0/500` | avg build/query `85393.566 / 6682.852`; repair query tokens `51328`; rerank tokens `0` | inherits v229 strict/lenient `0.834000 / 0.846000` |
| LoCoMo non-adversarial full | answer/prompt/evidence rows/retrieval hits `0/1540` | ledger `4/1540`; repair reason `2/1540`; applied `0/1540` | avg build/query `62015.57402597403 / 6108.888311688312`; repair query tokens `21394`; rerank tokens `25396` | inherits v229 strict/lenient `0.793506 / 0.818831` |

Changed-answer paired judge is not needed because both full runs are answer-identical to v229. V230 inherits v229's full dual DeepSeek flash judge records.

## Decision

Promote v230 to current local LTS. Accuracy is unchanged, but #5 risk is lower than v229 because source-backed typed memory now participates in a narrow repair-time state/update verifier instead of only appearing in trace ledgers. The tradeoff is a small query-token increase from additional repair calls; this is acceptable for LTS because no answers changed and the trigger is tightly gated.

Remaining priorities:
- #2 still needs real query-token reduction without broad row deletion or broad rerank.
- #5 still needs higher-coverage state/update behavior, but only when typed memory is source-backed and question-aligned.
- `src` should continue to be trimmed after each stable step so old compatibility paths do not hide behavior.
