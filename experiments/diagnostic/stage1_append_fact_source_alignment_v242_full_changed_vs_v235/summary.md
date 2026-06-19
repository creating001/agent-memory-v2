# stage1_append_fact_source_alignment_v242_full_changed_vs_v235

## Purpose

验证 v242 append fact source alignment full run 是否可替代 v235 LTS。v242 只对 `fact` memory 做 build-time `user -> assistant` source alignment，并把 aligned assistant source append 到原 source ids 之后，目标是降低 memory provenance 风险且不扰乱原 evidence priority。

## Config

- base LTS: `configs/stage1_no_finalizer_v235_seeded_qwen36_no_think_build4k_cached.json`
- candidate: `configs/stage1_append_fact_source_alignment_v242_seeded_qwen36_no_think_build4k_cached.json`
- method commit: `22a9e639ff7d533307af6ac488528fb480aff891`
- answer/build model: `Qwen/Qwen3.6-35B-A3B`, no-thinking, temperature `0`
- judge: DeepSeek dual `deepseek-v4-flash`, temperature `0`, default thinking
- clean note: changed-only paired judge uses predictions and labels only for offline evaluation; labels/judge outputs are not used by build, retrieval, compiler, answer, cache seeding, or source alignment.

## Full Run Metrics

| Benchmark | v242 prediction diff vs v235 | avg build tokens | avg query tokens | source alignment | answer cache |
|---|---:|---:|---:|---:|---:|
| LongMemEval-S full | `38/500` | `85393.566` | `6428.594` | changed `5658`, added `6364` | `387/113/113` hit/miss/write |
| LoCoMo non-adversarial full | `0/1540` | `62015.57402597403` | `6094.017532467533` | changed `0`, added `0` | `1540/0/0` hit/miss/write |

## Changed Judge

| Scope | v235 strict/lenient | v242 strict/lenient | Delta |
|---|---:|---:|---:|
| LME changed `38` | `24/38` / `24/38` | `14/38` / `19/38` | strict `-10`, lenient `-5` |

Transition summary:

- strict losses: `11`
- strict gains: `1`
- lenient losses: `6`
- lenient gains: `1`
- unchanged correct: `13`
- unchanged wrong: `13`

Paired-delta full accuracy:

| Benchmark | v235 LTS | v242 derived full | Decision |
|---|---:|---:|---|
| LongMemEval-S full | strict/lenient `0.832000 / 0.844000` | strict/lenient `0.812000 / 0.834000` | regress |
| LoCoMo non-adversarial full | strict/lenient `0.794156 / 0.819481` | inherited `0.794156 / 0.819481` | tie |

Judge token usage:

- v235 changed judge total: `22893`
- v242 changed judge total: `22597`

## Diagnosis

v242 does not qualify as LTS. It reduces one build-side provenance risk in form, but the full changed judge shows that mechanical source appending is too broad for LongMemEval and hurts answer quality.

Observed badcase patterns:

- Insufficient-info answers often lost the specific missing-field rationale, e.g. from "iPad cost/date is not mentioned" to generic "not enough"; dual judge penalized these as unsupported or incomplete.
- Count and temporal-order questions lost event separation, e.g. museum/gallery count, dinner-party count, and trip order.
- Some preference/advice answers introduced extra cultural entities after source alignment changed the evidence mix, increasing prompt competition without improving grounding.

The main lesson is that build-time provenance should not blindly expand memory record sources. A better next step is a typed memory/source graph or activation audit that keeps original extraction evidence as the answer-facing anchor, then uses extra source candidates only after an answerability/evidence-utility gate.

## Decision

Do not promote v242. Current LTS remains v235.

## Outputs

- LME predictions: `outputs/diagnostic/stage1_append_fact_source_alignment_v242_lme_s_full/predictions.jsonl`
- LME traces: `outputs/diagnostic/stage1_append_fact_source_alignment_v242_lme_s_full/traces.jsonl`
- LoCoMo predictions: `outputs/diagnostic/stage1_append_fact_source_alignment_v242_locomo_nonadv_full/predictions.jsonl`
- LoCoMo traces: `outputs/diagnostic/stage1_append_fact_source_alignment_v242_locomo_nonadv_full/traces.jsonl`
- changed predictions/labels: `outputs/diagnostic/stage1_append_fact_source_alignment_v242_full_changed_vs_v235/`
- changed judge: `experiments/diagnostic/stage1_append_fact_source_alignment_v242_full_changed_vs_v235/`
