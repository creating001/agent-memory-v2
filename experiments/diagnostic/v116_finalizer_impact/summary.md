# v116 finalizer impact 诊断

## 目的

检查当前 v116 LTS 中 answer finalizer 的真实作用，特别是它是否还依赖容易被质疑的机械算术/相对时间规则。本诊断只用于离线审计；gold 和 judge 不进入 prediction pipeline。

## 输入

- v116 LME traces：`outputs/formal/stage1_extended_selected_context_v116_qwen36_no_think_build4k_lme_s_full_aeac792/traces.jsonl`
- v110/v116-compatible LME dual judge：`experiments/formal/stage1_modal_grounded_inference_v110_qwen36_no_think_build4k_lme_s_full_2f33213/deepseek_dual_judge.json`
- draft predictions：`outputs/diagnostic/v116_finalizer_impact/lme_finalizer_applied_draft_predictions.jsonl`
- draft dual judge：`experiments/diagnostic/v116_finalizer_impact/lme_draft_dual_judge.json`

## 结果

| Scope | strict | lenient |
|---|---:|---:|
| draft-only on finalizer-applied 8 | `1/8` | `1/8` |
| v116 final on same 8 | `1/8` | `2/8` |

v116 LME finalizer 实际触发 `8/500`，全部是 `missing_detail_from_structured_answer`。LoCoMo v116 finalizer 触发 `0/1540`。

## 结论

当前 LTS 的收益不来自相对时间、日期差、金额差、平均值或 count detail 等机械算答案规则。保留 broad mechanical finalizer 的解释成本高于收益。因此新增 v121，把 finalizer 收窄为 `source_grounded_consistency_guard`：只允许 source-grounded missing detail，不再做机械答案计算。
