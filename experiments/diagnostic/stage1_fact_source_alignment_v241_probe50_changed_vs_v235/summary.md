# stage1_fact_source_alignment_v241_probe50_changed_vs_v235

## 目的

验证 v241 是否能在 v240 的 role gate 上进一步降低 source alignment 风险：只允许 `fact` memory 做 `user -> assistant` provenance 修复，避免 profile/state/preference lifecycle memory 被扩源。

## 配置

- base: `configs/stage1_no_finalizer_v235_seeded_qwen36_no_think_build4k_cached.json`
- candidate: `configs/stage1_fact_source_alignment_v241_seeded_qwen36_no_think_build4k_cached.json`
- commit: `2ed94275a886d5fdf76c625b67a2d8d11c04bfec`
- answer cache: `outputs/cache/qwen36_no_think_build4k_answer_v241_fact_source_alignment_seeded.sqlite`
- cache seed: v235 prediction-time traces/predictions only; no labels or judge outputs.

## Probe 结果

| Benchmark | Scope | Alignment | Answer diff vs v235 | Answer cache | Query tokens |
|---|---:|---:|---:|---:|---:|
| LongMemEval-S | 50 | changed records `604`, added sources `751` | `2/50` | hit/miss/write `36/14/14` | avg `5674.84` |
| LoCoMo non-adversarial | 50 | changed records `0`, added sources `0` | `0/50` | hit/miss/write `50/0/0` | avg `6543.56` |

## Changed-Answer Judge

Dual `deepseek-v4-flash`, temperature `0`, default thinking, changed answers only.

| Benchmark | v235 strict/lenient | v241 strict/lenient | 结论 |
|---|---:|---:|---|
| LongMemEval-S changed `2` | `1/2` / `1/2` | `0/2` / `0/2` | 负向 |
| LoCoMo changed `0` | inherited | inherited | answer-identical |

主要负向是 `d4bfe0f95ae6b5d7a565a8c1`：previous occupation 从 v235 的 `marketing specialist at a small startup` 退化为 v241 的 `Marketing specialist`。

## 诊断

v241 显著降低了 alignment 范围，但仍把新补的 assistant source 放在原 source 前面，改变了 memory-source projection 的优先级。对 source provenance 来说，补充 source 有价值；但对 retrieval/context 来说，抢占原 source 的优先级会引发 specificity loss。

## 决策

不升 LTS，不进入 full。下一步 v242 改为 append alignment：保留 extractor 原始 source priority，只把 assistant source 作为追加 provenance/source candidate。

## 输出

- LME predictions: `outputs/diagnostic/stage1_fact_source_alignment_v241_lme_probe50/predictions.jsonl`
- LME traces: `outputs/diagnostic/stage1_fact_source_alignment_v241_lme_probe50/traces.jsonl`
- LoCoMo predictions: `outputs/diagnostic/stage1_fact_source_alignment_v241_locomo_probe50/predictions.jsonl`
- LoCoMo traces: `outputs/diagnostic/stage1_fact_source_alignment_v241_locomo_probe50/traces.jsonl`
- changed predictions/labels: `outputs/diagnostic/stage1_fact_source_alignment_v241_probe50_changed_vs_v235/`
- changed judge: `experiments/diagnostic/stage1_fact_source_alignment_v241_probe50_changed_vs_v235/`
