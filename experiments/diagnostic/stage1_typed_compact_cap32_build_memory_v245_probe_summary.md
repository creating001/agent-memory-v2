# stage1_typed_compact_cap32_build_memory_v245_probe_summary

## Purpose

验证 v244 的低成本替代：v245 保留 v235 的 `typed_compact` build prompt，只把 `max_records_per_chunk` 从 `20` 提到 `32`，希望提升 build memory coverage，同时不引入 lossless full-build 的延迟和 query-time patch logic。

## Config

- base LTS: `configs/stage1_no_finalizer_v235_seeded_qwen36_no_think_build4k_cached.json`
- candidate: `configs/stage1_typed_compact_cap32_build_memory_v245_seeded_qwen36_no_think_build4k_cached.json`
- method commit: `0f7134a543b40b72d2581896f86b058813709000`
- answer cache seed: v235 prediction-time traces/predictions only; no labels, judge outputs, benchmark tags, sample ids, or test feedback.

## Results

| Scope | Status | answer diff vs v235 | avg build tokens | avg query tokens | Notes |
|---|---|---:|---:|---:|---|
| LoCoMo probe50 | completed | `22/50` | `49196.58` | `6556.36` | v235 same keys: build `45868.0`, query `6543.56` |
| LME probe50 | aborted | unavailable | unavailable | unavailable | cold build produced no completed sample before termination |

LoCoMo memory coverage changed:

- avg records: `112.0 -> 140.8`
- avg active records: `98.0 -> 126.1`
- answer cache hit/miss/write: `4/46/46`

LoCoMo changed-answer judge:

| Scope | v235 strict/lenient | v245 strict/lenient | Delta |
|---|---:|---:|---:|
| LoCoMo changed `22` | `18/22` / `18/22` | `15/22` / `17/22` | strict `-3`, lenient `-1` |

Judge token usage:

- v235 changed judge total: `24923`
- v245 changed judge total: `24737`

## Diagnosis

v245 is rejected. Increasing the typed memory cap did increase record coverage, but it raised build tokens, did not reduce query tokens, and hurt LoCoMo changed-answer accuracy. The LME cold probe also showed the same operational problem as v244: changing build cache keys on broad LME samples can stall before any completed sample, so future build-side probes need targeted cold-build subsets before probe50.

The useful lesson is that build memory needs better quality and utility control, not just more records. Extra records introduce answer drift unless retrieval/compiler can select utility-bearing evidence rather than more source-adjacent noise.

## Decision

Do not promote v245. Current LTS remains v235.

## Outputs

- LoCoMo probe50: `outputs/diagnostic/stage1_typed_compact_cap32_build_memory_v245_locomo_probe50/`
- LoCoMo changed predictions/labels: `outputs/diagnostic/stage1_typed_compact_cap32_build_memory_v245_locomo_probe50_changed_vs_v235/`
- LoCoMo changed judge: `experiments/diagnostic/stage1_typed_compact_cap32_build_memory_v245_locomo_probe50_changed_vs_v235/`
- LME aborted run produced no committed experiment record.
