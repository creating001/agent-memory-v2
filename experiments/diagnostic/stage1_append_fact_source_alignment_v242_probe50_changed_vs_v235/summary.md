# stage1_append_fact_source_alignment_v242_probe50_changed_vs_v235

## 目的

验证 v242 是否能保留 v241 fact-only source alignment 的 build-side provenance 收益，同时避免新 source 抢占原 source priority。v242 只允许 `fact` memory 做 `user -> assistant` provenance 修复，并把 aligned assistant source append 到原 source ids 后面。

## 配置

- base: `configs/stage1_no_finalizer_v235_seeded_qwen36_no_think_build4k_cached.json`
- candidate: `configs/stage1_append_fact_source_alignment_v242_seeded_qwen36_no_think_build4k_cached.json`
- commit: `9813fb634ba0e10ab52f9a86f35e6600b74d4c44`
- answer cache: `outputs/cache/qwen36_no_think_build4k_answer_v242_append_fact_source_alignment_seeded.sqlite`
- cache seed: v235 prediction-time traces/predictions only; no labels or judge outputs.

## Probe 结果

| Benchmark | Scope | Alignment | Answer diff vs v235 | Answer cache | Query tokens |
|---|---:|---:|---:|---:|---:|
| LongMemEval-S | 50 | changed records `601`, added sources `685` | `4/50` | hit/miss/write `35/15/15` | avg `5675.08` |
| LoCoMo non-adversarial | 50 | changed records `0`, added sources `0` | `0/50` | hit/miss/write `50/0/0` | avg `6543.56` |

## Changed-Answer Judge

Dual `deepseek-v4-flash`, temperature `0`, default thinking, changed answers only.

| Benchmark | v235 strict/lenient | v242 strict/lenient | 结论 |
|---|---:|---:|---|
| LongMemEval-S changed `4` | `2/4` / `2/4` | `3/4` / `3/4` | 正向 `+1` |
| LoCoMo changed `0` | inherited | inherited | answer-identical |

关键变化：
- `4f59d44ad8458660ea315a98` tennis racket source 从错到对。
- `d4bfe0f95ae6b5d7a565a8c1` previous occupation 保持正确，append source order 修复了 v241 的 specificity loss。
- `d0d64a9b8426fda3ea1cd266` sister birthday gift 保持正确。

## 诊断

v242 是当前 source-alignment 分支中最稳的版本：LoCoMo 不漂移，LongMemEval probe 有正向 changed judge，且避免了 v241 的 previous-occupation loss。仍需 full 验证，因为 LME probe 中 source alignment 仍会改变 prompt，full 可能出现新漂移。

## 决策

进入 full 验证；暂不升 LTS。若 full changed-answer judge 继续不负向，并且 token 成本仍在预算内，可考虑作为新的 LTS 候选。

## 输出

- LME predictions: `outputs/diagnostic/stage1_append_fact_source_alignment_v242_lme_probe50/predictions.jsonl`
- LME traces: `outputs/diagnostic/stage1_append_fact_source_alignment_v242_lme_probe50/traces.jsonl`
- LoCoMo predictions: `outputs/diagnostic/stage1_append_fact_source_alignment_v242_locomo_probe50/predictions.jsonl`
- LoCoMo traces: `outputs/diagnostic/stage1_append_fact_source_alignment_v242_locomo_probe50/traces.jsonl`
- changed predictions/labels: `outputs/diagnostic/stage1_append_fact_source_alignment_v242_probe50_changed_vs_v235/`
- changed judge: `experiments/diagnostic/stage1_append_fact_source_alignment_v242_probe50_changed_vs_v235/`
