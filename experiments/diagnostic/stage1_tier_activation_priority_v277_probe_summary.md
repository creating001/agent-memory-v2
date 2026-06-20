# v277 Tier Activation Priority Probe Summary

## Purpose

Test whether the v276 memory tier manifest can actively participate in retrieval instead of remaining a build-only trace.

v277 added tier-aware ordering to the build-side activation priority manifest and enabled `retrieval.memory_activation_priority` for current-state, profile-preference, list-count, and temporal questions. It used a soft score boost rather than a hard gate, and final evidence still resolved to raw Memory rows.

## Configuration

- config: `configs/stage1_tier_activation_priority_v277_seeded_qwen36_no_think_build4k_cached.json`
- method commit: `00ebea1`
- parent LTS: v276 `configs/stage1_memory_tier_manifest_v276_seeded_qwen36_no_think_build4k_cached.json`
- priority scope: `current_state`, `profile_preference`, `list_count`, `temporal_lookup`
- priority parameters: `pool_k=40`, `score_boost=0.35`, `max_rank=96`
- clean setting: prediction uses no gold answer, judge output, benchmark tags, sample ids, test feedback, labels, or sample-level rules.

## Probe Results

| Benchmark | answer diff | prompt diff | retrieval diff | cache hit/miss | priority applied / reordered | avg query tokens |
|---|---:|---:|---:|---:|---:|---:|
| LongMemEval-S probe50 | `0/50` | `1/50` | `7/50` | `49/1` | `18 / 6` | `5684.22` |
| LoCoMo probe50 | `8/50` | `18/50` | `31/50` | `32/18` | `34 / 32` | `6536.62` |

LoCoMo changed-answer paired judge, dual `deepseek-v4-flash`, temperature `0`, default thinking:

| subset | changed answers | base strict/lenient | v277 strict/lenient | delta |
|---|---:|---:|---:|---:|
| LoCoMo probe50 changed vs v276 | `8` | `7 / 7` | `7 / 7` | `0 / 0` |

## Decision

Do not run v277 full and do not promote it.

Rationale: v277 did not regress on the small changed-answer judge, but it caused broad LoCoMo prompt/retrieval churn by applying tier activation to list-count and temporal questions. That is too much behavioral surface for a structural activation step. v278 narrows the same mechanism to current-state and profile-preference queries.

## Outputs

```text
outputs/diagnostic/stage1_tier_activation_priority_v277_lme_probe50/predictions.jsonl
outputs/diagnostic/stage1_tier_activation_priority_v277_lme_probe50/traces.jsonl
outputs/diagnostic/stage1_tier_activation_priority_v277_locomo_probe50/predictions.jsonl
outputs/diagnostic/stage1_tier_activation_priority_v277_locomo_probe50/traces.jsonl
outputs/diagnostic/stage1_tier_activation_priority_v277_locomo_probe50_changed_vs_v276/
experiments/diagnostic/stage1_tier_activation_priority_v277_lme_probe50/
experiments/diagnostic/stage1_tier_activation_priority_v277_locomo_probe50/
```
