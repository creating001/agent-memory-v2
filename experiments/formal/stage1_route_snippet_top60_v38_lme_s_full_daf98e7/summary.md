# v38 route-scoped snippet top60 LME full

## 目的

验证 v36 LME 主线上的一个 clean coverage 改动：不把 typed memory 直接放进 answer prompt，只对 question-text route 得出的 `list_count` 和 `temporal_lookup` 扩大 raw retrieval 到 top60，并对这两类长 row 使用 `role_query_snippet` 控制 query token。

核心假设是：v37 证明 typed memory prompt 化会干扰 reader，但 v36 badcase 仍有跨 session 聚合和时间窗口漏项；因此只增加目标 route 的 raw evidence 覆盖，尽量避免全局堆 context。

## 实验范围

- run: `stage1_route_snippet_top60_v38_lme_s_full_daf98e7`
- benchmark/subset: `LongMemEval-S / full`
- samples: `500`
- git commit: `daf98e726fd837ddffb1f2cb44226db201e6a9bf`
- dirty: 是，仅用户修改的 `docs/architecture.md`、`docs/clean_protocol.md`
- config at run time: `configs/stage1_route_snippet_top60_v38_cached.json`
- reproducible config: `experiments/formal/stage1_route_snippet_top60_v38_lme_s_full_daf98e7/config_snapshot.json`
- workers: prediction `8`，DeepSeek judge `16`
- answer model: local vLLM `Qwen/Qwen3-30B-A3B-Instruct-2507`
- answer max input/output: `131072 / 16384`

## 主要结果

- DeepSeek judge accuracy: `0.752000`
- correct / total: `376 / 500`
- invalid judge: `0`
- evidence recall: `1.000000`，500/500 有标注 evidence 的样本均召回
- avg build tokens: `80346.246`
- total build tokens: `40173123`
- avg query tokens: `5934.178`
- total query tokens: `2967089`
- DeepSeek judge tokens: prompt `78212`，completion `43228`，total `121440`

token 口径：build token 是新环境冷启动构建 memory 的逻辑 LLM token；本次 build cache 全命中只减少本机重复调用，不把方法成本记为 0。query token 是 prediction query/answer 阶段 LLM token，不含 embedding 和 judge。

## 运行诊断

- build memory records avg: `129.662`
- active build memory records avg: `116.456`
- compiled evidence items avg: `42.368`
- compiled memory records avg: `0.000`
- context chars avg: `18814.250`
- build cache hits/misses/writes: `3341 / 0 / 0`
- embedding cache hits/misses/writes: `247238 / 0 / 0`
- answer cache hits/misses/writes: `20 / 480 / 480`
- answer finalizer applied: `0 / 500`

Route audit:

| information_need | n | top_k | avg_query_tokens | p90_query_tokens | max_query_tokens | avg_rows |
|---|---:|---:|---:|---:|---:|---:|
| `current_state` | 22 | 40 | 6179.682 | 6674 | 7053 | 33.773 |
| `fact_lookup` | 183 | 40 | 5358.093 | 5760 | 6897 | 34.262 |
| `list_count` | 119 | 60 | 5834.034 | 6042 | 6792 | 47.798 |
| `profile_preference` | 15 | 40 | 5123.067 | 5566 | 5733 | 34.533 |
| `temporal_lookup` | 161 | 60 | 6705.025 | 7343 | 7752 | 49.354 |

## 对比结论

- vs v36 current LME best: `376` vs `386`，净 `-10`，accuracy `0.752` vs `0.772`
- vs v28 previous LME mainline: `376` vs `383`，净 `-7`，accuracy `0.752` vs `0.766`
- vs v37 row-linked typed memory prompt: `376` vs `372`，净 `+4`，accuracy `0.752` vs `0.744`

v38 相比 v36 的变化：

- gained: `20`
- lost: `30`
- changed-answer net: `-9`
- same-answer judge flip net: `-1`
- `list_count`: gained `3`，lost `10`
- `temporal_lookup`: gained `6`，lost `12`
- `fact_lookup`: gained `9`，lost `6`

错例分布：

- wrong total: `124`
- by information_need: `temporal_lookup 47`，`fact_lookup 33`，`list_count 30`，`current_state 8`，`profile_preference 6`
- by question_type: `multi-session 52`，`temporal-reasoning 27`，`single-session-preference 17`，`knowledge-update 15`，`single-session-assistant 8`，`single-session-user 5`

## 决策

v38 是负向 ablation，不作为当前主线，不跑 LoCoMo full。它相对 v37 有恢复作用，说明“不把 typed memory 直接塞进 answer prompt”是正确方向；但在 v36 底座上，route-scoped top60 + snippet 带来的覆盖收益小于噪声损失，尤其 `list_count` 和 `temporal_lookup`。

下一步不应继续简单扩大 context，也不应把更多 typed memory 直接放入 prompt。应基于 v36/v38 的 lost/gained badcase 和外部方法代码，设计更 general 的 build/query memory organization 或 rerank/selection 机制，让 build-stage memory 参与 evidence selection，而不是扩大最终 reader 负担。

## 输出路径

- predictions: `outputs/formal/stage1_route_snippet_top60_v38_lme_s_full_daf98e7/predictions.jsonl`
- traces: `outputs/formal/stage1_route_snippet_top60_v38_lme_s_full_daf98e7/traces.jsonl`
- metrics: `experiments/formal/stage1_route_snippet_top60_v38_lme_s_full_daf98e7/metrics.json`
- manifest: `experiments/formal/stage1_route_snippet_top60_v38_lme_s_full_daf98e7/manifest.json`
- config snapshot: `experiments/formal/stage1_route_snippet_top60_v38_lme_s_full_daf98e7/config_snapshot.json`
- DeepSeek judge: `experiments/formal/stage1_route_snippet_top60_v38_lme_s_full_daf98e7/deepseek_judge.json`
- evidence recall: `experiments/formal/stage1_route_snippet_top60_v38_lme_s_full_daf98e7/evidence_recall.json`
- comparisons: `judge_comparison_vs_v36.json`，`judge_comparison_vs_v28.json`，`judge_comparison_vs_v37.json`

## Clean 说明

- Prediction 阶段不读取 gold answer、judge output、benchmark label、question_type、category、sample id、row index、qid 或 test feedback。
- `information_need` route 只来自可见问题文本和可见 question_time。
- DeepSeek judge、evidence recall、badcase comparison 只用于离线诊断，不进入 prediction/retrieval/compiler/answer/verifier。
