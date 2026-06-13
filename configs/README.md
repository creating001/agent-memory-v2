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
- `stage1_operation_workpad_v42_cached.json`：v36 上的短 operation workpad；不新增 LLM 调用，不改 retrieval/build，只在 `list_count` / `temporal_lookup` 的 evidence_report prompt 中加入通用操作聚合纪律。当前 LongMemEval-S full 最好，但仅比 v36 净 +1，属于 close-margin 小幅正向。

## 当前候选

- `stage1_temporal_session_guide_v45_cached.json`：v44 后的进一步 token-safe 收窄版本；只对 `temporal_lookup` 打开 session-thread evidence layout 和 1 条 row-linked build memory guide，非 temporal prompt 与 v42 等价。待 gate，通过前不视为保留主线。

## 新配置规则

- 不使用 gold answer、judge output、benchmark label、sample id、qid、row index 或 test feedback。
- 关键开关显式写入配置，便于 ablation。
- 如果只是一次负向诊断，不长期保留配置文件；结论写入 `experiments/README.md` 或对应实验记录即可。
- 正式实验必须把实际运行配置保存到 `experiments/formal/<run_id>/config_snapshot.json`。
