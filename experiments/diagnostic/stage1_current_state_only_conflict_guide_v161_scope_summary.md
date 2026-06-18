# v161 Current-State Only Conflict Guide Scope Summary

## 目的

承接 v159/v160 的负向结论，诊断风险 #2/#5：是否可以把 long-profile `Update/Conflict Candidate Chain` 从 generic `fact_lookup` 上移除，只保留给真正需要 lifecycle/conflict reasoning 的 `current_state`，从而降低 context noise 和过宽 memory lifecycle activation。

## 方法

- 配置：`configs/stage1_current_state_only_conflict_guide_v161_qwen36_no_think_build4k_cached.json`。
- 父版本：当前 LTS `v158`，commit `f2ad4315b0ae449efdc7f85db04fa4aad051c4ed`。
- 唯一预测侧改动：long-turn profile 的 `update_conflict_guide_information_needs` 从 `["current_state", "fact_lookup"]` 收窄为 `["current_state"]`。
- 不改 retrieval、row ordering、selected context、answer prompt schema、repair trigger、finalizer 或 build memory。
- Clean 边界：prediction 只用 question text、question-derived route、raw Memory Context、source backpointers 和 query 前构建的 build memory；不使用 gold answer、judge output、benchmark label、sample id、row index、test feedback 或样本级规则。

## 结果

范围：LongMemEval-S `fact_lookup` route-all，183/500 条；LoCoMo 未跑，因为该改动只影响 long-turn profile 的 fact_lookup，且 LME changed subset strict 已净负。

| 项目 | 结果 |
|---|---:|
| answer diff vs v158 | `39/183` |
| row order changed | `0/183` |
| final row set changed | `0/183` |
| Update/Conflict guide applied | v158 `32/183` -> v161 `0/183` |
| avg query tokens | v158 `5650.186` -> v161 `5573.175` |
| avg context chars | v158 `18343.339` -> v161 `18051.055` |
| changed subset strict | v158 `23/39` -> v161 `22/39` |
| changed subset lenient | v158 `25/39` -> v161 `25/39` |
| gain/loss | strict `3/4`，lenient `4/4` |
| derived LME full | strict/lenient `0.820000 / 0.834000`，strict 低于 v158 `0.822000` |

## 诊断

- v161 成功降低了 fact_lookup 上的 guide/token/noise，并保持 raw evidence order/set 完全不变。
- 但仅移除 guide 仍会造成 `39/183` answer diff，changed subset strict 净负 `-1`。
- 这说明 v158 的 fact_lookup conflict guide 虽然从 #5 角度偏宽，但在部分 fact/profile-like 问题上仍能稳定 reader 注意力；简单移除会带来 strict 损失。
- 下一步 #2/#5 不应再用 broad fact prompt 开关做二元取舍；更稳的方向是更细的 question gate 或非答案影响的 manifest/audit，或者只在 current_state lifecycle repair 内继续增强。

## 决策

v161 不升 LTS，不跑 LoCoMo。当前 LTS 仍为 v158。

## Artifacts

- Prediction run: `outputs/diagnostic/stage1_current_state_only_conflict_guide_v161_lme_fact_lookup/`
- Changed-answer judge: `outputs/diagnostic/stage1_current_state_only_conflict_guide_v161_lme_changed_vs_v158/`
- Experiment record: `experiments/diagnostic/stage1_current_state_only_conflict_guide_v161_lme_fact_lookup/`
