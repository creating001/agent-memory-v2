# V231 Source-Backed Lifecycle No-Op Repair Prune Summary

## Decision

V231 replaces v230 as the current local LTS.

V231 keeps v230's retrieval, compiler prompt, source-backed memory-state diagnostics, finalizer, guarded fact tail-exchange rerank, answer cache, and accuracy. The only behavior change is disabling the source-backed lifecycle repair trigger because v230 full traces showed that this trigger added current_state repair calls but applied zero answer revisions on both benchmarks.

## Clean Boundary

- Prediction uses only question text, raw Memory Context, visible metadata, and build-stage memory generated before the question.
- No gold answer, judge output, benchmark label, sample id, row index, test feedback, or sample-level rule is used.
- Typed memory remains source-backed: the Managed Memory State Guide and source-backed ledger only index cited raw Memory Context rows; they are not independent answer evidence.
- V231 does not remove the source-backed state/update diagnostics; it only removes the no-op second-pass repair path.

## Full Verification

| Benchmark | v231 vs v230 diff | Source-backed state ledger | Repair | Token accounting | Accuracy |
|---|---:|---:|---:|---:|---:|
| LongMemEval-S full | answer/prompt/evidence rows/retrieval hits/route `0/500` | `14/500` | source-backed reason `4 -> 0`; triggered `10 -> 6`; applied `0` | avg build/query `85393.566 / 6637.824`; repair query `28814` | inherits strict/lenient `0.834000 / 0.846000` |
| LoCoMo non-adversarial full | answer/prompt/evidence rows/retrieval hits/route `0/1540` | `4/1540` | source-backed reason `2 -> 0`; triggered `4 -> 2`; applied `0` | avg build/query `62015.57402597403 / 6100.992207792207`; repair query `9234` | inherits strict/lenient `0.793506 / 0.818831` |

Query-token reduction vs v230 is `22514` total on LME (`45.028` per QA) and `12160` total on LoCoMo (`7.896103896104` per QA). Changed-answer judge is not needed because both full predictions are answer-identical to v230 and v229.

## Artifacts

- Config: `configs/stage1_source_backed_lifecycle_noop_repair_prune_v231_seeded_qwen36_no_think_build4k_cached.json`
- Method commits: `58571bcde95ae7e70e9df03923477987ba56f959`, `3bd6422a017d0e48dd20004a8e5efeda3268e618`
- LME full: `experiments/diagnostic/stage1_source_backed_lifecycle_noop_repair_prune_v231_lme_s_full/`
- LoCoMo full: `experiments/diagnostic/stage1_source_backed_lifecycle_noop_repair_prune_v231_locomo_nonadv_full/`
- Outputs: `outputs/diagnostic/stage1_source_backed_lifecycle_noop_repair_prune_v231_*`

Run manifests are dirty only because the v231 experiment directories existed as untracked generated artifacts during rerun; this was not rerun again just to make the manifest clean.

## Next

- #2: reduce real final prompt/context tokens without hard deleting source-backed evidence rows.
- #5: improve source-backed state/update coverage only when the typed memory activation is question-aligned and backed by cited Memory Context rows.
- Keep pruning no-op verifier paths before they become hidden cost or drift risk.
