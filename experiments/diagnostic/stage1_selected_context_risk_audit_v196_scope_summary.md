# stage1_selected_context_risk_audit_v196 LTS summary

## Decision

V196 replaces v194 as the current local LTS.

V196 inherits v194 and adds a trace-only selected-context risk audit. The audit reuses the clean source-grounded self-reference check from the rejected v195 hard gate, but only records which temporal selected-context center rows would fail role/self-reference/question-slot coverage checks. It never removes rows, changes retrieval order, changes prompts, or changes answers.

## Clean Boundary

- Prediction uses only question text, raw Memory Context, visible metadata, and build-stage memory generated before the question.
- No gold answer, judge output, benchmark label, sample id, row index, test feedback, or sample-level rule is used by retrieval, compiler, answer, repair, finalizer, audit, or cache construction.
- Answer cache seeding used prediction-time traces and predictions only; no labels or judge outputs were read.
- The selected-context risk audit is trace-only and is not included in the answer prompt.

## Full Verification

| Benchmark | v196 vs v194 prompt diff | v196 vs v194 answer diff | v196 answer cache | Inherited judge accuracy |
|---|---:|---:|---:|---:|
| LongMemEval-S full | `0/500` | `0/500` | `500/0/0` | strict/lenient `0.834000 / 0.846000` |
| LoCoMo non-adversarial full | `0/1540` | `0/1540` | `1540/0/0` | strict/lenient `0.793506 / 0.818831` |

## Audit Coverage

| Benchmark | audit applied | audited selected-context rows | risk rows |
|---|---:|---:|---:|
| LongMemEval-S full | `0/500` | `0` | `0` |
| LoCoMo non-adversarial full | `329/1540` | `1316` | `1083` |

Activation probe:

- Jon row: prompt/answer unchanged, audit risk rows `0`.
- Nate row: prompt/answer unchanged, audit flags two weak selected-context rows (`insufficient_slot_coverage`, `missing_self_reference`) while v194 `mention_time_fallback` keeps answer `2022-08-22`.
- John/James row: prompt/answer unchanged, audit flags four wrong-speaker/low-coverage selected-context rows, including `D17:29` as `missing_self_reference`.

## Why This Is LTS

V195 proved that turning the same source-grounded self-reference check into a hard selected-context gate reduces token/context noise but hurts LoCoMo accuracy. V196 keeps the useful part: it makes the risk visible and measurable while preserving v194 behavior. This reduces #3 selected-context heuristic risk and supports future conflict-aware activation without sacrificing v194 accuracy.

## Artifacts

- Config: `configs/stage1_selected_context_risk_audit_v196_seeded_qwen36_no_think_build4k_cached.json`
- Method commit: `a21d12bb37fd92a28b470552f616b5c63d3fc9d1`
- Activation probe: `experiments/diagnostic/stage1_selected_context_risk_audit_v196_activation_probe/`
- LME full: `experiments/diagnostic/stage1_selected_context_risk_audit_v196_lme_s_full/`
- LoCoMo full: `experiments/diagnostic/stage1_selected_context_risk_audit_v196_locomo_nonadv_full/`
- Outputs: `outputs/diagnostic/stage1_selected_context_risk_audit_v196_*`

## Next

- Use v196 audit traces to design a narrow conflict-aware activation that annotates risky selected-context rows instead of globally blocking them.
- Keep v195 hard selected-context gate rejected.
- Continue #5 lifecycle/state/conflict work with source-backed typed memory and raw evidence verification.
