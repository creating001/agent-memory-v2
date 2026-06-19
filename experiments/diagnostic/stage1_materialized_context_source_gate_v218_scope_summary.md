# stage1_materialized_context_source_gate_v218 rejection summary

## Decision

V218 is rejected and does not replace v217 LTS.

V218 adds a conservative materialized-context source gate for selected-context: same-session local context is first built as in v217, then only inserted into the prompt when the actual prompt-visible materialized text has enough overlap with the question. The rule is clean and general, but it is too broad for LoCoMo.

## Clean Boundary

- Prediction uses only question text, raw dialogue, source-backed typed memory, and retrieval traces.
- No gold answer, judge output, benchmark label, sample id, test feedback, or sample-level rule is used.
- Judge is run only offline after prediction.
- New answer/repair cache namespaces are used because prompts can change.

## Full Prediction Diff

| Benchmark | prompt/evidence diff | answer diff | retrieval hits diff | selected-context diff | answer cache |
|---|---:|---:|---:|---:|---:|
| LongMemEval-S full | `3/500` | `1/500` | `0/500` | `3/500` | `497/3/3` |
| LoCoMo non-adversarial full | `1480/1540` | `683/1540` | `0/1540` | `1480/1540` | `70/1470/1470` |

## Risk And Cost

| Benchmark | avg build tokens | avg query tokens | selected-context applied | selected-context risk rows |
|---|---:|---:|---:|---:|
| LongMemEval-S full | `85393.566` | `6636.242` | `1/500` | `0` |
| LoCoMo non-adversarial full | `62015.57402597403` | `5739.078571428571` | `1286/1540` | `0` |

Compared with v217, LoCoMo avg query tokens drop from `6095.268181818182` to `5739.078571428571`, and selected-context risk rows drop from `5841` to `0`. The risk reduction is real, but it changes too much prompt-visible context.

## Changed-Answer Judge

| Benchmark | changed answers | v217 strict/lenient | v218 strict/lenient | delta |
|---|---:|---:|---:|---:|
| LongMemEval-S full | `1` | `1/1`, `1/1` | `1/1`, `1/1` | `0 / 0` |
| LoCoMo non-adversarial full | `683` | `505/683`, `527/683` | `500/683`, `515/683` | `-5 / -12` |

Derived LoCoMo full accuracy would become strict/lenient `0.790260 / 0.811039`, down from v217 `0.793506 / 0.818831`. This fails the LTS requirement even though #3 risk and query tokens improve.

## Diagnosis

The materialized-context gate removes many risky local-context wrappers, but LoCoMo uses those wrappers as useful local disambiguation even when term coverage is weak. The next version should not use a broad prompt-visible hard gate over almost all selected-context rows. A better direction is source-flow scoring or rerank that preserves high-value context and only suppresses rows with stronger negative evidence, such as wrong speaker, unsupported time binding, or no final-evidence/source-backed overlap.

## Artifacts

- Method commit: `e39262d`
- Config: `configs/stage1_materialized_context_source_gate_v218_seeded_qwen36_no_think_build4k_cached.json`
- LME run: `experiments/diagnostic/stage1_materialized_context_source_gate_v218_lme_s_full/`
- LoCoMo run: `experiments/diagnostic/stage1_materialized_context_source_gate_v218_locomo_nonadv_full/`
- Changed judge outputs: `outputs/diagnostic/stage1_materialized_context_source_gate_v218_changed_vs_v217/`
