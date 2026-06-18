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
- Dual judge: `experiments/diagnostic/stage1_route_scoped_local_evidence_unit_v125_locomo_nonadv_full_route_only_merge/deepseek_dual_judge.json`
- Judge comparison vs V116 LTS: `experiments/diagnostic/stage1_route_scoped_local_evidence_unit_v125_locomo_nonadv_full_route_only_merge/deepseek_judge_comparison_vs_v116_lts.json`

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

## Dual Judge

Dual `deepseek-v4-flash` judge on the route-only full merge:

| predictions | strict | lenient | strict correct | lenient correct |
|---|---:|---:|---:|---:|
| V116 current LTS full | `0.779221` | `0.807143` | `1200/1540` | `1243/1540` |
| V125 route-only merge | `0.789610` | `0.807792` | `1216/1540` | `1244/1540` |

This full diagnostic is strict-positive but lenient-marginal:

- strict delta: `+16/1540`, accuracy `+0.010390`
- lenient delta: `+1/1540`, accuracy `+0.000649`
- temporal subset paired judge is stronger evidence for the route change itself: strict `+7`, lenient `+9` on the changed temporal keys

## Decision

This diagnostic established the LoCoMo full route-only metric for V125. The metric is strict-positive and lenient-marginal relative to V116:

- strict delta: `+16/1540`
- lenient delta: `+1/1540`

The original diagnostic conclusion treated V125 as a promising candidate only, because the earlier LTS rule required stronger full benchmark proof before promotion. That conclusion is superseded by `experiments/diagnostic/stage1_route_scoped_local_evidence_unit_v125_lts_promotion.md`: under the updated local LTS rule, one or more of the five goal risks can justify promotion if unresolved risks are documented. V125 is now the current local LTS because it lowers goal risk #4, partially lowers goal risk #3, and has positive LoCoMo dual-judge evidence. LongMemEval remains inherited by compatibility evidence, not by a new full answer/judge rerun.
