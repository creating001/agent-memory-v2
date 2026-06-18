# stage1_memory_source_interleave_v126 profile/state diagnostic

## Purpose

Test a conservative build-memory organization candidate that uses typed memory only as a source-backed ordering signal, not as reader evidence.

V126 inherits V125/V121. It keeps build, retrieval top-k, selected context, answer prompt, modal grounded inference, and source-grounded guard unchanged. The only new compiler behavior is route-scoped:

- `profile_preference`
- `current_state`

For those routes, `evidence_order=memory_source_interleave` preserves top retrieval anchors, then interleaves a small number of build-memory-linked raw source rows in original retrieval order. It does not expose typed memory text in the prompt and does not apply to `fact_lookup`, `list_count`, or `temporal_lookup`.

Prediction uses only question text, raw Memory Context, build-memory source backpointers, and prediction-time route. It uses no gold answers, judge output, benchmark labels, sample ids, row indices, test feedback, or sample-level rules.

## Config

- `configs/stage1_memory_source_interleave_v126_qwen36_no_think_build4k_cached.json`
- Answer cache namespace: `stage1_memory_source_interleave_v126_qwen36_no_think_build4k`
- Git commit: `88efe8b`
- Dirty status: dirty; includes v118-v126 configs/diagnostics and source changes for parser guard, source-grounded guard, route-scoped selected context, rerank filter, and memory-source interleave.

## Dry-Run Results

### LoCoMo

Compared against V125 dry-run:

| route | n | changed prompt | changed row ids | order-only changes | avg context char delta |
|---|---:|---:|---:|---:|---:|
| `current_state` | `4` | `4` | `4` | `4` | `-0.750` |
| `fact_lookup` | `882` | `0` | `0` | `0` | `0.000` |
| `list_count` | `270` | `0` | `0` | `0` | `0.000` |
| `profile_preference` | `46` | `46` | `46` | `45` | `-0.543` |
| `temporal_lookup` | `338` | `0` | `0` | `0` | `0.000` |

The first broad version also applied to `fact_lookup` and changed `929/1540` prompts, including `879/882` fact prompts. That was too close to the rejected V108 row-order risk, so the retained V126 config is profile/current only.

### LongMemEval-S

Compared against V116 traces:

| route | n | changed prompt | changed row ids | order-only changes | avg context char delta |
|---|---:|---:|---:|---:|---:|
| `current_state` | `22` | `7` | `7` | `4` | `-63.227` |
| `fact_lookup` | `183` | `0` | `0` | `0` | `0.000` |
| `list_count` | `119` | `0` | `0` | `0` | `0.000` |
| `profile_preference` | `15` | `5` | `5` | `3` | `+45.733` |
| `temporal_lookup` | `161` | `0` | `0` | `0` | `0.000` |

## Answer Diagnostics

### LoCoMo Profile/Current Route-All

- Input: `outputs/diagnostic_inputs/stage1_memory_source_interleave_v126_locomo_profile_state_route_all.jsonl`
- Predictions: `outputs/diagnostic/stage1_memory_source_interleave_v126_locomo_profile_state_route_all/predictions.jsonl`
- Traces: `outputs/diagnostic/stage1_memory_source_interleave_v126_locomo_profile_state_route_all/traces.jsonl`
- Samples: `50`
- Avg build/query tokens: `62479.100 / 6235.980`
- Build cache hit/miss/write: `405/0/0`
- Answer cache hit/miss/write: `0/50/50`
- Changed answers vs V125 route-only full subset: `21/50`

Lexical metrics only:

| predictions | exact | F1 | BLEU1 |
|---|---:|---:|---:|
| V125 same subset | `0.320000` | `0.526452` | `0.472298` |
| V126 | `0.360000` | `0.577031` | `0.522415` |

Exact gain/loss: `2/0`.

### LongMemEval-S Profile/Current Route-All

- Input: `outputs/diagnostic_inputs/stage1_memory_source_interleave_v126_lme_profile_state_route_all.jsonl`
- Predictions: `outputs/diagnostic/stage1_memory_source_interleave_v126_lme_profile_state_route_all/predictions.jsonl`
- Traces: `outputs/diagnostic/stage1_memory_source_interleave_v126_lme_profile_state_route_all/traces.jsonl`
- Samples: `37`
- Avg build/query tokens: `85852.243 / 6599.270`
- Build cache hit/miss/write: `245/0/0`
- Answer cache hit/miss/write: `0/37/37`
- Answer finalizer applied: `5`
- Changed answers vs V116 same subset: `18/37`

Lexical metrics only:

| predictions | exact | F1 | BLEU1 |
|---|---:|---:|---:|
| V116 same subset | `0.324324` | `0.558684` | `0.518824` |
| V126 | `0.324324` | `0.544108` | `0.502680` |

Exact gain/loss: `0/0`; F1/BLEU decreased on this small subset.

## Full Route-Only LoCoMo Artifact

To prepare a full diagnostic artifact without rerunning unchanged routes:

- Base predictions: V125 full route-only merge
- Override predictions: V126 LoCoMo profile/current route-all
- Allowed routes: `profile_preference,current_state`

Outputs:

- Predictions: `outputs/diagnostic/stage1_memory_source_interleave_v126_locomo_nonadv_full_route_only_merge/predictions.jsonl`
- Manifest: `experiments/diagnostic/stage1_memory_source_interleave_v126_locomo_nonadv_full_route_only_merge/manifest.json`
- Lexical metrics: `experiments/diagnostic/stage1_memory_source_interleave_v126_locomo_nonadv_full_route_only_merge/lexical_metrics.json`

Merge counts:

- base records: `1490`
- V126 override records: `50`
- total: `1540`

Full LoCoMo lexical metrics only:

| predictions | exact | F1 | BLEU1 |
|---|---:|---:|---:|
| V116 full | `0.236364` | `0.527409` | `0.474098` |
| V125 route-only full | `0.242857` | `0.535470` | `0.481605` |
| V126 route-only full | `0.244156` | `0.537112` | `0.483232` |

## Full Route-Only LongMemEval-S Artifact

To prepare the same full diagnostic artifact without rerunning unchanged routes:

- Base predictions: V116 full
- Override predictions: V126 LME profile/current route-all
- Allowed routes: `profile_preference,current_state`

Outputs:

- Predictions: `outputs/diagnostic/stage1_memory_source_interleave_v126_lme_s_full_route_only_merge/predictions.jsonl`
- Manifest: `experiments/diagnostic/stage1_memory_source_interleave_v126_lme_s_full_route_only_merge/manifest.json`
- Lexical metrics: `experiments/diagnostic/stage1_memory_source_interleave_v126_lme_s_full_route_only_merge/lexical_metrics.json`
- V116 same-run lexical metrics: `experiments/diagnostic/stage1_memory_source_interleave_v126_lme_s_full_route_only_merge/v116_full_lexical_metrics.json`

Merge counts:

- base records: `463`
- V126 override records: `37`
- total: `500`
- changed answers vs V116 full: `18/500`

Full LongMemEval-S lexical metrics only:

| predictions | exact | F1 | BLEU1 |
|---|---:|---:|---:|
| V116 full | `0.426000` | `0.631668` | `0.587792` |
| V126 route-only full | `0.426000` | `0.630589` | `0.586597` |

## Decision

Keep V126 as a narrow diagnostic candidate pending dual `deepseek-v4-flash` judge. Do not promote.

Reasoning:

- The profile/current-only scope is clean and small on both benchmarks.
- LoCoMo auxiliary lexical metrics are positive.
- LME exact is unchanged, but F1/BLEU decreased on both the small profile/current subset and the full route-only merge.
- Primary judge is missing because the current environment has no `DEEPSEEK_API_KEY`.

Next judge commands when the key is available:

```bash
python scripts/judge_predictions_dual_deepseek.py \
  --predictions outputs/diagnostic/stage1_memory_source_interleave_v126_locomo_nonadv_full_route_only_merge/predictions.jsonl \
  --labels outputs/prepare_locomo_non_adversarial/labels.jsonl \
  --output experiments/diagnostic/stage1_memory_source_interleave_v126_locomo_nonadv_full_route_only_merge/deepseek_dual_judge.json \
  --benchmark locomo \
  --workers 8 \
  --progress-every 50
```

If the LoCoMo full judge is positive, run LME profile/current dual judge before considering a formal full run.

```bash
python scripts/judge_predictions_dual_deepseek.py \
  --predictions outputs/diagnostic/stage1_memory_source_interleave_v126_lme_s_full_route_only_merge/predictions.jsonl \
  --labels outputs/prepare_longmemeval_s_cleaned/labels.jsonl \
  --output experiments/diagnostic/stage1_memory_source_interleave_v126_lme_s_full_route_only_merge/deepseek_dual_judge.json \
  --benchmark longmemeval \
  --workers 8 \
  --progress-every 50
```
