# stage1_selected_context_term_normalized_audit_v214 LTS summary

## Decision

V214 replaces v213 as the current local LTS.

V214 keeps prediction behavior unchanged and improves only the trace-only selected-context risk audit term matching. It canonicalizes safe singular/plural forms, removes generic question-template terms, and adds small source-backed lexical aliases such as `mom/mum`, `admire/enjoy/like`, and `motivation/support`.

## Clean Boundary

- Prediction uses only question text, raw Memory Context, visible metadata, and build-stage memory generated before the question.
- No gold answer, judge output, benchmark label, sample id, row index, test feedback, or sample-level rule is used by retrieval, compiler, answer, repair, finalizer, audit, cache construction, or selector thresholds.
- The selected-context risk audit is trace-only. It is not included in retrieval, compiler prompts, answer, repair, finalizer, or cache keys.

## Full Verification

| Benchmark | answer diff vs v213 | route diff | prompt diff | evidence rows diff | retrieval hits diff | effective selected-context diff | inherited judge accuracy |
|---|---:|---:|---:|---:|---:|---:|---:|
| LongMemEval-S full | `0/500` | `0/500` | `0/500` | `0/500` | `0/500` | `0/500` | strict/lenient `0.834000 / 0.846000` |
| LoCoMo non-adversarial full | `0/1540` | `0/1540` | `0/1540` | `0/1540` | `0/1540` | `0/1540` | strict/lenient `0.793506 / 0.818831` |

Only `retrieval.selected_context.risk_audit` trace fields differ from v213. Because both full predictions are answer-identical to v213, v214 inherits the v213/v212/v211/v209 dual DeepSeek flash judge records. No changed-answer judge is needed.

Token accounting is unchanged from v213/v209:

| Benchmark | avg build tokens | avg query tokens |
|---|---:|---:|
| LongMemEval-S full | `85393.566` | `6580.196` |
| LoCoMo non-adversarial full | `62015.57402597403` | `6095.268181818182` |

## Selected-context Audit

| Benchmark | audit applied samples | audited rows | v213 risk rows | v214 risk rows | delta |
|---|---:|---:|---:|---:|---:|
| LongMemEval-S full | `0/500` | `0` | `0` | `0` | `0` |
| LoCoMo non-adversarial full | `1493/1540` | `8300` | `6163` | `5841` | `-322` |

LoCoMo risk rows by information need:

| information_need | v213 risk rows | v214 risk rows | delta |
|---|---:|---:|---:|
| `fact_lookup` | `3809` | `3660` | `-149` |
| `list_count` | `1258` | `1135` | `-123` |
| `profile_preference` | `154` | `137` | `-17` |
| `temporal_lookup` | `942` | `909` | `-33` |
| total | `6163` | `5841` | `-322` |

## Why This Is LTS

V214 is safer than v213 for #3 audit fidelity: it reduces prompt-visible selected-context false-positive risk rows without changing retrieval, evidence rows, prompts, answers, token cost, or judge accuracy. It also keeps v213's materialized prompt-visible audit, v212's full-route audit coverage, v211's total-context pressure selector, and v209's conservative context budget.

Residual risks remain:

- #2: final prompt/query tokens remain above the normal target on both full benchmarks.
- #3: v214 improves audit fidelity, not prompt-visible mitigation. The remaining `5841` LoCoMo risk rows should drive the next source-backed selected-context organization/gating step.
- #5: typed memory remains source-backed activation/organization support; broader memory lifecycle/state reasoning still needs improvement.

## Artifacts

- Method commit: `2db0c32d9cbaea7dcb32d01beebf14d752c4dfed`
- LME evidence commit: `16f9f5907022fd32fa7eb7c7ee158f50d251dd98`
- LoCoMo evidence commit: `35456e56e4324fc05ec69397e110f9c004968fe2`
- LME full: `experiments/diagnostic/stage1_selected_context_term_normalized_audit_v214_lme_s_full/`
- LoCoMo full: `experiments/diagnostic/stage1_selected_context_term_normalized_audit_v214_locomo_nonadv_full/`
- Outputs: `outputs/diagnostic/stage1_selected_context_term_normalized_audit_v214_*`
