# 配置入口

`configs/` 只保留当前 LTS、当前 split best、强 baseline 和已保留正式实验支撑的关键对照。负向探索和无保留实验目录支撑的中间配置不长期保留；需要复现时从 git 历史回溯。

## 当前默认配置

| 用途 | 配置 | 状态 |
|---|---|---|
| 后续新实验默认配置 | `stage1_spacing_profile_v102_qwen36_no_think_build4k_cached.json` | V102 算法 + `Qwen/Qwen3.6-35B-A3B` answer/build backbone；请求级 `chat_template_kwargs.enable_thinking=false`；build `max_tokens=4096`，answer `max_output_tokens=16384`；使用独立 qwen36 no-thinking cache namespace。 |
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
