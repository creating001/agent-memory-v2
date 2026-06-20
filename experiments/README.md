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
| 1 | Build memory system | v321 已在 build 侧新增 `memory_workspace_policy_v1`，把 candidate activation、context pack、source expansion、answer verification、audit 五个 stage 变成可审计 policy surface，并标出 state/value guide、update-conflict guide、operation workpad、selected context、context budget 的 workspace 替代面。下一步让 compiler/retrieval 小范围消费 policy 做 source-backed activation/pack，而不是继续加 query patch。 |
| 2 | Query-time 简化与降 token | v321 已启用 compact selected context 和低 headroom `compiler.context_pressure`，先用通用 context organization 降 token。下一步优先删除或 trace-only 化已经被 workspace policy 覆盖的兼容层；每次只改一个 query surface，并用 changed-answer judge 验证。 |
| 3 | Context organization | 当前 query trace 已记录 plan/state/journal/contract/snapshot/policy final-evidence overlap、focus counts、manager decisions、context actions、verifier checks 和 worklists。下一步把 source pressure、same-slot coverage、temporal validity 和 conflict state 变成 policy 驱动的 pack/expand 决策，但最终证据仍保持 raw rows。 |
| 4 | Answer/verifier | v317 已新增 trace-only consistency verifier，检查数值、时间、说话人、实体、状态冲突和 unsupported answer。下一步用这些风险信号驱动 source expansion / answer abstention 的通用策略，但必须先做 paired diff 和 changed-answer judge，不能写 benchmark-specific rewrite。 |
| 5 | src cleanup | 每阶段小范围清理 `src/`，只删除已确认无用且不影响复现/消融的代码。 |

## 当前候选和近期结论

| 配置/文档 | 类型 | 关键结果 | 决策 |
|---|---|---|---|
| `configs/stage1_workspace_policy_pressure_v321_seeded_qwen36_no_think_build4k_cached.json` / `diagnostic/stage1_workspace_policy_pressure_v321_lme_smoke5/` / `diagnostic/stage1_workspace_policy_pressure_v321_locomo_smoke5/` / `diagnostic/stage1_workspace_policy_pressure_v321_lme_op_smoke21/` / `diagnostic/stage1_workspace_policy_pressure_v321_changed_vs_v320/` | system + token candidate | v321 新增 build-owned `memory_workspace_policy_v1`：5 个 query stage、6 个旧 query component 替代面，每题 policy applied。query tokens：LME smoke `5388.2`，LoCoMo smoke `5596.2`，LME op21 `5376.67`；context pressure applied `2/5 / 0/5 / 14/21`；consistency risk flags `0 / 4 / 2`。vs v320：LME smoke answer/prompt/evidence diff `0/5`；LoCoMo changed answers `2/5`，dual judge old/new 均 `2/2`；LME op21 changed answers `3/21`，dual judge old/new 均 `2/3`，唯一 `ea4e...` old/new 都 WRONG。 | 保留为下一候选；比 v320 更直接降低风险 1/5，并降低 LoCoMo smoke 与 LME op21 query token。暂不升 LTS：需要扩大 scope/full diff，且 `ea4e...` 暴露 context pressure 下的 wrong->wrong 行为，需要继续处理。 |
| `configs/stage1_snapshot_pressure_budget_v320_seeded_qwen36_no_think_build4k_cached.json` / `diagnostic/stage1_snapshot_pressure_budget_v320_lme_smoke5/` / `diagnostic/stage1_snapshot_pressure_budget_v320_locomo_smoke5/` / `diagnostic/stage1_snapshot_pressure_budget_v320_lme_op_smoke21/` / `diagnostic/stage1_snapshot_pressure_budget_v320_changed_vs_v319/` | token candidate | v320 继承 v319 snapshot，保留 `memory_system_state` anchor，做保守 source-backed pressure budget：global evidence `58/17k`、current/profile anchor keep `31`、temporal evidence `39/17.5k`、retrieval context budget `58/21k`。query tokens：LME smoke `5567.2 -> 5331.0`，LoCoMo smoke `6048.2 -> 5931.2`，LME op21 `5648.62 -> 5497.86`；consistency risk flags 继承 `0 / 4 / 2`。vs v319：LME smoke/op changed answer 仅 `1` 条，dual changed judge old/new 均 WRONG；LoCoMo smoke changed answer `1` 条，dual changed judge old/new 均 CORRECT。 | 保留为 token 降本候选，不升 LTS；full 前必须做 changed-answer judge 或更大 scope 验证。说明 query token 可以收紧，但预算改动会影响 prompt/answer，不能无 judge 直接继承性能。 |
| `configs/stage1_memory_workspace_snapshot_v319_seeded_qwen36_no_think_build4k_cached.json` / `diagnostic/stage1_memory_workspace_snapshot_v319_lme_smoke5/` / `diagnostic/stage1_memory_workspace_snapshot_v319_locomo_smoke5/` / `diagnostic/stage1_memory_workspace_snapshot_v319_lme_op_smoke21/` | candidate | v319 新增 compact build-owned `memory_workspace_snapshot_v1`，把 layered workspace、operation readiness、state/conflict/temporal/long-term worklists、context lanes 和 verifier worklists 汇总成 query/context/verifier 可消费的系统快照；context-budget anchor 回到 `memory_system_state`，避免 v318 full 中 workspace-contract anchor 导致的 evidence drift。smoke/op vs v317/v318 的 answer/prompt/evidence/final hits/token/cache diff 全 `0`。avg build/query tokens：`92386.0 / 5567.2`、`45868.0 / 6048.2`、`87656.19 / 5648.62`；snapshot applied `5/5 / 5/5 / 21/21`；state/verifier worklists 和 retrieve/expand/verify/audit readiness 全量可见；consistency risk flags `0 / 4 / 2`。 | 保留候选；主要降低风险 1/3/5，让 build 更像可操作 memory system，而不是 typed-memory hint。升 LTS 前需 full diff；若 full 输出不变可继承 LTS 性能，否则跑 changed-answer judge。 |
| `configs/stage1_memory_workspace_contract_v318_seeded_qwen36_no_think_build4k_cached.json` / `diagnostic/stage1_memory_workspace_contract_v318_*` / `diagnostic/stage1_memory_workspace_contract_v318_diff_vs_v288_full.json` | candidate / negative full diff | v318 smoke/op 相对 v317 diff 为 `0`，但 LME/LoCoMo full 相对 v288 发现 answer diff `19/500`、`59/1540`，prompt/evidence/final hits 也有变化；原因是 context-budget anchor 改为 `memory_workspace_contract` 后改变了部分保留证据。full avg build/query tokens：LME `85393.566 / 6364.47`，LoCoMo `62015.574 / 6149.53`。 | 不直接升 LTS；保留 workspace contract 作为 build interface，但默认不再让它直接驱动 budget anchor，改由 v319 compact snapshot 先进入 trace/context/verifier audit。 |
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
