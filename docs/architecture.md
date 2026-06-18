# Agent-Memory Architecture

本文件定义 Agent-Memory 项目的探索框架。它不是固定实现方案，而是给后续方法设计提供方向。`docs/method.md` 提供外部方法参考；本文件描述当前推荐的系统原则、模块边界和探索空间。方法和框架都是灵活的，只要遵守 clean setting、成本约束和可追溯要求，可以持续替换、扩展或重组模块。

## 1. 核心目标

本项目目标是构建一个通用、clean、且具有方法创新性的 Agent Memory 系统，并在 LongMemEval-S full 和 LoCoMo non-adversarial full 上用 judge accuracy 验证效果。核心不是固定某个现成框架，也不是为 benchmark 编写专门规则，而是在严格 clean setting 和成本约束下，系统性探索长期记忆的 build、management、retrieval、context organization 和 answer 机制。我们希望方法不仅能取得更高性能，还能体现本项目在长期记忆建模上的独特思考，形成一套更可靠、更可解释、性能更强、更具泛化能力的 Agent Memory 框架。框架、模块和具体方法都服务于这个目标，不应反过来限制方法探索。

核心要求：
- **clean**：不能使用 gold answer、judge output、benchmark 标签、sample id、test feedback 或样本级规则。
- **有效**：主要看 judge accuracy；F1、BLEU 只能作为辅助诊断。
- **通用**：不能只为某个 benchmark 写专门捷径，要能解释为真实 agent memory 系统中的合理机制。
- **可消融**：每个新增模块都应能关闭，方便判断收益来自哪里。
- **可追溯**：正式实验必须记录 commit、配置、token 成本、输出路径和诊断。

因此，本项目不是要证明某个固定 skeleton 永远正确，而是要围绕“长期记忆管理能力”持续提升：写入阶段如何沉淀有用 memory，查询阶段如何激活相关 memory，回答阶段如何稳定使用 memory，评测阶段如何定位错误并迭代。

## 2. 总体探索流程

下面是当前推荐的高层流程。具体实现可以替换或裁剪其中的模块。

```text
原始对话
  -> Build-stage memory 管理
       - 原始记忆 / raw conversation memory
       - LLM 参与的 typed memory 构建
       - event / fact / profile / preference / state / relation 等派生视图
       - dedup / merge / supersede / version / provenance
  -> 检索索引构建
       - raw turn/session index
       - typed memory index
       - time/entity/profile/event 等辅助索引

问题输入
  -> 问题分析 / route
  -> 多视角 memory 激活
  -> raw / typed / temporal / profile / event 综合检索
  -> memory context 组织 / compiler
  -> 答案生成
  -> 答案校验 / guardrails
  -> 最终答案 + trace

预测结果
  -> 离线评测
  -> 错误分析
  -> 消融与方法迭代
```

## 3. 大致的可探索模块

### Build-stage Memory Management

Build 阶段必须是本项目的重要能力，而不是只在 query 阶段临时检索 raw text。大模型可以参与 build 阶段，用于抽取、归纳、合并和维护 memory；但 build 结果不能引入任何不 clean 信息。

可探索方向：
- LLM 抽取 typed memory：event、fact、preference、profile、state、relationship、plan
- profile/event 双通道：稳定偏好和一次性事件分开管理
- temporal state：记录 valid_from、valid_to、supersedes、updated_by
- entity/relation memory：用于跨会话、多跳和人物关系激活
- memory manager：dedup、merge、conflict detection、supersede、importance、recency
- memory namespaces：user、assistant、session、topic、time scope
- build cache：避免重复对同一 conversation 做昂贵抽取

基本要求：
- build 输入只能来自原始对话和可见 metadata，不能读取 question 的 gold/judge/标签信息。
- build memory 可以作为预测时的一等信息源，但必须有清晰的类型、来源或生成记录，方便诊断。
- summary/profile/fact 可以提高效果，但不应无痕覆盖原始对话；如果系统选择让派生 memory 直接参与回答，必须在实验中记录这一设计和风险。
- 关键策略必须可关闭做 ablation，例如 raw-only、typed-memory-only、raw+typed、profile on/off、event on/off、temporal on/off。

### Raw Memory / Evidence Store

保存完整原始对话，是最底层、最可靠的记忆，也是最终事实来源。

可探索方向：
- turn-level 存储
- session-level 存储
- page / episode-level 存储
- turn + neighbor context
- raw evidence 与 metadata 的组织方式

基本要求：
- 保留 source id、role、date、session、order 等元信息。
- 能被 query-time 展开和引用。
- 原始对话不应被删除；即使答案主要来自 typed memory，也要能回查原始上下文用于诊断。

### Derived Memory Views

派生记忆是增强系统能力的核心视图，用于提高召回、压缩搜索空间、管理长期状态和组织证据。它不是固定某一种形式，可以是 LLM 抽取的 typed records，也可以是 profile、timeline、entity graph、temporal KG 或 procedural memory。

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
- 推荐保留 source_ids 或 provenance，便于诊断和回查；但是否强制 source-grounded 取决于具体方法设计和实验目标。
- 可以作为召回线索、排序特征、compiler 上下文，必要时也可以作为 answer context 的一部分。
- 应能单独关闭做 ablation，并报告它带来的 accuracy、token 成本和错误类型变化。

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

### Memory Context Organization / Compiler

Compiler 负责把激活出来的 memory 和 raw context 整理成 answer model 更容易使用的结构。它不只是 evidence table，也可以是 typed memory table、timeline、profile/event 对照、entity relation view、conflict chain 或 verifier input。

可探索方向：
- typed memory table
- evidence table
- timeline
- entity table
- profile / event 对照
- conflict chain
- list / count aggregation
- duration calculation
- missing evidence detection

重点问题：
- memory 已经激活时，如何减少 answer 阶段用错 memory。
- 如何处理过期事实、说话人错误、时间计算错误、profile 与 event 冲突。
- 如何在 accuracy 和可验证性之间取舍；source-grounded 是重要手段，但不是唯一目标。

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
- 关键配置和运行命令
- 输出目录和结果文件
- 本次改动对应的模块和预期作用

如果一个结果无法回到明确的代码状态、配置和输出文件，就不应作为正式主线结果汇报。
