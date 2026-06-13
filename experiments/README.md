# 实验入口

`experiments/` 是人工查看正式结果和关键诊断的入口。当前目录保持精简：无用 smoke、小样本、旧 ablation 结果不长期保留。

## 主要指标

方法好坏主要看离线 DeepSeek judge accuracy。

- LongMemEval-S full：500 条。
- LoCoMo non-adversarial full：1540 条。

`exact / F1 / BLEU` 只作为低成本诊断，不作为方法选择依据。

`avg_build_tokens` 表示在新环境中按当前方法构建 memory 需要消耗的逻辑 LLM token；cache 命中只能减少本机重复 API 调用，不能把方法成本记为 0。`avg_query_tokens` 表示 query/answer 阶段 LLM token。embedding 和 judge token 单独记录，不混入 prediction 的 build/query。

## 当前主线

配置：

- LongMemEval 当前最好：`configs/stage1_hybrid_bm25_v18_cached.json`
- LoCoMo 当前最好：`configs/stage1_structured_evidence_guide_v14_cached.json`

方法摘要：

- build 阶段由本地 Qwen LLM 从 raw dialogue 中构建 typed memory。
- memory 类型包括 event、fact、preference、profile、state、relationship、plan。
- memory manager 做 source/provenance 记录、去重、轻量 supersede、active/superseded 状态和 cache。
- query 阶段同时检索 raw turns、session context 和 typed memory。
- compiler 将 typed memory view 与 raw context 一起组织给 answer model。
- DeepSeek judge 只在预测完成后离线使用。
- 当前最强 baseline 是 external-aligned strict clean naive RAG：raw-turn dense top-40 + Date/role/query-time formatting + JSON answer extraction，不使用 build memory、lexical fusion 或 session expansion。
- v12 在保留 naive RAG raw dense top-40 的基础上，用 build-stage typed memory 只做 raw source expansion，不直接把 memory summary 作为唯一事实来源。
- v13 在 v12 上增加通用 temporal aid：只把 retrieved raw rows 里的相对时间短语按该 row timestamp 做日历换算，不使用 benchmark category/question_type/gold/judge/sample id 或样本实体规则。
- v14 在 v13 上增加 structured evidence guide：把 retrieved raw rows 与 activated build memory 的 source links 做 compact prompt 内索引，借鉴 A-Mem/HippoRAG/Hindsight/xMemory 的 memory neighborhood、provenance/backlink 和多视图检索思想，但不引入图数据库或 benchmark route 规则。
- v17 在 v16 row-guide-only 上做 selective row guide：对普通 fact/list/temporal 问题保留 row-level organization，对通用 personalized recommendation 信号关闭 row guide，借鉴 LangMem/Mem0/Graphiti 的 profile/preference 分层和弱推断约束。
- v18 在 v17 上增加通用 BM25 lexical + dense hybrid retrieval，借鉴 xMemory/SimpleMem/Graphiti/Hindsight 的多路检索融合，但不增加 evidence slots、不加入 LLM query planner、不使用 benchmark/sample 规则。

当前结论：

- LongMemEval-S full 当前最好为 v18 hybrid BM25：0.732 DeepSeek judge accuracy；相比 v17 净 +5，相比 v16 净 +12，相比 v13/v12 净 +9，相比 clean naive RAG 净 +22。主要收益来自通用 lexical+dense 融合对 temporal-reasoning 和 knowledge-update 的增强。
- v17 selective row guide 是 v18 的直接基线：0.722 DeepSeek judge accuracy；相比 v16 净 +7，相比 v13/v12 净 +4，相比 clean naive RAG 净 +17。主要收益来自 preference/recommendation 类更安全的 context organization。
- LoCoMo non-adversarial full 当前最好为 v14 structured evidence guide：0.735714 DeepSeek judge accuracy；相比 v13 净 +22，相比 v12 净 +57，相比 clean naive RAG 净 +58，主要收益来自 category 2/3/4 的 source-linked evidence organization。
- v17 在 LoCoMo non-adversarial full 上为 0.720779，低于 v16/v14、略低于 v13，高于 v12/naive；因此 v17 是 LME 主线，不是 LoCoMo 主线。
- v14 token gate 通过：LoCoMo avg_build_tokens 58386.008、avg_query_tokens 3818.198。build token 按逻辑冷启动成本记录，即使 build cache 全命中也计入 cached usage。
- v14 在 LongMemEval-S full 上为 0.704，低于 v12/v13 的 0.714；因此 v14 只作为 LoCoMo 当前主线和 LME 负向/混合消融，不能直接作为统一主线。
- v15 compact source-map guide 在 LME 上降到 0.686，在 LoCoMo 上为 0.720130，低于 v14 且略低于 v13；说明只保留 activated build memory source map 不足，v14 的 row-level organization 对 LoCoMo category 2 有实质作用，但会伤 LME。
- v16 row guide 在 LME 上为 0.708，在 LoCoMo 上为 0.729870；说明 row-level evidence organization 比 typed memory source map 更稳，是 v14 收益的主要来源之一，但 LME preference 退化明显，不能无条件作为统一主线。
- v17 token gate 通过：LME avg_build_tokens 80346.246、avg_query_tokens 5022.590；LoCoMo avg_build_tokens 58386.008、avg_query_tokens 3303.915。
- v13/v12 仍是重要 LME 对照：v13/v12 accuracy 均为 0.714，v12 query token 更低；LoCoMo 已被 v14 明显超过。
- v7 memory validity 在 LME 上较 v4 净提升 +5 条，和 v6 持平；avg query tokens 5858.762，接近 6K 预算。
- v7 memory validity 在 LoCoMo full 上降到 0.681818，低于 v4 的 0.695906，只比 v6 多 1 个正确；不作为 LoCoMo 主线。
- v8 组合 v6 route priority 与 v7 validity 后降到 0.600，说明两个开关没有稳定互补；不跑 LoCoMo。
- v9 evidence arbitration 降到 0.582，且 avg query tokens 6744.762 超过 6K 目标；仅 multi-session 从 v7 的 49/133 提到 56/133，可作为后续 compact/route-specific 设计线索。
- v10 compact evidence 降到 0.590，avg query tokens 6519.668 超过 6K 目标；evidence recall 0.998 且 multi-session 58/133，但整体被 assistant/preference/temporal 退化抵消，不作为主线。
- v11 selective list expansion 降到 0.594，avg query tokens 5824.768 在预算内；成本正向但 list_count 61/119 低于 v7 的 63/119，不作为主线。
- v6 route priority 是 LME clean 正向消融，但 LoCoMo full 降到 0.681611，不作为 LoCoMo 主线。
- v5 relative temporal text normalization 在 LME 上降到 0.590，不作为主线。
- v4.1 compact temporal workpad 降低 token 但 accuracy 退化，不作为主线。
- 下一步优先用 v18 跑 LoCoMo non-adversarial full；如果 v18 在 LoCoMo 不如 v14，则比较 v18/v14 错例集合，设计 general 的 selective source-linked organization，而不是 benchmark 形态的触发规则。

外部方法借鉴与取舍：

- 借鉴 LangMem 的 collection/profile 思路。
- 借鉴 Memobase 的 profile/event timeline，但不删除 raw dialogue。
- 借鉴 MIRIX 的多类型 memory taxonomy，但不引入多 agent memory OS。
- 借鉴 MemMachine 的 raw episode + profile 辅助。
- 借鉴 Graphiti/Zep 的 temporal/provenance 思路，但暂不引入重型图数据库。
- 借鉴 A-Mem 的 memory neighborhood 与 evolution links，但不把 LLM 生成链接作为唯一召回依据。
- 借鉴 HippoRAG / Hindsight 的 fact/entity link expansion、provenance 和多路检索融合，但当前阶段先做轻量 source map，不引入 heavy PPR/graph DB/query planner。
- 借鉴 xMemory 的 episode/semantic 多视图 hybrid memory，但保持 raw evidence 可追溯。

## 正式实验目录

正式全量实验使用：

```text
experiments/formal/<run_id>/
```

每个正式实验目录必须包含：

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

## 当前正式结果

| run | benchmark | subset | commit | accuracy | 主要结论 |
|---|---|---|---|---:|---|
| `stage1_hybrid_bm25_v18_lme_s_full_6c5ed99` | LongMemEval-S | full | `6c5ed99` | 0.732 | 当前 LME 最好；vs v17 净 +5，vs v16 净 +12，vs v13/v12 净 +9，vs clean naive RAG 净 +22；hybrid BM25+dense 在 token 预算内提升 temporal/knowledge 定位。 |
| `stage1_selective_row_guide_v17_lme_s_full_68b671b` | LongMemEval-S | full | `68b671b` | 0.722 | v18 的直接基线；vs v16 净 +7，vs v13/v12 净 +4，vs clean naive RAG 净 +17；profile-safe selective guide 改善 preference/recommendation。 |
| `stage1_selective_row_guide_v17_locomo_nonadv_full_68b671b` | LoCoMo | non-adversarial full | `68b671b` | 0.720779 | 非 LoCoMo 主线；低于 v16/v14、略低于 v13，但高于 v12/naive；LoCoMo 仍以 v14 为最好。 |
| `stage1_row_guide_v16_locomo_nonadv_full_5221021` | LoCoMo | non-adversarial full | `5221021` | 0.729870 | rows-only guide 高于 v13/v15/v12/naive，但低于 v14 净 -9；证明 row-level evidence organization 是主要正向来源。 |
| `stage1_row_guide_v16_lme_s_full_5221021` | LongMemEval-S | full | `5221021` | 0.708 | rows-only guide 高于 v14/v15/naive，但低于 v12/v13 净 -3；preference 退化明显，不作为 LME 主线。 |
| `stage1_source_map_guide_v15_locomo_nonadv_full_cc7f4c8` | LoCoMo | non-adversarial full | `cc7f4c8` | 0.720130 | source-map-only 低于 v14 净 -24、低于 v13 净 -2；高于 v12/naive 但主要继承 v13 收益，不作为主线。 |
| `stage1_source_map_guide_v15_lme_s_full_cc7f4c8` | LongMemEval-S | full | `cc7f4c8` | 0.686 | 负向；低于 v14 净 -9、低于 v13/v12 净 -14，也略低于 clean naive；说明 compact source map 未恢复 LME。 |
| `stage1_structured_evidence_guide_v14_locomo_nonadv_full_f48cf10` | LoCoMo | non-adversarial full | `f48cf10` | 0.735714 | 当前 LoCoMo 最好；vs v13 净 +22，vs v12 净 +57，vs clean naive RAG 净 +58；structured guide 对 category 2/3/4 正向，但 LME 同配置回退。 |
| `stage1_structured_evidence_guide_v14_lme_s_full_bc04642` | LongMemEval-S | full | `bc04642` | 0.704 | LoCoMo-positive 方法在 LME 负向；vs v13 净 -5，说明 guide 噪声会伤 knowledge-update/multi-session，不作为 LME 主线。 |
| `stage1_temporal_aid_v13_lme_s_full_8e8f070` | LongMemEval-S | full | `8e8f070` | 0.714 | v17 前 LME 并列最好；vs v12 净 0，vs clean naive RAG 净 +13；temporal aid 对 LME 无总分增益但不伤总体。 |
| `stage1_source_expansion_v12_lme_s_full_9ad6e03` | LongMemEval-S | full | `9ad6e03` | 0.714 | v17 前 LME 并列最好；build-stage typed memory 作为 raw source expansion 有明确正收益，vs clean naive RAG 净 +13；query token 低于 v13。 |
| `stage1_naive_rag_top40_external_lme_s_full_224aa42` | LongMemEval-S | full | `224aa42` | 0.688 | 强 clean baseline；对齐旧仓库 clean naive RAG 后显著高于 0.646/0.606，temporal-reasoning 提升明显。 |
| `stage1_naive_rag_top40_lme_s_full_3f40022` | LongMemEval-S | full | `3f40022` | 0.646 | 新的 LME 强 baseline；dense-only raw-turn top-40 超过 v6/v7 的 0.606，temporal/preference 仍弱。 |
| `stage1_memory_validity_v7_lme_s_full_85ddd44_cached` | LongMemEval-S | full | `85ddd44` | 0.606 | memory validity / route-specific superseded retrieval 正向；与 v6 持平，较 v4 +5，query token 接近 6K。 |
| `stage1_route_priority_v6_lme_s_full_a387f79_cached` | LongMemEval-S | full | `a387f79` | 0.606 | 早期 LME 对照；temporal route priority 小改动正向。 |
| `stage1_route_validity_v8_lme_s_full_79c9cea_cached` | LongMemEval-S | full | `79c9cea` | 0.600 | v6+v7 组合负向；temporal-reasoning 72/133，低于 v6/v7，不作为主线。 |
| `stage1_evidence_arbitration_v9_lme_s_full_122fd3e_cached` | LongMemEval-S | full | `122fd3e` | 0.582 | budget-warning 负向；multi-session 有收益，但整体退化且 avg query tokens 超 6K。 |
| `stage1_compact_evidence_v10_lme_s_full_f8b36eb_cached` | LongMemEval-S | full | `f8b36eb` | 0.590 | budget-warning 负向；evidence_recall=0.998，multi-session 提升到 58/133，但 avg query tokens=6519.668 且整体低于 v7。 |
| `stage1_selective_list_expansion_v11_lme_s_full_d7660f2_cached` | LongMemEval-S | full | `d7660f2` | 0.594 | 成本正向但 accuracy 负向；avg query tokens=5824.768，list_count 61/119，低于 v7。 |
| `stage1_temporal_preference_v4_lme_s_full_6c7d51e_cached` | LongMemEval-S | full | `6c7d51e` | 0.596 | v6 前 LME 最好；temporal 提升明显，但 multi-session 仍弱。 |
| `stage1_temporal_aid_v13_locomo_nonadv_full_8e8f070` | LoCoMo | non-adversarial full | `8e8f070` | 0.721429 | v14 前 LoCoMo 最好；相比 v12 净 +35、相比 clean naive RAG 净 +36，category 2 从 142/321 提到 186/321；token 在预算内。 |
| `stage1_source_expansion_v12_locomo_nonadv_full_3235553` | LoCoMo | non-adversarial full | `3235553` | 0.698701 | source expansion 在 LoCoMo 基本持平；只比 clean naive RAG 多 1 条，category 2 净 -10，已被 v13 超过。 |
| `stage1_naive_rag_top40_external_locomo_nonadv_full_49de2d2_w2` | LoCoMo | non-adversarial full | `49de2d2` | 0.698506 | 强 clean baseline；对齐旧仓库 clean naive RAG 细节后较 v4 净增 4 条。 |
| `stage1_temporal_preference_v4_locomo_nonadv_full_edf05a5_cached` | LoCoMo | non-adversarial full | `edf05a5` | 0.695906 | fact_lookup 可用，temporal/list/组合推理不足。 |
| `stage1_memory_validity_v7_locomo_nonadv_full_b10bfdf_cached` | LoCoMo | non-adversarial full | `b10bfdf` | 0.681818 | v7 validity/superseded retrieval 在 LoCoMo 负向；低于 v4，和 v6 基本持平，不作为主线。 |
| `stage1_route_priority_v6_locomo_nonadv_full_c57e810_cached` | LoCoMo | non-adversarial full | `c57e810` | 0.681611 | v6 在 LoCoMo 负向；route 改动只影响 1 条且无净收益，LoCoMo 主线仍是 v4。 |
| `stage1_temporal_text_v5_lme_s_full_e875d29_cached` | LongMemEval-S | full | `e875d29` | 0.590 | 相对时间文本归一化未提升 LME，preference 退化，作为负向 ablation。 |
| `stage1_temporal_preference_v4_1_lme_s_full_c5e6276_cached` | LongMemEval-S | full | `c5e6276` | 0.584 | compact workpad 省 token 但降分，作为负向 ablation。 |
| `stage1_memory_compiler_v3_lme_s_full_e9ee8bd_cached` | LongMemEval-S | full | `e9ee8bd` | 0.558 | typed compiler 有效，是 v4 前的强基线。 |
| `stage1_query_retrieval_v2_lme_s_full_66fb2c6_cached` | LongMemEval-S | full | `66fb2c6` | 0.540 | query retrieval cleanup 有小幅收益。 |
| `stage1_agent_memory_v1_lme_s_full_b8f58b3_cold` | LongMemEval-S | full | `b8f58b3` | 0.528 | 第一版 cold build baseline。 |
