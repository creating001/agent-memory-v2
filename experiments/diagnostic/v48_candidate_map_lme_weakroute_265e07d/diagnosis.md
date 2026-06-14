# v48 诊断

## 失败原因

v48 的 Candidate Evidence Map 是 clean 的，但全弱路由开启后不划算：

1. Token 超预算：按 v42 full route mix 估算，avg query tokens 从 `5865.644` 增到 `6250.456`。
2. Accuracy 净负：same-87 从 v42 `59/87` 退到 v48 `56/87`。
3. 副作用集中在 `temporal_lookup`、`profile_preference` 和 `list_count`，说明短候选图会放大错误候选或让 answer 过度改写。

## 离线对比

文件：`judge_comparison_vs_v42_same87.json`

- n_shared: `87`
- v42 correct: `59`
- v48 correct: `56`
- gains: `6`
- losses: `9`
- answer_changed: `32`

局部正向：

- `current_state` 从 `12/22` 到 `14/22`。
- 修复例子包括 Instagram followers `1250 -> 1300`、current apartment false premise、most recent family trip。

主要回退：

- `temporal_lookup` 从 `22/30` 到 `20/30`，例如 Instagram follower increase、cooking-for-friend 事件定位错误。
- `profile_preference` 从 `10/15` 到 `8/15`，部分 same-answer 或更长答案被 judge 判错。
- `list_count` 从 `15/20` 到 `14/20`，例如 magazine subscriptions 和 support group sessions。

## Token 与成本

文件：`full_query_token_estimate.json`

按 selected deltas 和 v42 full route counts 估算：

- current_state avg delta: `+624.682`, full count `22`
- list_count avg delta: `+613.550`, full count `119`
- profile_preference avg delta: `+588.333`, full count `15`
- temporal_lookup avg delta: `+601.400`, full count `161`
- weighted full avg delta: `+384.812`

这说明 candidate map 需要进一步 route-scope 和压缩，不能在 317/500 条上打开。

## Clean 复核

文件：`prompt_clean_scan.json`

- literal forbidden findings: `0`
- Candidate Evidence Map 只使用 question text、question-derived route、retrieved raw rows、row date/role/rank。
- 本诊断的 subset 选择不使用 labels/judge/question_type/category。

## 取舍

保留：

- Candidate map 作为可关闭模块留在代码中，后续只做 current_state 或更窄 route ablation。
- current_state 局部正向值得继续试，但必须 token-safe。

舍弃：

- 不保留 `configs/stage1_candidate_evidence_map_v48_cached.json` 顶层配置。
- 不跑 v48 LongMemEval-S full。
- 不把 candidate map 扩展到 list/profile/temporal 全弱路由。

## 下一步建议

v49 应该只针对 current_state：

- `candidate_guide_information_needs=["current_state"]`
- 降低 `candidate_guide_max_rows` 到 `4`
- 降低 `candidate_guide_snippet_chars` 到 `100-120`
- 保持 v42 其他 route 完全不变

这样 full avg token 增量约只覆盖 22/500 条 current_state，有机会保留 current_state 正收益并通过 6K 预算。v49 先跑 current_state same-22 + route-stratified sanity，不直接 full。
