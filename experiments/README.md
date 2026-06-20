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
| 2 | Query-time 简化与降 token | v323-v327 说明压缩 selected-context 能降 token 但 LoCoMo full 会回退。下一步优先删减或下沉 query 侧长 guide/兼容层，只保留短 policy output 和 raw evidence rows，而不是再剪 source rows。 |
| 3 | Context organization | 让 working/long-term/archival memory objects 真正参与 context organization：source-backed activation、conflict chain、state verification、raw-row expansion 和 audit worklist 要形成统一 plan，而不是分散 trace-only 信号。 |
| 4 | Answer/verifier | 用 consistency verifier 的数值、时间、说话人、实体、状态冲突和 unsupported-answer 风险触发通用 source expansion / abstention；禁止 benchmark-specific rewrite。 |
| 5 | src cleanup | 每阶段小范围清理 `src/`，只删除已确认无用且不影响复现/消融的代码。 |

## 当前候选和近期结论

| 配置/文档 | 类型 | 关键结果 | 决策 |
|---|---|---|---|
| `configs/stage1_workspace_query_component_policy_v334_seeded_qwen36_no_think_build4k_cached.json` / `diagnostic/v334_workspace_query_component_policy_lme_smoke5/summary.md` / `diagnostic/v334_workspace_query_component_policy_locomo_smoke5/summary.md` | cache-aligned shadow policy | v334 回用 v288 answer cache，验证 v333 的 build-owned query policy 是 prompt-visible no-op：LME smoke vs v288 diff `0/5`、avg query `5567.2`；LoCoMo smoke vs v288 full 同 key diff `0/5`、avg query `6048.2`；两边 `8/8` query component shadow-ready。 | 可作为后续 query 减法的安全基线，但暂不升 LTS：它减少系统设计风险，尚未真正降低 full query token 或 query stack 复杂度。下一步只压固定 answer/rules contract，不动 guide/raw evidence。 |
| `configs/stage1_workspace_query_component_policy_v333_seeded_qwen36_no_think_build4k_cached.json` / `diagnostic/v333_workspace_query_component_policy_lme_smoke5/summary.md` / `diagnostic/v333_workspace_query_component_policy_locomo_smoke5/summary.md` | build-owned query policy shadow | v333 把 8 个 query component 责任映射到 `memory_workspace_policy.query_component_policy`，smoke 中 LME/LoCoMo 均 `8/8` shadow-ready；prompt tokens 与 v288 smoke 对齐，但新 answer cache 触发 cold generation，LME 1 条 abstention 措辞 diff，dual judge LME `4/5`、LoCoMo `5/5`。 | 不作为后续基线。v333 证明 build-owned policy 覆盖面可行；下一步用 v334 回用 v288 answer cache 做零 diff 验证，再开始真正删除/下沉 query guide。 |
| `configs/stage1_route_gated_structured_guide_v332_seeded_qwen36_no_think_build4k_cached.json` / `diagnostic/v332_route_gated_structured_guide_probe_summary/summary.md` | route-gated guide token diagnostic | v332 只把 fact/profile 的 Structured Evidence Guide 行数从 12 降到 8，不动 raw Memory Context / evidence selection / answer contract / verifier。Probe50 avg query tokens：LME `5599.64`、LoCoMo `5868.8`；changed-answer judge：LME `4/6 -> 3/6` strict+lenient，LoCoMo strict `17/21 -> 16/21`、lenient `17/21 -> 18/21`。 | 不升 LTS。收益小且 strict 回退；不要继续做 max-row 微调，下一步转向把 query guide 层下沉到 build-time memory operations。 |
| `configs/stage1_inline_memory_header_v331_seeded_qwen36_no_think_build4k_cached.json` / `diagnostic/v331_inline_memory_header_probe_summary/summary.md` | query token diagnostic | v331 只把 Memory Context header 改为 inline，不动 evidence selection / raw row text / guide / answer contract / verifier。Probe50 avg query tokens：LME `5525.84`、LoCoMo `5720.06`，均低于 6K；changed-answer judge：LME old/new strict+lenient `5/7 -> 4/7`，LoCoMo `16/20,18/20 -> 16/20,18/20`。 | 不升 LTS。即使只压 answer-visible Memory header 也会造成 LME 1 条 specificity 回退；下一步 query 降 token 优先删减/下沉 guide 兼容层，避免改 raw evidence presentation。 |
| `configs/stage1_workspace_policy_profile_tier_v327_seeded_qwen36_no_think_build4k_cached.json` / `diagnostic/stage1_workspace_policy_profile_tier_v327_lme_full_changed_vs_v288/summary.md` / `diagnostic/stage1_workspace_policy_profile_tier_v327_locomo_full_changed_vs_v288/summary.md` | explicit profile-tier token candidate | v327 把 selected-context profiles 放进 build-owned `memory_workspace_policy_v1`：temporal/question-reference 用 `compact_source_coverage`，默认 fact/list/profile 用 `balanced_source_coverage`。LME full projected strict/lenient 继承 v288 `0.834 / 0.846`，avg query `6455.588 -> 6454.482`；LoCoMo full avg query `6093.962 -> 5755.880`，但 answer diff `684/1540`，changed-answer old/new strict `511/684 -> 490/684`、lenient `534/684 -> 509/684`，projected full `0.780519 / 0.803247`。 | 不升 LTS。profile-tier 是更系统的 build-owned context organization，但 selected-context 展示压缩仍会伤 LoCoMo；下一步改 query guide/兼容层，不再优先剪 raw/source context。 |
| `configs/stage1_workspace_policy_relaxed_pack_v325_seeded_qwen36_no_think_build4k_cached.json` / `diagnostic/stage1_workspace_policy_relaxed_pack_v325_lme_full_diff_vs_v288/summary.md` / `diagnostic/stage1_workspace_policy_relaxed_pack_v325_locomo_full_changed_vs_v288/summary.md` | relaxed token candidate | v325 放宽 build-owned selected-context pack：rows `5`、neighbor `160`、center `300`、before/after `1/2`。LME full vs v288 answer diff `0/500`，avg query `6455.588 -> 6454.864`，继承 strict/lenient `0.834 / 0.846`；LoCoMo full avg query `6093.962 -> 5787.903`，answer diff `673/1540`，changed-answer old/new strict `499/673 -> 481/673`、lenient `521/673 -> 503/673`，projected full `0.782468 / 0.807792`。 | 不升 LTS。保留 build-owned policy 方向；下一步不能再用固定 rows/chars/window 盲压，要做 source-pressure-aware pack/expand。 |
| `configs/stage1_workspace_policy_safe_pack_v324_seeded_qwen36_no_think_build4k_cached.json` / `diagnostic/stage1_workspace_policy_safe_pack_v324_scope_summary.md` | partial safe / token regression | v324 回到 v288 LTS 全局 evidence/context 预算，只让 build-owned `memory_workspace_policy_v1` 接管 selected-context pack。LME full 继承 v288 strict/lenient `0.834 / 0.846`；LoCoMo full avg query tokens `6093.962 -> 5547.798`，但 answer diff `691/1540`，changed-answer strict/lenient old `505/691`、`530/691` -> new `488/691`、`507/691`，projected LoCoMo full `0.783117 / 0.804545`。 | 不升 LTS。v325 已验证单纯放宽 pack 仍不够；问题要转向 source-pressure-aware pack/expand。 |
| `configs/stage1_workspace_policy_pack_v323_seeded_qwen36_no_think_build4k_cached.json` / `diagnostic/stage1_workspace_policy_pack_v323_scope_summary.md` / `diagnostic/stage1_workspace_policy_pack_v323_lme_full_changed_vs_v288/summary.md` | negative token lesson | v323 把 selected-context rows/window/chars 迁移到 build-owned `memory_workspace_policy.pressure_policy`，LoCoMo smoke 降 token且 changed-answer judge 无回退；但 LME full vs v288：answer diff `113/500`，avg query tokens `6455.588 -> 5972.272`，changed-answer dual judge old/new strict `72/113 -> 56/113`、lenient `76/113 -> 63/113`。 | 不升 LTS。保留 selected-context policy 设计；回滚或收窄 aggressive global context pressure，避免证据压缩带来性能回退。 |
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
