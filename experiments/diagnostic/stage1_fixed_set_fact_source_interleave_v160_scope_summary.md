# v160 Fixed-Set Fact Source Interleave Scope Summary

## 目的

承接 v159 的负向结论，继续诊断风险 #2/#5：能否让 build memory 只在已经选定的 raw evidence set 内做 source-backed organization，避免 ordering-before-truncation 改变最终证据覆盖。

## 方法

- 配置：`configs/stage1_fixed_set_fact_source_interleave_v160_qwen36_no_think_build4k_cached.json`。
- 父版本：当前 LTS `v158`，commit `f2ad4315b0ae449efdc7f85db04fa4aad051c4ed`。
- 代码改动：新增 `fixed_set_memory_source_interleave` evidence order。
- 预测侧语义：先按原 retrieval order 和 compiler budget 选定 visible raw Memory Context rows；随后仅在该固定 set 内用 source-linked build memory 调整顺序。typed memory 文本不进入 reader prompt，也不能改变最终 raw evidence set。
- Clean 边界：prediction 只用 question text、question-derived route、raw Memory Context、source backpointers 和 query 前构建的 build memory；不使用 gold answer、judge output、benchmark label、sample id、row index、test feedback 或样本级规则。

## 结果

范围：LongMemEval-S `fact_lookup` route-all，183/500 条；LoCoMo 未跑，因为 LME changed subset strict 已净负。

| 项目 | 结果 |
|---|---:|
| answer diff vs v158 | `49/183` |
| row order changed | `55/183` |
| final row set changed | `0/183` |
| avg query tokens | v158 `5650.186` -> v160 `5728.175` |
| avg context chars | v158 `18343.339` -> v160 `18343.339` |
| changed subset strict | v158 `28/49` -> v160 `27/49` |
| changed subset lenient | v158 `30/49` -> v160 `30/49` |
| gain/loss | strict `7/8`，lenient `8/8` |
| derived LME full | strict/lenient `0.820000 / 0.834000`，strict 低于 v158 `0.822000` |

## 诊断

- v160 修复了 v159 的 coverage drift：final row set changed 从 `24/183` 降到 `0/183`。
- 但仅改变 fixed set 内 row order 仍会引发较多 answer diff，并带来小幅 query token 上升。
- LME fact changed subset strict 净负 `-1`，说明 source-backed fact ordering 即使不改变 coverage，也会扰动 reader 对 slot matching 的注意力。
- 结论：#2/#5 下一步不应再把 memory signal 用作 broad fact row ordering；更稳方向是非重排式组织，例如固定 evidence set 上的轻量 session/group metadata，或只对 current_state/conflict 这类 memory lifecycle 强相关 route 使用。

## 决策

v160 不升 LTS，不跑 LoCoMo。当前 LTS 仍为 v158。

## Artifacts

- Prediction run: `outputs/diagnostic/stage1_fixed_set_fact_source_interleave_v160_lme_fact_lookup/`
- Changed-answer judge: `outputs/diagnostic/stage1_fixed_set_fact_source_interleave_v160_lme_changed_vs_v158/`
- Experiment record: `experiments/diagnostic/stage1_fixed_set_fact_source_interleave_v160_lme_fact_lookup/`
