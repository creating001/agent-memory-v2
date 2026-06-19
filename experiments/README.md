# 实验入口

`experiments/` 是正式结果和关键诊断的人类可读入口。各 run 目录保留 `summary.md`、`diagnosis.md`、`metrics.json`、`manifest.json` 和配置快照；本文件只维护稳定索引、当前决策和少量会影响下一步的结论。

## 当前 LTS

| 项目 | 结果 |
|---|---|
| 当前 LTS 配置 | `configs/stage1_state_update_organization_ledger_v225_seeded_qwen36_no_think_build4k_cached.json` |
| Backbone | `Qwen/Qwen3.6-35B-A3B` answer/build，`chat_template_kwargs.enable_thinking=false` |
| 方法 | V225 继承 v222，并在 Memory Lifecycle Manifest 中新增 trace-only State/Update Organization Ledger；不改变 retrieval、prompt、answer 或 cache。 |
| LongMemEval-S full | v225 与 v222 answer/prompt/evidence rows/retrieval hits/selected-context diff `0/500`；State/Update Organization Ledger `500/500`；avg build/query tokens `85393.566 / 6580.196`；继承 full `0.834000 / 0.846000`，`417/500` strict，`423/500` lenient |
| LoCoMo non-adversarial full | v225 与 v222 answer/prompt/evidence rows/retrieval hits/selected-context diff `0/1540`；State/Update Organization Ledger `1540/1540`；avg build/query tokens `62015.57402597403 / 6095.268181818182`；继承 full `0.793506 / 0.818831`，`1222/1540` strict，`1261/1540` lenient |
| 状态 | 当前本地 qwen3.6 no-thinking LTS。v225 降低 #5 state/update/conflict 误分类风险；v222 的 #2 evidence pressure、v221 的 source-flow severity、v217 的 context organization ledger、v216 的 memory provenance/activation、v211 的 #1 context-pressure selector 和 v209 的 #2 retrieval tail candidate 风险收敛保留。它不代表五个原始风险都已解决，#2 真实 token 降本和 #5 行为级 state/update reasoning 仍是优先待办。 |

`paired-delta derived` 的含义：新版本只改少量答案，未变化答案沿用父 LTS full dual judge records，变化答案单独跑 paired dual judge 后替换计数。若新版本与父 LTS answer-identical，则可继承父 LTS judge records，但必须记录 full answer diff、cache hit/miss 和输出路径。若论文级最终汇报需要完全独立 run，再对 LTS 配置重跑 fresh full judge。

## 口径说明

- `exact / F1 / BLEU` 只作为低成本诊断和 badcase 定位；是否升级 LTS 只看 dual `deepseek-v4-flash` judge strict/lenient accuracy。
- 新 LTS 优先看 clean/general 风险是否相对当前 LTS 或直接父对照减少；任一/若干项风险实质下降即可升级，但必须显式记录未解决项。性能提升是强加分项，不是唯一前提；性能下降则不能升 LTS。
- 如果改动只影响少量预测，优先做 changed-answer paired judge；不要为了 manifest clean 或形式完整重复重跑未变化样本。
- `v101` 及之前默认属于 `Qwen/Qwen3-30B-A3B-Instruct-2507` 历史探索；当前主线只看显式带 `qwen36_no_think_build4k` 的记录。

## 优先待办

| 优先级 | 项目 | 当前状态 | 下一步 |
|---:|---|---|---|
| 1 | #2 top-k/context noise/rerank | v222 显式记录 final evidence pressure：LME tail after rank `32` 为 `2016` rows，LoCoMo tail after rank `40` 为 `21780` rows；v223 宽 cap56 降 query 但 judge `-13/-12`，v224 profile-only cap56 只省 `6.145` query tokens 且 strict `-1`；v210/v215 证明机械压缩 prompt text 会伤 reader | 下一步不要做宽 final row cap 或 selected-context 包装硬删；优先做 retrieval/pre-compiler 层的 source/span 保真 rerank 或多样性选择，并要求 final evidence set/prompt 有窄 diff 后再 judge |
| 2 | #3 selected context | v221 将 v217 的 risk rows 拆成 evidence-backed severity；v218/v219 hard gate 和 v220 nearby timestamp removal 都降低局部风险或 token，但 changed judge 分别 `-5/-12`、`-4/-1`、`-4/-3` | 保留 selected-context 原文保真路径；后续只允许用 severity 作为审计或极窄 ordering guard，不能把 final evidence-backed local context 当可删除噪声 |
| 3 | #5 memory lifecycle/state/conflict/query-time reasoning | v225 新增 State/Update Organization Ledger：LME/LoCoMo `500/500`、`1540/1540`；activated update slots `156`、`422`，并把 ordinary non-state multi-value slots 单独标出 | 下一步从 audit 走向窄行为：只在 source-backed active/superseded lifecycle chain 上触发 state/update verifier 或 compiler guide；普通多值 fact/list/preference 不进入 stale-conflict 逻辑 |
| 4 | src cleanup | 已有多轮兼容分支，`repair.py`、compiler、pipeline 仍会继续变复杂 | 每个阶段结束后做小范围清理，删已确认无用的兼容代码，不删仍有消融价值的模块 |

## 保留候选

| 配置/文档 | 类型 | 关键结果 | 决策 |
|---|---|---|---|
| `configs/stage1_state_update_organization_ledger_v225_seeded_qwen36_no_think_build4k_cached.json` | current LTS | LME strict/lenient `0.834000/0.846000`，LoCoMo `0.793506/0.818831`；v225 vs v222 answer/prompt/evidence rows/retrieval hits/selected-context diff `0/500`、`0/1540`；State/Update Organization Ledger `500/500`、`1540/1540` | 当前 LTS；新增 trace-only state/update organization ledger，降低 #5 state/update/conflict 误分类风险，性能继承 v222 |
| `configs/stage1_evidence_pressure_ledger_v222_seeded_qwen36_no_think_build4k_cached.json` | previous LTS | LME strict/lenient `0.834000/0.846000`，LoCoMo `0.793506/0.818831`；v222 vs v221 answer/prompt/evidence rows/retrieval hits/selected-context diff `0/500`、`0/1540`；Evidence Pressure Ledger `500/500`、`1540/1540` | 被 v225 替代；新增 trace-only evidence pressure ledger，降低 #2 final evidence tail/session/adjacent pressure 不可诊断风险，性能继承 v221 |
| `configs/stage1_source_flow_severity_ledger_v221_seeded_qwen36_no_think_build4k_cached.json` | previous LTS | LME strict/lenient `0.834000/0.846000`，LoCoMo `0.793506/0.818831`；v221 vs v217 answer/prompt/evidence rows/retrieval hits/selected-context diff `0/500`、`0/1540`；LoCoMo risk rows `5841/5841` final raw evidence-backed、guarded-rerank eligible `0` | 被 v222 替代；新增 trace-only source-flow severity ledger，降低 #2/#3 误删和误排序风险，性能继承 v217 |
| `configs/stage1_context_organization_ledger_v217_seeded_qwen36_no_think_build4k_cached.json` | previous LTS | LME strict/lenient `0.834000/0.846000`，LoCoMo `0.793506/0.818831`；v217 vs v216 answer/prompt/evidence rows/retrieval hits/effective selected-context diff `0/500`、`0/1540`；Context Organization Ledger `500/500`、`1540/1540` | 被 v221 替代；新增 trace-only context organization/source-flow ledger，降低 #2/#3 不可诊断风险，性能继承 v216 |
| `configs/stage1_context_manifest_v216_seeded_qwen36_no_think_build4k_cached.json` | previous LTS | LME strict/lenient `0.834000/0.846000`，LoCoMo `0.793506/0.818831`；v216 vs v214 answer/prompt/evidence rows/retrieval hits/effective selected-context diff `0/500`、`0/1540`；context manifest `500/500`、`1540/1540` | 被 v217 替代；新增 trace-only Context Manifest / Memory Activation Ledger，降低 #5 provenance/activation 不可解释风险，性能继承 v214 |
| `configs/stage1_selected_context_term_normalized_audit_v214_seeded_qwen36_no_think_build4k_cached.json` | previous LTS | LME strict/lenient `0.834000/0.846000`，LoCoMo `0.793506/0.818831`；v214 vs v213 answer/route/prompt/evidence rows/retrieval hits/effective selected-context diff `0/500`、`0/1540`；LoCoMo selected-context risk rows `6163 -> 5841` | 被 v216 替代；规范化 trace-only selected-context audit term matching，降低 #3 误报风险，性能继承 v213 |
| `configs/stage1_materialized_selected_context_audit_v213_seeded_qwen36_no_think_build4k_cached.json` | previous LTS | LME strict/lenient `0.834000/0.846000`，LoCoMo `0.793506/0.818831`；v213 vs v212 answer/route/prompt/evidence rows/retrieval hits/effective selected-context diff `0/500`、`0/1540`；LoCoMo selected-context risk rows `7423 -> 6163` | 被 v214 替代；用 prompt-visible materialized context 审计 selected-context 风险，降低 #3 误报风险，性能继承 v212 |
| `configs/stage1_selected_context_full_risk_audit_v212_seeded_qwen36_no_think_build4k_cached.json` | previous LTS | LME strict/lenient `0.834000/0.846000`，LoCoMo `0.793506/0.818831`；v212 vs v211 answer/route/prompt/evidence rows/retrieval hits/selected-context diff `0/500`、`0/1540`；LoCoMo selected-context risk rows `7423` | 被 v213 替代；扩展 trace-only selected-context risk audit，降低 #3 隐性风险，性能继承 v211 |
| `configs/stage1_total_context_pressure_profile_v211_seeded_qwen36_no_think_build4k_cached.json` | previous LTS | LME strict/lenient `0.834000/0.846000`，LoCoMo `0.793506/0.818831`；v211 vs v209 answer/route/prompt/evidence rows/retrieval hits/selected-context diff `0/500`、`0/1540`；LME profile selected `500/500`，LoCoMo `0/1540` | 被 v212 替代；用 total raw context pressure 替代 avg-turn `long_turn_precision` selector，降低 #1 风险，性能继承 v209 |
| `configs/stage1_conservative_context_budget_v209_seeded_qwen36_no_think_build4k_cached.json` | previous LTS | LME strict/lenient `0.834000/0.846000`，LoCoMo `0.793506/0.818831`；v209 vs v207 answer/route/prompt/evidence rows diff `0/500`、`0/1540`；LME retrieval hits diff `137/500`、drop `416`；LoCoMo drop `0`；audit prompt/selected-context risk 均为 `0` | 被 v211 替代；保守实际 context budget 小幅降低 #2 retrieval tail candidate 风险，性能继承 v207 |
| `configs/stage1_context_budget_audit_v207_seeded_qwen36_no_think_build4k_cached.json` | previous LTS | LME strict/lenient `0.834000/0.846000`，LoCoMo `0.793506/0.818831`；v207 vs v206 answer/route/prompt/evidence rows/retrieval hits diff `0/500`、`0/1540`；audit prompt/selected-context risk 均为 `0` | 被 v209 替代；trace-only context-budget audit 降低 #2 不可见风险，性能继承 v206 |
| `configs/stage1_update_pair_state_conflict_guide_v206_seeded_qwen36_no_think_build4k_cached.json` | previous LTS | LME strict/lenient `0.834000/0.846000`，LoCoMo `0.793506/0.818831`；v206 vs v205 answer/route/prompt/evidence rows diff `0/500`、`0/1540`；LME guide `1/500`，LoCoMo guide `0/1540` | 被 v207 替代；active+superseded update-pair state guide gate，性能继承 v205/v204/v202 |
| `configs/stage1_question_aligned_stateful_conflict_guide_v205_seeded_qwen36_no_think_build4k_cached.json` | previous LTS | LME strict/lenient `0.834000/0.846000`，LoCoMo `0.793506/0.818831`；v205 vs v204 answer diff `0/500`、`0/1540`；LME prompt diff/guide `1/500`，LoCoMo prompt diff/guide `0/1540` | 被 v206 替代；source-backed question-aligned stateful conflict guide，性能继承 v204/v202 |
| `configs/stage1_separate_source_conflict_state_guide_v204_seeded_qwen36_no_think_build4k_cached.json` | previous LTS | LME strict/lenient `0.834000/0.846000`，LoCoMo `0.793506/0.818831`；v204 vs v202 answer/route/prompt/evidence rows diff `0/500`、`0/1540`；guide 触发 `0` | 被 v205 替代；source-separated conflict-gated state guide path，性能继承 v202 |
| `configs/stage1_retrieval_lexical_neutral_long_profile_v202_seeded_qwen36_no_think_build4k_cached.json` | previous LTS | LME strict/lenient `0.834000/0.846000`，LoCoMo `0.793506/0.818831`；v202 vs v201 answer/route/compiled context diff `0/500`、`0/1540`；retrieval profile redundant lexical protect key removed | 被 v204 替代；删除长 profile 冗余 retrieval lexical-protect override，性能继承 v201 |
| `configs/stage1_compiler_budget_neutral_long_profile_v201_seeded_qwen36_no_think_build4k_cached.json` | previous LTS | LME strict/lenient `0.834000/0.846000`，LoCoMo `0.793506/0.818831`；v201 vs v200 prompt/answer/route/compiler trace diff `0/500`、`0/1540`；compiler budget profile keys removed | 被 v202 替代；删除长 profile 冗余 compiler budget override，性能继承 v200 |
| `configs/stage1_finalizer_neutral_long_profile_v200_seeded_qwen36_no_think_build4k_cached.json` | previous LTS | LME strict/lenient `0.834000/0.846000`，LoCoMo `0.793506/0.818831`；v200 vs v199 prompt/answer/route diff `0/500`、`0/1540`；LME profile risk_count `5 -> 4` | 被 v201 替代；删除长 profile 的 finalizer override，性能继承 v199 |
| `configs/stage1_route_neutral_long_profile_v199_seeded_qwen36_no_think_build4k_cached.json` | previous LTS | LME strict/lenient `0.834000/0.846000`，LoCoMo `0.793506/0.818831`；v199 vs v198 prompt/answer/route diff `0/500`、`0/1540`；LME profile risk_count `6 -> 5` | 被 v200 替代；删除长 profile 的 route override，性能继承 v198 |
| `configs/stage1_default_short_context_layout_v198_seeded_qwen36_no_think_build4k_cached.json` | previous LTS | LME strict/lenient `0.834000/0.846000`，LoCoMo `0.793506/0.818831`；v198 vs v197 prompt/answer diff `0/500`、`0/1540`；LoCoMo granularity profile selected `0/1540` | 被 v199 替代；删除短 turn avg-turn profile，默认化短上下文排版，性能继承 v197 |
| `configs/stage1_granularity_profile_audit_v197_seeded_qwen36_no_think_build4k_cached.json` | previous LTS | LME strict/lenient `0.834000/0.846000`，LoCoMo `0.793506/0.818831`；v197 vs v196 prompt/answer diff `0/500`、`0/1540`；granularity audit selected LME `500/500`、LoCoMo `1540/1540` | 被 v198 替代；trace-only granularity profile audit 降低 #1/#3 隐性风险，性能继承 v196/v194/v193/v191/v184 |
| `configs/stage1_selected_context_risk_audit_v196_seeded_qwen36_no_think_build4k_cached.json` | previous LTS | LME strict/lenient `0.834000/0.846000`，LoCoMo `0.793506/0.818831`；v196 vs v194 prompt/answer diff `0/500`、`0/1540`；LoCoMo audit applied `329/1540`、risk rows `1083` | 被 v197 替代；trace-only selected-context risk audit 降低 #3 隐性风险，性能继承 v194/v193/v191/v184 |
| `configs/stage1_temporal_mention_time_fallback_v194_seeded_qwen36_no_think_build4k_cached.json` | previous LTS | LME strict/lenient `0.834000/0.846000`，LoCoMo `0.793506/0.818831`；v194 vs v193 prompt diff `0/500`、`1/1540`，answer diff `0/500`、`0/1540` | 被 v196 替代；窄 mention-time fallback 降低 #5 temporal activation 风险，性能继承 v193/v191/v184 |
| `configs/stage1_temporal_activation_audit_v193_seeded_qwen36_no_think_build4k_cached.json` | previous LTS | LME strict/lenient `0.834000/0.846000`，LoCoMo `0.793506/0.818831`；v193 vs v191 prompt/answer diff `0/500`、`0/1540` | 被 v194 替代；trace-only temporal activation audit 降低 #5 隐性 activation 风险，性能继承 v191/v184 |
| `configs/stage1_weekend_parser_gated_v191_seeded_qwen36_no_think_build4k_cached.json` | previous LTS | LME strict/lenient `0.834000/0.846000`，LoCoMo `0.793506/0.818831`；v191 vs v184 prompt/answer diff `0/500`、`0/1540` | 被 v193 替代；显式 gate v187/v188 rejected weekend parser 和 prompt-map `mention_time` 暴露，降低复现/兼容风险且性能继承 v184 |
| `configs/stage1_strict_event_time_candidate_map_v184_seeded_qwen36_no_think_build4k_cached.json` | previous LTS | LME strict/lenient `0.834000/0.846000`，LoCoMo `0.793506/0.818831`；v184 vs v181 answer diff `0/500`、`2/1540` | 被 v191 替代；严格 prompt-side event-time candidate map 降低 #5 query-time activation 风险，LoCoMo changed-answer dual judge `1/2 -> 2/2` |
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
| `stage1_profile_tail_cap56_v224_seeded_qwen36_no_think_build4k_cached.json` | v224 profile-only final evidence cap56 是 clean/source-preserving，LME no-op、LoCoMo prompt/evidence diff `40/1540`、answer diff `18/1540`，avg query tokens `6095.268 -> 6089.123`；changed-answer dual judge `13/18 -> 12/18` strict、`13/18 -> 13/18` lenient，严格正确率下降且 token 收益太小，不升 LTS。 |
| `stage1_route_tail_cap56_v223_seeded_qwen36_no_think_build4k_cached.json` | v223 route-scoped final evidence cap56 是 clean/source-preserving，LME no-op、LoCoMo avg query tokens `6095.268 -> 5980.044`，但 prompt/evidence diff `927/1540`、answer diff `369/1540`，changed-answer dual judge `258/369 -> 245/369` strict、`273/369 -> 261/369` lenient，derived LoCoMo full `0.785065/0.811039`，不升 LTS。 |
| `stage1_temporal_selected_context_center_timestamp_v220_seeded_qwen36_no_think_build4k_cached.json` | v220 不删除 local context，只在 temporal_lookup selected-context wrapper 中保留 center timestamp、去掉 nearby timestamp；LME prompt/answer diff `0/500`，LoCoMo avg query tokens `6095.268 -> 6048.208`，但 risk rows 仍为 `5841`，prompt diff `338/1540`、answer diff `99/1540`，changed-answer dual judge strict/lenient `63/99 -> 59/99`、`65/99 -> 62/99`，derived LoCoMo full `0.790909/0.816883` 低于 v217，不升 LTS。 |
| `stage1_temporal_materialized_context_source_gate_v219_seeded_qwen36_no_think_build4k_cached.json` | v219 将 v218 的 materialized-context source gate 收窄到 temporal_lookup；LME prompt/answer diff `0/500`，LoCoMo risk rows `5841 -> 4932`、avg query tokens `6095.268 -> 6065.517`，但 prompt diff `322/1540`、answer diff `105/1540`，changed-answer dual judge strict/lenient `69/105 -> 65/105`、`69/105 -> 68/105`，derived LoCoMo full `0.790909/0.818182` 低于 v217，不升 LTS。 |
| `stage1_materialized_context_source_gate_v218_seeded_qwen36_no_think_build4k_cached.json` | v218 的 materialized-context source gate 是 clean/general 的 source-flow hard gate；LME changed judge 持平 `1/1 -> 1/1`，LoCoMo avg query tokens `6095.268 -> 5739.079`、selected-context risk rows `5841 -> 0`，但 prompt diff `1480/1540`、answer diff `683/1540`，changed-answer dual judge strict/lenient `505/683 -> 500/683`、`527/683 -> 515/683`，derived LoCoMo full `0.790260/0.811039` 低于 v217，不升 LTS。下一步不能做过宽 prompt-visible hard gate，应做更细粒度 source-flow scoring/rerank。 |
| `stage1_compact_selected_context_format_v215_seeded_qwen36_no_think_build4k_cached.json` | v215 用更短 selected-context wrapper 试图降低 #2 query token；LoCoMo probe200 avg query tokens `6142.005 -> 6017.23`，但 prompt diff `198/200`、evidence row ids diff `47/200`、answer diff `86/200`。token 节省不足以抵消 reader 行为漂移，不升 LTS、不跑 full/judge。 |
| `stage1_role_aware_tail_snippet_v210_seeded_qwen36_no_think_build4k_cached.json` | v210 只压缩 rank `>32` tail row 的 prompt text，retrieval hits/evidence rows/source order 均不变，LME avg query tokens `6580.196 -> 6122.956`；但 answer diff `96/500`，changed-answer dual judge strict/lenient `55/96 -> 41/96`、`62/96 -> 53/96`，说明 row-set preserving tail snippet 仍会损伤 reader，不升 LTS、不跑 LoCoMo。 |
| `stage1_guarded_context_budget_v208_seeded_qwen36_no_think_build4k_cached.json` | v208 把 v207 的 `16000` char / `32` anchor context-budget audit 改成真实 retrieval budget；LME answer diff `0/500` 但 prompt/evidence rows diff `1/500`，avg query tokens `6580.196 -> 6580.362`，LoCoMo dropped `0` 且完全 no-op；不升 LTS。后续改用更保守或动态 prompt-stable guard。 |
| `stage1_conflict_gated_memory_state_guide_v203_seeded_qwen36_no_think_build4k_cached.json` | v203 首版 source-linked state guide 在 LME full 上 answer diff `10/500`、prompt diff `13/500`、evidence rows diff `11/500`；guide 触发 `3/500`，但把多次 museum/market/flight event 值误当 state conflict，同时 `memory_record_source=evidence_rows` 改变了原 current-state memory-aware evidence ordering。v204 已用 separate guide source 和 event-value exclusion 修正；v203 不升 LTS，不跑 LoCoMo full。 |
| `stage1_temporal_source_grounded_selected_context_v195_seeded_qwen36_no_think_build4k_cached.json` | v195 在 v194 上给 temporal selected-context 加 source-grounded self-reference hard gate；LoCoMo selected-context applied `1536 -> 1398`、avg query tokens `6089.272 -> 5996.258`，但 full answer diff `105/1540`，changed-answer dual judge 从 v194 `76/105` strict、`79/105` lenient 降到 v195 `67/105` strict、`68/105` lenient，derived LoCoMo full `0.787662/0.811688`，明显低于 v194，不升 LTS。 |
| `stage1_candidate_evidence_map_v192_seeded_qwen36_no_think_build4k_cached.json` | v192 打开 temporal/list_count `Candidate Evidence Map`，但三条 risky activation probe 上 answer diff `2/3`；changed-answer dual judge 从 v191 `2/2` strict/lenient 降到 v192 `1/2`，Nate 行退回 `The weekend of August 27-28, 2022` 且两遍判错，不升 LTS。 |
| `stage1_source_grounded_self_ref_selected_context_v190_seeded_qwen36_no_think_build4k_cached.json` | v190 用 source-grounded self-reference gate 收窄 temporal selected-context，Nate 行保留 `D19:9,D5:10`、John/James 行 selected-context `0`，但 Nate 答案仍退回 `2022-08-27 to 2022-08-28`，会丢 v184 LoCoMo `+1/+1`，不升 LTS；同时暴露 v187 weekend 解析全局污染重跑 v184 的复现风险。 |
| `stage1_temporal_question_ref_selected_context_v189_seeded_qwen36_no_think_build4k_cached.json` | v189 将 temporal selected-context 加上 question-reference gate，三条 risky probe 中 selected-context `3/3 -> 0/3`、avg query tokens 降到 `4898.667`，但答案退回 v181/v186-v188 行为，会丢 v184 LoCoMo `+1/+1`，不升 LTS。 |
| `stage1_temporal_ambiguity_event_time_map_v188_seeded_qwen36_no_think_build4k_cached.json` | v188 只在高置信 Event-Time Candidate Map 出现时加入 `mention_time`/planned `event_time` ambiguity contract，风险面比全局 temporal prompt 小；但三条 v184 risky activation probe 上 Nate row 仍回答 `2022-08-27 to 2022-08-28`，相对当前 LTS 会丢 LoCoMo `+1/+1`，不升 LTS。 |
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
| `diagnostic/stage1_state_update_organization_ledger_v225_scope_summary.md` | 当前 LTS 晋升结论：v225 新增 trace-only State/Update Organization Ledger，full answer/prompt/evidence rows/retrieval hits/selected-context diff 均为 `0`，性能继承 v222 |
| `diagnostic/stage1_state_update_organization_ledger_v225_lme_s_full/` | v225 LME full；vs v222 answer/prompt/evidence rows/retrieval hits/selected-context diff `0/500`，State/Update Organization Ledger `500/500` |
| `diagnostic/stage1_state_update_organization_ledger_v225_locomo_nonadv_full/` | v225 LoCoMo full；vs v222 answer/prompt/evidence rows/retrieval hits/selected-context diff `0/1540`，State/Update Organization Ledger `1540/1540` |
| `diagnostic/stage1_evidence_pressure_ledger_v222_scope_summary.md` | previous LTS 晋升结论：v222 新增 trace-only Evidence Pressure Ledger，full answer/prompt/evidence rows/retrieval hits/selected-context diff 均为 `0`，LoCoMo tail after rank `40` 为 `21780` rows / `2789101` chars |
| `diagnostic/stage1_evidence_pressure_ledger_v222_lme_s_full/` | v222 LME full；vs v221 answer/prompt/evidence rows/retrieval hits/selected-context diff `0/500`，Evidence Pressure Ledger `500/500` |
| `diagnostic/stage1_evidence_pressure_ledger_v222_locomo_nonadv_full/` | v222 LoCoMo full；vs v221 answer/prompt/evidence rows/retrieval hits/selected-context diff `0/1540`，Evidence Pressure Ledger `1540/1540` |
| `diagnostic/stage1_profile_tail_cap56_v224_scope_summary.md` | v224 负向结论：profile-only cap56 只省 LoCoMo avg query `6.145` tokens，changed-answer judge strict/lenient `-1/0`，不升 LTS |
| `diagnostic/stage1_route_tail_cap56_v223_scope_summary.md` | v223 负向结论：route-scoped final evidence cap56 降 LoCoMo query tokens，但 answer diff `369/1540`、changed-answer judge `-13/-12`，不升 LTS |
| `diagnostic/stage1_source_flow_severity_ledger_v221_scope_summary.md` | previous LTS 晋升结论：v221 新增 trace-only Source-flow Severity Ledger，full answer/prompt/evidence rows/retrieval hits/selected-context diff 均为 `0`，LoCoMo risk rows `5841/5841` 为 final raw evidence-backed |
| `diagnostic/stage1_source_flow_severity_ledger_v221_lme_s_full/` | v221 LME full；vs v217 answer/prompt/evidence rows/retrieval hits/selected-context diff `0/500`，Severity Ledger `500/500` |
| `diagnostic/stage1_source_flow_severity_ledger_v221_locomo_nonadv_full/` | v221 LoCoMo full；vs v217 answer/prompt/evidence rows/retrieval hits/selected-context diff `0/1540`，Severity Ledger `1540/1540`，guarded-rerank eligible `0` |
| `diagnostic/stage1_temporal_selected_context_center_timestamp_v220_scope_summary.md` | v220 负向结论：保留 context 文本但移除 nearby timestamp 后 changed-answer judge `-4/-3`，不升 LTS |
| `diagnostic/stage1_temporal_selected_context_center_timestamp_v220_lme_s_full/` | v220 LME full；prompt/answer/evidence/selected-context diff `0/500` |
| `diagnostic/stage1_temporal_selected_context_center_timestamp_v220_locomo_nonadv_full/` | v220 LoCoMo full；answer diff `99/1540`，risk rows `5841`，avg query tokens `6048.207792207792` |
| `diagnostic/stage1_temporal_materialized_context_source_gate_v219_scope_summary.md` | v219 负向结论：temporal-only hard gate 降低 selected-context risk/token，但 changed-answer judge `-4/-1`，不升 LTS |
| `diagnostic/stage1_temporal_materialized_context_source_gate_v219_lme_s_full/` | v219 LME full；prompt/answer/evidence/selected-context diff `0/500` |
| `diagnostic/stage1_temporal_materialized_context_source_gate_v219_locomo_nonadv_full/` | v219 LoCoMo full；answer diff `105/1540`，risk rows `4932`，avg query tokens `6065.516883116883` |
| `diagnostic/stage1_materialized_context_source_gate_v218_scope_summary.md` | v218 负向结论：selected-context risk rows 降为 `0`、LoCoMo query tokens 下降，但 prompt diff `1480/1540`、changed-answer judge `-5/-12`，不升 LTS |
| `diagnostic/stage1_materialized_context_source_gate_v218_lme_s_full/` | v218 LME full；answer diff `1/500`，changed-answer judge 持平 `1/1` |
| `diagnostic/stage1_materialized_context_source_gate_v218_locomo_nonadv_full/` | v218 LoCoMo full；answer diff `683/1540`，selected-context risk rows `0`，avg query tokens `5739.078571428571` |
| `diagnostic/stage1_context_organization_ledger_v217_scope_summary.md` | previous LTS 晋升结论：v217 新增 trace-only Context Organization Ledger，full answer/prompt/evidence rows/retrieval hits/effective selected-context diff 均为 `0`，性能继承 v216 |
| `diagnostic/stage1_context_organization_ledger_v217_lme_s_full/` | v217 LME full；vs v216 answer/prompt/evidence rows/retrieval hits/effective selected-context diff `0/500`，Context Organization Ledger `500/500` |
| `diagnostic/stage1_context_organization_ledger_v217_locomo_nonadv_full/` | v217 LoCoMo full；vs v216 answer/prompt/evidence rows/retrieval hits/effective selected-context diff `0/1540`，Context Organization Ledger `1540/1540`，selected-context risk rows `5841` |
| `diagnostic/stage1_context_budget_audit_v207_scope_summary.md` | previous LTS 晋升结论：v207 新增 trace-only context-budget audit，full answer/route/prompt/evidence rows/retrieval hits diff 均为 `0`，性能继承 v206 |
| `diagnostic/stage1_context_budget_audit_v207_lme_s_full/` | v207 LME full；vs v206 answer/route/prompt/evidence rows/retrieval hits diff `0/500`，audit prompt/selected-context risk `0/0` |
| `diagnostic/stage1_context_budget_audit_v207_locomo_nonadv_full/` | v207 LoCoMo full；vs v206 answer/route/prompt/evidence rows/retrieval hits diff `0/1540`，audit prompt/selected-context risk `0/0` |
| `diagnostic/stage1_update_pair_state_conflict_guide_v206_scope_summary.md` | previous LTS 晋升结论：v206 增加 active+superseded update-pair gate，full answer/route/prompt/evidence rows diff 均为 `0`，性能继承 v205/v204/v202 |
| `diagnostic/stage1_update_pair_state_conflict_guide_v206_lme_s_full/` | v206 LME full；vs v205 answer/route/prompt/evidence rows diff `0/500`，Managed Memory State Guide 触发 `1/500` |
| `diagnostic/stage1_update_pair_state_conflict_guide_v206_locomo_nonadv_full/` | v206 LoCoMo full；vs v205 answer/route/prompt/evidence rows diff `0/1540`，Managed Memory State Guide 触发 `0/1540` |
| `diagnostic/stage1_question_aligned_stateful_conflict_guide_v205_scope_summary.md` | previous LTS 晋升结论：v205 增加 question-aligned/stateful slot gates，LME guide 触发 `1/500` 且 answer diff `0/500`，LoCoMo prompt/answer diff `0/1540`，性能继承 v204/v202 |
| `diagnostic/stage1_question_aligned_stateful_conflict_guide_v205_lme_s_full/` | v205 LME full；vs v204 answer/route/evidence rows diff `0/500`，prompt diff `1/500`，Managed Memory State Guide 触发 `1/500` |
| `diagnostic/stage1_question_aligned_stateful_conflict_guide_v205_locomo_nonadv_full/` | v205 LoCoMo full；vs v204 answer/route/prompt/evidence rows diff `0/1540`，Managed Memory State Guide 触发 `0/1540` |
| `diagnostic/stage1_separate_source_conflict_state_guide_v204_scope_summary.md` | previous LTS 晋升结论：v204 分离 state-guide source 与 evidence ordering，full prompt/answer/evidence rows diff 均为 0，性能继承 v202 |
| `diagnostic/stage1_separate_source_conflict_state_guide_v204_lme_s_full/` | v204 LME full；vs v202 answer/route/prompt/evidence rows diff `0/500`，Managed Memory State Guide 触发 `0/500` |
| `diagnostic/stage1_separate_source_conflict_state_guide_v204_locomo_nonadv_full/` | v204 LoCoMo full；vs v202 answer/route/prompt/evidence rows diff `0/1540`，Managed Memory State Guide 触发 `0/1540` |
| `diagnostic/stage1_conflict_gated_memory_state_guide_v203_lme_s_full/` | v203 拒绝诊断；LME answer diff `10/500`、prompt diff `13/500`，event 多值误触发 state guide，已由 v204 修正 |
| `diagnostic/stage1_retrieval_lexical_neutral_long_profile_v202_scope_summary.md` | previous LTS 晋升结论：v202 删除长 profile 冗余 retrieval lexical-protect override，full answer/route/compiled context diff 均为 0，性能继承 v201 |
| `diagnostic/stage1_retrieval_lexical_neutral_long_profile_v202_lme_s_full/` | v202 LME full；vs v201 answer diff `0/500`、route diff `0/500`、compiled context diff `0/500`、normalized trace diff `0/500` |
| `diagnostic/stage1_retrieval_lexical_neutral_long_profile_v202_locomo_nonadv_full/` | v202 LoCoMo full；vs v201 answer diff `0/1540`、route diff `0/1540`、compiled context diff `0/1540`、raw trace diff 仅为 2 条 embedding cache 元数据 |
| `diagnostic/stage1_retrieval_lexical_neutral_long_profile_v202_activation_probe/` | v202 三条 risky activation probe；answer/route/compiled context/raw trace diff `0/3` |
| `diagnostic/stage1_compiler_budget_neutral_long_profile_v201_scope_summary.md` | previous LTS 晋升结论：v201 删除长 profile 冗余 compiler budget override，full prompt/answer/route/compiler trace diff 均为 0，性能继承 v200 |
| `diagnostic/stage1_compiler_budget_neutral_long_profile_v201_lme_s_full/` | v201 LME full；vs v200 prompt diff `0/500`、answer diff `0/500`、route diff `0/500`、compiler trace diff `0/500` |
| `diagnostic/stage1_compiler_budget_neutral_long_profile_v201_locomo_nonadv_full/` | v201 LoCoMo full；vs v200 prompt diff `0/1540`、answer diff `0/1540`、route diff `0/1540`、granularity audit selected `0/1540` |
| `diagnostic/stage1_compiler_budget_neutral_long_profile_v201_activation_probe/` | v201 三条 risky activation probe；prompt/answer diff `0/3`，granularity profile selected `0/3` |
| `diagnostic/stage1_finalizer_neutral_long_profile_v200_scope_summary.md` | previous LTS 晋升结论：v200 删除长 profile finalizer override，full prompt/answer/route diff 均为 0，性能继承 v199 |
| `diagnostic/stage1_route_neutral_long_profile_v199_scope_summary.md` | previous LTS 晋升结论：v199 删除长 profile route override，full prompt/answer/route diff 均为 0，性能继承 v198 |
| `diagnostic/stage1_default_short_context_layout_v198_scope_summary.md` | previous LTS 晋升结论：v198 删除短 turn avg-turn profile，full prompt/answer diff 均为 0，性能继承 v197 |
| `diagnostic/stage1_granularity_profile_audit_v197_scope_summary.md` | previous LTS 晋升结论：v197 trace-only granularity profile audit，full prompt/answer diff 均为 0，性能继承 v196 |
| `diagnostic/stage1_selected_context_risk_audit_v196_scope_summary.md` | previous LTS 晋升结论：v196 trace-only selected-context risk audit，full prompt/answer diff 均为 0，性能继承 v194 |
| `diagnostic/stage1_selected_context_risk_audit_v196_lme_s_full/` | v196 LME full；vs v194 prompt diff `0/500`、answer diff `0/500`、answer cache `500/0/0` |
| `diagnostic/stage1_selected_context_risk_audit_v196_locomo_nonadv_full/` | v196 LoCoMo full；vs v194 prompt diff `0/1540`、answer diff `0/1540`、audit applied `329/1540`、risk rows `1083` |
| `diagnostic/stage1_selected_context_risk_audit_v196_activation_probe/` | v196 三条 risky activation probe；prompt/answer diff `0/3`，audit 标出 Nate/John-James selected-context 风险 row |
| `diagnostic/stage1_temporal_source_grounded_selected_context_v195_changed_vs_v194/summary.md` | v195 负向结论：temporal selected-context hard gate 降低 context noise/token，但 LoCoMo changed-answer judge `76/105 -> 67/105` strict、`79/105 -> 68/105` lenient，不升 LTS |
| `diagnostic/stage1_temporal_source_grounded_selected_context_v195_locomo_nonadv_full/` | v195 LoCoMo full；vs v194 prompt diff `324/1540`、answer diff `105/1540`、selected-context rows `8540 -> 7572` |
| `diagnostic/stage1_temporal_source_grounded_selected_context_v195_lme_s_full/` | v195 LME full；vs v194 prompt diff `0/500`、answer diff `0/500` |
| `diagnostic/stage1_temporal_source_grounded_selected_context_v195_activation_probe/` | v195 三条 risky activation probe；保住 Nate `2022-08-22`，阻断 John/James wrong-speaker selected-context，但 full changed-answer judge 负向 |
| `diagnostic/stage1_temporal_mention_time_fallback_v194_scope_summary.md` | 历史 LTS 晋升结论：v194 窄 mention-time fallback，full answer diff 均为 0，性能继承 v193/v191/v184 |
| `diagnostic/stage1_temporal_mention_time_fallback_v194_lme_s_full/` | v194 LME full；vs v193 prompt diff `0/500`、answer diff `0/500`、answer cache `500/0/0` |
| `diagnostic/stage1_temporal_mention_time_fallback_v194_locomo_nonadv_full/` | v194 LoCoMo full；vs v193 prompt diff `1/1540`、answer diff `0/1540`、answer cache `1540/0/0` |
| `diagnostic/stage1_temporal_mention_time_fallback_v194_activation_probe/` | v194 三条 risky activation probe；只改 Nate prompt，answer diff `0/3` |
| `diagnostic/stage1_temporal_activation_audit_v193_scope_summary.md` | v193 晋升结论：trace-only temporal activation audit，full prompt/answer diff 均为 0，性能继承 v191/v184 |
| `diagnostic/stage1_temporal_activation_audit_v193_lme_s_full/` | v193 LME full；vs v191 prompt diff `0/500`、answer diff `0/500`、answer cache `500/0/0` |
| `diagnostic/stage1_temporal_activation_audit_v193_locomo_nonadv_full/` | v193 LoCoMo full；vs v191 prompt diff `0/1540`、answer diff `0/1540`、answer cache `1540/0/0` |
| `diagnostic/stage1_temporal_activation_audit_v193_activation_probe/` | v193 三条 risky activation probe；vs v191 prompt/answer diff `0/3`，audit 标出两个 `exact_today_low_question_coverage` |
| `diagnostic/stage1_candidate_evidence_map_v192_probe_summary.md` | v192 负向结论：宽 Candidate Evidence Map 增加 prompt/token 并丢 Nate changed-answer judge，不升 LTS |
| `diagnostic/stage1_candidate_evidence_map_v192_activation_probe/` | v192 三条 risky activation probe；answer diff vs v191 `2/3`，avg query tokens `6244.333` |
| `diagnostic/stage1_candidate_evidence_map_v192_changed_vs_v191_probe/` | v192 vs v191 changed-answer dual judge；v191 `2/2` -> v192 `1/2` |
| `diagnostic/stage1_weekend_parser_gated_v191_scope_summary.md` | 历史 LTS 晋升结论：v191 gate rejected weekend parser / prompt-map `mention_time`，full prompt/answer diff 均为 0，性能继承 v184 |
| `diagnostic/stage1_weekend_parser_gated_v191_lme_s_full_r2/` | v191 LME full；vs v184 prompt diff `0/500`、answer diff `0/500`、answer cache `500/0/0` |
| `diagnostic/stage1_weekend_parser_gated_v191_locomo_nonadv_full_r2/` | v191 LoCoMo full；vs v184 prompt diff `0/1540`、answer diff `0/1540`、answer cache `1540/0/0` |
| `diagnostic/stage1_weekend_parser_gated_v191_activation_probe_r2/` | v191 三条 risky activation probe；vs v184 prompt/answer diff `0/3`，answer cache `3/0/0` |
| `diagnostic/stage1_source_grounded_self_ref_selected_context_v190_probe_summary.md` | v190 probe 结论：self-reference gate 降 selected-context wrong-speaker 风险，但丢 v184 LoCoMo `+1/+1`，不升 LTS |
| `diagnostic/stage1_source_grounded_self_ref_selected_context_v190_activation_probe/` | v190 三条 risky activation probe；selected-context `2/3`，answer cache `0/3/3` |
| `diagnostic/stage1_temporal_question_ref_selected_context_v189_probe_summary.md` | v189 probe 结论：question-reference gate 降低 selected-context/token，但丢 v184 LoCoMo `+1/+1`，不升 LTS |
| `diagnostic/stage1_temporal_question_ref_selected_context_v189_activation_probe/` | v189 三条 risky activation probe；selected-context `0/3`，answer cache `0/3/3` |
| `diagnostic/stage1_temporal_ambiguity_event_time_map_v188_probe_summary.md` | v188 probe 结论：map-scoped ambiguity contract 未恢复 v184 Nate 行收益，不升 LTS |
| `diagnostic/stage1_temporal_ambiguity_event_time_map_v188_activation_probe/` | v188 三条 risky activation probe；map applied `1/3`，answer cache `2/1/1` |
| `diagnostic/stage1_weekend_event_time_candidate_map_v187_probe_summary.md` | v187 probe 结论：clean 解析 `this weekend`，但丢 v184 LoCoMo `+1/+1`，不升 LTS |
| `diagnostic/stage1_weekend_event_time_candidate_map_v187_activation_probe/` | v187 三条 risky activation probe；map applied `1/3`，answer cache `2/1/1` |
| `diagnostic/stage1_segment_local_event_time_candidate_map_v185_v186_probe_summary.md` | v185/v186 probe 结论：v186 风险更低但丢 v184 LoCoMo `+1/+1`，不升 LTS |
| `diagnostic/stage1_role_matched_event_time_candidate_map_v186_activation_probe/` | v186 三条 risky activation probe；map applied `0/3`，answer cache hits `3/3` |
| `diagnostic/stage1_segment_local_event_time_candidate_map_v185_activation_probe/` | v185 三条 risky activation probe；map applied `1/3`，仍有 role-mismatch prompt-map |
| `diagnostic/stage1_strict_event_time_candidate_map_v184_scope_summary.md` | 历史 LTS 晋升结论、clean 说明、full 指标、changed-answer judge 和残余风险 |
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
