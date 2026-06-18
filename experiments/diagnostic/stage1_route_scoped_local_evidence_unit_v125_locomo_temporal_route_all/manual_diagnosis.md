# stage1_route_scoped_local_evidence_unit_v125 diagnosis

## Purpose

Evaluate whether the rejected V124 broad local evidence expansion can be narrowed into a clean route-scoped temporal local evidence unit.

V125 inherits V121/V116 and only changes `retrieval.selected_context.route_overrides.temporal_lookup`: temporal questions may materialize a small same-session before/after window around up to four short anaphoric center rows. Fact/list/profile selected context remains unchanged.

The prediction path uses question text, raw retrieved turns, same-session visible turn order, and prediction-time `information_need`. It does not use gold answers, judge output, benchmark labels, sample ids, row indices, test feedback, or sample-level rules.

## Dry-Run Scope Check

- Config: `configs/stage1_route_scoped_local_evidence_unit_v125_qwen36_no_think_build4k_cached.json`
- Dry-run output: `outputs/diagnostic/stage1_route_scoped_local_evidence_unit_v125_locomo_dry/`
- Baseline traces: `outputs/formal/stage1_extended_selected_context_v116_qwen36_no_think_build4k_locomo_nonadv_full_aeac792/traces.jsonl`
- Mode: null answerer compile dry-run; no answer LLM calls

Delta vs V116:

| route | n | changed prompt | changed evidence row ids | avg context char delta | avg evidence row delta |
|---|---:|---:|---:|---:|---:|
| `current_state` | `4` | `0` | `0` | `0.0` | `0.0` |
| `fact_lookup` | `882` | `0` | `0` | `0.0` | `0.0` |
| `list_count` | `270` | `0` | `0` | `0.0` | `0.0` |
| `profile_preference` | `46` | `0` | `0` | `0.0` | `0.0` |
| `temporal_lookup` | `338` | `338` | `0` | `+1688.524` | `0.0` |

Selected context:

- V116 applied `1198/1540`; V125 applied `1536/1540`.
- Route override applied exactly `338/338` temporal samples.
- Materialized selected-context rows: V116 `7188`, V125 `8540`.
- V124 broad expansion had temporal avg context delta `+6077.1`; V125 reduces this to `+1688.524` and leaves non-temporal prompts unchanged.

## Temporal Answer Diagnostic

- Input: `outputs/diagnostic_inputs/stage1_route_scoped_local_evidence_unit_v125_locomo_temporal_route_all.jsonl`
- Predictions: `outputs/diagnostic/stage1_route_scoped_local_evidence_unit_v125_locomo_temporal_route_all/predictions.jsonl`
- Traces: `outputs/diagnostic/stage1_route_scoped_local_evidence_unit_v125_locomo_temporal_route_all/traces.jsonl`
- Metrics: `experiments/diagnostic/stage1_route_scoped_local_evidence_unit_v125_locomo_temporal_route_all/metrics.json`

Runner metrics:

- Samples: `338`
- Avg build/query tokens: `60931.935 / 5395.908`
- Build cache: hit/miss/write `2680/0/0`
- Answer cache: hit/miss/write `1/337/337`
- Selected-context applied: `338/338`, avg materialized rows `4.0`
- Answer finalizer applied: `0`
- Answer changed vs V116 same subset: `127/338`

Fresh paired dual flash judge on the same 338 temporal keys:

| predictions | strict | lenient | strict correct | lenient correct |
|---|---:|---:|---:|---:|
| V116 same subset | `0.772189` | `0.786982` | `261/338` | `266/338` |
| V125 temporal subset | `0.792899` | `0.813609` | `268/338` | `275/338` |

Paired judge gain/loss:

- strict `19/12`, net `+7`
- lenient `19/10`, net `+9`
- comparison and changed records: `experiments/diagnostic/stage1_route_scoped_local_evidence_unit_v125_locomo_temporal_route_all/paired_judge_comparison_vs_v116.json`

Lexical metrics only, not the method-selection metric:

| predictions | exact | F1 | BLEU1 |
|---|---:|---:|---:|
| V116 temporal subset | `0.186391` | `0.468985` | `0.436853` |
| V125 temporal subset | `0.215976` | `0.505710` | `0.471056` |

Exact-match changed-answer diagnostic:

- exact gain/loss: `13/3`
- unchanged exact correct: `59`
- unchanged exact wrong: `263`

## Full Cached Diagnostic

To prepare a full prediction artifact for later judge, the V125 answer cache was seeded from V116 prediction traces for identical prompts, then the full LoCoMo input was run with the real V125 config.

- Full cached predictions: `outputs/diagnostic/stage1_route_scoped_local_evidence_unit_v125_locomo_nonadv_full_cached/predictions.jsonl`
- Full cached traces: `outputs/diagnostic/stage1_route_scoped_local_evidence_unit_v125_locomo_nonadv_full_cached/traces.jsonl`
- Full cached metrics: `experiments/diagnostic/stage1_route_scoped_local_evidence_unit_v125_locomo_nonadv_full_cached/metrics.json`

Runner metrics:

- Avg build/query tokens: `62015.574 / 6058.560`
- Build cache: hit/miss/write `12411/0/0`
- Embedding cache: hit/miss `7422/0`
- Answer cache: hit/miss/write `1540/0/0`

Changed answers vs V116 full:

- total changed `131/1540`
- `temporal_lookup`: `127`
- non-temporal: `4`

The four non-temporal differences are not caused by V125 route-scoped selected context. They come from the general `json_answer` parser/cache-hit repair added in the same dirty worktree, which salvages old malformed cached JSON answers. Therefore the full cached run is useful as a diagnostic artifact, but it is not a pure V125 route-only formal result.

Full lexical metrics only:

| predictions | exact | F1 | BLEU1 |
|---|---:|---:|---:|
| V116 full | `0.236364` | `0.527409` | `0.474098` |
| V125 full cached | `0.242857` | `0.535751` | `0.481794` |

## Route-Only Full Merge

To isolate the V125 temporal selected-context change from the parser-guard effect, a separate full prediction artifact was assembled offline from completed predictions:

- V116 full predictions for non-temporal records
- V125 temporal route-all predictions for temporal records

This merge uses only prediction-time outputs and route traces. It reads no labels or judge output.

- Predictions: `outputs/diagnostic/stage1_route_scoped_local_evidence_unit_v125_locomo_nonadv_full_route_only_merge/predictions.jsonl`
- Manifest: `experiments/diagnostic/stage1_route_scoped_local_evidence_unit_v125_locomo_nonadv_full_route_only_merge/manifest.json`
- Manual diagnosis: `experiments/diagnostic/stage1_route_scoped_local_evidence_unit_v125_locomo_nonadv_full_route_only_merge/manual_diagnosis.md`

Merge counts:

- V116/base records: `1202`
- V125 temporal records: `338`
- route mismatch: `0`
- changed answers vs V116: `127/1540`, all `temporal_lookup`
- exact gain/loss: `13/3`

Route-only full lexical metrics only:

| predictions | exact | F1 | BLEU1 |
|---|---:|---:|---:|
| V116 full | `0.236364` | `0.527409` | `0.474098` |
| V125 route-only merge | `0.242857` | `0.535470` | `0.481605` |

## Decision

Keep V125 as a promising diagnostic candidate, not as LTS yet.

Evidence so far:

- clean/general scope check passed: non-temporal prompts and evidence rows are unchanged in dry-run
- cost is acceptable for LoCoMo: full cached avg query tokens `6058.560`, slightly over the 6K normal target but far below the 8K diagnostic threshold
- lexical metrics are positive on temporal subset and route-only full merge, but remain diagnostic only
- primary paired temporal dual judge is positive: strict `+7`, lenient `+9`
- full route-only dual judge is strict-positive but lenient-marginal against current v116 LTS; see `experiments/diagnostic/stage1_route_scoped_local_evidence_unit_v125_locomo_nonadv_full_route_only_merge/manual_diagnosis.md`
- LME compiler compatibility passed in null-answer dry-run: `0/500` prompt changes, `0/500` evidence-row changes, route unchanged, avg context delta `0.0`; see `experiments/diagnostic/stage1_route_scoped_local_evidence_unit_v125_lme_dry/manual_diagnosis.md`

Next step: inspect temporal gain/loss badcases and prove answer/finalizer compatibility on LongMemEval before considering a formal full run. V125 is not a new LTS yet because LTS requires fewer risk points and better full dual judge accuracy across the target benchmarks.
