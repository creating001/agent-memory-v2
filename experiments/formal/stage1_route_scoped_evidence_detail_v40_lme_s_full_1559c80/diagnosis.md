# Diagnosis for v40 LME full

## 结论

v40 route-scoped evidence detail 没有超过 v36，不应继续跑 LoCoMo full。

- v40: `0.742` (`371/500`)
- v36: `0.772` (`386/500`)
- delta: `-15`
- evidence_recall: `1.0`

## 主要现象

v40 的改动只影响 `list_count` 和 `temporal_lookup` 的 detailed evidence_report prompt：

- `list_count` detail prompts: `119/119`
- `temporal_lookup` detail prompts: `161/161`
- other routes detail prompts: `0/220`
- avg_compiled_memory_records: `0.0`
- retrieval top_k: `40`
- avg query tokens: `5910.438`

它相对 v39 有恢复，但相对 v36 仍净负：

- vs v36 gained: `22`
- vs v36 lost: `37`
- lost_by_information_need: `temporal_lookup 13`, `list_count 10`, `fact_lookup 10`, `current_state 4`
- gained_by_information_need: `fact_lookup 9`, `temporal_lookup 7`, `list_count 4`, `current_state 1`, `profile_preference 1`

## 判断

reader-side detailed evidence discipline 对部分 list/temporal 样本有效，但带来的保守、选择偏移或 JSON evidence_report variance 更大。LME 的主要瓶颈不是继续增加 prompt 操作规则，而是需要更可靠的 build/query-side organization：

- operand/table 结构应在 compiler 中形成更稳定的候选集合，而不是只靠 answer model 自己整理。
- temporal/event/state 应在 build memory 或 compiler 中形成更清晰的 event-role / validity view。
- profile/preference 仍然弱，不能靠 list/temporal detail 解决。

## 后续建议

- 不跑 v40 LoCoMo full。
- 顶层 v40 config 删除，只保留本 formal 目录中的 `config_snapshot.json` 追溯。
- 下一轮方法要在运行前重新分析 v36/v40 lost cases，并重点参考外部代码里的 scoped evidence extraction / operand table / temporal state 管理，但必须保持 general 和 clean。
- 优先探索 build-stage 或 compiler-stage 的结构化 operand/event view；不要继续单纯加 reader prompt。

## Offline Outputs

- DeepSeek judge: `experiments/formal/stage1_route_scoped_evidence_detail_v40_lme_s_full_1559c80/deepseek_judge.json`
- judge metrics summary: `experiments/formal/stage1_route_scoped_evidence_detail_v40_lme_s_full_1559c80/judge_metrics_summary.json`
- comparison: `experiments/formal/stage1_route_scoped_evidence_detail_v40_lme_s_full_1559c80/judge_comparison_vs_v36_v39_v38.json`
- badcase digest: `experiments/formal/stage1_route_scoped_evidence_detail_v40_lme_s_full_1559c80/badcase_digest.json`
- evidence recall: `experiments/formal/stage1_route_scoped_evidence_detail_v40_lme_s_full_1559c80/evidence_recall.json`
