# 外部方法覆盖与当前设计索引

本文件是当前 Agent Memory 方法探索的本地外部代码索引。它服务于新的 goal：构建一个通用、clean、系统化、可消融、可持续迭代，并且有方法创新性的 Agent Memory 框架。这里记录“哪些外部代码/方法可以作为设计依据、能借鉴什么、必须舍弃什么”，不改变 `docs/clean_protocol.md`。

## 使用原则

- 标为“已读代码”的方法，才可以作为方案或实验记录里的明确设计依据。
- 标为“已 clone，待读”的方法，只说明本地已有入口；不能声称已经吸收其实现细节。
- 外部方法只借鉴通用机制，不能迁移 gold answer、judge output、benchmark 标签、sample id、question_type、category、answer_session_ids、test feedback、样本级规则或 benchmark 专门 prompt。
- 任何 summary、profile、semantic memory、graph edge、reflection、skill 都不能替代 raw evidence。它们可以做 build organization、retrieval activation、context planning、verify/audit signal；最终答案仍必须回到 raw Memory rows。
- 如果外部方法有物理 delete、summary-only、LLM 自由改写事实、基于反馈写 memory 等机制，在本项目中必须改成 source-backed、non-destructive、可审计版本，或只作负面参考。

## 当前方法目标

当前重启线从 v288 LTS 出发。最重要的探索点不是再堆 query-time 规则，而是把 build 阶段做成真正的 Agent Memory system：

- **Memory objects**：event、fact、profile、preference、state、relationship、plan 等对象不只是 retrieval hint，需要带 source、time、subject/predicate/value、status、confidence、namespace/tier。
- **Memory layers**：short-term / working / long-term / archival / quarantine 的分层要成为 build artifact 和 query policy 的一部分。
- **Memory operations**：create、update、merge、supersede、retrieve、expand、verify、audit、context_pack 要有明确契约；DELETE 默认改为 non-destructive supersede/archival。
- **Source-backed workspace**：build 侧输出统一 workspace manifest，让 query 侧只做 activation、source expansion、context organization 和 answer verification；derived memory 不能直接作为最终事实。
- **Query 简化**：query 侧逐步从多个窄 guide 收敛成更少、更通用的 workspace plan / evidence compiler，减少 benchmark-shaped patch 和 query tokens。
- **实验口径**：候选/LTS 结论必须报告 full dual judge accuracy strict/lenient、avg build tokens、avg query tokens。full 口径可以全量 judge，也可以 changed-output judge + 未变样本继承后合并。

## 可迁移共识

### Build-Side Memory System

- `external/xMemory`：semantic/episodic 双通道、semantic -> source episode 回链、hierarchy/theme/semantic KNN 的组织思想值得参考。采用点：derived object 必须能 expand 到原始 episode/source rows；舍弃点：复杂 entropy/IG search 暂不直接进入主线，评测脚本中的 gold/judge 只作负面边界。
- `external/EverOS`：episode、atomic fact、profile、parent provenance、fact-child -> episode-parent retrieval、候选 shaper 很贴合当前目标。采用点：build artifact 区分 raw episode、atomic fact、profile/derived view，并保留 parent/source 回链；舍弃点：重型服务和非必要后台调度暂不迁移。
- `external/SimpleMem`：lossless typed memory、多视角 retrieval、structured context。采用点：typed memory 作为 source-backed index 和 context planner；舍弃点：压缩 memory 不能成为唯一事实源。
- `external/nemori`：buffer -> episode -> semantic memory、episode/semantic 双通道 search、source_messages 回链、episode merge。采用点：episode/semantic 分层和 source_messages provenance；舍弃点：prediction-correction semantic delta 不能用 benchmark answer/feedback。
- `external/mem0`：memory add/search、metadata scope、filter、lifecycle API。采用点：统一 memory operation API 思想；舍弃点：物理 DELETE 在本项目中改为 supersede/archival。
- `external/memanto`：memory taxonomy、namespace/filter、as-of、superseded、TTL 查询。采用点：非破坏性 temporal versioning 和 current/as-of 视图；舍弃点：外部 DB 依赖和不可审计压缩。
- `external/MemoryOS`、`external/letta`：short/mid/long-term、core/archival/recall memory、context window accounting。采用点：memory tiers 和上下文预算；舍弃点：完整 Memory OS 依赖暂不引入。
- `external/graphiti`：temporal/provenance schema，尤其 valid/invalid time 与 episode provenance。采用点：valid_from/valid_to、invalidated/superseded chain、source episode ids；舍弃点：LLM 过度推断 graph edge。
- `external/MIRIX`：episodic/semantic/core/procedural/resource memory taxonomy，episodic event schema。采用点：多类 memory object 的 schema 思维；舍弃点：数据库/服务层复杂度暂不迁移。
- `external/MemOS`：LongTerm/User memory 双通道、过滤近重复后 rerank、dialogue pair 文档格式。采用点：memory channel separation 和 clean rerank/document shaping；舍弃点：LLM rerank 和重型 scheduler 不进短期主线。

### Query / Retrieval / Context Organization

- `external/hindsight`：semantic/BM25/graph/temporal 四路 recall、per-source cap、RRF/interleave、rerank、token budget 裁剪。采用点：多路候选池和预算内 context selection；风险：rerank 降 token 不能牺牲 full accuracy。
- `external/HippoRAG`：fact/entity -> passage/raw chunk 回链、PPR/graph recall、dense fallback。采用点：graph/typed view 只做 recall expansion，最终回 raw rows；舍弃点：gold_docs/gold_answers 评测入口和 demo filter。
- `external/Mnemis`：hierarchical top-down selection、selected node 到 one-hop episode/relation 回链。采用点：层级选择和 source expansion；舍弃点：无 source 的 graph relation 不作为证据。
- `external/MAMGA`：multi-graph、RRF、temporal parser。采用点：temporal graph/RRF/relative time 的通用思路；舍弃点：session id 或 dataset keyword 映射。
- `external/memU`：profile/event/knowledge/behavior 类型拆分、staged retrieval、sufficiency check。采用点：memory-type gating 和不足时追加检索的通用框架；舍弃点：任何 category、judger、gold 相关逻辑。
- `external/creating001-agent-memory`：evidence-first query 组织、turn-pair/source-turn materialization、adjacent context window、时间题区分 memory date/event date。采用点：raw evidence materialization 和 reader discipline；舍弃点：target phrase、final answer、category、sample 规则、benchmark 对齐 guardrail。
- `external/LongMemEval`、`external/LoCoMo`：官方/基准 RAG prompt 可作为评估边界和 reader discipline 参考。`has_answer`、`answer_session_ids`、`question_type`、`category`、answer choices 均不能进 prediction。

### Context Compression / Procedural Memory

- `external/ACON`：structured history compression / resume。采用点：保留错误、决策、未解决槽位的结构化上下文；限制：summary 不能替代 raw evidence。
- `external/general-agentic-memory`：memory tree、directory summary、batch memorize/organize。采用点：层级组织和导航；限制：文件系统式 memory OS 先不迁移。
- `external/DeepResearch`：iterative evidence extraction / resummary。采用点：不足时的通用 iterative retrieve-read-audit 思想；限制：query token 成本要受控。
- `external/Memento`、`external/Memento-Skills`、`external/ReMe`、`external/buffer-of-thought-llm`：只可参考通用 procedural strategy，不能写入具体测试实体、答案、judge feedback 或失败样本规则。

### Negative / Boundary References

- `external/A-mem/test_advanced.py`：存在 benchmark category/answer 进入 answer 的不 clean 风险，只做负面边界和高层 memory neighborhood 参考。
- `external/MIA`：大量 correct/incorrect feedback、judge/gold 相关逻辑，只作负面边界；不能迁移到 prediction。
- `external/MemMachine/evaluation/*`：question_type、answer、answer_session_ids、has_answer 等评测字段只可用于评测格式理解，不能进入方法。
- 官方 LongMemEval / LoCoMo evaluation 代码中的 hidden labels、answer choices、category、question_type 只能用于 offline evaluation 或负面边界。

## 当前 v291 设计映射

v291 当前 LTS 目标是把 v288-v290 的 build manifests 收敛成更像 Agent Memory system 的 build-owned operation layer，而不是马上用 query prompt 替换已验证路径：

- 借鉴 xMemory / EverOS / Nemori：derived memory 必须有 source episode/source row 回链；`memory_operation_plan_v1` 的 retrieve/expand/verify 都要求回到 raw Memory rows。
- 借鉴 Mem0 / Memanto / Graphiti：把 update/delete 思想改成 non-destructive supersede、archival、current/historical/as-of view 和 provenance audit。
- 借鉴 MemoryOS / Letta / MIRIX：把 working/long-term/archival/quarantine 层次、多类 memory object、slot-level state management 放入 build artifact。
- 借鉴 MemOS / Hindsight / Mnemis：保留 source expansion、context_pack、audit、candidate organization 思想，但 v291 不直接把 compact workspace plan 放进 query prompt，避免 v289 的 accuracy 回退。
- 本项目自己的取舍：raw evidence 永远是 final authority；operation plan 先作为 source-backed state management、conflict handling、context organization 和 answer verification contract，后续 query 消费必须 guarded/additive、可消融、可回滚。

## 51 项覆盖索引

| # | 方法 | 本地代码入口 | 当前状态 | 当前取舍 |
|---:|---|---|---|---|
| 1 | A-MEM | `external/A-mem` | 已读部分代码 | 高层 neighborhood 可参考；不 clean answer/category 逻辑禁用。 |
| 2 | ACON | `external/ACON` | 已读核心 context optimizer | 参考结构化 compression/resume；summary 不替代 raw evidence。 |
| 3 | Acontext | `external/Acontext` | 已 clone，待读 | 可后续看 context/memory SDK 边界。 |
| 4 | agentmemory | `external/agentmemory` | 已读 search/reflect 入口 | 参考 scope、BM25/vector、token budget；reflection 只作组织思想。 |
| 5 | xMemory | `external/xMemory` | 已读核心 LoCoMo search/framework | 重点参考 episodic/semantic 双通道、source episode 回链、hierarchy expansion。 |
| 6 | Buffer of Thoughts | `external/buffer-of-thought-llm` | 已 clone，待读 | 只可能参考 procedural strategy。 |
| 7 | ChatHaruhi | `external/Chat-Haruhi-Suzumiya` | 已 clone，待读 | 可后续参考角色长期对话组织。 |
| 8 | LoCoMo | `external/LoCoMo` | 已读 RAG/eval prompt | 只参考 dialogue reader discipline；category/answer 禁用。 |
| 9 | EverOS | `external/EverOS` | 已读 memory/search/strategy | 重点参考 episode/atomic fact/profile、parent provenance、hierarchy retrieval。 |
| 10 | Everything is Context | `external/aigne-framework` | 已 clone，待读 | 可后续参考 context abstraction。 |
| 11 | HippoRAG2 | `external/HippoRAG` | 已读核心 retrieval/rerank | 参考 fact/entity -> raw passage 回链；gold eval 入口禁用。 |
| 12 | gbrain | `external/gbrain` | 已 clone，待读 | 可后续参考 personal graph memory。 |
| 13 | General Agentic Memory | `external/general-agentic-memory` | 已读 tree/node/prompts | 参考层级 memory tree 和 organize；不引入完整 FS memory OS。 |
| 14 | Generative Agents | `external/generative_agents` | 已 clone，待读 | 可后续参考 reflection/importance/recency。 |
| 15 | LD-Agent | `external/LD-Agent` | 已读 EventMemory/Personas | 参考 event/profile 双通道、recency；profile 不覆盖 raw evidence。 |
| 16 | Hindsight | `external/hindsight` | 已读 recall/rerank | 参考多路 recall、fusion、budget 裁剪；accuracy 回退则不主线化。 |
| 17 | HippoRAG | `external/HippoRAG` | 已读核心 retrieval/rerank | 同 #11，图只做 recall expansion。 |
| 18 | Honcho | `external/honcho` | 已 clone，待读 | 可后续参考 production API/session state。 |
| 19 | EM-LLM | `external/EM-LLM-model` | 已 clone，待读 | 可后续参考 episodic boundary。 |
| 20 | HyperMem | `external/EverOS` | 已 clone，待读具体实现 | 可后续参考 hypergraph，但必须 source-backed。 |
| 21 | IterResearch | `external/DeepResearch` | 已读 WebResummer prompt | 参考 iterative evidence extraction；query token 要受控。 |
| 22 | LangMem | `external/langmem` | 已读 profile guide | 参考 profile schema/namespace/update；不能覆盖 raw evidence。 |
| 23 | LCM | `external/lossless-claw` | 已 clone，待读 | 可后续参考 lossless context management。 |
| 24 | LightMem | `external/LightMem` | 已读 memory layer retrieval | 参考 search wrapper/metadata/used_content；不引入外部 backend。 |
| 25 | LongMemEval | `external/LongMemEval` | 已读 retrieval/generation | 参考 prompt/round expansion；hidden fields 禁用。 |
| 26 | MAGMA | `external/MAMGA` | 已读 builder/query/temporal | 参考 multi-graph/RRF/temporal parser；dataset keyword 禁用。 |
| 27 | Mem0 | `external/mem0`、`external/TeleMem` | 已读 mem0 main | 参考 add/search/filter/lifecycle；delete 改 supersede。 |
| 28 | Mem9 | `external/mem9` | 已 clone，待读 | 可后续参考 memory SDK/API。 |
| 29 | Memanto | `external/memanto` | 已读 parsing/read/write | 参考 taxonomy、namespace、as-of/superseded/TTL。 |
| 30 | Memary | `external/Memary` | 已读 entity store | 参考 entity/count/date 聚合；固定 entity 规则禁用。 |
| 31 | MemClaw | `external/caura-memclaw` | 已 clone，待读 | 可后续参考 governed lifecycle。 |
| 32 | Memento 2 | `external/Memento` | 已 clone，待读 | 只可参考通用 reflective memory。 |
| 33 | Memento-Skills | `external/Memento-Skills` | 已 clone，待读 | 只可沉淀通用 procedural skill。 |
| 34 | MemGPT / Letta | `external/letta` | 已读 memory schema | 参考 core/archival/recall memory、context accounting。 |
| 35 | Memlayer | `external/memlayer` | 已 clone，待读 | 可后续参考 SDK abstraction。 |
| 36 | MemMachine | `external/MemMachine` | 已读评测模型入口 | 只作负面边界；answer/session 标注禁用。 |
| 37 | Memobase | `external/memobase` | 已读 event docs | 参考 event tags/profile delta/created time。 |
| 38 | Memori | `external/Memori` | 已 clone，待读 | 可后续参考 production memory API。 |
| 39 | MIA | `external/MIA` | 已读部分 serve/inference | 多数 feedback/gold 相关，作为负面边界。 |
| 40 | MemoryOS | `external/MemoryOS` | 已读 retriever/updater/prompts | 参考 short/mid/long-term、user/assistant 双通道。 |
| 41 | MemoryBank | `external/MemoryBank-SiliconFriend` | 已读 retrieval/summarize | 参考 date history、same-source/date expansion；summary 不替代原文。 |
| 42 | MemOS | `external/MemOS` | 已读 search/rerank | 参考 LongTerm/User 双通道、近重复过滤、dialogue pair 文档。 |
| 43 | MemU | `external/memU` | 已读 retrieve/prompts | 参考 memory-type gating、staged retrieval、sufficiency。 |
| 44 | MIRIX | `external/MIRIX` | 已读 episodic schema | 参考多类 memory taxonomy 和 event schema。 |
| 45 | Mnemis | `external/Mnemis` | 已读 selector/prompts | 参考 hierarchy selection 和 node -> episode/relation 回链。 |
| 46 | Nemori | `external/nemori` | 已读 core/search/generator | 参考 episode/semantic 双通道、source_messages、merge。 |
| 47 | OpenMemory | `external/openmemory` | 已 clone，待读 | 可后续参考 local memory service/API。 |
| 48 | Cognee | `external/cognee` | 已 clone，待读 | 可后续参考 KG-LLM interface，必须 raw evidence 回链。 |
| 49 | ReMe | `external/ReMe` | 已 clone，待读 | 只可参考通用 procedural reflection。 |
| 50 | SimpleMem | `external/SimpleMem` | 已读 builder/retriever/answer | 参考 typed memory、多视角 retrieval、structured context。 |
| 51 | Zep / Graphiti | `external/graphiti` | 已读 temporal edge prompt | 参考 valid/invalid time、episode provenance。 |

## 下一步调研补洞

- 优先补读 `external/Acontext`、`external/honcho`、`external/openmemory`、`external/cognee`、`external/caura-memclaw`，重点看 production memory API、governance、audit 和 KG interface，而不是 benchmark trick。
- 对已读方法补一个 build-side ablation matrix：object taxonomy、workspace lifecycle、source expansion、hierarchy/episode parent、current/as-of view、query workspace plan。
- 任何新机制进入候选表前，必须在实验记录写明参考来源、采用点、舍弃点、clean 风险和 full 口径指标。
