# Diagnosis: stage1_hybrid_bm25_v18_lme_s_full_6c5ed99

## 结论

v18 是一次有效的通用检索增强：LongMemEval-S full DeepSeek judge accuracy 从 v17 的 `0.722` 提升到 `0.732`。这个提升不是靠扩大上下文窗口换来的，avg query tokens 为 `5117.622`，仍在 LME 6K 预算内；avg build tokens 为 `80346.246`，build cache 全命中但按逻辑 cold-build 成本计入。

## 分题型

| type | correct / total |
|---|---:|
| knowledge-update | 64 / 78 |
| multi-session | 74 / 133 |
| single-session-assistant | 52 / 56 |
| single-session-preference | 11 / 30 |
| single-session-user | 66 / 70 |
| temporal-reasoning | 99 / 133 |

相对 v17：knowledge-update `+2`，temporal-reasoning `+4`，multi-session `-1`，其余持平。说明 lexical supplement 主要帮助精确实体、时间和事实定位，但对跨会话综合仍需要更好的 memory/source organization。

## Retrieval 诊断

- lexical enabled prompts：`500/500`
- prompts with lexical hits：`500/500`
- prompts with final lexical hits：`466/500`
- avg lexical hits：`38.604`
- avg dense hits：`40.000`
- avg final hits：`40.000`
- avg compiled evidence items：`34.058`
- avg context chars：`17551.224`

BM25 在大多数样本进入最终 evidence rows，但没有扩大 top-k；收益来自候选重排/替换，而不是单纯增加 context。

## Prompt 诊断

- structured guide prompts：`492/500`
- row index prompts：`492/500`
- temporal aid prompts：`198/500`
- activated build memory prompts：`0/500`
- personalized recommendation prompts：`8/500`
- personalized recommendation with structured guide：`0/8`

route 分布与 v17 一致：fact_lookup `183`，temporal_lookup `161`，list_count `119`，profile_preference `15`，current_state `22`。v18 没有新增 benchmark/category 路由。

## 对照

| compare | net | v18-only | other-only |
|---|---:|---:|---:|
| v17 | +5 | 23 | 18 |
| v16 | +12 | 23 | 11 |
| v14 | +14 | 41 | 27 |
| v13 | +9 | 35 | 26 |
| v12 | +9 | 40 | 31 |
| clean naive RAG | +22 | 44 | 22 |

v18 对 LME 是当前最优，但提升幅度还没有达到 baseline target。下一步不能只做小规则堆叠，应继续围绕 general memory management：source-linked organization、multi-view memory、selective source expansion、query-time evidence compiler 做组合设计。

## 风险

- BM25 提升 LME，但可能在 LoCoMo 长会话中引入更多 lexical distractor；必须跑 LoCoMo full 验证。
- v18 的 compiled evidence items 比 v17 略少，但 context chars 更高，说明 lexical 命中的 row 可能更长；后续要控制 context budget。
- multi-session 仍低于 v17 1 条，后续优先分析跨会话综合 badcase，而不是继续扩大 top-k。

## 下一步

1. 提交本次 LME 正式记录，保证后续 LoCoMo prediction manifest 尽量 clean。
2. 用同一 v18 config 跑 LoCoMo non-adversarial full。
3. 如果 LoCoMo 不如 v14，比较 v18 与 v14 的错例集合，设计通用的 selective source-linked guide，而不是 benchmark-specific route。
