# v43_session_thread_memory_guide_lme_probe_cb5e118

## 目的

验证 v43 session-thread evidence layout + row-linked build memory guide 是否能改善 v42 在 list/count 与 temporal 聚合上的错误。

v43 只在 `list_count` / `temporal_lookup` 打开：

- `context_layout=session_thread`
- `memory_record_source=evidence_rows`
- `structured_guide_include_memory=true`
- `max_memory_records=6`

它不改变 build prompt、不改变 retrieval top-k、不新增 LLM 调用。

## 范围

- benchmark: `longmemeval_s`
- subset: `route_stratified_20`
- experiment_kind: `diagnostic`
- samples: `20`
- workers: `4`
- input_path: `/data/home_new/wujinqi/agent-memory/outputs/diagnostic/v35_lme_route_stratified_probe/prediction_input.jsonl`
- config_path: `/data/home_new/wujinqi/agent-memory/configs/stage1_session_thread_memory_guide_v43_cached.json`
- answer model: `Qwen/Qwen3-30B-A3B-Instruct-2507`
- answer max input/output: `131072/16384`

## Git

- commit: `cb5e11820fce7a7d751c6f98695dc92d202633db`
- dirty: `True`
- dirty_note: prediction 和 judge 时有用户修改的 `docs/architecture.md`、`docs/clean_protocol.md` 未提交；实验目录为本次运行新生成。

## Gate 指标

- prediction: `20/20`
- DeepSeek judge accuracy: `15/20 = 0.75`
- v42 same 20: `15/20 = 0.75`
- delta_vs_v42: `0`
- gained_vs_v42: `1`
- lost_vs_v42: `1`
- avg_build_tokens: `81690.45`
- total_build_tokens: `1633809`
- avg_query_tokens: `6023.95`
- total_query_tokens: `120479`
- max_query_tokens: `8003`
- answer cache hits/misses/writes: `0/20/20`
- build cache hits/misses/writes: `137/0/0`
- embedding cache hits/misses/writes: `10079/0/0`
- avg_compiled_memory_records: `2.4`
- avg_context_chars: `20277.0`

Gate 结论：失败。平均 query token 超过 `6000`，max query token 也超过 `8000`；accuracy 与 v42 持平，没有净收益。

## 路由检查

- current_state: n=`4`, avg query `6048.0`, max `6253`, session_thread `0/4`, memory guide `0/4`
- fact_lookup: n=`4`, avg query `5126.5`, max `5315`, session_thread `0/4`, memory guide `0/4`
- list_count: n=`4`, avg query `6466.25`, max `6860`, session_thread `4/4`, memory guide `4/4`
- profile_preference: n=`4`, avg query `5272.25`, max `5571`, session_thread `0/4`, memory guide `0/4`
- temporal_lookup: n=`4`, avg query `7206.75`, max `8003`, session_thread `4/4`, memory guide `4/4`

`session_thread` 和 `activated_build_memory` 的生效范围符合设计，只在 list/temporal 出现；问题是 token 成本过高。

## v42 对比

同 20 条：

- v42 correct: `15`
- v43 correct: `15`
- gained: `1`
- lost: `1`
- answer_changed: `4`
- same_answer_judge_flip: `0`

Gained:

- `d823172b5baf1eff81acb20c`：animal shelter fundraising dinner，从 v42 `February 2023` 改为 v43 `2023-02-14`，DeepSeek judge 正确。

Lost:

- `0a537c6dfde0742723049ca4`：photography setup accessories，v43 新增了更泛的 “protective gear for lenses and accessories”，judge 从 correct 变 wrong。该 route 未开启 session_thread/memory guide，属于 answer regeneration variance，不支持 v43 full。

## Clean 检查

- prompt clean scan 未命中 `question_type`、`sample_id`、`qid`、`row index`、`gold answer`、`judge output`、`reference answer`、`offline evaluator`。
- `category` 命中 `2` 次，均来自原始对话普通词，不是 benchmark label。
- DeepSeek judge 和 comparison 只在 prediction 完成后离线使用。

## 决策

不跑 full。v43 的思路对 temporal exact-date 有局部信号，但当前配置过宽、token 超预算且无净 accuracy 收益。

下一步若继续该方向，应改成更窄的 token-safe temporal-only 版本：

- 只对 `temporal_lookup` 打开 session_thread/memory guide。
- `max_memory_records` 从 `6` 降到 `2` 或 `3`。
- 非目标 route 复用相同 prompt/cache，避免无关 route 的 answer regeneration 干扰判断。

## 输出路径

- predictions: `/data/home_new/wujinqi/agent-memory/outputs/diagnostic/v43_session_thread_memory_guide_lme_probe_cb5e118/predictions.jsonl`
- traces: `/data/home_new/wujinqi/agent-memory/outputs/diagnostic/v43_session_thread_memory_guide_lme_probe_cb5e118/traces.jsonl`
- metrics: `/data/home_new/wujinqi/agent-memory/experiments/diagnostic/v43_session_thread_memory_guide_lme_probe_cb5e118/metrics.json`
- judge: `/data/home_new/wujinqi/agent-memory/experiments/diagnostic/v43_session_thread_memory_guide_lme_probe_cb5e118/deepseek_judge.json`
- comparison: `/data/home_new/wujinqi/agent-memory/experiments/diagnostic/v43_session_thread_memory_guide_lme_probe_cb5e118/judge_comparison_vs_v42_same20.json`
- prompt_clean_scan: `/data/home_new/wujinqi/agent-memory/experiments/diagnostic/v43_session_thread_memory_guide_lme_probe_cb5e118/prompt_clean_scan.json`
- manifest: `/data/home_new/wujinqi/agent-memory/experiments/diagnostic/v43_session_thread_memory_guide_lme_probe_cb5e118/manifest.json`
- config_snapshot: `/data/home_new/wujinqi/agent-memory/experiments/diagnostic/v43_session_thread_memory_guide_lme_probe_cb5e118/config_snapshot.json`
