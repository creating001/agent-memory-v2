# 实验入口

`experiments/` 是人工查看正式结果和关键诊断的入口。当前目录保持精简：无用 smoke、小样本、旧 ablation 结果不长期保留。

## 主要指标

方法好坏主要看离线 DeepSeek judge accuracy。

- LongMemEval-S full：500 条。
- LoCoMo non-adversarial full：1540 条。

`exact / F1 / BLEU` 只作为低成本诊断，不作为方法选择依据。

## 当前主线

配置：

- LongMemEval 当前最好：`configs/stage1_route_priority_v6_cached.json` 与 `configs/stage1_memory_validity_v7_cached.json` 并列
- LoCoMo 已验证配置：`configs/stage1_temporal_preference_v4_cached.json`

方法摘要：

- build 阶段由本地 Qwen LLM 从 raw dialogue 中构建 typed memory。
- memory 类型包括 event、fact、preference、profile、state、relationship、plan。
- memory manager 做 source/provenance 记录、去重、轻量 supersede、active/superseded 状态和 cache。
- query 阶段同时检索 raw turns、session context 和 typed memory。
- compiler 将 typed memory view 与 raw context 一起组织给 answer model。
- DeepSeek judge 只在预测完成后离线使用。

当前结论：

- LongMemEval-S full 当前最好为 v6/v7 并列：0.606 DeepSeek judge accuracy。
- LoCoMo non-adversarial full v4：0.695906 DeepSeek judge accuracy，低于目标，主要短板是 temporal_lookup、category 2、list/count 和 category 3 evidence recall。
- v7 memory validity 在 LME 上较 v4 净提升 +5 条，和 v6 持平；avg query tokens 5858.762，接近 6K 预算。
- v8 组合 v6 route priority 与 v7 validity 后降到 0.600，说明两个开关没有稳定互补；不跑 LoCoMo。
- v9 evidence arbitration 降到 0.582，且 avg query tokens 6744.762 超过 6K 目标；仅 multi-session 从 v7 的 49/133 提到 56/133，可作为后续 compact/route-specific 设计线索。
- v10 compact evidence 降到 0.590，avg query tokens 6519.668 超过 6K 目标；evidence recall 0.998 且 multi-session 58/133，但整体被 assistant/preference/temporal 退化抵消，不作为主线。
- v11 selective list expansion 降到 0.594，avg query tokens 5824.768 在预算内；成本正向但 list_count 61/119 低于 v7 的 63/119，不作为主线。
- v6 route priority 是 LME clean 正向消融，但 LoCoMo full 降到 0.681611，不作为 LoCoMo 主线。
- v5 relative temporal text normalization 在 LME 上降到 0.590，不作为主线。
- v4.1 compact temporal workpad 降低 token 但 accuracy 退化，不作为主线。

外部方法借鉴与取舍：

- 借鉴 LangMem 的 collection/profile 思路。
- 借鉴 Memobase 的 profile/event timeline，但不删除 raw dialogue。
- 借鉴 MIRIX 的多类型 memory taxonomy，但不引入多 agent memory OS。
- 借鉴 MemMachine 的 raw episode + profile 辅助。
- 借鉴 Graphiti/Zep 的 temporal/provenance 思路，但暂不引入重型图数据库。

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
| `stage1_memory_validity_v7_lme_s_full_85ddd44_cached` | LongMemEval-S | full | `85ddd44` | 0.606 | memory validity / route-specific superseded retrieval 正向；与 v6 持平，较 v4 +5，query token 接近 6K。 |
| `stage1_route_priority_v6_lme_s_full_a387f79_cached` | LongMemEval-S | full | `a387f79` | 0.606 | 当前 LME 并列最好；temporal route priority 小改动正向。 |
| `stage1_route_validity_v8_lme_s_full_79c9cea_cached` | LongMemEval-S | full | `79c9cea` | 0.600 | v6+v7 组合负向；temporal-reasoning 72/133，低于 v6/v7，不作为主线。 |
| `stage1_evidence_arbitration_v9_lme_s_full_122fd3e_cached` | LongMemEval-S | full | `122fd3e` | 0.582 | budget-warning 负向；multi-session 有收益，但整体退化且 avg query tokens 超 6K。 |
| `stage1_compact_evidence_v10_lme_s_full_f8b36eb_cached` | LongMemEval-S | full | `f8b36eb` | 0.590 | budget-warning 负向；evidence_recall=0.998，multi-session 提升到 58/133，但 avg query tokens=6519.668 且整体低于 v7。 |
| `stage1_selective_list_expansion_v11_lme_s_full_d7660f2_cached` | LongMemEval-S | full | `d7660f2` | 0.594 | 成本正向但 accuracy 负向；avg query tokens=5824.768，list_count 61/119，低于 v7。 |
| `stage1_temporal_preference_v4_lme_s_full_6c7d51e_cached` | LongMemEval-S | full | `6c7d51e` | 0.596 | v6 前 LME 最好；temporal 提升明显，但 multi-session 仍弱。 |
| `stage1_temporal_preference_v4_locomo_nonadv_full_edf05a5_cached` | LoCoMo | non-adversarial full | `edf05a5` | 0.695906 | fact_lookup 可用，temporal/list/组合推理不足。 |
| `stage1_route_priority_v6_locomo_nonadv_full_c57e810_cached` | LoCoMo | non-adversarial full | `c57e810` | 0.681611 | v6 在 LoCoMo 负向；route 改动只影响 1 条且无净收益，LoCoMo 主线仍是 v4。 |
| `stage1_temporal_text_v5_lme_s_full_e875d29_cached` | LongMemEval-S | full | `e875d29` | 0.590 | 相对时间文本归一化未提升 LME，preference 退化，作为负向 ablation。 |
| `stage1_temporal_preference_v4_1_lme_s_full_c5e6276_cached` | LongMemEval-S | full | `c5e6276` | 0.584 | compact workpad 省 token 但降分，作为负向 ablation。 |
| `stage1_memory_compiler_v3_lme_s_full_e9ee8bd_cached` | LongMemEval-S | full | `e9ee8bd` | 0.558 | typed compiler 有效，是 v4 前的强基线。 |
| `stage1_query_retrieval_v2_lme_s_full_66fb2c6_cached` | LongMemEval-S | full | `66fb2c6` | 0.540 | query retrieval cleanup 有小幅收益。 |
| `stage1_agent_memory_v1_lme_s_full_b8f58b3_cold` | LongMemEval-S | full | `b8f58b3` | 0.528 | 第一版 cold build baseline。 |
