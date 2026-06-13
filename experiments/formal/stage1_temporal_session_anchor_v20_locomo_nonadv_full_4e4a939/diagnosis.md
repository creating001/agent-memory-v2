# Diagnosis: stage1_temporal_session_anchor_v20_locomo_nonadv_full_4e4a939

## 结论

v20 是负向诊断。LoCoMo non-adversarial full accuracy 为 `0.727273`，低于 v18 的 `0.737013` 和 v14 的 `0.735714`。它没有解决目标 category 2，反而比 v18 少 5 条、比 v14 少 10 条。

## Category 诊断

| category | v20 | v18 | v14 |
|---|---:|---:|---:|
| 1 | 177 / 282 | 187 / 282 | 182 / 282 |
| 2 | 185 / 321 | 190 / 321 | 195 / 321 |
| 3 | 58 / 96 | 60 / 96 | 60 / 96 |
| 4 | 700 / 841 | 698 / 841 | 696 / 841 |

唯一正向是 category 4 相对 v18 多 2 条，但 category 1/2/3 全部退化，不能作为 LoCoMo 主线。

## Retrieval 诊断

- session_bm25 applied：`338/1540`
- prompts with session anchor hits：`338/1540`
- avg session anchor hits：`0.878`
- avg final session anchor hits：`0.490`
- avg query tokens：`3269.849`
- avg context chars：`9952.512`
- evidence recall：`0.889974`

evidence recall 略高于 v18，但 accuracy 低，说明问题不是简单召回覆盖，而是 anchor 插入扰动了证据排序或答案注意力。

## 对照

| compare | net | v20-only | other-only |
|---|---:|---:|---:|
| v18 | -15 | 29 | 44 |
| v14 | -13 | 104 | 117 |
| v16 | -4 | 58 | 62 |
| v17 | +10 | 63 | 53 |
| v13 | +9 | 114 | 105 |
| clean naive RAG | +45 | 139 | 94 |

v20 继承了 v18 的 hybrid retrieval，所以仍高于 naive/v13/v17，但相对当前最好 v18/v14 都是负向。

## 下一步

不要继续 session-anchor 插入线。下一轮更应做 answer-side 或 compiler-side 的 raw evidence organization：例如让 prompt 中的 row overview 更好表达 session/date/source diversity，但不改变最终 evidence row 排序；或者用轻量 rerank 先做离线诊断，再决定是否进入 full run。
