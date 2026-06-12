# Agent-Memory Clean Protocol

本文件规定通用 clean 规则。所有方法、代码和实验默认遵守这些规则。

## Core Rules

- 预测阶段只能使用真实系统可见的信息：问题文本、问题时间、原始对话、对话元数据、本地构建的 memory、检索/重排/编译/验证输出。
- 禁止在预测阶段使用任何答案相关信息，包括 gold answer、reference answer、target、judge label、judge rationale、judge output。
- judge 只能用于离线评测和错误分析，不能参与同一轮预测。
- 禁止使用 benchmark 隐藏标注或样本级信息，包括 question_type、category、sample id、qid、row index。
- 禁止根据具体测试题、具体测试实体或测试集错误结果手写规则。

## Review Checklist

- 是否读取了 gold / reference / target？
- 是否读取了 question_type / category / sample id / qid？
- 是否把 judge 输出传给 prediction？
- 是否存在样本级 if/else？
- 派生 memory 是否有 source_ids？
