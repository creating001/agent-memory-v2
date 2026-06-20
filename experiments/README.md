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

v288 关键证据见 `experiments/diagnostic/stage1_memory_object_index_v288_full_summary.md`。如果论文级最终汇报需要 fresh full judge，再对最终 LTS 配置完整重跑 dual judge；日常迭代优先用 full diff + changed-answer paired judge，避免无意义重跑。

## 口径

- 主线目标是通用、clean、可消融、可持续迭代、且有方法创新性的 Agent Memory system/library，不是围绕 LongMemEval/LoCoMo 手写补丁。
- 方法性能主要看 DeepSeek dual `deepseek-v4-flash` judge accuracy：strict 为两遍都判对，lenient 为任一遍判对；Exact/F1/BLEU 只作参考。
- 新 LTS 优先看 clean/general/system 风险是否减少；性能提升是强加分项，但不是唯一前提。若风险明显减少且性能不退，可以升 LTS；若小幅回退但显著降低 design-for-benchmark 或系统风险，需要明确记录 tradeoff 后再判断。
- 每个算法版本先做本地 git commit；正式实验记录引用 commit、配置、token 成本、outputs 路径和 judge 路径。GitHub 只在用户明确要求时 push。
- 普通诊断不需要反复重跑 full；若只影响少量预测，优先做 changed-answer paired judge。不要为了 manifest clean 或形式完整重复重跑未变化样本。

## 优先待办

| 优先级 | 方向 | 下一步 |
|---:|---|---|
| 1 | Build memory system | v311-v318 已建立 `memory_working_compiler_plan_v1`、`memory_system_state_v1`、`memory_operation_journal_v1`、`memory_workspace_contract_v1` 和通用 consistency audit。下一步让 source pressure、same-slot coverage、temporal validity、conflict state 和 verifier 反馈进入更统一的 workspace policy，减少旧 guide/packet 兼容层。 |
| 2 | Query-time 简化 | 收敛为 candidate activation、context compiler、source-grounded answer、consistency verifier 四层；优先删除或降级旧 state/value guide、operation registry 直读、query grouping fallback 等兼容层，删除前必须用 diff/单测证明不影响复现。 |
| 3 | Context organization | 当前 build 输出 workspace contract、context organization plan、memory system state 与 operation journal，query trace 已记录 contract/state/journal final-evidence overlap、focus counts、manager decisions、context actions、verifier checks，并由 workspace contract 驱动 anchor retention；下一步让 context compiler 用 contract 做通用 pack/verify/audit 决策。 |
| 4 | Answer/verifier | v317 已新增 trace-only consistency verifier，检查数值、时间、说话人、实体、状态冲突和 unsupported answer。下一步用这些风险信号驱动 source expansion / answer abstention 的通用策略，但必须先做 paired diff 和 changed-answer judge，不能写 benchmark-specific rewrite。 |
| 5 | src cleanup | 每阶段小范围清理 `src/`，只删除已确认无用且不影响复现/消融的代码。 |

## 当前候选和近期结论

| 配置/文档 | 类型 | 关键结果 | 决策 |
|---|---|---|---|
| `configs/stage1_memory_workspace_contract_v318_seeded_qwen36_no_think_build4k_cached.json` / `diagnostic/stage1_memory_workspace_contract_v318_lme_smoke5/` / `diagnostic/stage1_memory_workspace_contract_v318_locomo_smoke5/` / `diagnostic/stage1_memory_workspace_contract_v318_lme_op_smoke21/` | candidate | v318 在 v317 上新增 build-owned `memory_workspace_contract_v1`，把 short-term/working/long-term/archival/quarantine 层、create/update/merge/supersede/retrieve/expand/verify/audit readiness、context anchor source 和 raw-row expansion policy 收敛成稳定 query contract；context-budget anchor 改为消费该 contract。vs v317 三组 prediction/answer/prompt/evidence/final hits/token/cache diff 全 `0`，anchor retained set diff `0`（仅 source label/order trace 变化）。avg build/query tokens：`92386.0 / 5567.2`、`45868.0 / 6048.2`、`87656.19 / 5648.62`；workspace contract applied `5/5 / 5/5 / 21/21`，readiness 全覆盖；consistency risk flags 继承 v317 的 `0 / 4 / 2`。 | 保留候选；风险 1/3/5 继续下降，memory organization 不再只是 state/journal 内部字段，而是可由 query 统一消费的 workspace contract。当前仍是 smoke/diff 证据，升 LTS 前需 full diff 或 changed-answer judge |
| v292-v317 memory registry 到 verifier line | candidate history | v292-v316 建立 registry、working view、lifecycle/layer/API/context interface、working plan、system state 和 operation journal；v317 增加 trace-only consistency verifier audit。 | 已被 v318 继承；详细指标回到对应 diagnostic run 和 git |
| `configs/stage1_memory_object_index_v288_seeded_qwen36_no_think_build4k_cached.json` / `diagnostic/stage1_memory_object_index_v288_full_summary.md` | current LTS | v288 vs v287：LME/LoCoMo full answer/prompt/route/evidence/retrieval/build records diff `0`；`memory_object_index_v1` applied `2040/2040`；avg query tokens LME `6455.588`、LoCoMo `6093.962337662338` | 升 LTS；统一 build-owned memory object interface，性能继承 v287 |
| v276-v287 value/state memory line | previous anchors | tier manifest、operation ledger、state-conflict manifest、scalar/value manifest 和 state-only value slot guide 奠定 build-owned memory object 基础；全类型 value slot guide 曾明显回退，说明 memory 进入 query 必须 source-backed、typed、intent-gated。 | 被 v288+ 继承；保留关键教训，不在入口堆长历史 |

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
