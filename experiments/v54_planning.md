# v54 turn-window retrieval 规划

## 背景

当前 LongMemEval-S 最好结果是 v42 full：DeepSeek judge accuracy `387/500 = 0.774`。离线 badcase 诊断显示，很多错误不是目标会话完全没召回，而是 answer 阶段没有稳定使用相邻 turn 中的槽位、补充说明或局部上下文。典型问题包括 coupon/store 这类同一局部片段跨 user/assistant turn 才完整表达，以及金额/列表候选分散在同一会话邻近片段中。

v43-v46 的 session-thread prompt 方向有局部正向但 token 风险明显；v47-v53 的 reader-side schema / scoped evidence / repair 方向在诊断或 full 上不稳定。因此 v54 先不继续加长 answer prompt，而是把局部连续性前移到 retrieval。

## 外部参考

- `external/creating001-agent-memory/src/agent_memory/baseline/context.py`：参考其 turn-pair 检索文档和 `source_turns` 回投影思想；舍弃 strategy-specific 和样本/题型规则。
- `external/SimpleMem/simplemem/core/memory_builder.py`：参考 sliding window / overlap 保留局部上下文的思想；本阶段不引入其完整 build-side extractor。
- `external/xMemory/src/search/unified_search.py` 与 xMemory 的 original-message 回链思想：参考“先用聚合/窗口视图召回，再回到原始消息回答”的边界；本阶段不引入重型图或持久向量库。
- `docs/method.md` / `docs/method_cards.md` 中 MemMachine、Graphiti/Zep、xMemory 的 episode/neighbor/provenance 思路：采用邻域召回和 provenance，舍弃 benchmark-specific routing 和 graph DB 依赖。

## 方法

新增 `retrieval.turn_window_bm25`：

- 对每个 raw turn 构建前后相邻窗口文档，默认 `window_before=1`、`window_after=1`。
- window 文档只用于 BM25 检索，不直接进入 answer prompt。
- 命中 window 后投影回原始 `source_id`，与 lexical raw turn、dense raw turn、build-memory source hits 做 RRF。
- prompt 仍只包含原始 raw evidence rows；不开启 summary-only 或 judge/verifier 反馈。
- 配置关闭时与 v42 行为等价，可做 clean ablation。

v54 配置在 v42 上只改 retrieval：

- 开启 `turn_window_bm25.top_k=24`，每个 window 最多投影 3 个原始 source turn。
- dense `protect_top_n` 从 32 收到 28，让 window/lexical/build-memory 融合结果有少量进入 top40 的空间。
- `max_evidence_items=40`、`max_evidence_chars=18000`、answer max input/output `131072/16384` 保持不变。

## Clean 边界

- 预测阶段只使用 question、question_time、raw dialogue、visible turn metadata 和 build-stage memory。
- 不使用 gold answer、judge output、benchmark 标签、sample id、row index、offline feedback 或样本级规则。
- 信息需求 route 只来自 question-derived heuristic/analysis，不读取 benchmark label。
- DeepSeek judge 只在 prediction 完成后离线使用。

## Gate 计划

1. 单元测试和 `git diff --check` 必须通过。
2. 先跑 LongMemEval-S 诊断，不直接消耗 full。优先使用 question-derived / route-stratified 子集或既有诊断子集，只作为是否值得 full 的 gate。
3. 记录 commit、dirty 状态、配置、benchmark/subset、token 成本、cache、outputs 路径。
4. 若 same-subset DeepSeek judge 不高于 v42，或 avg query tokens 明显超过 6K，不跑 full。
5. 若诊断正向且 token 合格，再跑 LongMemEval-S full；LoCoMo 只在 LME 不负向或该机制明显适合 LoCoMo badcase 后推进。

## 预期

目标不是靠更多 prompt token 换分，而是在固定 top40 evidence budget 中更好激活同一局部事件的完整原始 turn。预期主要影响 `fact_lookup`、`current_state`、局部 temporal/list 边界错误；不预期解决 answer 阶段复杂算术和全局去重问题。
