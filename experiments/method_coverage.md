# 外部方法代码覆盖表

本文件记录 `docs/method.md` 51 个方法的本地代码覆盖情况。它是实验侧调研记录，不改变 clean protocol，也不把外部实现直接迁入项目。

使用原则：

- 标为“已读代码”的方法，才可以作为下一阶段设计的明确依据。
- 标为“已 clone，待读”的方法，只说明本地已有代码入口，不能在方案里声称已吸收其细节。
- 标为“不 clean / 只做负面参考”的内容，不能迁移任何使用 gold、judge、benchmark 标签、sample id、样本级规则或 test feedback 的逻辑。
- 旧项目 `external/creating001-agent-memory` 只能只读参考。clean naive RAG / query 组织思想可以参考；任何 target phrase、final answer、category、sample 规则和 benchmark 字段逻辑都不能迁移。

## 已读代码摘要

- `external/creating001-agent-memory/src/agent_memory/prompts/answer.py`、`answer_templates.py`、`baseline/context.py`、`baseline/retrieve.py`、`baseline/queries.py`、`baseline/routing.py`、`baseline/pipeline.py`、`baseline/evidence_finalizer.py`、`baseline/guardrails.py`、`prompts/retrieve.py`：重点参考 evidence-first query 组织、turn-pair/source-turn materialization、adjacent context window、两阶段 evidence extraction、窄机械 finalizer 和时间题区分 memory date / event date；不迁移不 clean guardrail、benchmark 对齐细节或样本级规则。
- `external/xMemory/evaluation/locomo/xMemory_search_framework.py`：参考 semantic/episodic 双通道、信息增益式 episode expansion、原始消息回链。
- `external/Mnemis/global_selection/global_selector.py`、`prompts.py`：参考层级图 top-down selection、selected node 到 one-hop episodes/relations 的回链。
- `external/graphiti/graphiti_core/prompts/extract_edges.py`：参考 temporal/provenance schema，特别是 `valid_at`、`invalid_at`、`episode_indices`。
- `external/SimpleMem/simplemem/core/memory_builder.py`、`hybrid_retriever.py`、`answer_generator.py`、`models/memory_entry.py`：参考 build-stage lossless typed memory、多视角检索和 structured context。
- `external/mem0/mem0/memory/main.py`：参考 metadata scope、search filter、memory add/search 工程边界。
- `external/A-mem/test_advanced.py`：确认其 benchmark category/answer 参与 answer 的部分不 clean，只做负面参考和高层 memory neighborhood 参考。
- `external/EverOS/src/everos/memory/models.py`、`search/manager.py`、`search/hierarchy.py`、`search/recall/base.py`、`search/shaper.py`、`strategies/extract_atomic_facts.py`、`strategies/extract_user_profile.py`：参考 episode/atomic fact/profile 分层、parent provenance、fact-child MaxSim 到 episode-parent 的 hierarchy retrieval、候选元数据清洗和 search DTO 结构。
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
- `external/LD-Agent/Module/EventMemory.py`、`Personas.py`：参考 topic/noun overlap、recency 和 session summary/profile 管理；profile 抽取不能替代 raw evidence。
- `external/MemoryOS/memoryos-pypi/retriever.py`、`updater.py`、`mid_term.py`、`long_term.py`、`prompts.py`：参考 short/mid/long-term 分层、user/assistant knowledge 双通道、timestamp 检查和多路并行 retrieval；暂不引入重型 memory OS 依赖。
- `external/agentmemory/src/functions/search.ts`、`external/agentmemory/src/prompts/reflect.ts`：参考 BM25/vector 混合搜索、token budget truncation、project/agent scope 与多 memory reflection；不把反思结果作为唯一事实源。
- `external/LongMemEval/src/generation/run_generation.py`、`retrieval/run_retrieval.py`：参考官方 generation prompt 和 turn->round expansion；其中 `has_answer`、`answer_session_ids`、`question_type` 只能用于评测/负面边界，不能进 prediction。
- `external/LoCoMo/task_eval/rag_utils.py`、`gpt_utils.py`：参考 dialogue-level RAG prompt 中“从对话精确作答”的读者纪律；`category`、answer choices 和评测字段不能进 prediction。
- `external/MemoryBank-SiliconFriend/utils/prompt_utils.py`、`memory_bank/memory_retrieval/local_doc_qa.py`、`utils/memory_utils.py`、`memory_bank/summarize_memory.py`：参考按日期保存历史、相关记忆+日期注入、相同 source/date 邻居扩展、history/personality 双摘要；风险是 summary/profile 可能压掉 raw evidence，因此只作为 profile/event 双通道和 source expansion 的参考，不让摘要成为唯一事实源。
- `external/memU/src/memu/app/retrieve.py`、`prompts/memory_type/{profile,event,knowledge,behavior}.py`、`prompts/retrieve/{pre_retrieval_decision,query_rewriter,llm_category_ranker,llm_item_ranker,judger}.py`：重点参考 profile/event/knowledge/behavior 类型拆分、query rewrite、category/item staged retrieval、sufficiency check；可借鉴为通用 memory-type gating 和不足时追加检索，但不能引入 gold/judge/benchmark 标签。
- `external/hindsight/README.md`、`external/hindsight/hindsight-api-slim/hindsight_api/engine/search/retrieval.py`、`fusion.py`、`reranking.py`：参考 semantic/BM25/graph/temporal 四路并行 recall、per-source cap、RRF/interleave fusion、cross-encoder rerank 后再按 token budget 裁剪。对 v103 的启发是保留多路候选池，但用 rerank 和上下文预算控噪声。
- `external/MemOS/src/memos/mem_scheduler/memory_manage_modules/search_pipeline.py`、`rerank_pipeline.py`、`external/MemOS/src/memos/reranker/strategies/dialogue_common.py`：参考 LongTermMemory/UserMemory 双通道搜索、过滤短/近重复 memory 后 rerank、对话 pair 作为 rerank 文档的格式；当前只采用 cross-encoder rerank 与文档截断思想，不引入 LLM rerank。
- `external/general-agentic-memory/src/gam/core/tree.py`、`core/node.py`、`prompts/gam_prompts.py`：参考 memory tree / directory summary / batch memorize + organize 的层级组织思想；当前不引入文件系统式 memory OS，只借鉴“短 memory record + 层级摘要”的组织原则。
- `external/nemori/nemori/core/memory_system.py`、`search/unified.py`、`domain/models.py`、`llm/generators/{episode,semantic,merger}.py`、`llm/prompts.py`、`evaluation/longmemeval/search.py`：参考 buffer -> episode -> semantic memory、episode/semantic 双通道 hybrid search、source_messages 回链、prediction-correction semantic delta 和 episode merge；评测脚本里的 gold/question_type 只作为负面边界，不能进入 prediction。

## 51 项覆盖表

| # | 方法 | 本地代码入口 | 当前状态 | 对本项目的取舍 |
|---:|---|---|---|---|
| 1 | A-MEM | `external/A-mem` | 已读部分代码 | 高层参考 memory neighborhood；发现 category/answer 进入 answer 的不 clean 逻辑，不能迁移。 |
| 2 | ACON | `external/ACON` | 已读核心 context optimizer | 参考结构化 history compression / resume；不能让 summary 替代 raw evidence。 |
| 3 | Acontext | `external/Acontext` | 已 clone，待读 | 可能参考 context/memory SDK 工程边界。 |
| 4 | agentmemory | `external/agentmemory` | 已读 search/reflect 入口 | 参考轻量混合检索、scope、token budget 和 reflection；reflection 只能作通用组织思想，不能替代 raw evidence。 |
| 5 | xMemory | `external/xMemory` | 已读 LoCoMo search framework | 参考 semantic/episodic 双通道、原始消息回链和 adaptive expansion。 |
| 6 | Buffer of Thoughts | `external/buffer-of-thought-llm` | 已 clone，待读 | 只可能参考 procedural strategy，不写入样本事实。 |
| 7 | ChatHaruhi | `external/Chat-Haruhi-Suzumiya` | 已 clone，待读 | 可能参考角色长期对话记忆组织。 |
| 8 | LoCoMo | `external/LoCoMo` | 已读 RAG/eval prompt 入口 | 参考 dialogue-level RAG prompt；预测阶段不能使用 category、answer choices、gold 或评测字段。 |
| 9 | EverOS | `external/EverOS` | 已读 memory models/search/strategies | 参考 episode、atomic fact、profile、cascade 管理和 hierarchy retrieval。 |
| 10 | Everything is Context | `external/aigne-framework` | 已 clone，待读 | 可能参考 file/context abstraction，不作为当前设计依据。 |
| 11 | From RAG to Memory / HippoRAG2 | `external/HippoRAG` | 已读核心 retrieval/rerank | 参考 fact/entity -> passage 回链、PPR/dense passage fusion；不迁移 gold_docs/gold_answers 评测入口和 DSPy demo filter。 |
| 12 | gbrain | `external/gbrain` | 已 clone，待读 | 可能参考 personal graph memory。 |
| 13 | General Agentic Memory via Deep Research | `external/general-agentic-memory` | 已读 GAM tree / node / prompts | 参考层级 memory 组织和 batch memorize/organize；文件系统式 memory OS 暂不迁移。 |
| 14 | Generative Agents | `external/generative_agents` | 已 clone，待读 | 参考 reflection/importance/recency 的经典结构；不直接适配 benchmark。 |
| 15 | LD-Agent | `external/LD-Agent` | 已读 EventMemory/Personas | 参考 topic overlap、recency、session summary 和 persona/profile 抽取；profile 不覆盖 raw evidence。 |
| 16 | Hindsight | `external/hindsight` | 已读 recall/rerank 核心 | 参考四路并行 retrieval、RRF/interleave、cross-encoder rerank 和 token budget 裁剪；retain/reflect 更重，暂不迁移。 |
| 17 | HippoRAG | `external/HippoRAG` | 已 clone，待读核心 | 可能参考 entity graph + retrieval fusion。 |
| 18 | Honcho | `external/honcho` | 已 clone，待读 | 可能参考 production memory API / session state。 |
| 19 | EM-LLM | `external/EM-LLM-model` | 已 clone，待读 | 可能参考 episodic/infinite-context memory。 |
| 20 | HyperMem | `external/EverOS` | 已 clone，待读 HyperMem 具体目录 | 可能参考 hypergraph memory，但需要 source provenance。 |
| 21 | IterResearch | `external/DeepResearch` | 已读 WebResummer prompt | 参考 iterative evidence extraction；全量使用前需评估 query token 成本。 |
| 22 | LangMem | `external/langmem` | 已读 profile guide | 参考 profile schema、namespace、update-in-place；不让 profile 替代 raw evidence。 |
| 23 | LCM | `external/lossless-claw` | 已 clone，待读 | 可能参考 lossless context management。 |
| 24 | LightMem | `external/LightMem` | 已读 memory layer 检索入口 | 参考 NaiveRAG/MemZero wrapper、metadata 和 used_content 组织；不引入其外部 backend。 |
| 25 | LongMemEval | `external/LongMemEval` | 已读 retrieval/generation 入口 | 参考官方 generation prompt 和 round expansion；`has_answer`、`answer_session_ids`、`question_type` 等隐藏字段不能进 prediction。 |
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
| 40 | MemoryOS | `external/MemoryOS` | 已读 pypi retriever/updater/prompts | 参考 short/mid/long-term 分层、双通道 knowledge 和 timestamp 检查；不作为短期重型依赖。 |
| 41 | MemoryBank | `external/MemoryBank-SiliconFriend` | 已读 retrieval/summarize 入口 | 参考按日期 history/profile 管理、相关记忆注入和 same-source/date 邻居扩展；不能让 summary/profile 替代 raw evidence。 |
| 42 | MemOS | `external/MemOS` | 已读 search/rerank 入口 | 参考 LongTerm/User memory 双通道、过滤后 rerank 和 dialogue pair 文档格式；不引入重型 memory OS 或 LLM rerank。 |
| 43 | MemU | `external/memU` | 已读 retrieve 与 memory-type prompts | 参考 profile/event/knowledge/behavior 类型拆分、query rewrite、category/item staged retrieval 和 sufficiency check；预测阶段只可使用问题、原始对话和 build memory。 |
| 44 | MIRIX | `external/MIRIX` | 已读 episodic schema | 参考 episodic/semantic/core memory taxonomy 和 event schema。 |
| 45 | Mnemis | `external/Mnemis` | 已读 global selector/prompts | 参考层级图 selection 和 selected node 回链 episode/relation。 |
| 46 | Nemori | `external/nemori` | 已读核心 memory/search/generator 与评测入口 | 参考 episode/semantic 双通道、source_messages 回链、hybrid search、semantic delta 和 episode merge；评测字段不能进 prediction。 |
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
- v64 采用 list_count-only adjacent-turn window BM25：借鉴 creating001 的 turn-pair/source-turn materialization，并结合 v54 在 `list_count` diagnostic 上 gain/loss `1/0` 的局部信号；119 条 LongMemEval-S list_count diagnostic 已验证负向（v64 `93/119` < v42 same119 `95/119`），顶层 config 删除，只保留诊断快照。
- v65 采用 unit/sum mechanical finalizer：借鉴 creating001 的窄后处理 finalizer 思想，但只允许基于已生成答案和 visible evidence_report 做通用数值单位补全或加和一致性修正，不使用 gold、judge、benchmark 标签或样本规则；LongMemEval-S full 已验证负向（v65 `379/500` < v42 `387/500`，gain/loss `20/28`，answer_changed `120`），且受 current code drift 影响，不是纯 finalizer 正向消融。顶层 config 和源码分支删除，只保留 formal 快照。
- v103 采用 query-side rerank + context budget：借鉴 Hindsight 的多路候选后 cross-encoder rerank、EverOS 的候选池/parent provenance、MemOS 的 rerank 文档截断。保持 v102 build memory 和 raw evidence first，不让 typed memory 直接成为独立事实源。LongMemEval-S full 在同 Qwen3.6 no-thinking backbone 下已验证负向：v103 strict/lenient `0.780/0.818`，低于后续主目录 v102 dual flash rerun 的 `0.814/0.830`；虽然 avg query tokens 降到 `5186.944`，但 accuracy 退步，不能作为 LTS 候选。
- clean 侧：所有 route 和 compiler 只能来自 question text、question_time、原始对话和 memory metadata；不能使用 LoCoMo category、LongMemEval question_type、evidence label、gold 或 judge。
