# stage1_object_lifecycle_tail_exchange_v253_full_summary

## 目的

验证 v253 是否可以把 v250 的 object-slot tail rescue 推进为更主动但仍受保护的 build-memory source activation：collection/object slot 命中后，只替换最终候选尾部，避免抢占 protected top evidence。

## 配置

- config: `configs/stage1_object_lifecycle_tail_exchange_v253_seeded_qwen36_no_think_build4k_cached.json`
- parent LTS: `configs/stage1_object_slot_tail_rescue_v250_seeded_qwen36_no_think_build4k_cached.json`
- method commit: `253f141`
- probe/experiment base commit: `b25301c`
- answer cache: `outputs/cache/qwen36_no_think_build4k_answer_v250_object_slot_tail_rescue_seeded.sqlite`
- cache note: prediction-time answer cache only; no labels, judge outputs, benchmark labels, sample ids, or test feedback are used by retrieval/compiler/answer.

## Clean 口径

- v253 只读取原始对话、可见元数据、question text 和 build-stage typed memory/source links。
- object-slot 只作为 source-backed activation，最终上下文仍回到 raw source rows。
- full changed judge 只用于离线评测 v253 改变答案的样本，不进入 prediction、retrieval、compiler、answer 或 cache build。

## Full 结果

| Benchmark | Scope | answer diff vs v250 | retrieval-order diff | final-evidence diff | object-slot applied | changed judge v250 | changed judge v253 | derived strict/lenient |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| LongMemEval-S | `500` | `8/500` | `0/500` | `30/500` | `89/500` | `7/8` / `7/8` | `3/8` / `5/8` | `0.824000 / 0.840000` |
| LoCoMo non-adversarial | `1540` | `67/1540` | `0/1540` | `159/1540` | `198/1540` | `34/67` / `42/67` | `37/67` / `39/67` | `0.796104 / 0.817532` |

Token / context:

| Benchmark | avg build tokens | avg query tokens | avg context chars | avg evidence |
|---|---:|---:|---:|---:|
| LongMemEval-S | `85393.566` | `6553.78` | `19744.354` | `34.816` |
| LoCoMo non-adversarial | `62015.57402597403` | `6094.337662337663` | `17407.243506493505` | `54.122727272727275` |

Derived full accuracy is computed from v250 full counts plus changed-answer dual judge deltas:

- LongMemEval-S: v250 `416/500` strict and `422/500` lenient; v253 changed-answer delta `-4` strict and `-2` lenient, so v253 is `412/500` strict and `420/500` lenient.
- LoCoMo: v250 `1223/1540` strict and `1262/1540` lenient; v253 changed-answer delta `+3` strict and `-3` lenient, so v253 is `1226/1540` strict and `1259/1540` lenient.

## 诊断

- v253 的 bounded tail exchange 确实更有行为变化：LME `8` 条答案改变，LoCoMo `67` 条答案改变。
- LoCoMo strict 有小幅收益，但 lenient 回退；LME strict/lenient 都回退，尤其 single-session-preference changed subset 从 v250 `4/5` strict 降到 v253 `0/5` strict。
- 关键风险来自 collection/object slot 的适用边界过宽：个别 recommendation/advice 型问题被路由成 list/count 后，object slot 会用很弱的 overlap term 激活无关 collection 证据。
- 一个明确 badcase 是 `39f2adfa686f1fa663896c83`：问题是个性化 cocktail suggestion，v253 因 weak term `one` 激活 object slots，替换尾部 evidence 后让答案失去支持。
- 这不是 benchmark-specific 问题，而是系统边界问题：collection expansion 应服务于 enumerate/list/count，不应介入 advice/recommendation/suggestion 这类需要 profile + evidence synthesis 的问题；object-slot overlap 也不能依赖 `one` 这类泛词。

## 决策

v253 不升 LTS。当前 LTS 仍是 v250。

拒绝原因不是“风险减少但性能未提升”，而是 v253 在 full evaluation 上引入了实质 accuracy 回退：LongMemEval-S strict `0.832000 -> 0.824000`，lenient `0.844000 -> 0.840000`；LoCoMo lenient `0.819481 -> 0.817532`。因此它只能作为 v254 的诊断前驱。

下一步 v254 应保留 v253 的系统化方向，但收紧 object-slot activation：

- block advice/recommendation/suggestion/resource-seeking queries from collection/object-slot activation；
- ignore weak overlap terms such as `one`/`ones`/generic request terms when deciding object-slot matches；
- keep the gate configurable and ablatable, with defaults preserving prior configs unless explicitly enabled；
- rerun probe/full changed judge before any LTS decision。

## 输出

- LME predictions/traces: `outputs/diagnostic/stage1_object_lifecycle_tail_exchange_v253_lme_full/`
- LoCoMo predictions/traces: `outputs/diagnostic/stage1_object_lifecycle_tail_exchange_v253_locomo_full/`
- LME full records: `experiments/diagnostic/stage1_object_lifecycle_tail_exchange_v253_lme_full/`
- LoCoMo full records: `experiments/diagnostic/stage1_object_lifecycle_tail_exchange_v253_locomo_full/`
- changed predictions/labels: `outputs/diagnostic/stage1_object_lifecycle_tail_exchange_v253_full_changed_vs_v250/`
- changed dual judge: `experiments/diagnostic/stage1_object_lifecycle_tail_exchange_v253_full_changed_vs_v250/`
