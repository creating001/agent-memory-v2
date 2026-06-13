# stage1_temporal_aid_frontload_v22_lme_s_full_2143e43

## 目的

验证一个 query-side temporal compiler 消融：在 v18 hybrid BM25+dense retrieval、selective row guide、build-stage typed memory source expansion 全部不变的前提下，把 `Temporal Aid` 从长 `Memory Context` 后面前置到 context 前，并加入通用 duration mention 抽取，例如 `two weeks`、`a week and a half`。

设计借鉴 SimpleMem 的 timestamp normalization / structured memory unit，以及 Graphiti/Zep 的 episode-time provenance。该方法只使用问题文本、row timestamp 和 raw row text，不使用 gold answer、judge output、benchmark 标签、sample id、qid、row index 或样本级规则。

## 范围

- benchmark: LongMemEval-S
- subset: full
- n_samples: 500
- experiment_kind: formal
- commit: `2143e43aa0e3cc3b9fe2fbca8a6a544eb03899c5`
- prediction dirty: `false`
- config snapshot: `experiments/formal/stage1_temporal_aid_frontload_v22_lme_s_full_2143e43/config_snapshot.json`
- predictions: `outputs/formal/stage1_temporal_aid_frontload_v22_lme_s_full_2143e43/predictions.jsonl`
- traces: `outputs/formal/stage1_temporal_aid_frontload_v22_lme_s_full_2143e43/traces.jsonl`

## 结果

- DeepSeek judge accuracy: `360/500 = 0.720`
- v18 baseline: `366/500 = 0.732`
- vs v18: fixed `21`，hurt `27`，net `-6`
- evidence recall: `1.0`
- judge invalid: `0`

按类型：

| type | correct | total | accuracy |
|---|---:|---:|---:|
| knowledge-update | 61 | 78 | 0.782051 |
| multi-session | 73 | 133 | 0.548872 |
| single-session-assistant | 53 | 56 | 0.946429 |
| single-session-preference | 12 | 30 | 0.400000 |
| single-session-user | 64 | 70 | 0.914286 |
| temporal-reasoning | 97 | 133 | 0.729323 |

## Token 成本

- avg_build_tokens: `80346.246`
- avg_query_tokens: `5134.496`
- total_build_tokens: `40173123`
- total_query_tokens: `2567248`
- build memory cache hits/misses/writes: `3341/0/0`
- build token accounting: 按逻辑冷启动 LLM token 记录，cache hit 只减少本机重复 API 调用，不把方法 build 成本记为 0。

## Prompt 诊断

- temporal_aid_prompts: `198`
- frontloaded_temporal_aid_prompts: `198`
- duration_mentions_prompts: `145`

## 结论

v22 是负向消融，不跑 LoCoMo full，不作为主线配置保留。当前 unified best 仍是 `configs/stage1_hybrid_bm25_v18_cached.json`。

主要判断：Temporal Aid 前置和 duration mention 抽取能修复一部分样本，但会引入额外注意力噪声，尤其伤 knowledge-update、multi-session 和 temporal-reasoning。后续不应继续加更多 regex 型 temporal aid，而应优先改进更稳的 evidence selection / conflict chain / typed memory management。

## 离线评测文件

- judge: `experiments/formal/stage1_temporal_aid_frontload_v22_lme_s_full_2143e43/deepseek_judge.json`
- evidence recall: `experiments/formal/stage1_temporal_aid_frontload_v22_lme_s_full_2143e43/evidence_recall.json`
- metrics: `experiments/formal/stage1_temporal_aid_frontload_v22_lme_s_full_2143e43/metrics.json`
- manifest: `experiments/formal/stage1_temporal_aid_frontload_v22_lme_s_full_2143e43/manifest.json`
