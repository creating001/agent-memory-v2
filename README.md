# Agent-Memory

本项目目标是搭建一套通用、clean、可消融、可持续迭代的 Agent-Memory 框架。LongMemEval 和 LoCoMo 是用于验证的 benchmark，用于检验框架在长期对话记忆任务中的有效性。核心目标不是为某个 benchmark 写专门规则，而是在 clean 和成本约束下沉淀一套更高性能、更可靠、更可解释、更具泛化能力的 Agent-Memory 方法。

## 目录结构

```text
.
├── AGENTS.md                    # Codex 开发协作规则
├── README.md                    # 项目入口说明
├── docs/
│   ├── clean_protocol.md        # clean setting 和泄漏红线
│   ├── constraints.md           # token、调用次数和成本约束
│   ├── experiment_protocol.md   # 模型、judge prompt 和指标协议
│   ├── architecture.md          # 项目探索框架
│   ├── method.md                # 外部方法总览和推荐主线
│   └── method_cards.md          # 详细方法 card
├── src/                         # 本项目自己的核心方法代码
├── configs/                     # 模型、检索、路由、实验配置
├── scripts/                     # 运行、评测、分析、数据准备脚本
├── experiments/                 # 面向人工查看的实验看板、ablation、诊断报告
├── outputs/                     # 预测结果、日志、中间产物，默认不作为方法代码
├── data/                        # 本地数据入口或软链接说明，不提交大数据
└── external/                    # 外部 repo、baseline 和参考实现
```

## 重要文档

- `docs/clean_protocol.md`：所有方法、代码和实验必须遵守的 clean 规则。
- `docs/constraints.md`：token、LLM 调用次数、build/query 成本等技术指标约束。
- `docs/experiment_protocol.md`：模型配置、judge prompt、指标和公共实验口径。
- `docs/architecture.md`：项目主框架和可探索模块。
- `docs/method.md`：外部方法总览、推荐主线和方法索引。
- `docs/method_cards.md`：详细方法 card，需要深入参考具体方法时再读。

## 实验可追溯

实验可追溯主要依赖本地 git。正式实验和结果汇报应记录对应的 commit、是否存在未提交改动、关键配置、运行命令和输出路径。方法迭代应尽量保持改动小而清晰，方便用 git diff 回看每次增益来自哪里。

`experiments/` 是主要观察入口，不只是日志 dump。每个正式实验应在 `experiments/` 下留下一个可读目录，至少包含实验目的、方法改动、配置摘要、指标结果、token 成本、关键诊断、输出路径和下一步判断。用户主要通过这个目录观察 Codex 的实验结果和方法迭代过程。

## 外部方法参考

本项目不是从零拍脑袋设计 memory 方法。`docs/method.md` 和 `docs/method_cards.md` 是重要设计输入：提出新 memory、retrieval、compiler、verifier 或 ablation 时，应先参考外部方法，总结可迁移机制、舍弃原因和预期收益，再落到本项目的 clean、成本和可消融约束下实现。
