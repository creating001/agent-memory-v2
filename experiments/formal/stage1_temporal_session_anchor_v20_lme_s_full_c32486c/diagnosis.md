# Diagnosis: stage1_temporal_session_anchor_v20_lme_s_full_c32486c

## 结论

v20 是局部正向、总体负向的 raw session-anchor 诊断。LME accuracy 为 `0.722`，低于 v18 的 `0.732`，但 temporal-reasoning 提升到 `101/133`，高于 v18 的 `99/133`。相比 v19，v20 证明“只回流 raw rows”比“暴露 build-memory source map”更稳，但仍不足以成为 LME 主线。

## 分题型

| type | v20 | v18 | delta |
|---|---:|---:|---:|
| knowledge-update | 62 / 78 | 64 / 78 | -2 |
| multi-session | 70 / 133 | 74 / 133 | -4 |
| single-session-assistant | 53 / 56 | 52 / 56 | +1 |
| single-session-preference | 11 / 30 | 11 / 30 | 0 |
| single-session-user | 64 / 70 | 66 / 70 | -2 |
| temporal-reasoning | 101 / 133 | 99 / 133 | +2 |

问题在于 session anchors 的收益集中在 temporal，但代价落在 multi-session 和 user fact。后续若继续这个方向，必须更精细地控制 anchor 插入位置或只在更强 temporal intent 下触发。

## Retrieval 诊断

- session_bm25 applied：`161/500`
- prompts with session anchor hits：`161/500`
- avg session anchor hits：`1.288`
- avg final session anchor hits：`0.760`
- final hits avg：`40.414`
- avg query tokens：`5101.412`
- avg context chars：`17502.464`

session anchors 没有扩大 compiler evidence rows 的预算，主要替换尾部 raw rows；token 成本可控。

## 对照

| compare | net | v20-only | other-only |
|---|---:|---:|---:|
| v18 | -5 | 17 | 22 |
| v17 | 0 | 29 | 29 |
| v14 | +9 | 40 | 31 |
| v13 | +4 | 36 | 32 |
| clean naive RAG | +17 | 47 | 30 |

v20 比 v17 持平、比 v13/naive 好，但没有超过 v18。当前 LongMemEval 主线仍是 v18。

## 下一步

跑 LoCoMo full 是有价值的，因为 v20 的 temporal 局部收益正好对应 v18/v14 在 LoCoMo category 2 的差异。如果 LoCoMo 不能超过 v18/v14，则删除 v20 配置，只保留实验记录；如果 LoCoMo 明显提升，再回到 LME 做更保守的触发/保护策略。
