# stage1_evidence_pressure_ledger_v222 LTS summary

## Decision

V222 replaces v221 as the current local LTS.

V222 is a trace-only #2 evidence pressure ledger. It inherits v221 behavior exactly, and adds Context Manifest statistics for final evidence row count, source/session concentration, adjacent-turn pressure, and tail evidence after ranks `32` and `40`.

## Clean Boundary

- Prediction uses only question text, raw Memory Context, visible metadata, and build-stage memory generated before the question.
- No gold answer, judge output, benchmark label, sample id, row index, test feedback, or sample-level rule is used.
- The ledger is diagnostic only: it does not change retrieval, prompt, evidence rows, selected-context materialization, answer, repair, cache namespace, or judge path.

## Full Verification

| Benchmark | answer diff | prompt diff | evidence rows diff | retrieval hits diff | selected-context diff | pressure ledger | avg build/query tokens | inherited judge accuracy |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| LongMemEval-S full | `0/500` | `0/500` | `0/500` | `0/500` | `0/500` | `500/500` | `85393.566 / 6580.196` | strict/lenient `0.834000 / 0.846000` |
| LoCoMo non-adversarial full | `0/1540` | `0/1540` | `0/1540` | `0/1540` | `0/1540` | `1540/1540` | `62015.57402597403 / 6095.268181818182` | strict/lenient `0.793506 / 0.818831` |

Both full runs use answer cache only: LME `500/0/0`, LoCoMo `1540/0/0`. Because v222 is answer-identical to v221, it inherits v221/v217 dual DeepSeek flash judge records. No changed-answer judge is needed.

## Evidence Pressure

| Benchmark | avg rows | p95 rows | avg sessions | avg adjacent pairs | tail rows/chars after rank 32 | tail rows/chars after rank 40 |
|---|---:|---:|---:|---:|---:|---:|
| LongMemEval-S full | `34.746` | `40.0` | `14.25` | `6.556` | `2016 / 1567119` | `0 / 0` |
| LoCoMo non-adversarial full | `54.142857142857146` | `60.0` | `20.723376623376623` | `9.446753246753246` | `34100 / 4316226` | `21780 / 2789101` |

Interpretation: #2 pressure is now measurable at the final evidence layer, not only in raw retrieval hits. LoCoMo has substantial tail-rank evidence after rank `40`, so future token/rerank work should target source/span-preserving pre-compiler organization instead of hard deleting selected-context wrappers.

## Artifacts

- Config: `configs/stage1_evidence_pressure_ledger_v222_seeded_qwen36_no_think_build4k_cached.json`
- Method commit: `7c79b8949049db6af37f367ef5ba2f44e59f220f`
- LME full: `experiments/diagnostic/stage1_evidence_pressure_ledger_v222_lme_s_full/`
- LoCoMo full: `experiments/diagnostic/stage1_evidence_pressure_ledger_v222_locomo_nonadv_full/`
- Outputs: `outputs/diagnostic/stage1_evidence_pressure_ledger_v222_*`
- Git status during runs: LME clean; LoCoMo dirty only because the LME experiment directory was already untracked.

## Next

- Use the pressure ledger to design a narrow retrieval/pre-compiler candidate that preserves source anchors and temporal neighbor chains while reducing final evidence tail pressure.
- Keep selected-context raw-evidence materialization unless a future guard proves prompt and answer drift are narrow and judge-positive.
- Continue #5 toward state/update/conflict organization beyond evidence-first activation, without treating typed memory as independent answer evidence.
