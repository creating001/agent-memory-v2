# Agent-Memory 方法详细卡片

本文件包含 51 个方法的详细 card。建议只在需要深入参考具体方法时读取。方法总览和推荐主线见 `docs/method.md`。

## 1. A-MEM: Agentic Memory for LLM Agents

- **资料**：类型：图记忆/结构化记忆；论文：[论文/页面](https://arxiv.org/abs/2502.12110)；代码：[GitHub](https://github.com/WujiangXu/A-mem)

- **动机**：A-MEM 针对的是普通 memory bank 只有“存入/相似度检索”、组织结构固定的问题。LoCoMo 的多跳、时间和 open-domain 问题常要求把分散会话中的小事实连起来；LongMemEval 还要求区分用户/助手来源、旧事实和更新事实。单纯 top-k chunk 容易召回冗余相邻话题，缺少可遍历关系。
- **方法 - Build 侧**：它借鉴 Zettelkasten，把每条记忆写成 atomic note，保留原始内容和 timestamp，同时由 LLM 生成 keywords、tags、contextual description。新 note 写入时先用 embedding 找近邻，再让 LLM 判断是否建立 linked memories；随后触发 memory evolution，只更新邻居的 context、keywords、tags 等派生属性。
- **方法 - Query 侧**：查询先 embedding 到 note 空间，论文主要用 top-k relevant memories 注入上下文，并在 LoCoMo 上分析不同题型的效果。迁移到 Agent-Mem 时，link 适合作为候选扩展，但答案必须回到 raw turn/source span，而不能只信 note 描述。
- **优点**：note 比纯 chunk 多了主题、标签、上下文和边，适合多跳召回；选择性 top-k 比全量 LoCoMo/LongMemEval 历史省 token；动态演化能逐渐改善同一用户长期主题的组织。
- **缺点/风险**：Build 阶段 LLM 调用重；evolution 若改写事实会制造无源记忆；keywords 不含说话人或时间时，LongMemEval 的 assistant-source、knowledge-update 和 temporal 题会出错。
- **可借鉴点与实验**：做四档 ablation：raw-round RAG、+atomic note metadata、+link expansion、+metadata-only evolution。强约束 raw evidence immutable，所有 note/link 带 `source_turn_ids`。分 LoCoMo multi-hop/temporal 和 LongMemEval KU/TR/ABS 看收益与污染率。

## 2. ACON: Optimizing Context Compression for Long-horizon LLM Agents

- **资料**：类型：压缩与上下文管理；论文：[论文/页面](https://arxiv.org/abs/2510.00615)；代码：[GitHub](https://github.com/microsoft/acon)

- **动机**：ACON 解决长程 agent 的上下文无限增长：工具输出、动作历史和中间状态越积越多，既耗 token，又让模型被噪声干扰。它不是长期记忆库，而是压缩策略优化；对 LongMemEval/LoCoMo 的启发在于如何做可审计的上下文压缩，而不是替代原始证据。
- **方法 - Build 侧**：ACON 固定 agent，不训练主模型，而在自然语言空间优化 compressor guideline。它收集“无压缩成功、压缩后失败”的轨迹，让 auditor 对比两条轨迹，标出丢失的变量、状态、前置条件、时间点和格式约束，再让 LLM 更新压缩提示；第二轮用成功压缩轨迹进一步删冗余。最后可把大模型 compressor 蒸馏到小模型。
- **方法 - Query 侧**：执行时分别压缩历史和最新 observation，保持足够状态供下一步行动。Agent-Mem 中更安全的用法是 query-time evidence-state：先检索原文，再把候选压成带 `evidence_ids/omitted_ids/conflicts` 的表格，答题前回查原文。
- **优点**：失败驱动，比人工写摘要规则更贴近任务；可同时降 token 和提升长工具链成功率；模型无关，适合 API 模型。
- **缺点/风险**：任何有损压缩都可能删除 LoCoMo/LongMemEval 的低显著性事实、否定、说话人或旧状态；若用测试集反馈优化 guideline，会形成评测泄漏。
- **可借鉴点与实验**：建立 `raw 正确、compressed 错误` 样本池。比较 raw-only、naive summary、ACON guideline、可逆 evidence table。指标同时看 token、答案准确率、evidence coverage、speaker/time 错误和 LongMemEval ABS 误答率。

## 3. Acontext

- **资料**：类型：产品/工程系统；无论文，项目页：[GitHub](https://github.com/memodb-io/Acontext)；代码：[GitHub](https://github.com/memodb-io/Acontext)

- **动机**：Acontext 的官方定位是“skill memory layer”：agent 不只要记住事实，还要记住做事方法、失败教训和用户偏好的工作流。它反对黑箱向量记忆污染上下文，主张把记忆写成可读、可编辑、可迁移的 Markdown skill 文件。
- **方法 - Build 侧**：系统以 session messages、工具调用、artifacts 和 task complete/failed 信号为输入，先做 task extraction，再由 LLM distillation 总结什么有效、什么失败、用户偏好是什么。Skill Agent 根据 learning space 中的 `SKILL.md` schema 决定新建或更新哪个 skill 文件；文件可以按联系人、项目、任务类型等用户定义结构组织。
- **方法 - Query 侧**：它不主打 embedding top-k，而是 progressive disclosure：给 agent `list_skills/get_skill/get_skill_file` 之类工具，agent 先看索引，再按需读取完整 skill。对 LongMemEval/LoCoMo，Acontext 不应保存实体答案，而应保存“如何解 temporal/list/count/update 题”的程序性策略。
- **优点**：Markdown 可审计、可 git diff、可人工修正；不绑定向量库或框架；适合跨 agent 复用 retrieval/compiler 操作规程。
- **缺点/风险**：事实召回能力弱，依赖 agent 主动选对 skill；skill 若写入 benchmark 实体、日期或答案，会污染评测；程序模板可能压过当前 evidence。
- **可借鉴点与实验**：只允许 entity-free procedural skill，例如“时间题先抽 query date 与事件 date”。做 no-skill、人工 skill、Acontext learned skill 三组；在 LongMemEval TR/KU/ABS 和 LoCoMo temporal/multi-hop 上测泛化，并审计 skill 是否含答案泄漏。

## 4. agentmemory

- **资料**：类型：产品/工程系统；论文：[论文/页面](https://www.agent-memory.dev/)；代码：[GitHub](https://github.com/rohitg00/agentmemory)

- **动机**：agentmemory 面向真实 coding agent 的跨会话记忆：每轮 prompt、工具调用、失败、项目结构和决策都需要持续捕获并可快速召回。官网强调“capture every session, recall in milliseconds”，并宣称 LongMemEval-S R@5 作为检索指标。
- **方法 - Build 侧**：它通过 hooks 自动采集 `SessionStart`、`UserPromptSubmit`、`PreToolUse`、`PostToolUse`、失败上下文、compact 前注入、subagent 生命周期等事件。原始 observation 经隐私过滤、去重、压缩和 consolidation，形成 Working、Episodic、Semantic、Procedural 四层；还包含版本、supersession、TTL、矛盾检测、audit row、知识图谱和 git snapshot。
- **方法 - Query 侧**：MCP/REST 暴露 recall、save、smart_search、sessions、timeline、audit 等工具。检索是 BM25、vector、KG entity traversal 三路信号，经 RRF 融合并做 session diversification，结果可追溯到 source observations。对 LoCoMo 需把会话对话导入为 observation/timeline；对 LongMemEval 则更接近线上 memory 系统。
- **优点**：工程面完整，有 hooks、MCP、REST、scope、审计和 provenance；混合检索比单向量更稳；适合 Agent-Mem runtime 参考。
- **缺点/风险**：默认面向 coding agent，压缩、TTL 和重要性淘汰会伤害长期对话小事实；KG 抽取错会扩散；自动删除与 LongMemEval ABS/KU 审计冲突。
- **可借鉴点与实验**：做 BM25-only、vector-only、graph-only、RRF、RRF+session diversification；再测 no consolidation、semantic consolidation、retention off/on。LongMemEval 看 R@5 与 QA，LoCoMo 看 temporal/multi-hop 证据覆盖。

## 5. Beyond RAG for Agent Memory: Retrieval by Decoupling and Aggregation

- **资料**：类型：参数/模型内记忆；论文：[论文/页面](https://arxiv.org/abs/2602.02007)；代码：[GitHub](https://github.com/HU-xiaobai/xMemory)

- **动机**：xMemory 认为 agent memory 是有界、连贯、强相关的交互流，不像普通 RAG 的异质文档库。flat top-k 会把相似但不关键的片段一起召回；summary hierarchy 又会抹掉小差异。LoCoMo 中“Gina 何时丢掉 DoorDash 工作”这类题正需要区分相似后续事件。
- **方法 - Build 侧**：它遵循 decoupling before aggregation：先把 raw messages 切成局部 segments，再从每个 segment 抽 memory components，表示事实、约束、属性、关系或状态更新；component 保留 source segment 指针。随后把相关 components 聚成 groups，用 sparsity-semantic faithfulness objective 控制组内大小和语义一致性。新 component 到来时可 attach、新建 group，并周期性 split/merge。
- **方法 - Query 侧**：检索自顶向下。先用 query 选 group 和 component 的 compact backbone，并利用 kNN 邻接做覆盖与去冗余；再从 selected components 回到 segments/messages。只有当候选原文能降低 reader uncertainty 时才展开，避免把冗余历史重新塞回上下文。
- **优点**：非常贴合 LoCoMo/LongMemEval 的多证据 QA；高层组织可省 token，source 指针又能回查原文；对 list/count、多跳和时间细节比 flat RAG 更稳。
- **缺点/风险**：component 抽取错误会在高层路由中放大；uncertainty 估计依赖可用 logits 或 proxy；构建成本高于 raw-turn RAG。
- **可借鉴点与实验**：实现 `group -> component -> raw turn` 两阶段扩展。Ablation：flat RAG、component-only、+group Stage I、+uncertainty Stage II、+dynamic split/merge。分 LongMemEval MR/TR/KU 和 LoCoMo multi-hop/temporal 测 token、coverage、答案。

## 6. Buffer of Thoughts: Thought-Augmented Reasoning with Large Language Models

- **资料**：类型：产品/工程系统；论文：[论文/页面](https://arxiv.org/abs/2406.04271)；代码：[GitHub](https://github.com/YangLing0818/buffer-of-thought-llm)

- **动机**：Buffer of Thoughts 解决的是复杂推理每次都从零设计 CoT/ToT 结构的问题。它把历史解题过程蒸馏为 high-level thought-template，形成 meta-buffer。对 Agent-Mem，它不是事实记忆，而是“如何读证据、如何分解问题”的程序性推理记忆。
- **方法 - Build 侧**：每道题先由 problem distiller 抽关键变量、约束和抽象任务类型。解题完成后，buffer-manager 用三步蒸馏：核心任务总结、通用解法步骤、可复用 answering template；模板存入 meta-buffer，并带 description/category。若新模板与已有模板相似，则更新或跳过，控制冗余。
- **方法 - Query 侧**：新问题先 distill，再用 embedding 在模板描述上检索最相似 thought-template；超过阈值则实例化模板，低于阈值则使用粗粒度默认模板并在解题后扩展 buffer。用于 LongMemEval/LoCoMo 时，模板应指导 temporal、multi-hop、abstention、count/list 等读证据流程。
- **优点**：可把多轮试错沉淀成低成本单次推理结构；buffer-manager 让模板随任务增长；小模型也能受益。
- **缺点/风险**：模板质量依赖初始模型；创造性或开放式对话收益小；若模板里包含具体人物、日期、答案，会直接污染 benchmark。
- **可借鉴点与实验**：构建 entity-free `reasoning_templates`，例如“KU 题先找旧事实和最新覆盖事实”。Ablation：无模板、人工模板、BoT learned、去 problem distiller、去 buffer-manager。看 LongMemEval TR/KU/ABS 和 LoCoMo multi-hop 的收益。

## 7. ChatHaruhi: Reviving Anime Character in Reality via Large Language Model

- **资料**：类型：个性化/对话长期记忆；论文：[论文/页面](https://arxiv.org/abs/2308.09597)；代码：[GitHub](https://github.com/LC1332/Chat-Haruhi-Suzumiya)

- **动机**：ChatHaruhi 关注角色扮演：只靠“请扮演某角色”的 prompt，模型要么不知道作品细节，要么风格被通用助手习惯覆盖。它把角色背景、经典剧情和对话风格组织成可检索 memory，使模型在新问题上仍能贴近角色。
- **方法 - Build 侧**：系统从小说、电视剧、动漫脚本中抽取角色相关 story/dialogue，形成每个角色的 memory bank。片段不强制只保留 QA，而是保留叙事、动作和多轮上下文，以维持剧情信息。对数据少的角色，用 LLM 基于原始脚本模拟新对话，构建 ChatHaruhi-54K；也可用这些数据微调本地模型。
- **方法 - Query 侧**：给定角色 R 和用户问题 q，系统用 embedding 从角色故事库 D 中检索 M 个相关经典片段，加上改进的 system prompt、角色补充说明和最近对话历史 H，形成 `sR-D-H-q` 提示。对 LongMemEval/LoCoMo，这相当于 persona/profile + episodic quote retrieval。
- **优点**：保留原始说话风格和情境，比裸 prompt 更稳定；检索片段让模型知道角色世界观；短期 history 保持连续性。
- **缺点/风险**：目标是角色一致性，不是严格证据 QA；生成式数据可能放大风格偏差；embedding 检索会漏掉时间/反事实；persona 可能覆盖真实证据。
- **可借鉴点与实验**：借鉴 profile、episodic quote、recent dialogue 三层，但在 Agent-Mem 中 profile 只作为候选，不得替代 raw evidence。Ablation：prompt-only、profile-only、retrieved episodes、episodes+recent history；测 LoCoMo persona consistency 与 LongMemEval preference/ABS。

## 8. Evaluating Very Long-Term Conversational Memory of LLM Agents

- **资料**：类型：图记忆/结构化记忆；论文：[论文/页面](https://arxiv.org/abs/2402.17753)；代码：[GitHub](https://github.com/snap-research/LoCoMo)

- **动机**：LoCoMo 是长时对话记忆评测，不是单一 memory 方法。它指出早期多会话数据太短，无法检验几个月跨度、多人设、因果事件、图像分享和长程一致性。Agent-Mem 必须把它当核心压力测试：召回旧事实只是第一步，还要理解时间、因果、说话人和不可答问题。
- **方法 - Build 侧**：数据生成采用 machine-human pipeline。每个虚拟 agent 先有 persona，再生成带日期和因果边的 temporal event graph；对话由 generative agent 架构驱动，含短期摘要、长期 observation memory、reflect/respond，以及 image sharing/response。随后人工编辑长程不一致、无关图片和 event grounding。最终形成 50 条对话，平均约 300 turns、9K tokens、19.3 sessions，并构建 7,512 个 QA。
- **方法 - Query 侧**：评测包括 QA、event summarization、多模态对话生成。QA 分 single-hop、multi-hop、temporal、open-domain、adversarial；基线包含短上下文、长上下文和 RAG，并发现 observation/assertion 数据库对 RAG 有帮助，但长上下文和 RAG 仍远低于人类，尤其 temporal 和 adversarial。
- **优点**：问题类型直接对应长期记忆失败；有事件图和人工修订，便于分析时间/因果；对多跳和说话人归属比普通检索更苛刻。
- **缺点/风险**：数据主要由 LLM 合成再人工修订，真实用户分布有限；平均 9K tokens 比 LongMemEval-S/M 短很多；多模态图像多由 caption 代理，不能完全代表真实视觉记忆。
- **可借鉴点与实验**：用 LoCoMo 做 retrieval/evidence 诊断集：raw full-context、flat RAG、speaker-aware RAG、observation DB、event-graph expansion、temporal rerank。与 LongMemEval 搭配：LoCoMo 看人设/事件图，多跳时间；LongMemEval 看超长用户-助手、更新和拒答。

## 9. EverOS (part of EverMind)

- **资料**：类型：产品/工程系统；论文：[论文/页面](https://evermind-ai.com/)；代码：[GitHub](https://github.com/EverMind-AI/EverOS)

- **动机**：EverOS 的主张是把长期记忆从某个 agent 产品里解耦出来，做成跨 Claude Code、Codex、OpenClaw、Hermes 等工具都能复用的一层本地运行时。它不是先假设“向量库就是记忆”，而是把 context、decision、file、trajectory 都视为可携带资产。对 LongMemEval/LoCoMo 这类长对话评测，关键启发是：记忆系统必须能审计“答案来自哪个原始交互”，否则高分很难区分是可靠召回、压缩猜测还是污染。
- **方法 - Build 侧**：官方 README 明确采用 local-first、Markdown as source of truth：用户轨有 `user.md`、`episodes/`、`.atomic_facts/`、`.foresights/`，agent 轨有 `agent.md`、`.cases/`、`skills/`。SQLite 记录状态、队列和审计，LanceDB 承载向量、BM25 和 scalar filter，所有索引都由 Markdown 派生，可重建。它还把 conversations、agent trajectories、files、多模态材料纳入抽取，并按 `user_id / agent_id / app_id / project_id / session_id` 做正交 scope。
- **方法 - Query 侧**：查询不是单一 top-k dense retrieval，而是 BM25、cosine ANN、scalar filters 的 hybrid retrieval，并可按多维 scope 缩小候选；必要时也能直接读取 Markdown 原文。对 LongMemEval 的 knowledge-update、abstention 和 LoCoMo 的人物/会话题，这种设计可以先由 scope 确定人、项目、会话，再用 episodes/atomic facts 召回，最后回读源文件确认。
- **优点**：最大优点是可检查、可 diff、可版本化，适合研究系统复盘召回错误；user memory 和 agent memory 分轨，能避免把 procedural skill 与用户事实混在一起；本地 SQLite/LanceDB 降低了实验复现对外部服务的依赖。Markdown 源文件还能让人工快速定位抽取错误。
- **缺点/风险**：EverOS 本身不是针对 LongMemEval/LoCoMo 报告 SOTA 的算法论文，不能把工程完整性等同于 QA 准确率。`.foresights/` 这类预测性记忆若进入事实回答，会把推测写成证据；Markdown schema 如果放松，也会变成难检索的文本堆。多模态能力对文本 benchmark 不是核心收益。
- **可借鉴点与实验**：Agent-Mem 可复用“原始 episode + 派生 atomic fact + 可重建索引”的布局。建议做 `raw-turn only`、`raw+episode markdown`、`raw+atomic facts`、`raw+facts+scope filters`、`关闭 foresight` 五组消融；指标除 answer accuracy 外，必须报 evidence coverage、wrong-speaker rate、LongMemEval abstention false-positive 和 LoCoMo temporal/person confusion。

## 10. Everything is Context: Agentic File System Abstraction for Context Engineering

- **资料**：类型：产品/工程系统；论文：[论文/页面](https://arxiv.org/abs/2512.05470)；代码：[GitHub](https://github.com/AIGNE-io/aigne-framework)

- **动机**：这篇论文把 memory、tools、files、human notes、scratchpad 都统一称作 context artefacts，认为问题不只是“召回什么”，还包括谁有权读取、为何选中、如何压缩、如何刷新、如何验证。它借 Unix “everything is a file” 提出 Agentic File System，用文件系统的 namespace、metadata、access control、transaction log 治理上下文生命周期。
- **方法 - Build 侧**：Build 侧把 History、Memory、Scratchpad 分层：History 是不可变全量事实源，记录输入、输出、中间推理、timestamp、origin、model version；Memory 是从 history 变换出的 episodic/fact/procedural/user 等结构化索引视图；Scratchpad 是任务内临时工作区，结束后经验证才进入 memory 或 history。每个 artefact 都有 lineage、version、access policy。
- **方法 - Query 侧**：Context Constructor 从 `/context/history/`、`/context/memory/`、tools 和 human input 中选择、排序、压缩上下文，并生成 ContextManifest，记录 selected/excluded items、原因、token 预算和 provenance。Context Updater 支持一次性 snapshot、推理中 streaming、交互时 adaptive refresh。Context Evaluator 再检查 hallucination、contradiction、context drift，并把验证后的输出写回。
- **优点**：它非常适合 LongMemEval/LoCoMo 的实验诊断。manifest 能把错误拆成 retrieval miss、compression loss、context selection error、answer hallucination；History 不可变也能防止 summary 覆盖旧事实。对 multi-session temporal 题，lineage 和 version 比单纯 embedding 更有价值。
- **缺点/风险**：它是上下文治理架构，不是新的排序或图检索算法；Constructor 的压缩仍可能删掉低显著但 gold 的事实。论文示例是 AIGNE memory agent 和 GitHub MCP assistant，并没有直接给 LongMemEval/LoCoMo 分数。因此迁移时要把它当实验框架，而不是直接替代 recall 模型。
- **可借鉴点与实验**：为每个 Agent-Mem query 强制产出 `ContextManifest`：候选源、RRF/graph/temporal 分、被丢弃证据、压缩版本、最终 evidence table。消融 `无 manifest`、`history 可变摘要`、`只 snapshot`、`adaptive refresh`、`Evaluator 关闭`；在 LongMemEval 知识更新/拒答和 LoCoMo temporal/open-domain 上统计错误归因是否更稳定。

## 11. From RAG to Memory: Non-Parametric Continual Learning for Large Language Models

- **资料**：类型：参数/模型内记忆；论文：[论文/页面](https://arxiv.org/abs/2502.14802)；代码：[GitHub](https://github.com/OSU-NLP-Group/HippoRAG)

- **动机**：HippoRAG2 继承 HippoRAG 的“非参数长期记忆”路线，但指出原版 entity-centric 的索引和查询会丢上下文：query 只落到实体节点，无法表达关系和 passage 语境。它要让 RAG 更像持续学习的外部记忆，在不改 LLM 参数的情况下，把新知识组织成可关联的 phrase-triple-passage 图。
- **方法 - Build 侧**：离线阶段用 LLM OpenIE 从 passage 中抽取 schema-less triples，把 subject/object 作为 phrase nodes，relation 作为边；再用 embedding 做 synonym detection，连接相似 phrase。HippoRAG2 的增量是加入 passage nodes，并用 `contains` context edge 把 passage 与其中 phrase 连接，形成 dense-sparse integration：phrase 保持概念稀疏性，passage 保存上下文。
- **方法 - Query 侧**：在线阶段不是 NER-to-node，而是 query-to-triple：用 embedding 找 top triples，再由 LLM recognition memory 过滤不相关 triples。过滤后的 triples 给 phrase seeds，所有 passage nodes 也可作为 broader seeds；PPR 的 reset probability 由 phrase ranking score 和 passage embedding similarity 决定，并用 passage-node weight 平衡。若 triple 为空，则回退 dense retrieval。
- **优点**：它在 MuSiQue、2Wiki、HotpotQA、LV-Eval、NarrativeQA 等 RAG benchmark 上显著提升 recall/F1，且 ablation 显示 query-to-triple、passage node、triple filter、reset weight 都有贡献。对 LoCoMo multi-hop，可借它从一个人物/事件扩散到相关会话；对 LongMemEval multi-session，也能作为跨 session candidate expansion。
- **缺点/风险**：原实验不是 LongMemEval/LoCoMo，且语料偏百科/文档。对话中的代词、省略、说话人、时间有效期和“后来改口”比百科 triples 难得多；OpenIE 错边会被 PPR 放大。recognition filter 用 LLM，会增加成本并可能把少见但关键事实过滤掉。
- **可借鉴点与实验**：只把 HippoRAG2 图作为召回扩展，最终答案必须引用 raw turn。消融 `dense only`、`NER-to-node`、`query-to-triple`、`w/o filter`、`w/o passage node`、`PPR passage weight=0/0.05/0.3`，并给 graph seeds 加 speaker/time filters；分别看 LoCoMo multi-hop/temporal、LongMemEval multi-session/knowledge-update 的 recall@k 与 answer accuracy。

## 12. gbrain

- **资料**：类型：产品/工程系统；论文：[论文/页面](https://github.com/garrytan/gbrain)；代码：[GitHub](https://github.com/garrytan/gbrain)

- **动机**：gbrain 是工程型“agent brain”，强调每条消息先触发 signal detector，再 search、respond、write、auto-link、sync。它的启发不是某个单一算法，而是把个人/团队知识库做成 schema-aware 的 Markdown 图谱，让 agent 在调用外部 API 前先查自己的 brain。
- **方法 - Build 侧**：官方 README 描述 signal detector 会在每条消息上捕捉 ideas、entity mentions、time-sensitive todos、names、links；写入 page 和 timeline 后，auto-link 用 `[[wiki/people/bob]]` 这类模式做无 LLM 的 typed edges/backlinks，新实体生成 stub page，图随写入增长。cron enrichment 后台做 dedup、citation fix、salience scoring、contradiction finding、next-day prep。schema pack 可由 `detect/suggest/review-candidates` 从真实文件系统聚类并经 LLM 建议，再由人工 gate 启用。
- **方法 - Query 侧**：gbrain 查询侧是 hybrid search：pgvector HNSW 向量、BM25 keyword、RRF、source-tier boost、intent-aware query rewriting；还提供 conservative/balanced/tokenmax 三种 search mode。per-query graph signals 会做 adjacency boost、cross-source boost、session demote；每个结果带 evidence tag 和 create_safety，`--explain` 可显示 base score 与每个 boost。
- **优点**：schema pack 对 LongMemEval/LoCoMo 很有迁移价值，因为 person、event、preference、commitment、relationship、time_state 本就应有不同抽取规则和路径。Markdown/source-tier 让 evidence 可人工校验；graph signals 可补 dense retrieval 在多跳关系上的短板。
- **缺点/风险**：gbrain 没有论文级 LongMemEval/LoCoMo 结果，默认面向 agent/团队知识库，不是多说话人长期对话 QA。schema 过强会漏开放事实，过松又退回普通 RAG；salience 与 cron enrichment 若用于删改用户事实，会伤害低频 gold evidence。cross-source boost 对 benchmark 还可能引入外部污染。
- **可借鉴点与实验**：为 Agent-Mem 做对话 schema pack，并要求每个派生 page/fact 都含 `speaker, subject, time_span, source_turn_ids, confidence`。实验比较 `通用 schema`、`对话 schema`、`schema+graph boosts`、`schema+session demote`；在 LoCoMo 人物混淆和 LongMemEval knowledge-update 上测 extraction coverage、wrong-attribution rate、answer accuracy。

## 13. General Agentic Memory Via Deep Research

- **资料**：类型：文本长期记忆/经验压缩；论文：[论文/页面](https://arxiv.org/abs/2511.18423)；代码：[GitHub1](https://github.com/VectorSpaceLab/general-agentic-memory/)；[GitHub2](https://github.com/VectorSpaceLab/general-agentic-memory)

- **动机**：GAM 反对传统 memory 的 AOT 压缩：提前把完整历史压成轻量 memory 必然丢细节，遇到 ad-hoc request 时无法恢复。它采用 JIT compilation 思路，离线只做轻 memo 和完整 page-store，真正的高价值上下文在 query-time 由 Researcher 深度检索、整合、反思生成。
- **方法 - Build 侧**：历史被切成 session。Memorizer 对每个新 session 做两件事：一是生成 memo，作为对整体轨迹有用的轻量线索；二是生成 header，把前文关键上下文装饰到该 session，形成 `{header, content}` page 并写入 page-store。论文实现中将输入切成 2048-token pages，用 BGE-M3 做 dense retriever，同时保留 BM25 和 page-id 直接浏览工具。
- **方法 - Query 侧**：Researcher 收到请求后，根据 memo 分析 information needs，规划 search actions；可并行调用 embedding search、BM25 keyword search、page-id retrieval。拿到 pages 后生成 integration result，再 reflect 判断信息是否完整；若不完整，产生新的 request 继续检索，默认最大 reflection depth 为 3、每轮最多 5 页。最后可返回 integration、相关 page 或 source extraction。
- **优点**：它直接评了 LoCoMo，并报告 single-hop、multi-hop、temporal、open-domain 均优于 Long-LLM、RAG、A-Mem、Mem0、MemoryOS、LightMem；在 GPT-4o-mini 下 LoCoMo F1 分别约为 57.75/42.29/59.45/33.30。它还在 HotpotQA、RULER、NarrativeQA 上说明 JIT 搜索对多跳和长上下文更稳。
- **缺点/风险**：Query-time latency 明显高于普通 top-k；Researcher 可能被 memo 先验带偏，且 integration-only 输出可能遮蔽具体证据。GAM 的 LoCoMo 是对话 QA，但没有覆盖 LongMemEval 的 knowledge-update/abstention 细分；若 page-store 不保留 turn-level speaker/time，深度研究也会找错证据。
- **可借鉴点与实验**：Agent-Mem 可复刻 `memo as navigation, raw pages as evidence`。消融 `无 memo`、`memo+top-k`、`memo+iterative researcher`、`BM25 only`、`dense only`、`page-id only`、`depth=1/3/5`、`pages=3/5/20`、`integration only vs integration+source spans`；在 LongMemEval-S 和 LoCoMo 同时报 accuracy、source coverage、latency、token cost。

## 14. Generative Agents: Interactive Simulacra of Human Behavior

- **资料**：类型：经验学习/自进化记忆；论文：[论文/页面](https://arxiv.org/abs/2304.03442)；代码：[GitHub](https://github.com/joonspk-research/generative_agents)

- **动机**：Generative Agents 试图让 25 个 sandbox agent 产生长期一致、可相信的行为，而不是一次性回复。它提出 memory stream、importance、reflection、planning 的组合，让 agent 能从连续观察中形成高层认识，并把这些认识反馈到后续行为。对长期记忆研究，它是“观察流如何沉淀为可用经验”的经典起点。
- **方法 - Build 侧**：所有 observation、conversation、plan、reflection 都作为自然语言 memory object 写入 stream，并附 created timestamp、last accessed timestamp、importance。importance 由 LLM 按 1-10 评分；最新事件 importance 累计超过阈值 150 时触发 reflection。Reflection 先基于最近 100 条记忆生成 3 个高层问题，再用这些问题召回相关记忆，生成带证据引用的 insight，并作为新 memory 写回。Plan 也会从日计划递归拆到 5-15 分钟动作。
- **方法 - Query 侧**：行为生成时，系统按 relevance、recency、importance 融合排序。Relevance 用 embedding cosine；recency 用按 sandbox hours 衰减的指数函数，论文实现 decay factor 为 0.995；importance 取创建时评分，三者 min-max 后等权相加。召回结果用于反应、对话和重新规划。
- **优点**：它给出了非常实用的 memory item 字段和 rerank baseline，reflection 机制也能把多次低层观察合成为高层 profile/relationship。控制实验中去掉 observation、planning、reflection 都会降低 believability；端到端模拟还展示了 party invitation、mayor candidacy 等信息扩散和关系形成。
- **缺点/风险**：原任务评价 believable behavior，不是 LongMemEval/LoCoMo 的精确事实 QA。importance/recency 会压低旧但关键的小事实；reflection 可能合理化、补全或 embellish 未说过内容，论文也观察到 memory retrieval failure 与 embellishment。对 benchmark，reflection 不能直接当最终证据。
- **可借鉴点与实验**：Agent-Mem 可借 `created_at/last_accessed/importance` 作为 rerank feature，但禁止基于 importance 删除事实。消融 `relevance only`、`+recency`、`+importance`、`+reflection hints`、`reflection 必须回 raw turn`；重点看 LongMemEval temporal/knowledge-update 是否被 recency 误伤，以及 LoCoMo multi-hop 中 reflection 是否提高 recall 还是增加 hallucination。

## 15. Hello Again! LLM-powered Personalized Agent for Long-term Dialogue

- **资料**：类型：个性化/对话长期记忆；论文：[论文/页面](https://arxiv.org/abs/2406.05925)；代码：[GitHub](https://github.com/leolee99/LD-Agent)

- **动机**：LD-Agent 针对长期多会话开放域对话，认为仅保存历史事件或仅维护 persona 都不够；系统需要同时记住跨会话事件、当前会话上下文、用户 persona 和 agent persona，才能生成连续且个性化的回应。它与 LongMemEval/LoCoMo 的关系是结构高度相关，但原目标是 response generation 而非证据 QA。
- **方法 - Build 侧**：事件模块分长短期记忆。长期 memory bank `M_L` 存历史 session 的发生时间和 event summary，经 text encoder 编码；短期 cache `M_S` 存当前 session 的 timestamped utterances。若新 utterance 与上次记录间隔超过阈值 `beta=600s`，就触发 summarizer 把短期缓存写成长记忆并清空。Persona 模块为 user 与 agent 分别维护 `P_u/P_a`，可用 LoRA instruction-tuned extractor 或 LLM CoT extractor 从 utterance 中抽 trait，无 trait 输出 `No Trait`。
- **方法 - Query 侧**：检索历史事件时不只看 event summary 与当前 query 的 semantic similarity，还抽取名词 topic library，计算 query/key 的 topic overlap，并乘以时间衰减 `lambda_t=e^{-t/tau}`；语义分低于 `gamma=0.5` 返回 no relevant memory。最终生成器输入新 utterance、retrieved memory、短期上下文、user persona、agent persona。
- **优点**：模块边界清楚，适合把 LongMemEval 的 user facts、assistant facts、preference 和多会话历史分槽管理；topic overlap 对口语对话中“同一话题但表达不同”的召回有帮助。论文在 MSC/CC 多会话数据集上显示 LD-Agent 对 ChatGPT、ChatGLM、BlenderBot 等均有提升，ablation 中 event memory 通常贡献最大。
- **缺点/风险**：原评测是 BLEU/ROUGE/METEOR 与人工 coherence/fluency/engagingness，不是 LongMemEval/LoCoMo answer correctness。Event summary 可能压掉限定条件、否定、说话人；persona 抽取可能把一次性状态写成长期属性。时间衰减也可能伤害很早但仍有效的事实。
- **可借鉴点与实验**：Agent-Mem 可采用四槽 prompt：`recent context / event evidence / user profile / assistant profile`，但 answer 前必须展开 raw evidence。消融 `recent only`、`+event`、`+user persona`、`+assistant persona`、`topic overlap off`、`time decay off`、`summary答 vs raw展开答`；在 LongMemEval preference/assistant-fact 和 LoCoMo single-hop/temporal 上分别看收益。

## 16. Hindsight is 20/20: Building Agent Memory that Retains, Recalls, and Reflects

- **资料**：类型：产品/工程系统；论文：[论文/页面](https://arxiv.org/abs/2512.12818)；代码：[GitHub](https://github.com/vectorize-io/hindsight)

- **动机**：Hindsight 的核心是 epistemic separation：长期记忆不应把事实、经验、观察摘要和主观观点混在同一个向量池。许多长记忆错误来自把模型推断当用户事实、把 agent belief 当世界事实、或把 entity summary 当可直接引用证据。它用 retain/recall/reflect 三操作把事实召回和偏好化推理分开。
- **方法 - Build 侧**：TEMPR retain 把对话转为 narrative facts，每个 memory unit 含自然语言、embedding、temporal metadata `tau_s/tau_e/tau_m`、type、confidence 和辅助元数据。四个 network 分别是 world facts、agent experiences、opinions/beliefs、observations/entity summaries。系统做 entity recognition/resolution，并构造 temporal、semantic、entity、causal 四类边；CARA 维护 opinion network，遇到新证据时按支持/矛盾调整 confidence。
- **方法 - Query 侧**：Recall 不是固定 top-k，而是在 token budget 下并行跑 semantic vector、BM25 keyword、graph spreading activation、temporal retrieval。四路候选用 Reciprocal Rank Fusion 融合，再由 cross-encoder rerank，最后按 token budget 贪心选入。Reflect 阶段读取相关 facts 与行为 profile；benchmark 中 profile 设为中性、低 bias strength，以避免偏好层影响事实 QA。
- **优点**：它直接报告 LongMemEval-S 与 LoCoMo。LongMemEval 中 OSS-20B full-context 为 39.0，Hindsight OSS-20B 达 83.6，OSS-120B/Gemini-3 版本到 89.0/91.4；LoCoMo 中 Hindsight OSS-20B/OSS-120B/Gemini-3 为 83.18/85.67/89.61。尤其 multi-session、temporal、preference 等类别受益明显。
- **缺点/风险**：部分 baseline 来自外部报告或公开 leaderboard，复现公平性需要谨慎；技术报告没有系统展开组件级 ablation。Narrative extraction 仍可能丢掉小事实；opinion/observation 若在事实题中被过度信任，会造成推断污染。四路检索和 rerank 的实现成本也高于简单 RAG。
- **可借鉴点与实验**：Agent-Mem 应给每条派生记忆标 `epistemic_type=stated/inferred/observed/summarized/opinion`，answer 默认只用 stated/raw evidence，inferred 只做 hint。消融 `semantic only`、`+BM25`、`+graph`、`+temporal`、`RRF off`、`cross-encoder off`、`opinion excluded/included`；重点测 LongMemEval abstention/knowledge-update 和 LoCoMo open-domain 中推断污染是否下降。

## 17. HippoRAG: Neurobiologically Inspired Long-Term Memory for Large Language Models

- **资料**：类型：参数/模型内记忆；论文：[论文/页面](https://arxiv.org/abs/2405.14831)；代码：[GitHub](https://github.com/OSU-NLP-Group/HippoRAG)

- **动机**：HippoRAG 借鉴 hippocampal indexing theory，认为人类可由局部 cue 激活关联网络完成 pattern completion，而标准 RAG 把 passage 孤立编码，难以跨 passage 整合新知识。它希望用 LLM 抽取 KG，再用 Personalized PageRank 在图上单步完成多跳候选召回。
- **方法 - Build 侧**：离线索引中，LLM 先做 NER，再在 named entities 辅助下 OpenIE，抽取 noun phrase nodes 和 relation edges，构成 schema-less KG。检索 encoder 再为相似但非完全一致的 phrase 加 synonym edges，阈值如 0.8。系统维护 node-to-passage 矩阵，记录每个 node 来自哪些 passage；还定义 node specificity，近似 IDF，用于提升更特异的 query nodes。
- **方法 - Query 侧**：在线检索先用 LLM 从 query 抽 named entities，再用 encoder 映射到 KG query nodes。PPR 的 personalized distribution 在这些 query nodes 上初始化，并把概率扩散到相关子图；PPR 后的 node probability 乘 node-to-passage 矩阵得到 passage scores，返回 top passages 给 reader。它本质上把多跳检索压成一次图搜索。
- **优点**：在 MuSiQue、2WikiMultiHopQA 上较 BM25、Contriever、ColBERTv2、RAPTOR、Propositionizer 明显提高 recall，且单步 HippoRAG 在 QA 上可接近或超过 IRCoT，并比 iterative retrieval 便宜和更快。Ablation 显示 PPR、node specificity、synonym edges、OpenIE 质量都会影响结果。
- **缺点/风险**：原实验不是 LongMemEval/LoCoMo，而是多跳文档 QA；方法偏实体中心，对多说话人、代词、省略、偏好变化和时间有效期没有原生建模。错误分析也指出 NER/OpenIE/PPR 都会出错。对话中如果实体抽错或把旧状态连到新状态，PPR 会把噪声扩散。
- **可借鉴点与实验**：Agent-Mem 可把 HippoRAG 作为 `entity graph recall expansion`，但每个 node 必须带 speaker/time/session/source_turn。消融 `dense only`、`entity one-hop`、`PPR`、`PPR+node specificity`、`PPR+synonym`、`PPR+speaker/time filters`；在 LoCoMo multi-hop 和 LongMemEval multi-session 上分别报告 all-support recall、wrong-time evidence 和最终 accuracy。

## 18. Honcho

- **资料**：类型：产品/工程系统；论文：[论文/页面](https://honcho.dev/)；代码：[GitHub](https://github.com/plastic-labs/honcho)

- **动机**：Honcho 是生产型 stateful agent memory，核心哲学是 peer-centric：记忆围绕 Workspace 下的 Peer、Session、Message 和 perspective 组织，而不是围绕一个全局用户表。它特别适合多用户、多 agent、NPC、群聊和长期关系场景，因此对 LoCoMo 的多人物对话和 LongMemEval 的 user/assistant 区分有直接工程启发。
- **方法 - Build 侧**：官方文档里的 primitives 是 Workspaces、Peers、Sessions、Messages。Workspace 隔离不同 app/use case；Peer 可代表人类、AI agent、群体或实体；Session 是 peers 之间的一组交互；Message 是带 source peer 标签的原子数据。内部 collections 以 `(observer, observed)` peer pair 为 key，后台异步从消息中推理 representation、session summary、Conclusions、Peer Cards 等。
- **方法 - Query 侧**：查询可用 `peer.chat()` 询问 Honcho 对某个 peer 的理解，也可用 `session.context(summary=True, tokens=...)` 生成 prompt-ready context，再转 OpenAI/Anthropic 消息格式。检索支持 peer/session/global 层面的 hybrid search，官网还把 reasoning 分成 minimal/low/medium/high/max：从单次 semantic lookup 到多轮、定量、全历史 deep research，并允许 token budget 和 peer scoping 控制上下文。
- **优点**：它最有价值的是 perspective 建模：A 对 B 的观察、B 自述、assistant 对用户的推断不应混为同一事实。LoCoMo 中人物多、关系多，这能降低“把某人的观点当成另一个人的事实”的错误；LongMemEval 中 assistant/user facts 分离也能受益。异步 dreaming 可把重型分析移出在线路径。
- **缺点/风险**：Conclusions 是后台推理结果，不等于原始证据；异步处理可能在查询时尚未完成。官网强调关系、情绪、行为画像等 production use cases，并非给 LongMemEval/LoCoMo 的可复现实验。若 Peer Cards 过度总结，低频事实和时间限定会被覆盖。
- **可借鉴点与实验**：Agent-Mem 应把每条 fact/profile 写成 `source_peer, subject_peer, observer_peer, perspective_scope, source_turn_ids`。消融 `global memory`、`peer-scoped`、`observer/observed scoped`、`conclusions excluded/included`、`async summaries off/on`；重点统计 LoCoMo 人物混淆、观点归属错误，以及 LongMemEval single-session-user vs single-session-assistant 的互相污染。

## 19. Human-inspired Episodic Memory for Infinite Context LLMs

- **资料**：类型：参数/模型内记忆；论文：[论文/页面](https://arxiv.org/abs/2407.09450)；代码：[GitHub](https://github.com/em-llm/EM-LLM-model)

- **动机**：EM-LLM 解决的是无限长上下文中的事件化记忆，而不是传统外部文档 RAG。它认为固定窗口或固定 chunk 会切裂语义事件；人类会在 surprise/预测误差处形成事件边界，并在回忆时同时利用相似性和时间邻近性。对 Agent-Mem，最可迁移的是 episode segmentation 与邻接扩展，而不是 KV-cache 工程本身。
- **方法 - Build 侧**：模型把过长上下文分为 initial tokens、local context 和 evicted tokens。Evicted tokens 不按固定长度直接存，而是组织成 episodic events。初始边界由 Bayesian surprise 给出：当前 token 的负 log likelihood 超过移动窗口均值和方差形成的阈值即为候选边界；再用 attention key similarity 构图，通过 modularity 或 conductance 优化边界，使 event 内相似高、event 间相似低。该过程无需 fine-tuning。
- **方法 - Query 侧**：生成新 token 时，每层独立从 episodic memory 检索事件。第一阶段用 k-NN 按当前 query 与 event representative tokens 的 dot product 找 `k_s` 个相似 events，形成 similarity buffer；第二阶段把这些 events 在原序列中的邻居加入 queue，形成 contiguity buffer，通常取相邻 ±1。最终 context 包含 initial tokens、contiguity buffer、similarity buffer、local context。
- **优点**：EM-LLM 在 LongBench 和 Infinity-Bench 上跨多个 base LLM 超过若干长上下文基线，并显示 retrieval/QA 类任务收益大；还与 RAG、full-context 做比较，报告在 LongBench 上优于 NV-Embed-v2 RAG 和 full-context，并可在 passkey retrieval 上扩到千万 token。消融显示 surprise、boundary refinement、contiguity buffer 互补，segmentation 与人类事件边界有相关性。
- **缺点/风险**：它没有直接评 LongMemEval/LoCoMo，且 KV-cache 事件不天然可读、可引用、可审计。对于需要回答“用户具体哪天说过什么”的 benchmark，仅靠隐藏 KV memory 很难给 source spans。边界切错会把问题和答案拆开；contiguity buffer 也会引入邻近噪声，尤其在主题切换频繁的对话中。
- **可借鉴点与实验**：Agent-Mem 可离线用 surprise/topic-shift 生成 episode segments，并保留 raw turns；检索命中某 event 后扩展相邻 event，而不是固定 chunk。消融 `fixed turn chunk`、`session chunk`、`topic segment`、`surprise segment`、`surprise+refinement`、`adjacent ±0/±1/±2`、`similarity buffer only vs +contiguity`；在 LoCoMo temporal/multi-hop 和 LongMemEval multi-session 上测 evidence coverage、context tokens、边界错误率。

## 20. HyperMem: Hypergraph Memory for Long-Term Conversations

- **资料**：类型：参数/模型内记忆；论文：[论文/页面](https://arxiv.org/abs/2604.08256)；代码：[GitHub](https://github.com/EverMind-AI/EverOS/tree/main/methods/HyperMem)

- **动机**：HyperMem 针对长期对话中“同一主题跨月分散、多事实共同指向一个答案”的问题。普通 chunk RAG 只按相似片段取 top-k，GraphRAG 多数仍是二元边，容易把运动、工作、人物关系等高阶关联拆散；LoCoMo 的 multi-hop、temporal、open-domain 正好暴露这种碎片化召回。论文直接在 LoCoMo 上报告 92.73% LLM-as-a-judge accuracy，但未把 LongMemEval 作为主实验。
- **方法 - Build 侧**：构建三层超图：Topic 节点表示长期主题，Episode 节点表示时间连续且语义完整的子对话，Fact 节点表示可回答查询的原子事实。写入时先用 LLM 做 streaming episode boundary detection，依据语义完整性、时间间隔、话题转移信号决定是否切段；再把新 episode 和历史相似 episode 比较，执行 topic initialization / creation / update；最后在 topic 上下文中抽取 facts，并把事实锚定到原 episode。Episode hyperedge 连接同主题的多个 episode，Fact hyperedge 连接同 episode 的多个事实，并带重要性权重。
- **方法 - Query 侧**：离线为 topic、episode、fact 都建 BM25 与 dense index，并做 hypergraph embedding propagation：用超边内节点权重聚合出 hyperedge embedding，再回传到节点，使跨时间但同主题的节点向量更接近。在线检索是 coarse-to-fine：query 先在 topic 层 BM25+dense，用 RRF 融合并 rerank，取 top-k topic；展开到其 episode 后重复打分；再展开到 fact，选 top facts，并可附 episode summary 作为叙事上下文。
- **优点**：Topic-Episode-Fact 明确对应“主题覆盖、事件边界、答案证据”三个粒度，能减少 top-k 只命中局部事实的问题。超边比普通边更适合 LoCoMo 中“多次提到同一长期事件”的问题。事实节点保留 source episode，可把答案回溯到原始对话。
- **缺点/风险**：Build 侧依赖多次 LLM 判断，episode 边界和 topic 合并错误会被超边放大；fact 抽取若过度摘要，会损害 LongMemEval 的 knowledge-update 和 assistant-provided information 类问题。高准确率来自 LoCoMo 专门设置，迁移到 100K+ LongMemEval-S 需要重新测构建成本和召回饱和。
- **可借鉴点与实验**：Agent-Mem 可只实现轻量版：raw_turn 不动，派生 Topic/Episode/Fact 三层索引。可落地 ablation：去掉 topic 层只做 episode+fact；去掉 hyperedge propagation；只用 BM25、只用 dense、RRF+dense+reranker 三组；fact-only vs fact+episode summary；在 LoCoMo 分 category 看 multi-hop/temporal 提升，在 LongMemEval-S 看 retrieval recall@10、answer accuracy、build token 和 query token。

## 21. IterResearch: Rethinking Long-Horizon Agents with Interaction Scaling

- **资料**：类型：上下文管理/压缩记忆；论文：[论文/页面](https://arxiv.org/abs/2511.07327)；代码：[GitHub](https://github.com/Alibaba-NLP/DeepResearch)

- **动机**：IterResearch 处理长程研究 agent 的 context suffocation 和 noise contamination。传统 ReAct/DeepResearch 把所有搜索结果、推理和工具返回线性追加到一个上下文，交互越多，模型可用推理空间越小，早期噪声还会永久污染后续决策。它没有直接面向 LoCoMo/LongMemEval，但“持续交互后只保留任务相关状态”的思想可映射到长期对话 memory 的 build/query 流程。
- **方法 - Build 侧**：核心是 MDP-inspired iterative workspace reconstruction。每一轮状态不是全历史，而是 `s_t=(question, M_t, last_action/tool_response)`；其中 `M_t` 是 evolving report，作为压缩任务记忆。模型输出结构化 decision：Think、更新后的 Report、Action。环境执行 Action 返回 tool response 后，系统丢弃旧轨迹，只用新 report 和最近反馈重建工作区。训练侧用 EAPO，把终局正确性按轨迹长度几何折扣，鼓励更短、更有效的探索，并用 trajectory 分解产生每轮训练样本。
- **方法 - Query 侧**：查询时 agent 总是读取当前问题、报告记忆和上一轮反馈，而不是检索全历史。Report 起到任务内长期记忆的作用：保留已验证发现、开放问题、排除项和下一步计划。工具包括搜索、学术检索、网页阅读、Python 等；当信息足够时 Action 可以是 final answer，否则继续探索。
- **优点**：把 memory update 放进每一步 decision，显式解决长期 agent 的上下文膨胀；workspace 大小近似 O(1)，论文展示到 2048 interactions 仍能 scaling。对 Agent-Mem 来说，它提示我们 memory 不只是事实库，也可以是“当前任务报告”。
- **缺点/风险**：Report 是有损压缩，若用于 LongMemEval/LoCoMo 直接回答，会丢失原始证据、时间细节和 assistant 提供的信息。EAPO 需要训练和 oracle reward，不能用 benchmark gold/judge 信号污染记忆策略。它适合任务轨迹，不等价于用户长期画像。
- **可借鉴点与实验**：可在 Agent-Mem 增加 query_scratch_report：每个问题迭代召回、读证、更新 evidence report。可落地 ablation：单次 retrieve-read vs 2/4/8 轮 iterative retrieval；report 中是否保留 source_turn_ids；只摘要 vs 摘要+未解决槽位；用 LongMemEval multi-session、temporal、knowledge-update 测准确率和证据覆盖；用 LoCoMo multi-hop 测迭代是否提升而 token 是否可控。

## 22. LangMem

- **资料**：类型：产品/工程系统；论文：[论文/页面](https://langchain-ai.github.io/langmem/)；代码：[GitHub](https://github.com/langchain-ai/langmem)

- **动机**：LangMem 是工程化长期记忆抽象，目标是让 LangGraph/LangChain agent 能从交互中学习、跨会话保持一致，并支持事实、经验和行为规则三类记忆。它不是 LoCoMo/LongMemEval 论文方法，但其官方文档明确覆盖 memory manager、memory tools、background manager、LangGraph store、namespace 和 semantic search，适合做可复现工程 baseline。
- **方法 - Build 侧**：LangMem 的基本写入模式是：输入 conversation 和当前 memory state，让 LLM 判断如何 expand / consolidate memory state，再返回更新结果。语义记忆分 collection 和 profile：collection 是可不断插入的事实/事件/关系文档，需处理过抽取导致 precision 下降、欠抽取导致 recall 低；profile 是单文档当前状态，适合名字、偏好、目标等 schema 化字段。Episodic memory 记录成功交互的 observation/thought/action/result；procedural memory 通过 prompt optimizer 从反馈轨迹中改写系统行为。写入既可 hot path 由 agent 主动工具调用，也可 background 反思抽取。
- **方法 - Query 侧**：Query 侧通过 `create_search_memory_tool` 或 LangGraph BaseStore 检索；支持 direct access、semantic search、metadata filtering。命名空间可按 organization/user/app/context 分层，并支持运行时模板变量。Agent 可在对话中自主决定何时搜索记忆，或由应用在 prompt 前热路径注入相关记忆。
- **优点**：接口清楚，和生产 agent runtime 贴合；semantic/profile/episodic/procedural taxonomy 方便把 LongMemEval 的用户事实、偏好、过去事件和行为风格分开存储。命名空间和 metadata 对多用户、多项目隔离非常关键。
- **缺点/风险**：默认依赖 LLM 抽取和合并，若没有 source_turn_ids、时间戳、supersede 语义，会在 LongMemEval knowledge-update 和 temporal 类问题上出错。Collection/profile 的取舍也会影响 LoCoMo：profile 利于当前状态，collection 更利于历史问答。
- **可借鉴点与实验**：可把 LangMem 当工程 baseline：collection-only、profile-only、collection+profile 三组；hot path vs background extraction；semantic search vs metadata filter+semantic；namespace 按 user/session/task 三种粒度。LongMemEval 测 IE、preference、knowledge-update；LoCoMo 测 temporal/multi-hop，并强制每条 memory 带 `source_turn_ids/date/type/confidence`。

## 23. LCM: Lossless Context Management

- **资料**：类型：经验学习/自进化记忆；论文：[论文/页面](https://papers.voltropy.com/LCM)；代码：[GitHub](https://github.com/Martian-Engineering/lossless-claw)

- **动机**：LCM（Lossless Context Management）针对编码/长程 agent 的上下文腐化与无限会话问题。它反对让模型临时写脚本管理自己的上下文，而把 memory 管理下沉到 deterministic engine：既压缩 active context，又保留所有原文可恢复。它主评测是 OOLONG/Volt vs Claude Code，不是 LoCoMo/LongMemEval；但“摘要只是视图，原文才是事实源”与长期记忆评测高度相关。
- **方法 - Build 侧**：LCM 维护 dual-state memory：Immutable Store 和 Active Context。每个 user message、assistant response、tool result 都带 role、tokens、timestamp 写入不可变存储，绝不改写。Active Context 只放最近原文和旧消息的 Summary Node 指针；当 token 超过 soft threshold，异步 compaction；超过 hard threshold，阻塞压缩最旧 block。摘要节点组成层级 DAG，保留指向原始消息的稳定 ID。大文件不复制进 store，而保存路径引用和类型感知 exploration summary，文件 ID 随摘要 DAG 传播。
- **方法 - Query 侧**：模型在 active context 中看到摘要和稳定 ID。需要细节时，用 `lcm_expand` 在子任务中展开原文，用 `lcm_grep` 搜索不可变历史；主交互循环避免无限展开造成 context flooding。LCM 还提供 LLM-Map/Agentic-Map，把大批量处理的循环、并发、重试、schema validation 交给引擎，避免模型手写循环污染上下文。
- **优点**：关键优点是 lossless retrievability：摘要错误不会毁掉原文证据。对 LongMemEval/LoCoMo，这可避免只存摘要导致的历史状态、时间计数、assistant 信息丢失。软/硬阈值和三层摘要降级保证系统总能收敛。
- **缺点/风险**：LCM 本身不是语义长期记忆，缺少用户偏好、事实冲突、时间状态的专门索引；如果只靠 grep 和摘要遍历，LoCoMo 的开放问答或 LongMemEval 的多 session 证据可能召回慢。论文评测与对话记忆 benchmark 不同，不能直接等价迁移。
- **可借鉴点与实验**：Agent-Mem 应采用 LCM 原则：raw turns immutable，derived summaries 可替换。可落地 ablation：summary-only vs summary+expandable raw IDs；soft/hard threshold 512/1K/2K turns；semantic retrieval 后是否自动 expand raw source；在 LongMemEval knowledge-update/temporal 上测试非破坏性 supersede；在 LoCoMo 测 fact answer 是否引用原文而非摘要。

## 24. LightMem: Lightweight and Efficient Memory-Augmented Generation

- **资料**：类型：参数/模型内记忆；论文：[论文/页面](https://arxiv.org/abs/2510.18866)；代码：[GitHub](https://github.com/zjunlp/LightMem)

- **动机**：LightMem 直接针对 memory-augmented generation 的高成本问题：原始对话冗余多、固定 turn/session 粒度会混话题、在线更新把延迟压到用户请求路径上。它以 Atkinson-Shiffrin 人类记忆模型组织 sensory、short-term、long-term 三阶段，并在 LongMemEval-S 和 LoCoMo 上同时报告准确率、token、API calls、runtime。
- **方法 - Build 侧**：Light1 sensory memory 先用 LLMLingua-2 等压缩模型做 token retain/discard，基于保留概率或条件熵保留高信息 token；压缩结果进入 sensory buffer。buffer 达阈值后触发 topic segmentation：用压缩模型 attention 矩阵找相邻 turn 的局部边界候选，再用 embedding similarity 过滤，取二者交集作为 topic 边界。Light2 topic-aware STM 把 `{topic, message turns}` 放入 STM buffer，达阈值后调用 LLM 生成 summary，形成 LTM entry：`{topic, embedding(summary), summary, user/model turns}`。Light3 LTM 在线只 soft insert，离线 sleep-time 根据相似度和时间戳构建 update queue，后续并行合并/去重。
- **方法 - Query 侧**：查询时从 LTM 做向量检索，返回较短的 topic-aware entries 和必要原始 turns 给 reader。在线阶段不做重型 update，因此 query latency 低；离线 update 通过“后来的 entry 可更新早期 entry”的时间约束处理事实演化。
- **优点**：在 LongMemEval-S 和 LoCoMo 上同时体现效果与成本优势；topic segmentation 避免把多个主题混进同一 memory entry；sleep-time update 把高成本维护从请求路径移开。官方消融显示去掉 topic segmentation 准确率明显下降。
- **缺点/风险**：预压缩可能删掉罕见但关键的 LongMemEval evidence；topic boundary 错误会影响 summary；离线合并若不保留 source_turn_ids，会破坏 LoCoMo/LongMemEval 对原始证据的要求。soft update 到 offline update 之间存在短暂不一致窗口。
- **可借鉴点与实验**：可借鉴“低成本 sensory filter + topic STM + offline consolidation”。可落地 ablation：compression ratio 0.4/0.6/0.8；STM threshold 256/512/768/1024；attention-only、similarity-only、hybrid segmentation；online soft-only vs offline update；summary-only vs summary+raw turns。指标必须同时报 LongMemEval/LoCoMo accuracy、retrieval recall、build/query tokens、API calls 和 runtime。

## 25. LongMemEval: Benchmarking Chat Assistants on Long-Term Interactive Memory

- **资料**：类型：Benchmark/评测集；论文：[论文/页面](https://arxiv.org/abs/2410.10813)；代码：[GitHub](https://github.com/xiaowu0162/LongMemEval)

- **动机**：LongMemEval 不是方法而是长期交互记忆 benchmark。它指出既有数据集常是人类对话、上下文短、能力覆盖不全，尤其缺少 assistant-provided information、knowledge update、temporal metadata 与 abstention。LongMemEval-S 约 115K tokens，LongMemEval-M 约 500 sessions/1.5M tokens，比 LoCoMo 更强调可扩展历史和五类核心能力。
- **方法 - Build 侧**：数据构建先定义 164 个用户属性，覆盖 lifestyle、belongings、life events、situational context、demographic information。人工基于属性生成问题、答案和 evidence statements，并可为 evidence/question 标注时间戳。每个 evidence statement 被嵌入任务型 user-assistant session，用户不是直白报事实，而是在办理简历、旅行、购物等任务中顺带透露。随后用 ShareGPT、UltraChat 和模拟 session 采样混合，按时间戳组装长历史，并人工检查 evidence 是否自然、位置是否多样。
- **方法 - Query 侧**：评测系统必须先在线读完整交互历史并写入记忆，再在最后回答问题。论文把 memory system 统一为 indexing、retrieval、reading 三阶段和 value/key/query/reading 四个控制点。推荐设计包括：value 用 round 而非 session；key 用原 value 加 extracted user facts 做扩展；temporal query 用 LLM 提取时间范围过滤；reading 用 JSON 格式和 Chain-of-Note 先抽关键信息再推理。
- **优点**：能力覆盖明确：IE、multi-session reasoning、knowledge update、temporal reasoning、abstention。它能区分“召回不到证据”和“召回了但 reader 不会用”。对 Agent-Mem 是最重要的防过拟合评测框架之一。
- **缺点/风险**：500 个问题规模不大，LLM judge 对 open-ended preference/abstention 仍可能有偏差；人工构造 evidence 可能与真实用户长期行为不同。LongMemEval 的 round/value 结论不一定直接迁移到 LoCoMo，因为 LoCoMo 对 commonsense/open-domain 和人类长期对话有不同分布。
- **可借鉴点与实验**：Agent-Mem 报告必须按 LongMemEval 六类题拆分：single-session-user、assistant、preference、multi-session、temporal、knowledge-update，并单列 abstention。可落地 ablation：value=session/round/fact；key=V/V+fact/V+summary；query=原问题/时间扩展/实体扩展；reading=direct/CoN/JSON+CoN。再把同样模块迁移到 LoCoMo，检验 temporal 与 multi-hop 是否一致提升。

## 26. MAGMA: A Multi-Graph based Agentic Memory Architecture for AI Agents

- **资料**：类型：参数/模型内记忆；论文：[论文/页面](https://arxiv.org/abs/2601.03236)；代码：[GitHub](https://github.com/FredJiang0324/MAMGA)

- **动机**：MAGMA 认为现有 MAG 系统把所有记忆放进 monolithic store，再按语义相似度/近因检索，导致 temporal、causal、entity、semantic 关系纠缠。LoCoMo 和 LongMemEval 正好包含时间顺序、因果解释、多 session 合成和实体一致性，因此它把每条 memory item 放入多个正交图视角，并用 intent-aware traversal 做查询。
- **方法 - Build 侧**：基本单元是 Event-Node，包含内容 `c_i`、时间戳 `tau_i`、dense vector `v_i` 和实体/时间/上下文 metadata。边空间拆成四类：Temporal Graph 是按时间严格有序的链；Causal Graph 是 LLM consolidation 从局部邻域推断出的因果/蕴含边；Semantic Graph 连接向量相似事件；Entity Graph 连接事件与抽象实体节点。写入用双流：fast path 做事件切分、向量索引、时间主干更新并入队；slow path 后台读取局部邻域，用 LLM 补 causal/entity 等结构。
- **方法 - Query 侧**：Router 先分析 query intent，分类为 WHY/WHEN/ENTITY 等，并解析时间窗、抽取 dense embedding 与 keywords。Anchor identification 融合 vector、keyword、time filtering 的 RRF。随后从 anchors 出发做 heuristic beam search，转移分数同时包含 query intent 对边类型的结构权重和语义相似度；最后按 query 类型拓扑排序 retrieved subgraph，序列化为带 timestamp/content/ref id 的 context，并用 salience budget 控制 token。
- **优点**：关系类型解耦，能解释为什么召回某条证据；LoCoMo overall judge 0.700，高于 Full Context、A-MEM、MemoryOS、Nemori；LongMemEval 平均 61.2%，同时把 token 从 101K 降到 0.7K-4.2K。异步 consolidation 保持写入响应性。
- **缺点/风险**：Causal edges 很容易由 LLM 过度推断，若没有 source/provenance 会污染答案；多图维护复杂，存储和后台任务比纯向量高。论文也承认 benchmark 主要还是对话类，非对话/多模态迁移需校准。
- **可借鉴点与实验**：Agent-Mem 可先实现 Temporal+Entity 两图，Causal 只在原文有明确因果词或 reader 二次验证时加入。可落地 ablation：w/o adaptive policy、w/o temporal、w/o entity、w/o causal；single-graph only；router intent 错误注入；fast-only vs fast+slow consolidation。LongMemEval 看 knowledge-update/temporal，LoCoMo 看 adversarial/multi-hop，并记录 latency、tokens/query、graph build time。

## 27. Mem0: Building Production-Ready AI Agents with Scalable Long-Term Memory

- **资料**：类型：产品/工程系统；论文：[论文/页面](https://arxiv.org/abs/2504.19413)；代码：[GitHub1](https://github.com/mem0ai/mem0)；[GitHub2](https://github.com/TeleAI-UAGI/TeleMem)

- **动机**：Mem0 面向生产 agent 长期记忆：固定 context 无法跨 session 保存用户偏好，full context 成本高且注意力退化，普通 RAG 不会动态更新、去重和处理冲突。论文主评测是 LoCoMo，报告 Mem0 与 graph 版 Mem0g 在 single-hop、multi-hop、open-domain、temporal 上优于多数 memory/RAG baseline；没有把 LongMemEval 作为主表，但其更新机制直接对应 LongMemEval 的 knowledge-update。
- **方法 - Build 侧**：基础 Mem0 是增量 extraction + update。每次处理相邻 message pair，并取数据库里的 conversation summary 和最近 `m=10` messages 作为上下文，由 LLM 抽取候选 salient memories。对每个候选 fact，先向量检索 top `s=10` 相似旧记忆，再把候选和旧记忆交给 LLM tool-call 判断四种操作：ADD、UPDATE、DELETE、NOOP。Graph 版 Mem0g 用 LLM 抽实体和关系三元组，实体节点含 type、embedding、timestamp，边为 labeled relation；新三元组写入前按实体相似度匹配节点，并用 conflict resolver 把过期关系标 invalid，而不是物理删除。
- **方法 - Query 侧**：基础版按语义检索 memory facts 注入回答。Mem0g 有双路检索：entity-centric 先识别 query entity，定位图节点并沿 incoming/outgoing edges 构造相关 subgraph；semantic triplet retrieval 把 query 与关系三元组文本编码比相似度，按阈值返回高相关 triplets。两路可覆盖实体型和概念型查询。
- **优点**：写入操作清楚，适合工程 API；ADD/UPDATE/DELETE/NOOP 给长期记忆生命周期一个可审计接口。LoCoMo 表明基础自然语言记忆对 single-hop/multi-hop 有优势，graph 版对 temporal 和 open-domain 更有帮助；延迟和 token 远低于 full context。
- **缺点/风险**：DELETE 若真删除旧事实会破坏历史问答，因此在 Agent-Mem 中必须改成 supersede；LLM 抽取可能把一次性上下文写成长期偏好。Graph 版不总是提升 multi-hop，说明结构化也可能带来冗余和召回噪声。
- **可借鉴点与实验**：可采用 Mem0 操作接口，但每条 memory 必须有 source_turn_ids、timestamp、state(active/superseded/invalid)。可落地 ablation：ADD-only vs ADD/UPDATE/NOOP vs full operation；DELETE 改物理删除 vs supersede；text memory vs graph memory vs hybrid；entity retrieval vs triplet retrieval。LoCoMo 按四类题测，LongMemEval 特别测 knowledge-update 和 temporal，并检查旧状态问题是否仍可回答。

## 28. Mem9

- **资料**：类型：产品/工程系统；论文：[论文/页面](https://mem9.ai/)；代码：[GitHub](https://github.com/mem9-ai/mem9)

- **动机**：Mem9 是面向 agent 的持久云记忆服务，目标不是提出新算法论文，而是解决工程上的“记忆如何跨 session、机器、工具和 agent 共享”。官方页面强调 persistent across sessions、shared across agents、dashboard 可视化、hybrid search zero config，并公开 LoCoMo benchmark 结果；这使它适合作为 memory-as-service 形态的工程参照。
- **方法 - Build 侧**：Mem9 通过 API key 绑定一个 memory space，支持 direct content write 或 messages ingest。写入接口包含 `appId` 隔离、`agent_id`/`X-Mnemo-Agent-Id` 归因、`session_id`、tags、metadata、memory_type（insight/pinned/session）、mode（smart/raw）以及是否保存原始 session。服务层负责持久化、会话消息捕获、生命周期状态、版本号和 superseded_by 等字段。官方说明 keyword search 默认可用，加入 embeddings 后自动升级为 vector+keyword，无需重建调用管线。
- **方法 - Query 侧**：查询通过 `GET /memories?q=...` 做 recall-style search，或 `search_mode=keyword` 做子串搜索；可按 appId、tags、source、state、memory_type、agent_id、session_id 过滤。Space Chain 支持跨多个空间 recall 并全局 rerank。Dashboard 支持查看、分析、导入导出；Codex、Claude Code、OpenCode、Dify 等集成通过 hooks/plugin 在 agent 流程中注入读取和写入。
- **优点**：最可落地的是边界：同一 API key 可跨机器共享，appId 可隔离应用，metadata/tags/version/state 便于审计。官方 LoCoMo 展示 qwen3.5-plus 下 LLM Score 71.95%、Evidence Recall 53.76%，说明它至少对 LoCoMo 做了端到端记忆检索评测。
- **缺点/风险**：官方公开的机制细节少，难判断 smart ingest 如何抽取、去重、更新；LoCoMo temporal F1 仅 13.79%、evidence recall 18.6%，提示时间推理/证据覆盖仍弱。云服务还涉及隐私、密钥泄漏和多 agent 误共享风险。
- **可借鉴点与实验**：Agent-Mem 可借鉴 API schema：app/project/user namespace、agent attribution、session raw 保存、tags/metadata、version/superseded_by。可落地 ablation：keyword vs vector+keyword；appId 隔离 vs 全局搜索；insight/pinned/session 三种类型；scanAll space-chain vs 单空间。在 LongMemEval 测 session-message 保留对 assistant 类问题的影响，在 LoCoMo 复测 evidence recall 与 temporal 类弱项。

## 29. Memanto: Typed Semantic Memory with Information-Theoretic Retrieval for Long-Horizon Agents

- **资料**：类型：产品/工程系统；论文：[论文/页面](https://arxiv.org/abs/2604.22085)；代码：[GitHub](https://github.com/moorcheh-ai/memanto)

- **动机**：Memanto 挑战“高质量 agent memory 必须用混合知识图谱”的假设。它认为 Mem0/Zep/Letta/A-MEM 等 hybrid graph+vector 系统有 memory tax：写入需要 LLM entity extraction、schema 维护，检索需要多 query 或 graph traversal，导致延迟和复杂度。Memanto 用 typed semantic memory + Moorcheh Information Theoretic Search（ITS）主张单查询、零 ingestion delay 也能在 LongMemEval 和 LoCoMo 高分。
- **方法 - Build 侧**：Build 侧不做知识图谱。系统提供 13 类 semantic memory schema，如 fact、preference 等，每类有检索语义和优先级/衰减信号。写入进入 Moorcheh zero-indexing semantic database，新内容即时可检索。服务包括 daily summary、conflict resolution、answer、recall、remember、agent/session/auth、memory sync、tool connect 等。冲突解决在同 namespace、同 type 内按语义相似找矛盾记忆，触发 supersede、retain、annotate 三选一；时间版本支持 as-of、changed-since、current-only，superseded entries 非破坏性保留。
- **方法 - Query 侧**：Query 侧用 ITS 做单次语义检索，阈值和 retrieval limit 可调，不走多 query graph traversal。论文五阶段消融显示，从 k=10/threshold 0.15 到 k=40/threshold 0.10 带来最大增益；再放宽到最高 k=100/threshold 0.05 进一步提升，说明 LongMemEval/LoCoMo 中 recall 比过窄 precision 更重要。最后由 LLM 在较宽候选上过滤并回答。
- **优点**：系统简单，写入成本低，冲突和时态版本直接对准 LongMemEval knowledge-update；论文报告 LoCoMo 87.1%、LongMemEval 89.8%，且在 vector-only single-query 中领先。非破坏性 supersede 适合需要历史状态回溯的长期记忆。
- **缺点/风险**：强依赖 Moorcheh ITS 专有检索能力，普通向量库未必复现；13 类 schema 可能不适合所有 agent 任务。较大 k 依赖 reader LLM 能过滤噪声，小模型或长尾问题可能被 irrelevant context 干扰。论文也承认现有 benchmark 对非对话、多 agent 共享、冲突压力覆盖不足。
- **可借鉴点与实验**：Agent-Mem 可借鉴轻量 typed schema 和非破坏性 temporal versioning，但不绑定特定数据库。可落地 ablation：type schema 关闭/开启；k=10/40/100；threshold 0.15/0.10/0.05；conflict resolver 关闭/retain/supersede/annotate；current-only vs as-of retrieval。LongMemEval 看 knowledge-update、temporal、multi-session；LoCoMo 看 open-domain/temporal，并记录 retrieval latency、write latency、噪声候选数量。

## 30. Memary

- **资料**：类型：产品/工程系统；论文：[论文/页面](https://kingjulio8238.github.io/memarydocs/)；代码：[GitHub1](https://github.com/kingjulio8238/memary)；[GitHub2](https://github.com/kingjulio8238/Memary)

- **动机**：Memary 是早期 agent memory 工程框架，目标是把人类式记忆、知识图谱和 dashboard 接到现有 agent 上，让 agent 自动记录交互、分析用户偏好、回放执行并把专有数据注入记忆。它没有 LongMemEval/LoCoMo 论文评测，官方 benchmarking 页面仍是 coming soon；因此更适合作为结构参考，而不是效果 baseline。
- **方法 - Build 侧**：Memary 的系统包括 routing agent、knowledge graph 和 memory modules，集成到 ChatAgent。默认 agent 是 ReAct，用工具规划与执行查询；每个 agent response 会写回知识图谱。KG 使用 Neo4j，LlamaIndex 把文档节点加入 graph store；外部查询可用 Perplexity/mistral-7b-instruct。Memory module 包含 Memory Stream 和 Entity Knowledge Store。Memory Stream 记录所有插入 KG 的 entities 及 timestamp，表示用户接触过哪些概念；Entity Knowledge Store 聚合同一实体的出现次数和最近时间，表示用户对哪些实体更熟悉或更关注。
- **方法 - Query 侧**：查询先走 KG query engine；如果没有相关 metadata，routing agent 调外部 LLM/search。KG retrieval 是 recursive：识别 query key entities，构建距实体最大深度 2 的 subgraph；多个 key entities 时把多个 subgraph 做 multi-hop join，再基于子图构造上下文，避免全图搜索。最终新 context window 包含 agent response、最相关实体、以及被摘要过的 chat history。
- **优点**：把 memory stream（广度/时间线）和 entity knowledge store（频率/近因）分开，适合做用户兴趣演化分析；KG 子图深度限制能控制查询成本；dashboard/rewind 方向对调试长期 agent 很有价值。
- **缺点/风险**：机制较早，很多功能标注 future/coming soon；把 response 写入 KG 容易把模型幻觉当知识，若没有 source 和验证会污染 LoCoMo/LongMemEval。Entity frequency/recency 不足以回答时间状态、知识更新和 assistant-provided information。
- **可借鉴点与实验**：Agent-Mem 可借鉴 memory stream + entity store，但每个 entity 必须连接 raw turn、speaker、date 和置信度。可落地 ablation：KG recursive depth 1/2/3；entity frequency-only、recency-only、frequency+recency；外部 search fallback 开/关；response writeback 仅写 user evidence vs 写 assistant response。用 LongMemEval 测 assistant 信息和 knowledge-update 的污染风险，用 LoCoMo 测 multi-hop subgraph join 是否提升 evidence recall。

## 31. MemClaw (Caura)

- **资料**：类型：产品/工程系统；论文：[论文/页面](https://memclaw.net/)；代码：[GitHub](https://github.com/caura-ai/caura-memclaw)

- **动机**：MemClaw 的问题设定不是单个助手记住一个用户，而是多租户、多 agent fleet 共享经验：不同 agent 写入 plain text 后，需要在权限、PII、scope、trust tier 和审计约束下复用。它明确指出 LoCoMo/LongMemEval 只测单 agent 长对话形态，因此自己的重点是生产部署中会随 agent 数量放大的延迟、token 成本、治理和跨 agent 结果传播。
- **方法 - Build 侧**：写入时做 single-pass LLM enrichment：从一个 content 字段自动分类 14 类 memory type，生成 title、summary、tags、importance_score、PII 标记和实体；Postgres/pgvector、Redis、知识图谱和 JSONB document store 分工存储。治理层给每条记忆加 tenant、agent、scope_agent/team/org、status、audit log。contradiction detection 用 RDF triple 比较加 LLM 语义判断，发现冲突后记录 contradiction chain 并 supersede；crystallization 将近重复合并成带 provenance 的 canonical atomic facts。
- **方法 - Query 侧**：召回是混合检索：pgvector semantic similarity、full-text keyword、knowledge graph expansion 最多 2 hop，并按 similarity、importance、freshness、graph boost 组合排序。MCP 暴露 write、recall、manage、list、entity_get、doc、tune、evolve、insights 等工具；evolve 允许 agent 报告成功/失败，更新权重并生成 rule 型预防记忆。每个 agent 还能独立调 top_k、min_similarity、graph hops 和 blend weights。
- **优点**：它把 benchmark 常忽略的生产维度做成一等公民：权限边界、PII 隔离、可审计生命周期、跨 agent 可见性和 per-agent retrieval tuning。对于 LongMemEval 的 knowledge update、abstention 和 LoCoMo 的 temporal/persona 类题，status、freshness、contradiction chain、provenance 能减少旧事实覆盖新事实的风险。
- **缺点/风险**：crystallization 和 supersede 如果没有保留原始 turns，会把“曾经正确但现在过期”的证据压平成单一事实；importance/freshness 排序可能漏掉 LongMemEval 中隐藏很深的小事实；fleet 共享在个人对话 benchmark 上不是直接收益，且 PII/tenant 规则配置错误会带来严重数据泄漏。
- **可借鉴点与实验**：可把 MemClaw 的 governed memory schema 移植为 evidence-first 版本：canonical fact 必须挂 source_ids、valid_from/to、contradicting_ids、status 和 scope。实验做 raw-only、raw+enrichment、raw+KG、raw+contradiction、raw+crystallization 五组，在 LongMemEval 的 KU/TR/ABS 与 LoCoMo temporal/multi-hop 上分别报告 recall@k、最终 EM/F1、token、冲突误判率；另测 importance/freshness 权重网格，验证排序收益是否来自真实证据而不是泄漏式摘要。

## 32. Memento 2: Learning by Stateful Reflective Memory

- **资料**：类型：经验学习/自进化记忆；论文：[论文/页面](https://arxiv.org/abs/2512.22716)；代码：[GitHub](https://github.com/Agent-on-the-Fly/Memento)

- **动机**：Memento 2 不是普通 RAG，而是把“反思记忆”形式化为 Stateful Reflective Decision Process。它认为 LLM agent 可在冻结参数下通过 episodic memory 持续改进：读相似经历对应 policy improvement，写入新 outcome 对应 policy evaluation。与 LongMemEval/LoCoMo 的关系是间接的：二者问事实记忆，而 Memento 2 主要给出“如何从历史问答失败中改进检索/编译策略”的理论框架。
- **方法 - Build 侧**：记忆项是 episode/case，包含 state、action、reward、next state，必要时还包含失败反馈、反思文本和置信度。Write 不是简单日志，而是在交互后把环境 reward 或 correctness signal 写回 memory；论文还讨论 memory 慢速演化、固定大小 buffer、sliding window、importance-weighted memory 等方式，以保证 read-write 过程稳定。
- **方法 - Query 侧**：当前任务先被视为 state，retriever 从 episodic memory 中选择 case；若相似度不足，可走 void case，避免硬套错误经验。读取策略用 Parzen/kernel similarity 给 case 分布建模，在 memory coverage 足够时更偏向相似案例，在低覆盖区域保留探索。LLM 基于当前 state 与 retrieved case 生成动作或答案。
- **优点**：它把“经验库为何能学”讲清楚：retrieval action 是可优化对象，memory coverage radius 与近邻质量决定泛化；void case 能防止在 LongMemEval/LoCoMo 新型问题上过度套用旧 prompt。对于 Agent-Mem，最有价值的是把失败样例转成策略层记忆，而不是把它混入事实证据。
- **缺点/风险**：Memento 2 的 memory 是过程经验，不是可直接引用的用户事实。若把“某类题常问最近偏好”当成答案证据，会污染 LongMemEval 的 abstention 和 LoCoMo 的 adversarial/temporal 问题。它还依赖 reward 或 judge；弱 judge 写入错误 reflection 后，会形成持续偏置。
- **可借鉴点与实验**：落地时只让 Memento 2 控制 retriever/compiler：记录“duration 题要解析绝对时间”“conflict 题先找最新事实”“false premise 题必须允许不知道”等 failure memories。实验做 no-reflection、reflection-as-prompt、reflection-as-router、reflection+void-case 四组；同一 raw evidence pool 下比较 LongMemEval 五能力和 LoCoMo 四类题，额外统计错误 reflection 触发率、检索覆盖半径、answer evidence 是否仍来自原始 turns。

## 33. Memento-Skills: Let Agents Design Agents

- **资料**：类型：经验学习/自进化记忆；论文：[论文/页面](https://arxiv.org/abs/2603.18743)；代码：[GitHub](https://github.com/Memento-Teams/Memento-Skills)

- **动机**：Memento-Skills 将可复用经验从“反思文本”升级成可执行、可测试的 skill library。它承接 Memento 2 的 Read-Write loop，但 memory item 变成 Markdown、prompt、代码、spec、测试等多文件 skill folder。它没有直接面向 LongMemEval/LoCoMo；可借鉴的是 procedural memory：把长对话 QA 中反复出现的时间线整理、冲突判定、证据表编译做成技能，而非把 benchmark 答案写成记忆。
- **方法 - Build 侧**：系统从少量 atomic skills 起步；执行任务后，若成功则提高对应 skill utility，若失败则用 LLM-based failure attribution 从完整执行轨迹和 judge rationale 中定位最该负责的 skill。随后 skill rewriter 做文件级更新，加入 guardrail 或替代策略；若 utility 低于阈值，则重构旧 skill 或生成新 skill。更新后用 UnitTestGate 回放失败样本，防止 regression。
- **方法 - Query 侧**：query 进入 stateful prompt 后，behavior-aligned skill router 选择 skill；路由器不是只靠语义相似，而是用合成正例/ hard negatives、InfoNCE 和单步 offline RL 训练，让“执行该 skill 是否能解决任务”成为检索目标。被选中的 skill 指导工具调用、检索、推理和答案组织，执行结果继续反哺 skill store。
- **优点**：skill 是外部化程序记忆，具备版本、测试和回滚边界，适合把 Agent-Mem 的 pipeline 经验沉淀为可审计模块。对于 LongMemEval/LoCoMo，这种方式能提升读题、query expansion、temporal normalization、multi-hop evidence stitching，而不会直接篡改事实存储。
- **缺点/风险**：skill router 一旦错误，会造成系统性失败；skill 可能过拟合 GAIA/HLE 或某个 benchmark 的表面模板。若把 LoCoMo/LongMemEval dev 题型直接蒸馏成规则，会产生评测泄漏。skill 更新还可能引入安全风险，例如过度扩大工具权限或把 process hint 当事实证据。
- **可借鉴点与实验**：建立四类技能：timeline_sort、profile_lookup、conflict_resolution、evidence_table_compile；每个技能写适用条件、反例、输入输出 schema 和 held-out tests。消融 no-skill、semantic-router、behavior-router、behavior-router+test-gate；在固定 raw memory 上评估 LongMemEval TR/KU/ABS 和 LoCoMo temporal/multi-hop，报告 router hit@k、技能触发后的 evidence recall、失败回滚次数和跨 split 迁移。

## 34. MemGPT: Towards LLMs as Operating Systems

- **资料**：类型：产品/工程系统；论文：[论文/页面](https://arxiv.org/abs/2310.08560)；代码：[GitHub](https://github.com/letta-ai/letta)

- **动机**：MemGPT 将 LLM 上下文窗口类比为操作系统主存，把外部存储类比为磁盘，目标是在有限 prompt 中实现 virtual context management。它早于 LongMemEval/LoCoMo，实验集中在 multi-session chat 和 document QA，但其 memory hierarchy 对两类长对话 benchmark 很直接：近期 turns 要留在主上下文，历史证据要能分页召回，persona/working state 要可更新。
- **方法 - Build 侧**：主上下文由 system instructions、working context 和 FIFO message queue 组成；外部上下文分为 recall storage 与 archival storage。新消息进入 FIFO，queue manager 在 token 压力下把旧消息写入 recall storage，并维护递归摘要；长期事实或文档块写入 archival storage。working context 是可被函数调用修改的热记忆，保存 persona、用户偏好或当前任务状态。
- **方法 - Query 侧**：LLM 通过函数调用主动管理记忆：搜索 recall storage 找旧对话，搜索 archival storage 找文档；结果必须显式搬回 main context 才能被模型使用。heartbeat/request_heartbeat 允许多步函数链，模型可迭代搜索、分页、再回答。文档 QA 中，MemGPT 能反复查询 archival storage，而不受一次性 top-k context 限制。
- **优点**：层次边界清楚，解释了为什么需要 working、episodic recall、archival 三类存储，也提供了可观察的工具轨迹。对 LongMemEval/LoCoMo，MemGPT 的价值在于将近期上下文和历史证据分离，并通过多步检索解决 multi-hop 或跨 session 题，而不是盲目塞满长窗口。
- **缺点/风险**：它依赖模型自主决定何时检索、检索什么；在 benchmark QA 中，弱模型可能直接回答而漏查。递归摘要会丢细节，working context 更新可能覆盖旧状态；函数链增加延迟和成本。若 retrieved memory 没有 source id，LongMemEval 的 abstention 与 knowledge update 会被摘要幻觉误导。
- **可借鉴点与实验**：借鉴三层结构但降低自主性：deterministic router 先做 evidence recall，再让 LLM 编译。消融 self-retrieval、fixed top-k、fixed top-k+heartbeat、working-context on/off、summary on/off；在 LongMemEval M/S 和 LoCoMo 上记录是否发起检索、检索轮数、gold evidence recall@k、回答准确率和 token。关键验证：MemGPT 式分页是否优于一次性高 k，以及摘要是否必须回链 raw turns。

## 35. Memlayer

- **资料**：类型：产品/工程系统；无论文，项目页：[GitHub](https://github.com/divagr18/memlayer)；代码：[GitHub](https://github.com/divagr18/memlayer)

- **动机**：Memlayer 的目标是让开发者用很少代码给任意 LLM 加 persistent memory：自动过滤、抽取结构知识、混合检索并注入上下文。它没有论文型 benchmark 设计，但与 LongMemEval/LoCoMo 的关系很明确：它代表“轻量 SDK + salience gate + vector/KG hybrid”的工程路线，适合验证自动过滤是否会伤害隐藏小事实与时间题。
- **方法 - Build 侧**：Memlayer 包装 OpenAI/Claude/Gemini/Ollama 等 client；对话后先过 salience gate，保存 facts、preferences、user info、decisions、relationships，跳过 greetings、acknowledgments、filler 和 meta conversation。三种 operation mode 控制过滤和存储：LOCAL 用 sentence-transformers 与 ChromaDB+NetworkX，ONLINE 用 embedding API 与同样的 vector+graph，LIGHTWEIGHT 用关键词过滤和 graph-only。后台线程抽取 facts、entities、relationships，写入向量库和知识图谱。
- **方法 - Query 侧**：`client.chat()` 自动召回并注入 memory。检索分三档：Fast 取 2 个向量结果、无图遍历；Balanced 取 5 个向量结果；Deep 取 10 个结果并启用实体抽取和 1-hop graph traversal，适合“tell me everything”或 multi-hop。系统还提供 trace/observability 和调参项，如 salience_threshold、scheduler/curation interval。
- **优点**：它的接入面非常小，模式和检索档位提供了清晰 latency/accuracy knob。对于 LoCoMo 的 single-hop/persona，salience facts 与 graph relationships 会直接有用；对于 LongMemEval 的多 session reasoning，Deep tier 可以作为高召回路径，Balanced/Fast 则用于低成本线上对话。
- **缺点/风险**：salience gate 对 benchmark 极危险：LongMemEval 常把答案藏在任务型对话的边缘细节中，过滤掉“小事实”会不可逆。KG 抽取可能产生幻觉边，LIGHTWEIGHT graph-only 在语义改写问题上召回弱。后台 consolidation 若不保留 raw turn，会让 temporal reasoning 和 knowledge update 无法复核。
- **可借鉴点与实验**：应把 raw turn 永久保留，gate 只决定是否生成 derived facts/KG。实验做 raw-only、raw+salience facts、raw+facts+KG、raw+facts+KG+Deep tier，另设 salience_threshold 扫描；LongMemEval 分 IE/MR/TR/KU/ABS，LoCoMo 分 single/multi/temporal/open-domain，报告被 gate 丢弃的 gold evidence 比例、graph edge 误召回、Fast/Balanced/Deep 的 token 与延迟。

## 36. MemMachine

- **资料**：类型：产品/工程系统；论文：[论文/页面](https://memmachine.ai/)；代码：[GitHub](https://github.com/MemMachine/MemMachine)

- **动机**：MemMachine 的核心假设是长期个性化 agent 必须保留 ground truth，而不是在 ingest-time 过度抽取。官方 README 定位为 open-source long-term memory layer，含 working、episodic、profile 三类 memory；其论文摘要进一步强调存储完整 conversational episodes、用 contextualized retrieval 扩展 nucleus matches。它和 LongMemEval/LoCoMo 高度相关，因为两者都要求跨会话证据、时间变化和用户画像。
- **方法 - Build 侧**：系统通过 REST/Python SDK/MCP 接入 agent，按 org/project/group/agent/user/session 建 memory instance。Working memory 保存当前 session 短期上下文；episodic memory 用 graph database 保存跨 session conversational context；profile memory 用 SQL 保存长期用户事实和偏好。与纯 fact extraction 不同，它强调完整 episode 持久化，再在 profile 层抽取稳定偏好，避免写入阶段丢失对话邻域。
- **方法 - Query 侧**：查询先找 nucleus match，即最相关的原始 episode/turn，再扩展周边上下文来补全多轮证据；profile memory 提供用户事实先验，working memory 补近期状态。论文摘要还描述 Retrieval Agent 在 direct retrieval、parallel decomposition、iterative chain-of-query 间路由，以适配单跳、多跳和需要迭代澄清的查询。
- **优点**：它最贴近 Agent-Mem 的 evidence-first 需求：raw episode 是主证据，profile 只是辅助导航。MemMachine 在 LoCoMo 和 LongMemEvalS 上直接报告成绩，并指出检索深度、context formatting、search prompt、query bias correction 等检索侧优化收益大于 sentence chunking 等 ingest 侧优化，这对长对话 QA 很有启发。
- **缺点/风险**：邻域扩展会带入噪声，尤其 LoCoMo open-domain 或 LongMemEval false-premise 问题会被相邻无关事实诱导。profile 与 episode 冲突时，如果没有 freshness/source 规则，会把旧偏好当当前事实。iterative retrieval 成本高，graph episodic store 的 schema 若设计过重，会增加写入和迁移复杂度。
- **可借鉴点与实验**：主线可实现 raw episode + nucleus+neighbor expansion：先召回最小证据，再按同 session、前后 N turns、同实体、同时间窗扩展。消融 nucleus-only、fixed-neighbor、adaptive-neighbor、parallel decomposition、chain-of-query、profile on/off；在 LongMemEvalS/M 和 LoCoMo 上报告 gold evidence recall、context precision、token、错答中的邻域噪声占比，并强制最终答案引用 raw episode ids。

## 37. Memobase

- **资料**：类型：产品/工程系统；论文：[论文/页面](https://memobase.io/)；代码：[GitHub](https://github.com/memodb-io/memobase)

- **动机**：Memobase 面向“用户画像型长期记忆”，目标是在虚拟陪伴、教育、个性化助手等应用中持续维护 user profile 和 event timeline。它强调三项工程指标：性能、LLM 成本和在线延迟；不是通用 RAG，但官方称在 LoCoMo 上有强表现。与 LongMemEval 的关系主要在 profile、time-aware memory 和低延迟 context API 是否足以回答事实/更新/时间题。
- **方法 - Build 侧**：Memobase 以 user 为中心，不以 agent 为中心。所有输入先作为 blob 插入到用户下，例如 ChatBlob；系统不在 hot path 立即“记忆化”，而是用 per-user buffer 批处理。buffer 达到阈值或空闲一定时间后 flush，抽取 structured profile，字段以 topic、sub_topic、content 组织，并记录 id、created_at；同时维护 user events，用于时间相关问题。默认处理后删除原始 blob，也可配置保留。
- **方法 - Query 侧**：应用可直接调用 `u.profile()` 取结构画像，或调用 `u.context(max_token_size, prefer_topics)` 打包 prompt 字符串，包含 User Background 与 Latest Events。profile 可用于系统 prompt、用户分析和推荐；context API 让在线阶段只需少量 SQL 操作即可取到重点记忆，避免每次做重型 agent 检索。
- **优点**：profile schema 简洁，适合 LoCoMo 的 persona/preference 和产品应用的 latest events；buffer 批处理降低 LLM 成本，context API 在线低延迟。它也提醒我们 LongMemEval/LoCoMo 不一定都需要复杂多 agent，很多题先用 user profile/event timeline 就能缩小检索范围。
- **缺点/风险**：默认删除 blob 对 evidence-first QA 很危险：LongMemEval 要求追溯具体任务对话，profile-only 可能无法回答 multi-session、abstention 或细粒度 temporal reasoning。profile 抽象会合并旧偏好和新状态，也可能把一次事件写成稳定属性。若 context API 只给摘要，模型很难判断 false premise。
- **可借鉴点与实验**：把 Memobase 作为 first-stage navigation，不作为最终证据。每个 profile/event 必须带 source blob/turn ids 和时间戳，最终 compiler 回查 raw turns。实验做 profile-only、event-only、profile+raw、event+raw、raw-only；在 LongMemEval KU/TR/ABS 与 LoCoMo temporal/persona 上比较准确率、profile 冲突率、raw 回查成功率，并测 blob 删除开关对可验证性的影响。

## 38. Memori

- **资料**：类型：产品/工程系统；无论文，项目页：[GitHub](https://github.com/GibsonAI/Memori)；代码：[GitHub](https://github.com/GibsonAI/Memori)

- **动机**：Memori 的定位是 agent-native memory infrastructure，强调“记住 agent 做过什么，而不只是说过什么”。它包装已有 LLM client，也能通过 OpenClaw/Hermes/MCP 接入，自动捕获 conversation 和 agent execution。它与 LoCoMo 直接相关：官方 benchmark 文档称用结构化 memory 在 LoCoMo 取得较高准确率和低 token；与 LongMemEval 的关系是可检验 triples+summaries 能否覆盖更新、时间和 abstention。
- **方法 - Build 侧**：Memori 将应用逻辑与 LLM 之间的请求响应拦截下来，按 entity_id 与 process_id attribution 归属记忆；session 用来聚合多步 agent 执行。Advanced Augmentation 后台 pipeline 把原始对话拆成 semantic triples，捕捉具体事实、偏好、约束、变化属性，并链接到原始 conversation；同时生成 conversation summaries，保留任务意图、时间进展和上下文。OpenClaw 插件还捕获 tool calls、decisions、outcomes。
- **方法 - Query 侧**：SDK 包装后会自动持久化和召回；MCP/Hermes 提供 `memori_recall` 与 summary 类工具，让 agent 按需取结构记忆。triples 用于精确事实召回和压缩，summaries 用于补充叙事和 temporal flow；两层互链，避免孤立 triple 脱离语境。LoCoMo 文档强调这种结构化表示可显著降低每 query token。
- **优点**：相对纯向量 chunk，triples 降噪、压缩和可过滤；summaries 补足“为什么/如何变化”的叙事。process_id/session 机制适合 Agent-Mem 记录工具流程和编译失败，可让策略记忆与用户事实分开。对 LoCoMo 的 single-hop/persona 和 LongMemEval 的信息抽取，结构化 triples 会提升 recall precision。
- **缺点/风险**：triple 容易丢失否定、条件、时间限定和说话人，LongMemEval 的 knowledge update/abstention 会被错误三元组伤害；conversation summary 仍可能幻觉。process memory 若被注入 answer evidence，会把“agent 曾经这么做”误当成“用户事实”。自动包装 client 还可能捕获敏感工具输出，需要权限和脱敏。
- **可借鉴点与实验**：采用双 store：factual triples/summaries 与 process traces 物理隔离。事实 triple 必须包含 polarity、valid_time、speaker、source_turn_ids；process hint 只影响 retriever/compiler。实验做 raw-only、triple-only、summary-only、triple+summary、triple+summary+raw verification；在 LongMemEval KU/TR/ABS 与 LoCoMo temporal/multi-hop 上统计 triple 缺失时间限定导致的错答，以及 process hint 是否降低重复检索失败。

## 39. Memory Intelligence Agent

- **资料**：类型：参数/模型内记忆；论文：[论文/页面](https://arxiv.org/abs/2604.04503)；代码：[GitHub](https://github.com/ECNU-SII/MIA)

- **动机**：Memory Intelligence Agent（MIA）面向 deep research agents，而非聊天助手：它批评长上下文/轨迹检索会引入噪声、成本增加，且只保存“结果是什么”，缺少“如何得到结果”的 process-oriented memory。它没有直接评估 LongMemEval/LoCoMo，但对 Agent-Mem 的启发是把历史搜索/推理流程作为 planner 策略记忆，而 factual QA 仍必须由原始对话证据回答。
- **方法 - Build 侧**：MIA 是 Manager-Planner-Executor 架构。Memory Manager 是非参数记忆，保存高价值历史轨迹；写入时把图片压缩成 caption，把冗长搜索轨迹压缩成 structured workflow summary，并按语义相似做替换或新增。每条 memory 记录 question、caption、usage count、success count、correct/incorrect label 等。系统还通过 alternating RL 训练 Executor 服从 plan，再训练 Planner 吸收 memory context；test-time learning 中同时抽取非参数 workflow memory 和用 GRPO 更新 Planner 参数。
- **方法 - Query 侧**：当前 query 先检索相似 workflow，评分由 semantic similarity、value reward、frequency reward 组成，既取 positive paradigms 也取 failed trajectories 作为 negative constraints。Planner 基于这些记忆生成 search plan，Executor 执行工具检索与分析；在开放环境下，MIA 用 Reviewer/Area-Chair 式 unsupervised judgment 提供 reward，支持自进化。
- **优点**：它清楚地区分“事实记忆”和“过程记忆”：workflow 用来指导分解、搜索深度、工具顺序和失败规避。对 LongMemEval/LoCoMo，MIA 可用于改进 retrieval planning，比如 temporal 题先定时间窗，多跳题并行拆分，false-premise 题加入校验步骤，而不直接提供答案。
- **缺点/风险**：MIA 涉及训练和 test-time 参数更新，不适合作为 clean benchmark 预测过程；如果在 LongMemEval/LoCoMo test 上用答案或 judge 更新 Planner，会构成泄漏。workflow summary 也可能把错误检索习惯固化为策略；非参数和参数记忆混合后，可解释性比外部 evidence store 更弱。
- **可借鉴点与实验**：只借鉴策略层：保存 query decomposition、search depth、temporal filter、evidence verification 的成功/失败 workflow，不让其进入 answer evidence。消融 no-workflow、positive-only、positive+negative、semantic-only scoring、semantic+value+frequency；固定 raw dialogue store，在 LongMemEval 和 LoCoMo 上报告检索轮数、gold evidence recall、错误重复率、token 成本，严格禁止 test-time 依据答案更新。

## 40. Memory OS of AI Agent

- **资料**：类型：经验学习/自进化记忆；论文：[论文/页面](https://arxiv.org/abs/2506.06326)；代码：[GitHub](https://github.com/BAI-LAB/MemoryOS)

- **动机**：MemoryOS 将对话记忆类比操作系统内存管理，认为长期 agent 需要按寿命分层：Short-Term Memory 保存近期页面，Mid-Term Memory 保存主题段落，Long-term Persona Memory 保存稳定用户画像/知识。它直接在 LoCoMo 上评估，并与 MemoryBank、MemGPT 等比较；对 LongMemEval 的关系是其 STM/MTM/LPM 分层可对应近期上下文、跨 session 证据和用户事实更新。
- **方法 - Build 侧**：STM 将每个 dialogue page 表示为 `{Q_i, R_i, T_i}`，并构建 dialogue chain 维持上下文。STM 是固定长度队列，满后 FIFO 转入 MTM。MTM 用 segment-page 组织：相同主题 pages 进入同一 segment，匹配分数结合 embedding cosine 与 keyword Jaccard；segment summary 由 LLM 根据相关 pages 生成。MTM 的 heat 由访问次数、交互长度、recency 加权，低 heat segment 可被淘汰，高 heat segment 触发 LPM 更新。LPM 维护 user profile、user KB、user traits、agent traits 等队列。
- **方法 - Query 侧**：召回时 STM 全量进入 prompt，因为它代表最近上下文；MTM 先按语义/关键词选 top-m segments，再在其中选 top-k pages；LPM 从 User KB 和 Assistant Traits 中取相关条目，同时常驻 profile/traits。response generation 将 STM、MTM pages、LPM persona 合并，以获得连贯和个性化回答。
- **优点**：它的层次清晰、实现可控，且直接针对 LoCoMo 的 single-hop、multi-hop、temporal、open-domain 做实验和 ablation。论文报告 MTM 贡献最大，LPM 次之，chain 较小；这对 Agent-Mem 提示：主题页检索比单纯长期 persona 更关键。heat 机制也能限制长期存储无限膨胀。
- **缺点/风险**：FIFO 和 heat 会淘汰低频旧事实，而 LongMemEval 常专门考低频 needle；LPM 可能把短期状态固化为长期偏好，伤害 knowledge update。segment summary 若替代 raw pages，会丢证据；persona 常驻注入还可能让模型在 abstention 题中猜测。
- **可借鉴点与实验**：保留 MemoryOS 的 STM/MTM/LPM，但让 MTM page 指向 raw turns，LPM 仅作 prior。消融 STM-only、MTM-only、LPM-only、STM+MTM、STM+MTM+LPM、chain on/off、heat eviction on/off、top-k pages 扫描。LongMemEval 上重点看 IE/MR/TR/KU/ABS，LoCoMo 上复现四类题，报告低 heat gold evidence 被淘汰率、profile 误固化率和 k 增大后的噪声拐点。

## 41. MemoryBank: Enhancing Large Language Models with Long-Term Memory

- **资料**：类型：经验学习/自进化记忆；论文：[论文/页面](https://arxiv.org/abs/2305.10250)；代码：[GitHub](https://github.com/zhongwanjun/MemoryBank-SiliconFriend)

- **动机**：MemoryBank 是早期长期陪伴式记忆系统，目标是让 LLM 在多日互动中记住历史经历、生成用户画像，并用更拟人化的遗忘/强化机制管理记忆。它早于 LongMemEval，LoCoMo 论文和后续系统常把它作为长期对话记忆基线。对 Agent-Mem，MemoryBank 代表 summary+retrieval+personality+forgetting 的经典路线。
- **方法 - Build 侧**：Memory storage 保存 daily conversation records、daily event summaries、global event summary、daily personality insights 和 global personality summary。对话每天被 LLM 摘成事件摘要，多日摘要再聚合成全局摘要；人格理解同样从 daily traits/emotions 聚合到 global portrait。每个 memory piece 进入 dense retrieval 索引。更新机制受 Ebbinghaus forgetting curve 启发，用 retention strength、elapsed time、recall reinforcement 控制记忆随时间衰减或因被召回而增强。
- **方法 - Query 侧**：当前 conversation context 被编码后，与 memory pieces 做 dual-tower dense retrieval；系统把 relevant memory、global user portrait、global event summary 组织进 prompt，让 SiliconFriend 能引用旧建议、旧经历和用户性格来回答。若某条记忆被召回，其强度增加、时间重置，从而降低未来遗忘概率。
- **优点**：daily/global 分层摘要可作为长期导航，强度信号可做 ranking feature；在陪伴场景，personality summary 能提升连续性和个性化。对于 LoCoMo persona 和 temporal 类题，它提供了事件/人格两条索引；对于 LongMemEval 的多 session reasoning，global summary 可快速定位可能证据。
- **缺点/风险**：遗忘机制与 benchmark 目标冲突：LongMemEval/LoCoMo 可能考很久之前、低频但精确的事实，按时间衰减删除会直接丢 gold evidence。personality inference 容易把单次情绪或事件误写成稳定人格；summary 可能幻觉、遗漏数字和条件；reinforcement 会让常被问到的信息越来越强，冷门事实更难找。
- **可借鉴点与实验**：只把 MemoryBank summary 当 navigation，不允许替代 raw evidence；memory strength 影响排序，不控制删除。实验做 raw-only、daily summary、global summary、summary+raw verification、forgetting on/off、reinforcement on/off；LongMemEval 上重点看 hidden IE、TR、KU、ABS，LoCoMo 上看 temporal/persona/multi-hop，报告旧证据丢失率、summary-to-raw 命中率、人格误归纳案例和时间衰减对 recall@k 的影响。

## 42. MemOS: A Memory OS for AI System

- **资料**：类型：产品/工程系统；论文：[论文/页面](https://arxiv.org/abs/2507.03724)；代码：[GitHub](https://github.com/MemTensor/MemOS)

- **动机**：MemOS 的出发点是把长期记忆从“RAG 插件”提升为可调度的系统资源。论文指出静态参数、短上下文和临时检索都缺少生命周期、版本、权限和 provenance，因此难以支撑持续个性化、知识更新和跨任务复用。它的核心判断是：记忆不是一次性的上下文拼接，而是会被创建、激活、迁移、融合、归档和遗忘的长期资产。
- **方法 - Build 侧**：核心抽象是 MemCube，payload 可承载 plaintext、activation/KV cache、parameter delta，metadata 记录时间、来源、版本、权限、使用频率和状态。MemReader 把用户请求解析成 MemoryCall，MemOperator 负责混合检索和结构化组织，MemScheduler 决定 memory 类型、加载路径和迁移策略，MemLifecycle/MemStore 处理过期、归档、发布和共享。
- **方法 - Query 侧**：查询时先解析意图、时间范围、实体和上下文锚点，再按任务在 plaintext、KV activation、参数能力模块之间调度；高频稳定 plaintext 可预转成 KV 注入以降低 TTFT，过期参数可回落到可审计 plaintext。调度结果不是简单 top-k，而是带权限、版本和访问路径的 Memory API 调用。
- **优点**：系统化、可审计，显式支持 provenance、versioning、ACL、TTL 和 memory migration。论文在 LoCoMo 上报告整体 LLM judge 75.80，在 LongMemEval 上整体 77.8，并用同一基础模型比较 Mem0、Zep、MemU、MIRIX 等。
- **缺点/风险**：架构很大，parameter/activation memory 的工程门槛高；若在 Agent-Mem 中全量照搬，容易把 benchmark 的关键问题从“证据召回与校验”扩散成“操作系统工程”。此外，把稳定事实蒸馏进 activation 或 parameter 后，回滚和逐条溯源会比外部明文记录困难得多。
- **可借鉴点与实验**：先落地非参数版 MemCube：content、source_turn_ids、valid_time、version、supersedes、confidence、access_count。可做三组 ablation：LoCoMo/LongMemEval 上只用 plaintext、plaintext+metadata routing、metadata routing+KV/summary cache；同时扫 chunk size 与 top-k；另测 QPS 下 add/search 成功率和延迟。

## 43. MemU

- **资料**：类型：产品/工程系统；论文：[论文/页面](https://memu.pro/)；代码：[GitHub](https://github.com/NevaMind-AI/memU)

- **动机**：MemU 面向 proactive agent 的“workspace to memory”问题：用户数据来自对话、文件、URL、图片/音频和工具流，不能每次塞回完整上下文，也不能只靠人工标签。其官方文档强调自动结构化、跨链接和约 10x token reduction。它更偏“持续工作的个人/企业助手”，目标是让 agent 在后台理解用户、客户、项目和资源，而不是等用户显式说“请记住”。
- **方法 - Build 侧**：MemU 把记忆组织成类似文件系统的层次：resources 像 mount point，memory items 像文件，categories 像目录，cross-references 像 symlink。ingest 阶段解析 raw workspace，抽取 facts、preferences、skills、relationships，并持续监控 agent I/O；proactive bot 在后台更新用户 profile、待办和可能的下一步意图。
- **方法 - Query 侧**：对外提供 memorize、status、categories、retrieve 等 API，检索时按 user/task scope 返回压缩后的 typed context，而不是原始日志。官方示例中 retrieve 输入用户 query 和 where 条件，返回可直接注入 agent 的相关上下文。层次化 category 还能先给主题概览，再下钻到 item 或 resource，适合低 token 预算下的渐进式召回。
- **优点**：工程接口简洁，memory-as-filesystem 的心智模型适合命名空间、资源挂载和可浏览调试；resource/item/category 三层比纯 chunk 更利于把 long conversation 压成可控上下文。
- **缺点/风险**：公开资料主要是产品/工程文档，没有像 LoCoMo/LongMemEval 那样的完整论文实验；自动抽取 facts/preferences 若缺少源 turn 绑定，会产生二手事实污染。proactive 更新如果没有“确认/撤销/过期”机制，可能把短期任务、临时情绪或错误网页内容长期固化。
- **可借鉴点与实验**：在 Agent-Mem 中可复用 filesystem schema：resource=会话/文档，item=原子事实，category=用户、事件、偏好、任务。ablation：LongMemEval/LoCoMo 上比较 raw turns、flat item、resource-item-category、再加 cross-link；另测 token 压缩率、source recall、错误更新回滚率。可以额外评估后台刷新策略：每轮更新、会话后更新、只在冲突或高置信事实出现时更新。

## 44. MIRIX: Multi-Agent Memory System for LLM-Based Agents

- **资料**：类型：产品/工程系统；论文：[论文/页面](https://arxiv.org/abs/2507.07957)；代码：[GitHub](https://github.com/Mirix-AI/MIRIX)

- **动机**：MIRIX 认为现有记忆系统过于 flat，只把历史切块向量化，难以覆盖个性化、抽象知识、程序流程、敏感原文和多模态资源。它把 memory routing 和 retrieval 视为长期 agent 的核心能力。论文的隐含前提是：不同认知功能需要不同存储格式，如果都塞进同一个向量库，检索时只能靠相似度猜测语义角色。
- **方法 - Build 侧**：系统定义六类记忆：Core 保存 persona/human 高优先级 profile，容量接近上限时受控改写；Episodic 保存带 timestamp 的事件；Semantic 保存实体、概念和关系；Procedural 保存流程和脚本；Resource 保存文档/图片/转录内容；Knowledge Vault 保存地址、凭据等需逐字保真的敏感信息。每类由 Memory Manager 维护，Meta Memory Manager 负责路由和去重更新。
- **方法 - Query 侧**：MIRIX 提出 Active Retrieval：Chat Agent 先从当前输入推断 topic，再对六类 memory 分别检索 top entries，并用 `<episodic_memory>` 等标签注入系统提示。它还提供多种 retrieval tools，让 agent 根据问题选择合适模块。
- **优点**：taxonomy 清楚，能避免偏好、事件、流程、原文凭据互相污染；在 LoCoMo 中只允许使用检索记忆、不看原始 transcript，报告 overall 85.38%，强在 multi-hop 和 temporal。另有 ScreenshotVQA，多模态长期屏幕记忆减少 99.9% 存储。
- **缺点/风险**：八个 agent 和六类 memory 对纯文本 benchmark 可能过重；类别边界若定义不清，manager 会重复写入或漏写。Active Retrieval 依赖 topic 生成，一旦 topic 偏了，所有分库检索都会被带偏；Knowledge Vault 也必须有严格权限，否则会造成敏感信息过召回。
- **可借鉴点与实验**：Agent-Mem 可先实现 Core/Profile、Episodic、Semantic、Resource 四类，Knowledge Vault 禁入 benchmark 答案。ablation：单 flat store vs 六类路由；主动生成 topic vs 直接 query；每类 top-k 独立预算 vs 全局 top-k，并在 LoCoMo multi-hop/temporal 上看收益。同时记录每道题命中的 memory type，形成分类混淆矩阵，检查偏好问题是否误入 episodic、时间问题是否漏掉 timestamp。

## 45. Mnemis: Dual-Route Retrieval on Hierarchical Graphs for Long-Term LLM Memory

- **资料**：类型：参数/模型内记忆；论文：[论文/页面](https://arxiv.org/abs/2602.15313)；代码：[GitHub](https://github.com/microsoft/Mnemis)

- **动机**：Mnemis 针对相似度检索的盲点：很多长期记忆问题需要全局枚举和结构扫描，例如“某人去过哪些城市”，关键证据可能与 query 语义相距很远。论文把传统 embedding/BM25 视作 System-1，把层级图遍历视作 System-2。它特别适合回答“所有相关项”“跨会话归纳”“弱语义但强结构关系”的问题。
- **方法 - Build 侧**：它构建两张图。Base graph 保存 Episodes、Entities、Edges、Episodic Edges，增量抽取实体和关系，并记录 valid_at/invalid_at，还强制把 speaker 抽为实体以增强召回。Hierarchical graph 把 layer-0 entities 自底向上聚合为 category nodes，遵循 minimum concept abstraction、many-to-many mapping、compression efficiency 三个原则，并周期性重建。
- **方法 - Query 侧**：System-1 对 episode/entity/edge 做 embedding 与 BM25 检索，再用 RRF 或 reranker 排序；System-2 从最高层 category 开始，让 LLM 逐层选择相关分支，到实体后取相连 edges 和 episodes。最后对两路结果 union 后重排并格式化为 context。这个过程把“先找相似片段”扩展为“先定位概念区域，再取区域内全部证据”，对答案需要覆盖完整集合时尤其关键。
- **优点**：兼顾局部语义相似与全局结构覆盖。论文在 LoCoMo 达到 93.9，在 LongMemEval-S 达到 91.6；ablation 显示 System-1+System-2 的 LoCoMo overall 93.3，高于单独 System-1 Graph、RAG+Graph 或 System-2。
- **缺点/风险**：层级构建和 Global Selection 需要额外 LLM 成本，论文也承认当前以周期重建处理更新；System-2 对枚举类问题强，对严格时间序列问题可能不稳定。层级摘要若过度抽象，会让模型沿错误 category 浏览；many-to-many mapping 虽提升召回，也会增加噪声分支。
- **可借鉴点与实验**：可为 Agent-Mem 加一层“枚举路由”：当问题含 all/list/which/ever/几次等，触发 category-to-entity traversal。ablation：dense+BM25、base graph、base+hierarchy；再按 query type 分析 LoCoMo single-hop/multi-hop/temporal。还应测 global selection 调用次数、选中 category 的人工正确率、以及层级深度过浅或过深时的召回变化。

## 46. What Deserves Memory: Adaptive Memory Distillation for LLM Agents

- **资料**：类型：参数/模型内记忆；论文：[论文/页面](https://arxiv.org/abs/2508.03341)；代码：[GitHub](https://github.com/nemori-ai/nemori)

- **动机**：NEMORI 关注 build 侧“什么值得写入记忆”。论文批评 importance score、emotion tag、fact template 都是设计者启发式，容易主观偏置或过度存储；它用 predictive coding 思想，把未来效用转化为“已有知识无法预测的部分”。这使写入策略从“我觉得重要”变成“相对当前记忆确实新增或修正了什么”。
- **方法 - Build 侧**：框架分两级，受 structure、representation、distillation 三个 prior 约束。Episodic Memory Integration 先用 LLM 对消息窗口做局部分段，生成 narrative episode、cue 和 embedding，再通过 associative integration 合并有连续性的旧 episode。Semantic Knowledge Distillation 再用 existing memory 合成 anticipatory schema，把真实 episode 与预测 schema 的差异抽成 semantic insights，并用 new/merge/conflict 写入语义库。
- **方法 - Query 侧**：推理阶段同时检索 episodic narratives、少量 raw episodes 和 semantic knowledge，拼成回答上下文。论文强调构建过程与管理系统解耦，可作为 A-MEM、MemoryOS 等第三方系统的 distillation layer。narrative 负责高效召回，raw episode 负责精确校验，semantic insight 负责跨 episode 的抽象补充，三者分工比单一摘要更稳。
- **优点**：写入准则数据驱动，episode 级处理降低消息级成本；在 LoCoMo 上 gpt-4.1-mini 平均 LLM judge 80.8，gpt-4o-mini 73.0；LongMemEvalS 上用 3.7-4.8K tokens 超过 101K full context。它还证明写入质量能比单纯扩大上下文更重要，尤其在长输入注意力被稀释时更明显。
- **缺点/风险**：管理和检索策略相对朴素；prediction error 本身依赖 LLM 对“已有知识”的预测质量，错误预测会把噪声当新知识。另一个风险是 narrative episode 会改写原始话语，如果没有 raw episode 兜底，精确偏好、数字和时间可能被摘要损坏。
- **可借鉴点与实验**：Agent-Mem 可把“写入”改为 compare(expected_from_memory, actual_episode)。ablation：固定 20-turn chunk vs LLM partition；无预测差异 vs NEMORI distill；只 episodic、只 semantic、二者结合；在 LongMemEval knowledge-update 和 LoCoMo temporal 上测 source precision 与存储压缩率。还可单独评估 new/merge/conflict 三类 consolidation 的准确率，防止更新题被误合并。

## 47. OpenMemory

- **资料**：类型：产品/工程系统；论文：[论文/页面](https://openmemory.cavira.app/)；代码：[GitHub1](https://github.com/caviraoss/openmemory)；[GitHub2](https://github.com/CaviraOSS/OpenMemory)

- **动机**：OpenMemory 针对“向量库不等于记忆”的工程痛点：普通 RAG 不知道事实、事件、偏好、情绪、程序性经验的差异，也不处理时间有效性、重要性衰减、关联路径和本地隐私。官方定位是 local persistent memory store for LLM applications。它强调用户拥有数据库和 schema，适合桌面助手、IDE、MCP host 等本地长期使用场景。
- **方法 - Build 侧**：它采用 local-first SQLite 思路，记忆分成 episodic、semantic、procedural、emotional、reflective 多 sector；支持 temporal knowledge graph 的 valid_from/valid_to，decay engine 对不同 sector 做自适应遗忘，reinforcement pulse 根据对话或工具结果提升强度。Waypoint graph 维护双向关联边，连接器可导入 GitHub、Notion、Drive 等资源。官方页还提到 sector-aware decay、scheduled audits、root-child long-doc stitching 等工程机制。
- **方法 - Query 侧**：查询不是单纯 cosine，而是 composite scoring：salience、recency、coactivation 等信号共同排序；explainable recall 返回 waypoint traces，说明哪些节点被召回以及原因。它还提供 SDK、server、VS Code、MCP 等集成。对长对话 QA，可先按 sector 过滤，再用 waypoint 扩展相邻事件或偏好，最后把 trace 和源文本一起交给答案模型。
- **优点**：本地、可解释、低运维，schema 直接覆盖长期对话需要的事件、事实、技能、反思和情绪线索；时间有效性和 decay 比硬 TTL 更接近真实长期记忆。
- **缺点/风险**：公开资料是产品/README，不是 LoCoMo/LongMemEval 论文实验；emotional sector 对 benchmark QA 可能引入不必要噪声。decay/reinforcement 如果没有任务级验证，可能让常被提到但错误的记忆越来越强，反而压制少见但真实的证据。
- **可借鉴点与实验**：Agent-Mem 可借鉴 multi-sector+composite scoring，但所有 node 必须保留 source_turn_ids。ablation：cosine only vs cosine+recency+salience；无 decay vs sector-aware decay；无 waypoint trace vs trace-expanded retrieval，并在 LongMemEval temporal/knowledge-update 上测幻觉和过期事实。还要把 decay 设成只影响召回排序、不删除 raw evidence，避免评测中需要早期事实时不可恢复。

## 48. Optimizing the Interface Between Knowledge Graphs and LLMs for Complex Reasoning

- **资料**：类型：产品/工程系统；论文：[论文/页面](https://arxiv.org/abs/2505.24478)；代码：[GitHub](https://github.com/topoteretes/cognee)

- **动机**：Cognee 论文关注 KG 与 LLM 的接口优化：GraphRAG pipeline 有 chunk size、retriever type、top-k、QA prompt、graph prompt、task preprocessing 等大量超参，但很多系统默认凭经验配置，导致复杂推理效果不稳定。它提醒我们，图结构本身不是银弹，真正影响答案的是“如何切、如何抽、如何查、如何序列化给模型”。
- **方法 - Build 侧**：Cognee 是 ECL 管线：Extract 摄取 text/PDF/image/audio/source code 并记录元数据、去重；Cognify 用 Pydantic schema 和 LLM 抽取 entities、relations、attributes、summaries；Load 写入 graph、relational、vector stores。Dreamify 把 ingestion、chunking、LLM extraction、retrieval、evaluation 视为一个参数化 pipeline，用 TPE 搜索配置。它调的不是单点模型参数，而是整条“原文到图再到答案”的接口组合。
- **方法 - Query 侧**：它支持 chunk-level、summary-based、graph neighborhood、RAG、graph completion、graph-summary completion 等 retriever。graph completion 会取匹配节点及周边 triplets，格式化为结构化文本交给 LLM，以支持 multi-hop reasoning。统一接口允许只换 retriever 或 prompt，不必重写整条 ingestion pipeline，因此适合做受控实验。
- **优点**：最大价值是提醒 KG memory 不是“建图即有效”，接口和超参决定质量。论文在 HotPotQA、TwoWikiMultiHop、MuSiQue 上优化 EM/F1/LLM correctness，训练集和 held-out test 都有可见提升；例如 HotPotQA F1 和 correctness 经调参后明显高于默认配置，说明小的接口改动可带来大差异。
- **缺点/风险**：并未直接评测 LoCoMo/LongMemEval，任务更偏静态多跳 QA；样本量较小，metric 和 prompt 敏感。若把调参结果直接迁移到长期对话，可能忽视时间有效性、用户偏好更新和多 session 噪声。
- **可借鉴点与实验**：Agent-Mem 的 graph 层应被当作可调模块。ablation：chunk 200/500/1000/2000、graph vs text retriever、top-k 1/5/10/20、graph prompt 简洁/结构化；在 LoCoMo multi-hop 与 LongMemEval multi-session 上报告 accuracy、context tokens、graph extraction error。建议加一个“图证据序列化格式”实验：triples、natural-language facts、triples+source quote，比较模型是否更少编造中间关系。调参集必须和最终测试集隔离，避免把 benchmark 题型调成隐式提示。

## 49. Remember Me, Refine Me: A Dynamic Procedural Memory Framework for Experience-Driven Agent Evolution

- **资料**：类型：产品/工程系统；论文：[论文/页面](https://arxiv.org/abs/2512.10696)；代码：[GitHub1](https://github.com/agentscope-ai/ReMe)；[GitHub2](https://github.com/modelscope/ReMe)

- **动机**：ReMe 关注 procedural memory 的动态演化。论文认为许多 agent memory 是 passive accumulation：存 raw trajectory 或粗摘要，复用时不适配新任务，长期会混入过期或有害经验。它强调“记住”和“精炼”必须闭环，经验池要随着任务分布和模型能力变化而更新。
- **方法 - Build 侧**：ReMe 的 experience acquisition 从成功和失败轨迹中抽取结构化经验 E=<usage scenario, content, keywords, confidence, tools>。LLMsumm 做三类分析：success pattern recognition、failure trigger analysis、comparative insight generation；随后用 LLM-as-judge 验证 actionable/accurate/value，并用相似度去重写入 experience pool。
- **方法 - Query 侧**：新任务到来时，用 usage scenario 等字段做 embedding 检索 top-K，必要时 rerank，再用 rewriting module 把多条经验改写成适配当前任务的 guidance。执行后 refinement 会 selective addition 成功经验；失败时最多 3 次 reflection 产生候选 lesson；每条经验记录 retrieval frequency 和 utility，低效经验按阈值删除。这样复用的不是原轨迹，而是“何时用、怎么做、要避开什么”的程序性片段。
- **优点**：闭环覆盖抽取、复用、精炼，适合工具调用/多步任务。BFCL-V3 与 AppWorld 上 ReMe(dynamic) 稳定优于 No Memory、A-MEM、LangMem；Qwen3-8B+ReMe 可超过无记忆 Qwen3-14B，说明 memory quality 可部分替代模型规模。论文 ablation 还显示 keypoint-level experience、selective addition、failure-aware reflection、utility deletion 都有独立贡献。
- **缺点/风险**：不是 LoCoMo/LongMemEval 的长期对话 QA 方法；固定在任务开始检索一次，对中途状态变化反应有限；LLM-as-judge 可能漏判经验质量。如果把 ReMe 用来存用户事实，utility deletion 可能错误删除低频但重要的偏好或一次性事件，因此应严格限定为策略层记忆。
- **可借鉴点与实验**：Agent-Mem 可把 ReMe 用于“检索策略经验”而非用户事实，如 temporal 问题要取 valid interval。ablation：trajectory-level vs keypoint-level、selective vs full addition、是否 utility deletion、K=1/3/5/10，并在 LoCoMo/LongMemEval 按题型记录策略命中率。所有 procedure memory 都必须标注来源实验和适用条件，禁止由测试集答案反向生成规则。

## 50. SimpleMem: Efficient Lifelong Memory for LLM Agents

- **资料**：类型：参数/模型内记忆；论文：[论文/页面](https://arxiv.org/abs/2601.02553)；代码：[GitHub](https://github.com/aiming-lab/SimpleMem)

- **动机**：SimpleMem 指出现有长期记忆要么保留全历史导致低信息密度和中间上下文退化，要么用迭代推理在线过滤导致 token 与延迟过高。它直接在 LoCoMo 和 LongMemEval-S 上评测，目标是在固定 token 预算下提升信息密度、时间归一化和检索效率。
- **方法 - Build 侧**：构建侧是三阶段。第一，Semantic Structured Compression 用固定窗口切分对话，LLM 作为语义密度门控：低价值寒暄输出空集，高价值窗口被转成自包含 memory units；同一生成步骤完成指代消解、相对时间转 ISO 时间和事实原子化。每个 memory unit 同时建 dense embedding、BM25 lexical、symbolic metadata 三类索引。第二，Online Semantic Synthesis 在写入时把同 session 的相关事实合成为高密度条目，减少碎片。
- **方法 - Query 侧**：Intent-Aware Retrieval Planning 让 LLM 根据 query 和当前历史生成语义查询、词法查询、符号约束和检索深度 `d`；系统并行查 dense、BM25、metadata 三路，每路 top-n，n 随复杂度变化，再用集合并去重形成紧凑上下文。LongMemEval/LoCoMo 中，这对应先判断是 temporal、multi-hop、preference 还是 single-hop，再动态调节证据范围。
- **优点**：机制与 benchmark 痛点高度对应：时间归一化帮助 temporal reasoning，指代消解和多视角索引帮助跨 session 检索，在线合成降低碎片。论文中 GPT-4.1-mini 在 LoCoMo 平均 F1 43.24、约 531 tokens，明显高于 Mem0 且比 full-context 少约 30 倍 token；LongMemEval-S 上 GPT-4.1-mini 平均 76.87%，GPT-4.1 平均 83.97%。
- **缺点/风险**：“semantic lossless”在实践中很难保证，压缩和在线合成可能把细粒度措辞、否定、旧状态覆盖掉；若合成条目无 source id，回答会变成二手事实；intent planner 可能低估复杂 query，导致召回不足。LongMemEval/LoCoMo 的开放域和知识更新题尤其容易暴露压缩误删与时间冲突。
- **可借鉴点与实验**：可采用 SimpleMem 的三路索引和意图规划，但 raw dialogue 必须保留，压缩 memory 只做召回入口。落地消融包括无时间归一化/无指代消解、chunk storage 替代 semantic compression、关闭 online synthesis、固定 top-k 替代 intent depth、dense-only/BM25-only/symbolic-only。除 F1/accuracy 外，记录检索 token、source-turn 命中率和 knowledge-update 旧事实误召回。

## 51. Zep: A Temporal Knowledge Graph Architecture for Agent Memory

- **资料**：类型：产品/工程系统；论文：[论文/页面](https://arxiv.org/abs/2501.13956)；代码：[GitHub](https://github.com/getzep/graphiti)

- **动机**：Zep/Graphiti 认为传统 RAG 面向静态文档，不适合企业 agent 持续吸收对话、业务数据和状态变化；长期记忆需要同时回答“现在是什么”和“过去何时成立”。它直接在 Deep Memory Retrieval 和 LongMemEval 上评测，与 Agent-Mem 主线高度相关；LoCoMo 未直接评测，但其 temporal KG 很适合多会话对话依赖。
- **方法 - Build 侧**：Graphiti 构建动态时序知识图谱 `G=(N,E,phi)`，分三层：episode subgraph 保存 message/text/JSON 原始输入，是 non-lossy 存储；semantic entity subgraph 保存解析并消歧后的实体和事实边；community subgraph 用 label propagation 动态维护实体社区及摘要。系统使用双时间线：事件参考时间 `T` 和数据库事务时间 `T'`，事实边带 `t'created/t'expired/tvalid/tinvalid`；新事实若与时间重叠的旧事实矛盾，会使旧边失效而非删除。
- **方法 - Query 侧**：检索函数可写成 `f=query -> search -> rerank -> constructor`。search 同时覆盖 facts、entities、communities，使用 cosine、BM25 和 graph BFS；BFS 可从近期 episode seed 出发，捕捉上下文接近性。rerank 支持 RRF、MMR、episode mention frequency、node distance 和 cross-encoder。constructor 输出事实及有效日期、实体名与摘要、社区摘要，供 LLM 生成答案。
- **优点**：episode 与 semantic 双层让派生事实能回溯原始消息，时间有效期支持知识更新、历史关系和 temporal reasoning；BM25、向量和 BFS 组合比单向量检索更稳。论文中 DMR 上 Zep gpt-4-turbo 94.8%，gpt-4o-mini 98.2%；LongMemEval 中上下文从平均 115k 降到 1.6k，gpt-4o-mini 分数 55.4% 到 63.8%，gpt-4o 60.2% 到 71.2%，延迟约降 90%。
- **缺点/风险**：实体抽取、关系抽取和矛盾失效依赖 LLM，若边写错或时间范围错，会在图中传播；无正式 ontology 时社区和关系名可能漂移；构图成本高于轻量 memory；LongMemEval 中 single-session-assistant 类别下降，说明图谱摘要可能不适合助手自述细节；DMR 本身较短，full-context 已很强，不足以证明复杂长期记忆。
- **可借鉴点与实验**：Agent-Mem 可实现轻量 temporal graph：entity、event/state、relation、valid_from、valid_to、source_turn_ids、transaction_time；图只做召回和扩展，最终答案仍引用 raw dialogue。LongMemEval/LoCoMo 消融包括无 temporal invalidation、无 episode raw backpointer、BM25-only/vector-only/BFS-only、无 community、top-k 10/20/50、cross-encoder rerank 开关；重点看 knowledge-update、temporal、多 session 和证据可追溯率。
