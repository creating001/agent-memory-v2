# Diagnosis: stage1_profile_memory_contract_v24_lme_s_full_bc7983d

## 结论

v24 profile memory contract 在 preference 局部有正向信号，但 LongMemEval-S full 主指标负向：0.714，低于 v18 的 0.732，净 -9。因此不作为主线，不跑 LoCoMo full。

## 关键指标

- n_samples：500
- judge accuracy：0.714, 357/500
- judge invalid：0
- vs v18：fixed 15, hurt 24, net -9
- evidence recall：1.0
- avg_build_tokens：80346.246
- avg_query_tokens：5133.588
- build cache：hits 3341, misses 0, writes 0
- prompt_changed_total：15
- prompt_changed_nonprofile：0

## 分题型诊断

- single-session-preference：11/30 -> 13/30，局部 +2。
- multi-session：74/133 -> 70/133，净 -4。
- temporal-reasoning：99/133 -> 96/133，净 -3。
- knowledge-update：64/78 -> 62/78，净 -2。
- single-session-user：66/70 -> 64/70，净 -2。
- single-session-assistant：52/56 -> 52/56，持平。

## 机制判断

- v24 只改变 `profile_preference` route 下的 15 个 prompt；非 profile prompt 与 v18 完全一致。
- preference 局部收益说明“偏好约束式回答契约 + source-linked typed memory guide”有一定价值。
- 但 full benchmark 结果必须按完整 500 条 judge accuracy 选择；本轮没有超过 v18。
- evidence recall 仍为 1.0，说明主要瓶颈不是 gold evidence 是否进入 context，而是 answer 使用稳定性和 memory/profile 信号质量。
- 不应把该局部正向直接扩展成更大范围 prompt guidance；v21 已证明全局 route guidance 会明显伤 LME。

## 处置

- v24 配置和代码不作为主线保留。
- formal 记录保留用于追溯。
- 不跑 LoCoMo full，避免在 LME full 已负向的方法上继续消耗评测成本。

## 下一步

- 如果继续利用 preference 局部信号，应先设计更强的 build-stage profile/event 管理，提升 typed memory 本身质量，而不是只改 answer prompt。
- 考虑实现 answer prompt cache 作为实验基础设施，降低 query-side 小改动被 answer nondeterminism 淹没的风险；cache 只能按 prompt/model/config key 命中，不能读取 gold/judge。
- 下一轮方法仍需以 full judge accuracy 为准，不能只看 preference 局部。
