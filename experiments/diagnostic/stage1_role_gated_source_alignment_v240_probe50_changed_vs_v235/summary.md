# stage1_role_gated_source_alignment_v240_probe50_changed_vs_v235

## 目的

验证 v240 的 conservative source alignment：只允许原始 source 为 `user` turn、候选 source 为同 session 后续 `assistant` turn 的 build-memory provenance 修复。该版本用于收窄 v239 在 LoCoMo 多人物对话中的 wrong-speaker/source 扩散风险。

## 配置

- base: `configs/stage1_no_finalizer_v235_seeded_qwen36_no_think_build4k_cached.json`
- candidate: `configs/stage1_role_gated_source_alignment_v240_seeded_qwen36_no_think_build4k_cached.json`
- commit: `a8800695b61f671d253aa5d147d3f8e63944b876`
- answer cache: `outputs/cache/qwen36_no_think_build4k_answer_v240_role_gated_source_alignment_seeded.sqlite`
- cache seed: v235 prediction-time traces/predictions only; no labels or judge outputs.

## Probe 结果

| Benchmark | Scope | Alignment | Answer diff vs v235 | Answer cache | Query tokens |
|---|---:|---:|---:|---:|---:|
| LongMemEval-S | 50 | changed records `4800`, added sources `6168` | `5/50` | hit/miss/write `14/36/36` | avg `5685.58` |
| LoCoMo non-adversarial | 50 | changed records `0`, added sources `0` | `0/50` | hit/miss/write `50/0/0` | avg `6543.56` |

## Changed-Answer Judge

Dual `deepseek-v4-flash`, temperature `0`, default thinking, changed answers only.

| Benchmark | v235 strict/lenient | v240 strict/lenient | 结论 |
|---|---:|---:|---|
| LongMemEval-S changed `5` | `3/5` / `3/5` | `3/5` / `3/5` | 持平；`+1/-1` |
| LoCoMo changed `0` | inherited | inherited | answer-identical |

关键 LME 变化：
- gain: `4f59d44ad8458660ea315a98` tennis racket source wording 更简洁，judge 从错到对。
- loss: `d4bfe0f95ae6b5d7a565a8c1` previous occupation 从 `marketing specialist at a small startup` 退化为 `Marketing specialist`。

## 诊断

v240 成功阻断 LoCoMo 多人物相邻 turn 扩源，解决 v239 的主要风险。但 LongMemEval 中大量 `answer_*` user/assistant 会话仍被 source alignment 广泛触发，平均每样本 `96` 条 record 改 source。这个范围对 provenance repair 仍过宽，尤其 profile/state/preference 这类 lifecycle memory 被扩源后会影响 previous/current value 的 specificity。

## 决策

不升 LTS，不进入 full。下一步 v241 将 source alignment 进一步限制到 `fact` memory，只修复 assistant-provided factual answer 的 provenance，不改 profile/state/preference lifecycle source。

## 输出

- LME predictions: `outputs/diagnostic/stage1_role_gated_source_alignment_v240_lme_probe50/predictions.jsonl`
- LME traces: `outputs/diagnostic/stage1_role_gated_source_alignment_v240_lme_probe50/traces.jsonl`
- LoCoMo predictions: `outputs/diagnostic/stage1_role_gated_source_alignment_v240_locomo_probe50/predictions.jsonl`
- LoCoMo traces: `outputs/diagnostic/stage1_role_gated_source_alignment_v240_locomo_probe50/traces.jsonl`
- changed predictions/labels: `outputs/diagnostic/stage1_role_gated_source_alignment_v240_probe50_changed_vs_v235/`
- changed judge: `experiments/diagnostic/stage1_role_gated_source_alignment_v240_probe50_changed_vs_v235/`
