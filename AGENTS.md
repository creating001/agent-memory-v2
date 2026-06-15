# AGENTS.md

## 项目说明

本项目目标是搭建一套通用、clean、可消融、可持续迭代的 Agent-Memory 框架，并在 LongMemEval 和 LoCoMo 等 benchmark 上验证其有效性。

## 必须遵守

- 所有 memory、retrieval、route、answer、verifier、eval 和结果汇报相关工作，都必须遵守 `docs/clean_protocol.md`。

## 参考文件

- `README.md`：项目入口和目录结构。
- `docs/clean_protocol.md`：clean setting 和泄漏红线。修改预测或评测逻辑前必须阅读。
- `docs/constraints.md`：token、build/query 成本等技术指标约束。修改 retrieval、compiler、answer、verifier 或实验配置前必须阅读。
- `docs/experiment_protocol.md`：模型配置、judge prompt、指标和公共实验口径。修改模型、judge、metric、统计脚本或实验汇报格式前必须阅读。
- `docs/architecture.md`：项目主框架。设计或修改 memory、retrieval、compiler、answer、verifier 等核心流程时必须阅读。
- `docs/method.md`：外部方法总览。设计新 memory 方法、route、compiler、ablation 或 roadmap 时必须阅读。
- `docs/method_cards.md`：详细方法 card。需要深入参考具体方法时再阅读；小的修 bug、路径调整、格式改动不需要默认加载全文。

## 开发规则

- 配置和关键参数要显式记录，避免隐藏常量。
- 不能无说明地用大幅增加 query tokens、 build tokens 的方式换分；超出 `docs/constraints.md` 预算的实验必须标成 expensive / diagnostic。
- 设计新方法前必须参考 `docs/method.md`；需要深入某类方法时再读 `docs/method_cards.md`，并在方案或实验记录里说明借鉴了哪些外部方法、取舍是什么。
- 正式实验和结果汇报必须记录本地 git commit；
- 正式实验必须在 `experiments/` 下留下人类可读的实验记录，不能只把预测文件和日志丢到 `outputs/`。记录应包含目的、改动、配置、指标、token 成本、诊断结论、输出路径和下一步建议。
