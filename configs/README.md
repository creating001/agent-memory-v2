# 配置入口

`configs/` 只保留当前 LTS、当前 split best、强 baseline 和已保留正式实验支撑的关键对照。负向探索和无保留实验目录支撑的中间配置不长期保留；需要复现时从 git 历史回溯。

## 当前默认配置

| 用途 | 配置 | 状态 |
|---|---|---|
| 后续新实验默认配置 | `stage1_spacing_profile_v102_qwen36_no_think_build4k_cached.json` | V102 算法 + `Qwen/Qwen3.6-35B-A3B` answer/build backbone；请求级 `chat_template_kwargs.enable_thinking=false`；build `max_tokens=4096`，answer `max_output_tokens=16384`；使用独立 qwen36 no-thinking cache namespace。 |
| 已拒绝诊断候选 | `stage1_no_relative_time_finalizer_v113_qwen36_no_think_build4k_cached.json` | 继承 v110 modal-only grounded inference，只关闭全局 relative-time mechanical finalizer。v102 finalizer-impact 离线诊断显示 LoCoMo relative-time 改写在触发样本上从 draft lenient `40/46` 降到 final `34/46`，但 v110 LoCoMo 路径中该 finalizer 已实际触发 `0` 次；v113 相比 v110 LME/LoCoMo answer text 分别 changed `0/500` 和 `0/1540`，因此拒绝为 no-op。 |
| 已拒绝诊断候选 | `stage1_evidence_unit_rerank_v112_qwen36_no_think_build4k_cached.json` | 在 v110 正向候选基础上加入 Qwen3-Reranker-0.6B evidence-unit rerank；LME full strict/lenient `0.810000 / 0.828000`，低于 v102 和 v110，停止，不跑 LoCoMo full。诊断显示真实 changed-answer gain/loss `11/12`，multi-session 与 temporal coverage 受损。 |
| 已拒绝诊断候选 | `stage1_modal_abstention_repair_v111_qwen36_no_think_build4k_cached.json` | 在 v110 基础上增加 source-grounded modal abstention repair；只在 modal/inference 问题的最终 draft answer 明确拒答/信息不足时触发 verifier。Smoke 有局部收益，但 LongMemEval-S full strict/lenient `0.816000 / 0.828000`，主指标低于 v102 `0.830000` 和 v110 `0.834000`，停止，不跑 LoCoMo full。 |
| 正向但未达标候选 | `stage1_modal_grounded_inference_v110_qwen36_no_think_build4k_cached.json` | v109 收窄 ablation：只在 modal yes/no inference 问题触发 grounded inference discipline，排除 plain advice/recommendation `what do you think` 负例；LME strict/lenient `0.812000 / 0.834000`，LoCoMo strict/lenient `0.779221 / 0.799351`，LoCoMo lenient 距 `0.800000` 还差 1 题，暂不替代 v102 LTS。 |
| 已拒绝诊断候选 | `stage1_grounded_inference_v109_qwen36_no_think_build4k_cached.json` | v108 后的新方向：不改 retrieval/build/finalizer，只在 question-text modal/inference 问题上加入 grounded inference discipline；LME full strict/lenient `0.816000 / 0.828000`，主指标低于 v102 `0.830000`，停止，不跑 LoCoMo full。 |
| 已拒绝诊断候选 | `stage1_source_coverage_v108_qwen36_no_think_build4k_cached.json` | v107 后的新方向：typed memory 不进入 reader prompt，只作为 source-linked coverage signal；LME full strict/lenient `0.802000 / 0.824000`，低于 v102，停止，不跑 LoCoMo full。 |
| 诊断候选 | `stage1_route_scoped_memory_activation_v107_qwen36_no_think_build4k_cached.json` | v106 route 诊断后的隔离 ablation：只在 question-derived `fact_lookup` / `profile_preference` 打开 source-aligned typed memory activation；LME lenient 与 v102 持平、strict 略低；LoCoMo lenient 与 v102 持平、strict 略低，不作为 LTS。 |
| 已拒绝诊断候选 | `stage1_memory_activation_v106_qwen36_no_think_build4k_cached.json` | v105 负向后的隔离 ablation：保留 source-aligned typed memory activation guide，但恢复 v102 `evidence_order=retrieval`；LME full strict/lenient `0.806000 / 0.820000`，仍低于 v102 `0.814000 / 0.830000`，不跑 LoCoMo full。 |
| 已拒绝诊断候选 | `stage1_memory_activation_v105_qwen36_no_think_build4k_cached.json` | 在当前 qwen3.6 no-thinking v102 LTS 上打开 source-aligned typed memory activation guide，并用 `memory_aware` raw-row ordering；LME full strict/lenient `0.774000 / 0.800000`，低于 v102 `0.814000 / 0.830000`，不跑 LoCoMo full。下一步只测试 activation，不改变 v102 retrieval order。 |
| 已拒绝诊断候选 | `stage1_context_guard_v104_qwen36_no_think_build4k_cached.json` | 移除大块 granularity profile 切换；selected context 改为 per-turn `max_center_chars`；关闭 mechanical finalizer，启用 source-grounded repair guardrail；LME full 负向且 query token 过高，不作为 LTS。 |
| 历史 qwen3-30b 参考 | `stage1_spacing_profile_v102_cached.json` | `Qwen/Qwen3-30B-A3B-Instruct-2507` backbone；LongMemEval-S / LoCoMo non-adversarial full 单次 flash accuracy 均为 `0.800000`。旧 backbone，不作为当前 qwen3.6 dual flash target 判断。 |

说明：

- qwen3.6 no-thinking v102 已在主目录 formal rerun 并按 dual flash judge 重算：LongMemEval-S strict/lenient `0.814000 / 0.830000`，LoCoMo strict/lenient `0.776623 / 0.798052`。`agent-memory-other` 只作为测试目录，不作为主项目 LTS 来源。
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
- v110 同样复用 v102 build-memory cache，因为 build/retrieval 全部未改；v110 answer cache 使用独立 `qwen36_no_think_build4k_answer_v110_modal_grounded_inference.sqlite`。正式 run 前用 v102 traces + v102 predictions seed 相同 prompt 的 prediction-time final answers；不读取 labels/judge/category/sample id，不再用 v109 traces 覆盖未改 prompt。v110 是当前正向候选，不是默认 LTS。
- v111 同样复用 v102 build-memory cache，base answer cache 使用独立 `qwen36_no_think_build4k_answer_v111_modal_abstention_repair.sqlite`，可从 v110 traces + predictions seed；repair cache 使用 `qwen36_no_think_build4k_answer_repair_v111_modal_abstention.sqlite`。repair trigger 只看 prediction-time question/draft answer/Memory Context，不读取 labels/judge/category/sample id。
- v112 同样复用 v102 build-memory cache，因为 build 阶段未改；answer cache 使用独立 `qwen36_no_think_build4k_answer_v112_evidence_unit_rerank.sqlite`。rerank 只读 question text、raw turns、same-session neighbors 和 build-memory source links，不读取 labels/judge/category/sample id。
- v113 同样复用 v102 build-memory cache，因为 build/retrieval/compiler/backbone 全部未改；answer cache 使用独立 `qwen36_no_think_build4k_answer_v113_no_relative_time_finalizer.sqlite`。正式 run 前可从 v110 prediction traces seed 相同 prompt 的 base answer cache；预测阶段不读取 labels/judge/category/sample id。

## 当前 Split Best

| Benchmark | 配置 | 结果 | 用途 |
|---|---|---:|---|
| LongMemEval-S full | `stage1_evidence_answer_detail_v88_cached.json` | `400/500 = 0.800000` | LME split best，v98 长 turn 分支与其 prediction 完全一致。 |
| LoCoMo non-adversarial full | `stage1_budgeted_selected_context_v96_cached.json` | `1232/1540 = 0.800000` | LoCoMo split best；单独优于 v98，但不是双基准统一算法。 |

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

## 使用规则

- 新主线配置必须显式记录关键开关、cache path 和 cache namespace。
- 任何 prompt、answer parsing、finalizer、repair、retrieval 或 build-memory 改动都必须另起版本，不要复用 LTS answer cache 证明新方法。
- 正式实验必须保存 `config_snapshot.json`、`summary.md`、`metrics.json`、`diagnosis.md`、`manifest.json`，并记录 commit、dirty 状态、benchmark/subset、token 成本和 outputs 路径。
