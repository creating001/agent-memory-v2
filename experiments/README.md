# 实验入口

`experiments/` 是人工查看正式结果和关键诊断的入口。当前目录已按 LTS 收尾整理：只保留当前 LTS 证据链、split best、强 baseline、关键转折点和最新负向诊断。旧负向探索的细节不再长期堆目录；重要结论保留在本文件和 git 历史中。

## 当前默认实验配置

| 项目 | 结果 |
|---|---|
| 默认配置 | `configs/stage1_spacing_profile_v102_qwen36_no_think_build4k_cached.json` |
| Answer / build LLM | `Qwen/Qwen3.6-35B-A3B`，请求级 `chat_template_kwargs.enable_thinking=false`。 |
| 继承算法 | V102 raw-memory-granularity adaptive；retrieval/compiler/finalizer 行为与 V102 一致，build 上限为 `4096`。 |
| qwen3.6 no-thinking full 结果 | LongMemEval-S strict/lenient `0.814000 / 0.830000`；LoCoMo strict/lenient `0.776623 / 0.798052`。这是主目录 formal rerun + dual flash judge 结果，不引用 `agent-memory-other` 测试目录数字。 |
| 状态 | 当前默认 LTS；两个 benchmark 使用同一算法。按 dual flash lenient judge，LME 达到当前 baseline target，LoCoMo 距 `80%` baseline target 还差 4 题。LME avg query tokens `6137.344`，略高于 6K normal target，是后续优化点。 |

## Backbone 口径说明

- `v101` 及之前的探索默认是 `Qwen/Qwen3-30B-A3B-Instruct-2507` 口径，属于历史 qwen3-30b 探索。
- 当前默认 LTS 是 `Qwen/Qwen3.6-35B-A3B` no-thinking 口径；只有 run/config 名称显式带 `qwen36_no_think_build4k` 的记录才属于这个新 backbone。
- 不要把 v101 及之前的 qwen3-30b 数字与 qwen3.6 no-thinking 数字直接当作同 backbone 方法对比。
- `agent-memory-other` / `agent-memory-gpt` 是外部测试目录，不作为主项目 LTS 结果来源。

## 当前正向候选

| 项目 | 结果 |
|---|---|
| 配置 | `configs/stage1_modal_grounded_inference_v110_qwen36_no_think_build4k_cached.json` |
| 目的 | v109 收窄 ablation：保留 `would/might/could/likely/considered` 等 modal yes/no inference 的 grounded inference discipline，排除 plain advice/recommendation `what do you think` 负例。 |
| 结果 | LongMemEval-S strict/lenient `0.812000 / 0.834000`；LoCoMo strict/lenient `0.779221 / 0.799351`。相比 v102，LME lenient `+2`、LoCoMo lenient `+2`；但 LoCoMo 距 `0.800000` 还差 1 题，暂不替代 v102 LTS。 |
| 诊断 | v110 实际改变 prompt/answer 的样本集中在 modal inference；LoCoMo Open-Domain(category 3) lenient `45/96 -> 54/96`，但 Multi-Hop/Temporal/Single-Hop 有小幅抵消。 |
| 诊断文档 | `diagnostic/stage1_v102_generalization_audit_v104_plan.md` |

## 下一正式候选

| 项目 | 结果 |
|---|---|
| 配置 | `configs/stage1_modal_abstention_repair_v111_qwen36_no_think_build4k_cached.json` |
| 目的 | 在 v110 基础上增加 source-grounded modal abstention verifier，只修正“modal/inference 问题 + draft 明确信息不足”的过度拒答。 |
| Smoke | LoCoMo 11 个 v110 modal-abstention wrong 子集从 `0/11` 到 strict/lenient `3/11`；LME 2 个触发子集从 `0/2` 到 lenient `1/2`。Smoke 目录已清理，结论记录在 `diagnostic/stage1_v102_generalization_audit_v104_plan.md`。 |
| 计划 | 先提交 v111 代码/config，正式跑 LongMemEval-S full；若 LME 不低于 v110/v102 主口径，再跑 LoCoMo full。 |

## 已拒绝上下文候选

| 项目 | 结果 |
|---|---|
| 配置 | `configs/stage1_context_guard_v104_qwen36_no_think_build4k_cached.json` |
| 目的 | 移除按全样本平均 turn 长度的大块 profile 切换；selected context 改为 per-turn `max_center_chars`；关闭 mechanical finalizer，启用 source-grounded repair guardrail。 |
| 结果 | LongMemEval-S full 单次 flash `395/500 = 0.790000`，avg query tokens `7367.622`，answer repair 触发 `178/500`；过预算且未形成 LTS 提升，已停止，不跑 LoCoMo full。 |
| 诊断文档 | `diagnostic/stage1_v102_generalization_audit_v104_plan.md` |

## 最新负向候选

| 项目 | 结果 |
|---|---|
| 配置 | `configs/stage1_grounded_inference_v109_qwen36_no_think_build4k_cached.json` |
| 目的 | 保持 v102 build/retrieval/granularity/selected context/finalizer 不变，只在 question-text modal/inference 问题上加入 grounded inference discipline，尝试减少 LoCoMo Open-Domain 过度拒答。 |
| 结果 | LongMemEval-S full strict/lenient `0.816000 / 0.828000`；strict 比 v102 高 1 题，但主指标 lenient 比 v102 `0.830000` 低 1 题。触发 prompt `7/500`，触发样本 lenient gain/loss `1/1`。负向/不确定，停止，不跑 LoCoMo full。 |
| 诊断结论 | 通用 inference discipline 可以减少一个过度拒答，但也把一个有用 personalized advice 改成 abstention；下一步应区分 grounded yes/no inference 与 advice/recommendation，或做可拒绝的 abstention verifier。 |
| 配置 | `configs/stage1_source_coverage_v108_qwen36_no_think_build4k_cached.json` |
| 目的 | typed memory 不进入 reader prompt，只作为 source-linked coverage signal；对 `fact_lookup` / `profile_preference` / `current_state` 使用 source-anchor coverage，temporal/list 维持 v102。 |
| 结果 | LongMemEval-S full strict/lenient `0.802000 / 0.824000`，低于 v102 `0.814000 / 0.830000`；avg query tokens `6195.524`。负向，停止，不跑 LoCoMo full。 |
| 诊断结论 | 现有 build memory source links 作为 row coverage signal 仍偏噪，fact_lookup 净损失；v102 保持 LTS。 |

## 已拒绝候选补充

| 项目 | 结果 |
|---|---|
| 配置 | `configs/stage1_route_scoped_memory_activation_v107_qwen36_no_think_build4k_cached.json` |
| 目的 | 只在 question-derived `fact_lookup` / `profile_preference` 打开 source-aligned typed memory activation，避免 v106 在 temporal/list 上的负向。 |
| LME 结果 | strict/lenient `0.810000 / 0.830000`，lenient 与 v102 持平，strict 低 2 题；avg query tokens `6308.482`。 |
| LoCoMo 结果 | strict/lenient `0.774675 / 0.798052`，lenient 与 v102 持平，strict 低 3 题；Multi-Hop `+7`、Open-Domain `+3`，但 Temporal `-7`、Single-Hop `-3` 抵消。 |
| 诊断结论 | route-scoped activation 有局部有效信号，但直接放进 reader prompt 仍不稳定；v102 保持 LTS。 |
| 配置 | `configs/stage1_memory_activation_v106_qwen36_no_think_build4k_cached.json` |
| 目的 | v105 负向后的隔离 ablation：只保留 source-aligned typed memory activation guide，恢复 v102 `evidence_order=retrieval`，不改变 raw-row ordering。 |
| 结果 | LongMemEval-S full strict/lenient `0.806000 / 0.820000`，低于 v102 `0.814000 / 0.830000`；avg query tokens `6638.526`。负向，停止，不跑 LoCoMo full。 |
| 诊断结论 | activation-only 恢复了 v102 的 evidence rows，但直接暴露 typed memory guide 仍带来 token/noise；下一步不要继续直接把 typed memory 作为 reader prompt guide。 |
| 配置 | `configs/stage1_memory_activation_v105_qwen36_no_think_build4k_cached.json` |
| 目的 | 在 qwen3.6 no-thinking v102 LTS 上打开 source-aligned typed memory activation guide，并用 `memory_aware` raw-row ordering，验证 build memory 是否能从“辅助检索”升级为 query-time organization signal。 |
| 结果 | LongMemEval-S full strict/lenient `0.774000 / 0.800000`，低于 v102 `0.814000 / 0.830000`；avg query tokens `6614.138`，avg evidence rows 从 v102 `34.752` 降到 `24.528`。负向，停止，不跑 LoCoMo full。 |
| 诊断结论 | `memory_aware` ordering 让多证据聚合题过早丢 raw rows；下一步只测试 typed memory activation，不改变 v102 retrieval order。 |

## 历史 qwen3-30b 参考

| 项目 | 结果 |
|---|---|
| 配置 | `configs/stage1_spacing_profile_v102_cached.json` |
| 算法口径 | 同一套 raw-memory-granularity adaptive 算法；短 turn 恢复 v96 prompt spacing，长 turn 保持 v98 precision branch；不使用 benchmark 标签、gold、judge、sample id、row index 或测试反馈。 |
| LongMemEval-S full | 单次 flash judge `400/500 = 0.800000`。 |
| LoCoMo non-adversarial full | 单次 flash judge `1232/1540 = 0.800000`。 |
| token | LME avg build/query `80346.246 / 5912.794`；LoCoMo avg build/query `58386.008 / 5496.281`。 |
| 状态 | 历史参考结果，backbone 是 `Qwen/Qwen3-30B-A3B-Instruct-2507`；`v101` 及之前均按 qwen3-30b 历史探索理解，不作为当前 qwen3.6 dual flash target 判断。 |

## Split Best

| Benchmark | run | accuracy | 说明 |
|---|---|---:|---|
| LongMemEval-S full | `formal/stage1_spacing_profile_v102_qwen36_no_think_build4k_lme_s_full_4fc01c0` | strict `0.814000` / lenient `0.830000` | 当前 qwen3.6 no-thinking LTS LME；judge 为 dual `deepseek-v4-flash`。 |
| LoCoMo non-adversarial full | `formal/stage1_spacing_profile_v102_qwen36_no_think_build4k_locomo_nonadv_full_1526d1c` | strict `0.776623` / lenient `0.798052` | 当前 qwen3.6 no-thinking LTS LoCoMo；LoCoMo judge prompt 为 single-label `CORRECT/WRONG`，judge 为 dual `deepseek-v4-flash`。 |

## 保留 Formal Runs

| run | 作用 |
|---|---|
| `stage1_spacing_profile_v102_lme_s_full_f844921` | 历史 qwen3-30b LongMemEval-S 证明链。 |
| `stage1_spacing_profile_v102_locomo_nonadv_full_f844921` | 历史 qwen3-30b LoCoMo 证明链。 |
| `stage1_spacing_profile_v102_qwen36_no_think_build4k_lme_s_full_4fc01c0` | 当前 qwen3.6 no-thinking LTS LongMemEval-S 主目录 rerun。 |
| `stage1_spacing_profile_v102_qwen36_no_think_build4k_locomo_nonadv_full_1526d1c` | 当前 qwen3.6 no-thinking LTS LoCoMo 主目录 rerun；judge 使用 single-label prompt。 |
| `stage1_granularity_adaptive_v98_lme_s_full_7b0aab9` | v102 LME 兼容继承来源。 |
| `stage1_granularity_adaptive_v98_locomo_nonadv_full_252a24b` | v98 统一候选，LoCoMo 差 9 题的对照。 |
| `stage1_evidence_answer_detail_v88_lme_s_full_55b8177` | 历史 v88 LME judge 来源。 |
| `stage1_evidence_answer_detail_v88_spacing_fix_lme_s_full_31abf0b` | v88 prompt/cache spacing 修复复现。 |
| `stage1_budgeted_selected_context_v96_locomo_nonadv_full_3c146bd` | v102 LoCoMo 兼容继承来源。 |
| `stage1_budgeted_selected_context_v96_lme_s_full_e04d28b` | 说明 v96 不是统一算法的关键负向对照。 |
| `stage1_selected_context_v95_locomo_nonadv_full_43ee885` | selected-context 正向转折点。 |
| `stage1_selected_context_v95_lme_s_full_790975f` | selected-context 在 LME 负向/过预算的对照。 |
| `stage1_naive_rag_top40_external_lme_s_full_224aa42` | clean naive RAG LME baseline。 |
| `stage1_naive_rag_top40_external_locomo_nonadv_full_49de2d2_w2` | clean naive RAG LoCoMo baseline。 |
| `stage1_answer_format_guard_v35_locomo_nonadv_full_80158a9` | LoCoMo 强 baseline。 |
| `stage1_lme_token_safe_format_guard_v36_lme_s_full_4af3244` | LME 强 baseline。 |
| `stage1_hybrid_bm25_v18_lme_s_full_6c5ed99` | hybrid BM25+dense LME baseline。 |
| `stage1_hybrid_bm25_v18_locomo_nonadv_full_bb1cc3c` | hybrid BM25+dense LoCoMo baseline。 |
| `stage1_evidence_report_contract_v28_lme_s_full_9917c22` | LME evidence_report contract 关键提升点。 |
| `stage1_temporal_event_contract_v29_locomo_nonadv_full_c7b8390` | LoCoMo temporal event/mention time 关键提升点。 |
| `stage1_update_conflict_guide_v80_lme_s_full_152b0e5` | LME update/conflict guide 关键提升点。 |
| `stage1_rerank_context_v103_lme_s_full_f9fae4b` | qwen3.6 no-thinking v103 负结果：LME 单次 flash `405/500 = 0.810`，低于 qwen3.6 v102 dual flash lenient `0.830` 且只换来 query token 降低；说明单 turn rerank + 强裁剪不是当前主线。 |
| `stage1_context_guard_v104_lme_s_full_043795e` | qwen3.6 no-thinking v104 负结果：LME 单次 flash `395/500 = 0.790`，avg query tokens `7367.622`；说明粗暴取消 profile + broad answer repair 不适合作为 LTS。 |
| `stage1_memory_activation_v105_qwen36_no_think_build4k_lme_s_full_d8f2b4c` | qwen3.6 no-thinking v105 负结果：LME strict/lenient `0.774/0.800`，typed memory activation + `memory_aware` ordering 降低 multi-session 覆盖，不跑 LoCoMo full。 |
| `stage1_memory_activation_v106_qwen36_no_think_build4k_lme_s_full_36c76cc` | qwen3.6 no-thinking v106 负结果：LME strict/lenient `0.806/0.820`，activation-only 仍低于 v102 且 query token 增加，不跑 LoCoMo full。 |
| `stage1_route_scoped_memory_activation_v107_qwen36_no_think_build4k_lme_s_full_12a80f2` | qwen3.6 no-thinking v107 LME：strict/lenient `0.810/0.830`，lenient 持平但 strict 低于 v102。 |
| `stage1_route_scoped_memory_activation_v107_qwen36_no_think_build4k_locomo_nonadv_full_935b7b7` | qwen3.6 no-thinking v107 LoCoMo：strict/lenient `0.774675/0.798052`，lenient 持平但 strict 低于 v102，未达到 baseline target。 |
| `stage1_source_coverage_v108_qwen36_no_think_build4k_lme_s_full_293474e` | qwen3.6 no-thinking v108 负结果：LME strict/lenient `0.802/0.824`，source-anchor coverage 低于 v102，不跑 LoCoMo full。 |
| `stage1_grounded_inference_v109_qwen36_no_think_build4k_lme_s_full_6ebbd45` | qwen3.6 no-thinking v109 负/不确定结果：LME strict/lenient `0.816/0.828`，主指标低于 v102，不跑 LoCoMo full。 |
| `stage1_modal_grounded_inference_v110_qwen36_no_think_build4k_lme_s_full_2f33213` | qwen3.6 no-thinking v110 正向候选 LME：strict/lenient `0.812/0.834`，lenient 比 v102 高 2 题但 strict 低 1 题。 |
| `stage1_modal_grounded_inference_v110_qwen36_no_think_build4k_locomo_nonadv_full_2f33213` | qwen3.6 no-thinking v110 正向候选 LoCoMo：strict/lenient `0.779221/0.799351`，lenient 比 v102 高 2 题，但仍差 1 题到 `0.800000`。 |

## 保留 Diagnostic Runs

| run | 作用 |
|---|---|
| `diagnostic/stage1_prompt_discipline_v100_lme_stratified_120_f844921` | 负向诊断：全 route prompt discipline 伤 LongMemEval-S，不跑全量。 |
| `diagnostic/stage1_short_turn_candidate_anchor_v101_locomo_stratified_200_f844921` | 负向诊断：短 turn source-anchor/candidate-guide 伤 LoCoMo，不跑全量。 |
| `diagnostic/stage1_granularity_adaptive_v99_locomo_route_stratified_200_6c5bdf4` | 历史负向诊断：宽泛 short-answer boundary 在 route-stratified 200 上明显负向，后续不要走单纯“更短答案”方向。 |
| `diagnostic/stage1_v102_generalization_audit_v104_plan.md` | 当前结构审计：granularity/profile、selected context、mechanical finalizer、top-k/noise 和 build-memory 使用方式；提出 v104 诊断候选。 |
| `diagnostic/judge_protocol_audit_20260617.md` | 当前 judge 口径审计：记录双 `deepseek-v4-flash` 正式协议，以及 LoCoMo flash repeat 稳定性。 |

## 输出路径

正式 run 的预测和 trace 在：

```text
outputs/formal/<run_id>/predictions.jsonl
outputs/formal/<run_id>/traces.jsonl
```

诊断 run 的预测和 trace 在：

```text
outputs/diagnostic/<run_id>/
```

`outputs/cache/` 只保留近期复现 LTS 和关键 baseline 所需的 embedding/build/answer cache。cache 命中只减少本地重复 API 调用；`avg_build_tokens` / `avg_query_tokens` 仍按逻辑冷启动 visible LLM token 记录。若服务端明确返回 thinking token，则单独记录 `avg_build_think_tokens` / `avg_query_think_tokens`，并用 `avg_build_total_tokens` / `avg_query_total_tokens` 表示真实 visible + think 成本。

## 评估口径

- 主指标：DeepSeek dual flash judge accuracy。`deepseek-v4-flash` 独立跑两遍，strict accuracy 表示两遍都判对；lenient accuracy 表示任一遍判对。
- LoCoMo judge prompt 只允许输出一个 label：`CORRECT` 或 `WRONG`；不要求 reasoning 或 JSON。两遍 DeepSeek flash judge 均保持 temperature `0` 和 default thinking。
- 当前记录两遍 flash 的单次 accuracy 和分歧样本，用于诊断 judge 随机分歧和 badcase；方法主指标仍是 dual flash strict/lenient。
- 单次 flash accuracy 只作为诊断指标，不再作为唯一主指标。
- `exact / F1 / BLEU` 只作为低成本诊断，不作为方法选择依据。
- LongMemEval-S full：500 条。
- LoCoMo non-adversarial full：1540 条。
- 正式实验必须记录 commit、dirty 状态、配置、benchmark/subset、token 成本、outputs 路径和诊断结论。这里的 dirty 来自 `git status --short`；如果只包含未提交的实验产物目录，应标注为 artifact-only dirty，不等同于 prediction pipeline 代码/config dirty。

## 清理规则

- 顶层只保留有复现或对比价值的 run；负向探索如果已有结论且不支撑当前 LTS，可以删除目录。
- 新方法必须另起版本和 cache namespace，不能复用 LTS answer cache 证明新方法。
- 任何使用 gold answer、judge output、benchmark 标签、sample id、row index、test feedback 或样本级规则的预测逻辑都不允许进入项目。
