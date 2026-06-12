# Agent-Memory Technical Constraints

本文件规定技术指标约束，用于防止方法通过无限增加 token、LLM 调用或复杂度来换取不可持续的分数。这些约束是默认工程预算；诊断实验、baseline 复现或明确标注的 expensive ablation 可以临时超出，但不能无说明地作为主线方法。

## Benchmark Scope

- LongMemEval：默认使用完整评测集。
- LoCoMo：只使用 non-adversarial subset，即排除 adversarial/category 5。

## Performance Targets

正确率目标是阶段性主线目标，不是破坏 clean setting 或成本约束的理由。所有结果必须同时满足 `docs/clean_protocol.md` 和本文档的 token 预算要求。

| Benchmark | Scope | Baseline target | Minimum target | Mainline target | Stretch target |
|---|---|---:|---:|---:|---:|
| LongMemEval | full | >= 80% accuracy | >= 82% accuracy | >= 84% accuracy | >= 86% accuracy |
| LoCoMo | non-adversarial | >= 78% accuracy | >= 80% accuracy | >= 82% accuracy | >= 84% accuracy |

## Default Budgets

| 指标 | 目标 |  主线硬约束 |
|---|---:|---:|
| LongMemEval avg build tokens | <= 300K / sample |  > 360K 只能作为 expensive / diagnostic |
| LoCoMo avg build tokens | <= 100K / sample |  > 120K 只能作为 expensive / diagnostic |
| LongMemEval avg query tokens | <= 6K / QA |  > 8K 只能作为 expensive / diagnostic |
| LoCoMo avg query tokens | <= 6K / QA | > 8K 只能作为 expensive / diagnostic |

其中 `avg_build_tokens` 和 `avg_query_tokens` 必须只包含 LLM 调用 token，embedding 模型和 rerank 模型的 token 不纳入统计。
