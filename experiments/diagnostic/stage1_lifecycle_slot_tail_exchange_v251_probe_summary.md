# stage1_lifecycle_slot_tail_exchange_v251_probe_summary

## Purpose

Evaluate v251 as a conservative successor to v250 LTS: source-backed lifecycle slot-chain hits for `current_state` / `profile_preference` are allowed to enter only the retrieval tail, while typed memory text remains excluded from reader evidence and object-slot activation stays list-count tail rescue.

## Config

- algorithm commit: `e5645c7`
- config: `configs/stage1_lifecycle_slot_tail_exchange_v251_seeded_qwen36_no_think_build4k_cached.json`
- parent LTS: `configs/stage1_object_slot_tail_rescue_v250_seeded_qwen36_no_think_build4k_cached.json`
- clean boundary: prediction uses no labels, judge output, benchmark tags, sample ids, test feedback, gold answers, or sample-level rules.

## Probe Result

| Benchmark | scope | slot-chain applied | answer diff vs v250 | retrieval/final evidence diff vs v250 | avg build/query tokens |
|---|---:|---:|---:|---:|---:|
| LongMemEval-S | `50` | `1/50` | `0/50` | `0/50` / `0/50` | `86398.54 / 5677.40` |
| LoCoMo non-adversarial | `50` | `0/50` | `0/50` | `0/50` / `0/50` | `45868.00 / 6543.56` |

The single LME activation projected two source rows for a profile-preference slot, but `tail_exchange_protect_top_n=56` protected the whole effective candidate set on the relevant long-context route, so the final candidate/evidence order was unchanged.

## Decision

Do not promote v251. It is clean and low risk, but too conservative to create a performance opportunity. The useful lesson is to express tail exchange as "protect all but the last N candidate rows" rather than a fixed absolute protect count, because effective `top_k` varies by route and granularity profile.

Next: v252 should keep the same source-backed lifecycle slot-chain gate but add an explicit `tail_exchange_max_swaps` cap so a 40-row route can still exchange only its final 4 rows while a 60-row route protects the first 56 rows.

## Outputs

- LME records: `experiments/diagnostic/stage1_lifecycle_slot_tail_exchange_v251_lme_probe50/`
- LME predictions/traces: `outputs/diagnostic/stage1_lifecycle_slot_tail_exchange_v251_lme_probe50/`
- LoCoMo records: `experiments/diagnostic/stage1_lifecycle_slot_tail_exchange_v251_locomo_probe50/`
- LoCoMo predictions/traces: `outputs/diagnostic/stage1_lifecycle_slot_tail_exchange_v251_locomo_probe50/`
