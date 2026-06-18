# v173 source-grounded modal inference repair

## 结论

`configs/stage1_source_grounded_modal_inference_repair_v173_qwen36_no_think_build4k_cached.json` 晋升为当前本地 LTS。v173 继承 v172 的 build、retrieval、answer 和 source-grounded finalizer，只新增一个显式配置的窄 repair trigger：当 draft 是拒答、问题是 modal yes/no 形式、不是 recommendation/external-name/list/count/which-what/sensitive-attribution 题，且预测期 `evidence_report` 至少有 2 个 source-backed support items 并带有动机、偏好、因果、情绪或结果锚点时，才调用 answer verifier。

该机制只使用 question、route、draft JSON、visible Memory Context 和预测期 evidence_report；不使用 gold answer、judge output、benchmark label、sample id、test feedback 或样本级规则。gold/judge 只用于离线 changed-answer evaluation。

## 指标

| Benchmark | v173 结论 |
|---|---|
| LongMemEval-S full | v173 与 v172 answer diff `0/500`；继承 v172 patched full strict/lenient `415/500`、`420/500`，即 `0.830000 / 0.840000`。 |
| LoCoMo non-adversarial full | v173 与 v172 answer diff `2/1540`；changed-answer paired dual judge strict/lenient `0/2 -> 2/2`；patched full strict/lenient `1220/1540`、`1259/1540`，即 `0.792208 / 0.817532`。 |

变化样本：

| record_key | question | v172 | v173 | judge |
|---|---|---|---|---|
| `09948051ad1179cead77946e` | `Would Melanie go on another roadtrip soon?` | `The provided information is not enough.` | `Unlikely` | v172 `0/1`，v173 `1/1` |
| `563cf440f22a0686ad946f02` | `Would Calvin enjoy performing at the Hollywood Bowl?` | `The provided information is not enough.` | `Likely yes, as Calvin explicitly states that performing live fuels his soul, energizes him, and that he loves the connection with the crowd.` | v172 `0/1`，v173 `1/1` |

## 触发面

- LME：new modal trigger 静态命中 `0/500`，answer diff `0/500`。
- LoCoMo：new modal trigger 命中 `3/1540`，其中 `2` 条 applied、`1` 条 verifier keep refusal。
- blocked cases：recommendation/advice/good-idea、external named option、which/what/list/count、敏感属性归因、support 只有 origin/identity 等弱锚点时不触发。

## 成本和复现

- LME prediction：`outputs/diagnostic/stage1_source_grounded_modal_inference_repair_v173_lme_s_full/predictions.jsonl`
- LME traces：`outputs/diagnostic/stage1_source_grounded_modal_inference_repair_v173_lme_s_full/traces.jsonl`
- LoCoMo prediction：`outputs/diagnostic/stage1_source_grounded_modal_inference_repair_v173_locomo_nonadv_full/predictions.jsonl`
- LoCoMo traces：`outputs/diagnostic/stage1_source_grounded_modal_inference_repair_v173_locomo_nonadv_full/traces.jsonl`
- changed-answer judge：`experiments/diagnostic/stage1_source_grounded_modal_inference_repair_v173_changed_vs_v172/`
- LME cache：build hits/misses `3341/0`，answer hits/misses `500/0`，repair hits/misses/writes `6/0/0`。
- LoCoMo cache：build hits/misses `12411/0`，answer hits/misses `1540/0`，repair hits/misses/writes `0/3/3`。
- logical token accounting：LME avg build/query tokens `85393.566 / 6239.336`；LoCoMo avg build/query tokens `62015.57402597403 / 6058.651298701298`。

## 风险结论

v173 降低 #4 over-abstention/source-grounded verifier 风险和 #5 query-time memory reasoning 风险：typed/support evidence 不直接替代原文答案，只作为触发 answer verifier 的 source-backed activation；最终答案仍回到 Memory Context。它不扩大到外部命名、推荐、列表或敏感属性推理，因此比 broad modal repair 风险更低。

仍未解决：#1 granularity/profile 泛化、#2 top-k/context noise/rerank、#3 selected-context 泛化，以及更广泛的 #5 lifecycle/update/conflict management。下一步优先做 coverage-preserving route-aware context organization 和 answer-slot-aware lifecycle/update/conflict verifier。
