# stage1_context_manifest_v216 LTS summary

## Decision

V216 replaces v214 as the current local LTS.

V216 adds a trace-only Context Manifest / Memory Activation Ledger. It records source flow from lexical/dense/typed-memory hits through context budget, selected-context materialization, final evidence rows, and source-backed typed-memory activation. This reduces #5 risk by making build-stage memory use auditable as source-backed activation rather than a hidden retrieval side effect.

## Clean Boundary

- Prediction uses only question text, raw Memory Context, visible metadata, and build-stage memory generated before the question.
- No gold answer, judge output, benchmark label, sample id, row index, test feedback, or sample-level rule is used.
- The new manifest is trace-only. It is not read by retrieval, compiler, answer, repair, finalizer, judge, or cache-key construction.
- Derived memory remains navigation/activation; final evidence remains raw source rows.

## Full Verification

| Benchmark | answer diff | prompt diff | evidence rows diff | retrieval hits diff | effective selected-context diff | context manifest | answer cache | inherited judge accuracy |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| LongMemEval-S full | `0/500` | `0/500` | `0/500` | `0/500` | `0/500` | `500/500` | `500/0/0` | strict/lenient `0.834000 / 0.846000` |
| LoCoMo non-adversarial full | `0/1540` | `0/1540` | `0/1540` | `0/1540` | `0/1540` | `1540/1540` | `1540/0/0` | strict/lenient `0.793506 / 0.818831` |

Token accounting is unchanged from v214:

| Benchmark | avg build tokens | avg query tokens |
|---|---:|---:|
| LongMemEval-S full | `85393.566` | `6580.196` |
| LoCoMo non-adversarial full | `62015.57402597403` | `6095.268181818182` |

Context Manifest aggregate:

| Benchmark | avg typed-memory source ids | avg final rows backed by typed-memory sources | samples with typed-memory-backed final rows |
|---|---:|---:|---:|
| LongMemEval-S full | `9.776` | `6.394` | `486/500` |
| LoCoMo non-adversarial full | `26.02857142857143` | `11.597402597402597` | `1539/1540` |

## Why This Is LTS

V216 is behavior-identical to v214 while reducing a real #5 observability risk: before v216, memory activation, projected source hits, selected-context materialization, context-budget drops, and final evidence rows were traceable only by reading several scattered trace fields. V216 records them in one normalized manifest, making later memory organization, rerank, and context compiler changes easier to audit without introducing prompt or answer drift.

Residual risks remain:

- #2: v216 does not reduce final query tokens. v210 and v215 show that mechanical prompt-text compression is unsafe.
- #3: selected-context prompt-visible mitigation is still unresolved; v216 only makes source flow easier to inspect.
- #5: v216 improves provenance/activation audit, but does not yet add a stronger state/update memory organization algorithm.

## Artifacts

- Config: `configs/stage1_context_manifest_v216_seeded_qwen36_no_think_build4k_cached.json`
- Method commit: `3764f54`
- LME record commit: `0748975`
- LoCoMo record commit: `33144a8`
- LME full: `experiments/diagnostic/stage1_context_manifest_v216_lme_s_full_r1/`
- LoCoMo full: `experiments/diagnostic/stage1_context_manifest_v216_locomo_nonadv_full/`
- Outputs: `outputs/diagnostic/stage1_context_manifest_v216_*`

## Next

- Use v216 manifests to design source/span-preserving #2 context organization or guarded rerank.
- For #5, move from audit to a source-backed typed memory organization that supports state/update and conflict reasoning without treating derived memory as standalone evidence.
