# v172 profile preference value guard

## 结论

`configs/stage1_profile_preference_value_guard_v172_qwen36_no_think_build4k_cached.json` 晋升为当前本地 LTS。v172 继承 v171 的 build、retrieval、answer、repair 和 cache 设置，只新增一个窄的 source-grounded finalizer 分支：当 draft 已经拒答、问题直接询问 favorite/preference/like/interest 的具体值、且预测期 `evidence_report` 中只有一个非含糊 preference-like support `value` 时，保留该值。

该分支不使用 gold answer、judge output、benchmark label、sample id、test feedback 或样本级规则；gold/judge 只用于离线诊断和 paired evaluation。

## 指标

| Benchmark | v172 结论 |
|---|---|
| LongMemEval-S full | v172 与 v171 answer diff `0/500`；继承 v171 patched full strict/lenient `415/500`、`420/500`，即 `0.830000 / 0.840000`。 |
| LoCoMo non-adversarial full | v172 与 v171 answer diff `1/1540`；changed-answer paired dual judge strict/lenient `0/1 -> 1/1`；patched full strict/lenient `1218/1540`、`1257/1540`，即 `0.790909 / 0.816234`。 |

变化样本：

| record_key | question | v171 | v172 | judge |
|---|---|---|---|---|
| `6658015006384a53816e150c` | `What is Evan's favorite food?` | `The provided information is not enough.` | `ginger snaps` | v171 `0/1`，v172 `1/1` |

## 触发面

- LME：answer diff `0/500`；finalizer applied `2/500`，reason 仍为 `source_value_specificity_preservation` 和 `numeric_slot_label_preservation`，没有新增 profile preference 触发。
- LoCoMo：answer diff `1/1540`；finalizer applied `9/1540`，其中新增 `profile_preference_value_preservation` 正好 1 条。
- blocked cases：recommendation/advice/modal/list/count/temporal/option 问题、多候选 support、代词/unnamed/unknown 等含糊值不触发。

## 成本和复现

- LME prediction：`outputs/diagnostic/stage1_profile_preference_value_guard_v172_lme_s_full/predictions.jsonl`
- LME traces：`outputs/diagnostic/stage1_profile_preference_value_guard_v172_lme_s_full/traces.jsonl`
- LoCoMo prediction：`outputs/diagnostic/stage1_profile_preference_value_guard_v172_locomo_nonadv_full/predictions.jsonl`
- LoCoMo traces：`outputs/diagnostic/stage1_profile_preference_value_guard_v172_locomo_nonadv_full/traces.jsonl`
- changed-answer judge：`experiments/diagnostic/stage1_profile_preference_value_guard_v172_changed_vs_v171/`
- LME cache：build hits/misses `3341/0`，answer hits/misses `500/0`，repair hits/misses `6/0`。
- LoCoMo cache：build hits/misses `12411/0`，answer hits/misses `1540/0`，repair hits/misses `0/0`。
- logical token accounting：LME avg build/query tokens `85393.566 / 6239.336`；LoCoMo avg build/query tokens `62015.57402597403 / 6047.909090909091`。

## 风险结论

v172 降低 #4 over-abstention / answer surface loss 和 #5 profile-preference query-time memory activation 风险，同时 LoCoMo strict/lenient 提升且 LME 不退。它仍未解决 #1 granularity/profile 泛化、#2 top-k/context noise/rerank、#3 selected-context 泛化，以及更广泛的 #5 lifecycle/update/conflict reasoning。

下一步优先做 coverage-preserving route-aware context organization 和 answer-slot-aware lifecycle/update/conflict verifier；typed memory 继续只做 source-backed activation/index，不替代原文证据。
