# stage1_rerank_context_v103 诊断计划

## 目的

验证一个 query-side 候选：在 v102 的 clean build memory 基础上，保留 BM25+dense+build-memory-source 的 60 条候选池，但用 `Qwen/Qwen3-Reranker-0.6B` 重排并把最终 raw evidence context 控制到约 32-40 条，减少上下文噪声。

## 设计依据

- Hindsight：semantic / BM25 / graph / temporal 多路 recall 后做 RRF 和 cross-encoder rerank，再按 token budget 裁剪。
- EverOS：episode / atomic fact / profile 分层，候选 metadata 和 parent provenance 用来组织最终上下文。
- MemOS：检索后过滤短文本/近重复 memory，再 rerank；对话文档在 rerank 前做清晰格式化。
- 本项目历史诊断：v101 的 source-anchor/candidate-guide 在 LoCoMo stratified 200 上负向，说明“更多候选/更宽覆盖”会带来噪声；v37 的 typed memory 直接入 prompt 也负向，所以 v103 不把 build memory 当独立事实源。

## 配置

- config: `configs/stage1_rerank_context_v103_qwen36_no_think_build4k_cached.json`
- answer/build model: `Qwen/Qwen3.6-35B-A3B` no-thinking
- embedding: `Qwen/Qwen3-Embedding-0.6B`
- rerank: `Qwen/Qwen3-Reranker-0.6B` at `http://127.0.0.1:8002/v1`
- build cache: 复用 v102 qwen36 build4k cache，cache hit 仍按冷启动逻辑计入 build tokens
- answer cache: 新 namespace，不能复用 v102 answer

## Clean 边界

- 不使用 gold answer、judge output、benchmark label、sample id、row index、test feedback 或样本级规则。
- Rerank 只看 question、question_time 和 prediction-time retrieved raw turns。
- Build-memory source alignment 是 question-independent provenance repair，只看 build memory text 和同一 session 附近 raw turns。

## 预期观察

- 主要指标：dual judge strict/lenient accuracy。
- 成本指标：avg_build_tokens、avg_query_tokens、avg_rerank_tokens_when_applied、avg_context_chars。
- 诊断指标：rerank_applied_rate、avg_rerank_candidate_count、avg_rerank_returned_count、avg_compiled_evidence_items、evidence recall、按 LoCoMo category / LME question type 的正确率。
- 若 query tokens 明显下降但 accuracy 下降，说明当前模型依赖宽上下文兜底；若 accuracy 上升或持平且 token 降低，再继续做 rerank top-k/anchor 消融。
