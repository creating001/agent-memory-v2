# stage1_superseded_source_chain_v127 diagnostic

## Purpose

Test whether build memory can support source-backed update/conflict chains without exposing typed memory text to the reader.

V127 inherits V126. It keeps V116 build, retrieval top-k, granularity profiles, selected context, modal grounded inference, answer prompt, source-grounded guard, and `memory_source_interleave` compiler behavior unchanged. The only new change is retrieval-side: allow superseded build-memory records to participate in memory BM25 for `profile_preference` and `current_state`, in addition to the existing `temporal_lookup` and `list_count` allowlist.

Typed memory text is still not independent reader evidence: `compiler.max_memory_records=0`, and final prompts contain raw Memory Context rows. The memory record only contributes source backpointers used to organize raw source rows.

Prediction uses only question text, raw Memory Context, build-memory records built from dialogue, source backpointers, and prediction-time route. It uses no gold answers, judge output, benchmark labels, sample ids, row indices, test feedback, or sample-level shortcuts.

## Config

- Config: `configs/stage1_superseded_source_chain_v127_qwen36_no_think_build4k_cached.json`
- Answer cache namespace: `stage1_superseded_source_chain_v127_qwen36_no_think_build4k`
- Build cache: `outputs/cache/qwen36_no_think_build4k_memory_v102.sqlite`
- Git commit recorded by runs: `88efe8b`
- Dirty status: dirty; includes v118-v127 configs/diagnostics and source changes from the current exploration worktree.

## Dry-Run Results

### LongMemEval-S

Compared against retained V126 dry-run:

| route | n | changed prompt | changed rows | order-only | rows with superseded hits | new superseded-hit rows | avg context char delta |
|---|---:|---:|---:|---:|---:|---:|---:|
| `current_state` | `22` | `2` | `2` | `0` | `6` | `6` | `+6.409` |
| `fact_lookup` | `183` | `0` | `0` | `0` | `0` | `0` | `0.000` |
| `list_count` | `119` | `0` | `0` | `0` | `60` | `0` | `0.000` |
| `profile_preference` | `15` | `3` | `3` | `0` | `8` | `8` | `-47.600` |
| `temporal_lookup` | `161` | `0` | `0` | `0` | `72` | `0` | `0.000` |
| total | `500` | `5` | `5` | `0` | `146` | `14` | `-1.146` |

### LoCoMo

Compared against retained V126 `locomo_profile_state_dry`:

| route | n | changed prompt | changed rows | order-only | rows with superseded hits | new superseded-hit rows | avg context char delta |
|---|---:|---:|---:|---:|---:|---:|---:|
| `current_state` | `4` | `4` | `4` | `1` | `3` | `3` | `-14.500` |
| `fact_lookup` | `882` | `0` | `0` | `0` | `0` | `0` | `0.000` |
| `list_count` | `270` | `0` | `0` | `0` | `128` | `0` | `0.000` |
| `profile_preference` | `46` | `20` | `20` | `7` | `27` | `27` | `-4.478` |
| `temporal_lookup` | `338` | `0` | `0` | `0` | `156` | `0` | `0.000` |
| total | `1540` | `24` | `24` | `8` | `314` | `30` | `-0.171` |

Dry-run conclusion: the change is narrow and localized to the intended `profile_preference` / `current_state` routes. `fact_lookup`, `list_count`, and `temporal_lookup` prompts do not change.

## Answer Diagnostics

Changed-prompt inputs were created from prediction-time trace diffs only:

- LME input: `outputs/diagnostic_inputs/stage1_superseded_source_chain_v127_lme_changed_prompts.jsonl`
- LoCoMo input: `outputs/diagnostic_inputs/stage1_superseded_source_chain_v127_locomo_changed_prompts.jsonl`

### Changed-Prompt Subsets

| subset | n | v126 exact | v127 exact | v126 F1 | v127 F1 | v126 BLEU1 | v127 BLEU1 | changed answers | exact gain/loss |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| LME changed prompts | `5` | `0.200000` | `0.400000` | `0.253838` | `0.569361` | `0.240903` | `0.541519` | `4/5` | `1/0` |
| LoCoMo changed prompts | `24` | `0.291667` | `0.291667` | `0.523104` | `0.559140` | `0.474813` | `0.510234` | `9/24` | `0/0` |

Token/cost:

- LME changed prompts: avg build/query `89368.600 / 5943.000`; answer cache miss/write `5/5`; finalizer applied `1`.
- LoCoMo changed prompts: avg build/query `62778.958 / 6193.958`; answer cache miss/write `24/24`; finalizer applied `0`.

### Full Route-Only Merge

To avoid rerunning unchanged prompts, full diagnostic artifacts were produced by merging V127 changed-prompt predictions into V126 full route-only merges.

| artifact | base records | override records | total |
|---|---:|---:|---:|
| LME full route-only merge | `495` | `5` | `500` |
| LoCoMo full route-only merge | `1516` | `24` | `1540` |

Lexical metrics only:

| predictions | exact | F1 | BLEU1 |
|---|---:|---:|---:|
| V126 LME full route-only | `0.426000` | `0.630589` | `0.586597` |
| V127 LME full route-only | `0.428000` | `0.633744` | `0.589603` |
| V126 LoCoMo full route-only | `0.244156` | `0.537112` | `0.483232` |
| V127 LoCoMo full route-only | `0.244156` | `0.537674` | `0.483784` |

Full exact transitions:

- LME: changed answers `4/500`; exact gain/loss `1/0` (`Hawaii` -> `Paris` on one changed prompt).
- LoCoMo: changed answers `9/1540`; exact gain/loss `0/0`.

## Outputs

- LME dry-run traces: `outputs/diagnostic/stage1_superseded_source_chain_v127_lme_dry/traces.jsonl`
- LoCoMo dry-run traces: `outputs/diagnostic/stage1_superseded_source_chain_v127_locomo_dry/traces.jsonl`
- LME changed-prompt predictions: `outputs/diagnostic/stage1_superseded_source_chain_v127_lme_changed_prompts/predictions.jsonl`
- LoCoMo changed-prompt predictions: `outputs/diagnostic/stage1_superseded_source_chain_v127_locomo_changed_prompts/predictions.jsonl`
- LME full merge predictions: `outputs/diagnostic/stage1_superseded_source_chain_v127_lme_s_full_route_only_merge/predictions.jsonl`
- LoCoMo full merge predictions: `outputs/diagnostic/stage1_superseded_source_chain_v127_locomo_nonadv_full_route_only_merge/predictions.jsonl`
- LME full lexical metrics: `experiments/diagnostic/stage1_superseded_source_chain_v127_lme_s_full_route_only_merge/lexical_metrics.json`
- LoCoMo full lexical metrics: `experiments/diagnostic/stage1_superseded_source_chain_v127_locomo_nonadv_full_route_only_merge/lexical_metrics.json`

## Decision

Keep V127 as a narrow positive diagnostic candidate. Do not promote to LTS.

Reasoning:

- Clean/general risk is controlled: the change uses prediction-time route and source-linked memory records, not labels or sample-level rules.
- The impact scope is small and intended: LME `5/500` prompts and LoCoMo `24/1540` prompts changed, all in profile/current routes.
- Auxiliary lexical metrics are positive or neutral: LME full route-only exact gains `+1/500`; LoCoMo full route-only exact is unchanged with small F1/BLEU improvement.
- Primary metric is still missing because the current environment has no `DEEPSEEK*` env. V127 should be judged after V125/V126 pending candidates, or alongside them if batching judge cost is acceptable.

Next judge commands when the key is available:

```bash
python scripts/judge_predictions_dual_deepseek.py \
  --predictions outputs/diagnostic/stage1_superseded_source_chain_v127_lme_s_full_route_only_merge/predictions.jsonl \
  --labels outputs/prepare_longmemeval_s_cleaned/labels.jsonl \
  --output experiments/diagnostic/stage1_superseded_source_chain_v127_lme_s_full_route_only_merge/deepseek_dual_judge.json \
  --benchmark longmemeval \
  --workers 8 \
  --progress-every 50
```

```bash
python scripts/judge_predictions_dual_deepseek.py \
  --predictions outputs/diagnostic/stage1_superseded_source_chain_v127_locomo_nonadv_full_route_only_merge/predictions.jsonl \
  --labels outputs/prepare_locomo_non_adversarial/labels.jsonl \
  --output experiments/diagnostic/stage1_superseded_source_chain_v127_locomo_nonadv_full_route_only_merge/deepseek_dual_judge.json \
  --benchmark locomo \
  --workers 8 \
  --progress-every 50
```
