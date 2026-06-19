# 配置入口

`configs/` 只保留当前 LTS、强 baseline、split best 和仍有方法价值的关键对照。负向探索不长期堆在索引里；需要复现时从 git 历史和 `experiments/README.md` 回溯。

## 当前 LTS 配置

| 用途 | 配置 | 状态 |
|---|---|---|
| 后续新实验默认配置 | `stage1_source_backed_lifecycle_noop_repair_prune_v231_seeded_qwen36_no_think_build4k_cached.json` | 当前本地 v231 LTS。继承 v230/v229 full accuracy，保留 source-backed state diagnostics，删除 applied 为 0 的 source-backed lifecycle repair trigger；LongMemEval-S strict/lenient `0.834000 / 0.846000`，LoCoMo `0.793506 / 0.818831`。 |

## 保留对照

| 配置 | 作用 |
|---|---|
| `stage1_source_backed_lifecycle_noop_repair_prune_v231_seeded_qwen36_no_think_build4k_cached.json` | 当前 LTS；删除 no-op source-backed lifecycle repair trigger，LME `0.834000 / 0.846000`，LoCoMo `0.793506 / 0.818831`，相对 v230 answer/prompt/evidence/retrieval/route diff `0/500`、`0/1540`，avg query 降为 `6637.824`、`6100.992207792207`。 |
| `stage1_source_backed_lifecycle_memory_repair_v230_seeded_qwen36_no_think_build4k_cached.json` | v231 父 LTS；source-backed current-state lifecycle memory repair，LME `0.834000 / 0.846000`，LoCoMo `0.793506 / 0.818831`，相对 v229 answer/prompt/evidence/retrieval diff `0/500`、`0/1540`。 |
| `stage1_guarded_tail_exchange_rerank_v229_seeded_qwen36_no_think_build4k_cached.json` | v230 父 LTS；source/provenance-aware guarded tail exchange，LME `0.834000 / 0.846000`，LoCoMo `0.793506 / 0.818831`，相对 v225 answer diff `0/500`、`0/1540`。 |
| `stage1_state_update_organization_ledger_v225_seeded_qwen36_no_think_build4k_cached.json` | v229 父 LTS；trace-only State/Update Organization Ledger，LME `0.834000 / 0.846000`，LoCoMo `0.793506 / 0.818831`，相对 v222 answer/prompt/evidence rows/retrieval hits/selected-context diff `0/500`、`0/1540`。 |
| `stage1_evidence_pressure_ledger_v222_seeded_qwen36_no_think_build4k_cached.json` | v225 父 LTS；trace-only Evidence Pressure Ledger，性能继承 v221。 |
| `stage1_source_flow_severity_ledger_v221_seeded_qwen36_no_think_build4k_cached.json` | v222 父 LTS；trace-only Source-flow Severity Ledger，性能继承 v217。 |
| `stage1_context_organization_ledger_v217_seeded_qwen36_no_think_build4k_cached.json` | v221 父 LTS；trace-only Context Organization Ledger，性能继承 v216。 |
| `stage1_context_manifest_v216_seeded_qwen36_no_think_build4k_cached.json` | v217 父 LTS；trace-only Context Manifest / Memory Activation Ledger，性能继承 v214。 |
| `stage1_selected_context_term_normalized_audit_v214_seeded_qwen36_no_think_build4k_cached.json` | v216 父 LTS；normalized selected-context audit，LoCoMo selected-context risk rows `6163 -> 5841`，性能继承 v213。 |
| `stage1_total_context_pressure_profile_v211_seeded_qwen36_no_think_build4k_cached.json` | v214 父线；用 total raw context pressure 替代 avg-turn selector，性能继承 v209。 |
| `stage1_conservative_context_budget_v209_seeded_qwen36_no_think_build4k_cached.json` | v211 父线；保守 context budget 实际裁掉 LME tail retrieval candidates，性能继承 v207。 |
| `stage1_strict_event_time_candidate_map_v184_seeded_qwen36_no_think_build4k_cached.json` | 历史 LTS；严格 prompt-side event-time candidate map，LME `0.834000 / 0.846000`，LoCoMo `0.793506 / 0.818831`，相对 v181 answer diff `0/500`、`2/1540`。 |
| `stage1_grouped_event_time_candidate_manifest_v181_qwen36_no_think_build4k_cached.json` | v184 父 LTS；trace-only grouped event-time candidate manifest，answer-identical to v180，LME `0.834000 / 0.846000`，LoCoMo `0.792857 / 0.818182`。 |
| `stage1_trace_event_time_candidate_manifest_v180_qwen36_no_think_build4k_cached.json` | v181 父 LTS；trace-only answer-slot-aware event-time manifest，answer-identical to v176，LME `0.834000 / 0.846000`，LoCoMo `0.792857 / 0.818182`。 |
| `stage1_cross_route_profile_advice_repair_v176_qwen36_no_think_build4k_cached.json` | v180 父 LTS；错路由 advice/fact/list 拒答可进入 no-new-names profile advice verifier，LME `0.834000 / 0.846000`，LoCoMo `0.792857 / 0.818182`。 |
| `stage1_temporal_operand_arithmetic_repair_v175_qwen36_no_think_build4k_cached.json` | v176 父 LTS；source-grounded repair 只在窄 temporal/age/duration 拒答且操作数齐全时允许 verifier 做简单算术，LME `0.832000 / 0.842000`，LoCoMo `0.792857 / 0.818182`。 |
| `stage1_source_grounded_modal_inference_repair_v173_qwen36_no_think_build4k_cached.json` | v175 父 LTS；source-grounded repair 只在 modal yes/no 拒答且 support anchors 足够时调用 verifier，LME `0.830000 / 0.840000`，LoCoMo `0.792208 / 0.817532`。 |
| `stage1_source_grounded_temporal_calculation_repair_v174_qwen36_no_think_build4k_cached.json` | v174 no-op 诊断；temporal/age/duration source-grounded repair gate clean 但 full answer diff 为 0，保留为 #4/#5 verifier 提示词教训。 |
| `stage1_profile_preference_value_guard_v172_qwen36_no_think_build4k_cached.json` | v173 父 LTS；source-grounded finalizer 在拒答且唯一非含糊 preference support value 时保真 profile preference 值，LME `0.830000 / 0.840000`，LoCoMo `0.790909 / 0.816234`。 |
| `stage1_lifecycle_slot_specificity_guard_v171_qwen36_no_think_build4k_cached.json` | v172 父 LTS；source-grounded finalizer 保真 previous/current occupation/role 等 lifecycle slot 的唯一具体 support value，LME `0.830000 / 0.840000`，LoCoMo `0.790260 / 0.815584`。 |
| `stage1_source_value_specificity_guard_v170_qwen36_no_think_build4k_cached.json` | v171 父 LTS；source-grounded finalizer 保真短答丢失的唯一 support value specificity，LME `0.828000 / 0.838000`，LoCoMo `0.790260 / 0.815584`。 |
| `stage1_numeric_slot_label_guard_v169_qwen36_no_think_build4k_cached.json` | v170 父 LTS；source-grounded finalizer 只保真裸数字 `level` 槽位，LME `0.828000 / 0.838000`，LoCoMo `0.789610 / 0.815584`。 |
| `stage1_scoped_modal_profile_advice_repair_v168_qwen36_no_think_build4k_cached.json` | v169 父 LTS；scoped profile/advice repair，LME `0.826000 / 0.838000`，LoCoMo `0.789610 / 0.815584`。 |
| `stage1_memory_lifecycle_manifest_v162_qwen36_no_think_build4k_cached.json` | v168 父 LTS；trace-only lifecycle manifest，性能继承 v158。 |
| `stage1_current_state_source_repair_v151_qwen36_no_think_build4k_cached.json` | previous LTS；只保留 current-state source repair，LME `0.822000 / 0.834000`，LoCoMo `0.789610 / 0.815584`。 |
| `stage1_selective_source_repair_v150_qwen36_no_think_build4k_cached.json` | v151 父 LTS；profile/current repair，LME `0.820000 / 0.834000`，LoCoMo `0.789610 / 0.815584`，被 v151 收窄替代。 |
| `stage1_superseded_source_chain_v127_qwen36_no_think_build4k_cached.json` | v150 父 LTS；fresh full dual judge：LME `0.820000 / 0.832000`，LoCoMo `0.789610 / 0.815584`。 |
| `stage1_route_scoped_local_evidence_unit_v125_qwen36_no_think_build4k_cached.json` | v127 父 LTS；降低 #4 mechanical finalizer 和 #3 selected-context heuristic 风险。 |
| `stage1_memory_source_interleave_v126_qwen36_no_think_build4k_cached.json` | source-backed memory source interleave ablation，被 v127 继承修正。 |
| `stage1_route_scoped_fact_profile_state_budget_v129_qwen36_no_think_build4k_cached.json` | route-scoped token-budget 对照；成本方向有参考价值，但不是 LTS。 |
| `stage1_list_count_rerank_filter_v152_qwen36_no_think_build4k_cached.json` | #2 list-count rerank pruning 负向对照；降 query token 但 dual judge 负向且增加 rerank token。 |
| `stage1_source_grounded_guard_v121_qwen36_no_think_build4k_cached.json` | #4 source-grounded guardrail 对照；不做 broad mechanical answer rewrite。 |
| `stage1_long_profile_profile_state_selected_context_v128_qwen36_no_think_build4k_cached.json` | #1/#3 selected-context generalization 审计。 |
| `stage1_scoped_memory_state_guide_v142_qwen36_no_think_build4k_cached.json` | #5 scoped state guide 负向/混合对照。 |
| `stage1_memory_version_chain_v144_qwen36_no_think_build4k_cached.json` | #5 source-backed version-chain row ordering 负向/混合对照。 |
| `stage1_memory_slot_chain_v145_qwen36_no_think_build4k_cached.json` | #5 retrieval-time slot-chain 负向对照。 |
| `stage1_answer_slot_checklist_v149_qwen36_no_think_build4k_cached.json` | v150 的直接负向父思路；broad checklist 过度拒答。 |
| `stage1_current_state_update_contract_v153_qwen36_no_think_build4k_cached.json` | #5 prompt-only current-state update discipline 负向对照；提示下一步要做 slot/ledger/verifier 而非加宽 reader 规则。 |

## 当前 Split Best

| Benchmark | 配置 | 结果 | 用途 |
|---|---|---:|---|
| LongMemEval-S full | `stage1_source_backed_lifecycle_noop_repair_prune_v231_seeded_qwen36_no_think_build4k_cached.json` | strict `0.834000` / lenient `0.846000` | 当前 LTS；v231 vs v230 answer/prompt/evidence/retrieval/route diff `0/500`，性能继承 v230。 |
| LoCoMo non-adversarial full | `stage1_source_backed_lifecycle_noop_repair_prune_v231_seeded_qwen36_no_think_build4k_cached.json` | strict `0.793506` / lenient `0.818831` | 当前 LTS；v231 vs v230 answer/prompt/evidence/retrieval/route diff `0/1540`，性能继承 v230。 |

## 关键 Baseline

| 配置 | 作用 |
|---|---|
| `stage1_clean_skeleton.json` | 无 LLM smoke / 单元测试级骨架配置。 |
| `stage1_naive_rag_top40_external.json` | clean naive RAG 强 baseline。 |
| `stage1_hybrid_bm25_v18_cached.json` | raw-turn BM25 + dense hybrid baseline。 |
| `stage1_evidence_report_contract_v28_cached.json` | LME 早期强底座，可见 `evidence_report` contract。 |
| `stage1_temporal_event_contract_v29_cached.json` | LoCoMo temporal event/mention time 对照。 |
| `stage1_answer_format_guard_v35_cached.json` | LoCoMo 强 baseline，answer format guard。 |
| `stage1_lme_token_safe_format_guard_v36_cached.json` | LME token-safe format guard 对照。 |
| `stage1_update_conflict_guide_v80_cached.json` | LME update/conflict guide 对照。 |
| `stage1_selected_context_v95_cached.json` | LoCoMo 正向但 LME 负向/过预算的 selected-context 转折点。 |

## Cache 和版本规则

- 当前主线是 `Qwen/Qwen3.6-35B-A3B` no-thinking；只有显式带 `qwen36_no_think_build4k` 的配置才参与当前 LTS 对比。
- 新方法必须另起版本；若 answer prompt 或 repair/verifier prompt 改变，必须另起对应 cache path/namespace。若只改 source-grounded finalizer/postprocess 且 answer raw response 不变，可显式复用父 answer cache，并在记录中说明。
- v176 复用 v102 build-memory cache、v158 base answer cache，并用 v175 repair cache 预种 v176 repair cache；新增 cross-route profile advice trigger 只让新增 advice repair miss/write，避免旧 repair 重跑造成不可比表面漂移。
- v180 只新增 trace-only compiler diagnostics，prompt/answer/repair 不变，显式复用 v176 的 answer 与 repair cache；full answer diff 为 0 时继承 v176 dual judge 结果。
- v181 只新增 trace-only grouped manifest diagnostics，prompt/answer/repair 不变，显式复用 v180/v176 的 answer 与 repair cache；full answer diff 为 0 时继承 v180/v176 dual judge 结果。
- v184 新增严格 prompt-side event-time candidate map，并用 v181 full prediction traces/predictions 预种 answer cache；prompt-identical rows 命中 v181 answer，prompt-changed rows miss/write 后只对 changed answers 做 paired judge。
- v217 只新增 trace-only Context Organization Ledger，prompt/answer/retrieval/repair 不变，显式复用 v216 answer cache；full answer diff 为 0 时继承 v216 dual judge 结果。
- v222 只新增 trace-only Evidence Pressure Ledger，prompt/answer/retrieval/repair 不变，显式复用 v221 answer cache；full answer diff 为 0 时继承 v221 dual judge 结果。
- v225 只新增 trace-only State/Update Organization Ledger，prompt/answer/retrieval/repair 不变，显式复用 v222 answer cache；full answer diff 为 0 时继承 v222 dual judge 结果。
- v231 主 answer prompt 不变，显式复用 v229/v230 answer cache；source-backed lifecycle repair trigger 被关闭，剩余 repair 调用使用 v231 专属 repair cache path/namespace。
- cache 命中只能减少重复 API 调用，不能改变逻辑 token 统计。正式记录仍报告逻辑 cold-build/query token。
- 不得使用 gold answer、judge output、benchmark 标签、sample id、test feedback 或样本级规则构造配置、cache、prediction、retrieval、compiler、answer 或 repair。

## 已清理顶层配置

以下负向、被替代或已无保留实验目录支撑的候选已从 `configs/` 删除。结论保留在 `experiments/README.md` 或 git 历史中；确需复现时从历史 commit 取回配置。
