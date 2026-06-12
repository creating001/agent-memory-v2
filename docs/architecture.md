# Agent-Memory Architecture

本文件定义 Agent-Memory 项目的探索框架。它不是固定实现方案，而是给后续方法设计提供方向。`docs/method.md` 提供外部方法参考；本文件描述我们给出的大致思路和探索空间。

## 1. 核心目标

本项目目标是搭建一套通用、clean、可消融、可持续迭代的 Agent-Memory 框架，体现我们方法在长期对话记忆任务中的有效性和优势，并在 LongMemEval 和 LoCoMo 这两个 benchmark 上进行性能验证。我们不希望为某个 benchmark 写专门规则，而是希望在 clean 和成本约束下探索一套更高性能、更可靠、更可解释、更具泛化能力的 Agent-Memory 框架方法。

## 2. 总体探索流程

下面是当前推荐的高层流程。具体实现可以替换或裁剪其中的模块。

```text
原始对话
  -> 记忆存储
       - 原始记忆 / evidence memory
       - 派生记忆视图
  -> 检索索引构建

问题输入
  -> 问题分析 / route
  -> 多视角检索
  -> 原始证据扩展
  -> 证据整理 / compiler
  -> 答案生成
  -> 答案校验 / guardrails
  -> 最终答案 + trace

预测结果
  -> 离线评测
  -> 错误分析
  -> 消融与方法迭代
```

## 3. 大致的可探索模块

### Raw Memory / Evidence Store

保存完整原始对话，是最底层、最可靠的记忆，也是最终事实来源。

可探索方向：
- turn-level 存储
- session-level 存储
- page / episode-level 存储
- turn + neighbor context
- raw evidence 与 metadata 的组织方式

基本要求：
- 保留 source id、role、date、session、order 等元信息
- 能被 query-time 展开和引用
- 不被 summary、profile、fact 或 graph 替代

### Derived Memory Views

派生记忆是可选增强视图，用于提高召回、压缩搜索空间和组织证据。它不是 memory 的全部，也不能替代 raw memory。

可探索方向：
- session / episode summary
- event memory
- atomic fact
- profile fact
- temporal state
- entity / relation graph
- procedural skill
- error / reflection memory

基本要求：
- 必须回链 source_ids
- 只能作为召回线索、排序特征或 compiler 辅助
- 应能单独关闭做 ablation

### Retrieval

检索层负责从 raw memory 和派生视图中找到候选证据。

可探索方向：
- dense retrieval
- BM25 / lexical retrieval
- hybrid retrieval
- RRF / rank fusion
- rerank
- time-aware retrieval
- role-aware retrieval
- session / neighbor expansion
- entity / graph expansion
- query expansion / decomposition

重点问题：
- 如何提高离线证据召回率
- 如何减少噪声证据
- 如何处理 multi-hop、temporal、list/count、preference 等不同信息需求

### Evidence Organization / Compiler

Compiler 负责把检索到的候选证据整理成 answer model 更容易使用的结构。

可探索方向：
- evidence table
- timeline
- entity table
- profile / event 对照
- conflict chain
- list / count aggregation
- duration calculation
- missing evidence detection

重点问题：
- 证据已经召回时，如何减少 answer 阶段用错证据
- 如何处理过期事实、说话人错误、时间计算错误
- 如何让答案更稳定地 grounded in evidence

### Answer / Verifier

Answer 模块生成最终答案；verifier 检查答案是否被证据支持。

可探索方向：
- direct answer
- JSON answer
- answer with evidence ids
- consistency verifier
- temporal verifier
- contradiction checker
- abstention checker

重点问题：
- 答案是否被证据支持
- 是否使用了错误说话人的证据
- 是否使用了过期事实
- 是否应该回答 unknown / cannot determine

## 4. 评估关注点

除了最终 accuracy，还应关注：
- evidence recall
- context precision
- wrong speaker rate
- stale fact rate
- unsupported answer rate
- abstention correctness
- token cost
- build/query cost
- regression cases

方法有效不只看整体分数，还要看它解决了哪些错误、引入了哪些新错误。

## 5. 外部方法参考

外部方法调研是本项目的重要设计输入。`docs/method.md` 提供推荐主线和方法索引，`docs/method_cards.md` 提供具体方法 card。设计新模块时，应明确回答：

- 参考了哪些外部方法？
- 借鉴的是 build 侧、retrieval 侧、compiler 侧、verifier 侧，还是治理/工程组织？
- 哪些部分被采用，哪些部分因为不 clean、成本高、训练依赖强或不适合文本长期记忆而舍弃？
- 预期解决什么错误类型，如何做 ablation 验证？

外部方法只能作为设计参考和 baseline 来源，不能直接变成 benchmark 专门规则，也不能绕过 `docs/clean_protocol.md` 和 `docs/constraints.md`。

## 6. 实验可追溯

实验可追溯以本地 git 为准。正式实验应记录：

- git commit hash
- 工作区是否 dirty
- 关键配置和运行命令
- 输出目录和结果文件
- 本次改动对应的模块和预期作用

如果一个结果无法回到明确的代码状态、配置和输出文件，就不应作为正式主线结果汇报。
