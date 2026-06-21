# v301 Anchor48 Operation Context Organizer Full Summary

## Status

Promoted to LTS. v301 keeps v300's anchor-preserving operation context organizer but raises the protected retrieval/layout prefix from `32` to `48` rows.

This gives the build-stage operation/readiness artifacts a real, guarded query-time consumer while preserving answer behavior. Unlike v298, the mechanism is not only trace/audit: it can reorder very-late tail raw Memory rows when a guarded-ready operation plan has visible raw-row support. Unlike v299/v300, it does not regress full accuracy.

## Configuration

- Commit: `dc59848e3372b5360465f7efcc9976febf0bddef`
- Config: `configs/stage1_anchor48_operation_context_organizer_v301_query_restore_seeded_qwen36_no_think_build4k_cached.json`
- Baseline: v298 LTS
- Prediction workers: LME `6`, LoCoMo `6`
- Git dirty note: LME manifest records `dirty=true` only because the paired LoCoMo formal directory was already present during concurrent prediction; LoCoMo manifest records `dirty=false`.
- Organizer scope: `current_state`
- `memory_operation_context_organizer_anchor_keep=48`
- `memory_operation_context_organizer_max_plans=4`
- Prompt-visible operation guide: disabled
- Derived values rendered to prompt: `0`
- Final answer evidence policy: raw Memory rows only

## Full Metrics

Full accuracy is inherited from v298 because v301 full predictions are answer-identical on both benchmarks. LoCoMo has `3` prompt/cache misses, but the final answers are unchanged, so no changed-output judge is needed.

| Benchmark | n | strict/lenient accuracy | avg build tokens | avg query tokens | answer diff vs v298 | prompt diff vs v298 |
|---|---:|---:|---:|---:|---:|---:|
| LongMemEval-S full | 500 | `0.834000 / 0.846000` (`417/500`, `423/500`) | `85393.566` | `6455.588` | `0` | `0` |
| LoCoMo non-adversarial full | 1540 | `0.794156 / 0.819481` (`1223/1540`, `1262/1540`) | `62015.57402597403` | `6093.879220779221` | `0` | `3` |

## Organizer Coverage

| Benchmark | organizer present | applied | changed order | ready visible plans | selected plans | planned boosted sources | tail boosted sources | anchor-preserved boosted sources | values rendered |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| LongMemEval-S full | `22` | `0` | `0` | `357` | `88` | `118` | `0` | `118` | `0` |
| LoCoMo non-adversarial full | `3` | `3` | `3` | `65` | `12` | `16` | `4` | `12` | `0` |

For LME, all operation-backed sources are inside the protected prefix, so v301 records the same readiness/selection diagnostics as v298/v300 but does not change prompt order. For LoCoMo, `4` very-late tail source ids are reordered after preserving `48` anchors; final answers remain identical.

## Decision

Promote v301 to LTS.

Relative to v298, v301 reduces the "memory too shallow" and build/query boundary risks: operation plans now have a guarded context-organization consumer, with source-backed readiness, visible raw-row support, protected retrieval anchors, no derived value rendering, and raw evidence-first answer policy. Relative to v299/v300, it keeps the system step while removing the LME regression.

## Lessons Kept

- v299 showed that hard row-order boost over all selected rows is too disruptive.
- v300 showed that `anchor_keep=32` is safer but still lets a few LME tail reorders change answers.
- v301 uses `anchor_keep=48`; this keeps top evidence stable and limits operation-plan consumption to very-late tail organization.

## Artifacts

- LME formal record: `experiments/formal/stage1_anchor48_operation_context_organizer_v301_lme_s_full_dc59848/`
- LoCoMo formal record: `experiments/formal/stage1_anchor48_operation_context_organizer_v301_locomo_nonadv_full_dc59848/`
- LME predictions: `outputs/formal/stage1_anchor48_operation_context_organizer_v301_lme_s_full_dc59848/predictions.jsonl`
- LME traces: `outputs/formal/stage1_anchor48_operation_context_organizer_v301_lme_s_full_dc59848/traces.jsonl`
- LoCoMo predictions: `outputs/formal/stage1_anchor48_operation_context_organizer_v301_locomo_nonadv_full_dc59848/predictions.jsonl`
- LoCoMo traces: `outputs/formal/stage1_anchor48_operation_context_organizer_v301_locomo_nonadv_full_dc59848/traces.jsonl`

## Verification

- v300 code verification still applies: `python -m py_compile src/memory/compiler.py src/memory/pipeline.py src/tests/test_compiler.py`
- `python -m pyflakes src`
- `python -m unittest discover -s src/tests`
- Full LME and LoCoMo predictions with `6` workers
- Full answer diff vs v298: LME `0/500`, LoCoMo `0/1540`
