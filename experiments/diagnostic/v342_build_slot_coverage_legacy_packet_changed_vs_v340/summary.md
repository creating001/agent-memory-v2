# v342_build_slot_coverage_legacy_packet_changed_vs_v340

## Purpose

Paired changed-answer judge for v342 vs v340 on probe50. v342 keeps v341 build-owned slot coverage metadata but disables the v341 short compact-packet header and packet-line dedupe, so this run checks whether the conservative prompt rollback recovers v341's LoCoMo regression.

## Scope

- LoCoMo non-adversarial probe50: 20 changed answers.
- LongMemEval-S probe50: 5 changed answers.
- Judge: dual `deepseek-v4-flash`, temperature `0`, default thinking.
- Clean boundary: gold labels and judge outputs are used only after prediction; they are not consumed by build, retrieval, compiler, answer, verifier, or cache construction.

## Metrics

| Benchmark | Version | Changed n | Strict | Lenient |
|---|---:|---:|---:|---:|
| LoCoMo | v340 | 20 | `18/20` | `19/20` |
| LoCoMo | v342 | 20 | `17/20` | `17/20` |
| LongMemEval-S | v340 | 5 | `4/5` | `4/5` |
| LongMemEval-S | v342 | 5 | `5/5` | `5/5` |

Token probe summary:

- LoCoMo answer probe50 avg query tokens: v340 `5577.30` -> v342 `5590.30`.
- LongMemEval-S answer probe50 avg query tokens: v340 `5402.98` -> v342 `5396.60`.
- v342 config explicitly records `working_memory_packet_compact_short_header=false` and `working_memory_packet_compact_dedupe=false`.

## Diagnosis

v342 improves traceability by turning v341 compact-packet prompt compression into explicit opt-in switches and defaulting them off. This prevents old configs from silently inheriting v341's short header and dedupe behavior.

It still should not become LTS. LoCoMo changed-answer accuracy remains worse than v340, even after disabling the prompt compression. The likely remaining issue is that build-owned coverage/value propagation changes which packet entries expose visible `hint=` text. The next version should keep coverage metadata for slot guard, audit, and diagnostics, but prevent coverage-derived fields from changing compact packet visible hints or candidate ordering unless explicitly enabled and judged.

## Outputs

- `locomo_v340_dual_judge.json`
- `locomo_v342_dual_judge.json`
- `lme_v340_dual_judge.json`
- `lme_v342_dual_judge.json`
- `changed_answer_diff.json`
