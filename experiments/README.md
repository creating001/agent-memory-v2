# 实验入口

`experiments/` 是正式结果和关键诊断的人类可读入口。各 run 目录保留 `summary.md`、`diagnosis.md`、`metrics.json`、`manifest.json` 和配置快照；本文件只维护当前 LTS、统一口径、优先待办、近期候选和必要负向教训。长历史细节回到对应 scope summary、run 目录和 git。

## 当前 LTS

| 项目 | 结果 |
|---|---|
| 当前 LTS 配置 | `configs/stage1_memory_tier_manifest_v276_seeded_qwen36_no_think_build4k_cached.json` |
| Backbone | `Qwen/Qwen3.6-35B-A3B` answer/build，`chat_template_kwargs.enable_thinking=false` |
| 方法定位 | source-backed build memory management + operation ledger + schema/quality-aware memory system graph v3 + temporal-scope/validity/source-confidence manifest + working/long-term/archival/quarantine tier manifest + build-owned slot source policy + validity-aware graph utility source selection + governed typed-memory activation + build-stage activation utility manifest + narrow explicit-date/recent route conflict resolver + lifecycle-gated graph evidence utility + raw evidence compiler + source-grounded answer audit。Typed memory 只能作为受 governance/utility/tier 约束的 activation、ranking hint 和 audit；最终 evidence 仍回到 raw Memory rows。 |
| LongMemEval-S full | strict/lenient `0.832000 / 0.844000`，`416/500` strict，`422/500` lenient；avg build/query tokens `85393.566 / 6463.04` |
| LoCoMo non-adversarial full | strict/lenient `0.794156 / 0.819481`，`1223/1540` strict，`1262/1540` lenient；avg build/query tokens `62015.57402597403 / 6093.8493506493505` |
| LTS 理由 | v276 相对 v275：LME/LoCoMo full answer、prompt、route、evidence、retrieval、token 全部 `0` diff，answer cache `2040/0`；build graph `tier_manifest` 和 `source_policy` 均覆盖 `2040/2040`。它把 memory tier/lifecycle 作为 build memory system 的显式状态，性能主指标不退，同时减少 typed memory 过浅和 query-side scattered policy 风险。 |
| 主要局限 | v276 仍是结构性小步，不是直接提分；query stack 仍有 route/selected-context/state-guide/ledger/audit 兼容层；LME query tokens 仍略高于 6K 目标但低于 8K hard diagnostic 线，LoCoMo 也略高于 6K 目标。 |

v276 关键证据见 `experiments/diagnostic/stage1_memory_tier_manifest_v276_full_summary.md`。如果论文级最终汇报需要 fresh full judge，再对最终 LTS 配置完整重跑 dual judge；日常迭代优先用 full diff + changed-answer paired judge，避免无意义重跑。

## 口径

- 主线目标是通用、clean、可消融、可持续迭代、且有方法创新性的 Agent Memory system/library，不是围绕 LongMemEval/LoCoMo 手写补丁。
- 方法性能主要看 DeepSeek dual `deepseek-v4-flash` judge accuracy：strict 为两遍都判对，lenient 为任一遍判对；Exact/F1/BLEU 只作参考。
- 新 LTS 优先看 clean/general/system 风险是否减少；性能提升是强加分项，但不是唯一前提。若风险明显减少且性能不退，可以升 LTS；若小幅回退但显著降低 design-for-benchmark 或系统风险，需要明确记录 tradeoff 后再判断。
- 每个算法版本先做本地 git commit；正式实验记录引用 commit、配置、token 成本、outputs 路径和 judge 路径。GitHub 只在用户明确要求时 push。
- 普通诊断不需要反复重跑 full；若只影响少量预测，优先做 changed-answer paired judge。不要为了 manifest clean 或形式完整重复重跑未变化样本。

## 优先待办

| 优先级 | 方向 | 下一步 |
|---:|---|---|
| 1 | Build memory system | 在 v276 tier/source policy 基础上继续做 build-owned consolidation、conflict clustering、working-memory activation，不写 benchmark 规则。 |
| 2 | Query-time 简化 | 收敛为 candidate activation、context compiler、source-grounded answer、consistency verifier 四层；把能前移的判断前移到 build/management。 |
| 3 | Evidence utility | 用 build-stage utility/role 替代简单 overflow 或固定 top-k，增加 source pressure、same-slot coverage、temporal validity 和 utility ablation。 |
| 4 | Answer/verifier | 把 audit 推进为通用 consistency verifier：检查数值、时间、说话人、实体、状态冲突和 unsupported answer，不写 benchmark-specific rewrite。 |
| 5 | src cleanup | 每阶段小范围清理 `src/`，只删除已确认无用且不影响复现/消融的代码。 |

## 当前候选和近期结论

| 配置/文档 | 类型 | 关键结果 | 决策 |
|---|---|---|---|
| `configs/stage1_memory_tier_manifest_v276_seeded_qwen36_no_think_build4k_cached.json` / `diagnostic/stage1_memory_tier_manifest_v276_full_summary.md` | current LTS | v276 vs v275 full answer/prompt/route/evidence/retrieval/token diff `0`；tier_manifest seen LME `500/500`、LoCoMo `1540/1540`；answer cache `2040/0` | 升 LTS；把 working/long-term/archival/quarantine tier 纳入 build memory system，性能主指标不退 |
| `configs/stage1_build_slot_source_policy_v275_seeded_qwen36_no_think_build4k_cached.json` / `diagnostic/stage1_build_slot_source_policy_v275_full_summary.md` | previous LTS | v275 vs v274 full answer/prompt/route/evidence/retrieval/token diff `0`；source_policy seen LME `500/500`、LoCoMo `1540/1540` | 被 v276 继承；把 validity-aware source ordering 收敛到 build memory system |
| `configs/stage1_validity_aware_graph_utility_v274_seeded_qwen36_no_think_build4k_cached.json` / `diagnostic/stage1_validity_aware_graph_utility_v274_full_summary.md` | previous LTS | LME changed answers `1/500`，changed-answer dual judge delta strict/lenient `0/0`；LoCoMo answer diff `0/1540` | 被 v275/v276 继承；validity/source-confidence 参与 graph utility source selection |
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
