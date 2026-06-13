# Diagnosis: stage1_hybrid_bm25_v18_locomo_nonadv_full_bb1cc3c

## 结论

v18 在 LoCoMo non-adversarial full 上达到 `0.737013`，比 v14 `0.735714` 高 2 条，比 v17 高 25 条，并且 avg query tokens 从 v14 的 `3818.198` 降到 `3270.569`。这是一个通用正向结果：同一配置已经在 LongMemEval-S full 和 LoCoMo full 上都超过此前最好。

## Category 诊断

| category | v18 | v14 | delta |
|---|---:|---:|---:|
| 1 | 187 / 282 | 182 / 282 | +5 |
| 2 | 190 / 321 | 195 / 321 | -5 |
| 3 | 60 / 96 | 60 / 96 | 0 |
| 4 | 698 / 841 | 696 / 841 | +2 |

v18 的总分提升主要来自 category 1/4，category 2 仍然是 v14 structured evidence guide 更强。这提示后续要研究 source-linked organization，而不是继续盲目加 lexical 权重。

## Evidence Recall

| category | recall | n |
|---|---:|---:|
| 1 | 0.893617 | 282 |
| 2 | 0.890966 | 321 |
| 3 | 0.673913 | 92 |
| 4 | 0.910820 | 841 |

overall evidence recall 为 `0.889323`，高于 v14/v17 的 `0.871745`。召回提升明显，但 judge accuracy 只比 v14 高 2 条，说明 LoCoMo 的瓶颈不只是 evidence 是否被检索到，还包括 evidence 组织、冲突处理和多跳综合。

## Retrieval / Prompt 诊断

- lexical enabled prompts：`1540/1540`
- prompts with lexical hits：`1540/1540`
- prompts with final lexical hits：`1359/1540`
- avg lexical hits：`39.623`
- avg dense hits：`40.000`
- avg final hits：`40.000`
- structured guide prompts：`1540/1540`
- row index prompts：`1540/1540`
- temporal aid prompts：`391/1540`
- activated build memory prompts：`0/1540`

route 分布：fact_lookup `1018`，temporal_lookup `338`，list_count `131`，profile_preference `49`，current_state `4`。这些 route 来自 question text，不使用 benchmark category。

## 对照

| compare | net | v18-only | other-only |
|---|---:|---:|---:|
| v14 | +2 | 112 | 110 |
| v17 | +25 | 68 | 43 |
| v16 | +11 | 69 | 58 |
| v13 | +24 | 118 | 94 |
| v12 | +59 | 146 | 87 |
| clean naive RAG | +60 | 145 | 85 |

v18 与 v14 的互补错例很多：两边各自独有正确超过 100 条。后续最有价值的是分析 v18-only / v14-only 的 category 2 和 category 4 样本，找出通用 evidence organization 机制，而不是新增 benchmark-specific 分类规则。

## 风险与下一步

- v18 相对 v14 的 LoCoMo 优势很薄，不能直接说明 hybrid BM25 已解决 memory management。
- category 2 退化说明 row/source-linked guide 仍然重要。
- 下一步建议：基于 v18 主线做 `selective_source_linked_compiler` 设计，借鉴 Graphiti/HippoRAG/Hindsight/xMemory 的 provenance 与 neighborhood，但保持 raw evidence 为最终事实来源，并保持 query token <= 6K。
