# stage1_answer_support_audit_v256_full_summary

## 目的

验证 v256 是否能在不牺牲 v255 full accuracy 和 token 成本的前提下，把 answer/verifier 从窄 repair/finalizer 链条进一步收敛为通用、trace-only、source-grounded support audit。

## 配置

- config: `configs/stage1_answer_support_audit_v256_seeded_qwen36_no_think_build4k_cached.json`
- parent LTS: `configs/stage1_build_slot_inventory_v255_seeded_qwen36_no_think_build4k_cached.json`
- method commits: `b81e8b1`, `6b3c954`
- probe commit: `cb0c271`
- answer cache: `outputs/cache/qwen36_no_think_build4k_answer_v250_object_slot_tail_rescue_seeded.sqlite`

## Clean 口径

- v256 verifier 只读取 prediction-time final answer JSON、`evidence_report`、`sufficient` 和 prompt-visible Memory row count。
- Verifier 不调用模型、不改 prompt、不改 retrieval、不改 answer、不参与 cache key；judge 仅用于离线结果确认。
- Prediction 不读取 gold answer、judge output、benchmark label、sample id、test feedback 或样本级规则。

## Full 结果

| Benchmark | answer diff vs v255 | retrieval-order diff | final-evidence diff | token diff | strict/lenient |
|---|---:|---:|---:|---:|---:|
| LongMemEval-S | `0/500` | `0/500` | `0/500` | `0/500` | `0.832000 / 0.844000` |
| LoCoMo non-adversarial | `0/1540` | `0/1540` | `0/1540` | `0/1540` | `0.794156 / 0.819481` |

Token / verifier:

| Benchmark | avg build tokens | avg query tokens | verifier applied | verifier risk samples | avg support items |
|---|---:|---:|---:|---:|---:|
| LongMemEval-S | `85393.566` | `6579.782` | `500/500` | `11/500` | `2.006` |
| LoCoMo non-adversarial | `62015.57402597403` | `6094.017532467533` | `1540/1540` | `10/1540` | `2.3279220779220777` |

Verifier risk flags:

- LongMemEval-S: `answered_without_support_item=8`, `missing_evidence_report=7`, `missing_structured_payload=1`, `sufficiency_false_but_answered=1`, `support_item_without_memory_reference=1`, `unresolved_memory_reference=1`.
- LoCoMo: `answered_without_support_item=6`, `missing_evidence_report=5`, `missing_structured_payload=3`, `sufficiency_false_but_answered=1`.

## 诊断

- v256 is answer-identical to v255 on both full benchmarks, so it inherits v255/v250 dual-judge accuracy without changed-answer judge.
- Token accounting is identical to v255; answer cache hit rate is `500/500` and `1540/1540`.
- The new audit exposes unsupported-answer and malformed support-report risks that were previously invisible in the LTS trace. This reduces answer/verifier system risk without adding query-time patch complexity.
- Remaining work: use these audit flags to design a future source-grounded verifier that can safely trigger evidence reorganization or abstention, rather than adding benchmark-specific rewrites.

## 决策

v256 升为当前 LTS。

理由：相对 v255，v256 full judge accuracy 和 token 成本不回退，预测行为完全一致，同时新增通用 source-grounded answer support audit，降低 answer/verifier 可观测性和 unsupported-answer 风险。它不是性能提升版，但满足“风险更少且性能不降”的 LTS 条件。

## 输出

- LME predictions/traces: `outputs/diagnostic/stage1_answer_support_audit_v256_lme_full/`
- LoCoMo predictions/traces: `outputs/diagnostic/stage1_answer_support_audit_v256_locomo_full/`
- LME full records: `experiments/diagnostic/stage1_answer_support_audit_v256_lme_full/`
- LoCoMo full records: `experiments/diagnostic/stage1_answer_support_audit_v256_locomo_full/`
