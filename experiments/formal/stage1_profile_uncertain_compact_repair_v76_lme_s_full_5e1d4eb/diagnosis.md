# Diagnosis for v76 uncertain profile repair

## Summary

v76 收窄了 v75 的二阶段 profile repair：从 all-profile review 变成 uncertain-only repair。这个改动成功降低了额外 query token 和误伤面，但没有带来可靠 full-set 提升。

## Key Metrics

- samples_processed：500。
- fresh DeepSeek accuracy：0.768，384/500。
- v73 fresh accuracy：0.778，389/500。
- evidence_recall：1.0。
- avg_build_tokens：80346.246。
- avg_query_tokens：5880.232。
- repair_triggered/applied：6/4。
- repair_total_query_tokens：14235。
- answer_max_input/output：131072 / 16384。

## Comparison

Fresh judge vs v73：
- CORRECT->CORRECT：375。
- WRONG->WRONG：102。
- WRONG->CORRECT：9。
- CORRECT->WRONG：14。

Prediction-changed controlled comparison vs v73：
- prediction_changed：16。
- WRONG->CORRECT：6。
- CORRECT->WRONG：4。
- WRONG->WRONG：5。
- CORRECT->CORRECT：1。
- controlled accuracy：391/500 = 0.782。

这里的差异说明：v76 的真实改写局部有正信号，但 full judge 重评后仍不稳，不能只看 controlled subset 推主线。

## Error Pattern

- 变化全部集中在 `single-session-preference`，没有改善 multi-session 或 temporal 的主要错误。
- v76 避免了 v75 中 `favorite author discount` 这类非 profile fact 被 repair 改坏的问题，因为 uncertain-only 没有触发该样本。
- 仍然存在 preference answer 过泛或过窄的问题：有些拒答被修正，但也有原本通过 judge 的个性化答案被改短后失分。
- 当前 evidence recall 已经是 1.0，主要瓶颈不是“完全没召回证据”，而是 reader/context organization 没有稳定抽取 preference anchors、约束和可用推荐维度。

## Decision

不跑 LoCoMo full，不进入主线。v76 是有价值的诊断：profile repair 应作为低频补救，而不是通用答案改写器。下一步应先研究 changed badcases 和 preference/profile 类错误，设计更好的 profile evidence compiler 或 answer contract，再决定是否做新 full run。

## Artifacts

- `judge_comparison_vs_v73.json`：fresh / controlled 对比。
- `delta_badcases.md`：changed predictions 与 repair cases。
- `deepseek_judge.json`：离线 judge 全量结果。
- `evidence_recall.json`：离线证据召回诊断。
