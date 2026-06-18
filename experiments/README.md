# 实验入口

`experiments/` 是正式结果和关键诊断的人类可读入口。各 run 目录保留 `summary.md`、`diagnosis.md`、`metrics.json`、`manifest.json` 和配置快照；本文件只维护稳定索引、当前决策和少量会影响下一步的结论。

## 当前 LTS

| 项目 | 结果 |
|---|---|
| 当前 LTS 配置 | `configs/stage1_memory_lifecycle_manifest_v162_qwen36_no_think_build4k_cached.json` |
| Backbone | `Qwen/Qwen3.6-35B-A3B` answer/build，`chat_template_kwargs.enable_thinking=false` |
| 方法 | V162 trace-only memory lifecycle manifest：继承 v158 的预测行为，新增 build memory 与 activated memory 的 source-backed slot/conflict/visibility/query-overlap 审计。 |
| LongMemEval-S full | v162 与 v158 answer diff `0/500`，继承 dual judge strict/lenient `0.822000 / 0.834000`；`411/500` strict，`417/500` lenient |
| LoCoMo non-adversarial full | v162 与 v158 answer diff `0/1540`，继承 dual judge strict/lenient `0.789610 / 0.815584`；`1216/1540` strict，`1256/1540` lenient |
| 状态 | 当前本地 qwen3.6 no-thinking LTS。相对 v158，v162 不改变 prediction，降低 #5 lifecycle/conflict/query activation 的可诊断和治理风险；#1 granularity/profile、#2 top-k/context noise/rerank、以及把 #5 manifest 安全转成预测收益仍未解决。 |

`paired-delta derived` 的含义：新版本只改少量答案，未变化答案沿用父 LTS full dual judge records，变化答案单独跑 paired dual judge 后替换计数。若新版本与父 LTS answer-identical，则可继承父 LTS judge records，但必须记录 full answer diff、cache hit/miss 和输出路径。若论文级最终汇报需要完全独立 run，再对 LTS 配置重跑 fresh full judge。

## 口径说明

- `exact / F1 / BLEU` 只作为低成本诊断和 badcase 定位；是否升级 LTS 只看 dual `deepseek-v4-flash` judge strict/lenient accuracy。
- 新 LTS 优先看 clean/general 风险是否相对当前 LTS 或直接父对照减少；任一/若干项风险实质下降即可升级，但必须显式记录未解决项。性能提升是强加分项，不是唯一前提；性能下降则不能升 LTS。
- 如果改动只影响少量预测，优先做 changed-answer paired judge；不要为了 manifest clean 或形式完整重复重跑未变化样本。
- `v101` 及之前默认属于 `Qwen/Qwen3-30B-A3B-Instruct-2507` 历史探索；当前主线只看显式带 `qwen36_no_think_build4k` 的记录。

## 优先待办

| 优先级 | 项目 | 当前状态 | 下一步 |
|---:|---|---|---|
| 1 | #5 memory lifecycle/state/conflict/query-time reasoning | v154 已把 source-backed lifecycle ledger 放进窄 current-state repair；v162 新增 trace-only build/activated lifecycle manifest；v163 profile activation guide 因过度 abstain 失败；v164 profile repair 因触发过宽失败；v165 表面拒答限定后 no-op | 用 v162 manifest 切 badcase，优先做 answer-slot-aware verifier / lifecycle activation；profile/advice 下一步转向 evidence coverage，而不是继续调 repair prompt |
| 2 | #2 top-k/context noise/rerank | v129/v134/v140/v152 说明简单裁剪、tail snippet 或 list-count rerank pruning 会伤 accuracy；当前 query context 仍偏长 | 转向 coverage-preserving route-aware context organization：先保留覆盖证据，再做 grouping/dedup/aggregation table |
| 3 | #1 granularity/profile + #3 selected context | v158 已把 long-turn selected context 从一刀切禁用改成 narrow question-gated policy；granularity profile 仍基于 avg-turn chars | 继续重做更通用的 context organization，逐步减少 avg-turn profile 依赖 |
| 4 | src cleanup | 已有多轮兼容分支，`repair.py`、compiler、pipeline 仍会继续变复杂 | 每个阶段结束后做小范围清理，删已确认无用的兼容代码，不删仍有消融价值的模块 |

## 保留候选

| 配置/文档 | 类型 | 关键结果 | 决策 |
|---|---|---|---|
| `configs/stage1_memory_lifecycle_manifest_v162_qwen36_no_think_build4k_cached.json` | current LTS | LME strict/lenient `0.822000/0.834000`，LoCoMo `0.789610/0.815584`；v162 vs v158 answer diff `0/500`、`0/1540` | 当前 LTS；比 v158 降低 #5 lifecycle/conflict/query activation 的可诊断和治理风险且 accuracy 不降 |
| `configs/stage1_narrow_question_gated_selected_context_v158_qwen36_no_think_build4k_cached.json` | previous LTS | LME strict/lenient `0.822000/0.834000`，LoCoMo `0.789610/0.815584`；v158 vs v154 changed-answer paired judge 持平 | 被 v162 替代；仍是 #3 long-turn selected-context blanket-disable 风险收敛证据 |
| `configs/stage1_current_state_lifecycle_ledger_v154_qwen36_no_think_build4k_cached.json` | previous LTS | LME strict/lenient `0.822000/0.834000`，LoCoMo `0.789610/0.815584`；changed-answer paired judge vs v151 持平 | 被 v158 替代；仍是 #5 lifecycle ledger 父对照 |
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
| `stage1_surface_profile_advice_repair_v165_qwen36_no_think_build4k_cached.json` | 修复 v164 过宽触发，LME profile answer diff `0/15`，但触发 `4` 次 repair、增加 `18061` repair query tokens 且无收益；不升 LTS。 |
| `stage1_profile_advice_abstention_repair_v164_qwen36_no_think_build4k_cached.json` | clean 的 profile/advice abstention repair 触发过宽，错误修掉一条原本正确的 LME profile answer；changed subset strict/lenient `1/1 -> 0/1`、`1/1 -> 0/1`，不升 LTS。 |
| `stage1_profile_memory_activation_v163_qwen36_no_think_build4k_cached.json` | clean 的 profile memory activation guide 只使用可见 source-backed typed memory，但 LME profile changed subset strict/lenient `3/9 -> 2/9`、`4/9 -> 3/9`；主要失败是把 source-grounding 变成过度 abstain，不升 LTS。 |
| `stage1_current_state_only_conflict_guide_v161_qwen36_no_think_build4k_cached.json` | 移除 fact_lookup 上过宽 conflict guide，query/context 降低且 row set 不变，但 LME fact changed subset strict `23/39 -> 22/39`，lenient 持平；不升 LTS。 |
| `stage1_fixed_set_fact_source_interleave_v160_qwen36_no_think_build4k_cached.json` | 修复 v159 evidence-set drift，final row set changed `0/183`，但 LME fact changed subset strict `28/49 -> 27/49`，lenient 持平；不升 LTS。 |
| `stage1_fact_source_interleave_v159_qwen36_no_think_build4k_cached.json` | source-backed fact row ordering clean 但过宽；LME fact changed subset strict/lenient `28/46 -> 26/46`、`30/46 -> 28/46`，且 ordering-before-truncation 导致 final row set changed `24/183`。 |
| `stage1_question_gated_selected_context_v157_qwen36_no_think_build4k_cached.json` | question-level gate 明显收窄 v156 触发面，但 LME changed subset strict `3/5 -> 2/5`、lenient `4/5 -> 4/5`；bare `that` 误触发，需继续收窄。 |
| `stage1_long_profile_route_selected_context_v156_qwen36_no_think_build4k_cached.json` | 结构上比长 turn 一刀切禁用更 clean，但 LME changed-answer paired judge 负向：strict `11/17 -> 7/17`，lenient `12/17 -> 7/17`；下一步需要 question-level local-reference gate。 |
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
| `diagnostic/stage1_surface_profile_advice_repair_v165_scope_summary.md` | v165 no-op 诊断：表面拒答限定修复 v164 误修，但 LME profile answer diff `0/15` 且增加 repair cost |
| `diagnostic/stage1_surface_profile_advice_repair_v165_lme_changed_vs_v162/metrics.json` | v165 vs v162 LME profile answer diff 指标快照 |
| `diagnostic/stage1_surface_profile_advice_repair_v165_lme_profile_preference/` | v165 LME profile-preference diagnostic run artifacts |
| `diagnostic/stage1_profile_advice_abstention_repair_v164_scope_summary.md` | v164 负向诊断：profile/advice repair 误修正确答案，LME profile changed subset strict/lenient `-1/-1` |
| `diagnostic/stage1_profile_advice_abstention_repair_v164_lme_changed_vs_v162/metrics.json` | v164 vs v162 LME profile changed-answer paired dual judge 指标快照 |
| `diagnostic/stage1_profile_advice_abstention_repair_v164_lme_profile_preference/` | v164 LME profile-preference diagnostic run artifacts |
| `diagnostic/stage1_profile_memory_activation_v163_scope_summary.md` | v163 负向诊断：source-backed profile activation guide 导致 LME profile changed subset strict/lenient `-1/-1`，不升 LTS |
| `diagnostic/stage1_profile_memory_activation_v163_lme_changed_vs_v162/metrics.json` | v163 vs v162 LME profile changed-answer paired dual judge 指标快照 |
| `diagnostic/stage1_profile_memory_activation_v163_lme_profile_preference/` | v163 LME profile-preference diagnostic run artifacts |
| `diagnostic/stage1_memory_lifecycle_manifest_v162_scope_summary.md` | v162 LTS 晋升：trace-only lifecycle manifest，LME/LoCoMo answer diff 均为 0，性能继承 v158 |
| `diagnostic/stage1_memory_lifecycle_manifest_v162_lme_s_full/` | v162 LME full cached trace run artifacts |
| `diagnostic/stage1_memory_lifecycle_manifest_v162_locomo_nonadv_full/` | v162 LoCoMo full cached trace run artifacts |
| `diagnostic/stage1_narrow_question_gated_selected_context_v158_scope_summary.md` | v158 LTS 晋升：narrow question-gated selected context，LME answer diff `2/500` 且 paired judge 持平，LoCoMo diff `0/1540` |
| `diagnostic/stage1_narrow_question_gated_selected_context_v158_lme_s_full/` | v158 LME full cached prediction run artifacts |
| `diagnostic/stage1_narrow_question_gated_selected_context_v158_locomo_nonadv_full/` | v158 LoCoMo full cached prediction run artifacts |
| `diagnostic/stage1_current_state_only_conflict_guide_v161_scope_summary.md` | v161 负向诊断：fact conflict guide 移除降成本但 LME changed subset strict `-1` |
| `diagnostic/stage1_fixed_set_fact_source_interleave_v160_scope_summary.md` | v160 负向诊断：fixed-set source-backed fact ordering 保住 evidence set，但 LME changed subset strict `-1` |
| `diagnostic/stage1_fact_source_interleave_v159_scope_summary.md` | v159 负向诊断：fact_lookup source-backed interleave 改变 final evidence set，LME changed subset strict/lenient `-2/-2` |
| `diagnostic/stage1_question_gated_selected_context_v157_scope_summary.md` | v157 question-level selected-context gate 诊断：selected-context `6/500`，answer diff `5/500`，paired judge strict `-1`、lenient `0`，需收窄 bare `that` |
| `diagnostic/stage1_long_profile_route_selected_context_v156_scope_summary.md` | v156 route-scoped selected-context 负向诊断：answer diff `17/500`，paired judge strict/lenient `-4/-5`，下一步转 question-level gate |
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
