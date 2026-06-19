# stage1_memory_source_utility_v246_probe_summary

## Purpose

Evaluate v246 as a clean/general retrieval-systemization step from v235 LTS.
v246 keeps v235 build memory, answer prompt, repair-disabled path, and finalizer-disabled path, and only filters build-memory-derived raw source expansion with a configurable utility gate.

## Method

- Config: `configs/stage1_memory_source_utility_v246_seeded_qwen36_no_think_build4k_cached.json`
- Method commit: `88d6a2366edc4dbbdd97750edf7b5c913faf96d9`
- Gate: `preserve_top_n=4`, `min_matched_terms=2`, `max_memory_hits=10`
- Clean setting: no gold answers, judge output, benchmark labels, sample ids, test feedback, or sample-level rules were used in prediction/retrieval/compiler/answer/cache.
- Answer cache was seeded from v235 prediction traces only.

## Probe Results

| Benchmark | n | answer diff vs v235 | avg query tokens | memory-source hits | utility records kept/dropped | changed dual judge |
|---|---:|---:|---:|---:|---:|---|
| LongMemEval-S | 50 | 3/50 | v235 `5677.40` -> v246 `5672.50` | `7.22` -> `3.40` | kept `3.18`, dropped `3.14` | strict/lenient `2/3 -> 3/3` |
| LoCoMo non-adv | 50 | 16/50 | v235 `6543.56` -> v246 `6575.10` | `27.72` -> `10.18` | kept `6.84`, dropped `13.16` | strict `12/16 -> 14/16`, lenient `13/16 -> 16/16` |

DeepSeek dual flash judge used `deepseek-v4-flash`, temperature `0`, default thinking. Judge total usage for the changed subsets was `39234` tokens.

## Diagnosis

v246 reduces a real system risk in v235: typed memory no longer projects every matched memory record into raw source rows, so memory becomes a utility-ranked source activation layer instead of broad prompt noise. This is more general than the earlier source-alignment and typed-compact build attempts because it does not add benchmark-shaped answer rules or increase build records.

The probe signal is positive on changed-answer judge, especially LoCoMo lenient `+3/16`. However, LoCoMo answer churn is high (`16/50`) and query tokens increase by `31.54` on the probe. The main residual badcase is over-compression for profile/list answers: record `663162cd2f331f7d572f90cd` lost strict credit because the new answer omitted some destress activities, though it remained lenient-correct. Record `d5068b3c68a955ba6cdfe705` is also lenient-only and suggests the cap may drop some family-activity details.

## Decision

Promote v246 to full-candidate status, not LTS yet. It has lower memory-source noise risk and positive probe judge deltas, but full LME/LoCoMo runs are required before replacing v235. If full results show the same pattern but LoCoMo token/churn remains high, the next step is a v247 route-aware utility variant that is less aggressive for list/profile aggregation while preserving the general source-utility mechanism.

## Outputs

- LME probe: `outputs/diagnostic/stage1_memory_source_utility_v246_lme_probe50/`
- LoCoMo probe: `outputs/diagnostic/stage1_memory_source_utility_v246_locomo_probe50/`
- LME changed judge: `outputs/diagnostic/stage1_memory_source_utility_v246_lme_probe50_changed_vs_v235/`
- LoCoMo changed judge: `outputs/diagnostic/stage1_memory_source_utility_v246_locomo_probe50_changed_vs_v235/`
