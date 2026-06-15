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
- `configs/stage1_answer_format_guard_v35_cached.json`：v34 上的 answer format guard；修复 JSON answer salvage 和小数 duration，LoCoMo 强 baseline。
- `configs/stage1_relative_time_finalizer_v94_cached.json`：v35 上的 conservative relative-time finalizer；prompt-compatible full run 成为当前 LoCoMo 最好。
- `configs/stage1_lme_token_safe_format_guard_v36_cached.json`：v28 top40/evidence budget + v35 answer guard；v42 前 LME 最好，也是当前强 baseline。
- `configs/stage1_operation_workpad_v42_cached.json`：v36 上的短 operation workpad；v73 前 LME 最好，但只是 close-margin 小幅正向。
- `configs/stage1_finalizer_duration_fix_v73_cached.json`：v79 前 LongMemEval-S 最好主线；从 v42 出发只关闭有害的机械 duration decimal rounding finalizer。
- `configs/stage1_missing_detail_finalizer_v79_cached.json`：v73 上的 missing-detail finalizer；把 answer JSON 中的 `missing` 细节透出到短拒答。
- `configs/stage1_update_conflict_guide_v80_cached.json`：v79 上的 update/conflict candidate chain；只在 `current_state` / `fact_lookup` 对有旧值、新值、更正、历史范围信号的 user raw rows 加 source-preserving 索引，v88 前 LongMemEval-S 最好。
- `configs/stage1_update_conflict_value_slot_v81_cached.json`：v80 的 value-slot 收窄诊断；changed subset 正向，但 fresh full judge 未超过 v80，不作为当前 best。
- `configs/stage1_personalized_advice_contract_v83_cached.json`：v81 代码线上的 personalized advice reader discipline；LongMemEval-S full 与 v80 持平，但触发子集 mixed，不作为新 best。
- `configs/stage1_evidence_answer_detail_v88_cached.json`：v83 上的窄机械 finalizer；不改 build/retrieval/compiler/answer prompt，只用 answer JSON 已有 evidence_report 补 count detail、average、money difference 和 date endpoint duration，当前 LongMemEval-S 最好。

方法摘要：

- build 阶段由本地 Qwen LLM 从 raw dialogue 中构建 typed memory，类型包括 event、fact、preference、profile、state、relationship、plan。
- memory manager 记录 source/provenance、去重、轻量 supersede、active/superseded 状态和 cache。
- query 阶段同时检索 raw turns、session context 和 typed memory source links。
- retrieval 当前主线是 raw-turn dense + BM25 hybrid；v29/v28 使用 top-40，v33 在 LoCoMo 上扩到 top-60 并允许 typed memory 命中的 raw source turn 回链。
- compiler 将 raw evidence、temporal aid、structured guide 和可见 `evidence_report` 组织给 answer model。
- DeepSeek judge 只在预测完成后离线使用。

当前结论：

- LongMemEval-S full 当前最好为 v88：0.800 DeepSeek judge accuracy，400/500；首次达到 0.80 baseline target。
- LoCoMo non-adversarial full 当前最高为 v96 budgeted selected context：fresh full judge 1232/1540 = 0.800000，首次达到 0.80 minimum target；avg_build_tokens 58386.008，avg_query_tokens 5496.281，在 6K 主线预算内。v96 相对 v95 净 +21；prediction_changed 子集 `WRONG->CORRECT 53`、`CORRECT->WRONG 36`，净 +17。v95 是前一 best：1211/1540 = 0.786364；v94 是前前 best：1206/1540 = 0.783117；v35 是强 baseline：valid-only 0.780377。
- v95 同 config 已完成 LongMemEval-S full：DeepSeek judge 386/500 = 0.772，低于 v88 400/500 = 0.800，且 avg_query_tokens 7441.176 超过 6K 主线预算。结论：v95 是 LoCoMo 正向但 LME 负向/过预算的分叉诊断，不能作为统一主线。
- v96 token-safe selected context 已完成 LoCoMo full：DeepSeek judge 1232/1540 = 0.800000，高于 v95 1211/1540；avg_query_tokens 从 v95 的 5974.314 降到 5496.281，evidence recall 0.914714，与 v95 基本持平。相对 v95 changed-prediction 子集净 +17，相对 v94 changed-prediction 子集净 +28。结论：收窄局部上下文降低了 reader 噪声，是当前 LoCoMo 最好；需要同 config 跑 LongMemEval-S full 后再判断是否能成为统一主线。
- v96 同 config 已完成 LongMemEval-S full：DeepSeek judge 380/500 = 0.760000，低于 v88 400/500 = 0.800000；avg_query_tokens 6126.760 略超 6K。相对 v88 changed-prediction 子集净 -21，evidence recall 仍为 1.0，因此问题是 reader/context organization 噪声，不是召回缺失。结论：当前分别 best 已达到 0.80 baseline，但同一个算法尚未同时达标；v96 只保留为 LoCoMo best 分支。
- v28/v29 token gate 均通过：v28 LME avg_build_tokens 80346.246、avg_query_tokens 5736.928；v29 LoCoMo avg_build_tokens 58386.008、avg_query_tokens 3932.560。
- LoCoMo 诊断显示，很多 wrong case 已有 evidence 进入 context，主要问题是 answer 阶段混淆 mention date / event time、列表边界和隐含推理；下一步应改 build/query 两侧的 memory organization，而不是继续只堆 answer prompt。
- v29 temporal event contract 已完成双基准验证：LME `0.762`，低于 v28 `0.766`；LoCoMo `0.761688`，显著高于 v28 `0.737662` 但仍未达 `0.78` target。结论是 event-time 组织对 LoCoMo 有价值，但需要前移到 build-side typed memory，不能只靠 query prompt。
- v30 typed temporal/event build memory 已完成 LoCoMo full：DeepSeek judge accuracy `0.755686`，低于 v29 `0.761688`。字段门禁通过且 token gate 通过，但 evidence recall 从 `0.889323` 降到 `0.880208`，avg memory source hits 从 `22.381` 降到 `21.439`；结论是负向 ablation，不应作为当前主线。
- v31 detailed evidence_report 已完成 LoCoMo full：accuracy `0.755195`，低于 v29 `0.761688`。它把 evidence recall 提到 `0.891276`，但 answer/compiler 更保守，temporal/list/profile 回退；结论是负向 ablation，不跑 LongMemEval full。
- v32 selective repair 已完成 LoCoMo full：accuracy `0.761688`，与 v29 持平；avg query tokens `4466.223`，repair triggered `263/1540`，repair applied `11/1540`，repair-applied 子集 fixed `3` / broken `1`，但整体没有提升。不跑 v32 LongMemEval full。
- v33 top-60 retrieval expansion 已完成 LoCoMo full：valid-only accuracy `0.771930`，invalid-as-wrong `0.771429`，比 v29/v32 净 +15；evidence recall 从 top-40 的 `0.891276` 提到 `0.917969`，但 temporal_lookup 净 -9。
- v34 route-budgeted retrieval 已完成 LoCoMo full：valid-only accuracy `0.779727`，invalid-as-wrong `0.779221`，比 v33 净 +12、比 v29 净 +27；temporal_lookup 相对 v33 净 +7，说明 temporal top40 / non-temporal top60 的 budget 控制有效。
- v35 answer format guard 已完成 LoCoMo full：valid-only accuracy `0.780377`，invalid-as-wrong `0.779870`，比 v34 净 +1；只改 6 条 prediction，finalizer applied 2 条。结论是 close-margin 正向，valid-only 达标，但必须同时报告 invalid-as-wrong 仍差 1 条和 same-answer judge variance。
- v94 prompt-compatible relative-time finalizer 已完成 LoCoMo full：fresh full judge `0.783117`，1206/1540；controlled comparison vs v35 为 `0.781818`，1204/1540。只改变 6 条 prediction，changed subset 为 `WRONG->CORRECT 4`、`CORRECT->WRONG 1`、`CORRECT->CORRECT 1`。结论是当前 LoCoMo best，但方法收益按 controlled +3 记录，fresh full 中另有 +2 来自 judge variance。
- v36 LME token-safe format guard 已完成 LongMemEval-S full：accuracy `0.772`，386/500，比 v28 净 +3；avg query tokens `5715.468`，token 合格。结论是当前 LME 最好但仍是小幅正向，same-answer judge variance 可见，距 0.80 还差 14 条。
- v37 row-linked memory bundle 已完成 LongMemEval-S full：accuracy `0.744`，372/500，低于 v36 `0.772`。它通过 token gate 且 evidence recall 仍为 `1.0`，但 typed memory 直接进入 answer prompt 后让 temporal/list/current_state 明显回退；结论是负向 ablation，不跑 LoCoMo full，顶层 config 不长期保留。
- v38 route-scoped top60 + role_query_snippet 已完成 LongMemEval-S full：accuracy `0.752`，低于 v36 `0.772`。它相对 v37 恢复了部分 typed-memory-prompt 回退，但相对 v36 在 `list_count` 和 `temporal_lookup` 损失更大；结论是负向 ablation，不跑 LoCoMo full，顶层 config 不长期保留。
- v39 memory-aware evidence selector 已完成 LongMemEval-S full：accuracy `0.724`，362/500，低于 v36 `0.772` 和 v38 `0.752`。结论是 build-memory source signal 直接排序 final raw rows 会破坏 list/temporal operand coverage；负向 ablation，不跑 LoCoMo full，顶层 config 不长期保留。
- v40 route-scoped evidence detail 已完成 LongMemEval-S full：accuracy `0.742`，371/500，低于 v36 `0.772`。它相对 v39 恢复了部分 list/temporal，但相对 v36 仍净 `-15`；结论是单纯 reader-side detailed evidence rules 不够，不跑 LoCoMo full，顶层 config 不长期保留。
- v41 question-only LLM operation router 已完成 LongMemEval-S route-stratified 20 条 gate：avg_query_tokens `5837.55`，question_analysis_avg_query_tokens `331.05`，route_changed `6/20`，同子集 DeepSeek judge 与 v36 都是 `14/20`，无净收益且增加 token；不跑 full，顶层 config 不长期保留。
- v42 operation workpad 已完成 LongMemEval-S full：accuracy `0.774`，387/500，比 v36 净 `+1`；avg_build_tokens `80346.246`，avg_query_tokens `5865.644`，answer max input/output `131072/16384`。结论是当前 LME 最好但只是 close-margin 小幅正向；继续加长 reader prompt 不划算，下一步应转向 build-to-query memory organization。
- v42 复现修复控制已完成：commit `d6c6e8e` 修复 answer cache 命中二次解析和 `external_naive` disabled-block prompt drift；新控制 run 与原 v42 prediction `500/500` 完全一致。DeepSeek judge 重跑为 `0.772`，原 v42 为 `0.774`；差异来自同答案 judge variance，不是方法变化。后续方法比较必须基于修复后的代码。
- v73 duration finalizer fix 已完成 LongMemEval-S full：accuracy `0.778`，389/500，比 v42 修复控制 `0.772` 高 3 条；avg_build_tokens `80346.246`，avg_query_tokens `5864.706`。结论是当前 LME 最好主线；它只关闭一个明确有害的 duration rounding finalizer，不改变 retrieval/build/prompt。
- v79 missing-detail finalizer 已完成 LongMemEval-S full：accuracy `0.784`，392/500，比 v73 高 3 条；avg_build_tokens `80346.246`，avg_query_tokens `5864.706`，finalizer applied `29/500`，answer/build cache 全命中。prediction changed subset 为 `WRONG->CORRECT 6`、`CORRECT->WRONG 0`，未改 prediction 的同答案 judge 方差净 `-3`。结论是 clean、零额外 prediction LLM token 的小正向，当前 LME 最好，但仍未达到 0.80。
- v80 update/conflict guide 已完成 LongMemEval-S full：accuracy `0.792`，396/500，比 v79 高 4 条；avg_build_tokens `80346.246`，avg_query_tokens `5913.516`，update_conflict_guide_applied `60/500`，answer cache misses `60`。prediction changed subset 为 `WRONG->CORRECT 7`、`CORRECT->WRONG 4`，修复 personal best、Wells Fargo pre-approval、tennis previous/current、Instagram followers 等旧值/新值错误；仍有 total-cost/surface-format 回退，下一步需要更稳的 aggregation / current-state scope gate。
- v81 value-slot update/conflict guide 已完成 LongMemEval-S full：accuracy `0.790`，395/500；avg_build_tokens `80346.246`，avg_query_tokens `5903.352`，guide 触发 `44/500`。相比 v80，prediction changed subset 为 `WRONG->CORRECT 3`、`CORRECT->WRONG 1`，修复 v80 的 Lola 花费、评论数表述和家庭旅行地点回退；但未改 prediction 的 fresh judge 方差净 `-3`，所以不替代 v80 当前最好结论。
- v82 fact-operation workpad 已完成 LongMemEval-S full：accuracy `0.786`，393/500；avg_build_tokens `80346.246`，avg_query_tokens `5928.91`，answer cache misses `52/500`。由于当前代码已包含 v81 value-slot guide，v82 实际是 v81 + fact_lookup operation workpad；相对 v81 prediction changed subset 为 `WRONG->CORRECT 1`、`CORRECT->WRONG 2`，结论是负向，顶层 config 删除。
- v83 personalized advice contract 已完成 LongMemEval-S full：accuracy `0.792`，396/500；avg_build_tokens `80346.246`，avg_query_tokens `5912.794`，contract 触发 `29/500`。相对 v81 overall +1，但 prediction changed subset 为 `WRONG->CORRECT 2`、`CORRECT->WRONG 4`，净负，整体提升主要来自未改 prediction 的 judge variance；相对 v80 accuracy 持平。结论是 best-tie 候选，不是新 best，后续个性化建议应转向 build-side profile/event anchoring。
- v88 evidence answer detail 已完成 LongMemEval-S full：accuracy `0.800`，400/500；avg_build_tokens `80346.246`，avg_query_tokens `5912.794`，answer/build cache 全命中，finalizer applied `45/500`。相对 v80/v83 fresh full judge 均为净 `+4`；主要稳定修复 money difference `$270`、GPA average `3.83` 和 date endpoint duration `9 days`，count detail 无 changed-subset 回退但存在 judge 方差。结论是 clean、零额外 LLM token、达到 LME baseline target 的当前 LME 最好。
- v88 同一 config 已完成 LoCoMo non-adversarial full：accuracy `0.755844`，1164/1540，低于 v35 valid-only `0.780377`；avg_build_tokens `58386.008`，avg_query_tokens `3938.612`，token 合格。相对 v35 为 `WRONG->CORRECT 58`、`CORRECT->WRONG 96`、净 `-38`。结论是 v88 不能作为统一双基准主线；下一步应设计 v89，组合 v35 的 LoCoMo retrieval/format 优势和 v88 的窄 finalizer，再双基准 full 验证。
- v89 route-budgeted answer detail 已完成 LoCoMo non-adversarial full：accuracy `0.752597`，1159/1540，低于 v35 和 v88；avg_build_tokens `58386.008`，avg_query_tokens `4922.037`，token 合格。相对 v35 为 `WRONG->CORRECT 36`、`CORRECT->WRONG 79`、净 `-43`；相对 v88 净 `-5`。结论是负向 ablation：v35 的 top60 retrieval budget 不能直接叠到 v88 的 reader/prompt stack，顶层 config 删除，只保留 formal snapshot。
- v90 v35 plus answer detail 已完成 LoCoMo diagnostic full：accuracy `0.775033`，低于 v35 valid-only `0.780377`；avg_build_tokens `58386.008`，avg_query_tokens `4914.036`，token 合格。相对 v35 为 `WRONG->CORRECT 47`、`CORRECT->WRONG 57`、`WRONG->INVALID 2`，净 `-10`。结论是 v88 窄 finalizer 不能直接提升 v35 LoCoMo 底座；下一步应分析 v35 badcase 的 evidence organization，而不是继续叠 finalizer。
- v74 build 4K 输出上限消融已完成 LongMemEval-S full：accuracy `0.766`，383/500，低于 v73 `0.778`；avg_build_tokens 增至 `84656.5`，evidence recall 仍为 `1.0`。结论是负向 build-side 消融，顶层 config 删除，只保留 formal 快照。
- v75 all-profile compact repair 已完成 LongMemEval-S full：accuracy `0.766`，383/500，低于 v73 `0.778`；avg_query_tokens `5985.758`，接近 6K。controlled changed subset 对 v73 为轻微正向，但 all-profile repair 会误伤已支持的个性化答案，顶层 config 删除，只保留 formal 快照。
- v76 uncertain-only profile repair 已完成 LongMemEval-S full：accuracy `0.768`，384/500，低于 v73 `0.778`；avg_query_tokens `5880.232`，repair triggered/applied `6/4`。controlled changed subset 为 391/500，但 fresh full 不支撑主线。结论是 profile repair 只能作为低频拒答补救信号，不能继续作为通用重写器；顶层 config 删除，只保留 formal 快照。
- v77 missing reason enrichment 已完成 LongMemEval-S full：accuracy `0.772`，386/500，低于 v73 `0.778`；avg_query_tokens 与 v73 相同，finalizer applied `42/500`。changed subset 4 gain / 4 loss，controlled accuracy 与 v73 持平。结论是拒答措辞微调不稳定；顶层 config 和源码分支删除，只保留 formal 快照。
- v78 structured guide row features 已完成 LongMemEval-S controlled full：accuracy `0.758`，379/500，低于 v73 `0.778`；avg_build_tokens `80346.246`，avg_query_tokens `5891.06`，answer cache hits/misses `231/269`。changed-answer method surface 为 9 gain / 14 loss，`list_count` changed subset 1 gain / 5 loss，`temporal_lookup` 8 gain / 9 loss。结论是浅层数量/时间 row feature 会增加候选显著性但不能稳定解决 distinct item、scope 和 endpoint role；顶层 config 和源码开关删除，只保留 formal 快照。
- v66 route-aware context budget 已完成 LongMemEval-S full：accuracy `0.754`，377/500，低于 v42 修复控制 `0.772`；avg_query_tokens 从 `5864.706` 降到 `5235.538`，但 CORRECT->WRONG 27、WRONG->CORRECT 18，净 -9。结论是固定 route row/char 截断负向；query token 不是越多越好，但不能机械压缩上下文。
- v70 route snippet compact 已完成 LongMemEval-S full：accuracy `0.758`，379/500，低于 v42 修复控制 `0.772`；seeded cache 控制后 answer cache hits/misses `359/141`，prediction_changed `26/500`，changed subset `CORRECT->WRONG 13`、`WRONG->CORRECT 3`，主要损失来自 `list_count`。结论是纯 snippet 压缩负向；list/count 需要完整候选细节，不能靠 query snippet 换分。
- v71 temporal-order router 已完成 LongMemEval-S full：accuracy `0.770`，385/500，低于 v42 修复控制 `0.772`；seeded cache 控制后 answer cache hits/misses `462/38`，prediction_changed `11/500`，changed subset `WRONG->CORRECT 1`、`CORRECT->WRONG 1`。结论是 route-only 修正中性，不保留顶层 config 或 src route 改动；顺序题仍需要 endpoint/candidate validation。
- v69 supported uncertain repair 已完成 LongMemEval-S full：accuracy `0.760`，380/500，低于 v42 修复控制 `0.772`；avg_query_tokens `5981.198`，prediction_changed `6/500`。changed subset 为 WRONG->CORRECT 2、WRONG->WRONG 4，但 494 条未改 prediction 的 judge 重跑存在 CORRECT->WRONG 13、WRONG->CORRECT 5。结论是 repair 局部小正向但 full 未提升，且 profile/preference repair 仍有 unsupported 泛化风险；顶层 config 删除，只保留 formal 快照。
- v63 uncertain-only answer repair 已完成 LongMemEval-S full：accuracy `0.766`，383/500，低于 v42 `0.774`；vs v42 gained/lost `18/22`，net `-4`，repair triggered `47/500`、applied `10/500`，avg_query_tokens `6349.876` 超过 6K 主线预算。结论是负向且超预算，顶层 config 删除，仅保留 formal 快照；不继续把 broad answer repair 作为主线。
- v43 session-thread memory guide 已完成 LongMemEval-S route-stratified 20 条 gate：DeepSeek judge `15/20`，与 v42 same20 持平；avg_query_tokens `6023.95`、max `8003`，未过 token gate。结论是负向/中性 diagnostic，不跑 full，顶层 config 不长期保留。
- v44 temporal-only session guide 已完成 LongMemEval-S route-stratified 20 条 gate：DeepSeek judge `16/20`，比 v42 same20 净 `+1`；avg_query_tokens `5783.75`、max `7631`。但按 v42 full route mix 估计 full avg query `6064.479`，暂不跑 full，先做 v45 token-safe 收窄。
- v45 temporal session guide token-safe 收窄已完成 LongMemEval-S route-stratified 20 条 gate：DeepSeek judge `16/20`，比 v42 same20 净 `+1`、无新增错误；avg_build_tokens `81690.45`，avg_query_tokens `5744.5`，max `7352`，answer max input/output `131072/16384`。但按 v42 full route mix 估计 full avg query `6001.2865`，略超 6K 预算，不跑 full，顶层 config 不长期保留。
- v46 temporal session-thread-only 已完成 LongMemEval-S route-stratified 20 条 gate：DeepSeek judge `15/20`，与 v42 same20 持平；avg_build_tokens `81690.45`，avg_query_tokens `5722.5`，max `7274`，full route-mix 估计 `5965.8665` 通过 6K。changed-answer delta 为正，修复 exact-date case；raw loss 是同答案 judge variance。结论是不直接跑 full，继续做 temporal badcase 设计。
- v47 temporal aggregation contract 已完成 LongMemEval-S `temporal_aggregation_106` 诊断：DeepSeek judge `75/106 = 0.707547`，低于 v42 same-106 `81/106 = 0.764151`；gain/loss `5/11`，answer_changed `37`，finalizer_applied `11`，avg_query_tokens `7209.038`，estimated full avg query `5967.238`。结论是负向：schema 增 token，`count_increment` finalizer 导致重复计数，不跑 full，顶层 config 不长期保留。
- v48 Candidate Evidence Map 已完成 LongMemEval-S `weak_route_87` 诊断：DeepSeek judge `56/87 = 0.643678`，低于 v42 same-87 `59/87 = 0.678161`；gain/loss `6/9`，answer_changed `32`，estimated full avg query `6250.456` 超过 6K。结论是全弱路由开启负向且超预算；仅 current_state 有局部正向，后续 v49 已验证 current-state-only 仍只是弱信号，不扩 full。
- v49 current-state-only Candidate Map 已完成 LongMemEval-S `current_state_22` 诊断：DeepSeek judge `13/22 = 0.590909`，高于 v42 same-22 `12/22 = 0.545455`，gain/loss `3/2`，answer_changed `12`，estimated full avg query `5884.492` 通过 6K。结论是干净但收益太弱且有 temporal/order regression，不扩 full，顶层 config 不长期保留。
- v50 profile/advice memory guide 已完成 LongMemEval-S `single-session-preference_30` 诊断：DeepSeek judge `12/30 = 0.400000`，低于 v42 same-30 `13/30 = 0.433333`；gain/loss `1/2`，answer_changed `25`，avg query delta `+461.833`。结论是负向：拓宽 advice route + source-linked build memory guide 没有稳定提升 personalized advice，不跑 full，顶层 config 不长期保留。
- v51 profile/advice answer repair 已完成 LongMemEval-S `single-session-preference_30` 诊断：DeepSeek judge `16/30 = 0.533333`，高于 v42 same-30 `13/30 = 0.433333` 和 v50 same-30 `12/30 = 0.400000`；gain/loss `6/3`，repair applied `6/30`，applied draft `0/6` -> final `3/6`。但 avg_query_tokens `8382.667`，超过 8K diagnostic 边界；结论是 repair 思路有效但过贵，不跑 full，下一步做 token-safe profile-anchor repair，顶层 config 不长期保留。
- v52 profile uncertain repair 先在 LongMemEval-S `single-session-preference_30` 诊断正向：DeepSeek judge `15/30 = 0.500000`，高于 v42 same-30 `13/30 = 0.433333`，avg_query_tokens `5954.533`。但 full 失败：`385/500 = 0.770000`，低于 v42 `387/500 = 0.774000`；vs v42 gain/loss `19/21`，answer_changed `106`。结论是 answer-side repair 局部有效但 full 不稳定，不跑 LoCoMo，顶层 config 删除。
- v53 scoped evidence 两阶段回答已完成 LongMemEval-S `temporal_aggregation_106` 诊断：DeepSeek judge `63/106 = 0.594340`，低于 v42 same-106 `81/106 = 0.764151` 和 v47 `75/106 = 0.707547`；gain/loss `5/23`，answer_changed `68`，avg_query_tokens `5113.226`。结论是 clean 且 token 合格，但 extracted JSON 作为唯一事实输入会放大 extractor 边界错误，不跑 full，顶层 config 删除。
- v54 turn-window retrieval 已完成 LongMemEval-S `weak_route_87` 诊断：DeepSeek judge `59/87 = 0.678161`，与 v42 same-87 持平；gain/loss `7/7`，answer_changed `25`，avg_query_tokens `5959.874`。`list_count` 小正向被 profile/current/temporal 回退抵消，不跑 full，顶层 config 删除。
- v55 turn-window dense32 消融已完成 LongMemEval-S `weak_route_87` 诊断：DeepSeek judge `57/87 = 0.655172`，低于 v42/v54 same-87；gain/loss vs v42 `6/8`，avg_query_tokens `6000.310` 略超 6K。结论是当前 turn-window BM25 参数方向不稳定，停止继续微调，顶层 config 删除。
- v56 lossless atomic build memory 已完成 LongMemEval-S `weak_route_87` 诊断：DeepSeek judge `57/87 = 0.655172`，低于 v42 same-87 `59/87 = 0.678161`；gain/loss `4/6`，answer_changed `22`，avg_build_tokens `107052.839`，比 v42 same87 多约 `26060.977`，avg_query_tokens `6007.575` 略超 6K。结论是 build 侧更细粒度 extraction 增加 records 和成本，但没有改善最终 evidence 使用；不跑 full，顶层 config 删除，仅保留实验快照。
- v57 target-completeness checklist 已完成 LongMemEval-S `weak_route_87` 诊断：DeepSeek judge `59/87 = 0.678161`，与 v42 same87 持平；gain/loss `5/5`，answer_changed `28`，avg_build_tokens `80991.862`，avg_query_tokens `6270.575` 超过 6K。结论是 query/compiler 侧 checklist 会改变答案但不能净增正确率，而且增加 token；不跑 full，顶层 config 删除，仅保留实验快照。
- v58 clean rerank retrieval 已完成 LongMemEval-S `weak_route_87` 诊断：DeepSeek judge `55/87 = 0.632184`，低于 v42 same87 `59/87 = 0.678161`；gain/loss `6/10`，answer_changed `35`，avg_build_tokens `80991.862`，avg_query_tokens `5898.540`。rerank 全量应用且 prediction token gate 通过，但 list_count 从 `15/20` 降到 `12/20`、profile_preference 从 `10/15` 降到 `8/15`，只有 temporal_lookup 小幅 `22/30 -> 23/30`。结论是单文档相关性 rerank 会破坏多证据覆盖和 profile 连续性；不跑 full，顶层 config 删除，仅保留实验快照。
- v59 provenance alignment + source-anchor coverage 已完成 LongMemEval-S `weak_route_87` 诊断：DeepSeek judge `55/87 = 0.632184`，低于 v42 same87 `59/87 = 0.678161`；gain/loss `4/8`，avg_query_tokens `6065.920` 超过 6K 软预算。`current_state` 小幅正向 `12/22 -> 13/22`，但 `list_count` 和 `profile_preference` 明显回退；结论是全路由 source-anchor 会破坏证据覆盖，不跑 full，顶层 config 删除，仅保留实验快照。
- v60 dialogue + temporal reader contract 已完成 LongMemEval-S `weak_route_87` 诊断：DeepSeek judge `58/87 = 0.666667`，低于 v42 same87 `59/87 = 0.678161`；gain/loss `6/7`，answer_changed `29`，avg_build_tokens `80991.862`，avg_query_tokens `6202.195` 超过 6K。`current_state` 小幅正向 `12/22 -> 13/22`，但 `list_count` 回退 `15/20 -> 14/20`、`profile_preference` 回退 `10/15 -> 9/15`、`temporal_lookup` 持平。结论是继续加 reader prompt 不值得，不跑 full，顶层 config 删除，仅保留实验快照。
- v61 fact operation workpad gate 已完成 LongMemEval-S `fact_operation_33` 诊断：DeepSeek judge `27/33 = 0.818182`，与 v42 same33 持平；gain/loss `2/2`，answer_changed `12`，avg_build_tokens `80906.667`，avg_query_tokens `5694.030`。修复少数 exact numeric/format case，但引入等量 over-count / insufficient-answer regression；结论是中性，不跑 full，顶层 config 删除，仅保留实验快照。
- v62 dialogue episode layout 已完成 LongMemEval-S `fact_lookup_183` 诊断：DeepSeek judge `141/183 = 0.770492`，低于 v42 same183 `150/183 = 0.819672`；gain/loss `8/17`，answer_changed `54`，avg_build_tokens `80561.590`，avg_query_tokens `6220.005` 超过 6K。结论是负向且超预算，删除顶层 config 和对应源码分支，仅保留实验快照。
- v64 list_count-only adjacent-turn window BM25 已完成 LongMemEval-S `list_count_119` 诊断：DeepSeek judge `93/119 = 0.781513`，低于 v42 same119 `95/119 = 0.798319`；gain/loss `5/7`，answer_changed `17`，avg_query_tokens `5648.555`。结论是 clean 且 token 合格但负向，不跑 full，顶层 config 删除，仅保留实验快照。
- v65 unit/sum mechanical finalizer 已完成 LongMemEval-S full：DeepSeek judge `379/500 = 0.758000`，低于 v42 `387/500 = 0.774000`；vs v42 gain/loss `20/28`、answer_changed `120`，avg_build_tokens `80346.246`，avg_query_tokens `5924.318`，evidence recall `1.0`。结论是负向，且受 current code drift 影响，不是纯 finalizer 正向消融；顶层 config 和源码分支删除，只保留 formal 快照。

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
| `stage1_answer_format_guard_v35_prompt_compat_locomo_nonadv_full_555b618` | LoCoMo non-adversarial full prompt/cache compatibility control | 当前代码已恢复历史 v35 prediction：`1540/1540` answer 与 `stage1_answer_format_guard_v35_locomo_nonadv_full_80158a9` 完全一致，answer/build cache 全命中；历史 judge `1201/1540 = 0.779870` 可作为 baseline 继续引用。 |
| `stage1_answer_format_guard_v35_current_replay_locomo_nonadv_full_11b53e9` | LoCoMo non-adversarial full current-code replay | 当前 commit 下重放 v35 配置，用于隔离 v94 效果；DeepSeek judge `1185/1540 = 0.769481`，低于历史 v35 `1201/1540`，说明后续比较需注意 code/cache parsing drift。 |
| `v47_temporal_aggregation_lme_diag_5487300` | 106 条 LongMemEval-S question-derived temporal aggregation diagnostic | v47 aggregation report + count_increment finalizer 失败；DeepSeek judge `75/106`，低于 v42 same-106 `81/106`，gain/loss `5/11`。重复计数 regression 明显，不跑 full，顶层 config 已删除。 |
| `v48_candidate_map_lme_weakroute_265e07d` | 87 条 LongMemEval-S question-derived weak-route diagnostic | v48 Candidate Evidence Map 全弱路由失败；DeepSeek judge `56/87`，低于 v42 same-87 `59/87`，且 full query 估计 `6250.456` 超预算。仅 current_state 子集正向，转 v49 current-state-only。 |
| `v49_current_state_candidate_map_lme_5993d30` | 22 条 LongMemEval-S question-derived current_state diagnostic | v49 current-state-only Candidate Evidence Map 弱正向但不够主线；DeepSeek judge `13/22`，高于 v42 same-22 `12/22`，gain/loss `3/2`，full query 估计 `5884.492`。有 temporal/order regression，不跑 full，顶层 config 已删除。 |
| `v50_profile_advice_memory_guide_lme_pref_81351ef` | 30 条 LongMemEval-S single-session-preference diagnostic | v50 advice/profile route + source-linked build memory guide 失败；DeepSeek judge `12/30`，低于 v42 same-30 `13/30`，gain/loss `1/2`。说明 personalized advice 需要更可靠的 build-side profile/event memory，而不是更多 reader guide。 |
| `v51_profile_repair_lme_pref_79b1424` | 30 条 LongMemEval-S single-session-preference diagnostic | v51 profile/advice answer repair 有正向质量信号；DeepSeek judge `16/30`，高于 v42 same-30 `13/30`，repair applied draft `0/6` -> final `3/6`。但 avg_query_tokens `8382.667` 超预算，不跑 full；下一步收窄触发并压缩 repair context。 |
| `v52_profile_uncertain_repair_lme_pref_aa0f67c` | 30 条 LongMemEval-S single-session-preference diagnostic | v52 只在 profile/advice draft 拒答/unknown/missing 时 repair；DeepSeek judge `15/30`，高于 v42 same-30 `13/30`，avg_query_tokens `5954.533`，repair triggered `6/30`。后续 full 已证明整体负向。 |
| `v84_advice_turn_window_lme_pref30_61bccf2` | 30 条 LongMemEval-S single-session-preference diagnostic | v84 在 v83 上开启 advice query gated adjacent-turn BM25 window；DeepSeek judge `14/30`，高于 v83 same30 `13/30`，changed subset `WRONG->CORRECT 2`、`CORRECT->WRONG 1`。信号太弱且 prediction_changed `17/30`，不扩 full，顶层 config 删除。 |
| `v85_advice_source_anchor_lme_pref30_eda7838` | 30 条 LongMemEval-S single-session-preference diagnostic | v85 在 v83 上启用 build-memory source-anchor evidence ordering；DeepSeek judge `14/30`，与 v84 持平且只比 v83 same30 高 1。相对 v83 prediction_changed `25/30`、净 `+1`，扰动太大，不扩 full，顶层 config 删除。 |
| `v86_chronological_context_lme_qtext311_d7bd5e2` | 311 条 LongMemEval-S question-text aggregation/time/current diagnostic | v86 对 `list_count`/`temporal_lookup`/`current_state` 启用 chronological session-thread context layout；DeepSeek judge `230/311`，低于 v83 same311 `239/311` 和 v80 same311 `236/311`，prediction_changed `102/311`。局部修复时间线和 current-state，但 list/count regression 更多，不扩 full，顶层 config 删除。 |
| `v87_temporal_current_candidate_guide_lme_qtext311_ad56974` | 311 条 LongMemEval-S question-text aggregation/time/current diagnostic | v87 保留 retrieval-rank context，只对 `temporal_lookup`/`current_state` 加 Candidate Evidence Map；DeepSeek judge `236/311`，与 v80 same311 持平但低于 v83 same311 `239/311`，avg_query_tokens `6655.453`。比 v86 稳但不够好，不扩 full，顶层 config 删除。 |
| `v53_scoped_evidence_lme_diag_4db0bde` | 106 条 LongMemEval-S question-derived temporal/list diagnostic | v53 scoped evidence 两阶段回答失败；DeepSeek judge `63/106`，低于 v42 same-106 `81/106`，gain/loss `5/23`。token gate 和 clean scan 通过，但 extracted JSON 替代 raw evidence 后边界错误被放大，不跑 full，顶层 config 已删除。 |
| `v54_turn_window_lme_weakroute_fc48b22` | 87 条 LongMemEval-S question-derived weak-route diagnostic | v54 adjacent-turn window BM25 retrieval 持平 v42 same87；DeepSeek judge `59/87`，gain/loss `7/7`，avg_query_tokens `5959.874`。有局部 list/count 正向，但不稳定，不跑 full。 |
| `v55_turn_window_dense32_lme_weakroute_be846f3` | 87 条 LongMemEval-S question-derived weak-route diagnostic | v55 恢复 dense `protect_top_n=32` 后失败；DeepSeek judge `57/87`，低于 v42/v54 same87，avg_query_tokens `6000.310` 略超预算。停止当前 turn-window 参数方向。 |
| `v56_lossless_atomic_lme_weakroute_194dfa8` | 87 条 LongMemEval-S question-derived weak-route diagnostic | v56 build-side lossless atomic memory 失败；DeepSeek judge `57/87`，低于 v42 same87 `59/87`，gain/loss `4/6`，avg_build_tokens `107052.839`，avg_query_tokens `6007.575`。更多 atomic records 没转化为 accuracy，顶层 config 删除。 |
| `v57_target_completeness_lme_weakroute_73ac1bd` | 87 条 LongMemEval-S question-derived weak-route diagnostic | v57 query-side target-completeness checklist 持平 v42 same87；DeepSeek judge `59/87`，gain/loss `5/5`，answer_changed `28`，avg_query_tokens `6270.575` 超 6K。说明继续加 answer checklist 不值得，顶层 config 删除。 |
| `v58_rerank_lme_weakroute_da73814` | 87 条 LongMemEval-S question-derived weak-route diagnostic | v58 clean rerank retrieval 失败；DeepSeek judge `55/87`，低于 v42 same87 `59/87`，gain/loss `6/10`，avg_query_tokens `5898.540`。rerank 对 temporal 小正向，但损害 list_count 和 profile_preference 覆盖；不跑 full，顶层 config 删除。 |
| `v59_source_anchor_lme_weakroute_b086fea` | 87 条 LongMemEval-S question-derived weak-route diagnostic | v59 provenance alignment + source-anchor coverage 失败；DeepSeek judge `55/87`，低于 v42 same87 `59/87`，gain/loss `4/8`，avg_query_tokens `6065.920` 超 6K。source alignment 修复局部 current-state，但全路由 source-anchor 损害 list/profile 覆盖；不跑 full，顶层 config 删除。 |
| `v60_dialogue_temporal_lme_weakroute_fb0376b` | 87 条 LongMemEval-S question-derived weak-route diagnostic | v60 dialogue inference + temporal order reader contract 失败；DeepSeek judge `58/87`，低于 v42 same87 `59/87`，gain/loss `6/7`，avg_query_tokens `6202.195` 超 6K。current_state 小正向不足以抵消 list/profile 回退；不跑 full，顶层 config 删除。 |
| `v61_fact_operation_lme_diag_2dcb668` | 33 条 LongMemEval-S question-derived fact operation diagnostic | v61 fact_lookup operation workpad gate 中性；DeepSeek judge `27/33`，与 v42 same33 持平，gain/loss `2/2`，avg_query_tokens `5694.030`。收益上限小且不稳定；不跑 full，顶层 config 删除。 |
| `v62_dialogue_episode_fact_lme_diag_4293e55` | 183 条 LongMemEval-S question-derived fact_lookup diagnostic | v62 dialogue episode layout 失败；DeepSeek judge `141/183`，低于 v42 same183 `150/183`，gain/loss `8/17`，avg_query_tokens `6220.005` 超 6K。更长的 episode prompt 增加歧义，源码分支已删除。 |
| `v64_list_count_turn_window_lme_diag_f7eb691` | 119 条 LongMemEval-S question-derived list_count diagnostic | v64 list_count-only adjacent-turn window BM25 失败；DeepSeek judge `93/119`，低于 v42 same119 `95/119`，gain/loss `5/7`，avg_query_tokens `5648.555`。相邻窗口修复少量漏项但引入更多回退，不跑 full。 |

## 保留正式结果

| run | benchmark | subset | commit | accuracy | 主要结论 |
|---|---|---|---|---:|---|
| `stage1_update_conflict_guide_v80_lme_s_full_152b0e5` | LongMemEval-S | full | `152b0e5` | 0.792000 | 当前 LME 最好；v79 上的 source-preserving update/conflict chain，触发 60/500，changed subset `WRONG->CORRECT 7`、`CORRECT->WRONG 4`，avg query tokens 5913.516 仍在 6K 内。 |
| `stage1_personalized_advice_contract_v83_lme_s_full_65eebda` | LongMemEval-S | full | `65eebda` | 0.792000 | v81 代码线 + personalized advice reader discipline；触发 29/500，accuracy 与 v80 持平，但 changed subset 相对 v81 净 -2，不作为新 best。 |
| `stage1_update_conflict_value_slot_v81_lme_s_full_d6f0f93` | LongMemEval-S | full | `d6f0f93` | 0.790000 | v80 的 value-slot 收窄诊断；guide 触发 44/500，changed subset `WRONG->CORRECT 3`、`CORRECT->WRONG 1`，但 fresh full judge 低于 v80，不作为当前 best。 |
| `stage1_fact_operation_workpad_v82_lme_s_full_f2e042f` | LongMemEval-S | full | `f2e042f` | 0.786000 | v81 + fact_lookup operation workpad；changed subset 相对 v81 为 `WRONG->CORRECT 1`、`CORRECT->WRONG 2`，低于 v80/v81，负向，顶层 config 删除。 |
| `stage1_missing_detail_finalizer_v79_lme_s_full_7b34339` | LongMemEval-S | full | `7b34339` | 0.784000 | v80 前 LME 最好；v73 上的 missing-detail finalizer，prediction_changed 29/500，changed subset `WRONG->CORRECT 6`、`CORRECT->WRONG 0`，零额外 prediction LLM token。 |
| `stage1_finalizer_duration_fix_v73_lme_s_full_24396f9` | LongMemEval-S | full | `24396f9` | 0.778000 | v79 前 LME 最好和关键对照；只关闭 v42 中有害的机械 duration rounding finalizer，prediction_changed 1/500，token 不增加。 |
| `stage1_missing_reason_enrichment_v77_lme_s_full_f669b91` | LongMemEval-S | full | `f669b91` | 0.772000 | v73 上的 missing reason enrichment；零额外 token 但 changed subset 4 gain / 4 loss，fresh full 低于 v73，源码/config 删除。 |
| `stage1_profile_uncertain_compact_repair_v76_lme_s_full_5e1d4eb` | LongMemEval-S | full | `5e1d4eb` | 0.768000 | v75 的 uncertain-only profile repair；token 合格、controlled changed subset 轻微正向，但 fresh full 低于 v73，不进主线。 |
| `stage1_profile_compact_repair_v75_lme_s_full_f21f16b` | LongMemEval-S | full | `f21f16b` | 0.766000 | all-profile compact repair；changed subset 有信号，但会误伤已支持的个性化答案，avg query tokens 接近 6K，不进主线。 |
| `stage1_build4k_r20_v74_lme_s_full_8e4c88e` | LongMemEval-S | full | `8e4c88e` | 0.766000 | build 输出 2K->4K 消融；build tokens 增加但 accuracy 下降，evidence recall 不变，不进主线。 |
| `stage1_operation_workpad_v42_repro_fix_lme_s_full_d6c6e8e` | LongMemEval-S | full | `d6c6e8e` | 0.772000 | v42 复现修复控制，不是新方法；prediction 与原 v42 500/500 相同。judge 重跑比原 v42 少 1 条正确，属于同答案 judge variance。 |
| `stage1_operation_workpad_v42_lme_s_full_f7eb076` | LongMemEval-S | full | `f7eb076` | 0.774000 | v73 前 LME 最好；v36 上的短 operation workpad，vs v36 净 +1，收益很小，不能视为突破。 |
| `stage1_temporal_order_router_v71_lme_s_full_6e75890` | LongMemEval-S | full | `6e75890` | 0.770000 | v42 上的 temporal-order route 修正；changed subset 1 gain / 1 loss，整体中性。顶层 config 和 src route 改动撤出主线。 |
| `stage1_route_snippet_compact_v70_lme_s_full_6db4d31` | LongMemEval-S | full | `6db4d31` | 0.758000 | v42 上的 route-scoped query snippet 压缩；seeded cache 控制后只改 26 条 prediction，但 list_count 损失明显，顶层 config 删除。 |
| `stage1_supported_uncertain_repair_v69_lme_s_full_cd1fbbf` | LongMemEval-S | full | `cd1fbbf` | 0.760000 | v42 上的 supported uncertain repair；6 条实际改动中修复 2 条拒答，但 full judge 低于 v42，且 profile/preference repair 有 unsupported 泛化风险。顶层 config 删除。 |
| `stage1_route_context_budget_v66_lme_s_full_dd1320e` | LongMemEval-S | full | `dd1320e` | 0.754000 | v42 上的 route-aware context budget；avg query tokens 降到 5235.538，但 accuracy 净 -9。说明固定截断会丢失 answer 需要的细节，顶层 config 删除。 |
| `stage1_unit_sum_finalizer_v65_lme_s_full_45851fd` | LongMemEval-S | full | `45851fd` | 0.758000 | v42 上的 unit/sum mechanical finalizer 候选；低于 v42，gain/loss 20/28，answer_changed 120。负向且不是纯 finalizer 正向消融，源码/config 删除。 |
| `stage1_uncertain_repair_v63_lme_s_full_9ebc02c` | LongMemEval-S | full | `9ebc02c` | 0.766000 | v42 上的 uncertain-only answer repair；vs v42 gained/lost 18/22，net -4，avg_query_tokens 6349.876 超 6K。负向且超预算，顶层 config 删除。 |
| `stage1_lme_token_safe_format_guard_v36_lme_s_full_4af3244` | LongMemEval-S | full | `4af3244` | 0.772000 | v42 前 LME 最好和当前强 baseline；v28 top40/evidence budget + v35 answer guard，vs v28 净 +3；仍未达 0.80。 |
| `stage1_profile_uncertain_repair_v52_lme_s_full_9a04884` | LongMemEval-S | full | `9a04884` | 0.770000 | v42 上的 token-safe profile/advice repair；same30 正向但 full 负向，vs v42 净 -2，answer_changed 106。删除顶层 config，不跑 LoCoMo。 |
| `stage1_route_snippet_top60_v38_lme_s_full_daf98e7` | LongMemEval-S | full | `daf98e7` | 0.752000 | v36 上的 route-scoped top60 + snippet；vs v36 净 -10，list/temporal 噪声损失大于 coverage 收益，负向 ablation。 |
| `stage1_route_scoped_evidence_detail_v40_lme_s_full_1559c80` | LongMemEval-S | full | `1559c80` | 0.742000 | v36 上的 route-scoped detailed evidence_report；vs v36 净 -15，reader-side 规则不足以稳定提升 list/temporal，不跑 LoCoMo。 |
| `stage1_row_memory_bundle_v37_lme_s_full_7f1fea6` | LongMemEval-S | full | `7f1fea6` | 0.744000 | v36 上的 row-linked build memory bundle；typed memory prompt 化导致 temporal/list/current_state 回退，负向 ablation，不跑 LoCoMo。 |
| `stage1_memory_aware_selector_v39_lme_s_full_800421f` | LongMemEval-S | full | `800421f` | 0.724000 | v36 上的 memory-aware source selector；vs v36 净 -24，list/temporal final row order 噪声明显，负向 ablation，不跑 LoCoMo。 |
| `stage1_evidence_report_contract_v28_lme_s_full_9917c22` | LongMemEval-S | full | `9917c22` | 0.766000 | v36 前 LME 最好；vs v18 净 +17，vs v26 净 +10；仍未达 0.80。 |
| `stage1_budgeted_selected_context_v96_lme_s_full_e04d28b` | LongMemEval-S | full | `e04d28b` | 0.760000 | v96 同 config 的 LME 验证；低于 v88 `0.800` 且 avg_query_tokens 6126.760 略超 6K。evidence recall 1.0，说明回退来自 reader/context organization，不是召回缺失。 |
| `stage1_selected_context_v95_lme_s_full_790975f` | LongMemEval-S | full | `790975f` | 0.772000 | v95 同 config 的 LME 验证；低于 v88 `0.800`，avg_query_tokens 7441.176 超 6K。evidence recall 1.0 但 reader 噪声增加，不能作为主线。 |
| `stage1_budgeted_selected_context_v96_locomo_nonadv_full_3c146bd` | LoCoMo | non-adversarial full | `3c146bd` | 0.800000 | 当前 LoCoMo 最好；v95 selected context 的 token-safe 收窄，最多 6 行/邻接 120 字符，avg_query_tokens 5496.281。相对 v95 +21 correct，changed-prediction subset 净 +17；LME full 待验证。 |
| `stage1_selected_context_v95_locomo_nonadv_full_43ee885` | LoCoMo | non-adversarial full | `43ee885` | 0.786364 | v96 前 LoCoMo 最好；v94/v35 底座 + broad collection routing + selected-row local dialogue context。相对 v94 fresh full +5，changed-prediction subset 净 +10；avg_query_tokens 5974.314 接近预算。LME 同 config 已负向/超预算，因此不是统一主线。 |
| `stage1_relative_time_finalizer_v94_prompt_compat_locomo_nonadv_full_4299ac8` | LoCoMo | non-adversarial full | `4299ac8` | 0.783117 | v95 前 LoCoMo 最好；v35 + conservative relative-time finalizer。fresh full `1206/1540`，controlled vs v35 `1204/1540`，changed subset 净 +3，avg query tokens 4920.573。 |
| `stage1_answer_format_guard_v35_locomo_nonadv_full_80158a9` | LoCoMo | non-adversarial full | `80158a9` | 0.780377 | LoCoMo 强 baseline；valid-only 达 0.78，invalid-as-wrong 1201/1540 = 0.779870，close-margin。 |
| `stage1_relative_time_finalizer_v94_locomo_nonadv_full_11b53e9` | LoCoMo | non-adversarial full | `11b53e9` | 0.771429 | prompt/cache 漂移修复前的 v94 诊断；相对当时 current-v35 replay 弱正向 +3，但不作为当前结论。 |
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
