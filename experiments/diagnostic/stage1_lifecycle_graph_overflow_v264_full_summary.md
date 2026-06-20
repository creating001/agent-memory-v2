# v264 Lifecycle Graph Overflow Full Summary

## Purpose

Validate whether graph-backed evidence utility can safely move beyond passive audit by allowing a small tail-rescue overflow only when the build-time memory system graph exposes explicit lifecycle signals.

## Configuration

- config: `configs/stage1_lifecycle_graph_overflow_v264_seeded_qwen36_no_think_build4k_cached.json`
- method commit: `1dcd1305dd91b0527411c5ea24ab69db7346221e`
- parent LTS: v262 `configs/stage1_graph_evidence_utility_v262_seeded_qwen36_no_think_build4k_cached.json`
- graph utility:
  - `fusion_mode`: `overflow_tail_rescue`
  - `overflow_max_hits`: `4`
  - `required_signals`: `["supersede", "conflict_slot"]`
  - `require_new_source`: `true`

The module projects only raw source rows from source-backed memory graph slots. It does not put synthetic typed/graph memory text into final evidence.

## Full Results

| Benchmark | strict / lenient | avg build tokens | avg query tokens | graph utility applied | answer cache |
|---|---:|---:|---:|---:|---|
| LongMemEval-S full | `0.832000 / 0.844000` | `85393.566` | `6462.478` | `130/500` | hits/misses/writes `486/14/14` |
| LoCoMo non-adversarial full | `0.794156 / 0.819481` | `62015.57402597403` | `6094.017532467533` | `439/1540` | hits/misses/writes `1540/0/0` |

Accuracy is derived from v262 full judge records plus changed-answer paired judge where needed. LoCoMo is answer-identical to v262.

## Diff And Judge

- LME vs v262:
  - answer diff: `5/500`
  - prompt/final evidence diff: `14/500`
  - retrieval hits diff: `120/500`
  - pre-context-budget diff: `130/500`
  - changed-answer dual judge: v262 strict/lenient `1/5`, v264 strict/lenient `1/5`
  - per-record changed-answer judge labels are identical.
- LoCoMo vs v262:
  - answer diff: `0/1540`
  - prompt/final evidence diff: `0/1540`
  - retrieval hits diff: `118/1540`
  - pre-context-budget diff: `235/1540`

Judge outputs:

```text
outputs/diagnostic/stage1_lifecycle_graph_overflow_v264_lme_changed_vs_v262/v262_dual_judge.json
outputs/diagnostic/stage1_lifecycle_graph_overflow_v264_lme_changed_vs_v262/v264_dual_judge.json
outputs/diagnostic/stage1_lifecycle_graph_overflow_v264_lme_changed_vs_v262/v262_flash_1.json
outputs/diagnostic/stage1_lifecycle_graph_overflow_v264_lme_changed_vs_v262/v262_flash_2.json
outputs/diagnostic/stage1_lifecycle_graph_overflow_v264_lme_changed_vs_v262/v264_flash_1.json
outputs/diagnostic/stage1_lifecycle_graph_overflow_v264_lme_changed_vs_v262/v264_flash_2.json
```

## Decision

Promote v264 to local LTS.

Rationale: v264 keeps full judge accuracy unchanged while reducing the main v263 risk. The graph utility no longer overflows from generic source support or multi-value slots; it requires lifecycle conflict/supersede evidence from the build-time memory graph and still resolves final evidence to raw source rows.

## Outputs

```text
outputs/diagnostic/stage1_lifecycle_graph_overflow_v264_lme_full/predictions.jsonl
outputs/diagnostic/stage1_lifecycle_graph_overflow_v264_lme_full/traces.jsonl
outputs/diagnostic/stage1_lifecycle_graph_overflow_v264_locomo_full/predictions.jsonl
outputs/diagnostic/stage1_lifecycle_graph_overflow_v264_locomo_full/traces.jsonl
experiments/diagnostic/stage1_lifecycle_graph_overflow_v264_lme_full/
experiments/diagnostic/stage1_lifecycle_graph_overflow_v264_locomo_full/
```

## Next Steps

1. Move more lifecycle and utility computation into build-stage memory objects: validity, confidence, source-span quality, merge/supersede chains, relation edges.
2. Simplify query-time compatibility layers after each ablation proves they are unused or harmful.
3. Turn source-grounded answer audit into a bounded verifier for time, speaker, entity, numeric and stale-state consistency.
