# 实验入口

`experiments/` 是人工查看正式结果和关键诊断的入口。目录保持精简：只长期保留当前主线、强 baseline 和少数关键转折点；旧 smoke、小样本、负向探索和 partial judge 文件不长期保留。

## 主要指标

方法好坏主要看离线 DeepSeek judge accuracy。

- LongMemEval-S full：500 条。
- LoCoMo non-adversarial full：1540 条。
- `exact / F1 / BLEU` 只作为低成本诊断，不作为方法选择依据。

`avg_build_tokens` 表示在新环境中按当前方法构建 memory 需要消耗的逻辑 LLM token；cache 命中只能减少本机重复 API 调用，不能把方法成本记为 0。`avg_query_tokens` 表示 query/answer 阶段 LLM token。embedding 和 judge token 单独记录，不混入 prediction 的 build/query。

## 当前主线

保留配置：

- `configs/stage1_clean_skeleton.json`：最小骨架和单元测试入口。
- `configs/stage1_naive_rag_top40_external.json`：clean naive RAG 强 baseline。
- `configs/stage1_source_expansion_v12_cached.json`：build-stage typed memory 只做 raw source expansion 的关键对照。
- `configs/stage1_structured_evidence_guide_v14_cached.json`：structured evidence guide 关键对照。
- `configs/stage1_hybrid_bm25_v18_cached.json`：hybrid BM25+dense 强 baseline。
- `configs/stage1_structured_answer_contract_v26_cached.json`：structured answer contract 关键对照。
- `configs/stage1_evidence_report_contract_v28_cached.json`：当前 LME 最好主线候选，也是 v29 的底座。

方法摘要：

- build 阶段由本地 Qwen LLM 从 raw dialogue 中构建 typed memory，类型包括 event、fact、preference、profile、state、relationship、plan。
- memory manager 记录 source/provenance、去重、轻量 supersede、active/superseded 状态和 cache。
- query 阶段同时检索 raw turns、session context 和 typed memory source links。
- retrieval 当前主线是 raw-turn dense + BM25 hybrid top-40，并允许 typed memory 命中的 raw source turn 回链。
- compiler 将 raw evidence、temporal aid、structured guide 和可见 `evidence_report` 组织给 answer model。
- DeepSeek judge 只在预测完成后离线使用。

当前结论：

- LongMemEval-S full 当前最好为 v28：0.766 DeepSeek judge accuracy，383/500；距 0.80 baseline target 仍差 17 条。
- LoCoMo non-adversarial full 当前最高为 v29：0.761688，1173/1540；距 0.78 baseline target 仍差约 28 条。
- v28/v29 token gate 均通过：v28 LME avg_build_tokens 80346.246、avg_query_tokens 5736.928；v29 LoCoMo avg_build_tokens 58386.008、avg_query_tokens 3932.560。
- LoCoMo 诊断显示，很多 wrong case 已有 evidence 进入 context，主要问题是 answer 阶段混淆 mention date / event time、列表边界和隐含推理；下一步应改 build/query 两侧的 memory organization，而不是继续只堆 answer prompt。
- v29 temporal event contract 已完成双基准验证：LME `0.762`，低于 v28 `0.766`；LoCoMo `0.761688`，显著高于 v28 `0.737662` 但仍未达 `0.78` target。结论是 event-time 组织对 LoCoMo 有价值，但需要前移到 build-side typed memory，不能只靠 query prompt。

负向探索结论已压缩保留：

- answer-side route guidance、LLM retrieval planner、session anchor、source-map-only guide、count finalizer、frontloaded temporal aid 等都没有形成全量 clean 提升，旧目录已删除。
- 如果后续要重跑旧方法，应从保留的 key config / formal `config_snapshot.json` 出发重新生成，不把旧输出堆在主目录。

## 正式实验目录

正式全量实验使用：

```text
experiments/formal/<run_id>/
```

每个保留的正式实验目录必须包含：

- `summary.md`
- `metrics.json`
- `diagnosis.md`
- `manifest.json`
- `config_snapshot.json`
- 离线 judge 结果
- 预测 outputs 路径

必须记录：

- git commit 和 dirty 状态
- config
- benchmark/subset
- token 成本，尤其 build/query tokens
- build memory cache、records、memory hits
- runner workers / 并行度
- outputs 路径
- accuracy-first 诊断结论

如果必须做子集，只能标成 diagnostic，并优先按 question-derived information need 分层采样；不能把前 N 条子集当正式结论。

## 保留正式结果

| run | benchmark | subset | commit | accuracy | 主要结论 |
|---|---|---|---|---:|---|
| `stage1_evidence_report_contract_v28_lme_s_full_9917c22` | LongMemEval-S | full | `9917c22` | 0.766000 | 当前 LME 最好；vs v18 净 +17，vs v26 净 +10；仍未达 0.80。 |
| `stage1_temporal_event_contract_v29_lme_s_full_23e8b78` | LongMemEval-S | full | `23e8b78` | 0.762000 | v28 上的 temporal event contract query-side ablation；temporal_lookup 净 +2，但 current_state/list_count 回退，整体低于 v28。 |
| `stage1_temporal_event_contract_v29_locomo_nonadv_full_c7b8390` | LoCoMo | non-adversarial full | `c7b8390` | 0.761688 | 当前 LoCoMo 最好；主要收益来自 temporal_lookup/category 2，仍未达 0.78。 |
| `stage1_evidence_report_contract_v28_locomo_nonadv_full_ee13e22` | LoCoMo | non-adversarial full | `ee13e22` | 0.737662 | v29 前 LoCoMo 最好；只比 v18 多 1 条，是 v29 的关键对照。 |
| `stage1_hybrid_bm25_v18_lme_s_full_6c5ed99` | LongMemEval-S | full | `6c5ed99` | 0.732000 | 强 baseline；dense+BM25+build source expansion 的稳定底座。 |
| `stage1_hybrid_bm25_v18_locomo_nonadv_full_bb1cc3c` | LoCoMo | non-adversarial full | `bb1cc3c` | 0.737013 | LoCoMo 强 baseline；v28 基本与其持平。 |
| `stage1_naive_rag_top40_external_lme_s_full_224aa42` | LongMemEval-S | full | `224aa42` | 0.688000 | clean naive RAG baseline；用于证明 build/retrieval 增益。 |
| `stage1_naive_rag_top40_external_locomo_nonadv_full_49de2d2_w2` | LoCoMo | non-adversarial full | `49de2d2` | 0.698506 | clean naive RAG baseline；v18/v28 比它高约 60 条。 |
| `stage1_source_expansion_v12_lme_s_full_9ad6e03` | LongMemEval-S | full | `9ad6e03` | 0.714000 | build-stage typed memory 只做 raw source expansion 有正收益。 |
| `stage1_source_expansion_v12_locomo_nonadv_full_3235553` | LoCoMo | non-adversarial full | `3235553` | 0.698701 | LoCoMo 上 source expansion 基本持平，说明不能盲目扩 evidence。 |
| `stage1_structured_evidence_guide_v14_lme_s_full_bc04642` | LongMemEval-S | full | `bc04642` | 0.704000 | structured guide 在 LME 负向，提示 context organization 需选择性。 |
| `stage1_structured_evidence_guide_v14_locomo_nonadv_full_f48cf10` | LoCoMo | non-adversarial full | `f48cf10` | 0.735714 | LoCoMo 上曾显著正向，是后续 evidence organization 的关键线索。 |
| `stage1_structured_answer_contract_v26_lme_s_full_eecb206` | LongMemEval-S | full | `eecb206` | 0.746000 | v28 前 LME 最好；structured answer contract 有效但有回退。 |
| `stage1_structured_answer_contract_v26_locomo_nonadv_full_c21ef84` | LoCoMo | non-adversarial full | `c21ef84` | 0.729870 | LoCoMo 负向；说明 LME reader 约束不能直接泛化。 |

## 外部方法覆盖

外部方法代码覆盖和已读文件见：

```text
experiments/method_coverage.md
```

新方法设计必须说明参考了哪些外部代码、采用了什么、舍弃了什么，以及为什么仍满足 clean protocol。
