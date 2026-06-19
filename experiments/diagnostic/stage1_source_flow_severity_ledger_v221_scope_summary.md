# stage1_source_flow_severity_ledger_v221 LTS summary

## Decision

V221 replaces v217 as the current local LTS.

V221 is a trace-only #2/#3 source-flow safety improvement. It keeps v217 prediction behavior unchanged, but adds selected-context source-flow severity to the Context Manifest. Rows that look risky under local question-term matching are split into final raw evidence-backed rows, typed-memory-backed rows, memory-projected-backed rows, and non-final rows that might be eligible for a future guarded rerank/order experiment.

## Clean Boundary

- Prediction uses only question text, raw Memory Context, visible metadata, and build-stage memory generated before the question.
- No gold answer, judge output, benchmark label, sample id, row index, test feedback, or sample-level rule is used by retrieval, compiler, answer, repair, finalizer, cache construction, or severity logging.
- The severity ledger is trace-only and is not fed back into retrieval, compiler, answer, repair, finalizer, or cache keys.
- The design follows xMemory's decoupling-before-aggregation, Hindsight's multi-view retrieval plus rerank, and Graphiti/Mnemis provenance-first source-flow ideas, while keeping derived memory as source-backed activation/navigation rather than independent answer evidence.

## Full Verification

| Benchmark | answer diff vs v217 | prompt diff | evidence rows diff | retrieval hits diff | selected-context diff | severity ledger | inherited judge accuracy |
|---|---:|---:|---:|---:|---:|---:|---:|
| LongMemEval-S full | `0/500` | `0/500` | `0/500` | `0/500` | `0/500` | `500/500` | strict/lenient `0.834000 / 0.846000` |
| LoCoMo non-adversarial full | `0/1540` | `0/1540` | `0/1540` | `0/1540` | `0/1540` | `1540/1540` | strict/lenient `0.793506 / 0.818831` |

Token accounting is unchanged from v217:

| Benchmark | avg build tokens | avg query tokens | think tokens |
|---|---:|---:|---:|
| LongMemEval-S full | `85393.566` | `6580.196` | `0` |
| LoCoMo non-adversarial full | `62015.57402597403` | `6095.268181818182` | `0` |

LoCoMo source-flow severity:

| Item | Count |
|---|---:|
| selected-context risk rows | `5841` |
| final raw evidence-backed risk rows | `5841` |
| typed-memory-backed risk rows | `1198` |
| memory-projected-backed risk rows | `1198` |
| non-final evidence risk rows | `0` |
| guarded-rerank eligible risk rows | `0` |
| blocked by final evidence rows | `5841` |

## Interpretation

V218, v219, and v220 showed that directly deleting or rewriting prompt-visible selected context reduces local risk/token metrics but hurts LoCoMo judge accuracy. V221 explains why: the apparent selected-context risk rows on LoCoMo are not disposable noise; every risky row is also final raw evidence used by the reader. Future #2 rerank/context-noise work should therefore target retrieval or pre-compiler source selection, not selected-context wrapper removal, and should require a narrow behavior diff before judge.

Because v221 is answer-identical to v217 on both full benchmarks, it inherits v217's dual DeepSeek flash judge records. No changed-answer judge is needed.

## Artifacts

- Config: `configs/stage1_source_flow_severity_ledger_v221_seeded_qwen36_no_think_build4k_cached.json`
- Method commit: `6f744e12e6f769c901393ebd3ff3a97ffd00045e`
- LME full: `experiments/diagnostic/stage1_source_flow_severity_ledger_v221_lme_s_full/`
- LoCoMo full: `experiments/diagnostic/stage1_source_flow_severity_ledger_v221_locomo_nonadv_full/`
- Outputs: `outputs/diagnostic/stage1_source_flow_severity_ledger_v221_*`

## Next

- #2: Try retrieval/pre-compiler source diversity or rerank that preserves final evidence anchors; do not compress or hard-gate selected-context wrapper text.
- #5: Move from audit to source-backed state/update organization, without treating ordinary event/preference multivalue rows as state conflicts.
- Keep src cleanup scoped to code paths that are confirmed unused by retained LTS and ablation configs.
