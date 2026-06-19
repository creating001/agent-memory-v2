# 实验入口

`experiments/` 是正式结果和关键诊断的人类可读入口。各 run 目录保留 `summary.md`、`diagnosis.md`、`metrics.json`、`manifest.json` 和配置快照；本文件只维护稳定索引、当前决策和少量会影响下一步的结论。

## 当前 LTS

| 项目 | 结果 |
|---|---|
| 当前 LTS 配置 | `configs/stage1_strict_event_time_candidate_map_v184_seeded_qwen36_no_think_build4k_cached.json` |
| Backbone | `Qwen/Qwen3.6-35B-A3B` answer/build，`chat_template_kwargs.enable_thinking=false` |
| 方法 | V184 strict event-time candidate map：继承 v181 grouped event-time management view，并新增很窄的 prompt-side source-backed event-date activation；剥离 selected-context wrapper 时间，只允许 `exact_today` / explicit date 候选，禁用 time-of-day question activation。 |
| LongMemEval-S full | v184 与 v181 answer diff `0/500`，map applied `0/500`，answer cache `500/0/0`；继承 v181 full `0.834000 / 0.846000`，`417/500` strict，`423/500` lenient |
| LoCoMo non-adversarial full | v184 与 v181 answer diff `2/1540`，map applied `3/1540`，answer cache `1538/2/2`；changed-answer dual judge `1/2 -> 2/2`，derived full `0.793506 / 0.818831`，`1222/1540` strict，`1261/1540` lenient |
| 状态 | 当前本地 qwen3.6 no-thinking LTS。v184 在不改变 LME 的前提下提升 LoCoMo `+1/+1`，并降低 #5 query-time activation 风险；残余风险是 `exact_today` map 仍可能语义噪声，下一步继续收窄 activation 或要求更强 slot/action coverage。 |

`paired-delta derived` 的含义：新版本只改少量答案，未变化答案沿用父 LTS full dual judge records，变化答案单独跑 paired dual judge 后替换计数。若新版本与父 LTS answer-identical，则可继承父 LTS judge records，但必须记录 full answer diff、cache hit/miss 和输出路径。若论文级最终汇报需要完全独立 run，再对 LTS 配置重跑 fresh full judge。

## 口径说明

- `exact / F1 / BLEU` 只作为低成本诊断和 badcase 定位；是否升级 LTS 只看 dual `deepseek-v4-flash` judge strict/lenient accuracy。
- 新 LTS 优先看 clean/general 风险是否相对当前 LTS 或直接父对照减少；任一/若干项风险实质下降即可升级，但必须显式记录未解决项。性能提升是强加分项，不是唯一前提；性能下降则不能升 LTS。
- 如果改动只影响少量预测，优先做 changed-answer paired judge；不要为了 manifest clean 或形式完整重复重跑未变化样本。
- `v101` 及之前默认属于 `Qwen/Qwen3-30B-A3B-Instruct-2507` 历史探索；当前主线只看显式带 `qwen36_no_think_build4k` 的记录。

## 优先待办

| 优先级 | 项目 | 当前状态 | 下一步 |
|---:|---|---|---|
| 1 | #5 memory lifecycle/state/conflict/query-time reasoning | v184 已把 v181 grouped candidate management view 的一小部分接入 query-time activation，并避免 v182 的 relative/wrapper time 过强问题；但 `exact_today` 仍有 false-positive prompt-map 风险 | 继续收窄 `exact_today`：要求更强 question slot/action 覆盖，或把低置信候选退回 diagnostics-only |
| 2 | #2 top-k/context noise/rerank | v129/v134/v140/v152 说明简单裁剪、tail snippet 或 list-count rerank pruning 会伤 accuracy；当前 query context 仍偏长 | 转向 coverage-preserving route-aware context organization：先保留覆盖证据，再做 grouping/dedup/aggregation table |
| 3 | #1 granularity/profile + #3 selected context | v177 说明 row-length + center-row anaphora 的 selected-context gate 仍过宽；granularity profile 仍基于 avg-turn chars，v158 narrow question-gated policy 仍是较稳边界 | 继续重做更通用的 context organization；selected-context 不能只靠中心行 anaphora 扩邻居，优先做 question-side local reference 或 source-backed candidate map |
| 4 | src cleanup | 已有多轮兼容分支，`repair.py`、compiler、pipeline 仍会继续变复杂 | 每个阶段结束后做小范围清理，删已确认无用的兼容代码，不删仍有消融价值的模块 |

## 保留候选

| 配置/文档 | 类型 | 关键结果 | 决策 |
|---|---|---|---|
| `configs/stage1_strict_event_time_candidate_map_v184_seeded_qwen36_no_think_build4k_cached.json` | current LTS | LME strict/lenient `0.834000/0.846000`，LoCoMo `0.793506/0.818831`；v184 vs v181 answer diff `0/500`、`2/1540` | 当前 LTS；严格 prompt-side event-time candidate map 降低 #5 query-time activation 风险，LoCoMo changed-answer dual judge `1/2 -> 2/2` |
| `configs/stage1_grouped_event_time_candidate_manifest_v181_qwen36_no_think_build4k_cached.json` | previous LTS | LME strict/lenient `0.834000/0.846000`，LoCoMo `0.792857/0.818182`；v181 vs v180 answer diff `0/500`、`0/1540` | 被 v184 替代；trace-only grouped event-time manifest 降低 #5 organization/conflict audit 风险，性能继承 v180/v176 |
| `configs/stage1_trace_event_time_candidate_manifest_v180_qwen36_no_think_build4k_cached.json` | previous LTS | LME strict/lenient `0.834000/0.846000`，LoCoMo `0.792857/0.818182`；v180 vs v176 answer diff `0/500`、`0/1540` | 被 v181 替代；仍是 flat event-time manifest 父对照 |
| `configs/stage1_cross_route_profile_advice_repair_v176_qwen36_no_think_build4k_cached.json` | previous LTS | LME strict/lenient `0.834000/0.846000`，LoCoMo `0.792857/0.818182`；v176 vs v175 answer diff `2/500`、`0/1540` | 被 v180 替代；仍是 cross-route profile/advice repair 父对照，LME strict `+1`、lenient `+2` |
| `configs/stage1_temporal_operand_arithmetic_repair_v175_qwen36_no_think_build4k_cached.json` | previous LTS | LME strict/lenient `0.832000/0.842000`，LoCoMo `0.792857/0.818182`；v175 vs v173 answer diff `1/500`、`1/1540` | 被 v176 替代；仍是 temporal/age/duration query-time arithmetic reasoning 父对照 |
| `configs/stage1_source_grounded_modal_inference_repair_v173_qwen36_no_think_build4k_cached.json` | previous LTS | LME strict/lenient `0.830000/0.840000`，LoCoMo `0.792208/0.817532`；v173 vs v172 answer diff `0/500`、`2/1540` | 被 v175 替代；仍是 modal yes/no 拒答和 query-time memory reasoning 父对照 |
| `configs/stage1_profile_preference_value_guard_v172_qwen36_no_think_build4k_cached.json` | previous LTS | LME strict/lenient `0.830000/0.840000`，LoCoMo `0.790909/0.816234`；v172 vs v171 answer diff `0/500`、`1/1540` | 被 v173 替代；仍是 profile-preference value guard 父对照 |
| `configs/stage1_lifecycle_slot_specificity_guard_v171_qwen36_no_think_build4k_cached.json` | previous LTS | LME strict/lenient `0.830000/0.840000`，LoCoMo `0.790260/0.815584`；v171 vs v170 answer diff `1/500`、`0/1540` | 被 v172 替代；仍是 occupation/role lifecycle-slot specificity 父对照 |
| `configs/stage1_source_value_specificity_guard_v170_qwen36_no_think_build4k_cached.json` | previous LTS | LME strict/lenient `0.828000/0.838000`，LoCoMo `0.790260/0.815584`；v170 vs v169 answer diff `0/500`、`8/1540` | 被 v171 替代；仍是 #4 generic source value specificity 父对照 |
| `configs/stage1_numeric_slot_label_guard_v169_qwen36_no_think_build4k_cached.json` | previous LTS | LME strict/lenient `0.828000/0.838000`，LoCoMo `0.789610/0.815584`；v169 vs v168 answer diff `1/500`、`0/1540` | 被 v170 替代；仍是 #4 numeric slot label 父对照 |
| `configs/stage1_scoped_modal_profile_advice_repair_v168_qwen36_no_think_build4k_cached.json` | previous LTS | LME strict/lenient `0.826000/0.838000`，LoCoMo `0.789610/0.815584`；v168 vs v162 answer diff `2/500`、`0/1540` | 被 v169 替代；仍是 #5 profile/advice query-time memory reasoning 父对照 |
| `configs/stage1_memory_lifecycle_manifest_v162_qwen36_no_think_build4k_cached.json` | previous LTS | LME strict/lenient `0.822000/0.834000`，LoCoMo `0.789610/0.815584`；v162 vs v158 answer diff `0/500`、`0/1540` | 被 v168 替代；仍是 lifecycle/conflict/query activation manifest 父对照 |
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
| `stage1_weekend_event_time_candidate_map_v187_seeded_qwen36_no_think_build4k_cached.json` | v187 在 v186 基础上 clean 地解析 `this weekend`，并在 prompt map 中同时暴露 `mention_time`/`event_time`；但三条 v184 risky activation probe 上仍把 Nate row 回答成 `2022-08-27 to 2022-08-28`，相对当前 LTS 会丢 LoCoMo `+1/+1`，不升 LTS。 |
| `stage1_role_matched_event_time_candidate_map_v186_seeded_qwen36_no_think_build4k_cached.json` | v186 在 v184 三条 risky activation probe 上将 prompt-map 触发降到 `0/3`，风险低于 v184/v185，但答案退回 v181，其中 Nate row 从 v184 correct 退回 `2022-08-27 to 2022-08-28`；相对当前 LTS 会丢 LoCoMo `+1/+1`，不升 LTS。 |
| `stage1_segment_local_event_time_candidate_map_v185_seeded_qwen36_no_think_build4k_cached.json` | v185 用 segment-local binding、coverage-first ranking 和 exact_today 高覆盖阈值去掉两个 wrapper/nearby `today` false positives，但仍在 John/sister/dogs row 上把 James 的 dated event 放入 map；不升 LTS，v186 已用 role matching 修正。 |
| `stage1_prompt_safe_event_time_candidate_map_v182_qwen36_no_think_build4k_cached.json` | prompt-safe Event-Time Candidate Map 在 LoCoMo likely-map probe `39/40` 触发、answer diff `17/40`；changed-answer dual judge 从 v181 `17/17` strict/lenient 降到 v182 `15/17`，主要风险是 selected-context 包装时间被当成事件时间、relative/vague time 被过度推进 prompt。LME probe `0/1 -> 1/1` 不足以抵消 LoCoMo 负向；不升 LTS。 |
| `stage1_event_timeline_context_v179_qwen36_no_think_build4k_cached.json` | clean 的 Source Event Timeline context organization 将 `today`、explicit date、vague `recently` 和 mention-time-only 分开，但 prompt block 过强；4 条 order probe answer diff `3/4`，changed-answer dual judge strict/lenient `1/3 -> 0/3`，且出现半句答案和重复 airline；不升 LTS、不跑 full。 |
| `stage1_source_grounded_temporal_order_repair_v178_qwen36_no_think_build4k_cached.json` | clean 的 temporal-order verifier 触发很窄：v176 trace 上 LME `4/500`、LoCoMo `0/1540`；4 条 clean probe repair triggered `4/4` 但 applied `0/4`、answer diff `0/4`，新增 `27233` repair query tokens；目标坏例的 visible evidence 将 MoCA 解释为 `before 2023-01-15`，强行改成 gold 顺序会违反 clean，不升 LTS、不跑 full。 |
| `stage1_row_length_selected_context_gate_v177_qwen36_no_think_build4k_cached.json` | clean 的 row-local selected-context gate 试图减少 avg-turn profile 依赖，但 LME selected-context 从 `3/500` 扩到 `37/500`，answer diff `15/500`，changed-answer dual judge strict/lenient `12/15 -> 7/15`，avg query tokens `6291.590 -> 6318.580`；不升 LTS，不跑 LoCoMo。 |
| `v170 broad evidence_report list completion simulation` | 只凭 answer 短和 support values 多来补列表会过宽；会误展开 sum/order/current-state/二选一问题，窄门控仍触发 `65` 条且包含明显过包含风险；不实现、不升 LTS。 |
| `stage1_source_grounded_temporal_calculation_repair_v174_qwen36_no_think_build4k_cached.json` | 窄 source-grounded temporal/age/duration repair gate 是 clean 的，但 LME/LoCoMo full answer diff 均为 `0`，同时新增 repair miss/write `2+2`；安全但无收益，不升 LTS。下一步应保留 gate，强化“端点齐全即可计算、不要求答案短语原文出现”的 verifier 指令。 |
| `stage1_no_new_names_profile_advice_repair_v167_qwen36_no_think_build4k_cached.json` | LME full patched strict/lenient `0.826/0.838`（`+2/+2`），LoCoMo 持平；但 LoCoMo 有一条 profile modal wrong->wrong，无收益且有 overreach 风险；v168 已收窄并替代。 |
| `stage1_same_domain_profile_advice_repair_v166_qwen36_no_think_build4k_cached.json` | LME profile changed subset strict/lenient `0/3 -> 3/3` 正向，但一条 answer 引入 Memory Context 未支持的 `MICCAI/IPMI` 会议名；因 no-new-names clean 风险不升 LTS。 |
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
| `diagnostic/stage1_weekend_event_time_candidate_map_v187_probe_summary.md` | v187 probe 结论：clean 解析 `this weekend`，但丢 v184 LoCoMo `+1/+1`，不升 LTS |
| `diagnostic/stage1_weekend_event_time_candidate_map_v187_activation_probe/` | v187 三条 risky activation probe；map applied `1/3`，answer cache `2/1/1` |
| `diagnostic/stage1_segment_local_event_time_candidate_map_v185_v186_probe_summary.md` | v185/v186 probe 结论：v186 风险更低但丢 v184 LoCoMo `+1/+1`，不升 LTS |
| `diagnostic/stage1_role_matched_event_time_candidate_map_v186_activation_probe/` | v186 三条 risky activation probe；map applied `0/3`，answer cache hits `3/3` |
| `diagnostic/stage1_segment_local_event_time_candidate_map_v185_activation_probe/` | v185 三条 risky activation probe；map applied `1/3`，仍有 role-mismatch prompt-map |
| `diagnostic/stage1_strict_event_time_candidate_map_v184_scope_summary.md` | 当前 LTS 晋升结论、clean 说明、full 指标、changed-answer judge 和残余风险 |
| `diagnostic/stage1_strict_event_time_candidate_map_v184_lme_s_full/` | v184 LME full；answer diff `0/500`，map applied `0/500`，继承 v181 judge |
| `diagnostic/stage1_strict_event_time_candidate_map_v184_locomo_nonadv_full/` | v184 LoCoMo full；answer diff `2/1540`，map applied `3/1540` |
| `diagnostic/stage1_strict_event_time_candidate_map_v184_full_changed_vs_v181/` | v184 vs v181 LoCoMo changed-answer dual judge；strict/lenient `1/2 -> 2/2` |
| `diagnostic/stage1_strict_event_time_candidate_map_v184_probe_summary.md` | v184 seeded-cache probe；确认 prompt-identical rows 复用 v181 answer，避免重生成噪声 |
| `diagnostic/stage1_prompt_safe_event_time_candidate_map_v182_scope_summary.md` | v182 负向结论：map 过宽，LoCoMo changed-answer dual judge `17/17 -> 15/17`，促成 v184 收窄 |
| `diagnostic/stage1_grouped_event_time_candidate_manifest_v181_scope_summary.md` | v181 父 LTS；trace-only grouped event-time candidate manifest，LME/LoCoMo answer diff 均为 0 |
| `diagnostic/stage1_trace_event_time_candidate_manifest_v180_scope_summary.md` | v180 父 LTS；trace-only event-time candidate manifest，性能继承 v176 |
| `diagnostic/stage1_event_timeline_context_v179_scope_summary.md` | v179 负向教训：Source Event Timeline prompt block 过强 |
| `diagnostic/stage1_source_grounded_temporal_order_repair_v178_scope_summary.md` | v178 负向教训：clean source-grounded temporal-order repair 触发窄但无改动 |
| `diagnostic/stage1_row_length_selected_context_gate_v177_scope_summary.md` | v177 负向教训：row-length selected-context gate 过宽 |
| `diagnostic/stage1_cross_route_profile_advice_repair_v176_scope_summary.md` | v176 父 LTS；cross-route profile/advice source-backed repair |
| `diagnostic/stage1_temporal_operand_arithmetic_repair_v175_scope_summary.md` | v175 父 LTS；temporal/age/duration operand arithmetic verifier |
| `diagnostic/stage1_source_grounded_modal_inference_repair_v173_scope_summary.md` | v173 父 LTS；modal yes/no source-grounded verifier |
| `diagnostic/stage1_current_state_lifecycle_ledger_v154_scope_summary.md` | lifecycle ledger 关键父结论；更早历史从 git 和对应 experiment 目录追溯 |
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
