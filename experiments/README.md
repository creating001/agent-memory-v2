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
| 2 | Query-time 简化与降 token | v347 表明只压 Working Memory Packet boilerplate 可以小幅降 query token 且 probe changed-answer judge 不退；下一步做 larger/full cache-aligned diff，优先让 build-owned workspace policy 精确替换单个 query 组件，继续避免 broad 压 guide 语义或 raw evidence。 |
| 3 | Context organization | 让 working/long-term/archival memory objects 真正参与 context organization：source-backed activation、conflict chain、state verification、raw-row expansion 和 audit worklist 要形成统一 plan，而不是分散 trace-only 信号。 |
| 4 | Answer/verifier | 用 consistency verifier 的数值、时间、说话人、实体、状态冲突和 unsupported-answer 风险触发通用 source expansion / abstention；禁止 benchmark-specific rewrite。 |
| 5 | src cleanup | 每阶段小范围清理 `src/`，只删除已确认无用且不影响复现/消融的代码。 |

## 当前候选和近期结论

| 配置/文档 | 类型 | 关键结果 | 决策 |
|---|---|---|---|
| `configs/stage1_guard_only_short_packet_v347_seeded_qwen36_no_think_build4k_cached.json` / `diagnostic/v347_guard_only_short_packet_lme_probe50/summary.md` / `diagnostic/v347_guard_only_short_packet_locomo_probe50/summary.md` / `diagnostic/v347_guard_only_short_packet_changed_vs_v343/summary.md` | guard-only WMP presentation compression candidate | v347 继承 v343，只把 Working Memory Packet 的短 header 和 dedupe 显式打开到 `current_state` / `fact_lookup` / `profile_preference` 路由；不启用 broad compact guide，不改 raw Memory rows，不让 conflict-slot values 进入 prompt-visible packet hints。Probe50 avg query：LME `5427.60 -> 5357.30`，LoCoMo `5592.62 -> 5561.92`；compile-scan evidence row set/order diff 两边均 `0/50`，non-WMP prompt diff `0/50`。Changed-answer judge：LME v343/v347 均 strict+lenient `5/6`；LoCoMo v343/v347 均 `18/19`。 | 保留为当前最干净的 query-token 候选，但暂不升 LTS。它比 v344 更稳，因为只压 packet boilerplate、不压 guide 语义；下一步需要 larger/full cache-aligned diff 或 full changed-answer judge，确认 probe 外仍不回退。 |
| `configs/stage1_workspace_contract_budget_v346_seeded_qwen36_no_think_build4k_cached.json` / `diagnostic/v346_workspace_contract_budget_compile_scan_diff_vs_v343.md` | workspace-contract context-budget diagnostic | v346 让 build-owned `memory_workspace_contract_v1` 参与 runtime context budget：`registry_anchor_retention=true`、`anchor_source=memory_workspace_contract`，其余 v343 预算和 compiler evidence 不变。Compile-scan：LME prompt/evidence diff `0/50`，LoCoMo list-count prompt/evidence diff `2/50`；avg context chars LME `18034.42 -> 18034.42`，LoCoMo `16342.96 -> 16343.74`。Anchor retention 两边均 `50/50` 激活且 dropped anchors `0`。 | 不升 LTS，不跑 answer judge。方向 clean 且系统化，但当前 contract retention 只保护 anchor，几乎不降 query token；下一步要做 query-scoped workspace policy / guide replacement，而不是宽预算下保留全部 workspace anchors。 |
| `configs/stage1_compact_guide_blocks_v344_seeded_qwen36_no_think_build4k_cached.json` / `diagnostic/v344_compact_guide_blocks_lme_probe50/summary.md` / `diagnostic/v344_compact_guide_blocks_locomo_probe50/summary.md` / `diagnostic/v344_compact_guide_blocks_changed_vs_v343/summary.md` | compact guide token diagnostic | v344 基于 v343，只开启 `compact_query_guide_blocks=true`，不改变 raw Memory rows 和 evidence row 顺序。Probe50 avg query：LME `5427.60 -> 5340.08`，LoCoMo `5592.62 -> 5486.80`；compile-scan evidence row order diff 两边均 `0/50`。Changed-answer judge：LME v343/v344 strict+lenient `5/6 -> 6/6`；LoCoMo strict `24/27 -> 21/27`、lenient `24/27 -> 23/27`。 | 不升 LTS。token 下降真实，但 broad guide 压缩会造成 temporal 精度下降、list scope drift 和 inference over-abstention；后续不能默认压 guide 语义。 |
| `configs/stage1_guard_only_slot_coverage_packet_v343_seeded_qwen36_no_think_build4k_cached.json` / `diagnostic/v343_guard_only_slot_coverage_packet_lme_probe50/summary.md` / `diagnostic/v343_guard_only_slot_coverage_packet_locomo_probe50/summary.md` / `diagnostic/v343_guard_only_slot_coverage_packet_changed_vs_v340/summary.md` | guard-only build-owned coverage candidate | v343 保留 build-owned slot coverage 给 slot guard / audit / diagnostic，但不让 `conflict_slot.values` 默认变成 Working Memory Packet 的可见 `hint=`。Compile-scan vs v340：LoCoMo prompt diff `2/50`、LME `5/50`。Probe50 avg query：LME `5402.98 -> 5427.60`，LoCoMo `5577.30 -> 5592.62`。Changed-answer judge：LoCoMo v340/v343 均 strict/lenient `14/17` / `15/17`；LME v340/v343 均 `4/4`。 | 不升 LTS，但作为当前更安全的 coverage 候选保留。它消除了 v341/v342 的 packet-visible conflict-value 风险且 changed judge 不退；缺点是 query token 没降。 |
| `configs/stage1_memory_object_index_v288_seeded_qwen36_no_think_build4k_cached.json` / `diagnostic/stage1_memory_object_index_v288_full_summary.md` | current LTS | v288 vs v287：LME/LoCoMo full answer/prompt/route/evidence/retrieval/build records diff `0`；`memory_object_index_v1` applied `2040/2040`；avg query tokens LME `6455.588`、LoCoMo `6093.962337662338` | 升 LTS；统一 build-owned memory object interface，性能继承 v287 |

入口表只保留当前候选、关键反例和 LTS；旧中间版本回到对应 run summary 和 git 追溯。

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
| `diagnostic/v337_workspace_packet_structured_replacement_lme_probe50_changed_vs_v336/summary.md` / `diagnostic/v337_workspace_packet_structured_replacement_locomo_probe50_changed_vs_v336/summary.md` | 直接用 verbose Working Memory Packet 替换 fact/profile/current_state Structured Guide 会涨 query token，并在 LoCoMo changed judge 回退；后续需要短版、slot-conservative workspace packet。 |
| `diagnostic/v339_slot_guarded_compact_workspace_packet_locomo_probe50/summary.md` | suppress-only slot guard 能减少 misleading packet 和单样本 query token，但 relationship/status 问题仍可能需要短 row index；只抑制 packet 不足以恢复答案。 |
| `diagnostic/v344_compact_guide_blocks_changed_vs_v343/summary.md` | broad compact guide 能降 query token，但会削弱 temporal/list/inference 的 source-grounded约束；guide 语义不能无差别压缩。 |
| `diagnostic/v346_workspace_contract_budget_compile_scan_diff_vs_v343.md` | workspace contract 可以作为 clean 的 build-owned source-retention contract，但宽预算下只保护 anchors、不降 query token；降 token 应来自 query-scoped workspace policy 和组件替换，而不是简单保留全部 contract anchors。 |

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
