# 配置入口

`configs/` 只保留当前主线、强 baseline 和关键对照配置。旧负向探索配置不长期保留；正式实验目录里的 `config_snapshot.json` 负责历史追溯。

## 保留配置

- `stage1_clean_skeleton.json`：无 LLM smoke / 单元测试级骨架配置，也是 `scripts/run_stage1.py` 的默认配置。
- `stage1_naive_rag_top40_external.json`：对齐外部 clean naive RAG 的强 baseline，raw-turn dense top-40 + Date/role/query-time formatting + JSON answer extraction。
- `stage1_source_expansion_v12_cached.json`：build-stage typed memory 只作为 raw source turn 扩展入口，不把 summary 当唯一事实来源；用于验证 build memory 的基础收益。
- `stage1_structured_evidence_guide_v14_cached.json`：在 v13 基础上增加 structured evidence guide，是 LoCoMo evidence organization 的关键正向对照。
- `stage1_hybrid_bm25_v18_cached.json`：在 selective row guide 上加入 raw-turn BM25 lexical retrieval，与 dense top-40 和 build-memory source expansion 融合；当前强 baseline。
- `stage1_structured_answer_contract_v26_cached.json`：在 v18 上增加 route-scoped structured answer contract，关闭不稳定 count finalizer；LME 正向、LoCoMo 负向，是 reader 约束的重要对照。
- `stage1_evidence_report_contract_v28_cached.json`：当前主线候选，在 v18 上增加可见 `evidence_report` contract，要求 answer model 先整理 support / exclude / missing 证据再输出最终答案。

## 新配置规则

- 不使用 gold answer、judge output、benchmark label、sample id、qid、row index 或 test feedback。
- 关键开关显式写入配置，便于 ablation。
- 如果只是一次负向诊断，不长期保留配置文件；结论写入 `experiments/README.md` 或对应实验记录即可。
- 正式实验必须把实际运行配置保存到 `experiments/formal/<run_id>/config_snapshot.json`。
