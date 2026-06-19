# stage1_lossless_atomic_build_memory_v244_probe_summary

## Purpose

验证更系统化的 build-stage memory 是否能提升框架质量：v244 从 v235 LTS 出发，只把 build memory 改成 `lossless_atomic` prompt profile，并把 `max_records_per_chunk` 从 `20` 提到 `32`；retrieval、compiler、answer prompt、answer repair 和 finalizer 保持 v235。

## Config

- base LTS: `configs/stage1_no_finalizer_v235_seeded_qwen36_no_think_build4k_cached.json`
- candidate: `configs/stage1_lossless_atomic_build_memory_v244_seeded_qwen36_no_think_build4k_cached.json`
- method commit: `fd82d071be18d9e416e161f2095ac8db13b494ef`
- answer cache seed: v235 prediction-time traces/predictions only; no labels, judge outputs, benchmark tags, sample ids, or test feedback.

## Results

| Scope | Status | answer diff vs v235 | avg build tokens | avg query tokens | Notes |
|---|---|---:|---:|---:|---|
| LoCoMo probe50 | completed | `17/50` | `53199.68` | `5955.48` | v235 same keys: build `45868.0`, query `6543.56` |
| LME probe50 | aborted | unavailable | unavailable | unavailable | cold build exceeded reasonable probe latency and produced no completed sample before termination |

LoCoMo build memory changed substantially:

- avg records: `112.0 -> 160.6`
- avg active records: `98.0 -> 146.98`
- answer cache hit/miss/write: `6/44/44`

LoCoMo changed-answer judge:

| Scope | v235 strict/lenient | v244 strict/lenient | Delta |
|---|---:|---:|---:|
| LoCoMo changed `17` | `13/17` / `14/17` | `13/17` / `14/17` | tie |

Judge token usage:

- v235 changed judge total: `17884`
- v244 changed judge total: `18595`

## Diagnosis

v244 has a useful direction but is not a usable LTS candidate. The richer build memory increased LoCoMo memory coverage and reduced LoCoMo query tokens on the probe, but it did not improve changed-answer judge accuracy. More importantly, the LME probe cold build did not complete a single sample in a reasonable time window, so the method has unacceptable build-latency risk in its current form.

The next build-side version should keep the atomic-memory idea but make it cheaper and more controlled. Likely changes:

- keep `typed_compact` first-pass memory and add a smaller second-pass atomic detail extractor only for dense / long / high-entropy chunks;
- cap atomic records by source diversity and source utility instead of a broad per-chunk record cap;
- store extra atomic details as retrieval-only candidates, not broad prompt noise;
- measure build latency and cache misses before running broad probes.

## Decision

Do not promote v244. Current LTS remains v235.

## Outputs

- LoCoMo probe50: `outputs/diagnostic/stage1_lossless_atomic_build_memory_v244_locomo_probe50/`
- LoCoMo changed predictions/labels: `outputs/diagnostic/stage1_lossless_atomic_build_memory_v244_locomo_probe50_changed_vs_v235/`
- LoCoMo changed judge: `experiments/diagnostic/stage1_lossless_atomic_build_memory_v244_locomo_probe50_changed_vs_v235/`
- LME aborted run produced no committed experiment record.
