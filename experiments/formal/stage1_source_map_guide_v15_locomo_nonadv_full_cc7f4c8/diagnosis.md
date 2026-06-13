# Diagnosis for stage1_source_map_guide_v15_locomo_nonadv_full_cc7f4c8

## Summary

v15 在 LoCoMo non-adversarial full 上为 1109/1540 = 0.720130 DeepSeek judge accuracy，低于 v14 的 0.735714，也略低于 v13 的 0.721429；高于 v12 的 0.698701 和 clean naive 的 0.698506。token gate 通过：avg_build_tokens 58386.008，avg_query_tokens 3205.268。

核心判断：source-map-only 不是 v14 LoCoMo 提升的充分替代。v14 的 row overview 虽然在 LME 造成噪声，但在 LoCoMo category 2/3/4 中确实帮助了 evidence organization；直接删除会严重伤 category 2。

## Observations

- samples_processed: 1540
- avg_build_tokens: 58386.00779220779
- avg_query_tokens: 3205.268181818182
- avg_context_chars: 10201.026623376623
- avg_compiled_evidence_items: 40.0
- build_memory_cache_hits: 12411
- build_memory_cache_misses: 0
- avg_build_memory_records: 136.65974025974026
- avg_active_build_memory_records: 125.21103896103897
- avg_memory_hits: 19.84155844155844
- avg_memory_source_hits: 22.381168831168832
- structured_guide: True
- structured_guide_include_rows: False
- structured_guide_include_memory: True
- row_index_prompts: 0/1540
- activated_build_memory_prompts: 1540/1540
- temporal_aid_prompts: 391/1540
- max_memory_records: 4
- answer_max_input_tokens: 131072
- answer_max_output_tokens: 16384

## Judge Diagnosis

- accuracy: 1109/1540 = 0.720130
- invalid_judgments: 0
- judge_tokens: prompt 496575, completion 148952, total 645527
- evidence_recall: 1339/1536 = 0.871745
- vs_v14: v15-only 69, v14-only 93, net -24
- vs_v13: v15-only 92, v13-only 94, net -2
- vs_v12: v15-only 119, v12-only 86, net +33
- vs_naive_external_top40: v15-only 136, naive-only 102, net +34

Category read:

- category 1: 182/282 = 0.645，和 v14 持平 correct count。
- category 2: 169/321 = 0.526，较 v14 的 195/321 大幅下降，较 v13 的 186/321 也下降。
- category 3: 57/96 = 0.594，低于 v14 的 60/96，高于 v13 的 54/96。
- category 4: 701/841 = 0.833，高于 v14 的 696/841 和 v13 的 687/841。

## Interpretation

v15 降低了 query token，但性能不是主线可接受的改进。它保留了 category 4 的正向，说明 source map 对部分事实查找有价值；但 category 2 的回退太大，说明 LoCoMo 需要显式 row-level date/role/relative-time organization，而不仅是 typed memory source map。

结合 LME 0.686，v15 不是统一方向。下一步不能继续机械调 guide 长度，应先做 badcase 对照，区分 v14 row overview 改对/改错的模式，再考虑更通用的 selective evidence organization 或 verifier。

## Next Steps

- LoCoMo 主线仍为 v14；LME 主线仍为 v12/v13。
- v15 作为负向/混合消融保留，证明 source-map-only 不足。
- 下一步优先分析 v14 vs v15 的 category 2 和 LME temporal/multi-session badcases，再决定是否做 general selective evidence table、answer verifier 或 build-stage memory validity 改进。
