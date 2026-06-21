# v292 Memory Operation Plan Guide Full Summary

## Purpose

Test whether v291 `memory_operation_plan_v1` can be consumed directly at query time as a compact, source-backed operation contract, replacing the older `Managed Memory State Guide` and `Memory Value Slot Guide` for `current_state`.

This is a query simplification experiment, not a build change. Build/retrieval/answer settings remain v291-equivalent. Raw Memory rows remain final evidence.

## Config

- Config: `configs/stage1_memory_operation_plan_guide_v292_query_simplify_seeded_qwen36_no_think_build4k_cached.json`
- Commit: `9b55eacbedc91ae72c9a20b7eb465a16e555b56f`
- Key compiler changes: `memory_operation_plan_guide=true`, `memory_operation_plan_guide_information_needs=["current_state"]`, `memory_state_guide=false`, `memory_value_slot_guide=false`, `memory_workspace_plan=false`.
- Prediction workers: LME `6`, LoCoMo `6`.
- Judge: changed-output dual `deepseek-v4-flash`, temperature `0`, default thinking, API key loaded from local `.env`.

## Full Prediction Metrics

| Benchmark | n | avg build tokens | avg query tokens | answer cache hits/misses | changed answers vs v291 |
|---|---:|---:|---:|---:|---:|
| LongMemEval-S full | 500 | `85393.566` | `6327.884` | `478 / 22` | `12` |
| LoCoMo non-adversarial full | 1540 | `62015.57402597403` | `6094.364285714286` | `1537 / 3` | `1` |

## Changed-Output Judge

| Benchmark | changed n | v291 changed strict/lenient correct | v292 changed strict/lenient correct | merged v292 full strict/lenient |
|---|---:|---:|---:|---:|
| LongMemEval-S full | 12 | `9 / 9` | `4 / 5` | `0.824000 / 0.838000` (`412/500`, `419/500`) |
| LoCoMo non-adversarial full | 1 | `1 / 1` | `1 / 1` | `0.794156 / 0.819481` (`1223/1540`, `1262/1540`) |

## Decision

Rejected as LTS. v292 reduces LME query tokens by replacing two older query guides with the operation-plan guide, but the LME accuracy regression is too large: strict `-5/500`, lenient `-4/500` relative to v291. LoCoMo is flat.

Current LTS remains v291.

## Diagnosis

The result supports the architectural direction but rejects this direct replacement. The build-owned operation plan is useful as a system contract, but a compact current-state prompt is not yet a safe substitute for the older state/value guide behavior. The regression suggests the query side needs either an additive guarded consumer or a richer operation-plan view that preserves active/superseded value specificity, slot alignment, and conflict/source evidence expansion.

Next iteration should not remove the state/value guide wholesale. It should either:

- Distill the old state/value guide semantics into the build operation plan itself, then expose a smaller but equivalent source-backed view.
- Add operation-plan guide only when it can verify the active value and source expansion against visible raw rows without changing otherwise stable answers.
- Use changed-output judge before LTS promotion and keep full metrics merged from unchanged samples.

## Artifacts

- LME predictions: `outputs/diagnostic/stage1_memory_operation_plan_guide_v292_lme_full/predictions.jsonl`
- LME traces: `outputs/diagnostic/stage1_memory_operation_plan_guide_v292_lme_full/traces.jsonl`
- LoCoMo predictions: `outputs/diagnostic/stage1_memory_operation_plan_guide_v292_locomo_full/predictions.jsonl`
- LoCoMo traces: `outputs/diagnostic/stage1_memory_operation_plan_guide_v292_locomo_full/traces.jsonl`
- Diff/metrics JSON: `experiments/diagnostic/stage1_memory_operation_plan_guide_v292_diff_vs_v291.json`
- Changed subset: `outputs/diagnostic/stage1_memory_operation_plan_guide_v292_changed_vs_v291/`
- Changed judge: `experiments/diagnostic/stage1_memory_operation_plan_guide_v292_changed_vs_v291/`

