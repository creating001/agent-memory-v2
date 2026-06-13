# Diagnosis for stage1_operation_workpad_v42_lme_s_full_f7eb076

## 结论

v42 是当前 LongMemEval-S full 最好 formal 结果，但只是 close-margin 小幅正向：

- DeepSeek judge accuracy: `0.774`
- correct/valid/samples: `387/500/500`
- v36 baseline: `0.772`, `386/500`
- delta_vs_v36: `+1` correct
- avg_build_tokens: `80346.246`
- avg_query_tokens: `5865.644`
- answer max input/output: `131072/16384`

该结果通过平均 query token 预算，但 temporal_lookup 的单样本 max query token 达到 `8842`。v42 可以保留为 LME 当前候选，不应继续沿这个方向增加更长 reader prompt。

## 主要观察

- samples_processed: `500`
- avg_compiled_evidence_items: `34.062`
- avg_context_chars: `19665.61`
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
- operation_workpad: `True`
- operation_workpad_information_needs: `list_count`, `temporal_lookup`
- temporal_workpad: `True`
- temporal_text_normalization: `True`
- temporal_event_contract: `False`
- answer_output_format: `json_answer`
- answer_cache_hits/misses/writes: `20/480/480`
- answer_finalizer_applied_count: `1`
- answer_repair_enabled: `False`

## v36/v40 对比

Against v36 `stage1_lme_token_safe_format_guard_v36_lme_s_full_4af3244`:

- v36 correct: `386`
- v42 correct: `387`
- both_correct: `361`
- both_wrong: `88`
- gained: `26`
- lost: `25`
- net: `+1`
- changed_answer_count: `150`
- same_answer_judge_flip_count: `4`

Against v40 `stage1_route_scoped_evidence_detail_v40_lme_s_full_1559c80`:

- v40 correct: `371`
- v42 correct: `387`
- gained: `31`
- lost: `15`
- net: `+16`

解释：v42 证明短 operation discipline 比 v40 的详细 evidence rule 更稳，但相对 v36 的净收益非常小。大量 answer changed 后 gain/loss 基本抵消，说明继续靠 query prompt 微调的边际收益低。

## 分桶诊断

按 information_need:

- current_state: `12/22 = 0.5455`
- fact_lookup: `150/183 = 0.8197`
- list_count: `95/119 = 0.7983`
- profile_preference: `10/15 = 0.6667`
- temporal_lookup: `120/161 = 0.7453`

按 question_type:

- knowledge-update: `64/78 = 0.8205`
- multi-session: `87/133 = 0.6541`
- single-session-assistant: `53/56 = 0.9464`
- single-session-preference: `13/30 = 0.4333`
- single-session-user: `65/70 = 0.9286`
- temporal-reasoning: `105/133 = 0.7895`

v42 的弱项仍然是:

- `multi-session`: 跨 session 聚合和冲突处理不足。
- `single-session-preference`: 个性化建议容易变成通用建议。
- `current_state`: 最新状态和历史事实边界不稳定。
- `temporal_lookup`: operation workpad 不能彻底解决 event time / mention time / relative window 混淆。

## 剩余错误

v42 wrong total: `113`。

badcase tag counts:

- temporal: `59`
- large_context: `56`
- count_or_quantity: `54`
- gold_string_in_rows: `33`
- over_abstain: `22`
- update_or_state: `19`
- should_abstain: `15`
- other: `11`

代表性失败模式:

- 关键证据在 top rows 中，但 answer model 选择了 insufficient 或输出不完整，例如 coupon/Target 类过度 abstain。
- 问题要求具体日期时，模型只答月份或相对时间。
- 计数题仍会漏掉同类候选、误解 inclusive alternatives、或把相邻但 out-of-scope 的证据混入。
- 个性化建议题需要总结用户偏好和不偏好，当前 reader 常只复述一个事实或给通用建议。
- current_state 需要“当前仍成立”的状态记忆，而不是普通 fact 排序。

## 方法判断

v42 的正向来自通用 operation 聚合纪律，clean 且可消融；但提升只有 `+1/500`，不足以作为下一阶段主线突破。

下一阶段应把重点从 answer prompt 转到 build-to-query memory organization:

- build 阶段生成更自包含的 event/state/profile/preference memory units，并保留 source links。
- 对每条 memory 明确 `topic/entities/time/status/validity/candidate attributes`，但仍不让 summary 成为唯一事实来源。
- query 阶段用多视图检索和 candidate aggregation，而不是只把 raw rows 扁平交给 reader。
- preference/current_state 需要可回溯的 profile/state candidates；list/temporal 需要先形成候选集合再回答。

这个方向符合 SimpleMem 的 self-contained memory unit、多视图检索，Mnemis 的全局候选选择，Graphiti/Zep 的 temporal validity/source episode 思路，以及 creating001 的 evidence-first organization；但不能迁移任何 benchmark-specific route、样本规则、gold/judge 逻辑。

## Clean 检查

- Prediction 输入未暴露 gold answer、judge、benchmark label、sample id、row index、question_type 或 category。
- v42 route/retrieval/compiler/answer 没有根据 LME label 或样本 ID 做分支。
- `operation_workpad` 是通用自然语言操作提示，只按 question-derived information need 开关。
- Evidence recall、judge comparison 和 badcase digest 只在预测完成后离线读取 labels/judge。
- Prompt clean scan 未发现 hidden metadata；`category` 命中来自原始对话普通词。
- Dirty state 来自用户修改的 docs，不影响 prediction code/config。

## 决策

保留 v42 formal 结果和顶层 config。`experiments/README.md` 中应把 LME 当前最好从 v36 更新为 v42，同时保留 v36 作为强 baseline。

下一轮实验前必须先完成方法规划:

- 先读 v42/v36 badcase，不直接跑 full。
- 至少参考已 clone 的外部方法代码，说明采用和舍弃。
- 优先做 build 侧 memory organization 与 query 侧 candidate aggregation 的成体系改造。
- 若跑 LoCoMo full，只把它作为 v42 迁移性验证；不要把 LoCoMo full 当作替代方法设计。

## 输出路径

- predictions: `/data/home_new/wujinqi/agent-memory/outputs/formal/stage1_operation_workpad_v42_lme_s_full_f7eb076/predictions.jsonl`
- traces: `/data/home_new/wujinqi/agent-memory/outputs/formal/stage1_operation_workpad_v42_lme_s_full_f7eb076/traces.jsonl`
- judge: `/data/home_new/wujinqi/agent-memory/experiments/formal/stage1_operation_workpad_v42_lme_s_full_f7eb076/deepseek_judge.json`
- judge_metrics_summary: `/data/home_new/wujinqi/agent-memory/experiments/formal/stage1_operation_workpad_v42_lme_s_full_f7eb076/judge_metrics_summary.json`
- evidence_recall: `/data/home_new/wujinqi/agent-memory/experiments/formal/stage1_operation_workpad_v42_lme_s_full_f7eb076/evidence_recall.json`
- comparison_vs_v36_v40: `/data/home_new/wujinqi/agent-memory/experiments/formal/stage1_operation_workpad_v42_lme_s_full_f7eb076/judge_comparison_vs_v36_v40.json`
- badcase_digest: `/data/home_new/wujinqi/agent-memory/experiments/formal/stage1_operation_workpad_v42_lme_s_full_f7eb076/badcase_digest.json`
- metrics: `/data/home_new/wujinqi/agent-memory/experiments/formal/stage1_operation_workpad_v42_lme_s_full_f7eb076/metrics.json`
- manifest: `/data/home_new/wujinqi/agent-memory/experiments/formal/stage1_operation_workpad_v42_lme_s_full_f7eb076/manifest.json`
