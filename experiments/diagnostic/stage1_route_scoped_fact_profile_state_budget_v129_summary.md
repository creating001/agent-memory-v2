# stage1_route_scoped_fact_profile_state_budget_v129 diagnostic

## Purpose

Test a route-scoped compiler evidence budget as a clean way to reduce context noise and query tokens without changing retrieval recall.

V129 inherits V127. It keeps build memory, retrieval top-k, granularity profiles, selected context, `memory_source_interleave`, superseded source-chain activation, answer prompt, and source-grounded guard unchanged. The only prediction-time change is:

- `compiler.route_overrides.fact_lookup.max_evidence_chars = 17000`
- `compiler.route_overrides.profile_preference.max_evidence_chars = 17000`
- `compiler.route_overrides.current_state.max_evidence_chars = 17000`

It intentionally does not touch `temporal_lookup` or `list_count`, which are more coverage-sensitive.

Prediction uses no gold answers, judge output, benchmark labels, sample ids, row indices, test feedback, or sample-level shortcuts.

## Config

- Config: `configs/stage1_route_scoped_fact_profile_state_budget_v129_qwen36_no_think_build4k_cached.json`
- Inherits: `configs/stage1_superseded_source_chain_v127_qwen36_no_think_build4k_cached.json`
- Answer cache namespace: `stage1_route_scoped_fact_profile_state_budget_v129_qwen36_no_think_build4k`
- Build cache: `outputs/cache/qwen36_no_think_build4k_memory_v102.sqlite`
- Git commit recorded by runs: `88efe8b`
- Dirty status: dirty; includes v118-v129 configs/diagnostics and source changes from the current exploration worktree.

## Dry-Run Results

### LongMemEval-S

Compared against V127 dry-run:

| route | n | changed prompt | changed rows | avg context char delta | avg row delta |
|---|---:|---:|---:|---:|---:|
| `current_state` | `22` | `11` | `11` | `-702.8` | `-0.91` |
| `fact_lookup` | `183` | `100` | `100` | `-879.5` | `-0.87` |
| `list_count` | `119` | `0` | `0` | `0.0` | `0.00` |
| `profile_preference` | `15` | `7` | `7` | `-863.7` | `-0.53` |
| `temporal_lookup` | `161` | `0` | `0` | `0.0` | `0.00` |
| total | `500` | `118` | `118` | `-378.7` | `-0.37` |

Full dry-run metrics:

| config | avg context chars | avg compiled evidence rows |
|---|---:|---:|
| V127 | `19769.610` | `34.752` |
| V129 | `19390.896` | `34.378` |

### LoCoMo

Compared against V127 dry-run:

| route | n | changed prompt | changed rows | avg context char delta | avg row delta |
|---|---:|---:|---:|---:|---:|
| `current_state` | `4` | `0` | `0` | `0.0` | `0.00` |
| `fact_lookup` | `882` | `553` | `553` | `-477.4` | `-2.14` |
| `list_count` | `270` | `0` | `0` | `0.0` | `0.00` |
| `profile_preference` | `46` | `28` | `28` | `-446.2` | `-1.93` |
| `temporal_lookup` | `338` | `0` | `0` | `0.0` | `0.00` |
| total | `1540` | `581` | `581` | `-286.7` | `-1.28` |

Full dry-run metrics:

| config | avg context chars | avg compiled evidence rows |
|---|---:|---:|
| V127 | `17400.642` | `54.143` |
| V129 | `17113.901` | `52.860` |

## Answer Diagnostics

### LongMemEval-S Changed Prompts

Changed-prompt input:

- `outputs/diagnostic_inputs/stage1_route_scoped_fact_profile_state_budget_v129_lme_changed_prompts.jsonl`

| predictions | exact | F1 | BLEU1 |
|---|---:|---:|---:|
| V127 same 118 keys | `0.500000` | `0.698692` | `0.663354` |
| V129 | `0.508475` | `0.708981` | `0.674389` |

- Changed answers: `34/118`
- Exact gain/loss: `5/4`
- Same 118-key dry-run context: `19480.7 -> 17875.9` chars, `34.75 -> 33.16` evidence rows
- V129 avg build/query tokens: `85478.585 / 5686.864`
- Answer finalizer applied: `11`

Full LME route-only merge:

| predictions | exact | F1 | BLEU1 |
|---|---:|---:|---:|
| V127 full route-only | `0.428000` | `0.633744` | `0.589603` |
| V129 full route-only | `0.430000` | `0.636173` | `0.592207` |

Full changed answers: `34/500`; exact gain/loss `5/4`.

### LoCoMo Changed Prompts

Changed-prompt input:

- `outputs/diagnostic_inputs/stage1_route_scoped_fact_profile_state_budget_v129_locomo_changed_prompts.jsonl`

| predictions | exact | F1 | BLEU1 |
|---|---:|---:|---:|
| V127 same 581 keys | `0.247849` | `0.544244` | `0.481668` |
| V129 | `0.251291` | `0.545236` | `0.482139` |

- Changed answers: `225/581`
- Exact gain/loss: `9/7`
- Same 581-key dry-run context: `18871.6 -> 18111.5` chars, `56.85 -> 53.45` evidence rows
- V129 avg build/query tokens: `61597.389 / 6112.337`
- Answer finalizer applied: `0`

Full LoCoMo route-only merge:

| predictions | exact | F1 | BLEU1 |
|---|---:|---:|---:|
| V127 full route-only | `0.244156` | `0.537674` | `0.483784` |
| V129 full route-only | `0.245455` | `0.538048` | `0.483962` |

Full changed answers: `225/1540`; exact gain/loss `9/7`.

## Outputs

- LME dry-run traces: `outputs/diagnostic/stage1_route_scoped_fact_profile_state_budget_v129_lme_dry/traces.jsonl`
- LoCoMo dry-run traces: `outputs/diagnostic/stage1_route_scoped_fact_profile_state_budget_v129_locomo_dry/traces.jsonl`
- LME changed-prompt predictions: `outputs/diagnostic/stage1_route_scoped_fact_profile_state_budget_v129_lme_changed_prompts/predictions.jsonl`
- LoCoMo changed-prompt predictions: `outputs/diagnostic/stage1_route_scoped_fact_profile_state_budget_v129_locomo_changed_prompts/predictions.jsonl`
- LME full merge predictions: `outputs/diagnostic/stage1_route_scoped_fact_profile_state_budget_v129_lme_s_full_route_only_merge/predictions.jsonl`
- LoCoMo full merge predictions: `outputs/diagnostic/stage1_route_scoped_fact_profile_state_budget_v129_locomo_nonadv_full_route_only_merge/predictions.jsonl`
- LME full lexical metrics: `experiments/diagnostic/stage1_route_scoped_fact_profile_state_budget_v129_lme_s_full_route_only_merge/lexical_metrics.json`
- LoCoMo full lexical metrics: `experiments/diagnostic/stage1_route_scoped_fact_profile_state_budget_v129_locomo_nonadv_full_route_only_merge/lexical_metrics.json`

## Decision

Keep as a narrow positive token-budget diagnostic candidate; do not upgrade to LTS.

Reasoning:

- The rule is clean and general: it is keyed only by prediction-time information need and uses no benchmark labels, gold answers, sample ids, row indices, or test feedback.
- It does not affect `temporal_lookup` or `list_count`.
- Lexical signals are consistently small-positive on both benchmarks: LME full exact `+0.002`, LoCoMo full exact `+0.001299`.
- Token/context savings are real but modest. LME changed subset gets below 6K query tokens, but LoCoMo changed subset remains above the 6K normal target at `6112.337`.
- If dual judge budget becomes available, V129 can be compared with V125/V126/V127, but this is not strong enough by itself to replace V116 or to claim the top-k/context-noise issue is solved.

Next recommendation: try a less blunt evidence-density policy or rerank-assisted tail pruning that preserves high-support rows and removes low-marginal rows, rather than lowering a fixed char budget further.
