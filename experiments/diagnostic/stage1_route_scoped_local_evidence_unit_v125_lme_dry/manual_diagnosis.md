# stage1_route_scoped_local_evidence_unit_v125_lme_dry

## Purpose

Check LongMemEval compiler compatibility for V125 before any full answer/judge run.

This run uses a null answerer and therefore has no accuracy meaning. It only verifies whether the V125 route-scoped temporal selected-context override changes LongMemEval prompts, retrieved raw evidence row ids, route assignment, or context size relative to the current V116 LTS trace.

The comparison reads prediction-time traces only. It does not read gold answers, judge outputs, benchmark labels, sample ids, row indices, test feedback, or sample-level rules.

## Run

- Config snapshot: `experiments/diagnostic/stage1_route_scoped_local_evidence_unit_v125_lme_dry/config_snapshot.json`
- Predictions: `outputs/diagnostic/stage1_route_scoped_local_evidence_unit_v125_lme_dry/predictions.jsonl`
- Traces: `outputs/diagnostic/stage1_route_scoped_local_evidence_unit_v125_lme_dry/traces.jsonl`
- Metrics: `experiments/diagnostic/stage1_route_scoped_local_evidence_unit_v125_lme_dry/metrics.json`
- Compatibility comparison: `experiments/diagnostic/stage1_route_scoped_local_evidence_unit_v125_lme_dry/compatibility_vs_v116.json`

Reproduction command:

```bash
python scripts/run_stage1.py \
  --input outputs/prepare_longmemeval_s_cleaned/prediction_input.jsonl \
  --config /tmp/stage1_route_scoped_local_evidence_unit_v125_lme_dry_config.json \
  --run-id stage1_route_scoped_local_evidence_unit_v125_lme_dry \
  --benchmark longmemeval \
  --subset s_full \
  --experiment-kind diagnostic \
  --workers 8
```

The temporary config is the V125 config with answer mode changed to `null_answerer`, answer cache disabled, and repair disabled.

## Runner Metrics

- Samples: `500`
- Avg build tokens: `85393.566`
- Avg query tokens: `0.0` because answering was disabled
- Avg compiled evidence items: `34.752`
- Avg context chars: `19772.166`
- Selected-context applied: `0/500`
- Build cache hit/miss/write: `3341/0/0`
- Answer finalizer applied: `0`

## Compatibility Vs V116 LTS

Compared against `outputs/formal/stage1_extended_selected_context_v116_qwen36_no_think_build4k_lme_s_full_aeac792/traces.jsonl`.

| metric | result |
|---|---:|
| joined records | `500` |
| changed prompts | `0/500` |
| changed evidence row ids | `0/500` |
| changed routes | `0/500` |
| avg context char delta | `0.0` |
| avg evidence row delta | `0.0` |
| avg selected-context materialized delta | `0.0` |
| selected-context state changed | `161/500` |

By route:

| route | n | changed prompts | changed row ids | selected-context applied V116/V125 |
|---|---:|---:|---:|---:|
| `current_state` | `22` | `0` | `0` | `0/0` |
| `fact_lookup` | `183` | `0` | `0` | `0/0` |
| `list_count` | `119` | `0` | `0` | `0/0` |
| `profile_preference` | `15` | `0` | `0` | `0/0` |
| `temporal_lookup` | `161` | `0` | `0` | `0/0` |

The `selected_context_changed_count=161` comes from trace/config state: V125 records the `temporal_lookup` route override as available, while V116 does not. In LongMemEval all 161 temporal records remain ineligible or unapplied, so this state difference has no prompt, row, or context effect.

## Boundary

This dry-run proves only LongMemEval retrieval/compiler prompt compatibility.

It does not prove a new full LongMemEval answer/judge result. V125 inherits the V121 `source_grounded_consistency_guard`, while the previous V116 LTS used the older `structured_evidence_mechanical` finalizer. V116 LongMemEval formal metrics had finalizer applied on `8/500` records, and V121 has a focused smoke check showing identical predictions on those 8 records.

## Decision

The LME compiler compatibility risk is cleared: V125 changes `0/500` prompts and `0/500` evidence row sets on LongMemEval.

This dry-run is now used as compatibility evidence for the V125 local LTS promotion, not as a new full LME rerun. The promotion decision is recorded in `experiments/diagnostic/stage1_route_scoped_local_evidence_unit_v125_lts_promotion.md`: V125 lowers goal risk #4 and partially lowers goal risk #3, while LME metrics are inherited from V116 by compatibility evidence.
