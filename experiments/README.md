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
| 1 | Build memory system | 继续把 memory 从 typed retrieval hint 推进为 build-time managed state：已覆盖 value slots、activation ids、operation slots、state conflict slots、operation registry、working view、lifecycle audit；v302 已让 Working Memory Packet 显式消费 `memory_lifecycle_audit_v1`，下一步让 verifier/context budget 共用同一 lifecycle interface。 |
| 2 | Query-time 简化 | 收敛为 candidate activation、context compiler、source-grounded answer、consistency verifier 四层；下一步在 full diff 后删除或降级旧 state/value guide、operation registry 直读等兼容层。 |
| 3 | Context organization | v302 packet 已把 conflict/value/operation/object lifecycle stage 和 actions 放入 source-backed context organization；下一步把 source pressure、same-slot coverage、temporal validity 和 conflict state 合成统一 working-memory compiler。 |
| 4 | Answer/verifier | 把 trace-only audit 逐步推进为通用 consistency verifier：检查数值、时间、说话人、实体、状态冲突和 unsupported answer，不写 benchmark-specific rewrite。 |
| 5 | src cleanup | 每阶段小范围清理 `src/`，只删除已确认无用且不影响复现/消融的代码。 |

## 当前候选和近期结论

| 配置/文档 | 类型 | 关键结果 | 决策 |
|---|---|---|---|
| `configs/stage1_lifecycle_packet_v302_seeded_qwen36_no_think_build4k_cached.json` / `diagnostic/stage1_lifecycle_packet_v302_lme_smoke5/` / `diagnostic/stage1_lifecycle_packet_v302_locomo_smoke5/` / `diagnostic/stage1_lifecycle_packet_v302_lme_op_smoke21/` | candidate | v302 新增 `working_memory_packet_source=lifecycle_audit`，让 Working Memory Packet 直接消费 build-owned lifecycle audit，并在 prompt 中暴露 stage/actions/current-historical source order；最终证据仍回 raw Memory rows。v302 vs v301：LME smoke5、LoCoMo smoke5 answer/prompt/evidence/retrieval/token diff `0`；LME op-smoke21 answer/evidence/retrieval diff `0`，prompt diff `1/21`，packet `source=lifecycle_audit` applied `1/21`，avg query tokens `5631.524 -> 5636.190`，build tokens不变。 | 保留候选；减少 “lifecycle audit 只在 trace 里、memory 不参与 context organization” 风险；只有 smoke/diff，无 full judge，不升 LTS |
| v292-v301 memory registry 到 lifecycle view line | candidate history | v292 建立 `memory_operation_registry_v1`，v293-v295 让 registry 参与 utility、context/verifier audit 和 context-budget anchors，v296-v297 写成 Working Memory Packet 并合并旧 state/value guides，v298 增加 `memory_working_view_v1`，v299 让 utility/anchor retention 优先消费 working view，v300 补 working-view 消融开关，v301 增加 `memory_lifecycle_audit_v1`。各版 smoke/diff 未发现答案变化；详细指标回到对应 diagnostic run 和 git。 | 已被 v302 继承；作为 build-owned memory organization 线的可追溯锚点 |
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
