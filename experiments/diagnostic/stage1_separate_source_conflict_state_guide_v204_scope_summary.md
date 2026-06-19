# stage1_separate_source_conflict_state_guide_v204 LTS summary

## Decision

V204 replaces v202 as the current local LTS.

V204 is a #5 memory lifecycle/state/conflict/query-time reasoning cleanup. It keeps v202 prediction behavior, but adds a safer source-separated path for managed memory state guides:

- `compiler.memory_record_source` remains `retrieval`, so existing memory-aware evidence ordering is unchanged.
- `compiler.memory_state_guide_record_source` is `evidence_rows`, so any future state guide activation can inspect typed memory only when it links back to raw rows already present in Memory Context.
- `memory_state_guide_require_conflict=true` keeps the guide prompt-silent unless a slot has lifecycle/conflict evidence.
- Repeated `event` values no longer count as state conflicts; multi-value conflict only applies to `state`, `fact`, `profile`, and `preference` memory types, while explicit lifecycle markers such as `superseded`, `superseded_by`, or `valid_to` still count.

## Clean Boundary

- Prediction uses only question text, raw Memory Context, visible metadata, and build-stage memory generated before the question.
- No gold answer, judge output, benchmark label, sample id, row index, test feedback, or sample-level rule is used by retrieval, compiler, answer, repair, finalizer, audit, or cache construction.
- The new state-guide candidate trace is source-linked to rows selected by retrieval/compiler; it is not shown to the answer model unless the generic conflict gate fires.
- On both full benchmarks, the guide fired `0` times, so v204 answers and prompts are identical to v202 and inherit v202 judge records.

## Full Verification

| Benchmark | v204 vs v202 answer diff | route diff | prompt diff | evidence rows diff | Managed Memory State Guide | answer cache | inherited judge accuracy |
|---|---:|---:|---:|---:|---:|---:|---:|
| LongMemEval-S full | `0/500` | `0/500` | `0/500` | `0/500` | `0/500` | `500/0/0` | strict/lenient `0.834000 / 0.846000` |
| LoCoMo non-adversarial full | `0/1540` | `0/1540` | `0/1540` | `0/1540` | `0/1540` | `1540/0/0` | strict/lenient `0.793506 / 0.818831` |

Token accounting from run summaries is unchanged from v202:

| Benchmark | avg build tokens | avg query tokens |
|---|---:|---:|
| LongMemEval-S full | `85393.566` | `6579.622` |
| LoCoMo non-adversarial full | `62015.57402597403` | `6095.268181818182` |

The new trace-only state-guide record source differs on all rows by design: LME `500/500`, LoCoMo `1540/1540`. This is not prompt-visible and does not affect route, evidence rows, compiled prompt, answer, finalizer, or repair.

## v203 Rejection

V203 was not promoted. Its LME full run changed answers on `10/500`, prompts on `13/500`, and evidence rows on `11/500`. The Managed Memory State Guide fired on `3/500`, but inspection showed repeated `event` values such as museum visits and market participation being treated as state conflicts. It also set `memory_record_source=evidence_rows`, which changed memory-aware evidence ordering. V204 fixes both issues by separating guide source from ordering source and by excluding repeated event values from conflict detection.

## Why This Is LTS

V204 is safer than v202 for #5 because it makes the build-memory lifecycle/state guide path explicit, source-linked, and prompt-silent unless a generic conflict gate fires. It also prevents a future guide experiment from silently changing existing memory-aware evidence ordering. Performance is inherited from v202 because full prompts and answers are identical on both benchmarks.

Residual risks remain:

- The guide did not activate on either full benchmark, so this is a risk-reduction and auditability LTS, not a performance-improving LTS.
- Broader lifecycle/conflict reasoning still needs a positive prompt-visible activation that does not regress accuracy.
- The long-turn granularity profile remains active on LME and still needs further generalization.

## Artifacts

- Config: `configs/stage1_separate_source_conflict_state_guide_v204_seeded_qwen36_no_think_build4k_cached.json`
- Method commit: `d7ee5234ff9c1ab5b87480cba3dd122163d9d7cf`
- LME full: `experiments/diagnostic/stage1_separate_source_conflict_state_guide_v204_lme_s_full/`
- LoCoMo full: `experiments/diagnostic/stage1_separate_source_conflict_state_guide_v204_locomo_nonadv_full/`
- V203 rejected run: `experiments/diagnostic/stage1_conflict_gated_memory_state_guide_v203_lme_s_full/`
- Outputs: `outputs/diagnostic/stage1_separate_source_conflict_state_guide_v204_*`

## Next

- Design a narrower prompt-visible state guide that targets true active/superseded state slots and first validate it on changed-answer paired judge.
- Continue #2/#3 work on coverage-preserving context organization without hard row pruning.
- Continue reducing remaining `long_turn_precision` profile coupling with route-scoped or context-pressure mechanisms.
