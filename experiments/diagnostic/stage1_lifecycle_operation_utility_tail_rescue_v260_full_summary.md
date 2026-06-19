# stage1_lifecycle_operation_utility_tail_rescue_v260_full_summary

## 目的

验证 lifecycle operation utility 是否可以在不牺牲 v257 full accuracy 和 token 成本的前提下，把 build-stage operation ledger 从 trace-only 推进一步：作为 source-backed operation index，保守参与 retrieval trace / context organization。

## 配置

- config: `configs/stage1_lifecycle_operation_utility_tail_rescue_v260_seeded_qwen36_no_think_build4k_cached.json`
- parent LTS: `configs/stage1_build_operation_ledger_v257_seeded_qwen36_no_think_build4k_cached.json`
- implementation commit: `17082a2`
- v259 config commit: `7c8bb1b`
- v260 config commit: `d7fb5b0`
- answer cache: `outputs/cache/qwen36_no_think_build4k_answer_v260_lifecycle_operation_utility_tail_rescue_seeded.sqlite`

## Clean 口径

- Operation utility 只读取 build-stage typed memory records、operation ledger 和 raw source ids；不读取 gold answer、judge output、benchmark label、sample id 或 test feedback。
- Typed memory 只做 source-backed operation index；返回的 source hits 始终指向 raw Memory rows。
- v260 使用 append-only `tail_rescue`，不替换已有高置信 retrieval hits；answer prompt、repair、finalizer 和 verifier 逻辑不变。
- Answer cache 由 v257 prediction traces 和 predictions 预热；不读取 labels 或 judge outputs。

## v259 负向诊断

v259 使用 lifecycle-only operation utility，但融合方式为 `tail_exchange`。Full changed-answer paired judge 显示它不能升 LTS：

| Benchmark | answer diff vs v257 | changed strict gain/loss | changed lenient gain/loss | 结论 |
|---|---:|---:|---:|---|
| LongMemEval-S | `4/500` | `0/0` | `0/1` | lenient 回退 |
| LoCoMo non-adversarial | `10/1540` | `0/2` | `0/2` | strict/lenient 回退 |

通用教训：lifecycle/source-backed operation utility 是 clean 的，但 replacement/tail-exchange 即使只替换少量 evidence，也可能挤掉原本足够的上下文。后续应优先使用 append-only 或更强的 utility gate。

## v260 Full 结果

| Benchmark | answer diff vs v257 | retrieval hits diff | final-evidence diff | token diff | strict/lenient |
|---|---:|---:|---:|---:|---:|
| LongMemEval-S | `0/500` | `0/500` | `0/500` | `0/500` | `0.832000 / 0.844000` |
| LoCoMo non-adversarial | `0/1540` | `0/1540` | `0/1540` | `0/1540` | `0.794156 / 0.819481` |

Token / operation utility:

| Benchmark | avg build tokens | avg query tokens | answer cache hit/miss/write | operation utility applied | avg operation source hits |
|---|---:|---:|---:|---:|---:|
| LongMemEval-S | `85393.566` | `6579.782` | `500/0/0` | `14/500` | `0.09` |
| LoCoMo non-adversarial | `62015.57402597403` | `6094.017532467533` | `1540/0/0` | `22/1540` | `0.03961038961038961` |

Because v260 is answer-identical to v257 on both full benchmarks, it inherits v257 dual flash judge accuracy without a fresh full judge rerun.

## 诊断

- v260 keeps the system improvement from v258/v259: build memory operations can now produce traceable source-backed utility signals.
- v260 removes the risky part of v259: operation utility no longer swaps out existing evidence.
- Full answer/retrieval/evidence/token diffs are all zero, so the performance profile is unchanged from v257.
- This is still conservative: utility activation is visible in trace, but it rarely changes evidence. The next useful direction is a general evidence utility selector with stronger source support, not wider tail-exchange.

## 决策

v260 升为当前 LTS。

理由：相对 v257，v260 不降低 full judge accuracy、不增加 token 成本、不改变最终 evidence，同时把 build operation ledger 以更系统但保守的 append-only retrieval utility 形式接入。相对 v259，v260 修复了 replacement 导致的 accuracy 回退风险。

## 输出

- LME predictions/traces: `outputs/diagnostic/stage1_lifecycle_operation_utility_tail_rescue_v260_lme_full/`
- LoCoMo predictions/traces: `outputs/diagnostic/stage1_lifecycle_operation_utility_tail_rescue_v260_locomo_full/`
- LME full records: `experiments/diagnostic/stage1_lifecycle_operation_utility_tail_rescue_v260_lme_full/`
- LoCoMo full records: `experiments/diagnostic/stage1_lifecycle_operation_utility_tail_rescue_v260_locomo_full/`
- v259 LME changed judge: `experiments/diagnostic/stage1_lifecycle_operation_utility_v259_lme_full_changed_vs_v257/`
- v259 LoCoMo changed judge: `experiments/diagnostic/stage1_lifecycle_operation_utility_v259_locomo_full_changed_vs_v257/`
