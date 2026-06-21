# v347_guard_only_short_packet_changed_vs_v343

## Purpose

Offline changed-answer judge for v347 vs v343 on probe50. v347 inherits v343 guard-only source-backed slot coverage and isolates only Working Memory Packet presentation compression:

- `working_memory_packet_compact_short_header=true`
- `working_memory_packet_compact_dedupe=true`
- route overrides for `current_state`, `fact_lookup`, and `profile_preference` explicitly enable the same two packet-only flags

It does not enable broad `compact_query_guide_blocks`, does not compress Structured Guide / Temporal Aid / raw Memory rows, and does not make conflict-slot values visible as packet hints. Raw Memory rows remain final evidence.

## Scope

- LongMemEval-S probe50: 6 changed answers.
- LoCoMo non-adversarial probe50: 19 changed answers.
- Judge: dual `deepseek-v4-flash`, temperature `0`, default thinking.
- Clean boundary: labels and judge outputs are used only after prediction; they are not consumed by build, retrieval, compiler, answer, verifier, or caches.

## Metrics

| Benchmark | Version | Changed n | Strict | Lenient |
|---|---:|---:|---:|---:|
| LongMemEval-S | v343 | 6 | `5/6` | `5/6` |
| LongMemEval-S | v347 | 6 | `5/6` | `5/6` |
| LoCoMo | v343 | 19 | `18/19` | `18/19` |
| LoCoMo | v347 | 19 | `18/19` | `18/19` |

Token probe summary:

- LongMemEval-S answer probe50 avg query tokens: v343 `5427.60` -> v347 `5357.30`; avg context chars `18034.42` -> `17933.20`; avg build tokens unchanged at `86398.54`.
- LoCoMo answer probe50 avg query tokens: v343 `5592.62` -> v347 `5561.92`; avg context chars `16342.96` -> `16256.72`; avg build tokens unchanged at `45868.00`.
- v347 compile-scan vs v343: evidence row set/order changed `0/50` on both benchmarks; non-WMP prompt changes `0/50`; avg prompt char delta LME `-101.22`, LoCoMo `-86.24`.

Judge cost for this changed-answer diagnostic:

- LME v343/v347 dual judge total tokens: `2215` / `2401`.
- LoCoMo v343/v347 dual judge total tokens: `20027` / `20370`.

## Diagnosis

v347 is a clean query-token candidate, not a new LTS yet. It reduces query tokens by shortening duplicated Working Memory Packet presentation while preserving the raw evidence set and all non-WMP prompt content on the probe50 compile scan. The changed-answer dual judge shows no strict or lenient regression on either benchmark subset, and there are no per-record correct/wrong flips between v343 and v347.

The result is stronger than v344 for this local token-reduction direction because v344 compressed guide semantics broadly and regressed on LoCoMo changed-answer judge. v347 instead keeps guide semantics intact and only compresses packet boilerplate for routes where build-owned `memory_system_state` already supplies source-backed packet items.

Remaining risk: this is still probe50-level evidence. Before promoting into LTS, run a larger cache-aligned prompt/answer diff or full changed-answer judge against the current LTS lineage, and verify that the small token gain remains meaningful outside the probed routes.

## Outputs

- `changed_manifest.json`
- `changed_answer_diff.json`
- `lme_changed_answer_diff.json`
- `locomo_changed_answer_diff.json`
- `lme_v343_dual_judge.json`
- `lme_v347_dual_judge.json`
- `locomo_v343_dual_judge.json`
- `locomo_v347_dual_judge.json`
- `lme_v343_changed_predictions.jsonl`
- `lme_v347_changed_predictions.jsonl`
- `locomo_v343_changed_predictions.jsonl`
- `locomo_v347_changed_predictions.jsonl`
