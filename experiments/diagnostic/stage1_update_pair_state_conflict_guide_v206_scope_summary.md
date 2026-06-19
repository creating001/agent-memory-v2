# stage1_update_pair_state_conflict_guide_v206 LTS summary

## Decision

V206 replaces v205 as the current local LTS.

V206 is a narrow #5 memory lifecycle/state/conflict/query-time reasoning cleanup. It keeps v205 prediction behavior, but tightens prompt-visible Managed Memory State Guide activation so a state slot must contain an active-plus-superseded update pair with distinct values.

## Clean Boundary

- Prediction uses only question text, raw Memory Context, visible metadata, and build-stage memory generated before the question.
- No gold answer, judge output, benchmark label, sample id, row index, test feedback, or sample-level rule is used by retrieval, compiler, answer, repair, finalizer, audit, cache construction, or guide gates.
- Derived typed memory remains source-backed activation only; final facts must still be verified against raw Memory Context rows.
- The new active/superseded pair gate is a generic lifecycle/update condition, not a benchmark- or sample-specific shortcut.

## Full Verification

| Benchmark | v206 vs v205 answer diff | route diff | prompt diff | evidence rows diff | Managed Memory State Guide | answer cache | inherited judge accuracy |
|---|---:|---:|---:|---:|---:|---:|---:|
| LongMemEval-S full | `0/500` | `0/500` | `0/500` | `0/500` | `1/500` | `500/0/0` | strict/lenient `0.834000 / 0.846000` |
| LoCoMo non-adversarial full | `0/1540` | `0/1540` | `0/1540` | `0/1540` | `0/1540` | `1540/0/0` | strict/lenient `0.793506 / 0.818831` |

Because both full predictions are answer-identical to v205, v206 inherits the v205/v204/v202 dual DeepSeek flash judge records. No changed-answer judge is needed for this promotion.

Token accounting from run summaries:

| Benchmark | avg build tokens | avg query tokens |
|---|---:|---:|
| LongMemEval-S full | `85393.566` | `6580.196` |
| LoCoMo non-adversarial full | `62015.57402597403` | `6095.268181818182` |

The single LME prompt-visible activation remains `e1b01117f5349f7b26fd1dec`: active `Premier Gold` and superseded `Premier Silver` for the source-backed `has_status` slot. This is the intended update-pair case. LoCoMo has no prompt-visible Managed Memory State Guide activation.

LoCoMo's manifest records `dirty=true` because the LME v206 experiment directory was already untracked when the LoCoMo run started. The method code for both runs is commit `79353b93c163848b4f692ab1e73f8ff4d7de939c`; no source/config changes were dirty.

## Why This Is LTS

V206 is safer than v205 for #5 because it prevents isolated superseded/profile/preference lifecycle markers from becoming prompt-visible state-conflict guidance. It preserves the one real active/superseded status update activation from v205 and changes no routes, prompts, evidence rows, or answers on either full benchmark.

This does not mean all five original risk points are solved. Residual risks remain:

- #1/#3: LME still uses the `long_turn_precision` granularity profile; selected-context hard gates have previously hurt accuracy.
- #2: top-k/context noise and rerank remain open; previous hard pruning or broad rerank experiments were negative.
- #5: broader memory organization and update reasoning need more positive activations beyond status-like update pairs.

## Artifacts

- Config: `configs/stage1_update_pair_state_conflict_guide_v206_seeded_qwen36_no_think_build4k_cached.json`
- Method commit: `79353b93c163848b4f692ab1e73f8ff4d7de939c`
- LME full: `experiments/diagnostic/stage1_update_pair_state_conflict_guide_v206_lme_s_full/`
- LoCoMo full: `experiments/diagnostic/stage1_update_pair_state_conflict_guide_v206_locomo_nonadv_full/`
- Outputs: `outputs/diagnostic/stage1_update_pair_state_conflict_guide_v206_*`

## Next

- Continue #2 with coverage-preserving context organization rather than hard pruning.
- Continue #1/#3 by replacing the remaining long-turn profile dependency with general context-pressure or route-scoped evidence policies.
- Extend #5 only where source-backed update chains are visible and question-aligned.
