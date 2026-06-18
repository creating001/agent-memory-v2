# v150 Selective Source Repair Scope Summary

## 目的

v150 解决 v149 暴露的问题：broad answer-slot checklist 会在 LME 上过度拒答。新版本保留 v127 的 retrieval、row ordering、primary answer prompt 和 source-grounded finalizer，只在预测阶段 draft 明确不充分、拒答或 modal abstention 时，触发窄范围 source verifier/repair。

## 方法

- 基座：`configs/stage1_superseded_source_chain_v127_qwen36_no_think_build4k_cached.json`。
- 新配置：`configs/stage1_selective_source_repair_v150_qwen36_no_think_build4k_cached.json`。
- repair 范围：`current_state`、`profile_preference`。
- repair 输入：question、route、draft answer、answer JSON、同一份 Memory Context raw rows。
- current-state 新规则：允许从直接相关 raw rows 和 Question Time 计算简单 tenure/duration；current/previous state 必须匹配被问实体和 state relation；如果问题同时问 previous/current，需要同时保留。
- 借鉴外部方法但保持 clean：EverOS 的 source-of-truth/derived index 思路、SimpleMem 的二次 verification 与避免盲目扩上下文、MIA reflection 的 evidence sufficiency 检查，以及 memory consolidation 的 lifecycle/conflict 方向。

## Clean 边界

预测、repair、cache 和配置均不读取 gold answer、judge output、benchmark 标签、sample id、test feedback 或样本级规则。Changed-answer judge 只在预测完成后用于离线评估，不反馈到算法。

## Scope 和成本

| Benchmark | samples | base answer cache | repair triggered | repair applied | repair query tokens |
|---|---:|---:|---:|---:|---:|
| LongMemEval-S full | 500 | hits `500`, misses `0` | `9` | `2` | `39309` |
| LoCoMo non-adversarial full | 1540 | hits `1540`, misses `0` | `7` | `2` | `41375` |

v150 只改最终答案，不改 build/retrieval/compiler row set。实际答案变化：LME `2/500`，LoCoMo `2/1540`。

## Judge 结果

| Benchmark | changed subset v127 | changed subset v150 | delta | derived full v150 |
|---|---:|---:|---:|---:|
| LongMemEval-S | strict/lenient `1/2` / `1/2` | strict/lenient `1/2` / `2/2` | strict `+0`, lenient `+1` | strict/lenient `410/500` / `417/500` = `0.820000 / 0.834000` |
| LoCoMo non-adversarial | strict/lenient `1/2` / `1/2` | strict/lenient `1/2` / `1/2` | strict `+0`, lenient `+0` | strict/lenient `1216/1540` / `1256/1540` = `0.789610 / 0.815584` |

`derived full` 使用 v127 fresh full dual judge records，对 v150 改动答案的 record 替换为 changed-answer paired judge 结果；未变化答案不重跑 judge。

## Badcase 结论

- LME current-role duration：v127 拒答，v150 从总 tenure 与晋升耗时推导出 current role duration；dual judge 从 wrong/wrong 到 correct/correct。
- LME cultural recommendation：v150 加入 Nigerian/Mozambican culture 偏好后，一个 judge 认为过具体；strict 从 correct/correct 到 correct/wrong，但 lenient 保持正确。
- LoCoMo Dodge Charger vs Forester：v150 删除未在 Memory Context 逐字出现的具体车型名，改为 classic muscle car category；judge 保持 correct/correct。
- LoCoMo Whispering Falls：v150 从 inspiration 相关 raw rows 给出推测，但 judge 仍 wrong/wrong；说明 verifier 仍需更稳地区分 direct support 与 weak inference。

## LTS 决策

v150 晋升为当前本地 LTS。理由是相对 v127 降低 #4 final answer guardrail 和 #5 query-time state reasoning 风险，changed-answer paired dual judge 非负，LongMemEval-S lenient 小幅提升，LoCoMo 持平。

仍未解决：#1 granularity/profile generalization，#2 top-k/context noise/rerank，#5 更完整的 memory lifecycle、state/version/conflict handling 和 query-time memory management。

## Artifact

- Full prediction runs:
  - `experiments/diagnostic/stage1_selective_source_repair_v150_lme_s_full/`
  - `experiments/diagnostic/stage1_selective_source_repair_v150_locomo_nonadv_full/`
- Changed-answer judge:
  - `experiments/diagnostic/stage1_selective_source_repair_v150_lme_changed_answers/paired_judge_comparison_vs_v127.json`
  - `experiments/diagnostic/stage1_selective_source_repair_v150_locomo_changed_answers/paired_judge_comparison_vs_v127.json`
- Outputs:
  - `outputs/diagnostic/stage1_selective_source_repair_v150_lme_s_full/`
  - `outputs/diagnostic/stage1_selective_source_repair_v150_locomo_nonadv_full/`
  - `outputs/diagnostic/stage1_selective_source_repair_v150_lme_changed_answers/`
  - `outputs/diagnostic/stage1_selective_source_repair_v150_locomo_changed_answers/`
