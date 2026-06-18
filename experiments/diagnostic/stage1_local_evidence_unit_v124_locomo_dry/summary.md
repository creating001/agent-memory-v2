# stage1_local_evidence_unit_v124_locomo_dry

## Purpose

Check whether the selected-context short-turn policy can be generalized into a broader local evidence unit policy without running a costly answer-model evaluation.

V124 inherits V121/V116 and only changes short-turn `retrieval.selected_context`:

- adds `temporal_lookup` to the selected-context information needs
- raises selected-context `max_rows` from `6` to `10`
- keeps the same same-session local window policy

This prediction path uses only question text, retrieved raw turns, same-session visible turn order, and the prediction-time route. It does not use gold answers, judge output, benchmark labels, sample ids, row indices, test feedback, or sample-level rules.

## Protocol

- Config: `configs/stage1_local_evidence_unit_v124_qwen36_no_think_build4k_cached.json`
- Benchmark input: `outputs/prepare_locomo_non_adversarial/prediction_input.jsonl`
- Baseline trace comparison: `outputs/formal/stage1_extended_selected_context_v116_qwen36_no_think_build4k_locomo_nonadv_full_aeac792/traces.jsonl`
- Mode: compile dry-run with null answer, no answer-model calls
- Git commit: `88efe8b`
- Dirty status: dirty; includes pipeline/config/test/experiment-record changes for v118-v124 diagnostics and the v125 route-override implementation in progress

## Dry-Run Result

| metric | value |
|---|---:|
| samples changed | `1536 / 1540` |
| selected_context applied | `1536` vs v116 `1198` |
| materialized selected-context rows | `15360` vs v116 `7188` |
| average context char delta | `+2101.65` |
| max context char delta | `+8070` |
| min context char delta | `-81` |
| average evidence row delta | `-5.008` |

By route:

| route | n | changed | avg context char delta | avg evidence row delta |
|---|---:|---:|---:|---:|
| `current_state` | `4` | `0` | `0.0` | `0.0` |
| `fact_lookup` | `882` | `882` | `+976.8` | `-6.45` |
| `list_count` | `270` | `270` | `+1025.1` | `-6.40` |
| `profile_preference` | `46` | `46` | `+959.5` | `-6.28` |
| `temporal_lookup` | `338` | `338` | `+6077.1` | `-0.027` |

## Diagnosis

V124 is too broad for a mainline candidate. It globally changes almost every LoCoMo prompt, increases context by roughly 2.1K chars per sample, and reduces final raw evidence row count for non-temporal routes. That is a poor tradeoff for a policy intended to repair local missing evidence.

The useful signal remains narrower: LoCoMo badcase coverage showed many temporal failures have a missing supporting turn adjacent to an already retrieved turn. The next candidate should keep V116 selected context unchanged for fact/list/profile routes and add only a route-scoped temporal local evidence unit.

## Decision

Rejected before full answer evaluation. Do not run V124 full. Continue with a route-scoped V125 diagnostic.
