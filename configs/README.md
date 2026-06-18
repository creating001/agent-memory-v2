# 配置入口

`configs/` 只保留当前 LTS、当前 split best、强 baseline 和已保留正式实验支撑的关键对照。负向探索和无保留实验目录支撑的中间配置不长期保留；需要复现时从 git 历史回溯。

## 当前 LTS 配置

| 用途 | 配置 | 状态 |
|---|---|---|
| 后续新实验默认配置 | `stage1_superseded_source_chain_v127_qwen36_no_think_build4k_cached.json` | 当前本地 v127 LTS + `Qwen/Qwen3.6-35B-A3B` answer/build backbone；请求级 `chat_template_kwargs.enable_thinking=false`。继承 v125 route-scoped temporal local evidence unit 和 v121 source-grounded guard，并在 `profile_preference/current_state` routes 用 build-memory source backpointers 组织 active/superseded update chain；typed memory text 不作为 reader evidence。Fresh full dual judge：LongMemEval-S strict/lenient `0.820000 / 0.832000`，LoCoMo `0.789610 / 0.815584`。按 goal 五项风险审计：继承 #4/#3 风险收敛，并降低 #5 的 source-backed memory organization/update-chain 风险；#5 broad lifecycle/state/conflict/query-time reasoning、#1 granularity/profile、#2 top-k/context noise 仍未解决。 |
| 已拒绝 memory-management 诊断 | `stage1_memory_version_chain_v144_qwen36_no_think_build4k_cached.json` | 继承 v127，只把 `profile_preference/current_state` evidence ordering 改成 source-backed `memory_version_chain_interleave`，不把 typed memory text 当 reader evidence。Compile scope 窄且成本几乎不变，但 formal dual judge：LME strict/lenient `0.812000 / 0.840000` mixed，LoCoMo `0.785714 / 0.811688` 低于 fresh v127，不升 LTS；保留为 #5 state/version ablation。 |
| 近期 memory-management 诊断 | `stage1_scoped_memory_state_guide_v142_qwen36_no_think_build4k_cached.json` | 继承 v141 source-linked managed-memory state guide，但去掉 broad `fact_lookup` 触发，只在 `current_state/profile_preference` 使用，且 `max_memory_records=4`。Formal dual judge：LME strict/lenient `0.816000 / 0.836000`，LoCoMo `0.784416 / 0.806494`。相对 fresh v127，LME mixed、LoCoMo 负向，不升 LTS；作为 #5 下一步 conflict/as-of state、version chain 和 query-time memory reasoning 设计输入保留。 |
| 近期已拒绝结构诊断 | `stage1_query_context_budget_v136_qwen36_no_think_build4k_cached.json`；`stage1_budget_aware_selected_context_v137_qwen36_no_think_build4k_cached.json`；`stage1_tighter_context_budget_v138_qwen36_no_think_build4k_cached.json`；`stage1_context_pressure_compiler_v139_qwen36_no_think_build4k_cached.json`；`stage1_route_gated_context_pressure_v140_qwen36_no_think_build4k_cached.json` | v136 清除了 profile 但 LME selected_context 重新打开导致 avg context chars `20779.668`；v137 把 LME selected_context 降到 `32/500`，但 avg context chars 仍为 `20244.338`；v138 raw estimate 降到 `15292.94`，但 compiler/context chars 仍未降；v139 dry-run 正向但 LME full dual judge strict/lenient `0.790/0.818`；v140 route-gated 后略恢复到 `0.794/0.826`，仍低于 fresh v127 LME `0.820/0.832`，拒绝且不跑 LoCoMo。 |
| 已拒绝 memory-management 诊断 | `stage1_memory_state_guide_v141_qwen36_no_think_build4k_cached.json` | 回到 v127 底座并新增 source-linked managed-memory state guide。方向命中 #5，但 dry-run scope 太宽：LME `218/500` prompts、LoCoMo `932/1540` prompts 出现 guide，avg context chars 分别到 `20436.048` / `18313.279`；不跑 formal，下一版收窄。 |
| 已拒绝 token-budget 诊断 | `stage1_fact_tail_snippet_budget_v134_qwen36_no_think_build4k_cached.json` | 继承 v129/v133，只在 `fact_lookup` 对直接检索 rank `>40` 的 raw rows 使用 `query_snippet`，`tail_max_row_text_chars=100`；row selection 仍按未压缩文本预算，保证不因压缩额外纳入 row。LME dry-run `0/500` prompt/row change；LoCoMo fact route row set `0` change，avg context chars `17637.014 -> 17025.604`，changed-subset avg query `5910.726`。但 paired dual flash judge 对同 882 fact keys 负向：V129 strict/lenient `0.819728 / 0.833333`，V134 `0.807256 / 0.824263`，拒绝为 LTS 候选。 |
| token-budget 诊断候选 | `stage1_route_scoped_fact_profile_state_budget_v129_qwen36_no_think_build4k_cached.json` | 继承 v127，只给 `fact_lookup` / `profile_preference` / `current_state` 加 compiler route budget `max_evidence_chars=17000`，不改 retrieval top-k，不碰 `temporal_lookup` / `list_count`。LME full route-only lexical exact/F1/BLEU1 `0.428000/0.633744/0.589603 -> 0.430000/0.636173/0.592207`；LoCoMo `0.244156/0.537674/0.483784 -> 0.245455/0.538048/0.483962`。收益小且 LoCoMo changed-subset query 仍为 `6112.337`，不能升级 LTS。 |
| 已拒绝 token-budget 诊断 | `stage1_fact_tail_snippet_budget_v133_qwen36_no_think_build4k_cached.json` | 继承 v129，只在 `fact_lookup` 对 rank `>40` direct hits 使用 320-char query snippet。LME dry-run不变；LoCoMo fact changed prompt `207/882`、row set `0` change，但 fact avg context 只降 `8.552` chars，full avg context 只降 `4.898` chars，过保守，拒绝。 |
| 已拒绝 token-budget 诊断 | `stage1_fact_tail_filter_preserve_order_v132_qwen36_no_think_build4k_cached.json` | 继承 v129，新增 compiler `memory_tail_filter_preserve_order`，只在 `fact_lookup` 保留前 40 retrieval anchors 并加入最多 1 条 memory-linked tail raw row，避免 v130/v131 的 order-only drift。LoCoMo fact query 降到 `5115.770`，但 exact/F1/BLEU1 `0.249433/0.550951/0.488438 -> 0.241497/0.536504/0.476871`，full route-only exact `0.245455 -> 0.240909`，拒绝。 |
| 被 LTS 继承的 ablation | `stage1_memory_source_interleave_v126_qwen36_no_think_build4k_cached.json` | 继承 v125/v121，只在 `profile_preference` / `current_state` route 使用 source-backed `memory_source_interleave` raw-row ordering。LoCoMo profile/current paired dual `+4/+4`，LME profile/current `-1/-1`；v127 在其上补 active/superseded update chain 后成为 LTS。 |
| 上一版 LTS 对照 | `stage1_extended_selected_context_v116_qwen36_no_think_build4k_cached.json` | V116 extended selected context；继承 v110 modal-only grounded inference，只扩展短 turn selected-context 后向邻域。LongMemEval-S strict/lenient `0.812000 / 0.834000`，LoCoMo strict/lenient `0.779221 / 0.807143`。已被 v125 替代。 |
| 上一版 LTS 对照 | `stage1_route_scoped_local_evidence_unit_v125_qwen36_no_think_build4k_cached.json` | V125 route-scoped temporal local evidence unit；继承 v121 source-grounded guard 和 v116 selected-context 基础。LongMemEval-S 兼容继承 strict/lenient `0.812000 / 0.834000`，LoCoMo route-only strict/lenient `0.789610 / 0.807792`。已被 v127 替代。 |
| 已拒绝结构诊断 | `stage1_long_profile_profile_state_selected_context_v128_qwen36_no_think_build4k_cached.json` | 继承 v127，只在 long-turn profile 的 `profile_preference/current_state` 启用 per-row selected context，检验能否拆解长/短 turn heuristic。LME 只改 `37/500` prompts、LoCoMo `0/1540` 变化，但 LME exact 持平且 changed-subset avg query `6480.730`，不作为 accuracy candidate。 |
| clean/general 清理候选 | `stage1_source_grounded_guard_v121_qwen36_no_think_build4k_cached.json` | 继承 v116，只把 broad mechanical finalizer 收窄为 `source_grounded_consistency_guard`；不做 count/date/money/relative-time 机械算答案，只允许基于 answer model 自己的 `missing` 字段扩写拒答。 |
| 已拒绝诊断候选 | `stage1_local_evidence_unit_v124_qwen36_no_think_build4k_cached.json` | 继承 v121，把 short-turn selected context 扩展到 `temporal_lookup` 并把 `max_rows` 提到 `10`；LoCoMo dry-run changed `1536/1540`、avg context chars `+2101.65`，过宽，拒绝。 |
| 已拒绝诊断候选 | `stage1_aggregation_contract_v123_qwen36_no_think_build4k_cached.json` | 继承 v121，只在 `list_count` 打开 reader-side aggregation report；LME list_count route-all strict/lenient `0.815126 / 0.840336`，低于 v116 同子集，拒绝。 |
| 已拒绝诊断候选 | `stage1_per_row_selected_context_v122_qwen36_no_think_build4k_cached.json` | 继承 v121，只移除 long-turn profile 的 selected-context 关闭覆盖；LME dry-run selected_context applied `317/500` 且压缩 raw rows，拒绝。 |
| 上一版 qwen3.6 LTS 对照 | `stage1_spacing_profile_v102_qwen36_no_think_build4k_cached.json` | V102 raw-memory-granularity adaptive；LongMemEval-S strict/lenient `0.814000 / 0.830000`，LoCoMo strict/lenient `0.776623 / 0.798052`。v116 继承其 build/retrieval 基础并提升 LoCoMo lenient 到 baseline target 以上。 |
| 已拒绝诊断候选 | `stage1_no_relative_time_finalizer_v113_qwen36_no_think_build4k_cached.json` | 继承 v110 modal-only grounded inference，只关闭全局 relative-time mechanical finalizer。v102 finalizer-impact 离线诊断显示 LoCoMo relative-time 改写在触发样本上从 draft lenient `40/46` 降到 final `34/46`，但 v110 LoCoMo 路径中该 finalizer 已实际触发 `0` 次；v113 相比 v110 LME/LoCoMo answer text 分别 changed `0/500` 和 `0/1540`，因此拒绝为 no-op。 |
| 已拒绝诊断候选 | `stage1_evidence_unit_rerank_v112_qwen36_no_think_build4k_cached.json` | 在 v110 正向候选基础上加入 Qwen3-Reranker-0.6B evidence-unit rerank；LME full strict/lenient `0.810000 / 0.828000`，低于 v102 和 v110，停止，不跑 LoCoMo full。诊断显示真实 changed-answer gain/loss `11/12`，multi-session 与 temporal coverage 受损。 |
| 已拒绝诊断候选 | `stage1_modal_abstention_repair_v111_qwen36_no_think_build4k_cached.json` | 在 v110 基础上增加 source-grounded modal abstention repair；只在 modal/inference 问题的最终 draft answer 明确拒答/信息不足时触发 verifier。Smoke 有局部收益，但 LongMemEval-S full strict/lenient `0.816000 / 0.828000`，主指标低于 v102 `0.830000` 和 v110 `0.834000`，停止，不跑 LoCoMo full。 |
| 正向但已被 v116 替代 | `stage1_modal_grounded_inference_v110_qwen36_no_think_build4k_cached.json` | v109 收窄 ablation：只在 modal yes/no inference 问题触发 grounded inference discipline，排除 plain advice/recommendation `what do you think` 负例；LME strict/lenient `0.812000 / 0.834000`，LoCoMo strict/lenient `0.779221 / 0.799351`。v116 继承 v110 并把 LoCoMo lenient 提升到 `0.807143`，因此替代 v110。 |
| 已拒绝诊断候选 | `stage1_grounded_inference_v109_qwen36_no_think_build4k_cached.json` | v108 后的新方向：不改 retrieval/build/finalizer，只在 question-text modal/inference 问题上加入 grounded inference discipline；LME full strict/lenient `0.816000 / 0.828000`，主指标低于 v102 `0.830000`，停止，不跑 LoCoMo full。 |
| 已拒绝诊断候选 | `stage1_source_coverage_v108_qwen36_no_think_build4k_cached.json` | v107 后的新方向：typed memory 不进入 reader prompt，只作为 source-linked coverage signal；LME full strict/lenient `0.802000 / 0.824000`，低于 v102，停止，不跑 LoCoMo full。 |
| 诊断候选 | `stage1_route_scoped_memory_activation_v107_qwen36_no_think_build4k_cached.json` | v106 route 诊断后的隔离 ablation：只在 question-derived `fact_lookup` / `profile_preference` 打开 source-aligned typed memory activation；LME lenient 与 v102 持平、strict 略低；LoCoMo lenient 与 v102 持平、strict 略低，不作为 LTS。 |
| 已拒绝诊断候选 | `stage1_memory_activation_v106_qwen36_no_think_build4k_cached.json` | v105 负向后的隔离 ablation：保留 source-aligned typed memory activation guide，但恢复 v102 `evidence_order=retrieval`；LME full strict/lenient `0.806000 / 0.820000`，仍低于 v102 `0.814000 / 0.830000`，不跑 LoCoMo full。 |
| 已拒绝诊断候选 | `stage1_memory_activation_v105_qwen36_no_think_build4k_cached.json` | 在当时的 qwen3.6 no-thinking v102 LTS 上打开 source-aligned typed memory activation guide，并用 `memory_aware` raw-row ordering；LME full strict/lenient `0.774000 / 0.800000`，低于 v102 `0.814000 / 0.830000`，不跑 LoCoMo full。下一步只测试 activation，不改变 v102 retrieval order。 |
| 已拒绝诊断候选 | `stage1_context_guard_v104_qwen36_no_think_build4k_cached.json` | 移除大块 granularity profile 切换；selected context 改为 per-turn `max_center_chars`；关闭 mechanical finalizer，启用 source-grounded repair guardrail；LME full 负向且 query token 过高，不作为 LTS。 |
| 历史 qwen3-30b 参考 | `stage1_spacing_profile_v102_cached.json` | `Qwen/Qwen3-30B-A3B-Instruct-2507` backbone；LongMemEval-S / LoCoMo non-adversarial full 单次 flash accuracy 均为 `0.800000`。旧 backbone，不作为当前 qwen3.6 dual flash target 判断。 |

说明：

- qwen3.6 no-thinking v116 已在主目录 formal rerun/compatibility 检查并按 dual flash judge 汇报：LongMemEval-S strict/lenient `0.812000 / 0.834000`，LoCoMo strict/lenient `0.779221 / 0.807143`。`agent-memory-other` 只作为测试目录，不作为主项目 LTS 来源。
- v102 只根据 raw dialogue 的平均 turn 长度选择 granularity profile，不使用 benchmark 标签、gold、judge、sample id、row index 或测试反馈；但当前已标记为 generalization 风险，见 `experiments/diagnostic/stage1_v102_generalization_audit_v104_plan.md`。
- 长 turn 分支恢复 v88 precision path：top40、selected_context off、operation workpad、update/advice guide、evidence-answer-detail finalizer。
- 短 turn 分支继承 v96 selected-context path：top60、route-budgeted temporal top40、selected_context 最多 6 行。
- v101 及之前的配置默认属于 `Qwen/Qwen3-30B-A3B-Instruct-2507` 历史探索；只有显式带 `qwen36_no_think_build4k` 的配置才属于当前 qwen3.6 no-thinking backbone。
- 新方法必须另起版本和 cache namespace；不能用 qwen3-30B 的历史 cache 或外部测试目录结果证明 qwen3.6 no-thinking 配置。
- v105 复用 v102 build-memory cache，因为 build 阶段完全未改；正式汇报仍必须按 cached usage 统计逻辑 cold-build token。v105 answer cache 使用独立 `qwen36_no_think_build4k_answer_v105_memory_activation.sqlite`。
- v106 同样复用 v102 build-memory cache，因为 build 阶段完全未改；v106 answer cache 使用独立 `qwen36_no_think_build4k_answer_v106_memory_activation.sqlite`。
- v107 同样复用 v102 build-memory cache，因为 build 阶段完全未改；v107 answer cache 使用独立 `qwen36_no_think_build4k_answer_v107_route_scoped_memory_activation.sqlite`。
- v108 同样复用 v102 build-memory cache，因为 build 阶段完全未改；v108 answer cache 使用独立 `qwen36_no_think_build4k_answer_v108_source_coverage.sqlite`。为隔离局部 route 改动，正式 run 前可用 `scripts/seed_answer_cache_from_traces.py` 从 v102 prediction traces seed 相同 prompt 的 answer cache；该脚本只读 prediction-time prompt/answer/usage，不读 labels/judge/category/sample id。
- v109 同样复用 v102 build-memory cache，因为 build/retrieval 全部未改；v109 answer cache 使用独立 `qwen36_no_think_build4k_answer_v109_grounded_inference.sqlite`。为隔离局部 prompt 改动，正式 run 前可从 v102 prediction traces seed 相同 prompt 的 answer cache；只有触发 grounded inference discipline 的 prompt 会新跑。
- v110 同样复用 v102 build-memory cache，因为 build/retrieval 全部未改；v110 answer cache 使用独立 `qwen36_no_think_build4k_answer_v110_modal_grounded_inference.sqlite`。正式 run 前用 v102 traces + v102 predictions seed 相同 prompt 的 prediction-time final answers；不读取 labels/judge/category/sample id，不再用 v109 traces 覆盖未改 prompt。v110 是被 v116 继承并替代的正向候选。
- v111 同样复用 v102 build-memory cache，base answer cache 使用独立 `qwen36_no_think_build4k_answer_v111_modal_abstention_repair.sqlite`，可从 v110 traces + predictions seed；repair cache 使用 `qwen36_no_think_build4k_answer_repair_v111_modal_abstention.sqlite`。repair trigger 只看 prediction-time question/draft answer/Memory Context，不读取 labels/judge/category/sample id。
- v112 同样复用 v102 build-memory cache，因为 build 阶段未改；answer cache 使用独立 `qwen36_no_think_build4k_answer_v112_evidence_unit_rerank.sqlite`。rerank 只读 question text、raw turns、same-session neighbors 和 build-memory source links，不读取 labels/judge/category/sample id。
- v113 同样复用 v102 build-memory cache，因为 build/retrieval/compiler/backbone 全部未改；answer cache 使用独立 `qwen36_no_think_build4k_answer_v113_no_relative_time_finalizer.sqlite`。正式 run 前可从 v110 prediction traces seed 相同 prompt 的 base answer cache；预测阶段不读取 labels/judge/category/sample id。
- v116 同样复用 v102 build-memory cache，因为 build/retrieval/compiler/backbone 全部未改；answer cache 使用独立 `qwen36_no_think_build4k_answer_v116_extended_selected_context.sqlite`。正式 run 前可从 v110 prediction traces seed 相同 prompt 的 base answer cache；只有 selected context 文本真正改变的样本会新跑 answer。
- v121-v144 同样复用 v102 build-memory cache。v127 是当前本地 LTS，answer cache 使用独立 `qwen36_no_think_build4k_answer_v127_superseded_source_chain.sqlite`；v125 answer cache 使用独立 `qwen36_no_think_build4k_answer_v125_route_scoped_local_evidence_unit.sqlite`；v126 answer cache 使用独立 `qwen36_no_think_build4k_answer_v126_memory_source_interleave.sqlite`；v128 answer cache 使用独立 `qwen36_no_think_build4k_answer_v128_long_profile_profile_state_selected_context.sqlite`；v129 answer cache 使用独立 `qwen36_no_think_build4k_answer_v129_route_scoped_fact_profile_state_budget.sqlite`；v132 answer cache 使用独立 `qwen36_no_think_build4k_answer_v132_fact_tail_filter_preserve_order.sqlite`；v133 answer cache 使用独立 `qwen36_no_think_build4k_answer_v133_fact_tail_snippet_budget.sqlite`；v134 answer cache 使用独立 `qwen36_no_think_build4k_answer_v134_fact_tail_snippet_budget.sqlite`；v135 answer cache 使用独立 `qwen36_no_think_build4k_answer_v135_temporal_local_evidence_signal_gate.sqlite`；v136 answer cache 使用独立 `qwen36_no_think_build4k_answer_v136_query_context_budget.sqlite`；v137 answer cache 使用独立 `qwen36_no_think_build4k_answer_v137_budget_aware_selected_context.sqlite`；v138 answer cache 使用独立 `qwen36_no_think_build4k_answer_v138_tighter_context_budget.sqlite`；v139 answer cache 使用独立 `qwen36_no_think_build4k_answer_v139_context_pressure_compiler.sqlite`；v140 answer cache 使用独立 `qwen36_no_think_build4k_answer_v140_route_gated_context_pressure.sqlite`；v141 answer cache 使用独立 `qwen36_no_think_build4k_answer_v141_memory_state_guide.sqlite`；v142 answer cache 使用独立 `qwen36_no_think_build4k_answer_v142_scoped_memory_state_guide.sqlite`；v144 answer cache 使用独立 `qwen36_no_think_build4k_answer_v144_memory_version_chain.sqlite`。v130/v131 是 v132 前的 dry-run-only 收窄诊断，v133 是 v134 前的过保守 dry-run 诊断。full cached/merge diagnostic 可从 prediction traces seed or merge 相同 prompt，但必须标注为 diagnostic，并说明同一 dirty worktree 中 parser guard 对旧 malformed cached answers 的影响。

## 当前 Split Best

| Benchmark | 配置 | 结果 | 用途 |
|---|---|---:|---|
| LongMemEval-S full | `stage1_superseded_source_chain_v127_qwen36_no_think_build4k_cached.json` | strict `0.820000` / lenient `0.832000` | 当前本地 LTS fresh full dual judge。 |
| LoCoMo non-adversarial full | `stage1_superseded_source_chain_v127_qwen36_no_think_build4k_cached.json` | strict `0.789610` / lenient `0.815584` | 当前本地 LTS fresh full dual judge。 |

## 关键 Baseline / 对照

| 配置 | 作用 |
|---|---|
| `stage1_clean_skeleton.json` | 无 LLM smoke / 单元测试级骨架配置。 |
| `stage1_naive_rag_top40_external.json` | clean naive RAG 强 baseline。 |
| `stage1_hybrid_bm25_v18_cached.json` | raw-turn BM25 + dense hybrid baseline。 |
| `stage1_evidence_report_contract_v28_cached.json` | LME 早期强底座，可见 `evidence_report` contract。 |
| `stage1_temporal_event_contract_v29_cached.json` | LoCoMo temporal event/mention time 对照。 |
| `stage1_answer_format_guard_v35_cached.json` | LoCoMo 强 baseline，answer format guard。 |
| `stage1_selected_context_v95_cached.json` | LoCoMo 正向但 LME 负向/过预算的 selected-context 转折点。 |
| `stage1_lme_token_safe_format_guard_v36_cached.json` | LME token-safe format guard 对照。 |
| `stage1_update_conflict_guide_v80_cached.json` | LME update/conflict guide 对照。 |

## 已清理顶层配置

以下负向、被替代或已无保留实验目录支撑的候选已从 `configs/` 删除。结论保留在 `experiments/README.md` 或 git 历史中；确需复现时从历史 commit 取回配置：

- `stage1_source_expansion_v12_cached.json`
- `stage1_structured_evidence_guide_v14_cached.json`
- `stage1_structured_answer_contract_v26_cached.json`
- `stage1_selective_repair_v32_cached.json`
- `stage1_retrieval_top60_v33_cached.json`
- `stage1_route_budgeted_retrieval_v34_cached.json`
- `stage1_operation_workpad_v42_cached.json`
- `stage1_finalizer_duration_fix_v73_cached.json`
- `stage1_missing_detail_finalizer_v79_cached.json`
- `stage1_update_conflict_value_slot_v81_cached.json`
- `stage1_personalized_advice_contract_v83_cached.json`
- `stage1_relative_time_finalizer_v94_cached.json`
- `stage1_granularity_adaptive_v97_cached.json`
- `stage1_source_anchor_candidate_v91_cached.json`
- `stage1_uncertain_repair_v92_cached.json`
- `stage1_list_aggregation_v93_lme_cached.json`
- `stage1_list_aggregation_v93_locomo_cached.json`
- `stage1_temporal_local_evidence_signal_gate_v135_qwen36_no_think_build4k_cached.json`

## 使用规则

- 新主线配置必须显式记录关键开关、cache path 和 cache namespace。
- 任何 prompt、answer parsing、finalizer、repair、retrieval 或 build-memory 改动都必须另起版本，不要复用 LTS answer cache 证明新方法。
- 正式实验必须保存 `config_snapshot.json`、`summary.md`、`metrics.json`、`diagnosis.md`、`manifest.json`，并记录 commit、dirty 状态、benchmark/subset、token 成本和 outputs 路径。
