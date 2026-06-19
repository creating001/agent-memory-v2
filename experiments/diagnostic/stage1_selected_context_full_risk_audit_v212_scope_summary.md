# stage1_selected_context_full_risk_audit_v212 LTS summary

## Decision

V212 replaces v211 as the current local LTS.

V212 is a trace-only #3 selected-context risk audit expansion. It keeps v211 prediction behavior and judge accuracy unchanged, but broadens `retrieval.selected_context.risk_audit.information_needs` from `temporal_lookup` to `fact_lookup`, `list_count`, `profile_preference`, `temporal_lookup`, and `current_state`.

## Clean Boundary

- Prediction uses only question text, raw Memory Context, visible metadata, and build-stage memory generated before the question.
- No gold answer, judge output, benchmark label, sample id, row index, test feedback, or sample-level rule is used by retrieval, compiler, answer, repair, finalizer, audit, cache construction, or selector thresholds.
- The selected-context risk audit is trace-only. It is not included in retrieval, compiler prompts, answer, repair, finalizer, or cache keys.

## Full Verification

| Benchmark | answer diff vs v211 | route diff | prompt diff | evidence rows diff | retrieval hits diff | effective selected-context diff | answer cache | inherited judge accuracy |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| LongMemEval-S full | `0/500` | `0/500` | `0/500` | `0/500` | `0/500` | `0/500` | `500/0/0` | strict/lenient `0.834000 / 0.846000` |
| LoCoMo non-adversarial full | `0/1540` | `0/1540` | `0/1540` | `0/1540` | `0/1540` | `0/1540` | `1540/0/0` | strict/lenient `0.793506 / 0.818831` |

Token accounting is unchanged from v211/v209:

| Benchmark | avg build tokens | avg query tokens |
|---|---:|---:|
| LongMemEval-S full | `85393.566` | `6580.196` |
| LoCoMo non-adversarial full | `62015.57402597403` | `6095.268181818182` |

Because both full predictions are answer-identical to v211, v212 inherits the v211/v209/v207/v206 dual DeepSeek flash judge records. No changed-answer judge is needed.

## Selected-context Audit

| Benchmark | audit applied samples | audited rows | risk rows | Notes |
|---|---:|---:|---:|---|
| LongMemEval-S full | `0/500` | `0` | `0` | Effective selected-context is already absent on LME. |
| LoCoMo non-adversarial full | `1493/1540` | `8300` | `7423` | Audit now covers fact/list/profile/temporal selected-context rows, not only temporal. |

LoCoMo risk rows by information need:

| information_need | samples | audited rows | risk rows |
|---|---:|---:|---:|
| `fact_lookup` | `856` | `5136` | `4634` |
| `list_count` | `264` | `1584` | `1471` |
| `profile_preference` | `44` | `264` | `235` |
| `temporal_lookup` | `329` | `1316` | `1083` |

## Why This Is LTS

V212 is safer than v211 for #3 because selected-context risk is no longer mostly hidden outside temporal routes. The method is still conservative: it does not change selected-context materialization, evidence rows, prompts, or answers.

Residual risks remain:

- #2: final prompt/query tokens remain above the normal target on both full benchmarks. v210 showed mechanical text compression is unsafe.
- #3: v212 is an audit, not a mitigation. The next step should use this trace to design source-backed selected-context gates or organization views.
- #5: typed memory remains source-backed activation/organization support; broader memory lifecycle/state reasoning still needs improvement.

## Artifacts

- Method commit: `ff7990d712c766604628ef11f0de3031c2984661`
- LME evidence commit: `b636f7abc9a58a79eecce4325b17630c5bc8ea9c`
- LME full: `experiments/diagnostic/stage1_selected_context_full_risk_audit_v212_lme_s_full/`
- LoCoMo full: `experiments/diagnostic/stage1_selected_context_full_risk_audit_v212_locomo_nonadv_full/`
- Outputs: `outputs/diagnostic/stage1_selected_context_full_risk_audit_v212_*`

