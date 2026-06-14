# Diagnosis for v77 missing reason enrichment

## Summary

v77 是零额外 token 的 finalizer ablation：将 draft JSON 的 `missing` reason 拼进 generic insufficient answer。它 clean、可追溯、成本不变，但 full accuracy 没有提升。

## Key Metrics

- fresh DeepSeek accuracy：0.772，386/500。
- v73 fresh accuracy：0.778，389/500。
- evidence_recall：1.0。
- avg_build_tokens：80346.246。
- avg_query_tokens：5864.706。
- finalizer_applied：42/500。

## Comparison

Fresh judge vs v73：
- CORRECT->CORRECT：380。
- WRONG->WRONG：105。
- WRONG->CORRECT：6。
- CORRECT->WRONG：9。

Prediction-changed controlled comparison vs v73：
- prediction_changed：42。
- WRONG->CORRECT：4。
- CORRECT->WRONG：4。
- WRONG->WRONG：23。
- CORRECT->CORRECT：11。
- controlled accuracy：389/500 = 0.778。

## Error Pattern

- 正向样本主要是 missing target 明确的拒答，例如没有提到 egg tarts、iPad case、Sapiens 剩余页数、Sacramento Airbnb。
- 回退样本也多是拒答：更具体的 missing reason 让 judge 认为答案缩窄或没有覆盖 gold rubric。
- 这说明 LongMemEval 的 abstention/partial-support 判断不只是“越具体越好”；拒答措辞微调无法稳定提升。

## Decision

不进入主线，不跑 LoCoMo。删除顶层配置和源码分支，仅保留 formal 快照。下一步应研究 GPT/Qwen 差异和 v73 multi-session/temporal wrong cases，重点解决 reader 对已召回证据的聚合、时间计算和 partial-support 判断。
