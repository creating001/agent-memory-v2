# stage1_graph_evidence_utility_v262_full_summary

## 目的

验证 v262 是否能在 v261 memory system graph 之上加入一个 general、clean、source-backed evidence utility selector，同时不牺牲当前 LTS 的 full accuracy、token 成本和 prediction behavior。

v262 借鉴 `docs/method.md` 中 raw-evidence-first、source expansion、graph/hierarchy memory 和 Memory OS governance 思路：build-time graph 不是直接回答问题，而是作为可审计的 evidence utility index。该 index 只读取 typed memory object slots、lifecycle/source-support signals、当前 candidate pool 和 raw source ids；输出仍然是 raw source rows。

## 配置

- config: `configs/stage1_graph_evidence_utility_v262_seeded_qwen36_no_think_build4k_cached.json`
- parent LTS: `configs/stage1_memory_system_graph_v261_seeded_qwen36_no_think_build4k_cached.json`
- method commit: `27194e0`
- answer cache: `outputs/cache/qwen36_no_think_build4k_answer_v262_graph_evidence_utility_seeded.sqlite`

## Clean 口径

- `retrieval.graph_utility` 不读取 gold answer、judge output、benchmark label、sample id、row index、test feedback 或样本级规则。
- graph utility 只使用 build-stage typed memory records、question text、route result、当前候选 source ids 和 raw source ids。
- v262 LTS 候选配置使用 `fusion_mode=tail_rescue`、`require_new_source=true`；不替换 primary retrieval evidence，不把 synthetic memory text 放入 final evidence。
- Answer cache 由 v261 prediction traces 和 predictions 预热；不读取 labels 或 judge outputs。

## Full 结果

| Benchmark | answer diff vs v261 | retrieval hits diff | final-evidence diff | token diff | inherited strict/lenient |
|---|---:|---:|---:|---:|---:|
| LongMemEval-S | `0/500` | `0/500` | `0/500` | `0/500` | `0.832000 / 0.844000` |
| LoCoMo non-adversarial | `0/1540` | `0/1540` | `0/1540` | `0/1540` | `0.794156 / 0.819481` |

Token / graph utility coverage:

| Benchmark | avg build tokens | avg query tokens | answer cache hit/miss/write | graph utility applied | avg graph utility source hits |
|---|---:|---:|---:|---:|---:|
| LongMemEval-S | `85393.566` | `6579.782` | `500/0/0` | `341/500` | `2.378` |
| LoCoMo non-adversarial | `62015.57402597403` | `6094.017532467533` | `1540/0/0` | `1373/1540` | `2.9993506493506494` |

Full diff detail:

| Benchmark | graph utility source hits | novel source hits | graph applied but no final effect |
|---|---:|---:|---:|
| LongMemEval-S | `1189` | `1189` | `341/341` |
| LoCoMo non-adversarial | `4619` | `4619` | `1373/1373` |

Because v262 is answer-identical to v261 on both full benchmarks, it inherits v261 dual flash judge accuracy without a fresh full judge rerun.

## 诊断

- v262 reduces system risk by turning the trace-only memory graph into a reusable evidence utility interface with explicit source-backed selection, scoring, trace fields, and run metrics.
- The current `tail_rescue` mode is deliberately conservative. In full runs the primary candidate pool was already full, so graph utility generated many novel candidate source hits but did not change final retrieval or evidence rows.
- This means v262 is not an accuracy-improving version. It is a safe LTS step that makes the next behavior-affecting graph retrieval change easier to audit.
- The next step should test a constrained graph overflow or protected tail-exchange policy, but only with strong source-support gates and changed-answer judge because v258/v259 showed replacement can hurt accuracy.

## 决策

v262 升为当前 LTS。

理由：相对 v261，v262 full accuracy、token 成本和 prediction behavior 均不回退，同时把 memory system graph 从 trace-only governance 推进为 source-backed evidence utility selector/audit。它降低了“typed memory 只做浅 retrieval hint”的系统风险，但暂不声称带来性能提升。

## 输出

- LME predictions/traces: `outputs/diagnostic/stage1_graph_evidence_utility_v262_lme_full/`
- LoCoMo predictions/traces: `outputs/diagnostic/stage1_graph_evidence_utility_v262_locomo_full/`
- LME full records: `experiments/diagnostic/stage1_graph_evidence_utility_v262_lme_full/`
- LoCoMo full records: `experiments/diagnostic/stage1_graph_evidence_utility_v262_locomo_full/`
- LME probe records: `experiments/diagnostic/stage1_graph_evidence_utility_v262_lme_probe50/`
- LoCoMo probe records: `experiments/diagnostic/stage1_graph_evidence_utility_v262_locomo_probe50/`

## 下一步

- v263 should make graph evidence utility behavior-affecting without copying v259's risky replacement: consider overflow-before-context-budget or a source-support-gated tail exchange that protects lexical/dense/memory anchors.
- Keep performance primary: if v263 changes answers, run paired changed-answer dual judge before any LTS decision.
- Continue query-time cleanup after the graph selector has a controlled path into candidate/evidence selection.
