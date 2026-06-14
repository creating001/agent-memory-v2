# v58 rerank candidate planning

## 目的

v56 说明 build 侧更细粒度抽取没有自动转化为 accuracy；v57 说明继续增加 answer checklist 会改变答案但不净增正确率，并把 query token 推到 6K 以上。v58 改到 retrieval precision：扩大 clean 候选池，再用本地 reranker 重排，最终仍只给 answer model top-40 raw evidence。

## 外部方法参考

- creating001-agent-memory：参考 dedicated rerank 和 anchor retention。采用“候选池扩大 + reranker + 保留原始高 rank anchor”的通用机制；不迁移它的 factual-slot 手写 gate、target phrase、benchmark category、sample/id、gold/judge 或测试反馈逻辑。
- HippoRAG：参考 fact/entity/passage 检索后必须回链 raw passage，并用 dense passage 兜底。v58 不引入 DSPy/LLM rerank filter，也不读取 gold_docs/gold_answers。
- EverOS/SimpleMem/xMemory：参考 derived memory 只做 raw source activation/reranking signal，最终答案回到 raw episode/turn。

## 设计

- 底座：v42 `stage1_operation_workpad_v42_cached`。
- 候选池：BM25 + dense + build-memory source links 融合候选扩大到 `pool_k=80`。
- rerank：`Qwen/Qwen3-Reranker-0.6B` 本地服务，`document_max_chars=900`，`batch_size=16`。
- anchor retention：先保留 rerank top-8，再插入原始 retrieval top-8，随后接 rerank 余量，最终 top-40 进入 compiler。
- token 口径：rerank token 单独报告，不混入 `avg_build_tokens` / `avg_query_tokens`；answer prompt 仍是 top-40 raw evidence，目标是不增加 answer LLM query token。

## Clean 边界

- prediction 只使用 question、question_time、raw dialogue、typed memory source links 和 runtime route。
- 不使用 gold answer、judge output、question_type/category、sample id、row index、test feedback 或样本级规则。
- rerank 服务只对候选 raw turn 文本打相关性分，不生成答案，不读取离线评测结果。

## 预期与 gate

- 主要预期：提高 weak_route/current_state/temporal 中“证据在候选池但被噪声压制”的样例。
- 已知风险：reranker 可能把 list/count 的多操作数证据排窄，或对 profile/preference 的 personalized context 不稳定。
- diagnostic gate：先跑 LongMemEval-S `weak_route_87`，必须相对 v42 same87 净增 accuracy，且 `avg_query_tokens <= 6000`、`avg_build_tokens` 不变、rerank trace 完整；否则不跑 full。
