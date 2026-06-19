# stage1_fact_list_tail_rerank_filter_v226 rejection summary

## Decision

V226 is rejected and does not replace v225 LTS.

V226 attempted a source/span-preserving rerank filter for `fact_lookup` and `list_count`: keep the first `52` retrieval anchors, rerank tail candidates from a `60`-row pool with `Qwen/Qwen3-Reranker-0.6B`, then preserve source order in the returned evidence rows.

## Clean Boundary

- Prediction uses only question text, raw Memory Context, visible metadata, and build-stage memory generated before the question.
- No gold answer, judge output, benchmark label, sample id, test feedback, or sample-level rule is used by retrieval, compiler, answer, repair, finalizer, cache construction, or rerank.
- Probe comparison is against v225 LTS traces and predictions; no judge output is used to tune the method.

## Probe Diff

| Benchmark | Probe | prompt diff | evidence rows diff | retrieval hits diff | answer diff | rerank applied | rerank tokens |
|---|---:|---:|---:|---:|---:|---:|---:|
| LongMemEval-S | `50` | `18/50` | `18/50` | `22/50` | `6/50` | `36/50` | `758823` |
| LoCoMo non-adversarial | `80` | `22/80` | `22/80` | `27/80` | `32/80` | `41/80` | `597848` |

## Cost Snapshot

| Benchmark | Probe avg build tokens | Probe avg query tokens | Avg rerank tokens when applied |
|---|---:|---:|---:|
| LongMemEval-S | `86398.54` | `5623.88` | `21078.42` |
| LoCoMo non-adversarial | `45868.0` | `5904.65` | `14581.66` |

Rerank model tokens are reported separately and are not included in build/query LLM token budgets.

## Diagnosis

The method is clean, but the scope is wrong. The current pipeline expands candidate retrieval to `pool_k=60` whenever rerank applies by information need. That also changes the candidate pool for rows that were supposed to stay protected by lower effective top-k profiles, so v226 is not a narrow tail-noise filter.

The LoCoMo probe is especially unstable: `fact_lookup` has evidence-row diff `22/27`, and total answer drift reaches `32/80`. LongMemEval-S also shows broad drift, including `18/50` prompt/evidence changes. This fails the intended "small, source-preserving retrieval-tail intervention" gate, so full prediction and dual judge are not worth running for v226.

## Next Step

Supersede v226 with a general rerank activation gate: only expand candidate pool and call rerank when the route's pre-rerank effective `top_k` is large enough to expose a genuine tail region. This should be configured as a method-level retrieval constraint, not as a benchmark or sample rule.

## Artifacts

- Method commit: `a6843598050081dfdfe896639e06abc72937ca75`
- Config: `configs/stage1_fact_list_tail_rerank_filter_v226_seeded_qwen36_no_think_build4k_cached.json`
- LME probe: `experiments/diagnostic/stage1_fact_list_tail_rerank_filter_v226_lme_probe50/`
- LoCoMo probe: `experiments/diagnostic/stage1_fact_list_tail_rerank_filter_v226_locomo_probe80/`
- Outputs: `outputs/diagnostic/stage1_fact_list_tail_rerank_filter_v226_lme_probe50/`, `outputs/diagnostic/stage1_fact_list_tail_rerank_filter_v226_locomo_probe80/`
- Git status during runs: dirty because the probe experiment directories were untracked after the method commit.
