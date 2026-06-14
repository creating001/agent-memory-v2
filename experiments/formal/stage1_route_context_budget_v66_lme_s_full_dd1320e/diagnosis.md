# 诊断

## 背景

v42 错题诊断显示：LongMemEval-S full 中 evidence recall 已是 1.0，多数错题的 answer session rank 也在前列。问题更像是候选组织和 answer 聚合，而不是单纯 retrieval recall 不足。用户也指出 query token 压着预算上限可能引入上下文噪声。

v66 参考了外部 `creating001-agent-memory` 中 strategy-aware context budget / user-preference prioritization 的思想，但没有迁移任何 gold、judge、sample id、benchmark 标签或样本级逻辑。实现上只使用通用 route-derived `compiler.route_overrides`。

## 改动

在 v42 基础上增加：

```json
"route_overrides": {
  "temporal_lookup": {"max_evidence_items": 30, "max_evidence_chars": 15500},
  "list_count": {"max_evidence_items": 30, "max_evidence_chars": 15500},
  "current_state": {"max_evidence_items": 30, "max_evidence_chars": 15500}
}
```

其他保持不变：

- build memory 不变。
- retrieval top_k / dense / BM25 不变。
- answer model 不变，max input/output 仍为 131072 / 16384。
- answer cache 使用新 namespace，避免污染 v42 cache。

## 结果

- accuracy：0.754，低于 v42 修复控制 0.772，也低于原 v42 0.774。
- avg query tokens：5235.538，确实显著低于 v42 修复控制 5864.706。
- avg compiled evidence items：30.65，低于 v42 的 34.062。
- avg context chars：16909.644，低于 v42 的约 19665。
- evidence recall：1.0。

`judge_comparison_vs_v42.json` 显示：

- CORRECT -> CORRECT：359
- WRONG -> CORRECT：18
- WRONG -> WRONG：96
- CORRECT -> WRONG：27

按 question type，主要损失来自：

- multi-session：CORRECT->WRONG 10，WRONG->CORRECT 7。
- single-session-preference：CORRECT->WRONG 5，WRONG->CORRECT 2。
- temporal-reasoning：CORRECT->WRONG 7，WRONG->CORRECT 6。

## 判断

v66 说明 query token 不是越多越好，但固定截断也不是答案。它降低 token 后仍保持 evidence recall=1.0，说明 recall 指标不足以衡量 answer 阶段需要的细节完整性。对于 list/temporal/current_state，模型可能需要多个同 session 或近邻候选做去重、计数、时间端点和状态更新；固定截断破坏了部分细节，导致净负向。

## 后续取舍

不继续跑 v66 变体的 full。下一步应避免机械缩短 context，改为更有信息结构的方案：

- 用 build-stage typed memory 生成 candidate clusters / event chains，但最终仍回链 raw rows。
- query 侧先组织候选组和冲突候选，再让 answer model 基于 raw rows 作最终判断。
- 对 preference/advice 类问题单独处理“给出偏好类型而非具体新名字”的 general answer policy，但需要小心避免 broad repair 导致 full 负向。
