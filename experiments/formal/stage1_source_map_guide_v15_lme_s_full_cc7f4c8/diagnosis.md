# Diagnosis for stage1_source_map_guide_v15_lme_s_full_cc7f4c8

## Summary

v15 在 LongMemEval-S full 上为 343/500 = 0.686 DeepSeek judge accuracy，低于 v13/v12 的 0.714，也低于 v14 的 0.704 和 clean naive 的 0.688。token gate 通过：avg_build_tokens 80346.246，avg_query_tokens 4865.988。

核心判断：压缩掉 row overview 并只保留 source map 没有恢复 LME，说明 v14 的 LME 回退不只是 row_index 噪声；build memory source map 本身也可能让 answer model过度信任二手 typed memory，尤其在 temporal 和 multi-session 题上。

## Observations

- samples_processed: 500
- avg_build_tokens: 80346.246
- avg_query_tokens: 4865.988
- avg_context_chars: 16750.102
- avg_compiled_evidence_items: 35.318
- build_memory_cache_hits: 3341
- build_memory_cache_misses: 0
- avg_build_memory_records: 129.662
- avg_active_build_memory_records: 116.492
- avg_memory_hits: 8.208
- avg_memory_source_hits: 7.894
- structured_guide: True
- structured_guide_include_rows: False
- structured_guide_include_memory: True
- row_index_prompts: 0/500
- activated_build_memory_prompts: 464/500
- temporal_aid_prompts: 198/500
- max_memory_records: 4
- answer_max_input_tokens: 131072
- answer_max_output_tokens: 16384

## Judge Diagnosis

- accuracy: 343/500 = 0.686
- invalid_judgments: 0
- evidence_recall: 500/500 = 1.000
- vs_v14: v15-only 24, v14-only 33, net -9
- vs_v13: v15-only 34, v13-only 48, net -14
- vs_v12: v15-only 36, v12-only 50, net -14
- vs_naive_external_top40: v15-only 45, naive-only 46, net -1

Type-level read:

- assistant 类提升到 53/56，高于 v14 的 51/56，但这不是主问题。
- temporal-reasoning 降到 91/133，较 v14 97/133 和 v13 97/133 都差。
- multi-session 降到 68/133，仍低于 v13/v14。
- preference 只有 12/30，低于 v14 的 13/30。

## Interpretation

v15 的假设没有成立。source map 的 compact 形式减少了 query token，但没有提升 accuracy。LME 的 evidence_recall 已经满分，瓶颈不是单纯召回，而是 answer model 在长 context 中选择、消解冲突和使用 typed memory 的方式。继续微调 guide 长度或开关性价比低。

## Next Steps

- LME 主线保持 v12/v13；v15 作为负向消融。
- 不再沿着“给 answer prompt 加 typed memory guide”的方向盲目加宽/收窄。
- 下一步应转向更强的通用机制：answer-side evidence selection/verifier、conflict chain、或 build-stage memory 的质量/validity 改进；必须先看外部代码和 badcase，再跑全量。
