# stage1_object_lifecycle_tail_exchange_v254_full_summary

## 目的

验证 v254 是否能修复 v253 暴露出的 object-slot 适用边界风险：collection/object slot 只应用在更像 enumerate/list/count 的问题上；advice/recommendation/suggestion/resource-seeking 问题不触发；`one`/`advice`/`recommendation` 等泛词不再单独作为 overlap 证据。

## 配置

- config: `configs/stage1_object_lifecycle_tail_exchange_v254_scoped_seeded_qwen36_no_think_build4k_cached.json`
- parent LTS: `configs/stage1_object_slot_tail_rescue_v250_seeded_qwen36_no_think_build4k_cached.json`
- rejected parent diagnostic: `configs/stage1_object_lifecycle_tail_exchange_v253_seeded_qwen36_no_think_build4k_cached.json`
- method commit: `6a825d7`
- experiment base commit: `9b50a9e`
- answer cache: `outputs/cache/qwen36_no_think_build4k_answer_v250_object_slot_tail_rescue_seeded.sqlite`

## Clean 口径

- Prediction 只读取原始对话、可见元数据、question text、question-derived route 和 build-stage typed memory/source links。
- object-slot 仍只做 source-backed activation；最终 evidence 回到 raw source rows。
- advice gate 和 ignored overlap terms 是通用问题语义边界，不读取 gold answer、judge output、benchmark label、sample id、row index 或 test feedback。
- changed-answer judge 只用于 prediction 后离线评测；未变化答案沿用 v250 full parent records，重复答案复用既有同 `record_key`/同答案文本的 judge records。

## Full 结果

| Benchmark | answer diff vs v250 | retrieval-order diff | final-evidence diff | object-slot applied | advice blocked | derived strict/lenient |
|---|---:|---:|---:|---:|---:|---:|
| LongMemEval-S | `7/500` | `80/500` | `29/500` | `88/500` | `1/500` | `0.826000 / 0.842000` |
| LoCoMo non-adversarial | `65/1540` | `192/1540` | `154/1540` | `192/1540` | `8/1540` | `0.796104 / 0.817532` |

Token / context:

| Benchmark | avg build tokens | avg query tokens | avg context chars | avg evidence |
|---|---:|---:|---:|---:|
| LongMemEval-S | `85393.566` | `6564.542` | `19747.172` | `34.816` |
| LoCoMo non-adversarial | `62015.57402597403` | `6094.081168831169` | `17406.23051948052` | `54.122727272727275` |

Derived full accuracy:

- LongMemEval-S: v250 full `416/500` strict and `422/500` lenient. v254 changed subset delta is `-3/-1`, so v254 is `413/500` strict and `421/500` lenient.
- LoCoMo: v250 full `1223/1540` strict and `1262/1540` lenient. v254 changed subset delta is `+3/-3`, so v254 is `1226/1540` strict and `1259/1540` lenient.

## 与 v253 的差异

- LongMemEval-S: v254 vs v253 answer diff `1/500`。`39f2adfa686f1fa663896c83` 从 v253 的 unsupported refusal 回到 v250 的 cocktail recommendation answer；trace 记录 `object_slot_activation_skipped_reason='advice_query_blocked'`。
- LoCoMo: v254 vs v253 answer diff `4/1540`。其中 `370b822ccdf97a131f0c6b87`、`f0d7489889d05008576b0852`、`f260cbe9fc3c24df08459675` 回到 v250；`27baf30e807665dacb4ec386` 变成语义等价的新表述，fresh dual judge 为 strict+lenient correct。
- v254 修复了 v253 的一部分风险，但没有把 v253 的 full accuracy 回退完全追回：LME 仍低于 v250，LoCoMo lenient 仍低于 v250。

## 诊断

- advice/recommendation gate 是有效的：它命中了 v253 的 LME cocktail badcase，并在 LoCoMo 阻断 8 个 advice-like object-slot activation。
- 风险仍未完全解决：v254 仍保留较多 object-slot tail exchange，LoCoMo final evidence diff `154/1540`，说明 query-time activation 仍偏重，且会改变较多最终 evidence。
- 性能不满足新 LTS 要求：虽然 LoCoMo strict 比 v250 高 `+3`，但 LongMemEval-S strict/lenient 分别低 `-3/-1`，LoCoMo lenient 低 `-3`。在“性能也很重要”的约束下，不能把它升为 LTS。

## 决策

v254 不升 LTS。当前 LTS 仍是 v250。

v254 保留为一个有效的风险收敛实验：它证明 object-slot activation 需要问题语义边界和弱词过滤，但下一版不能继续靠更多 query-time gate 堆叠。下一步应回到新 goal 的核心：让 build 阶段形成更系统的 memory operations / typed source graph / evidence utility view，并减少 query 阶段补丁式 activation。

## 输出

- LME predictions/traces: `outputs/diagnostic/stage1_object_lifecycle_tail_exchange_v254_lme_full/`
- LoCoMo predictions/traces: `outputs/diagnostic/stage1_object_lifecycle_tail_exchange_v254_locomo_full/`
- LME full records: `experiments/diagnostic/stage1_object_lifecycle_tail_exchange_v254_lme_full/`
- LoCoMo full records: `experiments/diagnostic/stage1_object_lifecycle_tail_exchange_v254_locomo_full/`
- changed predictions/labels: `outputs/diagnostic/stage1_object_lifecycle_tail_exchange_v254_full_changed_vs_v250/`
- changed dual judge / derived aggregate: `experiments/diagnostic/stage1_object_lifecycle_tail_exchange_v254_full_changed_vs_v250/`
