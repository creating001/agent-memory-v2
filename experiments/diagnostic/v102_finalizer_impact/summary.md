# v102 finalizer impact 诊断

## 目的

检查 v102/v110 中 `structured_evidence_mechanical` finalizer 是否存在 design-for-benchmark 风险，以及它对 accuracy 的真实贡献。该诊断只在离线阶段读取 gold/judge，用于分析；预测逻辑和 cache 构建不读取 labels、judge、benchmark category、sample id 或 test feedback。

## 输入

- LME v102 traces：`outputs/formal/stage1_spacing_profile_v102_qwen36_no_think_build4k_lme_s_full_4fc01c0/traces.jsonl`
- LoCoMo v102 traces：`outputs/formal/stage1_spacing_profile_v102_qwen36_no_think_build4k_locomo_nonadv_full_1526d1c/traces.jsonl`
- Draft predictions：`outputs/diagnostic/v102_finalizer_impact/*_draft_predictions_finalizer_applied.jsonl`
- Draft dual judge：`lme_draft_dual_judge.json`，`locomo_draft_dual_judge.json`

## 结果

| Benchmark | finalizer 触发 | draft lenient | final lenient | 净变化 |
|---|---:|---:|---:|---:|
| LongMemEval-S | 54 | 22/54 | 27/54 | +5 |
| LoCoMo non-adversarial | 46 | 40/46 | 34/46 | -6 |

LME 触发原因：

- `missing_detail_from_structured_answer`: 47
- `evidence_report_count_answer_detail`: 5
- `evidence_report_money_difference`: 1
- `evidence_report_date_endpoint_duration`: 1

LoCoMo 触发原因：

- `evidence_report_relative_time_calculation`: 46

## 诊断

- LME 的 non-relative mechanical finalizer 仍有净正收益，尤其是 missing detail / count detail / money/date calculation；直接全关会有风险。
- LoCoMo 的 relative-time calculation 是净负：很多 draft 的相对时间表达已经被 judge 接受，机械改写反而会引入错误日期或过窄表述。
- relative-time finalizer 也是当前最像 benchmark answer-format solver 的规则。关闭它同时降低 general 风险和 LoCoMo 误改风险。

## 下一步

建立 v113：继承 v110 modal-only grounded inference，只关闭全局 `enable_relative_time_calculation`，其余 build/retrieval/compiler/backbone 不变。先跑 LongMemEval-S full；若不低于 v102/v110 主指标，再跑 LoCoMo non-adversarial full。
