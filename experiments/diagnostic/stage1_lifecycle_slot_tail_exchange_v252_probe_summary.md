# stage1_lifecycle_slot_tail_exchange_v252_probe_summary

## Purpose

Evaluate v252 as a bounded correction to v251 lifecycle slot-chain tail exchange. v252 protects all but the final `4` effective retrieval candidates, so lower-`top_k` route/profile settings can still receive a small source-backed lifecycle tail exchange.

## Config

- algorithm commit: `113798a`
- config: `configs/stage1_lifecycle_slot_tail_exchange_v252_seeded_qwen36_no_think_build4k_cached.json`
- parent LTS: `configs/stage1_object_slot_tail_rescue_v250_seeded_qwen36_no_think_build4k_cached.json`
- clean boundary: prediction uses no labels, judge output, benchmark tags, sample ids, test feedback, gold answers, or sample-level rules.

## Probe Result

| Benchmark | scope | slot-chain applied | answer diff vs v250 | retrieval/final evidence diff vs v250 | avg build/query tokens |
|---|---:|---:|---:|---:|---:|
| LongMemEval-S | `50` | `1/50` | `0/50` | `0/50` / `0/50` | `86398.54 / 5677.40` |
| LoCoMo non-adversarial | `50` | `0/50` | `0/50` | `0/50` / `0/50` | `45868.00 / 6543.56` |

The LME activation was a profile-preference slot whose projected source rows were already present in the final candidate/evidence set. Therefore v252 validates the bounded tail-exchange mechanism but does not create a probe performance opportunity.

## Decision

Do not promote v252 from probe. It is cleaner than v251 because the tail window is route-top-k aware, but the probe coverage is too low and behavior is answer-identical to v250. Keep the code/config as a source-backed lifecycle activation candidate, and prioritize a higher-coverage build-memory management or evidence-utility improvement next.

## Outputs

- LME records: `experiments/diagnostic/stage1_lifecycle_slot_tail_exchange_v252_lme_probe50/`
- LME predictions/traces: `outputs/diagnostic/stage1_lifecycle_slot_tail_exchange_v252_lme_probe50/`
- LoCoMo records: `experiments/diagnostic/stage1_lifecycle_slot_tail_exchange_v252_locomo_probe50/`
- LoCoMo predictions/traces: `outputs/diagnostic/stage1_lifecycle_slot_tail_exchange_v252_locomo_probe50/`
