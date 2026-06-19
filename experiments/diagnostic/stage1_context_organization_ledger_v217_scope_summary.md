# stage1_context_organization_ledger_v217 LTS summary

## Decision

V217 replaces v216 as the current local LTS. It adds a trace-only Context Organization Ledger inside the Context Manifest and keeps retrieval, compiled prompt, answer generation, repair, cache behavior, and judge records unchanged.

The ledger records prompt context pressure, context budget headroom/drop state, and selected-context source flow. For each run it links selected-context materialized/risky rows to final evidence rows, typed-memory source activation, and memory-projected retrieval.

## Clean Boundary

- Uses only question text, raw memory/context, source-backed typed memory, and normal retrieval traces.
- Does not use gold answer, judge output, benchmark label, sample id, test feedback, or sample-specific rules.
- The new ledger is diagnostic only; it is not consumed by retrieval, compiler, answer, repair, finalizer, cache keying, or judge.
- Typed memory remains source-backed activation. The ledger records whether it is grounded, not whether it should override raw evidence.

## Full Verification

| Benchmark | v217 vs v216 behavior diff | ledger coverage | answer cache | inherited dual judge |
|---|---|---:|---:|---|
| LongMemEval-S full | answer/prompt/evidence rows/retrieval hits/effective selected-context diff `0/500` | `500/500` | `500/0/0` | strict/lenient `0.834000 / 0.846000`, `417/500` strict, `423/500` lenient |
| LoCoMo non-adversarial full | answer/prompt/evidence rows/retrieval hits/effective selected-context diff `0/1540` | `1540/1540` | `1540/0/0` | strict/lenient `0.793506 / 0.818831`, `1222/1540` strict, `1261/1540` lenient |

| Benchmark | avg build tokens | avg query tokens | total build tokens | total query tokens | think tokens |
|---|---:|---:|---:|---:|---:|
| LongMemEval-S full | `85393.566` | `6580.196` | `42696783` | `3290098` | `0` |
| LoCoMo non-adversarial full | `62015.57402597403` | `6095.268181818182` | `95503984` | `9386713` | `0` |

## Ledger Aggregate

| Benchmark | avg prompt context chars | materialized selected-context rows | risk rows | risk from typed/projection | main risk reasons |
|---|---:|---:|---:|---:|---|
| LongMemEval-S full | `19775.056` | `12` | `0` | `0 / 0` | none |
| LoCoMo non-adversarial full | `17402.64` | `8540` | `5841` | `1198 / 1198` | `4034` insufficient slot coverage; `1807` insufficient slot terms |

## Why LTS

V217 has no performance drop because the final prompts and answers are identical to v216. It reduces #2/#3 diagnostic risk by making context organization pressure and selected-context source flow inspectable before any prompt-visible mitigation. This makes the next source/span-preserving context organization step safer and more measurable.

Residual risks remain:

- #2: the ledger does not itself reduce query tokens.
- #3: the selected-context risk rows are diagnosed, not yet prompt-visible mitigated.
- #5: v216 memory activation provenance remains available, but state/update organization still needs a clean source-backed design.

## Artifacts

- Config: `configs/stage1_context_organization_ledger_v217_seeded_qwen36_no_think_build4k_cached.json`
- Method commit: `42aefca`
- LME record: `experiments/diagnostic/stage1_context_organization_ledger_v217_lme_s_full/`
- LoCoMo record: `experiments/diagnostic/stage1_context_organization_ledger_v217_locomo_nonadv_full/`
- Outputs:
  - `outputs/diagnostic/stage1_context_organization_ledger_v217_lme_s_full/`
  - `outputs/diagnostic/stage1_context_organization_ledger_v217_locomo_nonadv_full/`
