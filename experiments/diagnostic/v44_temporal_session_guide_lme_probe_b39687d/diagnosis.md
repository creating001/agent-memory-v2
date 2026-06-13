# Diagnosis for v44_temporal_session_guide_lme_probe_b39687d

## 结论

v44 通过 20 条 diagnostic gate，但暂不跑 full。

- DeepSeek judge: `16/20 = 0.80`
- v42 same 20: `15/20 = 0.75`
- delta_vs_v42: `+1`
- avg_query_tokens: `5783.75`
- max_query_tokens: `7631`
- avg_build_tokens: `81690.45`
- answer max input/output: `131072/16384`

不跑 full 的原因不是 accuracy，而是 full route-mix token 估计：按 v42 LME full 的 temporal_lookup 占比估算，v44 full avg query 约 `6064.479`，略超 `6000` 目标。

## 有效信号

v44 只改变 temporal_lookup，并稳定保留 v43 的正向 case：

- record `d823172b5baf1eff81acb20c`
- question: `When did I volunteer at the local animal shelter's fundraising dinner?`
- v42 answer: `February 2023`
- v44 answer: `2023-02-14`
- judge: v42 wrong，v44 correct

该收益来自 session-thread raw context + row-linked memory guide，说明 build memory 作为 raw row guide 有价值，但必须严格控制规模。

## Token 诊断

Route avg query:

- current_state: `6062.5`
- fact_lookup: `5136.25`
- list_count: `5469.5`
- profile_preference: `5226.0`
- temporal_lookup: `7024.5`

只有 temporal_lookup 改变；non-temporal prompt 复用 v42 cache。v44 gate avg 看起来合格，是因为 20 条 probe 按 route 均衡采样；full 中 temporal_lookup 占 `161/500`，因此 full avg 可能超预算。

Full estimate:

- base v42 full avg query: `5865.644`
- weighted delta from gate: `+198.835`
- estimated v44 full avg query: `6064.479`

因此不能直接进入 full。

## Clean 检查

- v44 只使用 question text、visible question_time、raw dialogue、retrieval result 和 build-stage memory。
- `temporal_lookup` 是 question-derived route，不是 hidden benchmark type。
- answer cache 复用 v42 namespace 只基于 exact prompt hit；cache hit 仍从 stored usage 计入 logical query tokens。
- prompt scan 无 hidden metadata 命中；`category` 仅来自 raw dialogue 普通词。
- DeepSeek judge、comparison 和 full token estimate 只在 prediction 后离线使用。

## 决策

不跑 v44 full。继续做 v45 token-safe narrowing：

- route scope: `temporal_lookup`
- context_layout: `session_thread`
- structured_guide_include_memory: `true`
- max_memory_records: `1`
- answer cache: 继续复用 v42 exact-prompt cache

v45 gate 的通过条件：

- avg query <= `6000`
- max query < `8000`
- estimated full avg query <= `6000`
- same20 judge 相对 v42 不低于 `16/20` 或至少保留 d823 exact-date 修复且无 regression

## 输出路径

- predictions: `/data/home_new/wujinqi/agent-memory/outputs/diagnostic/v44_temporal_session_guide_lme_probe_b39687d/predictions.jsonl`
- traces: `/data/home_new/wujinqi/agent-memory/outputs/diagnostic/v44_temporal_session_guide_lme_probe_b39687d/traces.jsonl`
- judge: `/data/home_new/wujinqi/agent-memory/experiments/diagnostic/v44_temporal_session_guide_lme_probe_b39687d/deepseek_judge.json`
- comparison_vs_v42: `/data/home_new/wujinqi/agent-memory/experiments/diagnostic/v44_temporal_session_guide_lme_probe_b39687d/judge_comparison_vs_v42_same20.json`
- full_query_token_estimate: `/data/home_new/wujinqi/agent-memory/experiments/diagnostic/v44_temporal_session_guide_lme_probe_b39687d/full_query_token_estimate.json`
- prompt_clean_scan: `/data/home_new/wujinqi/agent-memory/experiments/diagnostic/v44_temporal_session_guide_lme_probe_b39687d/prompt_clean_scan.json`
- metrics: `/data/home_new/wujinqi/agent-memory/experiments/diagnostic/v44_temporal_session_guide_lme_probe_b39687d/metrics.json`
- manifest: `/data/home_new/wujinqi/agent-memory/experiments/diagnostic/v44_temporal_session_guide_lme_probe_b39687d/manifest.json`
