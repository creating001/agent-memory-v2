# v50 Profile Advice Memory Guide 诊断

## 目的

v42 在 LongMemEval-S `single-session-preference` 上只有 `13/30`。许多错误样本证据已经进入 context，但模型仍给泛化建议或过度拒答。v50 测试一个通用 personalization 方向：

- 扩展 question-text advice/recommendation route，把 `tips/advice/ideas/should I/what do you think` 这类问题路由到 `profile_preference`。
- 只在 `profile_preference` 中把 build-stage typed memory 作为 `Structured Evidence Guide` 的 source-linked 索引，不作为独立事实源。
- 保留 raw Memory Context 为最终事实来源。

外部参考：

- SimpleMem：multi-view context 和 structured answer context。
- Memobase：event/profile 分离与 profile delta 思想。
- MIRIX：semantic/episodic/profile 等不同 memory schema 分层。

## 范围

- benchmark: LongMemEval-S
- subset: `single-session-preference` 全量 30 条
- experiment_kind: diagnostic
- run_id: `v50_profile_advice_memory_guide_lme_pref_81351ef`
- base: v42 operation workpad
- commit: `81351ef18c6b5401e610c4dbcd49ce513bfe9dde`
- dirty: True。运行时包含用户修改的 `docs/architecture.md`、`docs/clean_protocol.md`，以及本轮 v50 代码/实验文件。
- answer model: `Qwen/Qwen3-30B-A3B-Instruct-2507`
- answer max input/output: `131072 / 16384`

实际运行配置保存在 `config_snapshot.json`。顶层 v50 config 已删除，不作为候选配置保留。

## 主要结果

- v50 DeepSeek judge accuracy: `12/30 = 0.400000`
- v42 same-30 baseline: `13/30 = 0.433333`
- gain/loss: `1/2`，净 `-1`
- same_wrong: `16`
- answer_changed: `25/30`
- route_changed: `15/30`
- avg_build_tokens: `79618.666667`
- avg_query_tokens: `5801.666667`
- avg_query_delta vs v42 same-30: `+461.833333`
- prompt clean scan: `0` findings
- full LME route audit: 只会改变 `15/500` 条 route，其中 `fact_lookup -> profile_preference` 为 `13` 条，`list_count -> profile_preference` 为 `1` 条。

token 口径：build tokens 是冷启动构建 memory 的逻辑 LLM token；本机 cache hit 不把方法成本记为 0。

## 结论

v50 失败，不跑 LongMemEval-S full，也不跑 LoCoMo full。

失败原因不是 clean 或 token，而是方法效果不足：拓宽 advice route 后，大多数原本错误的 personalized advice 样本仍然错误；source-linked build memory guide 没有让模型稳定提取用户特定约束，反而增加 query tokens 并引入 2 个 regression。

可保留的启发：personalized advice 需要更强的 build-side profile/event organization，但不能只是把 typed memory 作为 prompt guide 加进去。后续应回到 build memory 质量和状态管理本身，例如构建更可靠的 profile slots、preference evidence 和 event/profile delta，再通过 raw source 回链使用。

## 文件

- predictions: `outputs/diagnostic/v50_profile_advice_memory_guide_lme_pref_81351ef/predictions.jsonl`
- traces: `outputs/diagnostic/v50_profile_advice_memory_guide_lme_pref_81351ef/traces.jsonl`
- metrics: `experiments/diagnostic/v50_profile_advice_memory_guide_lme_pref_81351ef/metrics.json`
- judge: `experiments/diagnostic/v50_profile_advice_memory_guide_lme_pref_81351ef/deepseek_judge.json`
- comparison: `experiments/diagnostic/v50_profile_advice_memory_guide_lme_pref_81351ef/judge_comparison_vs_v42_same30.json`
- route audit: `experiments/diagnostic/v50_profile_advice_memory_guide_lme_pref_81351ef/full_route_change_audit.json`
- prompt scan: `experiments/diagnostic/v50_profile_advice_memory_guide_lme_pref_81351ef/prompt_clean_scan.json`
