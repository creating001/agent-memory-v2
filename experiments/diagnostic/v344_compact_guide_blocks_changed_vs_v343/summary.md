# v344_compact_guide_blocks_changed_vs_v343

## Purpose

Offline changed-answer judge for v344 vs v343 on probe50. v344 keeps v343 guard-only source-backed slot coverage, but enables compact query guide blocks to reduce query prompt tokens without changing raw Memory rows.

## Scope

- LongMemEval-S probe50: 6 changed answers.
- LoCoMo non-adversarial probe50: 27 changed answers.
- Judge: dual `deepseek-v4-flash`, temperature `0`, default thinking.
- Clean boundary: labels and judge outputs are used only after prediction; they are not consumed by build, retrieval, compiler, answer, verifier, or caches.

## Metrics

| Benchmark | Version | Changed n | Strict | Lenient |
|---|---:|---:|---:|---:|
| LongMemEval-S | v343 | 6 | `5/6` | `5/6` |
| LongMemEval-S | v344 | 6 | `6/6` | `6/6` |
| LoCoMo | v343 | 27 | `24/27` | `24/27` |
| LoCoMo | v344 | 27 | `21/27` | `23/27` |

Token probe summary:

- LongMemEval-S answer probe50 avg query tokens: v343 `5427.60` -> v344 `5340.08`.
- LoCoMo answer probe50 avg query tokens: v343 `5592.62` -> v344 `5486.80`.
- v344 compile-scan vs v343: evidence row order changed `0/50` on both benchmarks; avg prompt char delta LME `-222.00`, LoCoMo `-511.36`.

## Diagnosis

v344 is not an LTS candidate. It reduces query tokens, but compacting guide/workpad wording weakens LoCoMo answer behavior. Strict losses concentrate in general temporal/list/inference cases:

- Temporal precision loss: one answer collapsed a supported week interval to `June 2023`.
- List/scope drift: one answer included a related but wrong event.
- Over-abstention: one inference answer became insufficient despite enough source context.

The lesson is that guide compression can save tokens but should not be applied as a broad default. Next query-token work should target source-neutral fixed layout, component-level policy with paired judge, or build-owned source expansion that preserves the existing guide semantics.

## Outputs

- `changed_manifest.json`
- `changed_answer_diff.json`
- `lme_v343_dual_judge.json`
- `lme_v344_dual_judge.json`
- `locomo_v343_dual_judge.json`
- `locomo_v344_dual_judge.json`
- `lme_v343_changed_predictions.jsonl`
- `lme_v344_changed_predictions.jsonl`
- `locomo_v343_changed_predictions.jsonl`
- `locomo_v344_changed_predictions.jsonl`
