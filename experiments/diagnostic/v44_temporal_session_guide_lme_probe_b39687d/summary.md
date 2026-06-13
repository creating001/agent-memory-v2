# v44_temporal_session_guide_lme_probe_b39687d

## 目的

验证 v43 失败后的 token-safe 收窄版本：只对 `temporal_lookup` 打开 session-thread evidence layout 和最多 3 条 row-linked build memory guide。

非 temporal route 与 v42 prompt 等价，并复用 v42 answer cache；cache hit 仍按 stored usage 计入 logical query tokens。

## 范围

- benchmark: `longmemeval_s`
- subset: `route_stratified_20`
- experiment_kind: `diagnostic`
- samples: `20`
- workers: `4`
- input_path: `/data/home_new/wujinqi/agent-memory/outputs/diagnostic/v35_lme_route_stratified_probe/prediction_input.jsonl`
- config_path: `/data/home_new/wujinqi/agent-memory/configs/stage1_temporal_session_guide_v44_cached.json`
- answer model: `Qwen/Qwen3-30B-A3B-Instruct-2507`
- answer max input/output: `131072/16384`

## Git

- commit: `b39687d3d8328fe621844805f1d935b29c451361`
- dirty: `True`
- dirty_note: prediction 和 judge 时有用户修改的 `docs/architecture.md`、`docs/clean_protocol.md` 未提交；实验目录为本次运行新生成。

## Gate 指标

- prediction: `20/20`
- DeepSeek judge accuracy: `16/20 = 0.80`
- v42 same 20: `15/20 = 0.75`
- delta_vs_v42: `+1`
- gained_vs_v42: `1`
- lost_vs_v42: `0`
- avg_build_tokens: `81690.45`
- total_build_tokens: `1633809`
- avg_query_tokens: `5783.75`
- total_query_tokens: `115675`
- max_query_tokens: `7631`
- answer cache hits/misses/writes: `16/4/4`
- build cache hits/misses/writes: `137/0/0`
- embedding cache hits/misses/writes: `10079/0/0`
- avg_compiled_memory_records: `0.6`
- avg_context_chars: `19636.2`

Gate 结论：20 条 gate 通过，且相对 v42 有净 `+1`。但基于 v42 full route 分布的 full query token 估计为 `6064.479`，略超 `6000` 目标，因此不直接跑 v44 full。

## 路由检查

- current_state: n=`4`, avg query `6062.5`, max `6352`, session_thread `0/4`, memory guide `0/4`
- fact_lookup: n=`4`, avg query `5136.25`, max `5343`, session_thread `0/4`, memory guide `0/4`
- list_count: n=`4`, avg query `5469.5`, max `5656`, session_thread `0/4`, memory guide `0/4`
- profile_preference: n=`4`, avg query `5226.0`, max `5597`, session_thread `0/4`, memory guide `0/4`
- temporal_lookup: n=`4`, avg query `7024.5`, max `7631`, session_thread `4/4`, memory guide `4/4`

生效范围符合设计：只改 temporal_lookup。

## v42 对比

同 20 条：

- v42 correct: `15`
- v44 correct: `16`
- gained: `1`
- lost: `0`
- answer_changed: `1`
- same_answer_judge_flip: `0`

Gained:

- `d823172b5baf1eff81acb20c`：animal shelter fundraising dinner，从 v42 `February 2023` 改为 v44 `2023-02-14`，DeepSeek judge 正确。

## Full Token 估计

以 v42 LME full route 分布估计：

- v42 full avg query: `5865.644`
- v44-v42 temporal delta on gate: `+617.5` tokens/sample
- temporal_lookup 在 v42 full 中占 `161/500`
- weighted delta: `+198.835`
- estimated v44 full avg query: `6064.479`

该估计超过 `6000` average query token 目标。不能直接跑 v44 full；应先把 temporal overhead 进一步压低。

## Clean 检查

- prompt clean scan 未命中 `question_type`、`sample_id`、`qid`、`row index`、`gold answer`、`judge output`、`reference answer`、`offline evaluator`。
- `category` 命中 `2` 次，均来自原始对话普通词，不是 benchmark label。
- DeepSeek judge 和 comparison 只在 prediction 完成后离线使用。

## 决策

不直接跑 v44 full。v44 有质量信号，但 full 预算风险不合格。

下一步设计 v45：

- 仍只改 `temporal_lookup`。
- `max_memory_records` 从 `3` 降到 `1`。
- 保留 session_thread。
- 目标是保留 Valentine exact-date 修复，同时把 estimated full avg query 压回 `6000` 以下。

## 输出路径

- predictions: `/data/home_new/wujinqi/agent-memory/outputs/diagnostic/v44_temporal_session_guide_lme_probe_b39687d/predictions.jsonl`
- traces: `/data/home_new/wujinqi/agent-memory/outputs/diagnostic/v44_temporal_session_guide_lme_probe_b39687d/traces.jsonl`
- metrics: `/data/home_new/wujinqi/agent-memory/experiments/diagnostic/v44_temporal_session_guide_lme_probe_b39687d/metrics.json`
- judge: `/data/home_new/wujinqi/agent-memory/experiments/diagnostic/v44_temporal_session_guide_lme_probe_b39687d/deepseek_judge.json`
- comparison: `/data/home_new/wujinqi/agent-memory/experiments/diagnostic/v44_temporal_session_guide_lme_probe_b39687d/judge_comparison_vs_v42_same20.json`
- prompt_clean_scan: `/data/home_new/wujinqi/agent-memory/experiments/diagnostic/v44_temporal_session_guide_lme_probe_b39687d/prompt_clean_scan.json`
- full_query_token_estimate: `/data/home_new/wujinqi/agent-memory/experiments/diagnostic/v44_temporal_session_guide_lme_probe_b39687d/full_query_token_estimate.json`
- manifest: `/data/home_new/wujinqi/agent-memory/experiments/diagnostic/v44_temporal_session_guide_lme_probe_b39687d/manifest.json`
- config_snapshot: `/data/home_new/wujinqi/agent-memory/experiments/diagnostic/v44_temporal_session_guide_lme_probe_b39687d/config_snapshot.json`
