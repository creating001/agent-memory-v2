# stage1_answer_support_audit_v256_probe_summary

## 目的

验证 v256 trace-only source-grounded answer verifier 是否在不改变 v255 LTS 预测行为的前提下，为 answer/verifier 风险提供系统化审计信号。

## 配置

- config: `configs/stage1_answer_support_audit_v256_seeded_qwen36_no_think_build4k_cached.json`
- parent LTS: `configs/stage1_build_slot_inventory_v255_seeded_qwen36_no_think_build4k_cached.json`
- method commits: `b81e8b1`, `6b3c954`
- answer/build cache: 继承 v255/v250 缓存；v256 不改变 prompt、retrieval、answer cache namespace、repair/finalizer。

## Probe 结果

| Benchmark | n | answer diff vs v255 | retrieval-order diff | final-evidence diff | token diff | verifier risks |
|---|---:|---:|---:|---:|---:|---:|
| LongMemEval-S probe50 | 50 | `0/50` | `0/50` | `0/50` | `0/50` | `0` |
| LoCoMo non-adversarial probe50 | 50 | `0/50` | `0/50` | `0/50` | `0/50` | `0` |

Token / verifier:

| Benchmark | avg build tokens | avg query tokens | answer cache | verifier applied | avg support items | avg evidence_report items |
|---|---:|---:|---:|---:|---:|---:|
| LongMemEval-S probe50 | `86398.54` | `5677.4` | `50 hit / 0 miss` | `50/50` | `1.68` | `2.16` |
| LoCoMo non-adversarial probe50 | `45868.0` | `6543.56` | `50 hit / 0 miss` | `50/50` | `2.94` | `4.04` |

## 诊断

- v256 verifier is trace-only: it reads final answer JSON, `evidence_report`, `sufficient`, and prompt-visible Memory row count; it never calls a model or changes answer text.
- Probe confirms no behavior drift against v255: answers, final retrieval order, final evidence rows, and token accounting are identical on both probe sets.
- Initial probe exposed two audit-format false positives: missing JSON `answer` while final fallback answer was insufficient, and bare numeric memory refs such as `"16"`. Commit `6b3c954` fixed both by auditing the final returned answer and validating numeric memory references against the visible row count.
- Current probe has no verifier risk flags. Full run is still needed before any LTS decision.

## 输出

- LME probe: `outputs/diagnostic/stage1_answer_support_audit_v256_lme_probe50/`
- LoCoMo probe: `outputs/diagnostic/stage1_answer_support_audit_v256_locomo_probe50/`
- LME records: `experiments/diagnostic/stage1_answer_support_audit_v256_lme_probe50/`
- LoCoMo records: `experiments/diagnostic/stage1_answer_support_audit_v256_locomo_probe50/`
