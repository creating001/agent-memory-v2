# stage1_fact_tail_snippet_budget_v134 diagnostic

## Purpose

Continue the V132 token-budget diagnosis without deleting raw evidence rows.

V132 proved that hard `fact_lookup` tail row pruning can reduce LoCoMo query cost, but it lost accuracy because it removed too many low-rank raw rows. V133/V134 instead keep the V129 selected row set and only compress text for low-priority direct retrieval rows.

This policy is clean and general:

- It uses only prediction-time information need, retrieval rank, question text, and raw row text.
- It does not use gold answers, judge output, benchmark labels, sample ids, row indices, test feedback, or sample-level rules.
- It does not expose build-memory text as answer evidence because `compiler.max_memory_records` remains `0`.

## Code Change

- Added compiler tail row text controls:
  - `tail_row_text_after_rank`
  - `tail_row_text_mode`
  - `tail_max_row_text_chars`
- Tail compression is prompt-rendering only. Row selection still uses the uncompressed row text budget, so the policy cannot admit extra rows by shrinking earlier rows.
- Added unit coverage in `src/tests/test_compiler.py`:
  - tail compression only applies after the configured direct-hit rank;
  - neighbor rows are not compressed by tail rank rules;
  - tail compression does not admit extra rows.

## Configs

V133:

- Config: `configs/stage1_fact_tail_snippet_budget_v133_qwen36_no_think_build4k_cached.json`
- Inherits: `configs/stage1_route_scoped_fact_profile_state_budget_v129_qwen36_no_think_build4k_cached.json`
- Fact route override:
  - `tail_row_text_after_rank = 40`
  - `tail_row_text_mode = query_snippet`
  - `tail_max_row_text_chars = 320`

V134:

- Config: `configs/stage1_fact_tail_snippet_budget_v134_qwen36_no_think_build4k_cached.json`
- Inherits V133, with only:
  - `tail_max_row_text_chars = 100`
- Answer cache namespace: `stage1_fact_tail_snippet_budget_v134_qwen36_no_think_build4k`
- Build cache: `outputs/cache/qwen36_no_think_build4k_memory_v102.sqlite`
- Git commit recorded by runs: `88efe8b`
- Dirty status: dirty; includes v118-v134 configs/diagnostics and source changes from the current exploration worktree.

## Dry-Run Results

Compared against V129 dry-run.

### LongMemEval-S

V133 and V134 both produce no change:

- changed prompt: `0/500`
- changed row set: `0/500`
- avg context chars: unchanged `19390.896`
- avg compiled evidence rows: unchanged `34.378`

This is expected because LongMemEval uses the long-turn top40 path and the tail policy starts after rank 40.

### LoCoMo V133

V133 is too conservative:

| route | n | changed prompt | changed row set | avg context char delta | avg row delta |
|---|---:|---:|---:|---:|---:|
| `fact_lookup` | `882` | `207` | `0` | `-8.552` | `0.000` |
| other routes | `658` | `0` | `0` | `0.000` | `0.000` |

Full average context chars: `17113.901 -> 17109.003`.

### LoCoMo V134

V134 preserves row coverage and gives a real token-budget reduction:

| route | n | changed prompt | changed row set | avg context char delta | avg row delta |
|---|---:|---:|---:|---:|---:|
| `fact_lookup` | `882` | `882` | `0` | `-611.409` | `0.000` |
| `current_state` | `4` | `0` | `0` | `0.000` | `0.000` |
| `list_count` | `270` | `0` | `0` | `0.000` | `0.000` |
| `profile_preference` | `46` | `0` | `0` | `0.000` | `0.000` |
| `temporal_lookup` | `338` | `0` | `0` | `0.000` | `0.000` |

Full dry-run metrics:

| config | avg context chars | avg compiled evidence rows |
|---|---:|---:|
| V129 | `17113.901` | `52.860` |
| V134 | `16763.730` | `52.860` |

LoCoMo fact route specifically:

| config | avg context chars | avg compiled evidence rows |
|---|---:|---:|
| V129 | `17637.014` | `55.851` |
| V134 | `17025.604` | `55.851` |

## Answer Diagnostics

Changed-prompt input:

- `outputs/diagnostic_inputs/stage1_fact_tail_snippet_budget_v134_locomo_fact_changed.jsonl`

LoCoMo fact changed subset:

| predictions | exact | F1 | BLEU1 |
|---|---:|---:|---:|
| V129 same 882 keys | `0.249433` | `0.550951` | `0.488438` |
| V134 | `0.253968` | `0.550460` | `0.490170` |

- Changed answers: `366/882`
- Exact gain/loss: `22/18`
- V134 avg build/query tokens: `62126.289 / 5910.726`
- Answer finalizer applied: `0`

Full LoCoMo route-only merge:

| predictions | exact | F1 | BLEU1 |
|---|---:|---:|---:|
| V129 full route-only | `0.245455` | `0.538048` | `0.483962` |
| V134 full route-only | `0.248052` | `0.537767` | `0.484954` |

- Merge counts: V134 fact override `882`, V129/base non-fact `658`, total `1540`
- Full changed answers: `352/1540`
- Exact gain/loss: `22/18`

## Outputs

- V133 LME dry-run traces: `outputs/diagnostic/stage1_fact_tail_snippet_budget_v133_lme_dry/traces.jsonl`
- V133 LoCoMo dry-run traces: `outputs/diagnostic/stage1_fact_tail_snippet_budget_v133_locomo_dry/traces.jsonl`
- V134 LME dry-run traces: `outputs/diagnostic/stage1_fact_tail_snippet_budget_v134_lme_dry/traces.jsonl`
- V134 LoCoMo dry-run traces: `outputs/diagnostic/stage1_fact_tail_snippet_budget_v134_locomo_dry/traces.jsonl`
- V134 LoCoMo fact predictions: `outputs/diagnostic/stage1_fact_tail_snippet_budget_v134_locomo_fact_changed/predictions.jsonl`
- V134 LoCoMo full merge predictions: `outputs/diagnostic/stage1_fact_tail_snippet_budget_v134_locomo_nonadv_full_route_only_merge/predictions.jsonl`
- V134 LoCoMo full lexical metrics: `experiments/diagnostic/stage1_fact_tail_snippet_budget_v134_locomo_nonadv_full_route_only_merge/lexical_metrics.json`

## Decision

V133 is rejected as too conservative.

V134 is kept as a narrow positive token-budget diagnostic, not an LTS replacement yet:

- Clean: it uses only route/rank/question/raw row text and preserves row set.
- Cost: LoCoMo fact changed subset avg query tokens drops to `5910.726`, under the 6K target.
- Accuracy proxy: full LoCoMo route-only lexical exact improves `0.245455 -> 0.248052`, with exact gain/loss `22/18`; F1 is nearly flat but slightly negative.
- Risk: the effect is narrow and only lexical so far. Dual `deepseek-v4-flash` judge is still required before considering promotion.

Next recommendation: run dual flash judge for the V134 LoCoMo fact subset and full route-only merge. If judge agrees with the lexical positive, consider testing an adjacent `tail_max_row_text_chars=80` diagnostic; otherwise keep V134 as a token-budget note and move back to evidence organization rather than more compression.
