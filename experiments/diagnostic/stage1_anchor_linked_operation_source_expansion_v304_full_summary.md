# v304 Anchor-Linked Operation Source Expansion Full Summary

## Decision

Promote v304 to current LTS.

v304 keeps v303's source-backed operation source expansion mechanism but adds a visible-anchor linkage gate: an operation plan can add a missing raw source only when at least one source from the same source chain is already present in retrieval candidates. It also requires `active_with_history`, at least two matched slot terms, and emits at most one missing source per query.

## Clean Setting

- Algorithm commit: `7c4bb58c7bb982fdd0165cbaf7163862200ae5ad`
- Config: `configs/stage1_anchor_linked_operation_source_expansion_v304_query_restore_seeded_qwen36_no_think_build4k_cached.json`
- No gold answer, judge output, benchmark label, sample id, test feedback, or sample-level rule is used by prediction.
- Full judge accuracy uses v302 per-sample judge results because both benchmarks have zero answer/prompt/evidence diff vs v302. This is a full merged metric for this zero-diff case, not a rule that future versions must inherit.

## Formal Runs

- LME: `experiments/formal/stage1_anchor_linked_operation_source_expansion_v304_lme_s_full_7c4bb58/`
- LoCoMo: `experiments/formal/stage1_anchor_linked_operation_source_expansion_v304_locomo_nonadv_full_7c4bb58/`
- LME predictions: `outputs/formal/stage1_anchor_linked_operation_source_expansion_v304_lme_s_full_7c4bb58/predictions.jsonl`
- LoCoMo predictions: `outputs/formal/stage1_anchor_linked_operation_source_expansion_v304_locomo_nonadv_full_7c4bb58/predictions.jsonl`

Both formal summaries recorded `dirty=False`. The LoCoMo run summary records commit `5e1853c` because the LME formal run record was committed before running LoCoMo; no code/config change occurred after algorithm commit `7c4bb58`.

## Full Metrics

| Benchmark | strict/lenient | counts | avg build tokens | avg query tokens |
|---|---:|---:|---:|---:|
| LongMemEval-S full | `0.834000 / 0.846000` | `417/500`, `423/500` | `85393.566` | `6455.588` |
| LoCoMo non-adversarial full | `0.794156 / 0.819481` | `1223/1540`, `1262/1540` | `62015.57402597403` | `6093.879220779221` |

## Diff vs v302

| Benchmark | answer diff | prompt diff | evidence diff | operation source expansion |
|---|---:|---:|---:|---:|
| LongMemEval-S full | `0/500` | `0/500` | `0/500` | applied `1/500`, emitted `1` source |
| LoCoMo non-adversarial full | `0/1540` | `0/1540` | `0/1540` | applied `0/1540`, emitted `0` sources |

## Why v304 Replaces v302

v302 was the safe LTS because operation evidence coverage was trace-only. v303 proved that naive source expansion is risky: one weak overlap could activate active-only working-memory sources and regress LME. v304 keeps the system-level operation consumer but changes it into a guarded, anchor-linked source-chain completion policy. This reduces the v303 risk while preserving v302 accuracy and token cost.

The practical status is conservative: v304 does not force new prompt evidence unless the retrieved context already partially anchors the same operation source chain. It is therefore a safer LTS for continuing build-side memory operations than v302, while retaining identical benchmark outputs.

## Next Step

Use v304 as the baseline for a stricter but more useful expansion policy: require visible-anchor linkage, then experiment with source-chain utility scoring and source coverage improvements that can actually change final context without disturbing raw retrieval salience.
