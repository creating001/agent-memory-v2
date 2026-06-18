# stage1_long_profile_profile_state_selected_context_v128 diagnostic

## Purpose

Test a narrower replacement for the long-turn selected-context blanket disable.

V128 inherits V127. It keeps build memory, retrieval top-k, `memory_source_interleave`, superseded source-chain retrieval, answer prompt, and source-grounded guard unchanged. The only change is in the `long_turn_precision` granularity profile: instead of `selected_context.enabled=false`, it enables existing per-row selected context only for question-derived `profile_preference` and `current_state` routes.

This tests whether the long/short selected-context split can be decomposed into route plus row-level checks (`require_anaphora`, `max_center_chars`) without applying LoCoMo-style selected context to all LongMemEval routes.

Prediction uses no gold answers, judge output, benchmark labels, sample ids, row indices, test feedback, or sample-level shortcuts.

## Config

- Config: `configs/stage1_long_profile_profile_state_selected_context_v128_qwen36_no_think_build4k_cached.json`
- Inherits: `configs/stage1_superseded_source_chain_v127_qwen36_no_think_build4k_cached.json`
- Answer cache namespace: `stage1_long_profile_profile_state_selected_context_v128_qwen36_no_think_build4k`
- Build cache: `outputs/cache/qwen36_no_think_build4k_memory_v102.sqlite`
- Git commit recorded by runs: `88efe8b`
- Dirty status: dirty; includes v118-v128 configs/diagnostics and source changes from the current exploration worktree.

## Dry-Run Results

### LongMemEval-S

Compared against V127 dry-run:

| route | n | changed prompt | changed rows | selected eligible | selected applied | avg context char delta |
|---|---:|---:|---:|---:|---:|---:|
| `current_state` | `22` | `22` | `16` | `22` | `22` | `+491.591` |
| `fact_lookup` | `183` | `0` | `0` | `0` | `0` | `0.000` |
| `list_count` | `119` | `0` | `0` | `0` | `0` | `0.000` |
| `profile_preference` | `15` | `15` | `9` | `15` | `15` | `+324.133` |
| `temporal_lookup` | `161` | `0` | `0` | `0` | `0` | `0.000` |
| total | `500` | `37` | `25` | `37` | `37` | `+31.354` |

This is much narrower than V122 (`317/500` changed prompts), while still replacing the full long-profile selected-context disable with route-scoped row-level behavior.

### LoCoMo

Compared against V127 dry-run:

- changed prompt: `0/1540`
- changed rows: `0/1540`
- avg context char delta: `0.000`

The v128 long-profile change does not affect the short-turn LoCoMo path.

## Answer Diagnostics

Changed-prompt input:

- `outputs/diagnostic_inputs/stage1_long_profile_profile_state_selected_context_v128_lme_changed_prompts.jsonl`

LME changed-prompt subset:

| predictions | exact | F1 | BLEU1 |
|---|---:|---:|---:|
| V127 same 37 keys | `0.351351` | `0.586746` | `0.543303` |
| V128 | `0.351351` | `0.599866` | `0.555475` |

- Changed answers: `16/37`
- Exact gain/loss: `0/0`
- Avg build/query tokens: `85852.243 / 6480.730`
- Answer finalizer applied: `4`

Full LME route-only merge:

| predictions | exact | F1 | BLEU1 |
|---|---:|---:|---:|
| V127 full route-only | `0.428000` | `0.633744` | `0.589603` |
| V128 full route-only | `0.428000` | `0.634715` | `0.590504` |

Full changed answers: `16/500`; exact gain/loss `0/0`.

## Outputs

- LME dry-run traces: `outputs/diagnostic/stage1_long_profile_profile_state_selected_context_v128_lme_dry/traces.jsonl`
- LoCoMo dry-run traces: `outputs/diagnostic/stage1_long_profile_profile_state_selected_context_v128_locomo_dry/traces.jsonl`
- LME changed-prompt predictions: `outputs/diagnostic/stage1_long_profile_profile_state_selected_context_v128_lme_changed_prompts/predictions.jsonl`
- LME full merge predictions: `outputs/diagnostic/stage1_long_profile_profile_state_selected_context_v128_lme_s_full_route_only_merge/predictions.jsonl`
- LME full lexical metrics: `experiments/diagnostic/stage1_long_profile_profile_state_selected_context_v128_lme_s_full_route_only_merge/lexical_metrics.json`

## Decision

Reject as an accuracy candidate; keep only as structural evidence for the selected-context audit.

Reasoning:

- The design is clean and more general than the original dataset-shaped long/short selected-context split.
- It successfully narrows V122 from `317/500` changed LME prompts to `37/500`, with zero LoCoMo impact.
- However, it does not improve exact accuracy on the changed subset or full merge, and raises LME changed-subset avg query tokens to `6480.730`, above the 6K normal target.
- Do not spend DeepSeek judge budget on V128 unless later evidence suggests F1/BLEU-only improvements correspond to judge gains.
