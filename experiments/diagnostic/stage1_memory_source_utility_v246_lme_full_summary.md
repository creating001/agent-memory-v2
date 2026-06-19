# stage1_memory_source_utility_v246_lme_full_summary

## Purpose

Validate whether the positive v246 probe signal holds on LongMemEval-S full before running LoCoMo full or considering LTS promotion.

## Setup

- Config: `configs/stage1_memory_source_utility_v246_seeded_qwen36_no_think_build4k_cached.json`
- Method commit: `88d6a2366edc4dbbdd97750edf7b5c913faf96d9`
- Probe evidence commit: `1285b84979e63ab67da2d21414799e45a5384a1a`
- Full run: `experiments/diagnostic/stage1_memory_source_utility_v246_lme_full/`
- Changed judge outputs: `outputs/diagnostic/stage1_memory_source_utility_v246_lme_full_changed_vs_v235/`
- Judge: DeepSeek dual `deepseek-v4-flash`, temperature `0`, default thinking.

## Full Metrics

| Metric | v235 LTS | v246 |
|---|---:|---:|
| n | 500 | 500 |
| answer diff | - | 63 |
| avg build tokens | `85393.566` | `85393.566` |
| avg query tokens | `6579.782` | `6333.872` |
| avg memory-source hits | `9.784` | `4.464` |
| answer cache hits/misses | `500/0` | `284/216` |

v246 utility details: avg records seen `8.518`, kept `3.802`, dropped `4.716`; source hits before/after `9.784 -> 4.464`.

## Changed-Answer Judge

| Subset | v235 | v246 | Delta |
|---|---:|---:|---:|
| strict correct on changed 63 | `38/63` | `27/63` | `-11` |
| lenient correct on changed 63 | `39/63` | `30/63` | `-9` |
| derived full strict | `416/500` | `405/500` | `-11` |
| derived full lenient | `422/500` | `413/500` | `-9` |

Judge token usage for the changed subset was `77977` total tokens across v235/v246 dual runs.

## Diagnosis

v246 reduces query cost and typed-memory source noise, but the utility gate is too coarse. It relies on matched question terms plus top-rank preservation, which works for some direct fact/profile rows but drops low-overlap source rows that still matter for list aggregation, count calculation, advice, and temporal/numeric reasoning.

Representative regressions:

- `27a28d49af7d327bb9f25309`: `$270` became an abstaining lower-bound answer.
- `32eb6a6d4eb90246887b34fb`: count regressed from `4` to `3`.
- `42bbbfc59c3c45cd91ee953b`: clean abstention became unsupported `0`.
- `5110d0ed1a7cb0fefd131e4d`: useful recommendation became broad uncertainty.
- `676f08cb0b1213adf24077d5`: grounded advice became abstention.

## Decision

Reject v246 full and keep v235 as LTS. Do not run LoCoMo full for v246 because LME full already shows an unacceptable accuracy regression.

The lesson is still useful for the next version: memory-source expansion needs utility selection, but it must be typed and context-aware rather than a single matched-term cap. v247 should keep the general source-utility idea while protecting list/count/advice/numeric rows and using evidence role or compiler need rather than raw overlap alone.
