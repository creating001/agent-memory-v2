# stage1_question_aligned_stateful_conflict_guide_v205 LTS summary

## Decision

V205 replaces v204 as the current local LTS.

V205 is a narrow #5 memory lifecycle/state/conflict/query-time reasoning improvement. It keeps v204 retrieval and evidence ordering unchanged, but lets the Managed Memory State Guide become prompt-visible only when a source-linked conflict slot is both question-aligned and stateful:

- `compiler.memory_record_source` remains `retrieval`, so existing memory-aware evidence ordering is unchanged.
- `compiler.memory_state_guide_record_source` remains `evidence_rows`, so guide records must link back to raw rows already visible in Memory Context.
- `memory_state_guide_require_conflict=true` keeps the guide silent unless active/superseded, `valid_to`, `superseded_by`, or supported multi-value state/fact/profile/preference conflict evidence exists.
- `memory_state_guide_require_slot_overlap=true` requires the slot subject/predicate/value terms to overlap focused question terms; predicates such as `has_status` are split on underscores.
- `memory_state_guide_require_stateful_slot=true` blocks text-only matches from generic preferences/events, so a phrase such as "living room plants" does not become a living-place state guide.

## Clean Boundary

- Prediction uses only question text, raw Memory Context, visible metadata, and build-stage memory generated before the question.
- No gold answer, judge output, benchmark label, sample id, row index, test feedback, or sample-level rule is used by retrieval, compiler, answer, repair, finalizer, audit, cache construction, or the new guide gates.
- The guide is source-backed and advisory: it tells the answer model to verify every final fact against cited raw Memory Context rows.
- The new gates are generic slot/type/question gates, not benchmark- or sample-specific rules.

## Full Verification

| Benchmark | v205 vs v204 answer diff | route diff | prompt diff | evidence rows diff | Managed Memory State Guide | answer cache | inherited judge accuracy |
|---|---:|---:|---:|---:|---:|---:|---:|
| LongMemEval-S full | `0/500` | `0/500` | `1/500` | `0/500` | `1/500` | `499/1/1` | strict/lenient `0.834000 / 0.846000` |
| LoCoMo non-adversarial full | `0/1540` | `0/1540` | `0/1540` | `0/1540` | `0/1540` | `1540/0/0` | strict/lenient `0.793506 / 0.818831` |

Because both full predictions are answer-identical to v204, v205 inherits the v204/v202 dual DeepSeek flash judge records. No changed-answer judge is needed for this promotion.

Token accounting from run summaries:

| Benchmark | avg build tokens | avg query tokens |
|---|---:|---:|
| LongMemEval-S full | `85393.566` | `6580.196` |
| LoCoMo non-adversarial full | `62015.57402597403` | `6095.268181818182` |

The single LME prompt-visible activation is `e1b01117f5349f7b26fd1dec`: the question asks for the user's previous United Airlines frequent flyer status, and the guide exposes a source-backed `has_status` slot with active `Premier Gold` and superseded `Premier Silver`. The answer remains `Premier Silver`.

LoCoMo's manifest records `dirty=true` because the LME v205 experiment directory was already untracked when the LoCoMo run started. The method code for both runs is commit `41aa661f5eb5fcd97ae7df3c809fd55d28b855d5`; no source/config changes were dirty.

## Why This Is LTS

V205 is safer than v204 for #5 because v204's source-separated state guide path stayed prompt-silent on both full benchmarks, while v205 demonstrates one real prompt-visible activation under stricter source-backed, question-aligned, stateful-slot gates. It does not change routes, evidence rows, or answers on either full benchmark, so performance is not lower than v204.

Residual risks remain:

- The guide still activates rarely; broader memory management and update reasoning need more positive activations without making profile/preference/event conflicts overbroad.
- The long-turn granularity profile remains active on LME and still needs further generalization.
- Top-k/context noise and selected-context scope remain open risk areas.

## Artifacts

- Config: `configs/stage1_question_aligned_stateful_conflict_guide_v205_seeded_qwen36_no_think_build4k_cached.json`
- Method commit: `41aa661f5eb5fcd97ae7df3c809fd55d28b855d5`
- LME full: `experiments/diagnostic/stage1_question_aligned_stateful_conflict_guide_v205_lme_s_full/`
- LoCoMo full: `experiments/diagnostic/stage1_question_aligned_stateful_conflict_guide_v205_locomo_nonadv_full/`
- Outputs: `outputs/diagnostic/stage1_question_aligned_stateful_conflict_guide_v205_*`

## Next

- Extend source-backed state/update organization beyond status-like slots while preserving question alignment and stateful-slot gating.
- Continue #2/#3 work on coverage-preserving context organization without hard row pruning.
- Keep pruning redundant long-profile compatibility paths only after diff evidence shows they are no-op.
