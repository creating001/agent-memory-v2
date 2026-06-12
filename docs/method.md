# Agent-Memory 方法调研终稿

本文件提供 Agent-Memory 外部方法总览、推荐主线和方法索引。`docs/architecture.md` 提供项目探索框架；详细方法卡片见 `docs/method_cards.md`。

## 总体判断

现有 Agent Memory 方法表面上分支很多：有人做图，有人做摘要，有人做 profile，有人做 memory OS，也有人做 skill 或 reflection。但如果把它们放回 LongMemEval 和 LoCoMo 的真实错误模式里看，核心矛盾其实很集中：长期记忆系统不是“记得越抽象越好”，而是要在很长、很碎、带时间变化的交互历史里，稳定找到可核验的原始证据，并让回答阶段不把证据用错。

LongMemEval 更像是在拷问证据保真度：答案可能来自用户，也可能来自助手；可能是旧状态，也可能被后续更新覆盖；可能需要拒答；也可能藏在任务型对话的低显著片段里。LoCoMo 更像是在拷问跨会话组织能力：同一个人物、事件、偏好、时间线会分散在很多轮对话里，单纯 dense top-k 很容易召回局部相似片段，却漏掉全局关系、历史顺序或完整列表。因此，真正有迁移价值的方法，往往不是单独某个“高级存储结构”，而是能同时解决 evidence preservation、multi-view retrieval、temporal validity 和 answer grounding 的组合。

从这些方法里可以看到一个清晰趋势：早期方法倾向把记忆压成 summary、profile 或少量 fact，优点是省 token，缺点是源证据丢失后不可恢复；GraphRAG、Hypergraph、Temporal KG、Hierarchical graph 等方法提升了多跳和枚举召回，但如果边和事实由 LLM 推断而没有 source id，就会把“合理关系”误当成“用户说过的事实”；Memory OS / SDK 类方法给了工程治理启发，例如 namespace、版本、权限、生命周期和可重建索引，但照搬会让系统过重；Skill / reflection 类方法能沉淀解题流程，却必须限制在 procedural 层，不能写入 benchmark 具体事实或答案。

所以，Agent-Memory 的主路线应该是 evidence-first，而不是 summary-first；应该是 multi-view retrieval，而不是只押注单一向量库；应该是 query-time compiler，而不是 build-time 过度总结；应该是 source-grounded verification，而不是让模型凭二手 memory 自由发挥。最稳的方向不是追求一个万能 memory object，而是建立一套可回溯、可消融、可逐步增强的记忆流水线：原文永远不丢，派生记忆只做索引和线索，最终答案必须回到原始 turn/session/page 上定案。

对你们当前项目来说，这也意味着下一步不应该盲目引入庞大的 memory OS 或训练型 skill optimizer。你们已有的 raw-turn evidence、query-time retrieval、路由、compiler 思路是对的。后续真正值得加的，是那些能在不破坏 clean setting 的前提下提升召回覆盖和证据使用稳定性的模块：temporal fact、entity/session graph、profile/event typed view、source expansion、evidence table、consistency verifier，以及面向 list/count/duration/update 的通用程序性策略。

## 推荐主线

### 1. 底座：Immutable Raw Evidence Store

所有原始 turn、session、page 必须作为不可变证据层保留，字段至少包含 source_id、session_id、turn_id、role、absolute date、relative order、raw text。任何派生 summary、fact、profile、graph edge、skill hint 都不能覆盖原文，也不能单独作为最终证据。这个底座吸收 LCM、MemGPT、GAM、MemMachine、Graphiti、Everything is Context 的共同精华：摘要可以错，图可以错，profile 可以过期，但 raw evidence 必须能展开复核。

优先实验：raw-turn only、raw-session/page、raw+neighbor expansion、summary-only、summary+source expansion。重点看 LongMemEval knowledge-update、temporal-reasoning、abstention，以及 LoCoMo temporal/open-domain 的 source recall、wrong-speaker rate 和 stale-fact rate。

### 2. 派生层：Typed Views，不做单一大摘要

派生记忆应拆成多种 typed view：event memory 记录发生过的事，atomic fact 记录可直接问答的事实，profile memory 记录稳定偏好和身份信息，temporal state 记录 valid_from/valid_to 与被覆盖关系，entity graph 记录人物/实体/关系，procedural memory 记录解题流程。每个派生项都必须带 source_ids、time span、confidence、memory_type、是否 inferred。这里可以借鉴 MIRIX、LangMem、LD-Agent、Memobase、MemOS、OpenMemory、Hindsight、Graphiti，但要坚持一个约束：derived memory 只做召回入口和排序特征，不直接替代原文。

优先实验：flat raw、raw+event、raw+profile、raw+event+profile、raw+temporal state、raw+entity graph。每组都要单独报告 profile hallucination、旧事实误用、source coverage，而不是只看总 accuracy。

### 3. 索引层：Dense + BM25 + Time + Entity/Graph + Hierarchy

单一路向量检索不够。Dense 负责语义相近，BM25 负责专名、数字、罕见词和原话匹配，time filter 负责“之前/之后/最近/当时/多久”这类约束，entity/session graph 负责跨会话人物和关系扩展，hierarchical/category traversal 负责 list/all/count 这类全局覆盖问题。HippoRAG2、MAGMA、HyperMem、Mnemis、Graphiti、Cognee 的价值都在这里：它们不是让图替代证据，而是让图帮助找到证据。

优先实验：dense-only、dense+BM25、dense+BM25+time、dense+BM25+entity expansion、dense+BM25+entity+hierarchy、graph as hint vs graph as evidence。重点看 LoCoMo multi-hop/list/open-domain 和 LongMemEval multi-session/temporal。

### 4. Query 层：Question-Text Router + Evidence Compiler

路由只能来自 question text、question date 和真实可见 memory metadata，不能使用 benchmark 标注、sample id、gold answer 或 judge signal。推荐把路由定义成 information need，而不是 benchmark type：current-state、historical-state、knowledge-update、duration、order、most-recent、list/count、preference/profile、assistant-provided、open-domain、abstention。检索后先形成 evidence table，再由 answer model 生成简洁 JSON answer，最后用 verifier 检查答案是否被 evidence table 支持。

优先实验：retrieve+direct answer、retrieve+evidence table、retrieve+evidence table+verifier、iterative retrieval depth=1/2/3。要报告 table coverage、table contradiction、verifier 改对/改错比例、answer unsupported rate。这个方向主要借鉴 GAM、SimpleMem、IterResearch、LongMemEval 官方分析、Hindsight 和 Memento 系列。

### 5. 程序性记忆：只存通用解题策略

Procedural memory 可以保留，但必须极其克制。它可以记录“duration 题先找起点和终点”“knowledge-update 题优先找冲突链和最新有效事实”“list/count 题要扩大召回并去重”“assistant-source 题必须区分 role”等通用策略；不能记录具体实体、答案、benchmark id 或数据集特有捷径。Acontext、Buffer of Thoughts、Memento、Memento-Skills、ReMe 的启发都应收敛到这一层。

优先实验：no-skill、manual generic skill、LLM-reflection skill、validated skill。所有 skill diff 必须经过泄漏检查，确认没有具体 gold answer、样本实体和数据集字段。

### 6. 治理层：Provenance、Version、Invalidation、Audit

Agent-Mem 如果要做成可发表/可复现的方法，不能只报最后准确率。每条派生记忆必须能说明来自哪些 source turns、什么时候生成、是否经过合并、是否被新事实覆盖、是否只是模型推断。每次 query 也应保存 Context Manifest：用了哪些检索视角、各自 top-k 是什么、哪些证据被 compiler 保留或丢弃、verifier 是否发现矛盾。这样错误分析才能区分 retrieval miss、compression loss、wrong route、compiler error 和 answer hallucination。

优先实验：manifest off/on、source expansion off/on、temporal invalidation off/on、derived memory 可回链/不可回链。这个治理层不会直接显得“炫”，但它决定方法是否可信、可诊断、可持续迭代。

## 最终落地优先级

第一优先级：强化 query-time evidence compiler 和 source expansion。原因是你们当前 raw evidence 路线已经有效，最常见的增量不是“没召回任何东西”，而是召回后没有稳定组织证据，尤其是 temporal、multi-hop、count/list、knowledge-update。

第二优先级：加入轻量 temporal/entity typed view。不要一开始做完整 temporal KG，而是先抽 entity、event/state、valid_from、valid_to、source_ids、supersedes。目标是帮助路由、扩展和冲突判断，不是让图直接回答。

第三优先级：针对 profile/preference/open-domain 增加 profile/event 双通道。Profile 处理稳定偏好，event 处理一次性事件，回答前必须比较二者是否冲突，避免把一次事件写成长期偏好。

第四优先级：把程序性经验沉淀成少量通用 skill。只沉淀流程，不沉淀事实。这个方向适合在主要检索/编译框架稳定后再做。

暂缓方向：大规模 memory OS、参数化/训练型个人模型、RL skill optimizer、复杂多智能体协作记忆、纯基础设施图数据库。这些方法有工程或理论价值，但短期对 LongMemEval/LoCoMo 的 clean 提分性价比不高。

## 方法索引

| # | 方法 | 链接 |
|---:|---|---|
| 1 | A-MEM: Agentic Memory for LLM Agents | 论文：[论文/页面](https://arxiv.org/abs/2502.12110)；代码：[GitHub](https://github.com/WujiangXu/A-mem) |
| 2 | ACON: Optimizing Context Compression for Long-horizon LLM Agents | 论文：[论文/页面](https://arxiv.org/abs/2510.00615)；代码：[GitHub](https://github.com/microsoft/acon) |
| 3 | Acontext | 无论文，项目页：[GitHub](https://github.com/memodb-io/Acontext)；代码：[GitHub](https://github.com/memodb-io/Acontext) |
| 4 | agentmemory | 论文：[论文/页面](https://www.agent-memory.dev/)；代码：[GitHub](https://github.com/rohitg00/agentmemory) |
| 5 | Beyond RAG for Agent Memory: Retrieval by Decoupling and Aggregation | 论文：[论文/页面](https://arxiv.org/abs/2602.02007)；代码：[GitHub](https://github.com/HU-xiaobai/xMemory) |
| 6 | Buffer of Thoughts: Thought-Augmented Reasoning with Large Language Models | 论文：[论文/页面](https://arxiv.org/abs/2406.04271)；代码：[GitHub](https://github.com/YangLing0818/buffer-of-thought-llm) |
| 7 | ChatHaruhi: Reviving Anime Character in Reality via Large Language Model | 论文：[论文/页面](https://arxiv.org/abs/2308.09597)；代码：[GitHub](https://github.com/LC1332/Chat-Haruhi-Suzumiya) |
| 8 | Evaluating Very Long-Term Conversational Memory of LLM Agents | 论文：[论文/页面](https://arxiv.org/abs/2402.17753)；代码：[GitHub](https://github.com/snap-research/LoCoMo) |
| 9 | EverOS (part of EverMind) | 论文：[论文/页面](https://evermind-ai.com/)；代码：[GitHub](https://github.com/EverMind-AI/EverOS) |
| 10 | Everything is Context: Agentic File System Abstraction for Context Engineering | 论文：[论文/页面](https://arxiv.org/abs/2512.05470)；代码：[GitHub](https://github.com/AIGNE-io/aigne-framework) |
| 11 | From RAG to Memory: Non-Parametric Continual Learning for Large Language Models | 论文：[论文/页面](https://arxiv.org/abs/2502.14802)；代码：[GitHub](https://github.com/OSU-NLP-Group/HippoRAG) |
| 12 | gbrain | 论文：[论文/页面](https://github.com/garrytan/gbrain)；代码：[GitHub](https://github.com/garrytan/gbrain) |
| 13 | General Agentic Memory Via Deep Research | 论文：[论文/页面](https://arxiv.org/abs/2511.18423)；代码：[GitHub1](https://github.com/VectorSpaceLab/general-agentic-memory/)；[GitHub2](https://github.com/VectorSpaceLab/general-agentic-memory) |
| 14 | Generative Agents: Interactive Simulacra of Human Behavior | 论文：[论文/页面](https://arxiv.org/abs/2304.03442)；代码：[GitHub](https://github.com/joonspk-research/generative_agents) |
| 15 | Hello Again! LLM-powered Personalized Agent for Long-term Dialogue | 论文：[论文/页面](https://arxiv.org/abs/2406.05925)；代码：[GitHub](https://github.com/leolee99/LD-Agent) |
| 16 | Hindsight is 20/20: Building Agent Memory that Retains, Recalls, and Reflects | 论文：[论文/页面](https://arxiv.org/abs/2512.12818)；代码：[GitHub](https://github.com/vectorize-io/hindsight) |
| 17 | HippoRAG: Neurobiologically Inspired Long-Term Memory for Large Language Models | 论文：[论文/页面](https://arxiv.org/abs/2405.14831)；代码：[GitHub](https://github.com/OSU-NLP-Group/HippoRAG) |
| 18 | Honcho | 论文：[论文/页面](https://honcho.dev/)；代码：[GitHub](https://github.com/plastic-labs/honcho) |
| 19 | Human-inspired Episodic Memory for Infinite Context LLMs | 论文：[论文/页面](https://arxiv.org/abs/2407.09450)；代码：[GitHub](https://github.com/em-llm/EM-LLM-model) |
| 20 | HyperMem: Hypergraph Memory for Long-Term Conversations | 论文：[论文/页面](https://arxiv.org/abs/2604.08256)；代码：[GitHub](https://github.com/EverMind-AI/EverOS/tree/main/methods/HyperMem) |
| 21 | IterResearch: Rethinking Long-Horizon Agents with Interaction Scaling | 论文：[论文/页面](https://arxiv.org/abs/2511.07327)；代码：[GitHub](https://github.com/Alibaba-NLP/DeepResearch) |
| 22 | LangMem | 论文：[论文/页面](https://langchain-ai.github.io/langmem/)；代码：[GitHub](https://github.com/langchain-ai/langmem) |
| 23 | LCM: Lossless Context Management | 论文：[论文/页面](https://papers.voltropy.com/LCM)；代码：[GitHub](https://github.com/Martian-Engineering/lossless-claw) |
| 24 | LightMem: Lightweight and Efficient Memory-Augmented Generation | 论文：[论文/页面](https://arxiv.org/abs/2510.18866)；代码：[GitHub](https://github.com/zjunlp/LightMem) |
| 25 | LongMemEval: Benchmarking Chat Assistants on Long-Term Interactive Memory | 论文：[论文/页面](https://arxiv.org/abs/2410.10813)；代码：[GitHub](https://github.com/xiaowu0162/LongMemEval) |
| 26 | MAGMA: A Multi-Graph based Agentic Memory Architecture for AI Agents | 论文：[论文/页面](https://arxiv.org/abs/2601.03236)；代码：[GitHub](https://github.com/FredJiang0324/MAMGA) |
| 27 | Mem0: Building Production-Ready AI Agents with Scalable Long-Term Memory | 论文：[论文/页面](https://arxiv.org/abs/2504.19413)；代码：[GitHub1](https://github.com/mem0ai/mem0)；[GitHub2](https://github.com/TeleAI-UAGI/TeleMem) |
| 28 | Mem9 | 论文：[论文/页面](https://mem9.ai/)；代码：[GitHub](https://github.com/mem9-ai/mem9) |
| 29 | Memanto: Typed Semantic Memory with Information-Theoretic Retrieval for Long-Horizon Agents | 论文：[论文/页面](https://arxiv.org/abs/2604.22085)；代码：[GitHub](https://github.com/moorcheh-ai/memanto) |
| 30 | Memary | 论文：[论文/页面](https://kingjulio8238.github.io/memarydocs/)；代码：[GitHub1](https://github.com/kingjulio8238/memary)；[GitHub2](https://github.com/kingjulio8238/Memary) |
| 31 | MemClaw (Caura) | 论文：[论文/页面](https://memclaw.net/)；代码：[GitHub](https://github.com/caura-ai/caura-memclaw) |
| 32 | Memento 2: Learning by Stateful Reflective Memory | 论文：[论文/页面](https://arxiv.org/abs/2512.22716)；代码：[GitHub](https://github.com/Agent-on-the-Fly/Memento) |
| 33 | Memento-Skills: Let Agents Design Agents | 论文：[论文/页面](https://arxiv.org/abs/2603.18743)；代码：[GitHub](https://github.com/Memento-Teams/Memento-Skills) |
| 34 | MemGPT: Towards LLMs as Operating Systems | 论文：[论文/页面](https://arxiv.org/abs/2310.08560)；代码：[GitHub](https://github.com/letta-ai/letta) |
| 35 | Memlayer | 无论文，项目页：[GitHub](https://github.com/divagr18/memlayer)；代码：[GitHub](https://github.com/divagr18/memlayer) |
| 36 | MemMachine | 论文：[论文/页面](https://memmachine.ai/)；代码：[GitHub](https://github.com/MemMachine/MemMachine) |
| 37 | Memobase | 论文：[论文/页面](https://memobase.io/)；代码：[GitHub](https://github.com/memodb-io/memobase) |
| 38 | Memori | 无论文，项目页：[GitHub](https://github.com/GibsonAI/Memori)；代码：[GitHub](https://github.com/GibsonAI/Memori) |
| 39 | Memory Intelligence Agent | 论文：[论文/页面](https://arxiv.org/abs/2604.04503)；代码：[GitHub](https://github.com/ECNU-SII/MIA) |
| 40 | Memory OS of AI Agent | 论文：[论文/页面](https://arxiv.org/abs/2506.06326)；代码：[GitHub](https://github.com/BAI-LAB/MemoryOS) |
| 41 | MemoryBank: Enhancing Large Language Models with Long-Term Memory | 论文：[论文/页面](https://arxiv.org/abs/2305.10250)；代码：[GitHub](https://github.com/zhongwanjun/MemoryBank-SiliconFriend) |
| 42 | MemOS: A Memory OS for AI System | 论文：[论文/页面](https://arxiv.org/abs/2507.03724)；代码：[GitHub](https://github.com/MemTensor/MemOS) |
| 43 | MemU | 论文：[论文/页面](https://memu.pro/)；代码：[GitHub](https://github.com/NevaMind-AI/memU) |
| 44 | MIRIX: Multi-Agent Memory System for LLM-Based Agents | 论文：[论文/页面](https://arxiv.org/abs/2507.07957)；代码：[GitHub](https://github.com/Mirix-AI/MIRIX) |
| 45 | Mnemis: Dual-Route Retrieval on Hierarchical Graphs for Long-Term LLM Memory | 论文：[论文/页面](https://arxiv.org/abs/2602.15313)；代码：[GitHub](https://github.com/microsoft/Mnemis) |
| 46 | What Deserves Memory: Adaptive Memory Distillation for LLM Agents | 论文：[论文/页面](https://arxiv.org/abs/2508.03341)；代码：[GitHub](https://github.com/nemori-ai/nemori) |
| 47 | OpenMemory | 论文：[论文/页面](https://openmemory.cavira.app/)；代码：[GitHub1](https://github.com/caviraoss/openmemory)；[GitHub2](https://github.com/CaviraOSS/OpenMemory) |
| 48 | Optimizing the Interface Between Knowledge Graphs and LLMs for Complex Reasoning | 论文：[论文/页面](https://arxiv.org/abs/2505.24478)；代码：[GitHub](https://github.com/topoteretes/cognee) |
| 49 | Remember Me, Refine Me: A Dynamic Procedural Memory Framework for Experience-Driven Agent Evolution | 论文：[论文/页面](https://arxiv.org/abs/2512.10696)；代码：[GitHub1](https://github.com/agentscope-ai/ReMe)；[GitHub2](https://github.com/modelscope/ReMe) |
| 50 | SimpleMem: Efficient Lifelong Memory for LLM Agents | 论文：[论文/页面](https://arxiv.org/abs/2601.02553)；代码：[GitHub](https://github.com/aiming-lab/SimpleMem) |
| 51 | Zep: A Temporal Knowledge Graph Architecture for Agent Memory | 论文：[论文/页面](https://arxiv.org/abs/2501.13956)；代码：[GitHub](https://github.com/getzep/graphiti) |

## 详细方法卡片

详细方法卡片已拆分到 `docs/method_cards.md`。需要深入参考具体方法时再读取该文件，不要默认加载全文。
