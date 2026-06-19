# stage1_temporal_materialized_context_source_gate_v219 rejection summary

## Decision

V219 is rejected and does not replace v217 LTS.

V219 narrows the v218 materialized-context source gate to `temporal_lookup` selected-context rows only. This is clean and much less disruptive than v218, but changed-answer judge is still negative.

## Clean Boundary

- Prediction uses only question text, raw dialogue, source-backed typed memory, and retrieval traces.
- No gold answer, judge output, benchmark label, sample id, test feedback, or sample-level rule is used.
- Judge is run only offline after prediction.
- Fact/list/profile selected-context behavior is unchanged from v217.

## Full Prediction Diff

| Benchmark | prompt/evidence diff | answer diff | retrieval hits diff | selected-context diff | answer cache |
|---|---:|---:|---:|---:|---:|
| LongMemEval-S full | `0/500` | `0/500` | `0/500` | `0/500` | `500/0/0` |
| LoCoMo non-adversarial full | `322/1540` | `105/1540` | `0/1540` | `322/1540` | `1219/321/321` |

## Risk And Cost

| Benchmark | avg build tokens | avg query tokens | selected-context applied | selected-context risk rows |
|---|---:|---:|---:|---:|
| LongMemEval-S full | `85393.566` | `6637.824` | `3/500` | `0` |
| LoCoMo non-adversarial full | `62015.57402597403` | `6065.516883116883` | `1475/1540` | `4932` |

Compared with v217, LoCoMo selected-context risk rows drop from `5841` to `4932`, and avg query tokens drop from `6095.268181818182` to `6065.516883116883`. The risk reduction is narrower and safer than v218, but it still changes temporal answers enough to hurt judge accuracy.

## Changed-Answer Judge

| Benchmark | changed answers | v217 strict/lenient | v219 strict/lenient | delta |
|---|---:|---:|---:|---:|
| LongMemEval-S full | `0` | inherited | inherited | `0 / 0` |
| LoCoMo non-adversarial full | `105` | `69/105`, `69/105` | `65/105`, `68/105` | `-4 / -1` |

Derived LoCoMo full accuracy would become strict/lenient `0.790909 / 0.818182`, down from v217 `0.793506 / 0.818831`. This fails the LTS requirement.

## Diagnosis

Temporal-only hard gating avoids v218's broad damage, but still removes local context that the reader uses for valid temporal disambiguation. The next direction should avoid prompt-visible hard removal. Prefer source-flow scoring/rerank or a trace-informed compiler feature that keeps context available while marking risk, with stricter action only for wrong-speaker or unsupported-time evidence.

## Artifacts

- Method commit: `faedc42`
- Config: `configs/stage1_temporal_materialized_context_source_gate_v219_seeded_qwen36_no_think_build4k_cached.json`
- LME run: `experiments/diagnostic/stage1_temporal_materialized_context_source_gate_v219_lme_s_full/`
- LoCoMo run: `experiments/diagnostic/stage1_temporal_materialized_context_source_gate_v219_locomo_nonadv_full/`
- Changed judge outputs: `outputs/diagnostic/stage1_temporal_materialized_context_source_gate_v219_changed_vs_v217/`
