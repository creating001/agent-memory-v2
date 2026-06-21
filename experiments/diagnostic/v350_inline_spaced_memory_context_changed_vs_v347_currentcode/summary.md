# v350_inline_spaced_memory_context_changed_vs_v347_currentcode

## Purpose

Evaluate v350 against a current-code v347 baseline on probe50. v350 keeps v349's single-line raw Memory Context row header, but restores blank-line row separation:

- `memory_context_header_format=inline_spaced`
- raw Memory row text, row set, row order, retrieval, guide semantics, answer contract, and temporal/list route settings are unchanged

This targets query-token reduction without deleting raw evidence or compressing guide semantics.

## Compile-Scan Diff

| Scope | Prompt changed | Row set changed | Row order changed | Non-Memory block changed | Avg prompt char delta |
|---|---:|---:|---:|---:|---:|
| LongMemEval-S probe50 | `50/50` | `0/50` | `0/50` | `0/50` | `-424.56` |
| LoCoMo non-adversarial probe50 | `50/50` | `0/50` | `0/50` | `0/50` | `-588.48` |

The reduction comes entirely from `Memory Context` row headers.

## Answer Probe Tokens

| Scope | Version | Avg prompt tokens | Avg completion tokens | Avg query tokens |
|---|---|---:|---:|---:|
| LongMemEval-S probe50 | v347 current-code | `5110.04` | `246.08` | `5356.12` |
| LongMemEval-S probe50 | v350 | `4968.52` | `234.32` | `5202.84` |
| LoCoMo non-adversarial probe50 | v347 current-code | `5076.02` | `485.46` | `5561.48` |
| LoCoMo non-adversarial probe50 | v350 | `4879.86` | `451.62` | `5331.48` |

Compared with v349, restoring row spacing removes the LongMemEval completion-token regression while preserving most prompt-token savings.

## Changed-Answer Judge

Judge: dual `deepseek-v4-flash`, temperature `0`, default thinking.

| Benchmark | Version | Changed n | Strict | Lenient |
|---|---|---:|---:|---:|
| LongMemEval-S | v347 current-code | 2 | `1/2` | `1/2` |
| LongMemEval-S | v350 | 2 | `1/2` | `1/2` |
| LoCoMo | v347 current-code | 27 | `24/27` | `24/27` |
| LoCoMo | v350 | 27 | `24/27` | `25/27` |

Per-record flips:

- LongMemEval-S: none.
- LoCoMo: one strict+lenient regression, one lenient improvement, one strict+lenient improvement.

## Decision

Keep v350 as the current clean query-token candidate. It is not a new LTS yet because evidence is probe50-level, but it is stronger than v349: both benchmarks reduce total query tokens, row set/order are unchanged, non-Memory prompt blocks are unchanged, and changed-answer judge is non-negative on strict and positive on LoCoMo lenient.

Next step: run a larger cache-aligned diff or full changed-answer judge before any LTS decision, and keep watching completion-token behavior.

## Outputs

- `configs/stage1_inline_spaced_memory_context_v350_seeded_qwen36_no_think_build4k_cached.json`
- `configs/stage1_inline_spaced_memory_context_v350_compile_scan.json`
- `experiments/diagnostic/v350_inline_spaced_memory_context_compile_scan_lme_probe50/`
- `experiments/diagnostic/v350_inline_spaced_memory_context_compile_scan_locomo_probe50/`
- `experiments/diagnostic/v350_inline_spaced_memory_context_lme_probe50/`
- `experiments/diagnostic/v350_inline_spaced_memory_context_locomo_probe50/`

