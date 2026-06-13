# v38 Route-Scoped Snippet Top60 Planning

## 背景

当前 LongMemEval-S 最好结果仍是 v36：

- accuracy: `0.772`
- correct: `386/500`
- avg build tokens: `80346.246`
- avg query tokens: `5715.468`
- 距 `0.80` baseline target 还差 `14` correct

v37 row-linked build memory bundle 已证明负向：

- accuracy: `0.744`
- delta_vs_v36: `-14`
- evidence_recall: `1.0`
- 主要回退在 `temporal_lookup`、`list_count`、`current_state`

v37 regression 显示 raw rows 基本仍在 context，但 typed memory 进入 prompt 后会把局部事实显著化，导致 reader 抓住不完整或相邻错误事实。因此下一步不继续增加 answer prompt 中的 typed memory。

## 方法设计

新增 `configs/stage1_route_snippet_top60_v38_cached.json`。

核心思路：

- 保持 v36 的 build memory、answer format guard、evidence_report contract 和 top40 主体不变。
- 只对 question-text route 得出的 `list_count` 和 `temporal_lookup` 扩大 raw retrieval 到 top60。
- 对这两个 route 使用 `role_query_snippet`，长 assistant row 截为 query-focused snippet，长 user row 允许更宽预算。
- typed memory 仍只通过 build-memory BM25 回链 raw source turns，不作为 answer prompt 中的独立 fact view。
- fact_lookup、current_state、profile_preference 保持 v36 top40/full row，避免 v37 在 current_state 和相邻事实上出现的噪声。

这不是 benchmark label 规则：`information_need` 只来自问题文本和可见 question_time，不来自 LongMemEval question_type、LoCoMo category、gold、judge 或 sample id。

## 外部代码借鉴和取舍

- `external/creating001-agent-memory/src/agent_memory/baseline/context.py`：参考先扩大/回链 source turns，再 materialize 为 raw context 的思路；不迁移 financial sum、target phrase 或任何 benchmark/task-specific guardrail。
- `external/creating001-agent-memory/src/agent_memory/prompts/retrieve.py`：参考 count/list/temporal 需要保留 operands 和 close-but-wrong candidates；v38 不增加 LLM reranker，避免 query token 超预算。
- `external/SimpleMem/simplemem/core/hybrid_retriever.py`：参考 semantic/lexical/structured 多视角召回；v38 只做轻量 route-scoped raw retrieval expansion，不引入额外 LLM planner。
- `external/EverOS/src/everos/memory/search/hierarchy.py`：参考 atomic fact child -> episode parent 的层级回链；v38 继续把 build memory 用作 source expansion，而不是直接让 typed fact 回答。
- `external/ACON/src/productive_agents/ctxopt/history_optimizer.py` 和 LCM 思路：参考 query-focused context compression；v38 用 deterministic snippet 压缩，而不是 summary 替代 raw evidence。

## 预期收益

- `list_count`：top60 更可能覆盖全部 operands；snippet 压缩降低 token 风险。
- `temporal_lookup`：top60 更可能覆盖起点/终点/相邻时间窗口；Temporal Aid 和 evidence_report 继续负责读证。
- `multi-session`：更多 source rows 进入 context，缓解 v36 badcase 中跨 session 聚合漏项。

## 主要风险

- top60 可能引入更多相似噪声，尤其 temporal route 可能被旧事实或相邻事件干扰。
- `role_query_snippet` 可能截掉长 row 中远离 question terms 的答案，特别是 assistant 列表里答案项与问题词距离较远时。
- LME v36 avg query tokens 已接近 6K；必须先做 route-stratified token gate，不能直接跑 full。

## Gate 计划

先跑 LongMemEval-S route-stratified no-label diagnostic gate：

- input: `outputs/diagnostic/v35_lme_route_stratified_probe/prediction_input.jsonl`
- config: `configs/stage1_route_snippet_top60_v38_cached.json`
- samples: `20`
- 检查 avg query tokens 是否 `<= 6000`
- 检查 answer max input/output 是否 `131072/16384`
- 检查 `list_count` / `temporal_lookup` 是否实际 top60，其它 routes 是否保持 top40
- 检查 build tokens 仍按 logical cold-build usage 统计

如果 gate 失败，不跑 full。如果 gate 通过，再跑 LongMemEval-S full；LoCoMo 只有在 LME 不明显负向后再安排。

## Clean 边界

- Prediction 阶段不读取 gold answer、judge output、benchmark label、question_type、category、sample id、row index、qid、test feedback 或样本级规则。
- Route override 只使用 generic `information_need`。
- `role_query_snippet` 只根据 question terms 从当前 raw row 中截取片段，不引入外部答案或 label。
- DeepSeek judge、evidence recall 和 badcase 只用于离线诊断。
