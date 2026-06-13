# Diagnosis for stage1_row_guide_v16_lme_s_full_5221021

## Summary

v16 在 LongMemEval-S full 上达到 354/500 = 0.708 DeepSeek judge accuracy。它比 v15 source-map-only 高 11 条、比 v14 full guide 高 2 条，但仍比 v12/v13 主线低 3 条。token gate 通过：avg_build_tokens 80346.246，avg_query_tokens 5029.098。

核心判断：row-level evidence organization 是比 typed memory source map 更稳的方向；v15 负向不是因为 guide 这个方向完全错，而是 memory map 作为二手 typed memory 会引入干扰。LME 的主要问题在 preference 和部分 multi-session，不能把 row guide 无条件开给所有问题。

## Observations

- samples_processed: 500
- avg_build_tokens: 80346.246
- avg_query_tokens: 5029.098
- avg_context_chars: 17142.120
- avg_compiled_evidence_items: 35.318
- build_memory_cache_hits: 3341
- build_memory_cache_misses: 0
- avg_build_memory_records: 129.662
- avg_memory_hits: 8.208
- structured_guide: True
- structured_guide_include_rows: True
- structured_guide_include_memory: False
- row_index_prompts: 500/500
- activated_build_memory_prompts: 0/500
- temporal_aid_prompts: 198/500
- max_memory_records: 0
- answer_max_input_tokens: 131072
- answer_max_output_tokens: 16384

## Judge Diagnosis

- accuracy: 354/500 = 0.708
- invalid_judgments: 0
- evidence_recall: 500/500 = 1.000
- vs_v15: v16-only 46, v15-only 35, net +11
- vs_v14: v16-only 32, v14-only 30, net +2
- vs_v13: v16-only 29, v13-only 32, net -3
- vs_v12: v16-only 33, v12-only 36, net -3
- vs_naive_external_top40: v16-only 39, naive-only 29, net +10

Type-level read:

- knowledge-update: 60/78，比 v13/v14 更好。
- temporal-reasoning: 97/133，和 v13/v14 持平。
- multi-session: 71/133，略低于 v13。
- single-session-preference: 8/30，明显退化，是当前主要负向来源。

## Interpretation

v16 对 LME 的启发很明确：row overview 本身有价值，尤其对 temporal 和 knowledge-update 不伤甚至有收益；但对于 preference/profile 问题，row overview 会诱导 answer model 从局部 raw turns 中抽取不完整偏好，低于 v13 的 no-guide 表现。下一步不能做 benchmark-specific 路由，但可以按 question-text/router 的 `profile_preference` information need 关闭 row guide，或改成 profile/event 对照视图。

## Next Steps

- 不把 v16 作为 LME 主线；LME 仍为 v12/v13。
- 值得做 v17 selective row guide：只对非 `profile_preference` 的 clean runtime information need 打开 row guide，或为 `profile_preference` 使用更合适的 profile/event compiler。
- 设计 v17 前继续看外部 profile/event 方法代码和 badcase，避免简单按 benchmark 调参。
