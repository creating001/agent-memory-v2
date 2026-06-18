# 实验入口

`experiments/` 是正式结果和关键诊断的人类可读入口。各 run 目录保留 `summary.md`、`diagnosis.md`、`metrics.json`、`manifest.json` 和配置快照；本文件只维护稳定索引、当前决策和少量会影响下一步的结论。

## 当前 LTS

| 项目 | 结果 |
|---|---|
| 当前 LTS 配置 | `configs/stage1_current_state_lifecycle_ledger_v154_qwen36_no_think_build4k_cached.json` |
| Backbone | `Qwen/Qwen3.6-35B-A3B` answer/build，`chat_template_kwargs.enable_thinking=false` |
| 方法 | V154 current-state lifecycle ledger：继承 v151 的窄 current-state source repair，在 repair prompt 内加入 source-backed lifecycle ledger；ledger 只索引同一份 raw Memory Context，不作为二手 evidence。 |
| LongMemEval-S full | paired-delta derived dual judge strict/lenient `0.822000 / 0.834000`；`411/500` strict，`417/500` lenient |
| LoCoMo non-adversarial full | v154 与 v151 answer-normalized 等价，strict/lenient `0.789610 / 0.815584`；`1216/1540` strict，`1256/1540` lenient |
| 状态 | 当前本地 qwen3.6 no-thinking LTS。相对 v151，v154 不扩大触发面、不降 accuracy，并降低 #5 lifecycle/update reasoning 的可审计性风险；#1 granularity/profile、#2 top-k/context noise/rerank、更完整的 #5 memory management 仍未解决。 |

`paired-delta derived` 的含义：v154 预测与 v151 只有少量答案变化，未变化答案沿用 v151/v127 full dual judge records，变化答案单独跑 paired dual judge 后替换计数。若论文级最终汇报需要完全独立 run，再对 LTS 配置重跑 fresh full judge。

## 口径说明

- `exact / F1 / BLEU` 只作为低成本诊断和 badcase 定位；是否升级 LTS 只看 dual `deepseek-v4-flash` judge strict/lenient accuracy。
- 新 LTS 优先看 clean/general 风险是否相对当前 LTS 或直接父对照减少；任一/若干项风险实质下降即可升级，但必须显式记录未解决项。性能提升是强加分项，不是唯一前提；性能下降则不能升 LTS。
- 如果改动只影响少量预测，优先做 changed-answer paired judge；不要为了 manifest clean 或形式完整重复重跑未变化样本。
- `v101` 及之前默认属于 `Qwen/Qwen3-30B-A3B-Instruct-2507` 历史探索；当前主线只看显式带 `qwen36_no_think_build4k` 的记录。

## 优先待办

| 优先级 | 项目 | 当前状态 | 下一步 |
|---:|---|---|---|
| 1 | #5 memory lifecycle/state/conflict/query-time reasoning | v154 已把 source-backed lifecycle ledger 放进窄 current-state repair；typed memory 仍不直接替代 raw evidence | 继续做 answer-slot-aware verifier / lifecycle ledger，逐步扩到更多可安全识别的 state/update 槽位 |
| 2 | #2 top-k/context noise/rerank | v129/v134/v140/v152 说明简单裁剪、tail snippet 或 list-count rerank pruning 会伤 accuracy；当前 query context 仍偏长 | 转向 coverage-preserving route-aware context organization：先保留覆盖证据，再做 grouping/dedup/aggregation table |
| 3 | #1 granularity/profile + #3 selected context | v128/v140 表明长短 turn/profile 分支仍有 generalization 风险 | 重做更通用的 context organization，避免 benchmark profile 或长短 turn 硬分支 |
| 4 | src cleanup | 已有多轮兼容分支，`repair.py`、compiler、pipeline 仍会继续变复杂 | 每个阶段结束后做小范围清理，删已确认无用的兼容代码，不删仍有消融价值的模块 |

## 保留候选

| 配置/文档 | 类型 | 关键结果 | 决策 |
|---|---|---|---|
| `configs/stage1_current_state_lifecycle_ledger_v154_qwen36_no_think_build4k_cached.json` | current LTS | LME strict/lenient `0.822000/0.834000`，LoCoMo `0.789610/0.815584`；changed-answer paired judge vs v151 持平 | 当前 LTS；比 v151 增加 source-backed lifecycle ledger，风险更低且 accuracy 不降 |
| `configs/stage1_current_state_source_repair_v151_qwen36_no_think_build4k_cached.json` | previous LTS | LME strict/lenient `0.822000/0.834000`，LoCoMo `0.789610/0.815584`；changed-answer paired judge vs v150 正向/持平 | 被 v154 替代；仍是窄 source repair 父对照 |
| `configs/stage1_selective_source_repair_v150_qwen36_no_think_build4k_cached.json` | previous LTS | LME strict/lenient `0.820000/0.834000`，LoCoMo `0.789610/0.815584` | 被 v151 替代：profile repair 过度改写一条 LME recommendation，v151 移除该风险并提升 LME strict |
| `configs/stage1_superseded_source_chain_v127_qwen36_no_think_build4k_cached.json` | previous LTS | fresh full dual judge：LME `0.820000/0.832000`，LoCoMo `0.789610/0.815584` | 被 v150/v151 替代；仍是 source-backed update organization 父对照 |
| `configs/stage1_route_scoped_local_evidence_unit_v125_qwen36_no_think_build4k_cached.json` | previous LTS | LoCoMo temporal paired dual judge 正向；LME 兼容继承 v116 | 被 v127/v150 替代；保留为 #3/#4 风险收敛证据 |
| `configs/stage1_route_scoped_fact_profile_state_budget_v129_qwen36_no_think_build4k_cached.json` | token-budget | route-only exact 略正向但 judge 证据不足 | 作为成本方向父对照，不是 LTS |
| `configs/stage1_memory_source_interleave_v126_qwen36_no_think_build4k_cached.json` | memory organization | LoCoMo profile/current paired dual `+4/+4`，LME `-1/-1` | 被 v127 继承和修正；保留为 ablation |
| `configs/stage1_source_grounded_guard_v121_qwen36_no_think_build4k_cached.json` | clean/general cleanup | 收窄 broad mechanical finalizer 为 source-grounded consistency guard | 保留为 #4 风险收敛证据 |
| `diagnostic/stage1_build_memory_usage_trace_audit_v126_plan.md` | memory audit | v116 LoCoMo `1539/1540` 有 memory hits 且有 memory-projected source 进入最终 rows | 说明瓶颈是 source-backed organization/reasoning，不是完全没用 memory |

## 拒绝记录

这里只保留会影响下一步设计的负向结论；完整历史可从 git 和对应 run 目录追溯。

| 配置 | 原因 |
|---|---|
| `stage1_answer_slot_checklist_v149_qwen36_no_think_build4k_cached.json` | broad checklist 在 LME changed subset 明显负向：strict/lenient `13/21 -> 9/21`、`13/21 -> 10/21`；v150 已改成窄触发 verifier。 |
| `stage1_current_state_lifecycle_slot_trigger_v155_qwen36_no_think_build4k_cached.json` | 触发门比 v154 更窄但额外 verifier 没有改变任何答案，LME/LoCoMo answer diff 均为 0，同时增加 query tokens；不升 LTS。 |
| `stage1_current_state_update_contract_v153_qwen36_no_think_build4k_cached.json` | prompt-only current-state update discipline 在 LME changed subset 明显负向：strict/lenient `9/10 -> 5/10`，LoCoMo 持平；不升 LTS。 |
| `stage1_list_count_rerank_filter_v152_qwen36_no_think_build4k_cached.json` | list/count tail rerank 降 query token 但 LME changed subset `10/15 -> 9/15` strict、LoCoMo `75/120 -> 69/120` strict，且新增大量 rerank token。 |
| `stage1_scoped_version_chain_interleave_v148_qwen36_no_think_build4k_cached.json` | source-backed scoped row ordering scope clean，但 LME changed subset `5/10 -> 4/10` strict、`6/10 -> 4/10` lenient。 |
| `stage1_temporal_scope_priority_v147_qwen36_no_think_build4k_cached.json` | 全局 temporal priority 伤 current-state/list 证据选择；LME changed subset `5/6 -> 3/6`。 |
| `stage1_scoped_state_source_activation_v146_qwen36_no_think_build4k_cached.json` | 更 clean 但相对 v127 基本 no-op，不升 LTS。 |
| `stage1_memory_slot_chain_v145_qwen36_no_think_build4k_cached.json` | retrieval-time slot-chain 方向 clean，但 LME/LoCoMo full dual judge 均低于 v127。 |
| `stage1_memory_version_chain_v144_qwen36_no_think_build4k_cached.json` | LME mixed、LoCoMo 低于 v127；保留为 #5 state/version ablation。 |
| `stage1_scoped_memory_state_guide_v142_qwen36_no_think_build4k_cached.json` | LME mixed、LoCoMo 负向；提示 #5 不能只加宽 state guide。 |
| `stage1_route_gated_context_pressure_v140_qwen36_no_think_build4k_cached.json` | 虽降低 context chars，但 LME strict/lenient 仍低于 v127。 |
| `stage1_fact_tail_snippet_budget_v134_qwen36_no_think_build4k_cached.json` | token 降低但 LoCoMo fact paired dual judge 负向。 |
| `stage1_fact_tail_filter_preserve_order_v132_qwen36_no_think_build4k_cached.json` | hard row pruning 降 token 但 exact/F1/BLEU 下滑，未进入 judge 候选。 |

## 关键路径

| 路径 | 内容 |
|---|---|
| `diagnostic/stage1_current_state_lifecycle_slot_trigger_v155_scope_summary.md` | v155 lifecycle-slot trigger 诊断：answer diff 0 但 token 增加，不升 LTS |
| `diagnostic/stage1_current_state_lifecycle_ledger_v154_scope_summary.md` | v154 LTS 晋升、changed-answer judge、坏 run 教训和 #5 风险结论 |
| `diagnostic/stage1_current_state_lifecycle_ledger_v154_lme_s_full_r3/` | v154 LME full cached prediction run artifacts |
| `diagnostic/stage1_current_state_lifecycle_ledger_v154_locomo_nonadv_full_r3/` | v154 LoCoMo full cached prediction run artifacts |
| `diagnostic/stage1_current_state_update_contract_v153_scope_summary.md` | v153 current-state prompt-only discipline 负向结论和 #5 下一步 |
| `diagnostic/stage1_list_count_rerank_filter_v152_scope_summary.md` | v152 list-count rerank-filter 负向结论和 #2 下一步 |
| `diagnostic/stage1_current_state_source_repair_v151_scope_summary.md` | v151 LTS 晋升、changed-answer judge、badcase 和风险结论 |
| `diagnostic/stage1_current_state_source_repair_v151_lme_s_full/` | v151 LME full cached prediction run artifacts |
| `diagnostic/stage1_current_state_source_repair_v151_locomo_nonadv_full/` | v151 LoCoMo full cached prediction run artifacts |
| `diagnostic/stage1_current_state_source_repair_v151_lme_changed_vs_v150/` | LME v151 vs v150 changed-answer paired dual judge |
| `diagnostic/stage1_current_state_source_repair_v151_locomo_changed_vs_v150/` | LoCoMo v151 vs v150 changed-answer paired dual judge |
| `diagnostic/stage1_selective_source_repair_v150_scope_summary.md` | v150 LTS 晋升、changed-answer judge、badcase 和风险结论 |
| `diagnostic/stage1_selective_source_repair_v150_lme_s_full/` | v150 LME full cached prediction run artifacts |
| `diagnostic/stage1_selective_source_repair_v150_locomo_nonadv_full/` | v150 LoCoMo full cached prediction run artifacts |
| `diagnostic/stage1_selective_source_repair_v150_lme_changed_answers/` | LME changed-answer paired dual judge |
| `diagnostic/stage1_selective_source_repair_v150_locomo_changed_answers/` | LoCoMo changed-answer paired dual judge |
| `formal/stage1_superseded_source_chain_v127_lme_s_full_fresh/` | v127 fresh full dual judge parent records |
| `formal/stage1_superseded_source_chain_v127_locomo_nonadv_full_fresh/` | v127 fresh full dual judge parent records |

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
