# v159 Fact Source Interleave Scope Summary

## 目的

诊断风险 #2/#5：把 v158 已用于 `profile_preference/current_state` 的 source-backed `memory_source_interleave` 扩展到 `fact_lookup`，测试 build memory 能否只作为 raw row activation/order signal 来降低 context noise，而不把 typed memory 文本暴露为独立证据。

## 方法

- 配置：`configs/stage1_fact_source_interleave_v159_qwen36_no_think_build4k_cached.json`。
- 父版本：当前 LTS `v158`，commit `f2ad4315b0ae449efdc7f85db04fa4aad051c4ed`。
- 唯一预测侧改动：`fact_lookup` route 增加 `evidence_order=memory_source_interleave`，保留前 32 个 retrieval anchors，再最多提前 4 条 source-linked raw rows，每个 session 最多 1 条。
- Clean 边界：prediction 只用 question text、question-derived route、raw Memory Context、source backpointers 和 query 前构建的 build memory；不使用 gold answer、judge output、benchmark label、sample id、row index、test feedback 或样本级规则。

## 结果

范围：LongMemEval-S `fact_lookup` route-all，183/500 条；LoCoMo 未跑，因为 LME changed subset 已净负。

| 项目 | 结果 |
|---|---:|
| answer diff vs v158 | `46/183` |
| row order changed | `70/183` |
| final row set changed | `24/183` |
| avg query tokens | v158 `5650.186` -> v159 `5646.410` |
| avg context chars | v158 `18343.339` -> v159 `18325.710` |
| changed subset strict | v158 `28/46` -> v159 `26/46` |
| changed subset lenient | v158 `30/46` -> v159 `28/46` |
| gain/loss | strict `3/5`，lenient `3/5` |
| derived LME full | strict/lenient `0.818000 / 0.830000`，低于 v158 `0.822000 / 0.834000` |

## 诊断

- v159 不把 typed memory 文本加入 reader prompt，也没有显式删除 evidence rows，clean 边界成立。
- 但 `memory_source_interleave` 发生在 compiler 字符预算截断之前。row order 改变会让最终 visible row set 也改变，导致 `24/183` 条 fact_lookup 的 raw evidence 覆盖发生漂移。
- 对 `fact_lookup`，source-backed activation 过宽会把“memory-linked 但未必是当前问题精确 slot”的 raw row 提前，从而干扰原 retrieval order 和 evidence set。
- 这个结果说明 #5 不能简单扩大 build-memory source activation；#2 的下一步应先保证 coverage set 稳定，再做 set 内组织、分组或标注。

## 决策

v159 不升 LTS，不跑 LoCoMo。当前 LTS 仍为 v158。

下一步建议：做 coverage-preserving two-stage organization。先按 v158 retrieval/预算确定可见 raw evidence set，再只在这个固定 set 内做 source-backed grouping、dedup/conflict index 或局部排序；任何 memory signal 都不能改变最终 raw evidence 覆盖，除非另有独立 recall 保护。

## Artifacts

- Prediction run: `outputs/diagnostic/stage1_fact_source_interleave_v159_lme_fact_lookup/`
- Changed-answer judge: `outputs/diagnostic/stage1_fact_source_interleave_v159_lme_changed_vs_v158/`
- Experiment record: `experiments/diagnostic/stage1_fact_source_interleave_v159_lme_fact_lookup/`
