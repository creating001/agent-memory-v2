# stage1_build_operation_ledger_v257_full_summary

## 目的

验证 v257 是否能在不牺牲 v256 full accuracy 和 token 成本的前提下，把 build memory 从 typed-record/slot summary 推进为可审计的 memory operations layer。

## 配置

- config: `configs/stage1_build_operation_ledger_v257_seeded_qwen36_no_think_build4k_cached.json`
- parent LTS: `configs/stage1_answer_support_audit_v256_seeded_qwen36_no_think_build4k_cached.json`
- method commit: `62f870f`
- probe commit: `7c23438`
- answer cache: `outputs/cache/qwen36_no_think_build4k_answer_v250_object_slot_tail_rescue_seeded.sqlite`

## Clean 口径

- v257 ledger 只读取 build-stage typed memory records 和 raw source ids，不读取 question label、gold answer、judge output、benchmark tag、sample id 或 test feedback。
- Ledger 只进入 build trace 和 metrics；不改变 extraction prompt、retrieval、compiler prompt、answer、repair、finalizer、verifier 或 cache key。
- Derived memory 仍只做 source-backed activation/index；最终 evidence 仍回到 raw Memory rows。

## Full 结果

| Benchmark | answer diff vs v256 | retrieval-order diff | final-evidence diff | token diff | strict/lenient |
|---|---:|---:|---:|---:|---:|
| LongMemEval-S | `0/500` | `0/500` | `0/500` | `0/500` | `0.832000 / 0.844000` |
| LoCoMo non-adversarial | `0/1540` | `0/1540` | `0/1540` | `0/1540` | `0.794156 / 0.819481` |

Token / operation ledger:

| Benchmark | avg build tokens | avg query tokens | ledger applied | create | supersede | collection slots | source unbacked |
|---|---:|---:|---:|---:|---:|---:|---:|
| LongMemEval-S | `85393.566` | `6579.782` | `500/500` | `57909` | `5499` | `3806` | `0` |
| LoCoMo non-adversarial | `62015.57402597403` | `6094.017532467533` | `1540/1540` | `232409` | `13622` | `13470` | `0` |

## 诊断

- v257 is answer-identical to v256 on both full benchmarks, so it inherits v256/v255 dual-judge accuracy without changed-answer judge.
- Operation ledger covers all samples and records `create / merge / supersede / retain_active / retain_superseded / retain_collection_multi_value_slot / verify_source_backed / audit_slot / audit_conflict_slot`.
- The full run confirms all managed build memory records are source-backed (`source_unbacked=0`), and separates lifecycle updates from nonmanaged collection multi-value slots.
- This reduces build-memory-system risk: build memory is now represented as explicit memory operations, not only as shallow retrieval hints or opaque slot counts.

## 决策

v257 升为当前 LTS。

理由：相对 v256，v257 full judge accuracy 和 token 成本不回退，预测行为完全一致，同时新增 build-stage memory operation ledger，降低 build memory 组织、管理、source verification 和 lifecycle audit 风险。它不是 accuracy 提升版，但满足“风险更少且性能不降”的 LTS 条件。

## 输出

- LME predictions/traces: `outputs/diagnostic/stage1_build_operation_ledger_v257_lme_full/`
- LoCoMo predictions/traces: `outputs/diagnostic/stage1_build_operation_ledger_v257_locomo_full/`
- LME full records: `experiments/diagnostic/stage1_build_operation_ledger_v257_lme_full/`
- LoCoMo full records: `experiments/diagnostic/stage1_build_operation_ledger_v257_locomo_full/`
