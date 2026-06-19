# 实验入口

`experiments/` 是正式结果和关键诊断的人类可读入口。各 run 目录保留 `summary.md`、`diagnosis.md`、`metrics.json`、`manifest.json` 和配置快照；本文件只维护当前 LTS、口径、优先待办、近期候选和必要历史锚点。长历史细节回到对应 scope summary、run 目录和 git。

## 当前 LTS

| 项目 | 结果 |
|---|---|
| 当前 LTS 配置 | `configs/stage1_memory_system_graph_v261_seeded_qwen36_no_think_build4k_cached.json` |
| Backbone | `Qwen/Qwen3.6-35B-A3B` answer/build，`chat_template_kwargs.enable_thinking=false` |
| 方法定位 | build-time source-backed memory management + memory system graph + operation ledger + lifecycle operation utility + build-slot inventory + object-slot tail-rescue activation + query-time no-repair/no-finalizer + trace-only source-grounded answer support audit。Typed memory 只做 source-backed operation index / activation；最终 evidence 回到 raw Memory rows；memory system graph 只做 trace/metrics，不改预测。 |
| LongMemEval-S full | strict/lenient `0.832000 / 0.844000`，`416/500` strict，`422/500` lenient；avg build/query tokens `85393.566 / 6579.782` |
| LoCoMo non-adversarial full | strict/lenient `0.794156 / 0.819481`，`1223/1540` strict，`1262/1540` lenient；avg build/query tokens `62015.57402597403 / 6094.017532467533` |
| LTS 理由 | v261 vs v260 full LME/LoCoMo answer、retrieval、final-evidence 和 token diff 均为 `0`，继承 v260 accuracy；memory system graph 覆盖 LME `500/500`、LoCoMo `1540/1540`，记录 namespaces、lifecycle states、source-support / merge / supersede / slot edges。 |
| 主要局限 | v261 仍是 trace/governance 版本，不是 accuracy peak；下一步要让 graph 支持 general evidence utility selection，并继续收敛 query-time route/guide/repair/finalizer 兼容面。 |

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
| 1 | Evidence utility selection | v261 已有 trace-only memory system graph，但 graph 还不参与 candidate/evidence selection | 设计 general candidate pooling + utility scoring + anchor retention + source expansion；先 additive/append-only，再验证 replacement gate |
| 2 | Build memory system | v261 已记录 memory objects、namespaces、lifecycle states 和 operation edges，但 memory object schema 还偏 typed-record 后处理 | 继续把 event/state/profile/relation object schema 标准化，加入 confidence、validity、source span、usage utility 的可消融字段 |
| 3 | Query-time 简化 | route、selected context、state guide、ledger、audit 多层叠加，后续维护成本高 | 收敛为 candidate activation、context compiler、source-grounded answer、consistency verifier 四层，删除确认无用的兼容分支 |
| 4 | Answer/verifier 统一 | source-grounded support audit 仍是 trace-only；repair/finalizer 默认关闭后还残留兼容面 | 基于 audit 风险做通用 verifier，只检查数值、时间、说话人、实体、状态冲突、unsupported answer，不写 benchmark-specific rewrite |
| 5 | src cleanup | `pipeline.py`、compiler、repair/finalizer 兼容分支较多，后续改法成本上升 | 每个阶段做小范围清理，删除已确认无用的兼容代码；保留仍有消融价值和复现价值的模块 |

## 当前候选和近期结论

| 配置/文档 | 类型 | 关键结果 | 决策 |
|---|---|---|---|
| `configs/stage1_memory_system_graph_v261_seeded_qwen36_no_think_build4k_cached.json` / `diagnostic/stage1_memory_system_graph_v261_full_summary.md` | current LTS / memory system graph | v261 vs v260 full LME/LoCoMo answer/hits/final-evidence/token diff 全为 `0`; full accuracy 继承 `0.832000/0.844000`、`0.794156/0.819481`; graph applied LME `500/500`、LoCoMo `1540/1540` | 当前 LTS；build memory 从 typed records + ledger 推进为 trace-only source-backed system graph |
| `configs/stage1_lifecycle_operation_utility_tail_rescue_v260_seeded_qwen36_no_think_build4k_cached.json` / `diagnostic/stage1_lifecycle_operation_utility_tail_rescue_v260_full_summary.md` | previous LTS / lifecycle operation utility | v260 vs v257 full answer/hits/final-evidence/token diff 全为 `0`; operation utility applied LME `14/500`、LoCoMo `22/1540` | 被 v261 替代；保留为 append-only operation utility 父锚点 |
| `configs/stage1_lifecycle_operation_utility_v259_seeded_qwen36_no_think_build4k_cached.json` | rejected full / lifecycle tail-exchange lesson | LME answer diff `4/500`，changed lenient loss `1`; LoCoMo answer diff `10/1540`，changed strict/lenient loss `2/2` | 不升 LTS；`tail_exchange` 即使只替换 1 条 evidence 仍会伤害 accuracy |
| `configs/stage1_operation_utility_tail_exchange_v258_seeded_qwen36_no_think_build4k_cached.json` | rejected probe / collection operation lesson | seeded LoCoMo probe changed subset lenient `9/10 -> 8/10`; collection/list slot 噪声影响答案 | 不升 LTS；collection_multi_value_slot 不能作为强 evidence replacement 信号 |
| `configs/stage1_build_operation_ledger_v257_seeded_qwen36_no_think_build4k_cached.json` / `diagnostic/stage1_build_operation_ledger_v257_full_summary.md` | previous LTS / build operation ledger | v257 vs v256 full answer/retrieval/final-evidence/token diff 全为 `0`; operation ledger full 覆盖，source-unbacked records 为 `0` | 被 v260 替代；保留为 build operation ledger 父锚点 |
| v250-v256 source-backed audit/object-slot/build-slot line | previous LTS anchors | object-slot tail-rescue、build-slot inventory、answer support audit 都以 answer-identical 或 changed-answer safe 的方式降低风险 | 被 v257/v260 继承；详细见对应 full summary |
| v216-v254 rejected context/retrieval/prompt/object-slot lines | historical lessons | hard gate、prompt-side operation guide、wide selected context、tail-exchange replacement 多次造成 changed-answer 回退 | 不再逐版展开；详细历史见对应 scope summary 和 git |
| `formal/stage1_superseded_source_chain_v127_lme_s_full_fresh/` 和 `formal/stage1_superseded_source_chain_v127_locomo_nonadv_full_fresh/` | fresh full parent records | v127 fresh full dual judge parent records | 保留为早期 source-backed update organization 基线 |

## 负向教训索引

这些记录不再放进主叙事，但仍保留为避免重复踩坑的索引：

| 文档/目录 | 教训 |
|---|---|
| `diagnostic/stage1_lifecycle_operation_utility_v259_*_changed_vs_v257/` | lifecycle/source-backed operation utility 可以 clean，但不应替换高置信 evidence；优先 append-only 或 stronger utility gate |
| `diagnostic/stage1_operation_utility_tail_exchange_v258_locomo_probe50_seeded_changed_vs_v257/` | collection/list operation slot 噪声高，不能直接进入 tail-exchange |
| `diagnostic/stage1_profile_aware_gated_fact_list_rerank_v228_scope_summary.md` | profile-aware gated fact/list rerank clean，但 LoCoMo changed judge `-1/-5` |
| `diagnostic/stage1_route_tail_cap56_v223_scope_summary.md` | route-scoped final evidence cap 降 token 但 changed judge 明显回退 |
| `diagnostic/stage1_temporal_materialized_context_source_gate_v219_scope_summary.md` 和 `diagnostic/stage1_materialized_context_source_gate_v218_scope_summary.md` | selected-context hard gate 降 token / risk，但 answer regression 明显 |
| `diagnostic/stage1_event_timeline_context_v179_scope_summary.md` 和 `diagnostic/stage1_candidate_evidence_map_v192_probe_summary.md` | prompt block / wide evidence map 容易增 token 或挤掉关键 row |

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
