# v302 Operation Evidence Coverage Audit Full Summary

## Status

Promoted to LTS. v302 extends v301 with a trace-only `memory_operation_evidence_coverage_audit`.

The new audit consumes `memory_operation_plan_v1` and `memory_query_readiness_manifest_v1` to check whether each guarded operation plan's current/historical/source-expansion chain is visible in the raw Memory rows already selected for the prompt. It does not change retrieval, prompt text, answer generation, repair, finalizer, or final evidence.

This is a system step toward a more complete Agent Memory lifecycle: operation plans now support context organization through v301 and source-backed evidence coverage verification/audit through v302.

## Configuration

- Commit: `f44a789a89663c67c82fae72944b380d897c2ae8`
- Config: `configs/stage1_operation_evidence_coverage_audit_v302_query_restore_seeded_qwen36_no_think_build4k_cached.json`
- Baseline: v301 LTS
- Prediction workers: LME `6`, LoCoMo `6`
- Coverage audit scope: `current_state`
- `memory_operation_evidence_coverage_audit=true`
- `memory_operation_evidence_coverage_audit_max_plans=4`
- Prompt-visible operation guide: disabled
- Derived values rendered to prompt: `0`
- Git dirty note: LME manifest records `dirty=false`; LoCoMo manifest records `dirty=true` only because the paired LME formal directory existed during concurrent prediction.

## Full Metrics

Full accuracy is inherited from v301 because v302 full predictions are answer-identical and prompt-identical on both benchmarks.

| Benchmark | n | strict/lenient accuracy | avg build tokens | avg query tokens | answer diff vs v301 | prompt diff vs v301 |
|---|---:|---:|---:|---:|---:|---:|
| LongMemEval-S full | 500 | `0.834000 / 0.846000` (`417/500`, `423/500`) | `85393.566` | `6455.588` | `0` | `0` |
| LoCoMo non-adversarial full | 1540 | `0.794156 / 0.819481` (`1223/1540`, `1262/1540`) | `62015.57402597403` | `6093.879220779221` | `0` | `0` |

## Coverage Audit

| Benchmark | audit present/applied | selected plans | selected sources | visible sources | missing sources | full/partial/none coverage plans |
|---|---:|---:|---:|---:|---:|---:|
| LongMemEval-S full | `22/22` | `88` | `305` | `31` | `274` | `5 / 18 / 65` |
| LoCoMo non-adversarial full | `3/3` | `12` | `58` | `12` | `46` | `0 / 7 / 5` |

Current/historical coverage is tracked separately:

| Benchmark | current visible/missing | historical visible/missing |
|---|---:|---:|
| LongMemEval-S full | `31 / 268` | `31 / 268` |
| LoCoMo non-adversarial full | `12 / 44` | `12 / 44` |

These numbers are intentionally diagnostic, not a prompt feature. They show that v301/v302 now know where operation-plan source chains are under-covered, which gives the next source-expansion policy a clean, source-backed target instead of heuristic row pushing.

## Method Rationale

This follows the external-method direction already documented in `docs/method.md` and `experiments/method_coverage.md`: GraphRAG/HippoRAG/Mnemis/Hindsight-style graph or typed memory should expand back to raw evidence, not replace it. v302 adds the audit boundary needed before a future expansion consumer can safely add missing raw rows.

## Decision

Promote v302 to LTS. Relative to v301, it reduces the "memory too shallow" and answer/verifier systemization risks with no answer, prompt, or token regression. It also prepares the next step: a guarded source-expansion consumer that uses missing-source coverage rather than benchmark-shaped heuristics.

## Artifacts

- LME formal record: `experiments/formal/stage1_operation_evidence_coverage_audit_v302_lme_s_full_f44a789/`
- LoCoMo formal record: `experiments/formal/stage1_operation_evidence_coverage_audit_v302_locomo_nonadv_full_f44a789/`
- LME predictions: `outputs/formal/stage1_operation_evidence_coverage_audit_v302_lme_s_full_f44a789/predictions.jsonl`
- LME traces: `outputs/formal/stage1_operation_evidence_coverage_audit_v302_lme_s_full_f44a789/traces.jsonl`
- LoCoMo predictions: `outputs/formal/stage1_operation_evidence_coverage_audit_v302_locomo_nonadv_full_f44a789/predictions.jsonl`
- LoCoMo traces: `outputs/formal/stage1_operation_evidence_coverage_audit_v302_locomo_nonadv_full_f44a789/traces.jsonl`

## Verification

- `python -m py_compile src/memory/compiler.py src/memory/pipeline.py src/tests/test_compiler.py`
- `python -m pyflakes src`
- `python -m unittest discover -s src/tests`
- Full LME and LoCoMo predictions with `6` workers
- Full answer diff vs v301: LME `0/500`, LoCoMo `0/1540`
- Full prompt diff vs v301: LME `0/500`, LoCoMo `0/1540`
