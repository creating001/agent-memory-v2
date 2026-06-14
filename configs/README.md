# 配置入口

`configs/` 只保留当前主线、强 baseline 和关键对照配置。旧负向探索配置不长期保留；正式实验目录里的 `config_snapshot.json` 负责历史追溯。

## 保留配置

- `stage1_clean_skeleton.json`：无 LLM smoke / 单元测试级骨架配置，也是 `scripts/run_stage1.py` 的默认配置。
- `stage1_naive_rag_top40_external.json`：对齐外部 clean naive RAG 的强 baseline，raw-turn dense top-40 + Date/role/query-time formatting + JSON answer extraction。
- `stage1_source_expansion_v12_cached.json`：build-stage typed memory 只作为 raw source turn 扩展入口，不把 summary 当唯一事实来源；用于验证 build memory 的基础收益。
- `stage1_structured_evidence_guide_v14_cached.json`：在 v13 基础上增加 structured evidence guide，是 LoCoMo evidence organization 的关键正向对照。
- `stage1_hybrid_bm25_v18_cached.json`：在 selective row guide 上加入 raw-turn BM25 lexical retrieval，与 dense top-40 和 build-memory source expansion 融合；当前强 baseline。
- `stage1_structured_answer_contract_v26_cached.json`：在 v18 上增加 route-scoped structured answer contract，关闭不稳定 count finalizer；LME 正向、LoCoMo 负向，是 reader 约束的重要对照。
- `stage1_evidence_report_contract_v28_cached.json`：v36 前 LME 最好主线，在 v18 上增加可见 `evidence_report` contract，要求 answer model 先整理 support / exclude / missing 证据再输出最终答案。
- `stage1_temporal_event_contract_v29_cached.json`：v33 前 LoCoMo 最强主线，针对 temporal route 显式区分 `mention_time` 与 `event_time`；也是 v32 query-side repair 的底座。
- `stage1_selective_repair_v32_cached.json`：v29 draft answer 后只对运行时高风险样本触发 clean LLM verifier/repair；token 合格但 LoCoMo full 与 v29 持平。
- `stage1_retrieval_top60_v33_cached.json`：在 v29 底座上把 raw-turn dense+BM25 retrieval/compiler evidence budget 从 top-40 扩到 top-60；LoCoMo 正向但 temporal_lookup 回退。
- `stage1_route_budgeted_retrieval_v34_cached.json`：v33 的 route-budgeted 版本；非 temporal 保留 top60，temporal_lookup 回到 top40，v35 前 LoCoMo 最好。
- `stage1_answer_format_guard_v35_cached.json`：v34 上的 answer format guard；修复 JSON answer salvage 和小数 duration，当前 LoCoMo 最好。
- `stage1_lme_token_safe_format_guard_v36_cached.json`：v28 top40/evidence budget + v35 answer guard；v42 前 LME 最好，也是当前强 baseline。
- `stage1_operation_workpad_v42_cached.json`：v36 上的短 operation workpad；不新增 LLM 调用，不改 retrieval/build，只在 `list_count` / `temporal_lookup` 的 evidence_report prompt 中加入通用操作聚合纪律。v73 前 LongMemEval-S full 最好，但仅比 v36 净 +1，属于 close-margin 小幅正向。
- `stage1_lossless_build8k_r20_v74_cached.json`：build-side 容量消融；基于 v73/v42，不改 retrieval/compiler/answer/finalizer，只把 build extraction 切到 `lossless_atomic`，build 输出上限放到 8K，record 容量保持 20。
- `stage1_lossless_build8k_r40_v75_cached.json`：build-side 容量消融；在 v74 基础上把每 chunk record 容量从 20 放到 40，用于判断 record capacity 是否带来收益或噪声。

## 当前候选

当前 build-side 候选按两步验证：

1. `stage1_lossless_build8k_r20_v74_cached.json`：先只把 build 输出上限从 2048 放到 8192，并使用 `lossless_atomic` prompt，但 record 容量保持 20，验证是否主要受输出截断影响。
2. `stage1_lossless_build8k_r40_v75_cached.json`：再把 record 容量放到 40，验证更多 atomic memory 是否提升 source activation，还是带来 retrieval/context 噪声。

正式结果必须同时报告 build token、record 数、query token、accuracy 和 cache 命中。

`stage1_finalizer_duration_fix_v73_cached.json`：从 v42 出发，只关闭机械 duration decimal rounding finalizer。badcase 显示该 finalizer 在 LongMemEval-S full 中唯一一次触发时，把 answer model 正确草稿 `3.5 weeks` 改成 `4 weeks`。v73 不改 retrieval/build/prompt，使用 v42 answer cache 做 query/finalizer 侧消融；LongMemEval-S full DeepSeek judge `0.778`，当前 LME 最好，但还未达到 `0.80` baseline target。

v71 temporal-order router 已完成 LongMemEval-S full：accuracy `0.770`，低于 v42 修复控制 `0.772`；seeded cache 控制后 prediction_changed `11/500`，changed subset `WRONG->CORRECT 1`、`CORRECT->WRONG 1`，整体中性。结论是 route-only 修正不足，顶层 config 和 src route 改动撤出主线，只保留 formal 快照。v70 route snippet compact 已完成 LongMemEval-S full：accuracy `0.758`，低于 v42 修复控制 `0.772`；seeded cache 控制后 prediction_changed `26/500`，changed subset `CORRECT->WRONG 13`、`WRONG->CORRECT 3`，主要损失来自 `list_count`。结论是纯 query snippet 压缩负向，顶层 config 删除，只保留 formal 快照。v69 supported-uncertain repair 已完成 LongMemEval-S full：full judge `0.760`，低于 v42 修复控制 `0.772`；实际改动 6 条中 `WRONG->CORRECT 2`、`WRONG->WRONG 4`，但 full judge 重跑受 same-answer variance 影响明显。结论是局部小正向但不足以作为主线，顶层 config 删除，只保留 formal 快照。v67/v68 preliminary supported-uncertain repair 因 full avg query tokens 略超 6K，不作为主线配置保留。v66 route-aware context budget 已完成 LongMemEval-S full：query token 明显下降但 accuracy 低于 v42，顶层 config 删除，只保留 formal 快照。v65 unit/sum mechanical finalizer 已完成 LongMemEval-S full：accuracy 低于 v42，且不是纯 finalizer 正向消融；顶层 config 和源码分支删除，只保留 formal 快照。v64 list_count-only adjacent-turn window BM25 也已验证负向，只保留 diagnostic 快照。

负向诊断只保留在对应 `experiments/diagnostic/<run_id>/config_snapshot.json` 中，不保留顶层 config。

## 新配置规则

- 不使用 gold answer、judge output、benchmark label、sample id、qid、row index 或 test feedback。
- 关键开关显式写入配置，便于 ablation。
- 如果只是一次负向诊断，不长期保留配置文件；结论写入 `experiments/README.md` 或对应实验记录即可。
- 正式实验必须把实际运行配置保存到 `experiments/formal/<run_id>/config_snapshot.json`。
- 任何会影响 prompt、answer parsing、finalizer 或 repair 的改动，都不能默认复用旧 answer cache 来证明等价；需要更换 cache namespace，或显式做 prediction-level 复现对比并记录结论。
