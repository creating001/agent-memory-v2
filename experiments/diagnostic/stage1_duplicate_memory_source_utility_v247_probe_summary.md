# stage1_duplicate_memory_source_utility_v247_probe_summary

## Purpose

Test a conservative follow-up to v246. v247 keeps memory-only source projections and only removes low-utility duplicate build-memory source boosts when the same raw source was already retrieved by lexical or dense retrieval.

## Setup

- Config: `configs/stage1_duplicate_memory_source_utility_v247_seeded_qwen36_no_think_build4k_cached.json`
- Method commit: `1d2545d1cd647880c024510740030d2dd700f544`
- Clean setting: no gold answers, judge output, benchmark labels, sample ids, test feedback, or sample-level rules were used in prediction/retrieval/compiler/answer/cache.
- Answer cache was seeded from v235 prediction traces only.

## Probe Results

| Benchmark | n | answer diff vs v235 | avg query tokens | memory-source hits | duplicate drops | changed dual judge |
|---|---:|---:|---:|---:|---:|---|
| LongMemEval-S | 50 | 2/50 | v235 `5677.40` -> v247 `5689.26` | `7.22` -> `5.50` | avg `1.72` | strict/lenient `1/2 -> 2/2` |
| LoCoMo non-adv | 50 | 18/50 | v235 `6543.56` -> v247 `6560.04` | `27.72` -> `24.16` | avg `3.56` | strict `16/18 -> 14/18`, lenient `17/18 -> 15/18` |

DeepSeek dual flash judge used `deepseek-v4-flash`, temperature `0`, default thinking. Judge total usage for changed subsets was `40971` tokens.

## Diagnosis

v247 fixes v246's most direct problem: it does not remove memory-only evidence. However, even duplicate-only filtering changes RRF boost/protected source behavior enough to perturb LoCoMo profile/list answers. The losses are concentrated in detail-preserving profile/list outputs, for example:

- `663162cd2f331f7d572f90cd`: destress answer added unsupported activities and lost strict/lenient credit.
- `9748405e4eeefe3cc1d5339c`: useful uncertainty with celebration date became a shorter abstention and lost strict/lenient credit.
- `97e324be3e76a7dc37e954fd`: singular/plural specificity changed and lost lenient credit.

## Decision

Reject v247 probe and keep v235 as LTS. Do not run full. The source-utility line has a useful lesson but should not continue as source-hit deletion or duplicate boost deletion. Next work should move the utility signal into trace/audit or a later verifier/compiler decision that does not perturb raw evidence retrieval order directly.

## Outputs

- LME probe: `outputs/diagnostic/stage1_duplicate_memory_source_utility_v247_lme_probe50/`
- LoCoMo probe: `outputs/diagnostic/stage1_duplicate_memory_source_utility_v247_locomo_probe50/`
- LME changed judge: `outputs/diagnostic/stage1_duplicate_memory_source_utility_v247_lme_probe50_changed_vs_v235/`
- LoCoMo changed judge: `outputs/diagnostic/stage1_duplicate_memory_source_utility_v247_locomo_probe50_changed_vs_v235/`
