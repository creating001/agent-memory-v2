# v353 workspace source expansion probe summary

## Purpose

v353 makes the build-owned memory system participate in query operations more directly. It keeps v352's `memory_workspace_policy` micro packet, then adds a bounded `workspace_source_expansion` retrieval stage: query-relevant `memory_system_state` entries can expand back to raw source rows before context budgeting.

The goal is to make memory objects more than retrieval hints while also reducing query tokens. The new stage is source-backed, tail-exchange based, and budgeted: it protects the head retrieval window, inserts at most two raw source rows from memory objects, and replaces tail hits instead of increasing hit count.

## Clean boundary

Prediction uses no gold answers, judge outputs, benchmark tags, sample ids, test feedback, or sample-level rules. Memory objects remain activation/index handles only; final answer evidence is still raw Memory rows. DeepSeek judge was not run because `DEEPSEEK_API_KEY` was not present in the shell, and `.env` was not read.

## Method note

This version follows the project direction of a memory system rather than a prompt patch. The design is inspired by memory-OS style store/retrieve/manage APIs, source/provenance-linked memory objects, and xMemory-style expansion from organized memory units back to raw messages. The implemented policy is deliberately conservative: source-backed expansion is query-gated, limited, auditable, and still downstream of raw evidence.

## Changes

- Added `retrieval.workspace_source_expansion` with `memory_system_state` source, max `8` candidate entries, max `2` selected sources, `min_score=1.0`, `protect_top_n=32`, and `preserve_hit_count=true`.
- Inserted expansion after rerank and before context budget so selected memory objects can become raw-row candidates.
- Added trace and Context Manifest fields for candidate entries, selected sources, final source coverage, and replaced tail count.
- Tightened query context pressure in v353 configs: context budget `22000/60/32 -> 20000/56/28`; compiler `max_evidence_chars 18000 -> 17000`.
- Added focused unit test for tail-exchange source expansion.

## Runs

| Run | Path |
|---|---|
| LME compile scan | `outputs/diagnostic/v353_workspace_source_expansion_compile_scan_lme_probe50/traces.jsonl` |
| LoCoMo compile scan | `outputs/diagnostic/v353_workspace_source_expansion_compile_scan_locomo_probe50/traces.jsonl` |
| LME answer probe | `outputs/diagnostic/v353_workspace_source_expansion_lme_probe50/predictions.jsonl` |
| LoCoMo answer probe | `outputs/diagnostic/v353_workspace_source_expansion_locomo_probe50/predictions.jsonl` |

## Probe results vs v352

| Benchmark | row set diff | row order diff | prompt diff | avg prompt char delta | expansion applied | avg final expansion sources |
|---|---:|---:|---:|---:|---:|---:|
| LongMemEval-S probe50 | 40/50 | 40/50 | 40/50 | `-614.36` | 36/50 | `1.06` |
| LoCoMo non-adversarial probe50 | 50/50 | 50/50 | 50/50 | `-309.88` | 50/50 | `2.00` |

Context-budget estimated chars also decreased: LME avg delta `-1204.12`; LoCoMo avg delta `-173.06`. Tail replacement averaged `1.36` sources/sample on LME and `2.00` on LoCoMo.

## Query tokens

Answer probe actual usage:

| Benchmark | v352 avg query tokens | v353 avg query tokens | delta |
|---|---:|---:|---:|
| LongMemEval-S probe50 | `5194.52` | `5057.78` | `-136.74` |
| LoCoMo non-adversarial probe50 | `5358.64` | `5212.24` | `-146.40` |

Build tokens were unchanged for the paired probe inputs/caches: LME `86398.54`; LoCoMo `45868.00`.

## Answer changes

| Benchmark | changed answers |
|---|---:|
| LongMemEval-S probe50 | 3/50 |
| LoCoMo non-adversarial probe50 | 23/50 |

LME changes are mostly formatting/specificity variants. LoCoMo has many semantic changes, including at least one potentially risky relationship-status answer. It needs changed-answer dual DeepSeek judge before any LTS decision.

## Decision

Do not promote v353 to LTS yet. It improves the system design risk and reduces actual query tokens on both probe sets, but row sets change substantially and LoCoMo has 23/50 answer changes. Keep v353 as the current memory-system/source-expansion candidate pending changed-answer judge.

## Next

- Run changed-answer dual DeepSeek judge for v353 vs v352 once `DEEPSEEK_API_KEY` is available in the environment.
- Inspect LoCoMo changed answers, especially relationship/status and career/adoption cases, before broadening source expansion.
- If judge is neutral or positive, test a larger/full cache-aligned diff; if it regresses, keep the source-expansion trace and tighten entry scoring or route gating.
