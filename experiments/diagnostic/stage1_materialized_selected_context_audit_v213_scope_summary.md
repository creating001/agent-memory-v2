# stage1_materialized_selected_context_audit_v213 LTS summary

## Decision

V213 replaces v212 as the current local LTS.

V213 keeps prediction behavior unchanged and fixes the #3 selected-context risk audit to inspect the actual prompt-visible materialized selected-context row, not only the raw center turn. This makes the audit closer to what the answer model really sees and removes a large class of false-positive role/self-reference risks.

## Clean Boundary

- Prediction uses only question text, raw Memory Context, visible metadata, and build-stage memory generated before the question.
- No gold answer, judge output, benchmark label, sample id, row index, test feedback, or sample-level rule is used by retrieval, compiler, answer, repair, finalizer, audit, cache construction, or selector thresholds.
- The selected-context risk audit is trace-only. It is not included in retrieval, compiler prompts, answer, repair, finalizer, or cache keys.

## Full Verification

| Benchmark | answer diff vs v212 | route diff | prompt diff | evidence rows diff | retrieval hits diff | effective selected-context diff | inherited judge accuracy |
|---|---:|---:|---:|---:|---:|---:|---:|
| LongMemEval-S full | `0/500` | `0/500` | `0/500` | `0/500` | `0/500` | `0/500` | strict/lenient `0.834000 / 0.846000` |
| LoCoMo non-adversarial full | `0/1540` | `0/1540` | `0/1540` | `0/1540` | `0/1540` | `0/1540` | strict/lenient `0.793506 / 0.818831` |

Only `retrieval.selected_context.risk_audit` trace fields differ from v212. Because both full predictions are answer-identical to v212, v213 inherits the v212/v211/v209 dual DeepSeek flash judge records. No changed-answer judge is needed.

Token accounting is unchanged from v212/v209:

| Benchmark | avg build tokens | avg query tokens |
|---|---:|---:|
| LongMemEval-S full | `85393.566` | `6580.196` |
| LoCoMo non-adversarial full | `62015.57402597403` | `6095.268181818182` |

## Selected-context Audit

| Benchmark | audit applied samples | audited rows | risk rows | prompt-visible materialized rows | raw-center fallback rows |
|---|---:|---:|---:|---:|---:|
| LongMemEval-S full | `0/500` | `0` | `0` | `0` | `0` |
| LoCoMo non-adversarial full | `1493/1540` | `8300` | `6163` | `8300` | `0` |

LoCoMo risk rows by information need:

| information_need | v212 risk rows | v213 risk rows | delta |
|---|---:|---:|---:|
| `fact_lookup` | `4634` | `3809` | `-825` |
| `list_count` | `1471` | `1258` | `-213` |
| `profile_preference` | `235` | `154` | `-81` |
| `temporal_lookup` | `1083` | `942` | `-141` |
| total | `7423` | `6163` | `-1260` |

The remaining v213 risk reasons are source/text coverage checks: `insufficient_slot_coverage` `4555`, `insufficient_slot_terms` `1608`. The v212-only raw-center role checks `role_not_in_question` and `missing_self_reference` are eliminated under materialized prompt-visible auditing.

## Why This Is LTS

V213 is safer than v212 for #3 because the risk audit now reflects the actual selected-context text shown in the prompt. It reduces audited LoCoMo risk rows from `7423` to `6163` without changing retrieval, evidence rows, prompts, answers, token cost, or judge accuracy.

Residual risks remain:

- #2: final prompt/query tokens remain above the normal target on both full benchmarks. v210 showed mechanical text compression is unsafe.
- #3: v213 improves audit fidelity, not prompt-visible mitigation. The remaining `6163` LoCoMo risk rows should drive the next source-backed selected-context organization/gating step.
- #5: typed memory remains source-backed activation/organization support; broader memory lifecycle/state reasoning still needs improvement.

## Artifacts

- Method commit: `f039805dd799fbc074653a2cc393d2007614b829`
- LME evidence commit: `b27e375d0195051f53d07623f881f9ee171b8b28`
- LoCoMo evidence commit: `4e42be1c171cd06862076f04d48284eda8ccf79e`
- LME full: `experiments/diagnostic/stage1_materialized_selected_context_audit_v213_lme_s_full/`
- LoCoMo full: `experiments/diagnostic/stage1_materialized_selected_context_audit_v213_locomo_nonadv_full/`
- Outputs: `outputs/diagnostic/stage1_materialized_selected_context_audit_v213_*`
