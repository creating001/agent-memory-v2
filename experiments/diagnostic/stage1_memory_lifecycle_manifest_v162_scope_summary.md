# stage1_memory_lifecycle_manifest_v162 LTS summary

## Purpose

V162 promotes a trace-only governance layer on top of v158 LTS.

It keeps build memory, retrieval, compiler context, answer prompt, answer repair, and source-grounded finalizer behavior unchanged. The code adds a source-backed memory lifecycle manifest to each prediction trace. The manifest summarizes build-memory and memory-retrieval activation slots, status counts, source visibility, conflict candidates, and question-overlap terms. It is not fed back into retrieval, compiler, answer, repair, or finalization.

This version addresses #5 by making memory lifecycle/state/conflict/query activation auditable before using it for prediction. It does not claim to solve #5 completely.

## Config

- Config: `configs/stage1_memory_lifecycle_manifest_v162_qwen36_no_think_build4k_cached.json`
- Parent LTS: `configs/stage1_narrow_question_gated_selected_context_v158_qwen36_no_think_build4k_cached.json`
- Answer/repair cache namespace: intentionally reused from v158 because prompt and prediction behavior are unchanged.
- Tests: `python -m unittest discover -s src/tests` passed, `241` tests.
- Prediction commit recorded by runs: `7800c5f`
- Dirty state in run manifests: expected; v162 source/config/summary files were uncommitted during prediction.

## Metrics

| Benchmark | Result |
|---|---:|
| LongMemEval-S full | strict/lenient `411/500` / `417/500` = `0.822000 / 0.834000` |
| LoCoMo non-adversarial full | strict/lenient `1216/1540` / `1256/1540` = `0.789610 / 0.815584` |

The accuracy is inherited from v158 because answers are identical:

| Benchmark | answer diff vs v158 | answer cache | build cache |
|---|---:|---:|---:|
| LongMemEval-S full | `0/500` | `500` hits, `0` misses, `0` writes | `3341` hits, `0` misses, `0` writes |
| LoCoMo non-adversarial full | `0/1540` | `1540` hits, `0` misses, `0` writes | `12411` hits, `0` misses, `0` writes |

Token cost is unchanged from v158 logical cold-run accounting:

| Benchmark | avg build tokens | avg query tokens |
|---|---:|---:|
| LongMemEval-S full | `85393.566` | `6200.690` |
| LoCoMo non-adversarial full | `62015.574` | `6047.909` |

## Lifecycle Manifest Audit

| Benchmark | build slots | build conflict slots | activated slots | activated conflict slots |
|---|---:|---:|---:|---:|
| LongMemEval-S full | `28757` | `3574` across `500/500` samples | `2062` | `204` across `146/500` samples |
| LoCoMo non-adversarial full | `115667` | `8824` across `1540/1540` samples | `15772` | `429` across `314/1540` samples |

The manifest also records visible source-linked slots:

| Benchmark | build visible slots | activated visible slots |
|---|---:|---:|
| LongMemEval-S full | `4309` | `1418` |
| LoCoMo non-adversarial full | `17579` | `8147` |

Interpretation: v162 exposes enough lifecycle/conflict/query activation signal to drive targeted #5 badcase analysis, while avoiding the risk of letting unverified typed memory directly change answers.

## Decision

Promote v162 to current local LTS.

Reasoning:

- Risk reduction: #5 memory lifecycle/state/conflict/query activation is now auditable at build and query time.
- Clean/general: manifest uses only question text, route, source-linked build memory, retrieved raw evidence rows, and visible prediction-time metadata.
- Performance: LME and LoCoMo answers are identical to v158; dual judge accuracy is inherited without extra judge cost.
- Cost: no extra answer/build model calls; trace computation only.

Remaining risks:

- #1 granularity/profile still partly relies on average-turn profile and broad profile/state heuristics.
- #2 top-k/context noise still needs coverage-preserving organization rather than simple pruning.
- #5 still needs a prediction-side, answer-slot-aware lifecycle/verifier mechanism that safely uses manifest signals without overreach.

## Outputs

- LME predictions: `outputs/diagnostic/stage1_memory_lifecycle_manifest_v162_lme_s_full/predictions.jsonl`
- LME traces: `outputs/diagnostic/stage1_memory_lifecycle_manifest_v162_lme_s_full/traces.jsonl`
- LME metrics: `experiments/diagnostic/stage1_memory_lifecycle_manifest_v162_lme_s_full/metrics.json`
- LoCoMo predictions: `outputs/diagnostic/stage1_memory_lifecycle_manifest_v162_locomo_nonadv_full/predictions.jsonl`
- LoCoMo traces: `outputs/diagnostic/stage1_memory_lifecycle_manifest_v162_locomo_nonadv_full/traces.jsonl`
- LoCoMo metrics: `experiments/diagnostic/stage1_memory_lifecycle_manifest_v162_locomo_nonadv_full/metrics.json`
- Smoke run: `outputs/diagnostic/stage1_memory_lifecycle_manifest_v162_lme_smoke5/`

## Clean Note

Prediction code uses only raw dialogue, source-linked build memory, question text, route, retrieved evidence rows, and prediction-time traces. No gold answers, judge outputs, benchmark labels, sample ids, row indices, test feedback, or sample-level shortcuts are used by prediction, retrieval, compiler, repair, finalizer, cache construction, or manifest construction.

Promotion commit: this file is committed together with `eval: promote v162 lifecycle manifest lts`; use `git log --oneline -- experiments/diagnostic/stage1_memory_lifecycle_manifest_v162_scope_summary.md` for the exact local commit.
