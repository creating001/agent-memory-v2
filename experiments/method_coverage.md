# 外部方法代码覆盖表

本文件记录 `docs/method.md` 51 个方法的本地代码覆盖情况。它是实验侧调研记录，不改变 clean protocol，也不把外部实现直接迁入项目。

使用原则：

- 标为“已读代码”的方法，才可以作为下一阶段设计的明确依据。
- 标为“已 clone，待读”的方法，只说明本地已有代码入口，不能在方案里声称已吸收其细节。
- 标为“不 clean / 只做负面参考”的内容，不能迁移任何使用 gold、judge、benchmark 标签、sample id、样本级规则或 test feedback 的逻辑。
- 旧项目 `external/creating001-agent-memory` 只能只读参考。clean naive RAG / query 组织思想可以参考；任何 target phrase、final answer、category、sample 规则和 benchmark 字段逻辑都不能迁移。

## 已读代码摘要

- `external/creating001-agent-memory/src/agent_memory/prompts/answer.py`、`answer_templates.py`、`baseline/context.py`、`prompts/retrieve.py`：重点参考 evidence-first query 组织、turn-pair/source-turn context、时间题区分 memory date 与 event date；不迁移不 clean guardrail。
- `external/xMemory/evaluation/locomo/xMemory_search_framework.py`：参考 semantic/episodic 双通道、信息增益式 episode expansion、原始消息回链。
- `external/Mnemis/global_selection/global_selector.py`、`prompts.py`：参考层级图 top-down selection、selected node 到 one-hop episodes/relations 的回链。
- `external/graphiti/graphiti_core/prompts/extract_edges.py`：参考 temporal/provenance schema，特别是 `valid_at`、`invalid_at`、`episode_indices`。
- `external/SimpleMem/simplemem/core/memory_builder.py`、`hybrid_retriever.py`、`answer_generator.py`、`models/memory_entry.py`：参考 build-stage lossless typed memory、多视角检索和 structured context。
- `external/mem0/mem0/memory/main.py`：参考 metadata scope、search filter、memory add/search 工程边界。
- `external/A-mem/test_advanced.py`：确认其 benchmark category/answer 参与 answer 的部分不 clean，只做负面参考和高层 memory neighborhood 参考。
- `external/EverOS/src/everos/memory/models.py`、`search/manager.py`、`search/hierarchy.py`、`strategies/extract_atomic_facts.py`、`strategies/extract_user_profile.py`：参考 episode/atomic fact/profile 分层、parent provenance、fact-child MaxSim 到 episode-parent 的 hierarchy retrieval。
- `external/MAMGA/memory/memory_builder.py`、`query_engine.py`、`temporal_parser.py`：参考 temporal graph/RRF/relative time parser；其中 session id / dataset keyword 映射不 clean，不能迁移。
- `external/memanto/memanto/app/services/memory_parsing_service.py`、`memory_read_service.py`、`memory_write_service.py`：参考 memory type taxonomy、namespace/filter、as-of/superseded/TTL 查询。
- `external/letta/letta/schemas/memory.py`：参考 core/archival/recall memory 的分层和 context window accounting。
- `external/ACON/src/productive_agents/ctxopt/history_optimizer.py`、`experiments/smolagents/prompts/context_opt/prompt_history_v2.jinja`：参考 resumable structured summary 和错误/决策保留；不把 summary 作为唯一事实源。
- `external/DeepResearch/WebAgent/WebResummer/src/prompt.py`：参考 iterative evidence extraction / summary，但需要限制成本和避免 tool-style benchmark adaptation。
- `external/langmem/docs/docs/guides/manage_user_profile.md`：参考 profile 单实例 schema、namespace 和 update-in-place；profile 不能覆盖 raw evidence。
- `external/memobase/docs/site/features/event/event.mdx`：参考 event summary / event tags / profile delta / created time 的 event-profile 双通道。
- `external/MIRIX/mirix/schemas/episodic_memory.py`：参考 episodic event 的 `event_type`、`summary`、`details`、`actor`、`occurred_at`、`created_at`、`filter_tags`。
- `external/MemMachine/evaluation/episodic_memory/longmemeval_models.py`：只作为负面边界/评测格式参考；其中 question_type、answer、answer_session_ids、has_answer 等字段不能进入 prediction。
- `external/HippoRAG/src/hipporag/HippoRAG.py`、`rerank.py`：参考 fact/entity 检索后回链 passage/raw chunk，以及 dense passage 兜底；不迁移 gold_docs/gold_answers 评测入口和 DSPy demo filter 作为预测规则。
- `external/LightMem/src/lightmem/memory_toolkits/memories/layers/naive_rag.py`、`memzero.py`：参考 memory layer search wrapper、metadata 和 used_content 格式；不引入外部 memory backend 依赖。
- `external/Memary/src/memary/memory/entity_knowledge_store.py`：参考 entity/count/date 聚合的轻量 memory 管理思想；v39 不迁移固定 entity 规则。
- `external/MIA/Memory-Serve/*.py`、`external/MIA/Inference/*`：确认其中大量 correct/incorrect feedback、judge/gold 相关逻辑只可作为负面边界，不可迁移到 prediction。

## 51 项覆盖表

| # | 方法 | 本地代码入口 | 当前状态 | 对本项目的取舍 |
|---:|---|---|---|---|
| 1 | A-MEM | `external/A-mem` | 已读部分代码 | 高层参考 memory neighborhood；发现 category/answer 进入 answer 的不 clean 逻辑，不能迁移。 |
| 2 | ACON | `external/ACON` | 已读核心 context optimizer | 参考结构化 history compression / resume；不能让 summary 替代 raw evidence。 |
| 3 | Acontext | `external/Acontext` | 已 clone，待读 | 可能参考 context/memory SDK 工程边界。 |
| 4 | agentmemory | `external/agentmemory` | 已 clone，待读 | 可能参考轻量 agent memory API，不作为当前设计依据。 |
| 5 | xMemory | `external/xMemory` | 已读 LoCoMo search framework | 参考 semantic/episodic 双通道、原始消息回链和 adaptive expansion。 |
| 6 | Buffer of Thoughts | `external/buffer-of-thought-llm` | 已 clone，待读 | 只可能参考 procedural strategy，不写入样本事实。 |
| 7 | ChatHaruhi | `external/Chat-Haruhi-Suzumiya` | 已 clone，待读 | 可能参考角色长期对话记忆组织。 |
| 8 | LoCoMo | `external/LoCoMo` | 已 clone，使用为 benchmark 参考 | 只用于数据格式/评测理解，预测阶段不能使用标签/evidence。 |
| 9 | EverOS | `external/EverOS` | 已读 memory models/search/strategies | 参考 episode、atomic fact、profile、cascade 管理和 hierarchy retrieval。 |
| 10 | Everything is Context | `external/aigne-framework` | 已 clone，待读 | 可能参考 file/context abstraction，不作为当前设计依据。 |
| 11 | From RAG to Memory / HippoRAG2 | `external/HippoRAG` | 已读核心 retrieval/rerank | 参考 fact/entity -> passage 回链、PPR/dense passage fusion；不迁移 gold_docs/gold_answers 评测入口和 DSPy demo filter。 |
| 12 | gbrain | `external/gbrain` | 已 clone，待读 | 可能参考 personal graph memory。 |
| 13 | General Agentic Memory via Deep Research | `external/general-agentic-memory` | 已 clone，待读 | 可能参考 agentic retrieval 和 reflection，需要严格限制 feedback 泄漏。 |
| 14 | Generative Agents | `external/generative_agents` | 已 clone，待读 | 参考 reflection/importance/recency 的经典结构；不直接适配 benchmark。 |
| 15 | LD-Agent | `external/LD-Agent` | 已 clone，待读 | 可能参考长期对话 personalization。 |
| 16 | Hindsight | `external/hindsight` | 已 clone，待读 | 可能参考 retain/recall/reflect，但需确认训练/feedback 边界。 |
| 17 | HippoRAG | `external/HippoRAG` | 已 clone，待读核心 | 可能参考 entity graph + retrieval fusion。 |
| 18 | Honcho | `external/honcho` | 已 clone，待读 | 可能参考 production memory API / session state。 |
| 19 | EM-LLM | `external/EM-LLM-model` | 已 clone，待读 | 可能参考 episodic/infinite-context memory。 |
| 20 | HyperMem | `external/EverOS` | 已 clone，待读 HyperMem 具体目录 | 可能参考 hypergraph memory，但需要 source provenance。 |
| 21 | IterResearch | `external/DeepResearch` | 已读 WebResummer prompt | 参考 iterative evidence extraction；全量使用前需评估 query token 成本。 |
| 22 | LangMem | `external/langmem` | 已读 profile guide | 参考 profile schema、namespace、update-in-place；不让 profile 替代 raw evidence。 |
| 23 | LCM | `external/lossless-claw` | 已 clone，待读 | 可能参考 lossless context management。 |
| 24 | LightMem | `external/LightMem` | 已读 memory layer 检索入口 | 参考 NaiveRAG/MemZero wrapper、metadata 和 used_content 组织；不引入其外部 backend。 |
| 25 | LongMemEval | `external/LongMemEval` | 已 clone，使用为 benchmark 参考 | 只用于评测协议/数据理解，预测阶段不能使用 question_type/answer。 |
| 26 | MAGMA | `external/MAMGA` | 已读 memory builder/query/temporal | 参考 multi-graph/RRF/temporal parser；不迁移 session id/keyword 样本规则。 |
| 27 | Mem0 | `external/mem0`、`external/TeleMem` | 已读 mem0 main，TeleMem 待读 | 参考 metadata scope、filter、memory lifecycle。 |
| 28 | Mem9 | `external/mem9` | 已 clone，待读 | 可能参考 memory SDK/API。 |
| 29 | Memanto | `external/memanto` | 已读 parsing/read/write service | 参考 memory taxonomy、namespace、as-of/superseded/TTL。 |
| 30 | Memary | `external/Memary` | 已读 entity knowledge store | 参考 entity/count/date 聚合管理；只采用通用思想，不迁移固定 entity 规则。 |
| 31 | MemClaw | `external/caura-memclaw` | 已 clone，待读 | 可能参考 memory lifecycle / retrieval。 |
| 32 | Memento 2 | `external/Memento` | 已 clone，待读 | 只可能参考 stateful reflective memory；防止写入 benchmark 反馈。 |
| 33 | Memento-Skills | `external/Memento-Skills` | 已 clone，待读 | 只可沉淀通用 procedural skills，不能写测试实体/答案。 |
| 34 | MemGPT / Letta | `external/letta` | 已读 memory schema | 参考 core/archival/recall memory、context accounting。 |
| 35 | Memlayer | `external/memlayer` | 已 clone，待读 | 可能参考 SDK 层 memory abstraction。 |
| 36 | MemMachine | `external/MemMachine` | 已读评测模型入口 | 只作为负面边界/格式参考；含 answer/session 标注的逻辑不能迁移。 |
| 37 | Memobase | `external/memobase` | 已读 event docs | 参考 event + profile delta + created time 的双通道管理。 |
| 38 | Memori | `external/Memori` | 已 clone，待读 | 可能参考 production agent memory API。 |
| 39 | MIA | `external/MIA` | 已读部分 memory serve / inference 入口 | 多数 correct/incorrect feedback 与 judge/gold 相关逻辑不 clean，只做负面边界；候选选择与最终生成分离的工程思想可参考。 |
| 40 | MemoryOS | `external/MemoryOS` | 已 clone，待读 | 参考 memory OS 分层治理，不作为短期主线。 |
| 41 | MemoryBank | `external/MemoryBank-SiliconFriend` | 已 clone，待读 | 可能参考 profile summarization，但不能丢 raw evidence。 |
| 42 | MemOS | `external/MemOS` | 已 clone，待读 | 参考 memory OS / governance，不作为短期重型依赖。 |
| 43 | MemU | `external/memU` | 已 clone，待读 | 可能参考 memory update/API。 |
| 44 | MIRIX | `external/MIRIX` | 已读 episodic schema | 参考 episodic/semantic/core memory taxonomy 和 event schema。 |
| 45 | Mnemis | `external/Mnemis` | 已读 global selector/prompts | 参考层级图 selection 和 selected node 回链 episode/relation。 |
| 46 | Nemori | `external/nemori` | 已 clone，待读 | 可能参考 adaptive distillation；需防止过度摘要。 |
| 47 | OpenMemory | `external/openmemory` | 已 clone，待读 | 可能参考 local memory service/API。 |
| 48 | Cognee | `external/cognee` | 已 clone，待读 | 可能参考 KG-LLM interface，但需 raw evidence 回链。 |
| 49 | ReMe | `external/ReMe` | 已 clone，待读 | 只可参考通用 procedural reflection，不写入具体测试反馈。 |
| 50 | SimpleMem | `external/SimpleMem` | 已读 builder/retriever/answer | 参考 lossless typed memory、multi-view retrieval、structured answer context。 |
| 51 | Zep / Graphiti | `external/graphiti` | 已读 temporal edge prompt | 参考 temporal KG 的 `valid_at` / `invalid_at` / episode provenance。 |

## 当前设计输入

基于已读代码、v36/v37 badcase 和当前双基准结果，v37 row-linked build memory bundle 已被判定为负向：LongMemEval-S full `0.744`，比 v36 `0.772` 低 `14` correct。它说明 source-linked typed memory 的思路可以保留，但不宜直接作为 answer prompt 中的额外事实视图。

下一阶段设计原则：

- build 侧：继续使用现有 LLM typed memory records，保留 source/provenance、dedup、supersede 和 active/superseded 状态。
- management 侧：typed memory 不能覆盖 raw evidence，也不能无条件进入 final prompt。
- retrieval 侧：更应借鉴 EverOS/SimpleMem/xMemory 的 atomic fact child retrieval -> raw episode parent expansion，把 typed memory 用作 source selection、reranking、coverage/control signal。
- compiler 侧：减少派生 memory 与 raw evidence 在 prompt 中竞争，优先构造更少、更准的 raw evidence context、conflict chain 或 candidate aggregation。
- v38 具体采用 route-scoped raw top60 + `role_query_snippet`：借鉴 creating001 的 source-turn materialization 和 ACON/LCM 的 query-focused context compression，但不引入 LLM reranker、summary 替代事实源或 benchmark-specific guardrail。
- v39 采用 memory-aware evidence selector：借鉴 HippoRAG/EverOS 的 fact/entity/typed memory -> raw passage 回链，把 top60 候选压回 top40 raw evidence；typed memory 只做 source-linked selection signal，不进入 prompt fact view。
- v43 采用 session-thread evidence layout + row-linked build memory guide：借鉴 xMemory/SimpleMem 的 episodic raw message 回链、Mnemis 的 selected node -> episode 回链和 Graphiti/Zep 的 temporal/provenance 思路；typed memory 只作为已召回 raw rows 的定位 guide，不作为独立事实源。
- clean 侧：所有 route 和 compiler 只能来自 question text、question_time、原始对话和 memory metadata；不能使用 LoCoMo category、LongMemEval question_type、evidence label、gold 或 judge。
