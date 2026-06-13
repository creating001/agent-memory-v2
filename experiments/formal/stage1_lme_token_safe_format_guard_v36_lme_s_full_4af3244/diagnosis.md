# Diagnosis for stage1_lme_token_safe_format_guard_v36_lme_s_full_4af3244

## 结论

v36 是当前 LongMemEval-S full 最好 formal 结果：

- DeepSeek judge accuracy: `0.772`
- correct/valid/samples: `386/500/500`
- previous best v28: `0.766`, `383/500`
- delta: `+3` correct
- avg_build_tokens: `80346.246`
- avg_query_tokens: `5715.468`
- answer max input/output: `131072/16384`

该结果通过 LME token 约束，但距离 `0.80` 目标仍差 `14` correct。收益是小幅正向，不是方法突破；下一轮不能再做零散 answer-format 微调，应基于 badcase 和外部方法设计 build/query 侧的通用改进。

## 主要观察

- samples_processed: `500`
- avg_compiled_evidence_items: `34.062`
- avg_context_chars: `18861.108`
- build_memory_enabled: `True`
- build_memory_model: `Qwen/Qwen3-30B-A3B-Instruct-2507`
- build_memory_cache_hits/misses/writes: `3341/0/0`
- avg_build_memory_records: `129.662`
- avg_active_build_memory_records: `116.456`
- avg_memory_hits: `8.236`
- avg_memory_source_hits: `7.924`
- retrieval top_k/dense_top_k/max_top_k: `40/40/40`
- dense_protect_top_n: `32`
- compiler evidence_report_contract: `True`
- temporal_workpad: `True`
- temporal_text_normalization: `True`
- temporal_event_contract: `False`
- answer_output_format: `json_answer`
- answer_cache_hits/misses/writes: `412/88/88`
- answer_finalizer_applied_count: `1`
- answer_finalizer_reason: `duration_decimal_rounding`
- answer_repair_enabled: `False`

## v28 对比

Offline judge comparison against `stage1_evidence_report_contract_v28_lme_s_full_9917c22`:

- both_correct: `371`
- both_wrong: `102`
- gained: `15`
- lost: `12`
- net: `+3`
- answer_changed: `24/500`
- changed-answer net: `+2`
- same-answer judge flip net: `+1`

分 question_type:

- knowledge-update: gained `1`, lost `2`
- multi-session: gained `3`, lost `3`
- single-session-assistant: gained `2`, lost `0`
- single-session-preference: gained `3`, lost `4`
- single-session-user: gained `1`, lost `0`
- temporal-reasoning: gained `5`, lost `3`

分 information_need:

- temporal_lookup: gained `7`, lost `4`
- fact_lookup: gained `5`, lost `5`
- list_count: gained `2`, lost `2`
- current_state: gained `1`, lost `0`
- profile_preference: gained `0`, lost `1`

解释：v36 的 answer guard 对 temporal duration 和 JSON parsing 有实际帮助，但只有小幅净收益；同答案 judge 波动仍可见，必须作为 close-margin 结果报告。

## 剩余错误

v36 wrong total: `114`。

按 question_type:

- multi-session: `47`
- temporal-reasoning: `28`
- single-session-preference: `18`
- knowledge-update: `15`
- single-session-user: `4`
- single-session-assistant: `2`

按 information_need:

- temporal_lookup: `41`
- fact_lookup: `36`
- list_count: `23`
- profile_preference: `7`
- current_state: `7`

代表性错误类型：

- evidence session 已召回，但 reader 选择了过旧事实或最近但不相关事实。
- temporal_lookup 中相对时间和事件时间边界仍容易混淆。
- list_count 中容易漏掉同类实体，或把相邻但不属于问题范围的实体混入。
- multi-session 聚合问题经常需要从多个 session 合并数值、物品、事件或状态，而当前 compiler 仍偏扁平 evidence list。
- preference/current_state 需要更好的 profile/state memory 组织，不能让 profile summary 成为唯一事实来源。

## Clean 检查

- Prediction 输入未暴露 gold answer、judge、benchmark label、sample id、row index、question_type 或 category。
- v36 route/retrieval/compiler/answer 没有根据 LME label 或样本 ID 做分支。
- Duration rounding 是通用机械规则：只看问题文本是否询问 days/weeks/months/years，以及 draft answer 是否为单个小数 duration。
- Evidence recall、judge comparison 和 badcase 只在预测完成后离线读取 labels/judge。
- Dirty state 来自用户修改的 docs，不影响 prediction code/config。

## 决策

保留 v36 为当前 LME 最好 formal 结果，并更新实验入口。

下一轮方法设计要求：

- 先读 v36 badcase 和外部代码，不直接开 full run。
- 方法必须 general，不能按 benchmark label、question_type、sample id、测试实体或测试答案做规则。
- 优先考虑 build/query memory organization：事件/state/profile 的多视图索引、跨 session 聚合 scratchpad、候选答案聚合与冲突处理。
- 先用 no-label route-stratified diagnostic gate 验证 token、cache、trace 和 prompt，再跑 full。
- 如果只改 query-side，可以复用 build cache，但正式记录中的 build token 仍按 cold-build logical usage 统计。

## 输出路径

- predictions: `/data/home_new/wujinqi/agent-memory/outputs/formal/stage1_lme_token_safe_format_guard_v36_lme_s_full_4af3244/predictions.jsonl`
- traces: `/data/home_new/wujinqi/agent-memory/outputs/formal/stage1_lme_token_safe_format_guard_v36_lme_s_full_4af3244/traces.jsonl`
- judge: `/data/home_new/wujinqi/agent-memory/experiments/formal/stage1_lme_token_safe_format_guard_v36_lme_s_full_4af3244/deepseek_judge.json`
- evidence_recall: `/data/home_new/wujinqi/agent-memory/experiments/formal/stage1_lme_token_safe_format_guard_v36_lme_s_full_4af3244/evidence_recall.json`
- comparison_vs_v28: `/data/home_new/wujinqi/agent-memory/experiments/formal/stage1_lme_token_safe_format_guard_v36_lme_s_full_4af3244/judge_comparison_vs_v28.json`
- metrics: `/data/home_new/wujinqi/agent-memory/experiments/formal/stage1_lme_token_safe_format_guard_v36_lme_s_full_4af3244/metrics.json`
- manifest: `/data/home_new/wujinqi/agent-memory/experiments/formal/stage1_lme_token_safe_format_guard_v36_lme_s_full_4af3244/manifest.json`
