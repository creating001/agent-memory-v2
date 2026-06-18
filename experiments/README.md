# 实验入口

`experiments/` 是正式结果和关键诊断的人类可读入口。详细证据保留在各 run 目录、`summary.md`、`diagnosis.md`、`metrics.json` 和 `manifest.json` 中；本文件只维护稳定索引和当前决策。

## 当前 LTS

| 项目 | 结果 |
|---|---|
| 当前 LTS 配置 | `configs/stage1_superseded_source_chain_v127_qwen36_no_think_build4k_cached.json` |
| Backbone | `Qwen/Qwen3.6-35B-A3B` answer/build，`chat_template_kwargs.enable_thinking=false` |
| 方法 | V127 superseded source chain；继承 v125 route-scoped temporal local evidence unit 和 v121 source-grounded guard，并在 profile/current routes 用 build-memory source backpointers 组织 active/superseded update chain。Typed memory text 不作为 reader evidence。 |
| LongMemEval-S full | fresh full dual judge strict/lenient `0.820000 / 0.832000`；`410/500` strict，`416/500` lenient |
| LoCoMo non-adversarial full | fresh full dual judge strict/lenient `0.789610 / 0.815584`；`1216/1540` strict，`1256/1540` lenient |
| 状态 | 当前本地 qwen3.6 no-thinking LTS。按 goal 五项风险审计，v127 继承 #4/#3 风险收敛，并降低 #5 中的 source-backed memory organization/update-chain 风险；#5 更完整的 lifecycle、state/version/conflict handling、query-time memory reasoning 仍未解决，#1 granularity/profile 和 #2 top-k/context noise/rerank 也仍未解决。 |

## 口径说明

- `v101` 及之前默认属于 `Qwen/Qwen3-30B-A3B-Instruct-2507` 历史探索。
- 当前主线是 `Qwen/Qwen3.6-35B-A3B` no-thinking；只有名称显式带 `qwen36_no_think_build4k` 的记录才按当前 backbone 对比。
- `agent-memory-other` / `agent-memory-gpt` 是外部测试目录，不作为主项目 LTS 结果来源。
- `exact / F1 / BLEU` 只作为低成本诊断和 badcase 定位；算法是否成立、是否升级 LTS，只看 dual `deepseek-v4-flash` judge strict/lenient。
- 新 LTS 优先看 clean/general 风险是否相对当前 LTS 或直接父对照减少；这里的风险固定指 goal 中五项风险。任一/若干项风险实质下降即可升级，但必须显式记录未解决项；性能提升是强加分项，不是唯一前提。若改动影响预测结果，必须用 paired/full dual `deepseek-v4-flash` judge 说明 accuracy 变化；`exact / F1 / BLEU` 不能单独决定 LTS。

## 优先待办

| 优先级 | 项目 | 当前状态 | 下一步 |
|---:|---|---|---|
| 1 | #5 memory lifecycle/state/conflict/query-time reasoning | v145 已把 state/version slot chain 前移到 retrieval-time clean candidate expansion；compile scope 窄：LME slot-chain `16/500`、LoCoMo `34/1540`，context 基本不变 | 跑 formal answer + dual judge；只有 full accuracy 和风险同时可接受才升 LTS |
| 2 | #1 granularity/profile generalization + #2/#3 context pressure | v140 清除 profile 分支并降低 LME avg context chars 到 `18940.848`，但 LME strict/lenient `0.794/0.826` 低于 v127 | 重做 retrieval/context organization，避免 v139/v140 这种损覆盖的 compiler pressure |
| 3 | src cleanup | `src` 审计显示暂无可整模块删除的 tracked 代码；`repair.py`、rerank、turn-window 和 guide 逻辑仍有消融或 guardrail 价值 | 后续随实验节奏拆小 `compiler.py` / `pipeline.py`，删除确认无用的兼容分支，不删仍有验证价值的模块 |

## 保留候选

| 配置/文档 | 类型 | 关键结果 | 决策 |
|---|---|---|---|
| `configs/stage1_superseded_source_chain_v127_qwen36_no_think_build4k_cached.json` | current LTS | fresh full dual judge：LME strict/lenient `0.820000/0.832000`，LoCoMo `0.789610/0.815584` | 当前本地 LTS；降低 #5 的 source-backed update organization 风险，并继承 #4/#3 风险收敛；#5 broad lifecycle/state/conflict/reasoning、#1/#2 保留为优先风险 |
| `configs/stage1_route_scoped_local_evidence_unit_v125_qwen36_no_think_build4k_cached.json` | previous LTS | LoCoMo temporal paired dual judge strict/lenient `0.772189/0.786982 -> 0.792899/0.813609`；full route-only strict/lenient `0.789610/0.807792`；LME 兼容继承 v116 `0.812000/0.834000` | 被 v127 替代：v127 在保持 clean/source-backed 机制的同时降低 #5 build-memory organization 风险，后续 fresh full 结果确认当前 LTS 口径 |
| `configs/stage1_route_scoped_fact_profile_state_budget_v129_qwen36_no_think_build4k_cached.json` | token-budget | LME full route-only exact `0.428000 -> 0.430000`；LoCoMo `0.244156 -> 0.245455` | Narrow positive diagnostic；作为 v134 父对照 |
| `configs/stage1_memory_source_interleave_v126_qwen36_no_think_build4k_cached.json` | memory organization | LoCoMo profile/current paired dual `+4/+4`，LME profile/current `-1/-1` | 被 v127 继承和修正；保留为 ablation |
| `configs/stage1_source_grounded_guard_v121_qwen36_no_think_build4k_cached.json` | clean/general cleanup | 收窄 broad mechanical finalizer 为 source-grounded consistency guard；不宣称提分 | 保留为风险收敛改动 |
| `configs/stage1_long_profile_profile_state_selected_context_v128_qwen36_no_think_build4k_cached.json` | structure audit | LME profile/current prompt 只变 `37/500`，exact 持平；LoCoMo `0/1540` 变化 | 保留为 selected-context generalization 证据 |
| `diagnostic/stage1_build_memory_usage_trace_audit_v126_plan.md` | memory audit | v116 LoCoMo `1539/1540` 有 memory hits 且有 memory-projected source 进入最终 rows | 结论：瓶颈是 source-backed evidence organization，不是完全没用 memory |

## 拒绝记录

这里只保留近期会影响下一步决策的负向结论；完整负向链见 `diagnostic/stage1_v102_generalization_audit_v104_plan.md` 和 git 历史。

| 配置 | 原因 |
|---|---|
| `stage1_memory_version_chain_v144_qwen36_no_think_build4k_cached.json` | source-backed version-chain row ordering 只改 `current_state/profile_preference`，不把 typed memory text 当 reader evidence。Compile scope 合理：LME changed `31/500`、LoCoMo changed `50/1540`，几乎不增 context。但 full dual judge：LME strict/lenient `0.812000/0.840000`，LoCoMo `0.785714/0.811688`；LoCoMo 低于 fresh v127 `0.789610/0.815584`，不升 LTS。保留为 #5 state/version ablation。 |
| `stage1_scoped_memory_state_guide_v142_qwen36_no_think_build4k_cached.json` | scoped state guide 比 v141 收窄。相对 fresh v127，LME strict `408/500` 低于 `410/500`、lenient `418/500` 高于 `416/500`，但 LoCoMo strict/lenient `1208/1540` / `1242/1540` 均低于 v127 `1216/1540` / `1256/1540`。结论：作为 #5 阶段性诊断保留，不升统一 LTS；下一步做更完整的 conflict/as-of state、version chain 和 query-time memory reasoning。 |
| `stage1_memory_state_guide_v141_qwen36_no_think_build4k_cached.json` | #5 方向正确但 dry-run scope 太宽：source-linked state guide 在 LME `218/500`、LoCoMo `932/1540` prompts 出现，avg context chars `20436.048/18313.279`；主要被 fact_lookup 大面积触发，暂不 formal，下一版收窄 |
| `stage1_route_gated_context_pressure_v140_qwen36_no_think_build4k_cached.json` | route-gated 修正比 v139 略恢复，LME full dual strict/lenient `0.790/0.818 -> 0.794/0.826`，且 profile 分支清零、avg context chars 降到 `18940.848`；但仍低于 fresh v127 LME `0.820/0.832`，multi-session strict/lenient 只有 `0.714/0.759`，不跑 LoCoMo，不升 LTS |
| `stage1_temporal_local_evidence_signal_gate_v135_qwen36_no_think_build4k_cached.json` | 对 `temporal_lookup` neighbor 做硬 signal gate，scope clean 但 paired dual judge 负向。Prompt-changed-only merge vs v125：strict/lenient `0.792899/0.813609 -> 0.781065/0.798817`，净 strict `-4`、lenient `-5`；典型损失是删掉弱词面但关键的相邻时间锚，导致信息不足或错年/错日期 |
| `stage1_query_context_budget_v136_qwen36_no_think_build4k_cached.json` / `stage1_budget_aware_selected_context_v137_qwen36_no_think_build4k_cached.json` / `stage1_tighter_context_budget_v138_qwen36_no_think_build4k_cached.json` | v136 no-profile + context_budget 方向正确但 LME selected_context 重新打开；v137 修掉 selected_context 膨胀但 avg context chars 仍为 `20244.338`；v138 raw estimate 降到 `15292.94`，但 compiler/context chars 仍未降 |
| `stage1_context_pressure_compiler_v139_qwen36_no_think_build4k_cached.json` | dry-run 降低 LME context chars 到 `17601.658`，但 LME full dual judge strict/lenient 只有 `0.790/0.818`，低于 fresh v127 LME `0.820/0.832`；by-type 诊断显示 multi-session 明显受损 |
| `stage1_fact_tail_snippet_budget_v134_qwen36_no_think_build4k_cached.json` | token 降低但 paired dual judge 负向；LoCoMo fact subset strict/lenient `0.819728/0.833333 -> 0.807256/0.824263`，净 strict `-11`、lenient `-8` |
| `stage1_fact_tail_filter_preserve_order_v132_qwen36_no_think_build4k_cached.json` | hard row pruning 虽降 query 到 `5115.770`，但 LoCoMo fact exact `0.249433 -> 0.241497`，full exact `0.245455 -> 0.240909` |
| `stage1_long_profile_profile_state_selected_context_v128_qwen36_no_think_build4k_cached.json` | 不是 accuracy candidate；changed subset avg query `6480.730`，只作审计证据 |

## 历史 LTS

| 配置 | LTS 期间关键结果 | 替代原因 |
|---|---|---|
| `configs/stage1_extended_selected_context_v116_qwen36_no_think_build4k_cached.json` | LME strict/lenient `0.812000/0.834000`；LoCoMo strict/lenient `0.779221/0.807143` | 被 v125 替代：v125 继承 LME 兼容证据，降低 #4 mechanical finalizer 风险，部分降低 #3 selected-context heuristic 风险，并提升 LoCoMo temporal paired judge 与 full route-only strict。 |
| `configs/stage1_route_scoped_local_evidence_unit_v125_qwen36_no_think_build4k_cached.json` | LME inherited strict/lenient `0.812000/0.834000`；LoCoMo route-only strict/lenient `0.789610/0.807792` | 被 v127 替代：v127 继承 v125 的 #4/#3 风险收敛，并加入 source-backed active/superseded memory organization；fresh full v127 作为当前 LTS 口径。 |
| `configs/stage1_spacing_profile_v102_qwen36_no_think_build4k_cached.json` | LME strict/lenient `0.814000/0.830000`；LoCoMo strict/lenient `0.776623/0.798052` | 被 v116 替代：v116 保持 LME 达标，并把 LoCoMo lenient 推到 baseline target 以上。 |

## 关键 Formal Run

完整 run 细节在 `experiments/formal/<run_id>/`；本表只保留当前 LTS、直接父对照和基准入口。

| run | 作用 |
|---|---|
| `stage1_superseded_source_chain_v127_lme_s_full_fresh` | 当前 LTS fresh full；strict/lenient `0.820000/0.832000` |
| `stage1_superseded_source_chain_v127_locomo_nonadv_full_fresh` | 当前 LTS fresh full；strict/lenient `0.789610/0.815584` |
| `stage1_memory_version_chain_v144_lme_s_full` | v144 #5 source-backed version-chain row ordering formal；strict/lenient `0.812000/0.840000`，mixed vs v127 |
| `stage1_memory_version_chain_v144_locomo_nonadv_full` | v144 #5 source-backed version-chain row ordering formal；strict/lenient `0.785714/0.811688`，低于 fresh v127，故不升 LTS |
| `stage1_scoped_memory_state_guide_v142_lme_s_full` | v142 #5 scoped state guide formal；strict/lenient `0.816000/0.836000` |
| `stage1_scoped_memory_state_guide_v142_locomo_nonadv_full` | v142 #5 scoped state guide formal；strict/lenient `0.784416/0.806494`，低于 fresh v127，故不升 LTS |
| `stage1_extended_selected_context_v116_qwen36_no_think_build4k_lme_s_full_aeac792` | previous LTS；strict/lenient `0.812000/0.834000` |
| `stage1_extended_selected_context_v116_qwen36_no_think_build4k_locomo_nonadv_full_aeac792` | previous LTS；strict/lenient `0.779221/0.807143` |
| `stage1_spacing_profile_v102_qwen36_no_think_build4k_lme_s_full_4fc01c0` | qwen3.6 no-thinking v102 LME 对照 |
| `stage1_spacing_profile_v102_qwen36_no_think_build4k_locomo_nonadv_full_1526d1c` | qwen3.6 no-thinking v102 LoCoMo 对照 |
| `stage1_naive_rag_top40_external_lme_s_full_224aa42` | clean naive RAG LME baseline |
| `stage1_naive_rag_top40_external_locomo_nonadv_full_49de2d2_w2` | clean naive RAG LoCoMo baseline |

历史证明链和负向 formal run 细节见对应 run 目录与 `experiments/diagnostic/stage1_v102_generalization_audit_v104_plan.md`。

## Diagnostic 索引

| 文档/目录 | 作用 |
|---|---|
| `diagnostic/stage1_fact_tail_snippet_budget_v134_summary.md` | v133/v134 tail text budget 诊断 |
| `diagnostic/stage1_temporal_local_evidence_signal_gate_v135_analysis/` | v135 dry-run scope comparison and decision notes |
| `diagnostic/stage1_temporal_local_evidence_signal_gate_v135_locomo_temporal_route_all/manual_diagnosis.md` | v135 temporal paired judge rejection diagnosis |
| `diagnostic/stage1_fact_tail_filter_preserve_order_v132_summary.md` | v132 hard row pruning 负向诊断 |
| `diagnostic/stage1_route_scoped_fact_profile_state_budget_v129_summary.md` | v129 route-scoped char budget 诊断 |
| `diagnostic/stage1_route_scoped_local_evidence_unit_v125_lme_dry/` | v125 LongMemEval compiler compatibility dry-run |
| `diagnostic/stage1_route_scoped_local_evidence_unit_v125_locomo_temporal_route_all/temporal_gain_loss_badcase_analysis.md` | v125 temporal paired judge gain/loss badcase 分析 |
| `diagnostic/stage1_route_scoped_local_evidence_unit_v125_locomo_nonadv_full_route_only_merge/` | v125 LoCoMo full route-only merge dual judge 指标 |
| `diagnostic/stage1_route_scoped_local_evidence_unit_v125_lts_promotion.md` | v125 LTS 晋升决策记录 |
| `diagnostic/stage1_superseded_source_chain_v127_lts_promotion.md` | v127 LTS 晋升决策记录 |
| `diagnostic/stage1_long_profile_profile_state_selected_context_v128_summary.md` | v128 selected-context generalization 审计 |
| `diagnostic/stage1_superseded_source_chain_v127_summary.md` | v127 superseded source chain 诊断 |
| `diagnostic/stage1_memory_source_interleave_v126_profile_state_summary.md` | v126 profile/current source interleave 诊断 |
| `diagnostic/stage1_scoped_memory_state_guide_v142_badcase_summary.md` | v142 formal 后 LoCoMo gain/loss 聚合和 #5 下一步约束 |
| `diagnostic/stage1_memory_slot_chain_v145_scope_summary.md` | v145 retrieval-time memory slot chain scope 结论：触发范围窄、成本基本不变，进入 formal |
| `diagnostic/stage1_memory_version_chain_v144_scope_summary.md` | v144 source-backed version-chain row ordering scope/formal 结论：结构更 clean，但 accuracy 不升 LTS |
| `diagnostic/stage1_global_update_conflict_v143_scope_probe_summary.md` | v143 方向 probe：全局 update/conflict guide 对 LoCoMo 为 no-op，未成正式版本 |
| `diagnostic/src_cleanup_audit_20260618.md` | v142 后 src 清理审计：确认暂无可安全删除的整模块 |
| `diagnostic/stage1_build_memory_usage_trace_audit_v126_plan.md` | build memory 使用方式审计 |
| `diagnostic/stage1_v102_generalization_audit_v104_plan.md` | v102 generalization 风险与 v104-v134 累积诊断日志 |
| `diagnostic/judge_protocol_audit_20260617.md` | dual `deepseek-v4-flash` judge 协议审计 |
| `diagnostic/v116_finalizer_impact/` | v116 finalizer 影响诊断 |
| `diagnostic/v121_source_grounded_guard_lme_finalizer_applied_8/` | v121 source-grounded guard smoke |

## 输出路径

```text
outputs/formal/<run_id>/predictions.jsonl
outputs/formal/<run_id>/traces.jsonl
outputs/diagnostic/<run_id>/predictions.jsonl
outputs/diagnostic/<run_id>/traces.jsonl
```

`outputs/cache/` 只保留近期复现 LTS 和关键 baseline 所需的 embedding/build/answer cache。cache 命中只减少本地重复 API 调用；`avg_build_tokens` / `avg_query_tokens` 仍按逻辑冷启动 visible LLM token 记录。

## 评估规则

- 主指标：dual `deepseek-v4-flash` judge。`strict_accuracy` 表示两遍都正确；`lenient_accuracy` 表示任一遍正确。
- LoCoMo judge prompt 只允许输出 `CORRECT` 或 `WRONG`。
- judge 只能用于离线评测，不能进入 prediction、retrieval、compiler、answer、verifier 或 cache build。
- LongMemEval-S full：500 条。
- LoCoMo non-adversarial full：1540 条。
- 正式实验必须记录 commit、dirty 状态、配置、benchmark/subset、token 成本、outputs 路径和诊断结论。
- 新方法必须另起版本和 cache namespace，不能复用 LTS answer cache 证明新方法。
- 任何使用 gold answer、judge output、benchmark 标签、sample id、row index、test feedback 或样本级规则的预测逻辑都不允许进入项目。
