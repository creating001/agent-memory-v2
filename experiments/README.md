# 实验入口

`experiments/` 是人工查看正式结果和关键诊断的入口。当前目录已按 LTS 收尾整理：只保留当前 LTS 证据链、split best、强 baseline、关键转折点和最新负向诊断。旧负向探索的细节不再长期堆目录；重要结论保留在本文件和 git 历史中。

## 当前 LTS

| 项目 | 结果 |
|---|---|
| LTS 配置 | `configs/stage1_spacing_profile_v102_cached.json` |
| 算法口径 | 同一套 raw-memory-granularity adaptive 算法；短 turn 恢复 v96 prompt spacing，长 turn 保持 v98 precision branch；不使用 benchmark 标签、gold、judge、sample id、row index 或测试反馈。 |
| LongMemEval-S full | `400/500 = 0.800000`，与 v98/v88 prediction 完全一致。 |
| LoCoMo non-adversarial full | `1232/1540 = 0.800000`，与 v96 prediction 完全一致。 |
| token | LME avg build/query `80346.246 / 5912.794`；LoCoMo avg build/query `58386.008 / 5496.281`。 |
| 状态 | 统一算法达到 baseline target；未来探索另起版本，当前项目暂时固定为 LTS。 |

## Split Best

| Benchmark | run | accuracy | 说明 |
|---|---|---:|---|
| LongMemEval-S full | `formal/stage1_spacing_profile_v102_lme_s_full_f844921` | `0.800000` | 当前统一 LTS LME；与 v98/v88 prediction 完全一致。 |
| LoCoMo non-adversarial full | `formal/stage1_spacing_profile_v102_locomo_nonadv_full_f844921` | `0.800000` | 当前统一 LTS LoCoMo；与 v96 prediction 完全一致。 |

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

## 保留 Diagnostic Runs

| run | 作用 |
|---|---|
| `diagnostic/stage1_prompt_discipline_v100_lme_stratified_120_f844921` | 负向诊断：全 route prompt discipline 伤 LongMemEval-S，不跑全量。 |
| `diagnostic/stage1_short_turn_candidate_anchor_v101_locomo_stratified_200_f844921` | 负向诊断：短 turn source-anchor/candidate-guide 伤 LoCoMo，不跑全量。 |
| `diagnostic/stage1_granularity_adaptive_v99_locomo_route_stratified_200_6c5bdf4` | 历史负向诊断：宽泛 short-answer boundary 在 route-stratified 200 上明显负向，后续不要走单纯“更短答案”方向。 |

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

`outputs/cache/` 只保留近期复现 LTS 和关键 baseline 所需的 embedding/build/answer cache。cache 命中只减少本地重复 API 调用；`avg_build_tokens` / `avg_query_tokens` 仍按逻辑冷启动 LLM token 记录。

## 评估口径

- 主指标：DeepSeek judge accuracy。
- `exact / F1 / BLEU` 只作为低成本诊断，不作为方法选择依据。
- LongMemEval-S full：500 条。
- LoCoMo non-adversarial full：1540 条。
- 正式实验必须记录 commit、dirty 状态、配置、benchmark/subset、token 成本、outputs 路径和诊断结论。

## 清理规则

- 顶层只保留有复现或对比价值的 run；负向探索如果已有结论且不支撑当前 LTS，可以删除目录。
- 新方法必须另起版本和 cache namespace，不能复用 LTS answer cache 证明新方法。
- 任何使用 gold answer、judge output、benchmark 标签、sample id、row index、test feedback 或样本级规则的预测逻辑都不允许进入项目。
