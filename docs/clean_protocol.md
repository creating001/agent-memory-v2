# Agent-Memory Clean Protocol

本文件规定通用 clean 规则。所有方法、代码和实验默认遵守这些规则。

## Core Rules

- 禁止在预测阶段使用任何答案相关信息进行作弊。
- judge 只能用于离线评测和错误分析，不能参与同一轮预测。
- 禁止使用 benchmark 隐藏标注或样本级信息，包括 question_type、category、sample id、row index。
- 禁止根据具体测试题、具体测试实体或测试集错误结果手写规则。
