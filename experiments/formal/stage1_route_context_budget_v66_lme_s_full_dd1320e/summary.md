# v66 Route Context Budget

## 目的

验证一个 query-side 噪声控制假设：v42 的 query tokens 接近 6K，但更多上下文不一定更好。v66 在 v42 基础上只收窄 `temporal_lookup`、`list_count`、`current_state` 的 compiler evidence budget，build、retrieval、answer model 和 clean 输入保持不变。

## 结论

v66 是负向结果，不作为主线。

- DeepSeek judge accuracy：0.754，377/500，invalid=0。
- v42 修复控制 accuracy：0.772，386/500。
- vs v42 修复控制：CORRECT->WRONG 27，WRONG->CORRECT 18，净 -9。
- prediction changed：102/500。
- evidence_recall：1.0。

v66 证明“减少 query token / 减少上下文”不是单调正向。固定按 route 截断 30 行 / 15500 chars 会减少噪声，也会丢失 answer model 需要的细节。

## Token 成本

- avg build tokens：80346.246，与 v42 相同。
- total build tokens：40173123。
- avg query tokens：5235.538，比 v42 修复控制少 629.168。
- total query tokens：2617769，比 v42 修复控制少 314584。
- answer max input/output：131072 / 16384。

## 配置与 clean 记录

- benchmark/subset：LongMemEval-S full。
- config：`configs/stage1_route_context_budget_v66_cached.json`。
- git commit：`dd1320e66ffc18a3add490ffbd5602d359b60acf`。
- dirty：false。
- clean 口径：不使用 gold answer、judge output、benchmark 标签、sample id、test feedback 或样本级规则。

## 输出路径

- predictions：`outputs/formal/stage1_route_context_budget_v66_lme_s_full_dd1320e/predictions.jsonl`
- traces：`outputs/formal/stage1_route_context_budget_v66_lme_s_full_dd1320e/traces.jsonl`
- metrics：`experiments/formal/stage1_route_context_budget_v66_lme_s_full_dd1320e/metrics.json`
- judge：`experiments/formal/stage1_route_context_budget_v66_lme_s_full_dd1320e/deepseek_judge.json`
- evidence recall：`experiments/formal/stage1_route_context_budget_v66_lme_s_full_dd1320e/evidence_recall.json`
- v42 对比：`experiments/formal/stage1_route_context_budget_v66_lme_s_full_dd1320e/judge_comparison_vs_v42.json`

## 下一步

不要继续做固定 row/char 截断。更合理的方向是：保留 raw rows，但在 build/query 之间增加更精确的候选分层或证据组织，让模型优先看关键候选，同时不硬截聚合所需细节。
