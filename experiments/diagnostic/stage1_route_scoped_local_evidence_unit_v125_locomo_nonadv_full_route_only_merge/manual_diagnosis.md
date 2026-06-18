# stage1_route_scoped_local_evidence_unit_v125_locomo_nonadv_full_route_only_merge

## Purpose

Prepare a full LoCoMo diagnostic prediction artifact that isolates the V125 temporal route-scoped selected-context change from the separate dirty-worktree `json_answer` parser/cache-hit repair effect.

This is an offline merge of completed prediction outputs:

- V116 full predictions for all non-temporal records
- V125 temporal route-all predictions for temporal records

The merge key set comes from prediction-time route traces only. No labels, judge outputs, benchmark categories, sample ids, row indices, test feedback, or sample-level rules are used.

## Inputs

- V116 full predictions: `outputs/formal/stage1_extended_selected_context_v116_qwen36_no_think_build4k_locomo_nonadv_full_aeac792/predictions.jsonl`
- V116 route trace for audit: `outputs/formal/stage1_extended_selected_context_v116_qwen36_no_think_build4k_locomo_nonadv_full_aeac792/traces.jsonl`
- V125 temporal predictions: `outputs/diagnostic/stage1_route_scoped_local_evidence_unit_v125_locomo_temporal_route_all/predictions.jsonl`

## Outputs

- Predictions: `outputs/diagnostic/stage1_route_scoped_local_evidence_unit_v125_locomo_nonadv_full_route_only_merge/predictions.jsonl`
- Manifest: `experiments/diagnostic/stage1_route_scoped_local_evidence_unit_v125_locomo_nonadv_full_route_only_merge/manifest.json`
- Lexical metrics: `experiments/diagnostic/stage1_route_scoped_local_evidence_unit_v125_locomo_nonadv_full_route_only_merge/lexical_metrics.json`

Reproduction command:

```bash
python scripts/merge_predictions_by_trace_route.py \
  --base-predictions outputs/formal/stage1_extended_selected_context_v116_qwen36_no_think_build4k_locomo_nonadv_full_aeac792/predictions.jsonl \
  --override-predictions outputs/diagnostic/stage1_route_scoped_local_evidence_unit_v125_locomo_temporal_route_all/predictions.jsonl \
  --traces outputs/formal/stage1_extended_selected_context_v116_qwen36_no_think_build4k_locomo_nonadv_full_aeac792/traces.jsonl \
  --route temporal_lookup \
  --output outputs/diagnostic/stage1_route_scoped_local_evidence_unit_v125_locomo_nonadv_full_route_only_merge/predictions.jsonl \
  --manifest-output experiments/diagnostic/stage1_route_scoped_local_evidence_unit_v125_locomo_nonadv_full_route_only_merge/manifest.json
```

## Merge Counts

| source | count |
|---|---:|
| V116 non-temporal/base predictions | `1202` |
| V125 temporal predictions | `338` |
| route mismatch | `0` |
| total | `1540` |

Changed answers vs V116:

- total changed `127/1540`
- by route: `temporal_lookup=127`
- non-temporal changed `0`

Exact-match buckets vs V116:

| bucket | count |
|---|---:|
| both exact | `360` |
| both not exact | `1164` |
| gain exact | `13` |
| loss exact | `3` |

Lexical metrics only, not the method-selection metric:

| predictions | exact | F1 | BLEU1 |
|---|---:|---:|---:|
| V116 full | `0.236364` | `0.527409` | `0.474098` |
| V125 route-only merge | `0.242857` | `0.535470` | `0.481605` |
| V125 full cached with parser repair confound | `0.242857` | `0.535751` | `0.481794` |

## Decision

Use this route-only merge as the preferred full diagnostic artifact for later dual `deepseek-v4-flash` judge, because it isolates V125 temporal selected-context behavior. The earlier full cached artifact remains useful for parser-guard diagnostics but is not a pure V125 route-only result.

When `DEEPSEEK_API_KEY` is available, run:

```bash
python scripts/judge_predictions_dual_deepseek.py \
  --predictions outputs/diagnostic/stage1_route_scoped_local_evidence_unit_v125_locomo_nonadv_full_route_only_merge/predictions.jsonl \
  --labels outputs/prepare_locomo_non_adversarial/labels.jsonl \
  --output experiments/diagnostic/stage1_route_scoped_local_evidence_unit_v125_locomo_nonadv_full_route_only_merge/deepseek_dual_judge.json \
  --benchmark locomo \
  --workers 8 \
  --progress-every 50
```
