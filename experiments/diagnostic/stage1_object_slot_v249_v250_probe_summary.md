# stage1_object_slot_v249_v250_probe_summary

## 目的

验证 build-stage object graph 是否能从 trace-only 走向干净的 source-backed retrieval activation，同时避免把 typed memory 当作证据直接暴露。

## 版本

- v249: `d5867e1`，object-slot collection activation 作为独立 RRF hit list。
- v250: `88c3d20`，object-slot collection activation 改为 tail rescue，不参与 RRF，不进入 protected rerank source。
- base/LTS reference: v248 object graph trace-only probe。

## Clean 口径

- prediction pipeline 不读 gold answer、judge output、benchmark label、sample id、test feedback 或样本级规则。
- v249/v250 answer cache 均只从 v248 prediction-time traces/predictions seed；未读 labels 或 judge。
- changed judge 仅用于 LoCoMo v249 changed-answer offline evaluation，不回流到 retrieval、compiler、answer 或 cache。

## v249 结果

v249 seeded probe:

| Benchmark | object-slot applied | answer diff vs v248 | prompt/retrieval diff | query token delta |
|---|---:|---:|---:|---:|
| LongMemEval-S probe50 | `4/50` | `0/50` | `4/50` | `+10.14` avg |
| LoCoMo non-adversarial probe50 | `6/50` | `5/50` | `6/50` | `+313.58` avg |

LoCoMo changed-answer dual `deepseek-v4-flash`, temperature `0`, default thinking:

| Scope | v248 strict/lenient | v249 strict/lenient | 结论 |
|---|---:|---:|---|
| changed `5` | `2/5` / `4/5` | `2/5` / `2/5` | strict 持平，lenient 下降 `-2` |

诊断：v249 把 object-slot source hits 放进 RRF，宽泛 collection 槽会抢占原 evidence。LoCoMo badcase 主要来自 `activities`、`family`、`beach` 等泛词槽，导致开放列表题答案变窄或变形。v249 不升 LTS。

## v250 结果

v250 probe:

| Benchmark | object-slot audited | answer diff vs v248 | prompt diff | retrieval diff | query token delta |
|---|---:|---:|---:|---:|---:|
| LongMemEval-S probe50 | `4/50` | `0/50` | `0/50` | `0/50` | `0` |
| LoCoMo non-adversarial probe50 | `6/50` | `0/50` | `0/50` | `0/50` | `0` |

Token / context:

| Benchmark | avg build tokens | avg query tokens | avg context chars | avg evidence |
|---|---:|---:|---:|---:|
| LongMemEval-S probe50 | `86398.54` | `5677.40` | `18651.60` | `35.38` |
| LoCoMo non-adversarial probe50 | `45868.00` | `6543.56` | `17078.16` | `49.04` |

v250 保留了 build object-slot 的 source-backed activation trace，但不让它改变已满候选集的排序；probe 上性能和 v248 行为完全一致，因此不需要 changed-answer judge。

## 决策

- v249: rejected diagnostic，不升 LTS。
- v250: safe candidate。它修复 v249 的排序抢占风险，保持 probe 行为和 token 成本不回退；但当前 probe 中没有带来 accuracy 提升，是否升 LTS 需要 full run 或更多覆盖验证。

## 输出

- v249 seeded LME: `experiments/diagnostic/stage1_object_slot_collection_activation_v249_lme_probe50_seeded/`
- v249 seeded LoCoMo: `experiments/diagnostic/stage1_object_slot_collection_activation_v249_locomo_probe50_seeded/`
- v249 changed judge: `experiments/diagnostic/stage1_object_slot_collection_activation_v249_probe50_changed_vs_v248/`
- v250 LME: `experiments/diagnostic/stage1_object_slot_tail_rescue_v250_lme_probe50/`
- v250 LoCoMo: `experiments/diagnostic/stage1_object_slot_tail_rescue_v250_locomo_probe50/`
