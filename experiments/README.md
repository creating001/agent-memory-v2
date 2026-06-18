# 实验入口

`experiments/` 是正式结果和关键诊断的人类可读入口。详细证据保留在各 run 目录、`summary.md`、`diagnosis.md`、`metrics.json` 和 `manifest.json` 中；本文件只维护稳定索引和当前决策。

## 当前 LTS

| 项目 | 结果 |
|---|---|
| 当前 LTS 配置 | `configs/stage1_extended_selected_context_v116_qwen36_no_think_build4k_cached.json` |
| Backbone | `Qwen/Qwen3.6-35B-A3B` answer/build，`chat_template_kwargs.enable_thinking=false` |
| 方法 | V116 extended selected context；继承 v110 modal-only grounded inference，只扩展短 turn selected-context 后向邻域 |
| LongMemEval-S full | strict/lenient `0.812000 / 0.834000` |
| LoCoMo non-adversarial full | strict/lenient `0.779221 / 0.807143` |
| 状态 | 当前 qwen3.6 no-thinking LTS；两个 benchmark 使用同一算法。LME avg query tokens `6140.218` 略高于 6K normal target，LoCoMo avg query tokens `5956.221` 在 6K 内。 |

## 口径说明

- `v101` 及之前默认属于 `Qwen/Qwen3-30B-A3B-Instruct-2507` 历史探索。
- 当前主线是 `Qwen/Qwen3.6-35B-A3B` no-thinking；只有名称显式带 `qwen36_no_think_build4k` 的记录才按当前 backbone 对比。
- `agent-memory-other` / `agent-memory-gpt` 是外部测试目录，不作为主项目 LTS 结果来源。
- `exact / F1 / BLEU` 只作为低成本诊断和 badcase 定位；算法是否成立、是否升级 LTS，只看 dual `deepseek-v4-flash` judge strict/lenient。
- 新 LTS 必须同时满足：相对当前 LTS 或直接父对照风险点更少，并且 paired/full dual judge accuracy 更好。只省 token、只减少风险但不提分、或只有 lexical 正向，都不能替代 LTS。

## 优先待办

| 优先级 | 项目 | 当前状态 | 下一步 |
|---:|---|---|---|
| 1 | `v125` temporal local evidence unit | LoCoMo temporal subset lexical exact `0.186391 -> 0.215976`，full route-only exact `0.236364 -> 0.242857` | 补 temporal subset paired dual judge；若主指标正向，再考虑 full route-only judge |
| 2 | `v126` profile/current memory source interleave | LoCoMo profile/current route-all exact `0.320000 -> 0.360000`；full route-only exact 高于 v125 | 补 paired dual judge；若 LME judge 不正向则停止 |
| 3 | `v127` superseded source chain | LME full route-only lexical exact `0.426000 -> 0.428000`；LoCoMo exact 持平、F1/BLEU 小升 | 补 paired dual judge，并重点看 update/profile badcase |
| 4 | `v129` route-scoped char budget | LME/LoCoMo full route-only lexical 小正向；LoCoMo changed-subset query 仍 `6112.337` | 作为 token-budget 对照保留；优先级低于 evidence organization 候选 |

## 保留候选

| 配置/文档 | 类型 | 关键结果 | 决策 |
|---|---|---|---|
| `configs/stage1_route_scoped_fact_profile_state_budget_v129_qwen36_no_think_build4k_cached.json` | token-budget | LME full route-only exact `0.428000 -> 0.430000`；LoCoMo `0.244156 -> 0.245455` | Narrow positive diagnostic；作为 v134 父对照 |
| `configs/stage1_route_scoped_local_evidence_unit_v125_qwen36_no_think_build4k_cached.json` | temporal context | 只改变 LoCoMo temporal prompts `338/338`；route-only full exact `0.236364 -> 0.242857` | Promising diagnostic；待 judge |
| `configs/stage1_memory_source_interleave_v126_qwen36_no_think_build4k_cached.json` | memory organization | LoCoMo profile/current exact `0.320000 -> 0.360000`；LME exact 持平但 F1/BLEU 轻降 | Narrow diagnostic；待 judge |
| `configs/stage1_superseded_source_chain_v127_qwen36_no_think_build4k_cached.json` | memory/state chain | LME full route-only exact `0.426000 -> 0.428000`；LoCoMo exact 持平、F1/BLEU 小升 | Narrow diagnostic；待 judge |
| `configs/stage1_source_grounded_guard_v121_qwen36_no_think_build4k_cached.json` | clean/general cleanup | 收窄 broad mechanical finalizer 为 source-grounded consistency guard；不宣称提分 | 保留为风险收敛改动 |
| `configs/stage1_long_profile_profile_state_selected_context_v128_qwen36_no_think_build4k_cached.json` | structure audit | LME profile/current prompt 只变 `37/500`，exact 持平；LoCoMo `0/1540` 变化 | 保留为 selected-context generalization 证据 |
| `diagnostic/stage1_build_memory_usage_trace_audit_v126_plan.md` | memory audit | v116 LoCoMo `1539/1540` 有 memory hits 且有 memory-projected source 进入最终 rows | 结论：瓶颈是 source-backed evidence organization，不是完全没用 memory |

## 拒绝记录

| 配置 | 原因 |
|---|---|
| `stage1_fact_tail_snippet_budget_v134_qwen36_no_think_build4k_cached.json` | token 降低但 paired dual judge 负向；LoCoMo fact subset strict/lenient `0.819728/0.833333 -> 0.807256/0.824263`，净 strict `-11`、lenient `-8` |
| `stage1_fact_tail_snippet_budget_v133_qwen36_no_think_build4k_cached.json` | 过保守；LoCoMo fact avg context 只降 `8.552` chars，full avg context 只降 `4.898` chars |
| `stage1_fact_tail_filter_preserve_order_v132_qwen36_no_think_build4k_cached.json` | hard row pruning 虽降 query 到 `5115.770`，但 LoCoMo fact exact `0.249433 -> 0.241497`，full exact `0.245455 -> 0.240909` |
| `stage1_conservative_fact_tail_source_interleave_v131_qwen36_no_think_build4k_cached.json` | dry-run 仍主要是 order-only prompt drift，没有 context benefit |
| `stage1_fact_source_interleave_budget_v130_qwen36_no_think_build4k_cached.json` | dry-run order-only drift 过大，没有 context benefit |
| `stage1_long_profile_profile_state_selected_context_v128_qwen36_no_think_build4k_cached.json` | 不是 accuracy candidate；changed subset avg query `6480.730`，只作审计证据 |
| `stage1_local_evidence_unit_v124_qwen36_no_think_build4k_cached.json` | LoCoMo changed `1536/1540`，avg context `+2101.65`，过宽 |
| `stage1_aggregation_contract_v123_qwen36_no_think_build4k_cached.json` | LME list_count strict/lenient `0.848739/0.873950 -> 0.815126/0.840336` |
| `stage1_per_row_selected_context_v122_qwen36_no_think_build4k_cached.json` | LME selected_context applied `317/500`，大范围改变 prompt 并压缩 raw evidence rows |
| `stage1_rerank_filter_v120_qwen36_no_think_build4k_cached.json` | list/count tail filtering 降 token 但损 coverage；LME/LoCoMo route-all 均负向 |
| `stage1_inline_memory_hint_v119_qwen36_no_think_build4k_cached.json` | source-linked memory hint 直接进 reader prompt 造成净负 |
| `stage1_source_manifest_candidate_guide_v118_qwen36_no_think_build4k_cached.json` | prompt-side source manifest 成本高，LoCoMo list-count smoke 负向 |
| `stage1_no_relative_time_finalizer_v113_qwen36_no_think_build4k_cached.json` | 在 v110 路径上 answer text `0` change，是 no-op |
| `stage1_evidence_unit_rerank_v112_qwen36_no_think_build4k_cached.json` | LME strict/lenient `0.810000/0.828000`，低于 v102/v110/v116 |
| `stage1_modal_abstention_repair_v111_qwen36_no_think_build4k_cached.json` | LME strict 升但 lenient 降：`0.812000/0.834000 -> 0.816000/0.828000` |
| `stage1_grounded_inference_v109_qwen36_no_think_build4k_cached.json` | LME lenient 低于 v102，停止不跑 LoCoMo |
| `stage1_source_coverage_v108_qwen36_no_think_build4k_cached.json` | LME strict/lenient `0.802000/0.824000`，source-anchor coverage 不准 |
| `stage1_route_scoped_memory_activation_v107_qwen36_no_think_build4k_cached.json` | LME/LoCoMo lenient 持平但 strict 略低，不作为 LTS |
| `stage1_memory_activation_v106_qwen36_no_think_build4k_cached.json` | activation-only 仍低于 v102 且 query token 增加 |
| `stage1_memory_activation_v105_qwen36_no_think_build4k_cached.json` | typed memory activation + `memory_aware` ordering 降低 raw coverage，大幅负向 |
| `stage1_context_guard_v104_qwen36_no_think_build4k_cached.json` | LME single flash `0.790000`，avg query `7367.622`，过预算且负向 |

## Formal Run 索引

| run | 作用 |
|---|---|
| `stage1_extended_selected_context_v116_qwen36_no_think_build4k_lme_s_full_aeac792` | 当前 LME split best；strict/lenient `0.812000/0.834000` |
| `stage1_extended_selected_context_v116_qwen36_no_think_build4k_locomo_nonadv_full_aeac792` | 当前 LoCoMo split best；strict/lenient `0.779221/0.807143` |
| `stage1_spacing_profile_v102_qwen36_no_think_build4k_lme_s_full_4fc01c0` | qwen3.6 no-thinking v102 LME 对照 |
| `stage1_spacing_profile_v102_qwen36_no_think_build4k_locomo_nonadv_full_1526d1c` | qwen3.6 no-thinking v102 LoCoMo 对照 |
| `stage1_modal_grounded_inference_v110_qwen36_no_think_build4k_lme_s_full_2f33213` | v110 LME 正向候选，后续被 v116 继承 |
| `stage1_modal_grounded_inference_v110_qwen36_no_think_build4k_locomo_nonadv_full_2f33213` | v110 LoCoMo 正向候选，后续被 v116 替代 |
| `stage1_spacing_profile_v102_lme_s_full_f844921` | 历史 qwen3-30B LME 证明链 |
| `stage1_spacing_profile_v102_locomo_nonadv_full_f844921` | 历史 qwen3-30B LoCoMo 证明链 |
| `stage1_granularity_adaptive_v98_lme_s_full_7b0aab9` | v102 LME 兼容继承来源 |
| `stage1_granularity_adaptive_v98_locomo_nonadv_full_252a24b` | v98 统一候选 LoCoMo 对照 |
| `stage1_budgeted_selected_context_v96_locomo_nonadv_full_3c146bd` | v102 LoCoMo 兼容继承来源 |
| `stage1_selected_context_v95_locomo_nonadv_full_43ee885` | selected-context 正向转折点 |
| `stage1_naive_rag_top40_external_lme_s_full_224aa42` | clean naive RAG LME baseline |
| `stage1_naive_rag_top40_external_locomo_nonadv_full_49de2d2_w2` | clean naive RAG LoCoMo baseline |
| `stage1_hybrid_bm25_v18_lme_s_full_6c5ed99` | hybrid BM25+dense LME baseline |
| `stage1_hybrid_bm25_v18_locomo_nonadv_full_bb1cc3c` | hybrid BM25+dense LoCoMo baseline |
| `stage1_evidence_report_contract_v28_lme_s_full_9917c22` | LME evidence_report contract 关键提升点 |
| `stage1_temporal_event_contract_v29_locomo_nonadv_full_c7b8390` | LoCoMo temporal event/mention time 关键提升点 |
| `stage1_answer_format_guard_v35_locomo_nonadv_full_80158a9` | LoCoMo 强 baseline |
| `stage1_lme_token_safe_format_guard_v36_lme_s_full_4af3244` | LME 强 baseline |
| `stage1_update_conflict_guide_v80_lme_s_full_152b0e5` | LME update/conflict guide 关键提升点 |

负向 formal run 细节见对应 `experiments/formal/<run_id>/` 和 `experiments/diagnostic/stage1_v102_generalization_audit_v104_plan.md`。

## Diagnostic 索引

| 文档/目录 | 作用 |
|---|---|
| `diagnostic/stage1_fact_tail_snippet_budget_v134_summary.md` | v133/v134 tail text budget 诊断 |
| `diagnostic/stage1_fact_tail_filter_preserve_order_v132_summary.md` | v132 hard row pruning 负向诊断 |
| `diagnostic/stage1_route_scoped_fact_profile_state_budget_v129_summary.md` | v129 route-scoped char budget 诊断 |
| `diagnostic/stage1_long_profile_profile_state_selected_context_v128_summary.md` | v128 selected-context generalization 审计 |
| `diagnostic/stage1_superseded_source_chain_v127_summary.md` | v127 superseded source chain 诊断 |
| `diagnostic/stage1_memory_source_interleave_v126_profile_state_summary.md` | v126 profile/current source interleave 诊断 |
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
