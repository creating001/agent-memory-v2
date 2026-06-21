# v341_build_slot_coverage_workspace_packet_changed_vs_v340

## Purpose

Paired changed-answer judge for v341 vs v340 on probe50. This isolates the answer changes caused by build-owned slot coverage metadata plus compact workspace packet rendering changes, without re-judging unchanged samples.

## Scope

- LoCoMo non-adversarial probe50: 21 changed answers.
- LongMemEval-S probe50: 2 changed answers.
- Judge: dual `deepseek-v4-flash`, temperature `0`, default thinking.
- Clean boundary: gold labels and judge outputs are used only after prediction; they are not consumed by build, retrieval, compiler, answer, verifier, or cache construction.

## Metrics

| Benchmark | Version | Changed n | Strict | Lenient |
|---|---:|---:|---:|---:|
| LoCoMo | v340 | 21 | `19/21` | `20/21` |
| LoCoMo | v341 | 21 | `18/21` | `18/21` |
| LongMemEval-S | v340 | 2 | `2/2` | `2/2` |
| LongMemEval-S | v341 | 2 | `2/2` | `2/2` |

Token probe summary:

- LoCoMo answer probe50 avg query tokens: v340 `5577.30` -> v341 `5569.94`; compiled context chars delta avg `-78.18`.
- LongMemEval-S answer probe50 avg query tokens: v340 `5402.98` -> v341 `5363.26`; compiled context chars delta avg `-82.28`.

## Diagnosis

v341 is useful as a system-risk diagnostic because slot coverage becomes a build-owned, source-backed index signal rather than a query-time text parsing fallback. It also shows a modest query token reduction on both probe sets.

It should not become LTS: the LoCoMo changed subset regresses from v340 by one strict-correct item and two lenient-correct items. The likely issue is not the build-owned coverage metadata itself, but prompt-visible compact packet shortening/deduplication changing answer behavior. The next version should keep the build-owned coverage interface but avoid broad prompt-visible packet rewrites unless a paired judge confirms no regression.

## Outputs

- `locomo_v340_dual_judge.json`
- `locomo_v341_dual_judge.json`
- `lme_v340_dual_judge.json`
- `lme_v341_dual_judge.json`
- `changed_answer_diff.json`
