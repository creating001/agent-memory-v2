# v299 Memory Operation Context Organizer Full Summary

## Status

Rejected LTS candidate. v299 is a clean but too-aggressive first consumer of the v298 operation/readiness artifacts.

The method keeps derived memory out of the answer prompt and final evidence, then uses `memory_operation_plan_v1` plus `memory_query_readiness_manifest_v1` to reorder already selected raw Memory rows for `current_state` queries. This makes build-stage memory operations participate in context organization, but the current hard row-order boost regresses LongMemEval-S.

## Configuration

- Commit: `2d536c840943c5fc21171e9d57a46e1e653f29bb`
- Config: `configs/stage1_memory_operation_context_organizer_v299_query_restore_seeded_qwen36_no_think_build4k_cached.json`
- Baseline: current LTS v298, `configs/stage1_memory_operation_readiness_audit_v298_query_restore_seeded_qwen36_no_think_build4k_cached.json`
- Prediction workers: LME `6`, LoCoMo `6`
- New compiler setting: `memory_operation_context_organizer=true`
- Scope: `current_state`
- Max selected plans per query: `4`
- Prompt-visible operation guide: disabled
- Derived values rendered to prompt: `0`
- Final answer evidence policy: raw Memory rows only

## Full Metrics

Full accuracy is merged from v298 full dual judge counts plus v299 changed-output dual judge. Unchanged answers inherit v298 judgment; changed answers are judged offline with two independent `deepseek-v4-flash` runs at temperature `0` using `.env` for the API key.

| Benchmark | n | strict/lenient accuracy | avg build tokens | avg query tokens | answer diff vs v298 | prompt diff vs v298 |
|---|---:|---:|---:|---:|---:|---:|
| LongMemEval-S full | 500 | `0.824000 / 0.838000` (`412/500`, `419/500`) | `85393.566` | `6301.32` | `10` | `22` |
| LoCoMo non-adversarial full | 1540 | `0.794156 / 0.819481` (`1223/1540`, `1262/1540`) | `62015.57402597403` | `6094.0032467532465` | `1` | `3` |

## Changed-Output Judge

| Benchmark | changed answers | base strict/lenient | v299 strict/lenient | strict delta | lenient delta |
|---|---:|---:|---:|---:|---:|
| LongMemEval-S full | `10` | `9/10`, `9/10` | `4/10`, `5/10` | `-5` | `-4` |
| LoCoMo non-adversarial full | `1` | `1/1`, `1/1` | `1/1`, `1/1` | `0` | `0` |

The LME regression comes from current-state salience changes: examples that were correct under v298 become shorter refusals, wrong current values, or less complete list/order answers after operation-plan-backed row reordering.

## Organizer Coverage

| Benchmark | organizer applied | changed order | ready visible plans | selected plans | boosted raw source ids | values rendered |
|---|---:|---:|---:|---:|---:|---:|
| LongMemEval-S full | `22` | `22` | `357` | `88` | `118` | `0` |
| LoCoMo non-adversarial full | `3` | `3` | `65` | `12` | `16` | `0` |

The mechanism is clean: it only reorders visible raw rows whose source ids are backed by guarded-ready operation plans. It does not add hidden facts, render derived memory values, change retrieval candidates, enable repair/finalizer, or use judge/gold/sample-id information.

## Diagnosis

v299 validates the direction but not this consumer design.

- Positive: build-time operation/readiness artifacts can drive an auditable context organization step without exposing derived values.
- Negative: hard prioritization of operation-plan sources is too strong for LME current-state questions. It can demote high-salience existing evidence and produce under-specific or incorrect answers.
- Lesson: the next consumer should be softer and more local: use operation plans for source expansion, conflict-state verification, or answer audit first, and preserve original retrieval rank/anchor evidence unless the operation utility clearly resolves a current/superseded conflict.

## Decision

Do not promote v299 to LTS. Current LTS remains v298.

The method reduces the "memory too shallow" risk in mechanism, but it increases context-organization risk and causes an LME accuracy regression. The next iteration should keep the build-stage system idea while replacing hard row-order boosts with a guarded, source-backed utility policy that can be ablated independently.

## Artifacts

- LME formal record: `experiments/formal/stage1_memory_operation_context_organizer_v299_lme_s_full_2d536c8/`
- LoCoMo formal record: `experiments/formal/stage1_memory_operation_context_organizer_v299_locomo_nonadv_full_2d536c8/`
- LME predictions: `outputs/formal/stage1_memory_operation_context_organizer_v299_lme_s_full_2d536c8/predictions.jsonl`
- LME traces: `outputs/formal/stage1_memory_operation_context_organizer_v299_lme_s_full_2d536c8/traces.jsonl`
- LoCoMo predictions: `outputs/formal/stage1_memory_operation_context_organizer_v299_locomo_nonadv_full_2d536c8/predictions.jsonl`
- LoCoMo traces: `outputs/formal/stage1_memory_operation_context_organizer_v299_locomo_nonadv_full_2d536c8/traces.jsonl`
- LME changed judge: `outputs/diagnostic/stage1_memory_operation_context_organizer_v299_changed_vs_v298_lme/`
- LoCoMo changed judge: `outputs/diagnostic/stage1_memory_operation_context_organizer_v299_changed_vs_v298_locomo/`

## Verification

- `python -m py_compile src/memory/compiler.py src/memory/pipeline.py src/tests/test_compiler.py`
- `python -m pyflakes src`
- `python -m unittest discover -s src/tests`
- Full LME and LoCoMo predictions
- Changed-output dual `deepseek-v4-flash` judge for answer diffs
