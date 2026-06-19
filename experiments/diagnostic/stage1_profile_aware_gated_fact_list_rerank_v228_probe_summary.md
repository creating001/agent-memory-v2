# stage1_profile_aware_gated_fact_list_rerank_v228 probe summary

## Decision

V228 passes the probe gate and should proceed to full prediction and changed-answer judge.

## Method

V228 inherits v225 LTS and supersedes v227 with `retrieval.route_override_precedence = before_profile`. Route overrides can set default-context fact/list/current/profile behavior, while `long_context_pressure` still overrides them when selected. Fact/list rerank is additionally gated by `min_effective_top_k = 56`, so lower-context profiles do not expand to the rerank pool.

## Probe Results

| Benchmark | Probe | prompt diff | evidence rows diff | retrieval hits diff | answer diff | rerank applied | answer cache |
|---|---:|---:|---:|---:|---:|---:|---:|
| LongMemEval-S | `50` | `0/50` | `0/50` | `0/50` | `0/50` | `0/50` | `50/0` |
| LoCoMo non-adversarial | `80` | `22/80` | `22/80` | `27/80` | `10/80` | `41/80` | `58/22` |

LoCoMo changed-answer paired dual judge on the `10` changed answers:

| Side | strict | lenient |
|---|---:|---:|
| v225 | `7/10` | `7/10` |
| v228 | `9/10` | `9/10` |

## Cost Snapshot

| Benchmark | Probe avg build tokens | Probe avg query tokens | Rerank tokens |
|---|---:|---:|---:|
| LongMemEval-S | `86398.54` | `5679.58` | `0` |
| LoCoMo non-adversarial | `45868.0` | `6316.45` | `597848` |

Rerank model tokens are reported separately from build/query LLM visible tokens.

## Clean Boundary

- Prediction uses only question text, raw Memory Context, visible metadata, and build-stage memory generated before the question.
- The v228 answer cache was seeded from v225 prediction-time traces and predictions only, to avoid prompt-identical answer drift. It did not read labels, judge outputs, benchmark categories, sample ids, test feedback, or gold answers.
- The paired judge reads labels only after prediction for offline evaluation and is not used by retrieval, compiler, answer, repair, finalizer, or cache construction.

## Artifacts

- Method commit: `6ec5529a93c81e78e7f4cb09ffef1cead93d70a1`
- Config: `configs/stage1_profile_aware_gated_fact_list_rerank_v228_seeded_qwen36_no_think_build4k_cached.json`
- LME probe: `experiments/diagnostic/stage1_profile_aware_gated_fact_list_rerank_v228_lme_probe50/`
- LoCoMo probe: `experiments/diagnostic/stage1_profile_aware_gated_fact_list_rerank_v228_locomo_probe80/`
- Changed-answer judge outputs: `outputs/diagnostic/stage1_profile_aware_gated_fact_list_rerank_v228_changed_vs_v225/`
