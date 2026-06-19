# stage1_gated_fact_list_tail_rerank_filter_v227 rejection summary

## Decision

V227 is rejected and does not replace v225 LTS.

V227 fixed v226's fact/list rerank activation bug by adding `min_effective_top_k=56`: lower-context profiles no longer expand to the rerank `pool_k=60`.

## Probe Diff

| Benchmark | Probe | prompt diff | evidence rows diff | retrieval hits diff | answer diff | rerank applied | top-k gate skips |
|---|---:|---:|---:|---:|---:|---:|---:|
| LongMemEval-S | `50` | `1/50` | `1/50` | `2/50` | `0/50` | `0/50` | `36/50` |

The fact/list rerank gate worked: all `36/36` fact/list probe rows skipped rerank with `top_k_below_min_effective_top_k`, and `rerank_applied_count` was `0`.

## Diagnosis

The remaining drift is unrelated to rerank. V227 inherited v226's `current_state` and `profile_preference` route overrides at `top_k=60`. Because route overrides are currently applied after the `long_context_pressure` profile, the `profile_preference` override replaced the LME long-context profile's intended `top_k=40`, causing one profile-preference prompt/evidence diff in the probe.

This is a clean configuration/precedence issue, but it contaminates the method scope. V227 should be superseded by a profile-aware route override policy before any LoCoMo probe or judge.

## Artifacts

- Method commit: `38ac45f1ecab2ac2090be08f343c683fc5c13b93`
- Config: `configs/stage1_gated_fact_list_tail_rerank_filter_v227_seeded_qwen36_no_think_build4k_cached.json`
- LME probe: `experiments/diagnostic/stage1_gated_fact_list_tail_rerank_filter_v227_lme_probe50/`
- Outputs: `outputs/diagnostic/stage1_gated_fact_list_tail_rerank_filter_v227_lme_probe50/`
- Cache seeding: v225 LME and LoCoMo prediction-time answers were seeded into the v227 answer cache before the probe; no labels or judge outputs were read.
