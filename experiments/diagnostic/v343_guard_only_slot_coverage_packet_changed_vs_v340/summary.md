# v343_guard_only_slot_coverage_packet_changed_vs_v340

## Purpose

Paired changed-answer judge for v343 vs v340 on probe50. v343 keeps build-owned slot coverage for slot guard, audit, and diagnostics, but prevents conflict-slot `values` from becoming prompt-visible Working Memory Packet `hint=` text.

## Scope

- LoCoMo non-adversarial probe50: 17 changed answers.
- LongMemEval-S probe50: 4 changed answers.
- Judge: dual `deepseek-v4-flash`, temperature `0`, default thinking.
- Clean boundary: gold labels and judge outputs are used only after prediction; they are not consumed by build, retrieval, compiler, answer, verifier, or cache construction.

## Metrics

| Benchmark | Version | Changed n | Strict | Lenient |
|---|---:|---:|---:|---:|
| LoCoMo | v340 | 17 | `14/17` | `15/17` |
| LoCoMo | v343 | 17 | `14/17` | `15/17` |
| LongMemEval-S | v340 | 4 | `4/4` | `4/4` |
| LongMemEval-S | v343 | 4 | `4/4` | `4/4` |

Token probe summary:

- LoCoMo answer probe50 avg query tokens: v340 `5577.30` -> v343 `5592.62`.
- LongMemEval-S answer probe50 avg query tokens: v340 `5402.98` -> v343 `5427.60`.
- v343 compile-scan vs v340: LoCoMo prompt changed `2/50`, avg context-char delta `+1.74`; LongMemEval-S prompt changed `5/50`, avg context-char delta `-1.18`.

## Diagnosis

v343 is a better risk-control version than v341/v342 because coverage no longer broadly changes compact packet visible hints. The paired changed-answer judge is neutral against v340 on both benchmarks.

It should not become LTS yet: probe50 query tokens are higher than v340 on both benchmarks, and full accuracy has not been run. Keep the guard-only coverage policy as the safe default for future build-owned memory system work; continue query-token reduction through build-time workspace views that do not alter raw evidence or packet hints without paired judge support.

## Outputs

- `locomo_v340_dual_judge.json`
- `locomo_v343_dual_judge.json`
- `lme_v340_dual_judge.json`
- `lme_v343_dual_judge.json`
- `changed_answer_diff.json`
