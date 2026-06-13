# Diagnosis: stage1_llm_retrieval_planner_v23_lme_s_full_c9fcd76

## 结论

v23 LLM retrieval planner 是负向消融：LongMemEval-S full 从 v18 的 0.732 降到 0.716，净 -8。该方法 clean、token 未超预算，但没有带来 accuracy 收益，因此不进入主线，不跑 LoCoMo full。

## 关键指标

- n_samples：500
- judge accuracy：0.716, 358/500
- judge invalid：0
- vs v18：fixed 15, hurt 23, net -8
- evidence recall：1.0
- avg_build_tokens：80346.246
- avg_query_tokens：5360.726
- avg_query_planner_tokens：245.218
- avg_query_planner_queries：1.344
- build cache：hits 3341, misses 0, writes 0
- planner cache：hits 0, misses 500, writes 500

## 分题型诊断

- knowledge-update：64/78 -> 58/78，主要损失来源。
- multi-session：74/133 -> 74/133，没有改善。
- single-session-assistant：52/56 -> 53/56，小幅提升但不足以抵消损失。
- single-session-user：66/70 -> 64/70，有退化。
- temporal-reasoning：99/133 -> 98/133，基本持平偏负。
- preference：11/30 -> 11/30，无改善。

## 机制判断

- planner 只看到 clean 输入，未发现 gold/judge/benchmark label/sample id 泄漏。
- 500 条中 340 条只保留原问题，说明 LLM planner 大量时候没有生成有效补充查询，但仍增加平均 245 query tokens。
- 153 条生成 2 个查询，7 条生成 3 到 4 个查询；多查询没有带来 multi-session 或 knowledge-update 正收益。
- evidence recall 为 1.0，问题更可能在证据排序、context 组织或 answer 使用，而不是是否能召回 gold evidence。
- v23 让 dense/BM25/source-expansion 多查询 RRF 介入排序，原问题 dense top 受到保护，但补充查询仍可能改变后续 evidence ordering，knowledge-update 对排序噪声更敏感。

## 处置

- v23 配置和代码不作为主线保留。
- formal 记录保留用于追溯，输出路径见 `summary.md`。
- 不跑 LoCoMo full，避免在已确认负向的 LME 方法上浪费全量评测成本。

## 下一步

- 回到 v18 主线做 badcase 分析，重点看 knowledge-update 和 single-session-user 的 hurt/fixed 差异。
- 下一轮方法应优先考虑 build-stage memory management：更稳定的 state/update/supersession 表达、profile/event 分离、source-linked contradiction chain，而不是每题额外 LLM query planner。
- 若做 query-side 改动，应优先是低成本、可验证、可消融的 evidence compiler 或 answer arbitration，而不是继续增加 query planner LLM 调用。
