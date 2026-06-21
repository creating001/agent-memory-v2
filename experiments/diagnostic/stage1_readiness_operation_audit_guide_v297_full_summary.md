# V297 Readiness Operation Audit Guide Full Summary

## Status

Rejected LTS candidate. V297 hides derived operation-plan values from the prompt,
but the prompt-visible operation/audit guide still regresses LongMemEval-S.

## Configuration

- Commit: `5e006ce`
- Config: `configs/stage1_readiness_operation_audit_guide_v297_query_restore_seeded_qwen36_no_think_build4k_cached.json`
- Change vs v296: `memory_operation_plan_guide_render_values=false`.
- Cache protocol: answer cache seeded from v294 prediction-time traces/answers; only prompt-changed samples were regenerated.

## Metrics

| Benchmark | full strict/lenient | avg build tokens | avg query tokens | answer diff vs v294 | changed dual judge |
| --- | ---: | ---: | ---: | ---: | --- |
| LongMemEval-S full | `0.826000 / 0.842000` (`413/500`, `421/500`) | `85393.566` | `6351.784` | `11/500` | old `9/11` strict/lenient, new `5/11` strict and `7/11` lenient |
| LoCoMo non-adversarial full | `0.794156 / 0.819481` (`1223/1540`, `1262/1540`) | `62015.57402597403` | `6094.866233766234` | `1/1540` | old `1/1`, new `1/1` |

## Diagnosis

- All changed answers are `current_state` and include `Memory Operation Plan Guide`.
- All v297 operation guide rows use `values=raw_rows_only`; no derived active/historical/scalar values are rendered.
- Therefore the remaining regression comes from answer-prompt perturbation and operation-guide salience, not only from rendered values.

## Output Paths

- LME prediction: `outputs/formal/stage1_readiness_operation_audit_guide_v297_lme_s_full_5e006ce/predictions.jsonl`
- LoCoMo prediction: `outputs/formal/stage1_readiness_operation_audit_guide_v297_locomo_nonadv_full_5e006ce/predictions.jsonl`
- LME changed judge: `outputs/diagnostic/stage1_readiness_operation_audit_guide_v297_changed_vs_v294_lme/`
- LoCoMo changed judge: `outputs/diagnostic/stage1_readiness_operation_audit_guide_v297_changed_vs_v294_locomo/`

## Next Step

Do not put operation-plan guidance directly into the answer prompt for LTS.
Move the value of readiness/operation planning into build graph, trace audit,
verifier diagnostics, retrieval/context organization, or a future gated consumer
that can prove prompt-behavior equivalence before affecting answer text.
