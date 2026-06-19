# stage1_temporal_activation_audit_v193 LTS summary

## Decision

V193 replaces v191 as the current local LTS.

V193 inherits v191 prompt-side behavior and adds a trace-only Event-Time Candidate Map audit. The audit records prompt-eligible temporal activation candidates, rejected groups, and risk flags such as `exact_today_low_question_coverage`; it is not included in the answer prompt, retrieval, repair, finalizer, or cache key.

## Clean Boundary

- Prediction uses only question text, raw Memory Context, query-time route, visible metadata, and build-stage memory generated before the question.
- No gold answer, judge output, benchmark label, sample id, row index, test feedback, or sample-level rule is used by retrieval, compiler, answer, repair, finalizer, or cache construction.
- Answer cache seeding for v193 used v191 prediction-time traces and predictions only; no labels or judge outputs were read.

## Full Verification

| Benchmark | v193 vs v191 prompt diff | v193 vs v191 answer diff | v193 answer cache | Inherited judge accuracy |
|---|---:|---:|---:|---:|
| LongMemEval-S full | `0/500` | `0/500` | `500/0/0` | strict/lenient `0.834000 / 0.846000` |
| LoCoMo non-adversarial full | `0/1540` | `0/1540` | `1540/0/0` | strict/lenient `0.793506 / 0.818831` |

## Audit Coverage

| Run | audit applied | prompt-eligible candidates | key risk flags |
|---|---:|---:|---|
| activation probe | `3/3` | `3` | flags two `exact_today_low_question_coverage` rows |
| LongMemEval-S full | `10/500` | `0` | no prompt-eligible risk flags |
| LoCoMo non-adversarial full | `241/1540` | `3` | `3` flagged prompt-eligible candidates, including `2` `exact_today_low_question_coverage` rows |

## Why This Is LTS

V193 does not change answer behavior or judge accuracy, but it reduces #5 risk by making temporal activation risk auditable in traces. The previous v191 LTS had a known residual risk: prompt-side `exact_today` activation could be semantically noisy. V193 keeps that behavior for performance stability while exposing the risky activations and rejected groups as structured diagnostics for future clean tightening.

## Artifacts

- Config: `configs/stage1_temporal_activation_audit_v193_seeded_qwen36_no_think_build4k_cached.json`
- Method commit: `f85f80abc80c67b69869d5cf2d8aeecddf3f99c1`
- Activation probe: `experiments/diagnostic/stage1_temporal_activation_audit_v193_activation_probe/`
- LME full: `experiments/diagnostic/stage1_temporal_activation_audit_v193_lme_s_full/`
- LoCoMo full: `experiments/diagnostic/stage1_temporal_activation_audit_v193_locomo_nonadv_full/`
- Outputs: `outputs/diagnostic/stage1_temporal_activation_audit_v193_*`

## Next

- Use v193 traces to design a prompt-side tightening that preserves the Nate positive row.
- Avoid broad visible candidate guides like v192.
- Prefer conflict-aware temporal activation over simple `exact_today` threshold tuning.
