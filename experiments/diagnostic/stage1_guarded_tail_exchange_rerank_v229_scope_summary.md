# V229 Guarded Tail Exchange Rerank Scope Summary

## Purpose

V229 inherits the v225 LTS and replaces the rejected v228 broad fact/list rerank with a narrow, source/provenance-aware tail exchange. The reranker is only eligible for `fact_lookup`, keeps the first 52 retrieval anchors, and may return 56 rows from a 60-row candidate pool only when the rank 53-56 exchange zone has no memory-projected source, no same-session adjacent chain, and no question-term overlap.

This design follows metadata/provenance-aware rerank ideas from MemOS and xMemory-style original-source preservation. It uses only prediction-time question text, retrieval candidates, source ids, session/turn order, and build-memory provenance. It uses no gold answer, judge output, benchmark labels, sample id, test feedback, or sample-level rules.

## Runs

| Run | Output path | Git |
|---|---|---|
| LME probe50 | `outputs/diagnostic/stage1_guarded_tail_exchange_rerank_v229_lme_probe50` | `b8acd7ad22dc9cfcadaf1da3930297f00267d35f`, dirty only from untracked v229 experiment dirs |
| LoCoMo probe80 | `outputs/diagnostic/stage1_guarded_tail_exchange_rerank_v229_locomo_probe80` | `b8acd7ad22dc9cfcadaf1da3930297f00267d35f`, clean at start of run |
| LME full | `outputs/diagnostic/stage1_guarded_tail_exchange_rerank_v229_lme_s_full` | `b8acd7ad22dc9cfcadaf1da3930297f00267d35f`, dirty only from untracked v229 experiment dirs |
| LoCoMo full | `outputs/diagnostic/stage1_guarded_tail_exchange_rerank_v229_locomo_nonadv_full` | `b8acd7ad22dc9cfcadaf1da3930297f00267d35f`, dirty only from untracked v229 experiment dirs |

## Full Results

| Benchmark | v229 vs v225 diff | Rerank | Token accounting | Accuracy |
|---|---|---|---|---|
| LongMemEval-S full | answer/prompt/evidence rows/retrieval hits `0/500` | applied `0/500`; skip reasons `317` information need, `183` top-k below 56 | avg build/query `85393.566 / 6637.83`; rerank tokens `0` | inherits v225 strict/lenient `0.834000 / 0.846000` |
| LoCoMo non-adversarial full | answer diff `0/1540`; prompt/evidence/retrieval diff `2/1540` | applied `2/1540`; guard skipped `880/1540` (`805` memory source, `59` adjacent session, `16` question overlap); rerank tokens `25396` | avg build/query `62015.57402597403 / 6100.992207792207` | inherits v225 strict/lenient `0.793506 / 0.818831` |

Changed-answer paired judge is not needed because both full runs are answer-identical to v225. V229 therefore inherits v225's full dual DeepSeek flash judge records.

## Decision

Promote v229 to current LTS. The risk reduction is deliberately small: it does not solve #2 token reduction, but it turns v228's unsafe broad rerank into a guarded tail exchange that only changes two LoCoMo contexts and preserves all answers. It keeps v225's #5 State/Update Organization Ledger and prior trace/audit risk reductions.

Remaining priorities:
- #2 still needs higher-coverage tail noise reduction that lowers query tokens without broad prompt deletion or broad rerank.
- #5 still needs behavior-level state/update reasoning on source-backed lifecycle chains, not just trace ledgers.
