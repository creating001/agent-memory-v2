# stage1_build_operation_ledger_v257_probe_summary

## 目的

验证 v257 trace-only build memory operation ledger 是否能在不改变 v256 LTS 预测行为的前提下，把 build memory management 表达成更系统的 memory operations 层。

## 配置

- config: `configs/stage1_build_operation_ledger_v257_seeded_qwen36_no_think_build4k_cached.json`
- parent LTS: `configs/stage1_answer_support_audit_v256_seeded_qwen36_no_think_build4k_cached.json`
- method commit: `62f870f`
- build/answer cache: 继承 v256；v257 不改变 extraction prompt、retrieval、compiler、answer cache namespace、repair/finalizer/verifier 行为。

## Probe 结果

| Benchmark | n | answer diff vs v256 | retrieval-order diff | final-evidence diff | token diff | ledger applied |
|---|---:|---:|---:|---:|---:|---:|
| LongMemEval-S probe50 | 50 | `0/50` | `0/50` | `0/50` | `0/50` | `50/50` |
| LoCoMo non-adversarial probe50 | 50 | `0/50` | `0/50` | `0/50` | `0/50` | `50/50` |

Operation ledger counts:

| Benchmark | create | supersede | retain collection multi-value slot | audit slot | source unbacked |
|---|---:|---:|---:|---:|---:|
| LongMemEval-S probe50 | `5854` | `588` | `378` | `4537` | `0` |
| LoCoMo non-adversarial probe50 | `5600` | `700` | `400` | `4250` | `0` |

## 诊断

- v257 是 build-side systemization，不改变 query-time evidence selection 或 answer path。
- Ledger 显式记录 `create / merge / supersede / retain_active / retain_superseded / retain_collection_multi_value_slot / verify_source_backed / audit_slot / audit_conflict_slot`。
- Probe confirms no behavior drift against v256. Full run is still needed before LTS decision.

## 输出

- LME probe: `outputs/diagnostic/stage1_build_operation_ledger_v257_lme_probe50/`
- LoCoMo probe: `outputs/diagnostic/stage1_build_operation_ledger_v257_locomo_probe50/`
- LME records: `experiments/diagnostic/stage1_build_operation_ledger_v257_lme_probe50/`
- LoCoMo records: `experiments/diagnostic/stage1_build_operation_ledger_v257_locomo_probe50/`
