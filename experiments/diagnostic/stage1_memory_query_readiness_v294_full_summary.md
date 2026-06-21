# v294 Memory Query Readiness Full Summary

## Purpose

Improve the build side of the Agent Memory system without disturbing the verified v293 query path. v294 adds `memory_query_readiness_manifest_v1` to `memory_system_graph_v4`, turning the workspace, operation plan, layer transition, and object index artifacts into a guarded query-consumer policy.

This directly targets the risk that memory artifacts were still not governed enough for future query simplification. Each workspace slot now states whether it can be consumed as an additive source-backed index, source expansion plan, context organization signal, verification signal, or audit signal; it also explicitly blocks derived memory as final evidence and blocks replacing the stable state/value guide until equivalence is proven.

## Config

- Config: `configs/stage1_memory_query_readiness_v294_query_restore_seeded_qwen36_no_think_build4k_cached.json`
- Commit: `bf80cf6a3c8598d1fde6ac164f55bf4c67330cb7`
- Query behavior: v293-equivalent. `memory_state_guide=true`, `memory_value_slot_guide=true`, `memory_workspace_plan=false`.
- Prediction workers: LME `6`, LoCoMo `6`.
- Judge accuracy: inherited from v293 because full predictions are answer-identical on both benchmarks.
- Git dirty note: the LME run summary records `dirty=True` because the paired LoCoMo run was generating output concurrently; the v294 algorithm commit existed before both predictions.

## Full Metrics

| Benchmark | n | strict/lenient accuracy | avg build tokens | avg query tokens | answer diff vs v293 |
|---|---:|---:|---:|---:|---:|
| LongMemEval-S full | 500 | `0.834000 / 0.846000` (`417/500`, `423/500`) | `85393.566` | `6455.588` | `0` |
| LoCoMo non-adversarial full | 1540 | `0.794156 / 0.819481` (`1223/1540`, `1262/1540`) | `62015.57402597403` | `6093.962337662338` | `0` |

## Build Artifact Coverage

| Benchmark | operation plans | layer transitions | query readiness slots | guarded ready | replacement blocked |
|---|---:|---:|---:|---:|---:|
| LongMemEval-S full | `44630` | `102539` | `44630` | `44630` | `44630` |
| LoCoMo non-adversarial full | `196651` | `429060` | `196651` | `196651` | `196651` |
| Total | `241281` | `531599` | `241281` | `241281` | `241281` |

Consumer-mode totals: `additive_index=241281`, `source_expansion=241281`, `context_organization=241281`, `verification_signal=241281`, `trace_audit=241281`, `conflict_chain_audit=11328`, `superseded_chain_audit=11328`.

## Decision

Promote v294 to LTS. It reduces build-to-query system risk with no answer or token regression. The key improvement over v293 is not another query prompt patch; it is a build-owned readiness contract that makes future operation-plan consumption guarded, source-backed, auditable, and reversible.

## Artifacts

- Diff JSON: `experiments/diagnostic/stage1_memory_query_readiness_v294_diff_vs_v293.json`
- LME predictions: `outputs/diagnostic/stage1_memory_query_readiness_v294_lme_full/predictions.jsonl`
- LME traces: `outputs/diagnostic/stage1_memory_query_readiness_v294_lme_full/traces.jsonl`
- LoCoMo predictions: `outputs/diagnostic/stage1_memory_query_readiness_v294_locomo_full/predictions.jsonl`
- LoCoMo traces: `outputs/diagnostic/stage1_memory_query_readiness_v294_locomo_full/traces.jsonl`
