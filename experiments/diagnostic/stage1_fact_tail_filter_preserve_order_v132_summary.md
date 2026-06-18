# stage1_fact_tail_filter_preserve_order_v132 diagnostic

## Purpose

Test whether source-backed tail pruning can reduce LoCoMo `fact_lookup` context noise without the order-only drift caused by `memory_source_interleave`.

This diagnostic follows V129:

- V129 lowered route-scoped compiler context for `fact_lookup` / `profile_preference` / `current_state` to `17000` chars and was small-positive but did not fully solve LoCoMo query budget.
- V130 tried `memory_source_interleave` for `fact_lookup` with `source_anchor_keep=32` and `source_anchor_memory_rows=4`; dry-run showed LoCoMo prompt changed `879/882` fact rows with no context benefit.
- V131 narrowed that to `source_anchor_keep=40` and `source_anchor_memory_rows=1`; dry-run still changed `821/882` LoCoMo fact prompts because the same selected rows were reordered.
- V132 adds a new compiler evidence order, `memory_tail_filter_preserve_order`: select retrieval anchors plus a small number of memory-linked tail rows, then preserve original retrieval order in the final prompt.

V132 uses no gold answers, judge output, benchmark labels, sample ids, row indices, test feedback, or sample-level shortcuts. Build-memory text is not exposed as answer evidence because `compiler.max_memory_records` remains `0`; memory only selects raw source rows.

## Code Change

- Added `memory_tail_filter_preserve_order` to `src/memory/compiler.py`.
- Added unit coverage in `src/tests/test_compiler.py` proving it can include a memory-linked tail row while preserving retrieval order.

## Config

- Config: `configs/stage1_fact_tail_filter_preserve_order_v132_qwen36_no_think_build4k_cached.json`
- Inherits: `configs/stage1_route_scoped_fact_profile_state_budget_v129_qwen36_no_think_build4k_cached.json`
- Fact route override:
  - `evidence_order = memory_tail_filter_preserve_order`
  - `source_anchor_keep = 40`
  - `source_anchor_memory_rows = 1`
  - `source_anchor_per_session = 1`
- Answer cache namespace: `stage1_fact_tail_filter_preserve_order_v132_qwen36_no_think_build4k`
- Build cache: `outputs/cache/qwen36_no_think_build4k_memory_v102.sqlite`
- Git commit recorded by runs: `88efe8b`
- Dirty status: dirty; includes v118-v132 configs/diagnostics and source changes from the current exploration worktree.

## Dry-Run Results

Compared against V129 dry-run:

### LongMemEval-S

No change:

- changed prompt: `0/500`
- changed rows: `0/500`
- avg context chars: unchanged `19390.896`
- avg compiled evidence rows: unchanged `34.378`

This is expected because LongMemEval uses the long-turn top40 path and V132 keeps `40` retrieval anchors.

### LoCoMo

Only `fact_lookup` changed:

| route | n | changed prompt | changed row set | avg context char delta | avg row delta |
|---|---:|---:|---:|---:|---:|
| `fact_lookup` | `882` | `882` | `882` | `-2958.9` | `-14.86` |
| `current_state` | `4` | `0` | `0` | `0.0` | `0.00` |
| `list_count` | `270` | `0` | `0` | `0.0` | `0.00` |
| `profile_preference` | `46` | `0` | `0` | `0.0` | `0.00` |
| `temporal_lookup` | `338` | `0` | `0` | `0.0` | `0.00` |

Full dry-run metrics:

| config | avg context chars | avg compiled evidence rows |
|---|---:|---:|
| V129 | `17113.901` | `52.860` |
| V132 | `15419.230` | `44.352` |

LoCoMo fact route specifically:

| config | avg context chars | avg compiled evidence rows |
|---|---:|---:|
| V129 | `17637.0` | `55.85` |
| V132 | `14678.1` | `41.00` |

## Answer Diagnostics

Changed-prompt input:

- `outputs/diagnostic_inputs/stage1_fact_tail_filter_preserve_order_v132_locomo_fact_changed.jsonl`

LoCoMo fact changed subset:

| predictions | exact | F1 | BLEU1 |
|---|---:|---:|---:|
| V129 same 882 keys | `0.249433` | `0.550951` | `0.488438` |
| V132 | `0.241497` | `0.536504` | `0.476871` |

- Changed answers: `374/882`
- Exact gain/loss: `14/21`
- Same 882-key dry-run context: `17637.0 -> 14678.1` chars
- Same 882-key dry-run evidence rows: `55.85 -> 41.00`
- V132 avg build/query tokens: `62126.289 / 5115.770`
- Answer finalizer applied: `0`

Full LoCoMo route-only merge:

| predictions | exact | F1 | BLEU1 |
|---|---:|---:|---:|
| V129 full route-only | `0.245455` | `0.538048` | `0.483962` |
| V132 full route-only | `0.240909` | `0.529774` | `0.477337` |

Full changed answers: `374/1540`; exact gain/loss `14/21`.

## Outputs

- V130 LME dry-run traces: `outputs/diagnostic/stage1_fact_source_interleave_budget_v130_lme_dry/traces.jsonl`
- V130 LoCoMo dry-run traces: `outputs/diagnostic/stage1_fact_source_interleave_budget_v130_locomo_dry/traces.jsonl`
- V131 LME dry-run traces: `outputs/diagnostic/stage1_conservative_fact_tail_source_interleave_v131_lme_dry/traces.jsonl`
- V131 LoCoMo dry-run traces: `outputs/diagnostic/stage1_conservative_fact_tail_source_interleave_v131_locomo_dry/traces.jsonl`
- V132 LME dry-run traces: `outputs/diagnostic/stage1_fact_tail_filter_preserve_order_v132_lme_dry/traces.jsonl`
- V132 LoCoMo dry-run traces: `outputs/diagnostic/stage1_fact_tail_filter_preserve_order_v132_locomo_dry/traces.jsonl`
- V132 LoCoMo fact predictions: `outputs/diagnostic/stage1_fact_tail_filter_preserve_order_v132_locomo_fact_changed/predictions.jsonl`
- V132 LoCoMo full merge predictions: `outputs/diagnostic/stage1_fact_tail_filter_preserve_order_v132_locomo_nonadv_full_route_only_merge/predictions.jsonl`
- V132 LoCoMo full lexical metrics: `experiments/diagnostic/stage1_fact_tail_filter_preserve_order_v132_locomo_nonadv_full_route_only_merge/lexical_metrics.json`

## Decision

Reject as an accuracy candidate.

Reasoning:

- V132 is clean and solves the order-only drift problem from V130/V131.
- It substantially reduces LoCoMo fact query cost: changed-subset avg query tokens `5115.770`, with fact context chars reduced by `2958.9`.
- But it removes too many fact rows (`55.85 -> 41.00`) and produces a clear lexical regression: exact gain/loss `14/21`, full LoCoMo route-only exact `0.245455 -> 0.240909`.
- This confirms that fact_lookup still needs broader raw evidence coverage than a hard top40-plus-one tail filter.

Next recommendation: do not continue hard row-count tail pruning on fact_lookup. If reducing top-k noise further, use softer evidence density signals: keep all retrieval anchors but compress long low-support rows, or use rerank/memory as a row-text budget signal rather than as a row deletion signal.
