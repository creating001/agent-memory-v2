# v71 Temporal Order Router

## 目的

验证一个通用 question-text router 修正：把 `which/who ... first`、`from earliest to latest`、`order ... first/latest`、`date ... first` 这类顺序问题路由到 `temporal_lookup`，避免被裸 `which` 归入 `list_count`，或被 `latest` 归入 `current_state`。

v71 不改 build、retrieval、compiler、answer model、evidence_report 或 operation workpad。它只改变运行时 route，仍只使用 question text 和可见 metadata，不使用任何离线答案或评测信息。

## 结论

v71 是中性/未达标结果，不作为当前主线保留。

- DeepSeek judge full accuracy：0.770，385/500，invalid=0。
- v42 复现控制：0.772，386/500。
- prediction changed：11/500。
- changed predictions：WRONG->CORRECT 1，CORRECT->WRONG 1，CORRECT->CORRECT 6，WRONG->WRONG 3。
- unchanged predictions 的 judge variance：CORRECT->WRONG 6，WRONG->CORRECT 5。
- evidence_recall：1.0，500/500。

判断：temporal-order route 修正是 clean 且 general 的，但在 LongMemEval-S full 上没有净 accuracy 收益。它修复了一个 `Who did I meet first...` case，也破坏了一个 `Ferrari vs Porsche` abstention case。当前代码不应长期保留该 router 改动，正式结果保留在本目录，顶层 config 和 src 改动撤出主线。

## Token 成本

- avg build tokens：80346.246。
- total build tokens：40173123。
- avg query tokens：5912.454。
- total query tokens：2956227。
- answer max input/output：131072 / 16384。
- answer cache：462 hits / 38 misses / 38 writes。
- cache 控制：先用 v42 clean prediction traces seed v71 新 namespace，只让 route 改变导致 prompt 改变的样本重新调用 answer。

## 配置与 clean 记录

- benchmark/subset：LongMemEval-S full。
- config：`configs/stage1_temporal_order_router_v71_cached.json`。
- formal config snapshot：`experiments/formal/stage1_temporal_order_router_v71_lme_s_full_6e75890/config_snapshot.json`。
- git commit：`6e75890ab9e9071e2eab7f8c8a4c8efbd938f17b`。
- prediction dirty：false。
- clean 口径：prediction pipeline 未使用 gold answer、judge 输出、benchmark 标签、sample id、row index、question_type 或 test feedback。

## 输出路径

- predictions：`outputs/formal/stage1_temporal_order_router_v71_lme_s_full_6e75890/predictions.jsonl`
- traces：`outputs/formal/stage1_temporal_order_router_v71_lme_s_full_6e75890/traces.jsonl`
- metrics：`experiments/formal/stage1_temporal_order_router_v71_lme_s_full_6e75890/metrics.json`
- judge：`experiments/formal/stage1_temporal_order_router_v71_lme_s_full_6e75890/deepseek_judge.json`
- evidence recall：`experiments/formal/stage1_temporal_order_router_v71_lme_s_full_6e75890/evidence_recall.json`
- v42 对比：`experiments/formal/stage1_temporal_order_router_v71_lme_s_full_6e75890/judge_comparison_vs_v42_repro.json`

## 下一步

不要把单独 router 修正作为突破方向。更有价值的方向仍是 source-preserving candidate organization：对 order/list/count/current-state 问题构造候选链或冲突链，但最终保留完整 raw rows 供 answer 定案。
