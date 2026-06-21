# v349_inline_memory_context_changed_vs_v347_currentcode

## Purpose

Evaluate v349 against a current-code v347 baseline on probe50. v349 changes only raw Memory Context presentation:

- `memory_context_header_format=inline`
- raw Memory row text, row set, row order, retrieval, guide semantics, answer contract, and temporal/list route settings are unchanged

This is a clean offline diagnostic. Gold labels and judge outputs are used only after prediction for evaluation.

## Compile-Scan Diff

| Scope | Prompt changed | Row set changed | Row order changed | Non-Memory block changed | Avg prompt char delta |
|---|---:|---:|---:|---:|---:|
| LongMemEval-S probe50 | `50/50` | `0/50` | `0/50` | `0/50` | `-458.94` |
| LoCoMo non-adversarial probe50 | `50/50` | `0/50` | `0/50` | `0/50` | `-636.52` |

The reduction comes entirely from `Memory Context` row headers.

## Answer Probe Tokens

| Scope | Version | Avg prompt tokens | Avg completion tokens | Avg query tokens |
|---|---|---:|---:|---:|
| LongMemEval-S probe50 | v347 current-code | `5110.04` | `246.08` | `5356.12` |
| LongMemEval-S probe50 | v349 | `4968.52` | `580.94` | `5549.46` |
| LoCoMo non-adversarial probe50 | v347 current-code | `5076.02` | `485.46` | `5561.48` |
| LoCoMo non-adversarial probe50 | v349 | `4879.86` | `468.50` | `5348.36` |

v349 reduces prompt tokens on both benchmarks. It reduces total query tokens on LoCoMo, but increases LongMemEval total query tokens because answer completions become longer.

## Changed-Answer Judge

Judge: dual `deepseek-v4-flash`, temperature `0`, default thinking.

| Benchmark | Version | Changed n | Strict | Lenient |
|---|---|---:|---:|---:|
| LongMemEval-S | v347 current-code | 3 | `2/3` | `2/3` |
| LongMemEval-S | v349 | 3 | `2/3` | `2/3` |
| LoCoMo | v347 current-code | 24 | `21/24` | `22/24` |
| LoCoMo | v349 | 24 | `23/24` | `23/24` |

Per-record flips:

- LongMemEval-S: none.
- LoCoMo: two strict+lenient improvements, one lenient regression.

## Decision

Do not promote v349 as LTS. The method is low-risk and improves LoCoMo changed-answer accuracy while reducing LoCoMo total query tokens, but it fails the immediate query-token goal on LongMemEval because completion tokens increase. The next version should keep the lossless single-line row header but restore clearer row separation, then recheck whether LongMemEval completion verbosity returns to baseline while preserving prompt-token savings.

## Outputs

- `configs/stage1_inline_memory_context_v349_seeded_qwen36_no_think_build4k_cached.json`
- `configs/stage1_inline_memory_context_v349_compile_scan.json`
- `experiments/diagnostic/v349_inline_memory_context_compile_scan_lme_probe50/`
- `experiments/diagnostic/v349_inline_memory_context_compile_scan_locomo_probe50/`
- `experiments/diagnostic/v349_inline_memory_context_lme_probe50/`
- `experiments/diagnostic/v349_inline_memory_context_locomo_probe50/`
- `experiments/diagnostic/v349_baseline_v347_currentcode_compile_scan_lme_probe50/`
- `experiments/diagnostic/v349_baseline_v347_currentcode_compile_scan_locomo_probe50/`
- `experiments/diagnostic/v349_baseline_v347_currentcode_lme_probe50/`
- `experiments/diagnostic/v349_baseline_v347_currentcode_locomo_probe50/`

