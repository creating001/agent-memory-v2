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
| 1 | Build memory system | 保留 v327 的 build-owned profile-tier 思路，但不要继续只改 selected-context formatting；下一步让 workspace policy 负责 source expansion / conflict verification / guide replacement，最终 raw evidence presentation 尽量贴近 v288。 |
| 2 | Query-time 简化与降 token | v336 说明只压固定 answer contract 可以降 token 且不复现 v335 的 LME 回退。下一步优先把 query 侧长 guide/兼容层下沉到 build-owned workspace packet，只保留短 policy output 和 raw evidence rows，而不是再剪 source rows。 |
| 3 | Context organization | 让 working/long-term/archival memory objects 真正参与 context organization：source-backed activation、conflict chain、state verification、raw-row expansion 和 audit worklist 要形成统一 plan，而不是分散 trace-only 信号。 |
| 4 | Answer/verifier | 用 consistency verifier 的数值、时间、说话人、实体、状态冲突和 unsupported-answer 风险触发通用 source expansion / abstention；禁止 benchmark-specific rewrite。 |
| 5 | src cleanup | 每阶段小范围清理 `src/`，只删除已确认无用且不影响复现/消融的代码。 |

## 当前候选和近期结论

| 配置/文档 | 类型 | 关键结果 | 决策 |
|---|---|---|---|
| `configs/stage1_answer_contract_slot_guard_v336_seeded_qwen36_no_think_build4k_cached.json` / `diagnostic/v336_answer_contract_slot_guard_lme_probe50_changed_vs_v288/summary.md` / `diagnostic/v336_answer_contract_slot_guard_locomo_probe50_changed_vs_v288/summary.md` | compact answer contract candidate | v336 在 v335 的固定 answer/rules/output contract 压缩上加入通用 slot-complete guards：named venue/studio/store 可作为 where answer，occupation/role 保留 employer/workplace qualifier。Probe50 avg query：LME `5677.4 -> 5555.76`，LoCoMo `6544.92 -> 5700.88`；changed judge：LME strict+lenient `6/8 -> 6/8`，LoCoMo strict `20/25 -> 21/25`、lenient `20/25 -> 22/25`。 | 作为当前 query-token 候选保留，但不靠 probe50 升 LTS。下一步把 query guide 责任下沉到 build-owned workspace packet，而不是继续压 raw evidence。 |
| `configs/stage1_answer_contract_compact_v335_seeded_qwen36_no_think_build4k_cached.json` / `diagnostic/v335_answer_contract_compact_lme_probe50_changed_vs_v288/summary.md` / `diagnostic/v335_answer_contract_compact_locomo_probe50_changed_vs_v288/summary.md` | answer-contract token candidate | v335 只压固定 answer/rules/output contract，不压 Structured Guide / Temporal Aid / raw Memory Context。Probe50 avg query：LME `5677.4 -> 5530.18`，LoCoMo `5916.36 -> 5695.24`；changed judge：LME strict+lenient `6/8 -> 5/8`，LoCoMo strict `21/28 -> 26/28`、lenient `22/28 -> 26/28`。 | 不升 LTS。方向有价值但 LME 回退；v336 已用通用 slot-complete safeguards 修复该回退。 |
| `configs/stage1_workspace_query_component_policy_v334_seeded_qwen36_no_think_build4k_cached.json` / `diagnostic/v334_workspace_query_component_policy_lme_smoke5/summary.md` / `diagnostic/v334_workspace_query_component_policy_locomo_smoke5/summary.md` | cache-aligned shadow policy | v334 回用 v288 answer cache，验证 v333 的 build-owned query policy 是 prompt-visible no-op：LME smoke vs v288 diff `0/5`、avg query `5567.2`；LoCoMo smoke vs v288 full 同 key diff `0/5`、avg query `6048.2`；两边 `8/8` query component shadow-ready。 | 保留为 build-owned query policy 的零差异证据。v336 已承接 fixed answer-contract 压缩；下一步应替换 guide/workpad/component 责任。 |
| `configs/stage1_workspace_policy_profile_tier_v327_seeded_qwen36_no_think_build4k_cached.json` / `diagnostic/stage1_workspace_policy_profile_tier_v327_lme_full_changed_vs_v288/summary.md` / `diagnostic/stage1_workspace_policy_profile_tier_v327_locomo_full_changed_vs_v288/summary.md` | explicit profile-tier token candidate | v327 把 selected-context profiles 放进 build-owned `memory_workspace_policy_v1`：temporal/question-reference 用 `compact_source_coverage`，默认 fact/list/profile 用 `balanced_source_coverage`。LME full projected strict/lenient 继承 v288 `0.834 / 0.846`，avg query `6455.588 -> 6454.482`；LoCoMo full avg query `6093.962 -> 5755.880`，但 answer diff `684/1540`，changed-answer old/new strict `511/684 -> 490/684`、lenient `534/684 -> 509/684`，projected full `0.780519 / 0.803247`。 | 不升 LTS。profile-tier 是更系统的 build-owned context organization，但 selected-context 展示压缩仍会伤 LoCoMo；下一步改 query guide/兼容层，不再优先剪 raw/source context。 |
| `configs/stage1_memory_object_index_v288_seeded_qwen36_no_think_build4k_cached.json` / `diagnostic/stage1_memory_object_index_v288_full_summary.md` | current LTS | v288 vs v287：LME/LoCoMo full answer/prompt/route/evidence/retrieval/build records diff `0`；`memory_object_index_v1` applied `2040/2040`；avg query tokens LME `6455.588`、LoCoMo `6093.962337662338` | 升 LTS；统一 build-owned memory object interface，性能继承 v287 |

## 负向教训索引

| 文档/目录 | 教训 |
|---|---|
| `diagnostic/stage1_state_only_value_slot_guide_v287_full_summary.md` | memory object 可以进入 query，但必须 source-backed、typed、intent-gated，并保持 raw evidence-first。 |
| `diagnostic/stage1_explicit_date_temporal_route_v271_full_summary.md` | 显式日期可以帮助识别 temporal intent，但不能无条件抢过 fact/list；应只修正 latest/recent 与 explicit-date 冲突的窄场景。 |
| `diagnostic/stage1_graph_evidence_overflow_v263_scope_summary.md` | source-backed graph utility 可以进入 candidate tail，但不能无 lifecycle/utility gate 地 overflow。 |
| `diagnostic/stage1_profile_aware_gated_fact_list_rerank_v228_scope_summary.md` | profile-aware gated fact/list rerank clean，但 LoCoMo changed judge 回退。 |
| `diagnostic/stage1_route_tail_cap56_v223_scope_summary.md` | route-scoped final evidence cap 降 token，但 changed judge 明显回退。 |
| `diagnostic/stage1_temporal_materialized_context_source_gate_v219_scope_summary.md` | selected-context hard gate 降 token / risk，但 answer regression 明显。 |
| `diagnostic/stage1_workspace_policy_pack_v323_lme_full_changed_vs_v288/summary.md` | 大范围 context pressure 能降 query token，但 LME full changed-answer judge 明显回退；token 策略必须 source-pressure-aware，不能只按 headroom 剪 evidence。 |
| `diagnostic/v331_inline_memory_header_probe_summary/summary.md` / `diagnostic/v332_route_gated_structured_guide_probe_summary/summary.md` | query micro-compression 收益小且容易触发 specificity / strict 回退；后续 query 降 token 应下沉 guide 责任，不再继续做 header 或 max-row 微调。 |

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
