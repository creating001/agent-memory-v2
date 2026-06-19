# stage1_build_slot_inventory_v255_probe_summary

## 目的

v255 继承 v250 的 object-slot `tail_rescue` 行为，只把 object-slot grouping 明确为 question-independent build-slot inventory，并在 retrieval trace 中记录 `object_slot_activation_slot_index`。目标是减少 query-time 临时分组/补丁感，同时不改变 v250 的 answer、retrieval order 和 final evidence。

## 配置

- config: `configs/stage1_build_slot_inventory_v255_seeded_qwen36_no_think_build4k_cached.json`
- parent LTS: `configs/stage1_object_slot_tail_rescue_v250_seeded_qwen36_no_think_build4k_cached.json`
- method commit: `dfe2255`
- runs:
  - `stage1_build_slot_inventory_v255_lme_probe50`
  - `stage1_build_slot_inventory_v255_locomo_probe50`

## Probe50 结果

| Benchmark | answer diff vs v250 | retrieval-order diff | final-evidence diff | object-source diff | object-slot applied | avg build/query tokens |
|---|---:|---:|---:|---:|---:|---:|
| LongMemEval-S probe50 | `0/50` | `0/50` | `0/50` | `0/50` | `4/50` | `86398.54 / 5677.40` |
| LoCoMo probe50 | `0/50` | `0/50` | `0/50` | `0/50` | `6/50` | `45868.00 / 6543.56` |

Both runs hit the v250 answer cache for all 50 examples. No judge rerun is needed for the probe because answers are identical to v250 on every checked row.

## 诊断

- v255 produces behavior-identical probe outputs while exposing source-backed slot inventory stats in trace.
- Sample slot-index trace records `source=build_slot_index`, `slot_count`, `collection_slot_count`, `lifecycle_slot_count`, `source_backed_slot_count`, and `source_backed_collection_slot_count`.
- This is a systemization step, not an accuracy-improving step yet. It is a viable full-run candidate because it reduces build/query boundary risk without probe performance regression.

## 下一步

Run v255 full predictions against v250. If answer/retrieval/final-evidence diff remains `0`, v255 can inherit v250 full judge accuracy and become an LTS candidate on risk reduction with no performance loss. If any answers change, run paired changed-answer dual judge before making an LTS decision.

## 输出

- LME probe outputs: `outputs/diagnostic/stage1_build_slot_inventory_v255_lme_probe50/`
- LoCoMo probe outputs: `outputs/diagnostic/stage1_build_slot_inventory_v255_locomo_probe50/`
- LME probe records: `experiments/diagnostic/stage1_build_slot_inventory_v255_lme_probe50/`
- LoCoMo probe records: `experiments/diagnostic/stage1_build_slot_inventory_v255_locomo_probe50/`
