# 实验入口

`experiments/` 是正式结果和关键诊断的人类可读入口。各 run 目录保留 `summary.md`、`diagnosis.md`、`metrics.json`、`manifest.json` 和配置快照；本文件只维护当前 LTS、统一口径、优先待办、近期候选和必要负向教训。长历史细节回到对应 run 目录、scope summary 和 git。

## 当前 LTS

| 项目 | 结果 |
|---|---|
| 当前 LTS 配置 | `configs/stage1_memory_object_index_v288_seeded_qwen36_no_think_build4k_cached.json` |
| Backbone | `Qwen/Qwen3.6-35B-A3B` answer/build，`chat_template_kwargs.enable_thinking=false` |
| 方法定位 | source-backed Agent Memory system：build memory management + memory system graph v3 + `memory_object_index_v1` + tier manifest + operation ledger + state conflict manifest + scalar/value manifest + state-only value slot guide + raw evidence compiler + source-grounded answer audit。Typed memory 不能直接替代 evidence，只能作为 source-backed activation、state organization、conflict handling、context organization 和 audit signal；最终答案仍以 raw Memory rows 为证据。 |
| LongMemEval-S full | strict/lenient `0.834000 / 0.846000`，`417/500` strict，`423/500` lenient；avg build/query tokens `85393.566 / 6455.588` |
| LoCoMo non-adversarial full | strict/lenient `0.794156 / 0.819481`，`1223/1540` strict，`1262/1540` lenient；avg build/query tokens `62015.57402597403 / 6093.962337662338` |
| LTS 理由 | v288 相对 v287：LME/LoCoMo full answer/prompt/route/compiled evidence/compiled memory/materialized retrieval/build records diff 全部 `0`；build management diff 只来自新增 `memory_object_index_v1`，剥离 index 后 diff 为 `0`。它把 tier、operation、state conflict、source policy 和 value slots 收敛成统一 build-owned memory object interface，减少 build memory system 分散和 typed memory 只做 retrieval hint 的系统风险。 |
| 主要局限 | query stack 仍有 state guide、event-time guide、selected context、context budget、audit 等兼容层；`memory_object_index_v1` 已统一 build-owned interface，但 retrieval/context/verifier 尚未全面由该 index 驱动；LME/LoCoMo query tokens 仍略高于 6K 目标但低于 8K hard diagnostic 线。 |

v288 关键证据见 `experiments/diagnostic/stage1_memory_object_index_v288_full_summary.md`。

## 重启说明

v289-v354 这条候选线已从当前工作树清理，不再作为当前候选、LTS 依据或方法结论。后续重新从 v288 LTS 开始探索，重点回到更通用的 build-stage memory organization、memory operations、candidate pooling / rerank / source expansion、source-grounded answer 和 consistency verifier，而不是继续沿着 v288 之后的 query-time 补丁线堆规则。

## 口径

- 主线目标是通用、clean、可消融、可持续迭代、且有方法创新性的 Agent Memory system/library，不是围绕 LongMemEval/LoCoMo 手写补丁。
- 方法性能主要看 DeepSeek dual `deepseek-v4-flash` judge accuracy：strict 为两遍都判对，lenient 为任一遍判对；Exact/F1/BLEU 只作参考。
- 每个进入当前候选表、LTS 判断或算法性能结论的版本，都必须报告 full dual judge accuracy（strict/lenient）、avg build tokens、avg query tokens。没有 full 口径指标的 run 只能标为 probe/dry-run/diagnostic，不能作为算法性能结论。
- 新 LTS 优先看 clean/general/system 风险是否减少；性能提升是强加分项，但不是唯一前提。若风险明显减少且性能不退，可以升 LTS；若小幅回退但显著降低 design-for-benchmark 或系统风险，需要明确记录 tradeoff 后再判断。
- 每个算法版本先做本地 git commit；正式实验记录引用 commit、配置、token 成本、outputs 路径和 judge 路径。GitHub 只在用户明确要求时 push。
- 普通诊断不进入候选表。需要下性能结论时，先补齐 full 口径指标，再写入本文件。

## 优先待办

| 优先级 | 方向 | 下一步 |
|---:|---|---|
| 1 | Build memory system | 从 v288 出发重新设计更系统的 build-stage memory organization：short-term / working / long-term / archival 层次、不同 memory object、create / update / merge / supersede / retrieve / expand / verify / audit 操作，以及 source/provenance/governance。 |
| 2 | Design-for-benchmark cleanup | 检查 route、selected context、Managed Memory State Guide、ledger diagnostics、repair、finalizer、top-k/context budget；能通用化的改成 memory policy，不能通用化的删掉或降级为 diagnostic。 |
| 3 | Retrieval/context | 探索通用 candidate pooling + rerank + anchor retention + source expansion + evidence utility selection，减少固定大 top-k 和长/短 turn 规则。 |
| 4 | Answer/verifier | 整理成 source-grounded answer + 通用 consistency verifier，只检查数值、时间、说话人、实体、状态冲突和 unsupported answer，不写 benchmark-specific rewrite。 |
| 5 | Query-time 简化和 src cleanup | 判断哪些逻辑可以前移到 build-time memory lifecycle，哪些可以删除、合并；同时分阶段清理 `src/`，只删除已确认无用且不影响复现/消融的代码。 |

## 当前候选和近期结论

| 配置/文档 | 类型 | 关键结果 | 决策 |
|---|---|---|---|
| `configs/stage1_memory_object_index_v288_seeded_qwen36_no_think_build4k_cached.json` / `diagnostic/stage1_memory_object_index_v288_full_summary.md` | current LTS | v288 vs v287：LME/LoCoMo full answer/prompt/route/evidence/retrieval/build records diff `0`；`memory_object_index_v1` applied `2040/2040`；avg query tokens LME `6455.588`、LoCoMo `6093.962337662338` | 升 LTS；统一 build-owned memory object interface，性能继承 v287 |
| `configs/stage1_state_only_value_slot_guide_v287_seeded_qwen36_no_think_build4k_cached.json` / `diagnostic/stage1_state_only_value_slot_guide_v287_full_summary.md` | previous LTS | v287 vs v284：LME answer diff `2/500`、LoCoMo `1/1540`；changed-answer dual judge 全部 strict correct；avg query tokens LME `6455.588`、LoCoMo `6093.962337662338` | 被 v288 继承；state-only value slot guide 让 build-owned memory object 参与 state organization |
| `configs/stage1_current_state_value_slot_guide_v286_seeded_qwen36_no_think_build4k_cached.json` / `diagnostic/stage1_current_state_value_slot_guide_v286_changed_vs_v284/` | rejected diagnostic | current-state intent 限制后，LME changed-answer judge v284 strict/lenient `6/8`、`7/8`，v286 只有 `3/8`、`3/8` | 不升 LTS；intent gate 不够，plan/fact/event/profile/preference slot 仍会扰动 current-state answer focus |
| `configs/stage1_memory_value_slot_guide_v285_seeded_qwen36_no_think_build4k_cached.json` | rejected diagnostic | 全类型 value slot guide 过宽：LME guide applied `186/500`、answer diff `55/500`；LoCoMo guide applied `884/1540`、answer diff `422/1540` | 不升 LTS；证明 value slot 必须有 source-backed type/intent gate |
| `configs/stage1_scalar_value_manifest_v284_seeded_qwen36_no_think_build4k_cached.json` / `diagnostic/stage1_scalar_value_manifest_v284_full_summary.md` | previous LTS | v284 vs v283 full answer/prompt/evidence/retrieval diff `0`；scalar manifest 覆盖 `2040/2040`；avg query tokens LME `6464.954`、LoCoMo `6093.794155844156` | 被 v287 继承；build-owned value objects/slots 是 v287 的基础 |
| v276-v283 memory system line | previous anchors | tier manifest、operation ledger、state-conflict manifest、order-safe value parser 均以 clean/answer-identical 或 changed-answer judge 不退方式降低风险 | 保留为系统化 memory build 管线的可追溯锚点，详细见对应 full summary 和 git |

## 负向教训索引

| 文档/目录 | 教训 |
|---|---|
| `diagnostic/stage1_state_only_value_slot_guide_v287_full_summary.md` | memory object 可以进入 query，但必须 source-backed、typed、intent-gated，并保持 raw evidence-first。 |
| `diagnostic/stage1_explicit_date_temporal_route_v271_full_summary.md` | 显式日期可以帮助识别 temporal intent，但不能无条件抢过 fact/list；应只修正 latest/recent 与 explicit-date 冲突的窄场景。 |
| `diagnostic/stage1_graph_evidence_overflow_v263_scope_summary.md` | source-backed graph utility 可以进入 candidate tail，但不能无 lifecycle/utility gate 地 overflow。 |
| `diagnostic/stage1_profile_aware_gated_fact_list_rerank_v228_scope_summary.md` | profile-aware gated fact/list rerank clean，但 LoCoMo changed judge 回退。 |
| `diagnostic/stage1_route_tail_cap56_v223_scope_summary.md` | route-scoped final evidence cap 降 token，但 changed judge 明显回退。 |
| `diagnostic/stage1_temporal_materialized_context_source_gate_v219_scope_summary.md` | selected-context hard gate 降 token / risk，但 answer regression 明显。 |

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
