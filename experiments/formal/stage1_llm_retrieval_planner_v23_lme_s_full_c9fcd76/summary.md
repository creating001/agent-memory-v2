# stage1_llm_retrieval_planner_v23_lme_s_full_c9fcd76

## 目的

验证 v18 hybrid BM25+dense 主线之上的 query-side LLM retrieval planner 是否能在 clean setting 下提升 LongMemEval-S full accuracy。planner 只读取 question、question_time 和 question-text router 产生的 clean route，不读取 gold、judge、benchmark label、sample id、qid、row index 或测试反馈。

## 方法

- 基线：`configs/stage1_hybrid_bm25_v18_cached.json`
- 本轮配置：`configs/stage1_llm_retrieval_planner_v23_cached.json`
- 改动：本地 Qwen 在检索前生成通用补充查询，原问题检索结果继续保护；补充查询参与 BM25、dense 和 build-memory source expansion 的 RRF 融合。
- 借鉴：SimpleMem 的 intent-aware retrieval planning、xMemory/Hindsight 的多视角检索、外部 naive RAG 的多查询思路。
- 取舍：planner 不直接回答，不写 benchmark/sample 规则；所有最终证据仍来自 raw Memory Context。

## 范围

- benchmark：LongMemEval-S
- subset：full
- samples：500
- workers：8
- answer model：`Qwen/Qwen3-30B-A3B-Instruct-2507`
- answer max input：131072
- answer max output：16384
- judge：`deepseek-v4-flash`

## Git

- prediction commit：`c9fcd76e322942af89c14315bc964cad4d3d1407`
- prediction dirty：false
- judge/evidence recall 为 prediction 后离线诊断，不进入预测链路。

## 主指标

- DeepSeek judge accuracy：0.716, 358/500
- v18 baseline accuracy：0.732, 366/500
- 相对 v18：fixed 15, hurt 23, net -8
- 结论：v23 为负向消融，不跑 LoCoMo full，不作为主线配置保留。

## 分题型

| type | v18 | v23 | delta |
|---|---:|---:|---:|
| knowledge-update | 64/78 | 58/78 | -6 |
| multi-session | 74/133 | 74/133 | 0 |
| single-session-assistant | 52/56 | 53/56 | +1 |
| single-session-preference | 11/30 | 11/30 | 0 |
| single-session-user | 66/70 | 64/70 | -2 |
| temporal-reasoning | 99/133 | 98/133 | -1 |

## Token 成本

- avg_build_tokens：80346.246
- total_build_tokens：40173123
- build token 口径：逻辑 cold-build LLM tokens；cache hit 仍按 cached usage 计入 build tokens。
- avg_query_tokens：5360.726
- total_query_tokens：2680363
- query planner avg tokens：245.218
- query planner avg queries：1.344
- query planner cache：hits 0, misses 500, writes 500
- avg_embedding_tokens：15.958
- judge total_tokens：117922

## 诊断

- evidence recall：1.0，说明主要问题不是 gold evidence 是否进入 context，而是 planner 引入的检索排序和 answer 使用收益不足。
- 340/500 个样本 planner 只保留原问题，153/500 生成 2 个查询，7/500 生成 3 到 4 个查询。
- hurt 样本集中出现在 knowledge-update；多查询没有带来 multi-session 净提升。
- 增加 245 avg query tokens 后 accuracy 下降，不满足“性能优先且预算内有效提升”的要求。

## 输出

- predictions：`outputs/formal/stage1_llm_retrieval_planner_v23_lme_s_full_c9fcd76/predictions.jsonl`
- traces：`outputs/formal/stage1_llm_retrieval_planner_v23_lme_s_full_c9fcd76/traces.jsonl`
- metrics：`experiments/formal/stage1_llm_retrieval_planner_v23_lme_s_full_c9fcd76/metrics.json`
- manifest：`experiments/formal/stage1_llm_retrieval_planner_v23_lme_s_full_c9fcd76/manifest.json`
- evidence recall：`experiments/formal/stage1_llm_retrieval_planner_v23_lme_s_full_c9fcd76/evidence_recall.json`
- judge：`experiments/formal/stage1_llm_retrieval_planner_v23_lme_s_full_c9fcd76/deepseek_judge.json`

## 下一步

- 不继续沿用 v23 的“每题 LLM planner”作为主线。
- 下一轮应优先分析 knowledge-update 和 single-session-user 的 v18/v23 hurt cases，寻找 general 的 build-stage memory management 或 evidence compiler 改进。
- 若再次尝试 query planning，应避免每题额外 LLM 调用，只考虑可验证的低成本 query expansion 或 answer-side evidence arbitration。
