# v62 Dialogue Episode Fact Compiler 计划

## 目标

v42 在 LongMemEval-S full 上为当前主线参照：DeepSeek judge accuracy `387/500 = 0.774`，avg build tokens `80346.246`，avg query tokens `5865.644`。离线 badcase 显示，v42 的 113 个错误中有 34 个短答案错误的 gold 字符串已经出现在 Memory Context，28 个错误是拒答式输出。典型问题是已召回同一会话相邻 user/assistant turn，但 answer 把它们当成孤立行，没有读成一个对话 exchange。

v62 目标是解决 `fact_lookup` 中“已召回但没有合并相邻对话信息”的错误，同时不增加 build token、retrieval token 或额外 LLM 调用。

## 外部方法依据

- creating001-agent-memory：`baseline/chunking.py` 和 `baseline/context.py` 中的 turn-pair chunk 与 source-turn materialization 说明，对话问答里 user turn 与紧随的 assistant turn 常常共同构成可回答 episode。只借鉴通用 context organization，不迁移其不 clean 的 answer/category/sample 逻辑。
- MemoryBank：`local_doc_qa.py` 会按相同 source/date 合并邻近片段，说明邻接上下文对长期对话检索有价值；本项目不采用 summary/personality 作为唯一事实源。
- MemU：staged retrieval 与 sufficiency 思路强调 query 侧应该先把 memory 组织成可判断的信息单元；v62 只采用轻量 compiler 组织，不引入额外 LLM sufficiency loop，避免 query token 超预算。

## 方法

- 新增 `compiler.context_layout = dialogue_episode`。
- 默认关闭；v62 只通过 `compiler.route_overrides.fact_lookup` 开启。
- 对已经进入 Memory Context 的 raw evidence rows，按 `session_id` 和连续 `turn_index` 合并成 `Dialogue Episode` block。
- 不扩大检索范围，不读取 labels/judge/gold/sample id，不使用 benchmark question_type/category。
- 对 `fact_lookup` 同时开启已有 `dialogue_inference_contract`，允许 same-session neighboring turns 在同一 ongoing exchange 中共同解析省略 slot。

## 诊断口径

先跑 LongMemEval-S 中由当前 clean router 判定为 `fact_lookup` 的全量 183 条。子集选择只使用 question text 和当前 router，不使用 gold、judge、question_type、sample id 或 row index。

成功门槛：

- v62 same183 DeepSeek judge accuracy 相比 v42 same183 至少 `+3` correct。
- v42 已正确的 fact_lookup 样本回归不能超过新增收益。
- avg query tokens 保持 `<= 6000`，若超过则不作为主线。
- avg build tokens 按冷 build 逻辑成本计入，即使 build cache 全命中也记录 cached usage。

如果 fact_lookup 183 通过，再跑 LongMemEval-S full；否则删除顶层候选配置，只保留诊断 snapshot。
