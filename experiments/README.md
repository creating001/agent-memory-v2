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
- `configs/stage1_evidence_report_contract_v28_cached.json`：v36 前 LME 最好主线候选，也是 v29/v36 的底座。
- `configs/stage1_temporal_event_contract_v29_cached.json`：v33 前 LoCoMo 最强主线，显式区分 `mention_time` 与 `event_time`。
- `configs/stage1_selective_repair_v32_cached.json`：v29 底座上的 selective answer repair/verifier；token 合格但 LoCoMo full 与 v29 持平。
- `configs/stage1_retrieval_top60_v33_cached.json`：v29 底座上的 clean top-60 retrieval expansion；v34 前 LoCoMo 最好结果，但 temporal_lookup 回退。
- `configs/stage1_route_budgeted_retrieval_v34_cached.json`：v33 的 route-budgeted 版本；非 temporal 保留 top60，temporal_lookup 回到 top40，v35 前 LoCoMo 最好。
- `configs/stage1_answer_format_guard_v35_cached.json`：v34 上的 answer format guard；修复 JSON answer salvage 和小数 duration，当前 LoCoMo 最好。
- `configs/stage1_lme_token_safe_format_guard_v36_cached.json`：v28 top40/evidence budget + v35 answer guard；v42 前 LME 最好，也是当前强 baseline。
- `configs/stage1_operation_workpad_v42_cached.json`：v36 上的短 operation workpad；当前 LME 最好，但只是 close-margin 小幅正向。

方法摘要：

- build 阶段由本地 Qwen LLM 从 raw dialogue 中构建 typed memory，类型包括 event、fact、preference、profile、state、relationship、plan。
- memory manager 记录 source/provenance、去重、轻量 supersede、active/superseded 状态和 cache。
- query 阶段同时检索 raw turns、session context 和 typed memory source links。
- retrieval 当前主线是 raw-turn dense + BM25 hybrid；v29/v28 使用 top-40，v33 在 LoCoMo 上扩到 top-60 并允许 typed memory 命中的 raw source turn 回链。
- compiler 将 raw evidence、temporal aid、structured guide 和可见 `evidence_report` 组织给 answer model。
- DeepSeek judge 只在预测完成后离线使用。

当前结论：

- LongMemEval-S full 当前最好为 v42：0.774 DeepSeek judge accuracy，387/500；距 0.80 baseline target 仍差 13 条。
- LoCoMo non-adversarial full 当前最高为 v35：valid-only 0.780377，invalid-as-wrong 1201/1540 = 0.779870；valid-only 已达到 0.78 baseline target，保守 invalid-as-wrong 还差 1 条。
- v28/v29 token gate 均通过：v28 LME avg_build_tokens 80346.246、avg_query_tokens 5736.928；v29 LoCoMo avg_build_tokens 58386.008、avg_query_tokens 3932.560。
- LoCoMo 诊断显示，很多 wrong case 已有 evidence 进入 context，主要问题是 answer 阶段混淆 mention date / event time、列表边界和隐含推理；下一步应改 build/query 两侧的 memory organization，而不是继续只堆 answer prompt。
- v29 temporal event contract 已完成双基准验证：LME `0.762`，低于 v28 `0.766`；LoCoMo `0.761688`，显著高于 v28 `0.737662` 但仍未达 `0.78` target。结论是 event-time 组织对 LoCoMo 有价值，但需要前移到 build-side typed memory，不能只靠 query prompt。
- v30 typed temporal/event build memory 已完成 LoCoMo full：DeepSeek judge accuracy `0.755686`，低于 v29 `0.761688`。字段门禁通过且 token gate 通过，但 evidence recall 从 `0.889323` 降到 `0.880208`，avg memory source hits 从 `22.381` 降到 `21.439`；结论是负向 ablation，不应作为当前主线。
- v31 detailed evidence_report 已完成 LoCoMo full：accuracy `0.755195`，低于 v29 `0.761688`。它把 evidence recall 提到 `0.891276`，但 answer/compiler 更保守，temporal/list/profile 回退；结论是负向 ablation，不跑 LongMemEval full。
- v32 selective repair 已完成 LoCoMo full：accuracy `0.761688`，与 v29 持平；avg query tokens `4466.223`，repair triggered `263/1540`，repair applied `11/1540`，repair-applied 子集 fixed `3` / broken `1`，但整体没有提升。不跑 v32 LongMemEval full。
- v33 top-60 retrieval expansion 已完成 LoCoMo full：valid-only accuracy `0.771930`，invalid-as-wrong `0.771429`，比 v29/v32 净 +15；evidence recall 从 top-40 的 `0.891276` 提到 `0.917969`，但 temporal_lookup 净 -9。
- v34 route-budgeted retrieval 已完成 LoCoMo full：valid-only accuracy `0.779727`，invalid-as-wrong `0.779221`，比 v33 净 +12、比 v29 净 +27；temporal_lookup 相对 v33 净 +7，说明 temporal top40 / non-temporal top60 的 budget 控制有效。
- v35 answer format guard 已完成 LoCoMo full：valid-only accuracy `0.780377`，invalid-as-wrong `0.779870`，比 v34 净 +1；只改 6 条 prediction，finalizer applied 2 条。结论是 close-margin 正向，valid-only 达标，但必须同时报告 invalid-as-wrong 仍差 1 条和 same-answer judge variance。
- v36 LME token-safe format guard 已完成 LongMemEval-S full：accuracy `0.772`，386/500，比 v28 净 +3；avg query tokens `5715.468`，token 合格。结论是当前 LME 最好但仍是小幅正向，same-answer judge variance 可见，距 0.80 还差 14 条。
- v37 row-linked memory bundle 已完成 LongMemEval-S full：accuracy `0.744`，372/500，低于 v36 `0.772`。它通过 token gate 且 evidence recall 仍为 `1.0`，但 typed memory 直接进入 answer prompt 后让 temporal/list/current_state 明显回退；结论是负向 ablation，不跑 LoCoMo full，顶层 config 不长期保留。
- v38 route-scoped top60 + role_query_snippet 已完成 LongMemEval-S full：accuracy `0.752`，低于 v36 `0.772`。它相对 v37 恢复了部分 typed-memory-prompt 回退，但相对 v36 在 `list_count` 和 `temporal_lookup` 损失更大；结论是负向 ablation，不跑 LoCoMo full，顶层 config 不长期保留。
- v39 memory-aware evidence selector 已完成 LongMemEval-S full：accuracy `0.724`，362/500，低于 v36 `0.772` 和 v38 `0.752`。结论是 build-memory source signal 直接排序 final raw rows 会破坏 list/temporal operand coverage；负向 ablation，不跑 LoCoMo full，顶层 config 不长期保留。
- v40 route-scoped evidence detail 已完成 LongMemEval-S full：accuracy `0.742`，371/500，低于 v36 `0.772`。它相对 v39 恢复了部分 list/temporal，但相对 v36 仍净 `-15`；结论是单纯 reader-side detailed evidence rules 不够，不跑 LoCoMo full，顶层 config 不长期保留。
- v41 question-only LLM operation router 已完成 LongMemEval-S route-stratified 20 条 gate：avg_query_tokens `5837.55`，question_analysis_avg_query_tokens `331.05`，route_changed `6/20`，同子集 DeepSeek judge 与 v36 都是 `14/20`，无净收益且增加 token；不跑 full，顶层 config 不长期保留。规划和结论见 `experiments/v41_planning.md`。
- v42 operation workpad 已完成 LongMemEval-S full：accuracy `0.774`，387/500，比 v36 净 `+1`；avg_build_tokens `80346.246`，avg_query_tokens `5865.644`，answer max input/output `131072/16384`。结论是当前 LME 最好但只是 close-margin 小幅正向；继续加长 reader prompt 不划算，下一步应转向 build-to-query memory organization。规划和结论见 `experiments/v42_planning.md`。
- v43 session-thread memory guide 已完成 LongMemEval-S route-stratified 20 条 gate：DeepSeek judge `15/20`，与 v42 same20 持平；avg_query_tokens `6023.95`、max `8003`，未过 token gate。结论是负向/中性 diagnostic，不跑 full，顶层 config 不长期保留。规划和结论见 `experiments/v43_planning.md`。
- v44 temporal-only session guide 已完成 LongMemEval-S route-stratified 20 条 gate：DeepSeek judge `16/20`，比 v42 same20 净 `+1`；avg_query_tokens `5783.75`、max `7631`。但按 v42 full route mix 估计 full avg query `6064.479`，暂不跑 full，先做 v45 token-safe 收窄。规划和结论见 `experiments/v44_planning.md`。

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

## 关键诊断目录

| run | scope | 主要结论 |
|---|---|---|
| `v30_stateful_validity_probe_3525934` | 20 条 route-stratified mixed diagnostic | v30 build memory 字段质量通过；`mention_time=1711/1711`，`event_time=424/1711`，validity 只保留在 `state/profile/preference/relationship`，token gate 通过。 |
| `v31_evidence_report_detail_probe_b913567` | 20 条 route-stratified mixed diagnostic | v31 detailed evidence_report gate 通过；avg_query_tokens `5152.6`，detail rules `20/20` prompts，answer max output `16384`。 |
| `v32_selective_repair_probe_7cde029` | 20 条 route-stratified mixed diagnostic | v32 selective repair gate 通过；avg_query_tokens `5017.3`，repair triggered `1/20`，answer/repair max output `16384`。 |
| `v33_top60_locomo_probe_65daf7d` | 20 条 LoCoMo-only route-stratified diagnostic | v33 top-60 LoCoMo gate 通过；avg_query_tokens `5287.0`，avg_build_tokens `44168.8`，answer max output `16384`。 |
| `v34_route_budgeted_probe_8ce3c3b` | 20 条 LoCoMo-only route-stratified diagnostic | v34 route-budgeted retrieval gate 通过；avg_query_tokens `5050.0`，temporal top40、非 temporal top60 均生效，answer max output `16384`。 |
| `v35_lme_route_probe_e6de8c5` | 20 条 LongMemEval-S route-stratified diagnostic | v35 LoCoMo-winning config 未通过 LME query token gate；avg_query_tokens `7109.2`，p95 `8059`，不能直接跑 LME full。 |
| `v36_lme_token_safe_probe_e7ca9e5` | 20 条 LongMemEval-S route-stratified diagnostic | v36 token-safe config 通过 LME average query token gate；avg_query_tokens `5579.7`，随后已完成 LME full。 |
| `v37_row_memory_bundle_lme_probe_3d3cd07` | 20 条 LongMemEval-S route-stratified diagnostic | v37 row-linked build memory bundle 通过 LME average query token gate；avg_query_tokens `5564.5`，avg_compiled_memory_records `7.1`；后续 full 已证明负向。 |
| `v38_route_snippet_lme_probe_2091273` | 20 条 LongMemEval-S route-stratified diagnostic | v38 route-scoped top60 + `role_query_snippet` gate 通过；avg_query_tokens `5756.0`，list/temporal top60 生效，非目标 route 保持 top40；后续 full 已证明负向。 |
| `v39_memory_aware_selector_lme_probe_fd00801` | 20 条 LongMemEval-S route-stratified diagnostic | v39 route-scoped memory-aware selector gate 通过；avg_query_tokens `5607.8`，weighted full estimate `5566.583`，avg_build_tokens `81690.45`，typed memory 只做 source selection、prompt memory records 为 0。 |
| `v40_route_scoped_evidence_detail_lme_probe_983f882` | 20 条 LongMemEval-S route-stratified diagnostic | v40 route-scoped evidence detail gate 通过；avg_query_tokens `5714.0`，weighted full estimate `5716.6965`，avg_build_tokens `81690.45`，detail prompt 只在 `list_count` / `temporal_lookup` 生效。 |
| `v41_llm_question_router_lme_probe_243452f` | 20 条 LongMemEval-S route-stratified diagnostic | v41 question-only LLM operation router 预算 gate 通过；avg_query_tokens `5837.55`，question_analysis_avg_query_tokens `331.05`，route_changed `6/20`。同子集 DeepSeek judge v36=`14/20`、v41=`14/20`，没有净收益，不跑 full。 |
| `v42_operation_workpad_lme_probe_df25f6a` | 20 条 LongMemEval-S route-stratified diagnostic | v42 operation workpad gate 通过；avg_query_tokens `5660.25`，weighted full estimate `5668.1925`，workpad 只在 `list_count` / `temporal_lookup` 生效。同子集 DeepSeek judge v36=`14/20`、v42=`15/20`，净 +1，无 regression；后续 full 只取得 close-margin `+1/500`。 |
| `v43_session_thread_memory_guide_lme_probe_cb5e118` | 20 条 LongMemEval-S route-stratified diagnostic | v43 session-thread evidence layout + row-linked memory guide 未过 gate；avg_query_tokens `6023.95`、max `8003`，同子集 DeepSeek judge v43=`15/20`、v42=`15/20`，gained/lost `1/1`。不跑 full，顶层 config 不长期保留。 |
| `v44_temporal_session_guide_lme_probe_b39687d` | 20 条 LongMemEval-S route-stratified diagnostic | v44 temporal-only session guide 20 条质量 gate 通过；avg_query_tokens `5783.75`、max `7631`，同子集 DeepSeek judge v44=`16/20`、v42=`15/20`。但 full route-mix 估计 avg query `6064.479`，暂不跑 full，继续收窄。 |

## 保留正式结果

| run | benchmark | subset | commit | accuracy | 主要结论 |
|---|---|---|---|---:|---|
| `stage1_operation_workpad_v42_lme_s_full_f7eb076` | LongMemEval-S | full | `f7eb076` | 0.774000 | 当前 LME 最好；v36 上的短 operation workpad，vs v36 净 +1，仍未达 0.80。收益很小，不能视为突破。 |
| `stage1_lme_token_safe_format_guard_v36_lme_s_full_4af3244` | LongMemEval-S | full | `4af3244` | 0.772000 | v42 前 LME 最好和当前强 baseline；v28 top40/evidence budget + v35 answer guard，vs v28 净 +3；仍未达 0.80。 |
| `stage1_route_snippet_top60_v38_lme_s_full_daf98e7` | LongMemEval-S | full | `daf98e7` | 0.752000 | v36 上的 route-scoped top60 + snippet；vs v36 净 -10，list/temporal 噪声损失大于 coverage 收益，负向 ablation。 |
| `stage1_route_scoped_evidence_detail_v40_lme_s_full_1559c80` | LongMemEval-S | full | `1559c80` | 0.742000 | v36 上的 route-scoped detailed evidence_report；vs v36 净 -15，reader-side 规则不足以稳定提升 list/temporal，不跑 LoCoMo。 |
| `stage1_row_memory_bundle_v37_lme_s_full_7f1fea6` | LongMemEval-S | full | `7f1fea6` | 0.744000 | v36 上的 row-linked build memory bundle；typed memory prompt 化导致 temporal/list/current_state 回退，负向 ablation，不跑 LoCoMo。 |
| `stage1_memory_aware_selector_v39_lme_s_full_800421f` | LongMemEval-S | full | `800421f` | 0.724000 | v36 上的 memory-aware source selector；vs v36 净 -24，list/temporal final row order 噪声明显，负向 ablation，不跑 LoCoMo。 |
| `stage1_evidence_report_contract_v28_lme_s_full_9917c22` | LongMemEval-S | full | `9917c22` | 0.766000 | v36 前 LME 最好；vs v18 净 +17，vs v26 净 +10；仍未达 0.80。 |
| `stage1_answer_format_guard_v35_locomo_nonadv_full_80158a9` | LoCoMo | non-adversarial full | `80158a9` | 0.780377 | 当前 LoCoMo 最好；valid-only 达 0.78，invalid-as-wrong 1201/1540 仍差 1 条，close-margin。 |
| `stage1_route_budgeted_retrieval_v34_locomo_nonadv_full_fb6c703` | LoCoMo | non-adversarial full | `fb6c703` | 0.779727 | v35 前 LoCoMo 最好；非 temporal top60、temporal top40，vs v33 净 +12，距离 0.78 还差 2 条。 |
| `stage1_retrieval_top60_v33_locomo_nonadv_full_f016f9a` | LoCoMo | non-adversarial full | `f016f9a` | 0.771930 | v34 前 LoCoMo 最好；top-60 retrieval 带来 +15 correct，但 temporal_lookup 净 -9。 |
| `stage1_temporal_event_contract_v29_lme_s_full_23e8b78` | LongMemEval-S | full | `23e8b78` | 0.762000 | v28 上的 temporal event contract query-side ablation；temporal_lookup 净 +2，但 current_state/list_count 回退，整体低于 v28。 |
| `stage1_temporal_event_contract_v29_locomo_nonadv_full_c7b8390` | LoCoMo | non-adversarial full | `c7b8390` | 0.761688 | v33 前 LoCoMo 最好；主要收益来自 temporal_lookup/category 2，仍未达 0.78。 |
| `stage1_selective_repair_v32_locomo_nonadv_full_a80816a` | LoCoMo | non-adversarial full | `a80816a` | 0.761688 | v29 + selective repair；token 合格但 overall 与 v29 持平，repair-applied 子集 fixed 3 / broken 1，不跑 LME。 |
| `stage1_evidence_report_detail_v31_locomo_nonadv_full_894c7ee` | LoCoMo | non-adversarial full | `894c7ee` | 0.755195 | v29 底座 + detailed evidence_report；evidence recall 略升但 answer 更保守，负向 ablation。 |
| `stage1_typed_event_memory_v30_locomo_nonadv_full_91c2e1c` | LoCoMo | non-adversarial full | `91c2e1c` | 0.755686 | build-side typed temporal/event memory；字段语义更 clean 但 evidence recall 和 accuracy 低于 v29，负向 ablation。 |
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
