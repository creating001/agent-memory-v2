# Diagnosis for v43_session_thread_memory_guide_lme_probe_cb5e118

## 结论

v43 不通过 gate，不跑 LongMemEval-S full。

- prediction: `20/20`
- DeepSeek judge: `15/20 = 0.75`
- v42 same 20: `15/20 = 0.75`
- delta_vs_v42: `0`
- avg_query_tokens: `6023.95`
- max_query_tokens: `8003`
- avg_build_tokens: `81690.45`
- answer max input/output: `131072/16384`

主要原因：token 超预算，且没有净 accuracy 收益。v43 修复了一个 temporal exact-date case，但丢掉一个 answer regeneration case，整体持平。

## 有效信号

v43 的局部正向来自 temporal_lookup：

- record `d823172b5baf1eff81acb20c`
- question: `When did I volunteer at the local animal shelter's fundraising dinner?`
- v42 answer: `February 2023`
- v43 answer: `2023-02-14`
- judge: v42 wrong，v43 correct

这说明 session-thread layout + row-linked memory guide 可以帮助 answer model 看到同一 session 内更具体的 turn 和 build memory hint。

## 失败原因

Token:

- list_count avg query `6466.25`
- temporal_lookup avg query `7206.75`
- temporal max query `8003`

这个配置在 list/temporal 同时加入 session headers 和最多 6 条 memory guide，v42 本来已经接近 `6000` avg query 预算，因此超出不意外。

Accuracy:

- 同 20 条相对 v42 gained `1`、lost `1`。
- lost case 在 current_state route，而 v43 没有对 current_state 改 prompt；这是新 answer cache 下的 answer regeneration variance，不是 v43 目标模块带来的可控收益。
- 因此不能用这个 gate 支持 full run。

## Clean 检查

- v43 只读取 question text、visible question time、raw dialogue、retrieval result 和 build-stage memory。
- `session_thread` 只按 session_id/turn_index 组织已选 raw rows，不使用 benchmark row index。
- `row-linked build memory guide` 只指向已进入 prompt 的 raw evidence rows，不作为独立事实源。
- prompt scan 没有 hidden metadata 命中；`category` 仅为 raw dialogue 普通词。
- DeepSeek judge、comparison 和 token 判定只在 prediction 后离线使用。

## 决策

不保留顶层 v43 config 作为当前候选。保留代码开关和 diagnostic 结果，因为它提供了可复用的 compiler 能力和负向边界：

- session-thread layout 可能对 temporal exact-date 有用。
- row-linked memory guide 必须更小、更窄，否则 token 不合格。
- 不能同时对 list_count 和 temporal_lookup 大范围打开。

如果继续该路线，下一步应设计 temporal-only token-safe variant：

- route scope: only `temporal_lookup`
- max_memory_records: `2` 或 `3`
- answer cache: 复用相同 prompt 的已有 cache，只让变化 prompt miss cache，减少无关 route regeneration 噪声。
- gate 仍必须先过 avg query <= `6000` 且 max < `8000`，再看 judge。

## 输出路径

- predictions: `/data/home_new/wujinqi/agent-memory/outputs/diagnostic/v43_session_thread_memory_guide_lme_probe_cb5e118/predictions.jsonl`
- traces: `/data/home_new/wujinqi/agent-memory/outputs/diagnostic/v43_session_thread_memory_guide_lme_probe_cb5e118/traces.jsonl`
- judge: `/data/home_new/wujinqi/agent-memory/experiments/diagnostic/v43_session_thread_memory_guide_lme_probe_cb5e118/deepseek_judge.json`
- comparison_vs_v42: `/data/home_new/wujinqi/agent-memory/experiments/diagnostic/v43_session_thread_memory_guide_lme_probe_cb5e118/judge_comparison_vs_v42_same20.json`
- prompt_clean_scan: `/data/home_new/wujinqi/agent-memory/experiments/diagnostic/v43_session_thread_memory_guide_lme_probe_cb5e118/prompt_clean_scan.json`
- metrics: `/data/home_new/wujinqi/agent-memory/experiments/diagnostic/v43_session_thread_memory_guide_lme_probe_cb5e118/metrics.json`
- manifest: `/data/home_new/wujinqi/agent-memory/experiments/diagnostic/v43_session_thread_memory_guide_lme_probe_cb5e118/manifest.json`
