# v354 workspace source core gate probe summary

## Purpose

v354 tightens v353's `workspace_source_expansion` so source-backed memory objects can still expand to raw rows, but subject-only or generic-term matches no longer trigger expansion. The goal is to keep the Agent Memory system behavior from v353 while reducing the risk that a broad person-name match replaces useful tail evidence.

## Clean boundary

Prediction uses no gold answers, judge outputs, benchmark tags, sample ids, test feedback, or sample-level rules. The new gate uses only question text, build-owned memory object fields, raw source ids, and prediction-time route. DeepSeek dual judge was run offline after prediction only.

## Method changes

- Added `min_core_terms` to `retrieval.workspace_source_expansion`.
- Added a workspace-expansion-specific generic term filter; this does not alter global retrieval terms.
- Added route overrides so fact/profile/temporal routes expand at most one source, current-state can expand two, and list-count requires two non-subject core terms.
- Added `skipped_low_core_count` trace, Context Manifest, metrics aggregation, and unit tests for subject-only skip plus route override source caps.

## Runs

| Run | Path |
|---|---|
| LME compile scan | `outputs/diagnostic/v354_workspace_source_core_gate_compile_scan_lme_probe50/traces.jsonl` |
| LoCoMo compile scan | `outputs/diagnostic/v354_workspace_source_core_gate_compile_scan_locomo_probe50/traces.jsonl` |
| LME answer probe | `outputs/diagnostic/v354_workspace_source_core_gate_lme_probe50/predictions.jsonl` |
| LoCoMo answer probe | `outputs/diagnostic/v354_workspace_source_core_gate_locomo_probe50/predictions.jsonl` |
| LME dual judge | `experiments/diagnostic/v354_workspace_source_core_gate_lme_probe50/deepseek_dual_judge.json` |
| LoCoMo dual judge | `experiments/diagnostic/v354_workspace_source_core_gate_locomo_probe50/deepseek_dual_judge.json` |

## Probe metrics

| Benchmark | avg query tokens | strict | lenient | expansion applied | avg final expansion sources | skipped low-core avg |
|---|---:|---:|---:|---:|---:|---:|
| LongMemEval-S probe50 | `5122.66` | `48/50` | `48/50` | `35/50` | `0.62` | `264.88` |
| LoCoMo non-adversarial probe50 | `5192.02` | `44/50` | `45/50` | `42/50` | `0.86` | `252.82` |

Compared with v353, v354 reduces final expansion sources from LME `1.06 -> 0.62` and LoCoMo `2.00 -> 0.86`. Query tokens remain below v352 on both probes: LME `5194.52 -> 5122.66`, LoCoMo `5358.64 -> 5192.02`.

## Decision

Do not promote v354 to LTS yet. It is a cleaner and safer source-expansion candidate than v353 because it reduces subject-only activation risk and makes the expansion gate auditable. However, LoCoMo probe judge returns to v352-level strict/lenient `44/50` / `45/50`, so v354 needs more method work before larger/full LTS evaluation.

## Next

- Keep v354 as the current safer source-expansion candidate.
- Improve the build-side memory organization and source-expansion scoring so useful multi-hop/profile expansions survive the core gate without reintroducing subject-only broad activation.
- If a follow-up candidate improves LoCoMo probe judge or clearly reduces system risk with no broader regression, run larger/full paired judge before any LTS promotion.
