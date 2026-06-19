# stage1_build_slot_inventory_v255_full_summary

## 目的

验证 v255 是否能在不牺牲 v250 full accuracy 的前提下，把 object-slot tail rescue 从 query-time 临时分组推进为更系统的 build-slot inventory 视图。v255 不改 answer prompt、不增加 LLM 调用、不改变 object-slot tail-rescue 策略，只新增 `use_build_slot_index=true` 和对应 trace。

## 配置

- config: `configs/stage1_build_slot_inventory_v255_seeded_qwen36_no_think_build4k_cached.json`
- parent LTS: `configs/stage1_object_slot_tail_rescue_v250_seeded_qwen36_no_think_build4k_cached.json`
- method commit: `dfe2255`
- probe commit: `ab6b58a`
- answer cache: `outputs/cache/qwen36_no_think_build4k_answer_v250_object_slot_tail_rescue_seeded.sqlite`

## Clean 口径

- Build-slot inventory 只由 source-backed typed memory records 构造，不读取 question label、gold answer、judge output、benchmark tag、sample id 或 test feedback。
- Typed memory 仍只作为 source-backed activation/index；最终 evidence 仍回到 raw source rows。
- changed-answer judge 只在 prediction 后用于离线评测；v255 唯一 changed answer 与 v254 同 `record_key` 且同答案文本，复用 v254 fresh dual judge record。

## Full 结果

| Benchmark | answer diff vs v250 | retrieval-order diff | final-evidence diff | object-source diff | object-slot applied | strict/lenient |
|---|---:|---:|---:|---:|---:|---:|
| LongMemEval-S | `0/500` | `0/500` | `0/500` | `0/500` | `89/500` | `0.832000 / 0.844000` |
| LoCoMo non-adversarial | `1/1540` | `0/1540` | `1/1540` | `0/1540` | `198/1540` | `0.794156 / 0.819481` |

Token / context:

| Benchmark | avg build tokens | avg query tokens | avg context chars | avg evidence |
|---|---:|---:|---:|---:|
| LongMemEval-S | `85393.566` | `6579.782` | `19771.722` | `34.742` |
| LoCoMo non-adversarial | `62015.57402597403` | `6094.017532467533` | `17401.615584415584` | `54.137662337662334` |

Derived full accuracy:

- LongMemEval-S: answer-identical to v250, inherits v250 `416/500` strict and `422/500` lenient.
- LoCoMo: only `27baf30e807665dacb4ec386` differs in answer text. v250 judge was strict+lenient correct; v255 answer is identical to v254 on the same key, and v254 fresh dual judge was also strict+lenient correct. Delta is `0/0`, so v255 inherits v250 `1223/1540` strict and `1262/1540` lenient.

## 诊断

- v255 preserves v250 retrieval behavior on full: source-hit order is unchanged on both benchmarks, and object-slot source hits are unchanged.
- The single LoCoMo final-evidence/answer text difference is a previously judged semantic-equivalent “Who is Anthony?” answer; it does not change accuracy.
- The new trace exposes build-slot inventory stats for every sample via `object_slot_activation_slot_index`, including `slot_count`, `collection_slot_count`, `lifecycle_slot_count`, `source_backed_slot_count`, and `source_backed_collection_slot_count`.
- This reduces the #1/#5 system risk: object-slot activation is now auditable as a source-backed slot inventory rather than opaque query-time grouping, while still avoiding v249/v253/v254 style evidence抢占或过宽 activation。

## 决策

v255 升为当前 LTS。

理由：相对 v250，v255 full judge accuracy 不回退，token 成本基本持平，且 build/query 边界更清晰、trace 更可解释。它不是新的 accuracy peak，但满足“风险更少且性能不降”的 LTS 条件。

## 输出

- LME predictions/traces: `outputs/diagnostic/stage1_build_slot_inventory_v255_lme_full/`
- LoCoMo predictions/traces: `outputs/diagnostic/stage1_build_slot_inventory_v255_locomo_full/`
- LME full records: `experiments/diagnostic/stage1_build_slot_inventory_v255_lme_full/`
- LoCoMo full records: `experiments/diagnostic/stage1_build_slot_inventory_v255_locomo_full/`
- changed predictions/labels: `outputs/diagnostic/stage1_build_slot_inventory_v255_full_changed_vs_v250/`
- changed derived judge / full accuracy: `experiments/diagnostic/stage1_build_slot_inventory_v255_full_changed_vs_v250/`
