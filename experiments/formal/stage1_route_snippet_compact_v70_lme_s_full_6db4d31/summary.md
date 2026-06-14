# v70 Route Snippet Compact

## 目的

验证一个低噪声 query/compiler 假设：v42 的 `current_state` 和 `list_count` 在高 query token 桶里错误率更高，可能存在上下文噪声。v70 不改 build、retrieval、route、temporal workpad、evidence_report 或 answer model，只对 `current_state` 和 `list_count` 使用 `role_query_snippet` 压缩长行，temporal/fact/profile 保持 v42 full rows。

本实验参考了外部方法中的 source-turn materialization、episodic/source 回链和 staged retrieval 思想，但没有迁移 benchmark-specific guardrail；prediction 只使用 question text、question time、raw memory context、build memory source links 和运行时 route。

## 结论

v70 是负向结果，不作为主线配置保留。

- DeepSeek judge full accuracy：0.758，379/500，invalid=0。
- v42 复现控制：0.772，386/500。
- prediction changed：26/500。
- changed predictions：CORRECT->WRONG 13，WRONG->CORRECT 3，CORRECT->CORRECT 2，WRONG->WRONG 8。
- 主要损失来自 `list_count`：CORRECT->WRONG 10，WRONG->CORRECT 2。
- evidence_recall：1.0，500/500。

关键判断：对 list/count 和 current-state 题做 query-focused snippet 会丢失 answer 所需的细节，尤其是列表候选、排除项、数量边界和同 session 上下文。query token 不是越多越好，但也不能靠机械截短行来换分。

## Token 成本

- avg build tokens：80346.246。
- total build tokens：40173123。
- build token 口径：逻辑 cold-build 成本；build cache 命中只减少本机重复 API 调用，不改变方法成本。
- avg query tokens：5859.174。
- total query tokens：2929587。
- answer max input/output：131072 / 16384。
- answer cache：359 hits / 141 misses / 141 writes。
- cache 控制：先用 v42 clean prediction traces seed v70 新 namespace，只让 prompt 真正改变的 `current_state/list_count` 样本重新调用 answer；seed 脚本只读 prediction traces，不读 label/judge。

## 配置与 clean 记录

- benchmark/subset：LongMemEval-S full。
- config：`configs/stage1_route_snippet_compact_v70_cached.json`。
- formal config snapshot：`experiments/formal/stage1_route_snippet_compact_v70_lme_s_full_6db4d31/config_snapshot.json`。
- git commit：`6db4d31ecaeb1e0e028bbbfb497158e37f4dbbf4`。
- prediction dirty：false。
- clean 口径：prediction pipeline 未使用 gold answer、judge 输出、benchmark 标签、sample id、row index、question_type 或 test feedback。

## 输出路径

- predictions：`outputs/formal/stage1_route_snippet_compact_v70_lme_s_full_6db4d31/predictions.jsonl`
- traces：`outputs/formal/stage1_route_snippet_compact_v70_lme_s_full_6db4d31/traces.jsonl`
- metrics：`experiments/formal/stage1_route_snippet_compact_v70_lme_s_full_6db4d31/metrics.json`
- judge：`experiments/formal/stage1_route_snippet_compact_v70_lme_s_full_6db4d31/deepseek_judge.json`
- evidence recall：`experiments/formal/stage1_route_snippet_compact_v70_lme_s_full_6db4d31/evidence_recall.json`
- v42 对比：`experiments/formal/stage1_route_snippet_compact_v70_lme_s_full_6db4d31/judge_comparison_vs_v42_repro.json`

## 下一步

不要继续做纯 snippet / 纯压缩。下一阶段应保留 raw row 完整性，同时增加更明确的候选集合组织：例如 list/count 的 included/excluded candidate set、current-state 的 conflict/update chain、temporal 的 endpoint chain。目标是提高 evidence density，而不是减少原始证据内容。
