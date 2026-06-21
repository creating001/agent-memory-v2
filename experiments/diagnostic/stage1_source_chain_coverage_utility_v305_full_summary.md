# v305 Source-Chain Coverage Utility Full Summary

## Decision

Promote v305 to current LTS.

v305 keeps v304's anchor-linked source expansion, then makes the operation more explicit as a build-side source-chain coverage policy. An expansion plan must now pass a minimum utility score and may only fill an opposite current/historical source-role gap. The mechanism still emits raw source ids only; typed/derived memory is not rendered as evidence and cannot replace raw Memory rows.

## Clean Setting

- Algorithm commit: `57f8a57434dd4802d97b19fbf890f808a8e2ee04`
- Config: `configs/stage1_source_chain_coverage_utility_v305_query_restore_seeded_qwen36_no_think_build4k_cached.json`
- No gold answer, judge output, benchmark label, sample id, test feedback, or sample-level rule is used by prediction.
- Full judge accuracy is inherited from v304 because both benchmarks have zero answer/prompt/evidence diff vs v304. This is a valid full metric for this zero-output-diff case, not a requirement that future runs must use inheritance.

## External Method Signals

- EverOS-style source-backed memory objects and parent provenance: keep raw source chains as the authority.
- xMemory-style hierarchy/select-then-expand: select candidate memory objects first, then allow tightly gated source expansion.
- SimpleMem/hindsight-style multi-view context organization: use memory operations as organization and verification signals, not direct answer shortcuts.

## Formal Runs

- LME: `experiments/formal/stage1_source_chain_coverage_utility_v305_lme_s_full_57f8a57/`
- LoCoMo: `experiments/formal/stage1_source_chain_coverage_utility_v305_locomo_nonadv_full_57f8a57/`
- LME predictions: `outputs/formal/stage1_source_chain_coverage_utility_v305_lme_s_full_57f8a57/predictions.jsonl`
- LoCoMo predictions: `outputs/formal/stage1_source_chain_coverage_utility_v305_locomo_nonadv_full_57f8a57/predictions.jsonl`

LME run summary recorded `dirty=False`. LoCoMo run summary recorded `dirty=True` because the LME formal run artifacts were already untracked in the worktree; no code/config change occurred after algorithm commit `57f8a57`.

## Full Metrics

| Benchmark | strict/lenient | counts | avg build tokens | avg query tokens |
|---|---:|---:|---:|---:|
| LongMemEval-S full | `0.834000 / 0.846000` | `417/500`, `423/500` | `85393.566` | `6455.588` |
| LoCoMo non-adversarial full | `0.794156 / 0.819481` | `1223/1540`, `1262/1540` | `62015.57402597403` | `6093.879220779221` |

## Diff vs v304

| Benchmark | answer diff | prompt diff | evidence diff | retrieval diff | operation source expansion |
|---|---:|---:|---:|---:|---:|
| LongMemEval-S full | `0/500` | `0/500` | `0/500` | `1/500` | applied `1/500`, selected `1`, emitted `1` source |
| LoCoMo non-adversarial full | `0/1540` | `0/1540` | `0/1540` | `0/1540` | applied `0/1540`, selected `0`, emitted `0` sources |

The single LME retrieval change matched terms `ride` and `ticket` and emitted source `6702277b_1:turn_0004`, but the final compiled evidence, prompt, and answer were unchanged.

## Why v305 Replaces v304

v304 made source expansion safer by requiring a visible raw anchor from the same source chain. v305 reduces the remaining risk further by adding an explicit operation utility threshold and an opposite-role gap policy. This prevents source expansion from becoming another weak overlap retriever and turns it into a conservative memory operation: identify a source-chain coverage gap, verify that the opposite current/historical role is already represented, and only then offer one missing raw source to the overflow tail.

This is not a benchmark-specific rule and does not use labels or sample ids. It is a cleaner continuation point for the current goal: build memory objects and operations should participate in source coverage, conflict/state organization, context assembly, and verification, while final answers remain evidence-first.

## Next Step

Use v305 as the baseline for a more effective consumer: keep the utility/gap gates, then let the operation choose among source-chain coverage, conflict-state coverage, and answer-verification coverage under a tighter query token budget.
