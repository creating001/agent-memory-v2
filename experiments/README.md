# 实验入口

`experiments/` 是正式结果和关键诊断的人类可读入口。各 run 目录保留 `summary.md`、`diagnosis.md`、`metrics.json`、`manifest.json` 和配置快照；本文件只维护当前 LTS、口径、优先待办、近期候选和必要历史锚点。长历史细节回到对应 scope summary、run 目录和 git。

## 当前 LTS

| 项目 | 结果 |
|---|---|
| 当前 LTS 配置 | `configs/stage1_build_memory_object_graph_v248_seeded_qwen36_no_think_build4k_cached.json` |
| Backbone | `Qwen/Qwen3.6-35B-A3B` answer/build，`chat_template_kwargs.enable_thinking=false` |
| 方法定位 | build-time source-backed memory management + trace-only memory object graph + query-time no-repair/no-finalizer LTS。`preference/profile/relationship/state` 参与 lifecycle；`fact/event/plan` 保留为 active collection memory；object graph 组织 subject/predicate slot、lifecycle/collection、多值、冲突和 source coverage。 |
| LongMemEval-S full | strict/lenient `0.832000 / 0.844000`，`416/500` strict，`422/500` lenient；avg build/query tokens `85393.566 / 6579.782` |
| LoCoMo non-adversarial full | strict/lenient `0.794156 / 0.819481`，`1223/1540` strict，`1262/1540` lenient；avg build/query tokens `62015.57402597403 / 6094.017532467533` |
| LTS 理由 | 继承 v235 accuracy/token，v248 vs v235 full answer/query-token/retrieval-order diff `0/500`、`0/1540`；新增 source-backed build memory object graph，降低 build memory 只是扁平 typed list 的系统风险。 |
| 主要局限 | object graph 目前仍是 trace-only，尚未系统影响 retrieval/compiler/answer verification；retrieval/context 仍依赖固定 top-k、route override、selected-context 和多段 ledger。 |

`paired-delta derived` 的含义：新版本只改少量答案，未变化答案沿用父 LTS full dual judge records，变化答案单独跑 paired dual judge 后替换计数。若新版本与父 LTS answer-identical，可继承父 LTS judge records，但必须记录 full answer diff、cache hit/miss 和输出路径。论文级最终汇报再对最终 LTS 配置重跑 fresh full judge。

## 口径

- 主线目标是通用、clean、可消融、可持续迭代、且有方法创新性的 Agent Memory system/library，不是围绕 LongMemEval/LoCoMo 手写补丁。
- 方法性能主要看 DeepSeek dual `deepseek-v4-flash` judge accuracy：strict 为两遍都判对，lenient 为任一遍判对；Exact/F1/BLEU 只作参考。
- 新 LTS 优先看 clean/general 风险是否相对当前 LTS 或直接父对照减少；性能提升是强加分项，但不是唯一前提。如果一个版本显著减少 design-for-benchmark、泄漏/过拟合、query-time 补丁复杂度或系统性方法风险，即使某个 benchmark 小幅回退，也可以作为 LTS 候选；必须明确记录性能 tradeoff、风险收益和未解决项。纯降分且没有明确 general/system 风险收益的版本不升 LTS。
- 普通诊断不需要反复重跑 full；若只影响少量预测，优先做 changed-answer paired judge。不要为了 manifest clean 或形式完整重复重跑未变化样本。
- 每个算法版本先做本地 git commit；正式实验记录引用 commit、配置、token 成本、outputs 路径和 judge 路径。GitHub 只在用户明确要求时 push。

## 面向新 Goal 的优先待办

| 优先级 | 方向 | 当前问题 | 下一步 |
|---:|---|---|---|
| 1 | Memory operations / lifecycle | v235 继承 v233 的 build-time `stateful_only` lifecycle policy，但 memory operation 还主要停留在 trace/active filtering，尚未系统影响 retrieval/compiler/answer verification | 扩展通用 memory object 与 lifecycle policy，让 create/update/merge/supersede/retrieve/expand/verify/audit 更稳定地参与 context organization，同时保持 source/provenance 可追溯 |
| 2 | Query-time 简化 | v235 已删除默认 answer repair 和 no-op finalizer，但 route、selected context、state guide、ledger 仍多层叠加，像补丁式 pipeline | 继续收敛为 candidate activation、context compiler、source-grounded answer、通用 consistency verifier |
| 3 | Retrieval/context systemization | 固定 top-k、route override、selected-context 长短 turn 规则仍较多 | 改成更通用的 candidate pooling + rerank + anchor retention + source expansion + evidence utility selection，并报告 context precision / source recall / unsupported answer |
| 4 | Answer/verifier 统一 | 现有 repair/finalizer 是多条窄触发链；部分有效，但方法形态分散 | 收敛为 source-grounded answer + consistency verifier，只检查数值、时间、说话人、实体、状态冲突、unsupported answer，不写 benchmark-specific rewrite |
| 5 | src cleanup | `pipeline.py`、compiler、repair/finalizer 兼容分支较多，后续改法成本上升 | 每个阶段做小范围清理，删除已确认无用的兼容代码；保留仍有消融价值和复现价值的模块 |

## 当前候选和近期结论

| 配置/文档 | 类型 | 关键结果 | 决策 |
|---|---|---|---|
| `configs/stage1_build_memory_object_graph_v248_seeded_qwen36_no_think_build4k_cached.json` / `diagnostic/stage1_build_memory_object_graph_v248_full_summary.md` | current LTS / build memory object graph | full answer/query-token/retrieval-order diff LME `0/500`、LoCoMo `0/1540`; object_graph coverage LME `500/500`、LoCoMo `1540/1540`; inherits v235 accuracy/token | 当前 LTS；低风险 build-stage systemization，不改变 prediction path |
| `configs/stage1_object_slot_tail_rescue_v250_seeded_qwen36_no_think_build4k_cached.json` / `diagnostic/stage1_object_slot_v249_v250_probe_summary.md` | safe candidate / object-slot tail rescue | probe50 object-slot audited LME `4/50`、LoCoMo `6/50`; answer/prompt/retrieval/query-token diff vs v248 全为 `0`; fusion mode `tail_rescue` | 修复 v249 的 RRF 抢占风险；暂不升 LTS，先做 full/覆盖验证 |
| `configs/stage1_object_slot_collection_activation_v249_seeded_qwen36_no_think_build4k_cached.json` / `diagnostic/stage1_object_slot_v249_v250_probe_summary.md` | rejected diagnostic / object-slot RRF lesson | LME probe answer diff `0/50`; LoCoMo answer diff `5/50`; changed judge strict 持平 `2/5 -> 2/5`，lenient `4/5 -> 2/5` | 不升 LTS；collection slot 不能作为强 RRF 信号抢占原 evidence |
| `diagnostic/stage1_duplicate_memory_source_utility_v247_probe_summary.md` | rejected probe / duplicate-only utility lesson | probe50: LME changed judge `1/2 -> 2/2`，但 LoCoMo strict/lenient `16/18 -> 14/18`、`17/18 -> 15/18`; query tokens LME `5677.40 -> 5689.26`、LoCoMo `6543.56 -> 6560.04` | 不升 LTS、不跑 full；duplicate-only source boost deletion 仍会扰动 LoCoMo profile/list 细节。顶层 config/code 已清理，后续 utility 不直接删 retrieval hits |
| `diagnostic/stage1_memory_source_utility_v246_lme_full_summary.md` | rejected full / memory-source utility lesson | LME full query tokens `6579.782 -> 6333.872`、memory-source hits `9.784 -> 4.464`，但 answer diff `63/500`; changed judge strict/lenient `38/63 -> 27/63`、`39/63 -> 30/63`; derived full `0.810 / 0.826` | 不升 LTS；单一 matched-term utility gate 过度裁剪 list/count/advice/numeric 所需 source rows。顶层 config/code 已清理 |
| v244-v245 build-memory expansion probes | rejected build-side lessons | 更多/lossless typed records 增加 records、drift 或 cold-build 成本，未带来稳定 accuracy gain | build 要系统化，但不能只靠“更多 typed memory”；需要 source-backed utility、activation 和 management |
| `configs/stage1_append_fact_source_alignment_v242_seeded_qwen36_no_think_build4k_cached.json` | rejected full / source-alignment lesson | Full: LME answer diff `38/500`，changed judge strict/lenient `24/38 -> 14/38`、`24/38 -> 19/38`；derived full LME `0.812000/0.834000`，LoCoMo answer-identical | 不升 LTS；mechanical source append 虽减少形式 provenance 风险，但显著伤害性能，后续改为 typed source graph / activation audit + evidence-utility gate |
| v236-v238 prompt-side Memory Operations Guide | rejected line / code removed from current path | v236 list_count guide LoCoMo lenient 回退；v237 temporal guide strict 回退；v238 probe passed 但 full 负向：LME changed judge `14/19 -> 6/19` strict、`15/19 -> 7/19` lenient，LoCoMo `19/26 -> 18/26` | 不升 LTS；已从当前 `src`/`configs` 移除。教训是 source-backed operation view clean 但不能直接作为 answer prompt block；下一步转向 build-side memory quality、retrieval activation 或 verifier-side audit |
| v233-v235 no-repair/no-finalizer/stateful build policy | previous LTS anchors | LME `0.832000/0.844000`，LoCoMo `0.794156/0.819481`；逐步删除 repair/finalizer no-op surface | 被 v248 替代；保留为当前 LTS accuracy/token 父锚点 |
| v216-v231 context/retrieval/state/update anchors | historical LTS anchors | context manifest、ledger、context budget、guarded rerank、state/update organization 等 full 覆盖记录 | 详细历史见对应 run summary 和 git；README 不再展开逐版堆叠 |
| `formal/stage1_superseded_source_chain_v127_lme_s_full_fresh/` 和 `formal/stage1_superseded_source_chain_v127_locomo_nonadv_full_fresh/` | fresh full parent records | v127 fresh full dual judge parent records | 保留为早期 source-backed update organization 基线 |

## 负向教训索引

这些记录不再放进主叙事，但仍保留为避免重复踩坑的索引：

| 文档/目录 | 教训 |
|---|---|
| `diagnostic/stage1_profile_aware_gated_fact_list_rerank_v228_scope_summary.md` | profile-aware gated fact/list rerank clean，但 LoCoMo changed judge `-1/-5` |
| `diagnostic/stage1_gated_fact_list_tail_rerank_filter_v227_scope_summary.md` | fact/list top-k gate 被 route override 交互影响，LME probe50 profile diff `1/50` |
| `diagnostic/stage1_fact_list_tail_rerank_filter_v226_scope_summary.md` | fact/list tail rerank 扩大 candidate pool 后漂移过宽 |
| `diagnostic/stage1_route_tail_cap56_v223_scope_summary.md` | route-scoped final evidence cap56 降 token 但 changed judge `-13/-12` |
| `diagnostic/stage1_temporal_materialized_context_source_gate_v219_scope_summary.md` 和 `diagnostic/stage1_materialized_context_source_gate_v218_scope_summary.md` | selected-context hard gate 降 token / risk，但 answer regression 明显 |
| `diagnostic/stage1_temporal_source_grounded_selected_context_v195_changed_vs_v194/summary.md` | temporal selected-context hard gate 降噪但 LoCoMo changed judge `76/105 -> 67/105` strict |
| `diagnostic/stage1_candidate_evidence_map_v192_probe_summary.md` | 宽 Candidate Evidence Map 增 token 且丢关键 temporal row |
| `diagnostic/stage1_event_timeline_context_v179_scope_summary.md` | Source Event Timeline prompt block 过强 |
| `diagnostic/stage1_row_length_selected_context_gate_v177_scope_summary.md` | row-length selected-context gate 过宽 |

## 输出路径

```text
outputs/formal/<run_id>/predictions.jsonl
outputs/formal/<run_id>/traces.jsonl
outputs/diagnostic/<run_id>/predictions.jsonl
outputs/diagnostic/<run_id>/traces.jsonl
```

`outputs/cache/` 只保留复现 LTS 和关键 baseline 所需的 embedding/build/answer cache。cache 命中只减少本地重复 API 调用；`avg_build_tokens` / `avg_query_tokens` 仍按逻辑冷启动 visible LLM token 记录。

## 评估规则

准备升 LTS、正式汇报、full/split best 或需要下性能结论的 run，必须在 `experiments/` 下留下 summary、metrics、diagnosis、配置快照、git commit/dirty 状态、token 成本、outputs 路径和 judge 路径。普通诊断/dry-run 只需记录目的、配置或 commit、关键 trace/metrics 结论和 outputs 路径。
