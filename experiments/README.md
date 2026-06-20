# 实验入口

`experiments/` 是正式结果和关键诊断的人类可读入口。各 run 目录保留 `summary.md`、`diagnosis.md`、`metrics.json`、`manifest.json` 和配置快照；本文件只维护当前 LTS、统一口径、优先待办、近期候选和必要负向教训。长历史细节回到对应 scope summary、run 目录和 git。

## 当前 LTS

| 项目 | 结果 |
|---|---|
| 当前 LTS 配置 | `configs/stage1_order_safe_value_parser_v283_seeded_qwen36_no_think_build4k_cached.json` |
| Backbone | `Qwen/Qwen3.6-35B-A3B` answer/build，`chat_template_kwargs.enable_thinking=false` |
| 方法定位 | source-backed Agent Memory system view：build memory management + memory system graph v3 + working/long-term/archival/quarantine tier manifest + operation_manifest_v1 + state_conflict_manifest_v1 + source policy + governance/activation utility + scoped tier-aware state/profile activation + order-safe general value parser + raw evidence compiler + source-grounded answer audit。Typed memory 只能作为受 governance/utility/tier/operation 约束的 activation、ranking hint 和 audit；最终 evidence 仍回到 raw Memory rows。 |
| LongMemEval-S full | strict/lenient `0.834000 / 0.846000`，`417/500` strict，`423/500` lenient；avg build/query tokens `85393.566 / 6464.954` |
| LoCoMo non-adversarial full | strict/lenient `0.794156 / 0.819481`，`1223/1540` strict，`1262/1540` lenient；avg build/query tokens `62015.57402597403 / 6093.794155844156` |
| LTS 理由 | v283 相对 v280：LME full answer diff `3/500`，changed-answer dual judge strict/lenient `+1/+1`；LoCoMo full answer/prompt/route/evidence/retrieval/token/build_memory diff 全部 `0`。它去掉 update/conflict guide 中 benchmark-shaped 单位白名单，并对 event-order/timeline 问题使用 scalar-only extraction，减少非事件单位误导。 |
| 主要局限 | query stack 仍有 route/selected-context/state-guide/ledger/audit 兼容层；`operation_manifest_v1` 仍主要是 build-owned contract，还没有全面替代 query-side operation guide；LME/LoCoMo query tokens 仍略高于 6K 目标但低于 8K hard diagnostic 线。 |

v283 关键证据见 `experiments/diagnostic/stage1_order_safe_value_parser_v283_full_summary.md`。如果论文级最终汇报需要 fresh full judge，再对最终 LTS 配置完整重跑 dual judge；日常迭代优先用 full diff + changed-answer paired judge，避免无意义重跑。

## 口径

- 主线目标是通用、clean、可消融、可持续迭代、且有方法创新性的 Agent Memory system/library，不是围绕 LongMemEval/LoCoMo 手写补丁。
- 方法性能主要看 DeepSeek dual `deepseek-v4-flash` judge accuracy：strict 为两遍都判对，lenient 为任一遍判对；Exact/F1/BLEU 只作参考。
- 新 LTS 优先看 clean/general/system 风险是否减少；性能提升是强加分项，但不是唯一前提。若风险明显减少且性能不退，可以升 LTS；若小幅回退但显著降低 design-for-benchmark 或系统风险，需要明确记录 tradeoff 后再判断。
- 每个算法版本先做本地 git commit；正式实验记录引用 commit、配置、token 成本、outputs 路径和 judge 路径。GitHub 只在用户明确要求时 push。
- 普通诊断不需要反复重跑 full；若只影响少量预测，优先做 changed-answer paired judge。不要为了 manifest clean 或形式完整重复重跑未变化样本。

## 优先待办

| 优先级 | 方向 | 下一步 |
|---:|---|---|
| 1 | Build memory system | 继续让 query 消费 build-owned `state_conflict_manifest` / `operation_manifest`，前移 consolidation、conflict clustering、working-memory activation，不写 benchmark 规则。 |
| 2 | Query-time 简化 | 收敛为 candidate activation、context compiler、source-grounded answer、consistency verifier 四层；删除已被 build-owned manifests 覆盖的 state-guide/operation-guide 兼容层。 |
| 3 | Evidence utility | 用 build-stage utility/role 替代简单 overflow 或固定 top-k，增加 source pressure、same-slot coverage、temporal validity 和 utility ablation。 |
| 4 | Answer/verifier | 把 audit 推进为通用 consistency verifier：检查数值、时间、说话人、实体、状态冲突和 unsupported answer，不写 benchmark-specific rewrite。 |
| 5 | src cleanup | 每阶段小范围清理 `src/`，只删除已确认无用且不影响复现/消融的代码。 |

## 当前候选和近期结论

| 配置/文档 | 类型 | 关键结果 | 决策 |
|---|---|---|---|
| `configs/stage1_order_safe_value_parser_v283_seeded_qwen36_no_think_build4k_cached.json` / `diagnostic/stage1_order_safe_value_parser_v283_full_summary.md` | current LTS | v283 vs v280：LME answer diff `3/500`，changed-answer dual judge strict/lenient `+1/+1`；LoCoMo full diff `0`；avg query tokens LME `6464.954`、LoCoMo `6093.794155844156` | 升 LTS；减少固定单位白名单风险，同时保护 event-order/timeline 场景 |
| `configs/stage1_scalar_conflict_gate_v282_seeded_qwen36_no_think_build4k_cached.json` | rejected full | v282 去掉 event-order conflict chain 后，LME changed judge 仍 `3/4`，trip-order 样本继续回退 | 不升 LTS；不能简单移除 order 场景的 conflict chain |
| `configs/stage1_general_update_value_parser_v281_seeded_qwen36_no_think_build4k_cached.json` | rejected full | v281 去掉固定单位白名单，LME changed judge `3/4` vs v280 `3/4`，一条 views 修正但一条 trip-order 回退 | 不升 LTS；需要 order-safe scalar mode，被 v283 修正 |
| `configs/stage1_manifest_state_guide_v280_seeded_qwen36_no_think_build4k_cached.json` / `diagnostic/stage1_manifest_state_guide_v280_full_summary.md` | previous LTS | v280 vs v279 full answer/prompt/route/evidence/retrieval/token/build_memory diff `0`；state guide conflict source 改为 build manifest；avg query tokens LME `6463.628`、LoCoMo `6093.794155844156` | 被 v283 继承；减少 query 侧重复冲突推导 |
| `configs/stage1_memory_system_ops_v279_seeded_qwen36_no_think_build4k_cached.json` / `diagnostic/stage1_memory_system_ops_v279_full_summary.md` | previous LTS | v279 vs v278 full answer/prompt/route/evidence/retrieval/token diff `0`；operation/state-conflict manifest 覆盖 `2040/2040` | 被 v280 继承；build memory 成为 source-backed system view |
| `configs/stage1_state_profile_tier_activation_v278_seeded_qwen36_no_think_build4k_cached.json` / `diagnostic/stage1_state_profile_tier_activation_v278_full_summary.md` | previous LTS | v278 vs v276 full answer diff LME `2/500`、LoCoMo `4/1540`；changed-answer dual judge delta strict/lenient `0/0` | 被 v279 继承；tier/utility 真实参与 state/profile activation |
| `configs/stage1_tier_activation_priority_v277_seeded_qwen36_no_think_build4k_cached.json` / `diagnostic/stage1_tier_activation_priority_v277_probe_summary.md` | rejected probe | LoCoMo probe50 answer diff `8/50`，changed-answer dual judge delta `0/0`，但 prompt diff `18/50`、retrieval diff `31/50` | 不跑 full；list/temporal tier activation 过宽，被 v278 收窄 |
| `configs/stage1_memory_tier_manifest_v276_seeded_qwen36_no_think_build4k_cached.json` / `diagnostic/stage1_memory_tier_manifest_v276_full_summary.md` | previous LTS | v276 vs v275 full answer/prompt/route/evidence/retrieval/token diff `0`；tier_manifest seen LME `500/500`、LoCoMo `1540/1540` | 被 v278 继承；把 working/long-term/archival/quarantine tier 纳入 build memory system |
| `configs/stage1_explicit_date_temporal_route_v271_seeded_qwen36_no_think_build4k_cached.json` / `diagnostic/stage1_explicit_date_temporal_route_v271_full_summary.md` | rejected full | full changed answers: LME `5/500`、LoCoMo `75/1540`；changed-answer dual judge delta LME strict/lenient `-2/-2`，LoCoMo `-13/-14`；query tokens 下降但 accuracy 回退 | 不升 LTS；显式日期无条件抢过 fact/list/current 路由过宽 |
| v264-v267 memory governance / lifecycle graph line | previous anchors | lifecycle-gated graph utility、memory system quality、query surface simplification、governance manifest 均以 clean/answer-identical 或 changed-answer judge 不退方式降低风险 | 保留为可追溯锚点，详细见对应 full summary 和 git |
| v216-v263 rejected context/retrieval/prompt/object-slot lines | historical lessons | hard gate、prompt-side operation guide、wide selected context、tail-exchange replacement、simple overflow 多次造成 changed-answer 回退 | 不再逐版展开；需要时查对应 scope summary 和 git |

## 负向教训索引

| 文档/目录 | 教训 |
|---|---|
| `diagnostic/stage1_graph_evidence_overflow_v263_scope_summary.md` | source-backed graph utility 可以进入 candidate tail，但不能无 lifecycle/utility gate 地 overflow。 |
| `diagnostic/stage1_lifecycle_operation_utility_v259_*_changed_vs_v257/` | lifecycle/source-backed operation utility clean，但不应替换高置信 evidence；优先 append-only 或 stronger utility gate。 |
| `diagnostic/stage1_profile_aware_gated_fact_list_rerank_v228_scope_summary.md` | profile-aware gated fact/list rerank clean，但 LoCoMo changed judge 回退。 |
| `diagnostic/stage1_route_tail_cap56_v223_scope_summary.md` | route-scoped final evidence cap 降 token，但 changed judge 明显回退。 |
| `diagnostic/stage1_temporal_materialized_context_source_gate_v219_scope_summary.md` | selected-context hard gate 降 token / risk，但 answer regression 明显。 |
| `diagnostic/stage1_explicit_date_temporal_route_v271_full_summary.md` | 显式日期可以帮助识别 temporal intent，但不能无条件抢过 fact/list；应只修正 latest/recent 与 explicit-date 冲突的窄场景。 |

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
