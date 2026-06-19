# stage1_object_lifecycle_tail_exchange_v253_probe_summary

## Purpose

Evaluate v253 as a higher-coverage successor to v250/v252. It keeps source-backed lifecycle tail exchange for `current_state` / `profile_preference`, and changes list-count object-slot activation from no-op tail rescue to bounded tail exchange over only the last `4` effective retrieval candidates.

## Config

- algorithm commit: `253f141`
- config: `configs/stage1_object_lifecycle_tail_exchange_v253_seeded_qwen36_no_think_build4k_cached.json`
- parent LTS: `configs/stage1_object_slot_tail_rescue_v250_seeded_qwen36_no_think_build4k_cached.json`
- clean boundary: prediction uses no labels, judge output, benchmark tags, sample ids, test feedback, gold answers, or sample-level rules.

## Probe Result

| Benchmark | scope | object-slot applied | answer diff vs v250 | avg build/query tokens | changed dual judge |
|---|---:|---:|---:|---:|---|
| LongMemEval-S | `50` | `4/50` | `1/50` | `86398.54 / 5678.68` | strict/lenient `1/1 -> 1/1` |
| LoCoMo non-adversarial | `50` | `6/50` | `4/50` | `45868.00 / 6543.68` | strict `1/4 -> 1/4`, lenient `1/4 -> 2/4` |

Changed judge is offline only. LME changed `500 copies` to `500`; both are correct. LoCoMo changed subset has no strict regression and gains one lenient correct item on the family-activities question.

## Decision

Promote v253 to full-candidate status, not LTS yet. It is a cleaner version of the rejected v249 idea because object-slot source rows no longer enter RRF or protected rerank sources; they can only replace a tiny tail window. Probe signal is non-negative and slightly positive on LoCoMo lenient, but full validation is required because object-slot activation can affect list-count aggregation and previous broad collection activation hurt LoCoMo.

## Outputs

- LME records: `experiments/diagnostic/stage1_object_lifecycle_tail_exchange_v253_lme_probe50/`
- LME predictions/traces: `outputs/diagnostic/stage1_object_lifecycle_tail_exchange_v253_lme_probe50/`
- LoCoMo records: `experiments/diagnostic/stage1_object_lifecycle_tail_exchange_v253_locomo_probe50/`
- LoCoMo predictions/traces: `outputs/diagnostic/stage1_object_lifecycle_tail_exchange_v253_locomo_probe50/`
- changed predictions/labels: `outputs/diagnostic/stage1_object_lifecycle_tail_exchange_v253_probe50_changed_vs_v250/`
- changed judge: `experiments/diagnostic/stage1_object_lifecycle_tail_exchange_v253_probe50_changed_vs_v250/`
