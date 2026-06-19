# stage1_memory_system_graph_v261_full_summary

## 目的

验证 v261 是否能在不改变 v260 prediction behavior 的前提下，把 build memory 从 flat typed records + operation ledger 推进为更通用的 memory system graph。

设计借鉴 `docs/method.md` 中的 raw-evidence-first、Memory OS governance、Graphiti/HippoRAG/xMemory 式 graph/hierarchy 组织思想，但只采用可回链的 source-backed audit 结构，不引入重型外部系统，也不让派生 graph 直接替代原始 evidence。

## 配置

- config: `configs/stage1_memory_system_graph_v261_seeded_qwen36_no_think_build4k_cached.json`
- parent LTS: `configs/stage1_lifecycle_operation_utility_tail_rescue_v260_seeded_qwen36_no_think_build4k_cached.json`
- method commit: `580d039`
- answer cache: `outputs/cache/qwen36_no_think_build4k_answer_v261_memory_system_graph_seeded.sqlite`

## Clean 口径

- `memory_system_graph` 只读取 build-stage typed memory records、operation trace 和 raw source ids；不读取 gold answer、judge output、benchmark label、sample id 或 test feedback。
- Graph 只进入 build trace 和 run metrics；不进入 retrieval、compiler、answer、repair、finalizer、verifier 或 cache key。
- Typed memory 仍只做 source-backed operation index / activation；最终 evidence 仍回到 raw Memory rows。
- Answer cache 由 v260 prediction traces 和 predictions 预热；不读取 labels 或 judge outputs。

## Full 结果

| Benchmark | answer diff vs v260 | retrieval hits diff | final-evidence diff | token diff | strict/lenient |
|---|---:|---:|---:|---:|---:|
| LongMemEval-S | `0/500` | `0/500` | `0/500` | `0/500` | `0.832000 / 0.844000` |
| LoCoMo non-adversarial | `0/1540` | `0/1540` | `0/1540` | `0/1540` | `0.794156 / 0.819481` |

Token / graph coverage:

| Benchmark | avg build tokens | avg query tokens | answer cache hit/miss/write | graph applied | avg objects | avg source spans | avg slots |
|---|---:|---:|---:|---:|---:|---:|---:|
| LongMemEval-S | `85393.566` | `6579.782` | `500/0/0` | `500/500` | `115.818` | `116.84` | `89.26` |
| LoCoMo non-adversarial | `62015.57402597403` | `6094.017532467533` | `1540/0/0` | `1540/1540` | `150.91493506493507` | `178.95194805194805` | `127.69545454545455` |

Graph operation edges:

| Benchmark | source_support | create | slot_member | verify_source_backed | audit_slot | supersede | merge |
|---|---:|---:|---:|---:|---:|---:|---:|
| LongMemEval-S | `72476` | `57909` | `57909` | `57909` | `44630` | `5499` | `1` |
| LoCoMo non-adversarial | `319724` | `232409` | `232409` | `232409` | `196651` | `13622` | `0` |

Because v261 is answer-identical to v260 on both full benchmarks, it inherits v260 dual flash judge accuracy without a fresh full judge rerun.

## 诊断

- v261 adds a source-backed graph governance layer: memory objects, namespaces, lifecycle states, object slots, source-support edges, merge edges, and supersede edges are now visible in trace and metrics.
- Full answer/retrieval/final-evidence/token diffs are all zero, so this version does not buy system structure by sacrificing performance or query tokens.
- The graph exposes how much memory is profile/state, episodic, semantic, prospective, active, and superseded, which supports the next step: general evidence utility selection.
- This is still conservative. It does not yet improve accuracy; it reduces build-stage system risk and makes future graph-driven retrieval safer to audit.

## 决策

v261 升为当前 LTS。

理由：相对 v260，v261 full accuracy、token 成本和 prediction behavior 不回退，同时把 build memory 组织从 ledger/counts 推进为可审计 source-backed memory system graph。它更符合当前 goal 中“通用、clean、像系统/library，而不是 benchmark pipeline”的方向。

## 输出

- LME predictions/traces: `outputs/diagnostic/stage1_memory_system_graph_v261_lme_full/`
- LoCoMo predictions/traces: `outputs/diagnostic/stage1_memory_system_graph_v261_locomo_full/`
- LME full records: `experiments/diagnostic/stage1_memory_system_graph_v261_lme_full/`
- LoCoMo full records: `experiments/diagnostic/stage1_memory_system_graph_v261_locomo_full/`
- LME probe records: `experiments/diagnostic/stage1_memory_system_graph_v261_lme_probe50/`
- LoCoMo probe records: `experiments/diagnostic/stage1_memory_system_graph_v261_locomo_probe50/`

## 下一步

- v262 should use the graph as an audit-backed input to a general evidence utility selector: candidate pooling, anchor retention, source expansion, and append-only utility rescue first.
- Do not introduce replacement/tail-exchange until a stronger source-support gate and paired changed-answer judge show it is safe.
- Keep query-time cleanup active: disabled repair/finalizer compatibility config should be moved toward diagnostic-only surfaces or removed after confirming no reproducibility need.
