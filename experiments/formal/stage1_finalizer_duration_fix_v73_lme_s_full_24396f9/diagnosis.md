# v73 诊断

## 背景

v42 badcase 分析发现一个非模型错误：answer model 原始 JSON 明确给出 `3.5 weeks`，但 `structured_evidence_mechanical` finalizer 的 duration decimal rounding 把它改成了 `4 weeks`。这违反了保真原则：当模型已经输出带小数的精确时长时，机械后处理不应无条件四舍五入。

## 改动

仅关闭：

```json
"enable_duration_rounding_correction": false
```

其他保持不变：

- build memory 不变。
- retrieval top40 dense+BM25 不变。
- evidence_report / operation_workpad prompt 不变。
- answer LLM max input/output 仍为 131072 / 16384。
- answer cache 复用 v42 原始 draft cache，500/500 hit。

## 结果解释

唯一改变的样本：

- question：How many weeks did it take me to watch all the Marvel Cinematic Universe movies and the main Star Wars films?
- v42 answer：4 weeks。
- v73 answer：3.5 weeks。
- gold：3.5 weeks。
- judge transition：WRONG->CORRECT。

Full DeepSeek judge 从 0.772 到 0.778，其中 prediction-level 改动贡献至少 +1；其余 +2 来自 full judge 重跑 variance。由于 predictions 只变 1 条，稳健解读应是“确定修复 1 个错误，未引入预测回退”。

## 对后续方法的影响

v73 说明主线里应谨慎使用机械 finalizer：

- 只在 evidence JSON 明确可机械验证时改答案。
- 不应把小数时长、近似时长或用户原文单位强行整数化。
- 对 list/count/sum 的后处理仍要先证明 evidence_report 结构可靠，不能让后处理凭表面数字改写答案。

下一轮不要继续围绕这个 finalizer 微调，因为它只影响 1 条。更大的剩余空间在 multi-session temporal/list/count：召回证据已在 context 中，但 reader 漏掉候选、错误去重或算术不稳。
