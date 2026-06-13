# Diagnosis for stage1_row_guide_v16_locomo_nonadv_full_5221021

## Summary

v16 在 LoCoMo non-adversarial full 上达到 1124/1540 = 0.729870 DeepSeek judge accuracy，高于 v13 的 0.721429 和 v15 的 0.720130，但低于 v14 的 0.735714。token gate 通过：avg_build_tokens 58386.008，avg_query_tokens 3303.977。

核心判断：LoCoMo 需要 row-level evidence organization。v16 的 rows-only 明显超过 v15 source-map-only，说明 v14 的大部分 LoCoMo 收益不是来自 typed memory source map；但 v16 仍低于 v14，说明 source map 对 LoCoMo 也有补充价值。

## Observations

- samples_processed: 1540
- avg_build_tokens: 58386.00779220779
- avg_query_tokens: 3303.9772727272725
- avg_context_chars: 10638.89935064935
- avg_compiled_evidence_items: 40.0
- build_memory_cache_hits: 12411
- build_memory_cache_misses: 0
- avg_build_memory_records: 136.65974025974026
- avg_memory_hits: 19.84155844155844
- structured_guide: True
- structured_guide_include_rows: True
- structured_guide_include_memory: False
- row_index_prompts: 1540/1540
- activated_build_memory_prompts: 0/1540
- temporal_aid_prompts: 391/1540
- max_memory_records: 0
- answer_max_input_tokens: 131072
- answer_max_output_tokens: 16384

## Judge Diagnosis

- accuracy: 1124/1540 = 0.729870
- invalid_judgments: 0
- judge_tokens: prompt 495435, completion 150565, total 646000
- evidence_recall: 1339/1536 = 0.871745
- vs_v15: v16-only 113, v15-only 98, net +15
- vs_v14: v16-only 91, v14-only 100, net -9
- vs_v13: v16-only 96, v13-only 83, net +13
- vs_v12: v16-only 132, v12-only 84, net +48
- vs_naive_external_top40: v16-only 139, naive-only 90, net +49

Category read:

- category 1: 188/282，较 v14 净 +6。
- category 2: 186/321，和 v13 持平，低于 v14 的 195/321。
- category 3: 59/96，高于 v13，略低于 v14。
- category 4: 691/841，高于 v13，低于 v14。

## Interpretation

v16 是有价值的归因实验：row guide 是 general 且 clean 的 context organization 机制，在 LoCoMo 上正向，在 LME 上也比 v14/v15 更稳。但 v16 仍不是最终方法：LME 低于 v13，LoCoMo 低于 v14。

下一步应避免 benchmark-specific 规则。合理方向是按 clean runtime information need 做 selective compiler：例如 `profile_preference` 不使用 row guide，temporal/list/fact_lookup 使用 row guide；再考虑只在高置信情况下加入 memory source map。这来自 v16 的 LME preference 退化和 LoCoMo v14-v16 差异，不使用 benchmark category 或 judge 进入预测。

## Next Steps

- 保留 v16 为正向归因消融。
- 下一步做 v17 selective row guide/profile-safe compiler：只用 question-text router 的 information need 和 runtime metadata 控制 guide，而不是 benchmark 标签。
- 设计前应继续看外部 profile/event memory 代码，尤其 LangMem/Mem0/Memobase 或相关实现，避免凭空设计 profile 逻辑。
