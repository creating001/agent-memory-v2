# stage1_external_route_guidance_v21_lme_s_full_774be27

## 目的

验证一个 query-side prompt discipline 消融：在 v18 hybrid BM25+dense retrieval、selective row guide 和 raw evidence-first prompt 不变的前提下，让 `external_naive` prompt 真正启用 question-derived `information_need` guidance。

设计动机来自 Hindsight / SimpleMem 一类 intent-aware answering 思路，但本实验只使用问题文本产生的通用 route signal，不使用 gold answer、judge output、benchmark 标签、sample id、qid、row index 或样本级规则。

## 范围

- benchmark: LongMemEval-S
- subset: full
- n_samples: 500
- experiment_kind: formal
- commit: `774be27582abd0dcc3a1a70ea082260a69e5ebb9`
- prediction dirty: `false`
- config snapshot: `experiments/formal/stage1_external_route_guidance_v21_lme_s_full_774be27/config_snapshot.json`
- predictions: `outputs/formal/stage1_external_route_guidance_v21_lme_s_full_774be27/predictions.jsonl`
- traces: `outputs/formal/stage1_external_route_guidance_v21_lme_s_full_774be27/traces.jsonl`

## 结果

- DeepSeek judge accuracy: `351/500 = 0.702`
- v18 baseline: `366/500 = 0.732`
- vs v18: fixed `15`，hurt `30`，net `-15`
- evidence recall: `1.0`
- judge invalid: `0`

按类型：

| type | correct | total | accuracy |
|---|---:|---:|---:|
| knowledge-update | 55 | 78 | 0.705128 |
| multi-session | 70 | 133 | 0.526316 |
| single-session-assistant | 52 | 56 | 0.928571 |
| single-session-preference | 11 | 30 | 0.366667 |
| single-session-user | 65 | 70 | 0.928571 |
| temporal-reasoning | 98 | 133 | 0.736842 |

## Token 成本

- avg_build_tokens: `80346.246`
- avg_query_tokens: `5165.882`
- total_build_tokens: `40173123`
- total_query_tokens: `2582941`
- build memory cache hits/misses/writes: `3341/0/0`
- build token accounting: 按逻辑冷启动 LLM token 记录，cache hit 只减少本机重复 API 调用，不把方法 build 成本记为 0。

## 结论

v21 是负向消融，不跑 LoCoMo full，不作为主线配置保留。当前 unified best 仍是 `configs/stage1_hybrid_bm25_v18_cached.json`。

主要判断：在 evidence recall 不变的情况下，额外 answer-side route guidance 降低了 LME accuracy，说明问题不在召回，而在 prompt 指令对答案细节和更新链使用的干扰。后续不应继续叠加泛化但强约束的 answer rules，而应优先从 raw evidence organization、selective compiler 或更稳的 build-stage memory management 入手。

## 离线评测文件

- judge: `experiments/formal/stage1_external_route_guidance_v21_lme_s_full_774be27/deepseek_judge.json`
- evidence recall: `experiments/formal/stage1_external_route_guidance_v21_lme_s_full_774be27/evidence_recall.json`
- metrics: `experiments/formal/stage1_external_route_guidance_v21_lme_s_full_774be27/metrics.json`
- manifest: `experiments/formal/stage1_external_route_guidance_v21_lme_s_full_774be27/manifest.json`
