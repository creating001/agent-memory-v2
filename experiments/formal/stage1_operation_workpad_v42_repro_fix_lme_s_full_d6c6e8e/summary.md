# v42 复现修复控制实验

## 目的

验证 `d6c6e8e` 对 answer cache 与 `external_naive` prompt 漂移的修复是否恢复原 v42 行为。本实验不是新方法，只作为后续方法探索前的复现基线。

## 结论

- prediction 与原 v42 `stage1_operation_workpad_v42_lme_s_full_f7eb076` 完全一致：500/500 相同。
- DeepSeek judge 重跑 accuracy：0.772，386/500，invalid=0。
- 原 v42 judge accuracy：0.774，387/500。由于 prediction 完全相同，1 条净差异来自 judge 重跑波动。
- evidence_recall：1.0，500/500。

## 配置与 clean 记录

- benchmark/subset：LongMemEval-S full。
- config：`configs/stage1_operation_workpad_v42_cached.json`。
- git commit：`d6c6e8e331cab47581e246779818c166e04ed17f`。
- dirty：false。
- clean 口径：prediction pipeline 未使用 gold answer、judge 输出、benchmark 标签、sample id、test feedback 或样本级规则。

## Token 成本

- avg build tokens：80346.246。
- total build tokens：40173123。
- avg query tokens：5864.706。
- total query tokens：2932353。
- answer max input/output：131072 / 16384。
- build token 是逻辑 cold-build 成本；即使 build cache 全命中，也按 cached usage 计入新环境构建 memory 的成本。

## 输出路径

- predictions：`outputs/formal/stage1_operation_workpad_v42_repro_fix_lme_s_full_d6c6e8e/predictions.jsonl`
- traces：`outputs/formal/stage1_operation_workpad_v42_repro_fix_lme_s_full_d6c6e8e/traces.jsonl`
- metrics：`experiments/formal/stage1_operation_workpad_v42_repro_fix_lme_s_full_d6c6e8e/metrics.json`
- judge：`experiments/formal/stage1_operation_workpad_v42_repro_fix_lme_s_full_d6c6e8e/deepseek_judge.json`
- evidence recall：`experiments/formal/stage1_operation_workpad_v42_repro_fix_lme_s_full_d6c6e8e/evidence_recall.json`
- v42 复现对比：`experiments/formal/stage1_operation_workpad_v42_repro_fix_lme_s_full_d6c6e8e/reproduction_vs_v42.json`

## 下一步

后续新方法必须先基于这个修复后的可复现基线做设计。结合当前 avg query tokens 已接近 6K，下一阶段不应简单增加 top-k 或上下文长度，而应重点减少上下文噪声、改进候选组织和 build/query 协同。
