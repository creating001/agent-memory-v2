# v151 Current-State Source Repair Scope Summary

## 目的

v151 是 v150 的收窄版。v150 证明 current-state duration repair 有正收益，但 profile/preference repair 会过度改写 recommendation/profile 答案，并带来额外 query token。v151 保留 current-state source repair，移除 profile_preference repair 触发。

## 方法

- 基座：`configs/stage1_selective_source_repair_v150_qwen36_no_think_build4k_cached.json`。
- 新配置：`configs/stage1_current_state_source_repair_v151_qwen36_no_think_build4k_cached.json`。
- repair 范围：仅 `current_state`。
- build/retrieval/compiler/primary answer prompt/source-grounded finalizer：与 v127/v150 保持一致。
- clean 输入：question、route、draft answer、answer JSON、同一份 Memory Context raw rows；不读取 gold、judge、benchmark 标签、sample id、test feedback 或样本级规则。

## Scope 和成本

| Benchmark | samples | base answer cache | repair triggered | repair applied | repair query tokens | avg query tokens |
|---|---:|---:|---:|---:|---:|---:|
| LongMemEval-S full | 500 | hits `500`, misses `0` | `4` | `1` | `16866` | `6173.356` |
| LoCoMo non-adversarial full | 1540 | hits `1540`, misses `0` | `0` | `0` | `0` | `6047.909` |

相对 v150，v151 去掉 profile repair 后，LME avg query tokens 从 `6218.242` 降到 `6173.356`，LoCoMo 从 `6074.776` 降到 `6047.909`。

## Judge 结果

| 对比 | changed subset | v150/base | v151 | delta |
|---|---:|---:|---:|---:|
| LME vs v150 | `1` | strict/lenient `0/1` / `0/1` | `1/1` / `1/1` | strict `+1`, lenient `+1` |
| LoCoMo vs v150 | `2` | strict/lenient `1/2` / `1/2` | `1/2` / `1/2` | strict `+0`, lenient `+0` |
| LME vs v127 | `1` | strict/lenient `0/1` / `0/1` | `1/1` / `1/1` | strict `+1`, lenient `+1` |
| LoCoMo vs v127 | `0` | no answer change | no answer change | `0` |

Derived full LTS metrics:
- LongMemEval-S: strict/lenient `411/500` / `417/500` = `0.822000 / 0.834000`.
- LoCoMo non-adversarial: strict/lenient `1216/1540` / `1256/1540` = `0.789610 / 0.815584`.

## Badcase 结论

- v151 keeps the current-role duration repair: v127 refused, v151 computes the duration from directly relevant tenure evidence and Question Time; dual judge changes from wrong/wrong to correct/correct.
- v151 removes the LME cultural recommendation over-revision introduced by v150. The reverted answer is judged correct/correct in the v151 vs v150 paired run.
- v151 also removes two LoCoMo profile repair rewrites; paired judge is unchanged, so the narrower scope reduces risk and cost without accuracy loss.

## LTS 决策

v151 晋升为当前本地 LTS。它相对 v150 风险更低、query token 更低，LME strict 提升，LME lenient 和 LoCoMo strict/lenient 持平。

仍未解决：#1 granularity/profile generalization，#2 top-k/context noise/rerank，#5 更完整的 memory lifecycle、state/version/conflict handling 和 query-time memory management。

## Artifact

- Full prediction runs:
  - `experiments/diagnostic/stage1_current_state_source_repair_v151_lme_s_full/`
  - `experiments/diagnostic/stage1_current_state_source_repair_v151_locomo_nonadv_full/`
- Changed-answer judge:
  - `experiments/diagnostic/stage1_current_state_source_repair_v151_lme_changed_vs_v150/paired_judge_comparison_vs_v150.json`
  - `experiments/diagnostic/stage1_current_state_source_repair_v151_locomo_changed_vs_v150/paired_judge_comparison_vs_v150.json`
  - `experiments/diagnostic/stage1_current_state_source_repair_v151_lme_changed_vs_v127/paired_judge_comparison_vs_v127.json`
  - `experiments/diagnostic/stage1_current_state_source_repair_v151_locomo_changed_vs_v127/paired_judge_comparison_vs_v127.json`
- Outputs:
  - `outputs/diagnostic/stage1_current_state_source_repair_v151_lme_s_full/`
  - `outputs/diagnostic/stage1_current_state_source_repair_v151_locomo_nonadv_full/`
  - `outputs/diagnostic/stage1_current_state_source_repair_v151_lme_changed_vs_v150/`
  - `outputs/diagnostic/stage1_current_state_source_repair_v151_locomo_changed_vs_v150/`
