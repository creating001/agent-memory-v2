# v293 Memory Layer Transition Full Summary

## Purpose

Improve the build side of the Agent Memory system without disturbing the verified v291 query path. v293 adds `memory_layer_transition_manifest_v1` to `memory_system_graph_v4`, making the transition from raw turns to typed memory objects, tiered slots, workspace operation plans, and expanded raw rows explicit.

This directly targets the build-system risk that memory was still too shallow: memory objects now carry a clearer lifecycle/tier transition contract, non-destructive supersede/archive policy, quarantine blocking, and source-backed activation semantics.

## Config

- Config: `configs/stage1_memory_layer_transition_v293_query_restore_seeded_qwen36_no_think_build4k_cached.json`
- Commit: `50e90f8bec858ad0551250adcb3818c294f91cd2`
- Query behavior: v291-equivalent. `memory_state_guide=true`, `memory_value_slot_guide=true`, `memory_workspace_plan=false`.
- Prediction workers: LME `6`, LoCoMo `6`.
- Judge accuracy: inherited from v291 because full predictions are answer-identical on both benchmarks.

## Full Metrics

| Benchmark | n | strict/lenient accuracy | avg build tokens | avg query tokens | answer diff vs v291 |
|---|---:|---:|---:|---:|---:|
| LongMemEval-S full | 500 | `0.834000 / 0.846000` (`417/500`, `423/500`) | `85393.566` | `6455.588` | `0` |
| LoCoMo non-adversarial full | 1540 | `0.794156 / 0.819481` (`1223/1540`, `1262/1540`) | `62015.57402597403` | `6093.962337662338` | `0` |

## Build Artifact Coverage

| Benchmark | operation plans | layer transition slots | layer transition records | total transitions |
|---|---:|---:|---:|---:|
| LongMemEval-S full | `44630` | `44630` | `57909` | `102539` |
| LoCoMo non-adversarial full | `196651` | `196651` | `232409` | `429060` |
| Total | `241281` | `241281` | `290318` | `531599` |

## Decision

Promote v293 to LTS. It reduces build-side system risk with no answer, token, retrieval, or query-path regression. v292 showed direct query replacement of old state/value guides was unsafe; v293 keeps query stable and strengthens the build layer instead.

## Artifacts

- Diff JSON: `experiments/diagnostic/stage1_memory_layer_transition_v293_diff_vs_v291.json`
- LME predictions: `outputs/diagnostic/stage1_memory_layer_transition_v293_lme_full/predictions.jsonl`
- LME traces: `outputs/diagnostic/stage1_memory_layer_transition_v293_lme_full/traces.jsonl`
- LoCoMo predictions: `outputs/diagnostic/stage1_memory_layer_transition_v293_locomo_full/predictions.jsonl`
- LoCoMo traces: `outputs/diagnostic/stage1_memory_layer_transition_v293_locomo_full/traces.jsonl`

