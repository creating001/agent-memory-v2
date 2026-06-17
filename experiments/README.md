# 实验入口

`experiments/` 是人工查看正式结果和关键诊断的入口。当前目录已按 LTS 收尾整理：只保留当前 LTS 证据链、split best、强 baseline、关键转折点和最新负向诊断。旧负向探索的细节不再长期堆目录；重要结论保留在本文件和 git 历史中。

## 当前默认实验配置

| 项目 | 结果 |
|---|---|
| 默认配置 | `configs/stage1_spacing_profile_v102_qwen36_no_think_build4k_cached.json` |
| Answer / build LLM | `Qwen/Qwen3.6-35B-A3B`，请求级 `chat_template_kwargs.enable_thinking=false`。 |
| 继承算法 | V102 raw-memory-granularity adaptive；retrieval/compiler/finalizer 行为与 V102 一致，build 上限为 `4096`。 |
| qwen3.6 no-thinking full 结果 | 正在主目录重跑 v102 formal prediction + dual judge；完成后以主目录结果作为 LTS，不再直接引用 `agent-memory-other` 测试目录数字。 |
| 状态 | 作为后续新实验默认配置；v102 主目录复现完成前，qwen3.6 LTS 数字暂不固化。 |

## 当前诊断候选

| 项目 | 结果 |
|---|---|
| 配置 | `configs/stage1_context_guard_v104_qwen36_no_think_build4k_cached.json` |
| 目的 | 移除按全样本平均 turn 长度的大块 profile 切换；selected context 改为 per-turn `max_center_chars`；关闭 mechanical finalizer，启用 source-grounded repair guardrail。 |
| 结果 | LongMemEval-S full strict/lenient `0.772000 / 0.806000`，avg query tokens `7367.622`，answer repair 触发 `178/500`；过预算且未形成 LTS 提升，已停止，不跑 LoCoMo full。 |
| 诊断文档 | `diagnostic/stage1_v102_generalization_audit_v104_plan.md` |

## 已验证历史 LTS

| 项目 | 结果 |
|---|---|
| LTS 配置 | `configs/stage1_spacing_profile_v102_cached.json` |
| 算法口径 | 同一套 raw-memory-granularity adaptive 算法；短 turn 恢复 v96 prompt spacing，长 turn 保持 v98 precision branch；不使用 benchmark 标签、gold、judge、sample id、row index 或测试反馈。 |
| LongMemEval-S full | strict `386/500 = 0.772000`，lenient `403/500 = 0.806000`；flash 单 judge 为 `400/500 = 0.800000`。 |
| LoCoMo non-adversarial full | strict `1195/1540 = 0.775974`，lenient `1267/1540 = 0.822727`；flash 单 judge 为 `1232/1540 = 0.800000`。 |
| token | LME avg build/query `80346.246 / 5912.794`；LoCoMo avg build/query `58386.008 / 5496.281`。 |
| 状态 | 统一算法按 lenient dual judge 达到 baseline target；strict 是更保守的下界。这是历史验证结果，backbone 是 `Qwen/Qwen3-30B-A3B-Instruct-2507`。 |

## Split Best

| Benchmark | run | accuracy | 说明 |
|---|---|---:|---|
| LongMemEval-S full | `formal/stage1_spacing_profile_v102_lme_s_full_f844921` | strict `0.772000` / lenient `0.806000` | 当前统一 LTS LME；与 v98/v88 prediction 完全一致。 |
| LoCoMo non-adversarial full | `formal/stage1_spacing_profile_v102_locomo_nonadv_full_f844921` | strict `0.775974` / lenient `0.822727` | 当前统一 LTS LoCoMo；与 v96 prediction 完全一致。 |

## 保留 Formal Runs

| run | 作用 |
|---|---|
| `stage1_spacing_profile_v102_lme_s_full_f844921` | 当前 LTS LongMemEval-S 证明链。 |
| `stage1_spacing_profile_v102_locomo_nonadv_full_f844921` | 当前 LTS LoCoMo 证明链。 |
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
| `dual_judge_reassessment_20260617.md` | dual judge 正式口径、LTS strict/lenient 和历史 backbone/embedding 对比重算记录。 |
| `stage1_rerank_context_v103_lme_s_full_f9fae4b` | qwen3.6 no-thinking v103 负结果：LME strict/lenient `0.780 / 0.818`，低于 qwen3.6 v102 `0.806 / 0.844`；说明单 turn rerank + 强裁剪不是当前主线。 |
| `stage1_context_guard_v104_lme_s_full_043795e` | qwen3.6 no-thinking v104 负结果：LME strict/lenient `0.772 / 0.806`，avg query tokens `7367.622`；说明粗暴取消 profile + broad answer repair 不适合作为 LTS。 |

## 保留 Diagnostic Runs

| run | 作用 |
|---|---|
| `diagnostic/stage1_prompt_discipline_v100_lme_stratified_120_f844921` | 负向诊断：全 route prompt discipline 伤 LongMemEval-S，不跑全量。 |
| `diagnostic/stage1_short_turn_candidate_anchor_v101_locomo_stratified_200_f844921` | 负向诊断：短 turn source-anchor/candidate-guide 伤 LoCoMo，不跑全量。 |
| `diagnostic/stage1_granularity_adaptive_v99_locomo_route_stratified_200_6c5bdf4` | 历史负向诊断：宽泛 short-answer boundary 在 route-stratified 200 上明显负向，后续不要走单纯“更短答案”方向。 |
| `diagnostic/stage1_v102_generalization_audit_v104_plan.md` | 当前结构审计：granularity/profile、selected context、mechanical finalizer、top-k/noise 和 build-memory 使用方式；提出 v104 诊断候选。 |

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

- 主指标：DeepSeek dual judge accuracy。strict accuracy 表示 `deepseek-v4-flash` 和 `deepseek-v4-pro` 都判对；lenient accuracy 表示任一 judge 判对。
- flash/pro 单模型 accuracy 只作为诊断指标，不再作为唯一主指标。
- `exact / F1 / BLEU` 只作为低成本诊断，不作为方法选择依据。
- LongMemEval-S full：500 条。
- LoCoMo non-adversarial full：1540 条。
- 正式实验必须记录 commit、dirty 状态、配置、benchmark/subset、token 成本、outputs 路径和诊断结论。

## 清理规则

- 顶层只保留有复现或对比价值的 run；负向探索如果已有结论且不支撑当前 LTS，可以删除目录。
- 新方法必须另起版本和 cache namespace，不能复用 LTS answer cache 证明新方法。
- 任何使用 gold answer、judge output、benchmark 标签、sample id、row index、test feedback 或样本级规则的预测逻辑都不允许进入项目。
