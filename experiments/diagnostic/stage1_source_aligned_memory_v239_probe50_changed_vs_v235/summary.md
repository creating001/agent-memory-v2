# stage1_source_aligned_memory_v239_probe50_changed_vs_v235

## 目的

验证 v239 build-memory source alignment 是否能作为 v235 LTS 的 build-side provenance 改进。v239 只在 build memory 生成后，用同 session 相邻 raw turns 对 typed memory 的 `source_ids` 做 question-independent 对齐；不新增 answer prompt 规则，不使用 gold、judge、benchmark label、sample id、test feedback 或样本级规则。

## 配置

- base: `configs/stage1_no_finalizer_v235_seeded_qwen36_no_think_build4k_cached.json`
- candidate: `configs/stage1_source_aligned_memory_v239_seeded_qwen36_no_think_build4k_cached.json`
- commit: `239f01698cb2909d63329a87cd52270243534e9e`
- answer cache: `outputs/cache/qwen36_no_think_build4k_answer_v239_source_aligned_memory_seeded.sqlite`
- cache seed: v235 prediction-time traces/predictions only; no labels or judge outputs.

## Probe 结果

| Benchmark | Scope | Alignment | Answer diff vs v235 | Answer cache | Query tokens |
|---|---:|---:|---:|---:|---:|
| LongMemEval-S | 50 | changed records `940`, added sources `1248` | `2/50` | hit/miss/write `33/17/17` | avg `5676.06` |
| LoCoMo non-adversarial | 50 | changed records `550`, added sources `900` | `14/50` | hit/miss/write `17/33/33` | avg `6863.90` |

## Changed-Answer Judge

Dual `deepseek-v4-flash`, temperature `0`, default thinking, changed answers only.

| Benchmark | v235 strict/lenient | v239 strict/lenient | 结论 |
|---|---:|---:|---|
| LongMemEval-S changed `2` | `1/2` / `1/2` | `1/2` / `1/2` | 持平 |
| LoCoMo changed `14` | `13/14` / `13/14` | `12/14` / `13/14` | strict 负向 |

主要新增 LoCoMo 错例是 `28821506df08ca36f78e989a`：relationship status 从 v235 的 `Single` 变成 v239 的信息不足。另有 `d5068b3c68a955ba6cdfe705` lenient 改对，但不足以抵消 strict 风险。

## 诊断

v239 的 source alignment gate 过宽。它确实让 build memory 更 source-auditable，但在多人物对话中会把相邻 speaker 的 turn 大量加入 source chain，导致 retrieval/context 变化过宽，带来 wrong-speaker/source 扩散和拒答漂移。LoCoMo probe50 的 changed rate `14/50` 对一个 build-side provenance repair 来说过高。

## 决策

不升 LTS，不进入 full。v239 保留为负向对照。下一步 v240 将 source alignment 收窄为只允许 `user -> assistant` 问答式 provenance 修复，避免多人物相邻 turn 的 wrong-speaker 扩源。

## 输出

- LME predictions: `outputs/diagnostic/stage1_source_aligned_memory_v239_lme_probe50/predictions.jsonl`
- LME traces: `outputs/diagnostic/stage1_source_aligned_memory_v239_lme_probe50/traces.jsonl`
- LoCoMo predictions: `outputs/diagnostic/stage1_source_aligned_memory_v239_locomo_probe50/predictions.jsonl`
- LoCoMo traces: `outputs/diagnostic/stage1_source_aligned_memory_v239_locomo_probe50/traces.jsonl`
- changed predictions/labels: `outputs/diagnostic/stage1_source_aligned_memory_v239_probe50_changed_vs_v235/`
- changed judge: `experiments/diagnostic/stage1_source_aligned_memory_v239_probe50_changed_vs_v235/`
