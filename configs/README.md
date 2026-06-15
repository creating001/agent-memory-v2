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
- `stage1_answer_format_guard_v35_cached.json`：v34 上的 answer format guard；修复 JSON answer salvage 和小数 duration，LoCoMo 强 baseline。
- `stage1_relative_time_finalizer_v94_cached.json`：v35 上的 conservative relative-time finalizer；prompt-compatible full run 是当前 LoCoMo 最好。
- `stage1_selected_context_v95_cached.json`：v94/v35 底座上的当前候选；启用 question-text-only broad collection routing，并把已入选 raw turn 的同 session 相邻 turn 作为局部上下文物化，用于补全 `this/that/it/recently/last` 等承接信息。待 full 验证。
- `stage1_lme_token_safe_format_guard_v36_cached.json`：v28 top40/evidence budget + v35 answer guard；v42 前 LME 最好，也是当前强 baseline。
- `stage1_operation_workpad_v42_cached.json`：v36 上的短 operation workpad；不新增 LLM 调用，不改 retrieval/build，只在 `list_count` / `temporal_lookup` 的 evidence_report prompt 中加入通用操作聚合纪律。v73 前 LongMemEval-S full 最好，但仅比 v36 净 +1，属于 close-margin 小幅正向。
- `stage1_finalizer_duration_fix_v73_cached.json`：v79 前 LongMemEval-S 最好和关键对照；从 v42 出发只关闭有害的机械 duration decimal rounding finalizer。
- `stage1_missing_detail_finalizer_v79_cached.json`：v80 前 LongMemEval-S 最好；从 v73 出发，只在 answer JSON `sufficient=false`、`missing` 非空且 final answer 是短拒答时，把 missing 细节透出到最终答案。
- `stage1_update_conflict_guide_v80_cached.json`：v88 前 LongMemEval-S 最好；v79 上的 source-preserving update/conflict candidate chain，帮助 answer model 比较旧值、新值、更正和历史值。
- `stage1_update_conflict_value_slot_v81_cached.json`：v80 的 value-slot 收窄诊断；changed subset 正向但 full judge 未超过 v80。
- `stage1_personalized_advice_contract_v83_cached.json`：v81 代码线上的 personalized advice reader discipline；LongMemEval-S full 与 v80 accuracy 持平，但触发子集 mixed，是候选/诊断配置，不替代 v80。
- `stage1_evidence_answer_detail_v88_cached.json`：当前 LongMemEval-S 最好；v83 上的窄机械 finalizer，不改 build/retrieval/compiler/answer prompt，只在 answer JSON 已有 operands/items 时补 count detail、average、money difference 和 date endpoint duration。

## 当前候选

LongMemEval-S 当前最好是 `stage1_evidence_answer_detail_v88_cached.json`；LoCoMo 当前最好是 `stage1_relative_time_finalizer_v94_cached.json`。新方法进入顶层前必须先有 full benchmark accuracy 和 token 结果支撑。

v95 selected context 是当前待验证候选：参考 creating001 的 turn-pair/source-turn materialization、SimpleMem 的 structured raw context 和 MemU 的按信息需求检索组织，但只使用 question text、route、已检索 raw turns 及其同 session 邻接 turns，不使用 gold、judge、benchmark 标签、sample id 或样本级规则。预期解决 v94 LoCoMo badcase 中“证据行命中但代词/this book/last event 需要相邻 turn 才可读”的问题，同时用 `require_anaphora`、`max_rows` 和 `max_neighbor_chars` 控制 query token。

v94 prompt-compatible relative-time finalizer 已完成 LoCoMo full：fresh full judge `0.783117`，1206/1540；controlled comparison vs v35 为 `0.781818`，1204/1540。avg_build_tokens `58386.008`，avg_query_tokens `4920.573`，只改变 6 条 prediction，changed subset 净 +3。结论是当前 LoCoMo best，但方法收益按 controlled +3 记录，fresh full 中另有 +2 来自 judge variance。

v83 personalized advice contract 已完成 LongMemEval-S full：DeepSeek judge accuracy `0.792`，与 v80 持平，高于 v81 `0.790`；avg_build_tokens `80346.246`，avg_query_tokens `5912.794`，contract 触发 `29/500`。相对 v81 的 prediction changed subset 为 `WRONG->CORRECT 2`、`CORRECT->WRONG 4`，净负；overall +1 主要来自未改 prediction 的 fresh judge variance。结论是 best-tie 候选，不是新 best；后续 personalized advice 应转向 build-side profile/event anchoring 或 retrieval anchoring，而不是继续加 reader prompt。

v88 evidence answer detail 已完成 LongMemEval-S formal full：DeepSeek judge accuracy `0.800`，400/500；avg_build_tokens `80346.246`，avg_query_tokens `5912.794`，answer/build cache 全命中，finalizer applied `45/500`。相对 v80/v83 fresh full judge 均为净 `+4`。结论是 clean、零额外 LLM token，并首次达到 LME 0.80 baseline target。

v88 同一 config 已完成 LoCoMo non-adversarial full：DeepSeek judge accuracy `0.755844`，低于 v35 valid-only `0.780377`；avg_build_tokens `58386.008`，avg_query_tokens `3938.612`，token 合格。结论是 v88 不能作为统一主线；下一步需要设计 v89，把 v35 的 LoCoMo retrieval/format 优势与 v88 的窄 finalizer 组合后双基准 full 验证。

v82 fact-operation workpad 已完成 LongMemEval-S full：DeepSeek judge accuracy `0.786`，低于 v81 `0.790` 和 v80 `0.792`；avg_build_tokens `80346.246`，avg_query_tokens `5928.91`，token 合格。它只对 `fact_lookup` 中由问题文本触发的数值/集合操作增加 private operation workpad，但 changed subset 相对 v81 为 `WRONG->CORRECT 1`、`CORRECT->WRONG 2`。结论是负向；顶层配置删除，只保留 formal `config_snapshot.json`。

v80 已完成 LongMemEval-S full：DeepSeek judge accuracy `0.792`，396/500；avg_build_tokens `80346.246`，avg_query_tokens `5913.516`，update_conflict_guide_applied `60/500`。prediction changed subset 为 `WRONG->CORRECT 7`、`CORRECT->WRONG 4`，当前是 LME best。

v79 已完成 LongMemEval-S full：DeepSeek judge accuracy `0.784`，高于 v73 `0.778`；avg_build_tokens `80346.246`，avg_query_tokens `5864.706`，finalizer applied `29/500`。prediction changed subset 为 `WRONG->CORRECT 6`、`CORRECT->WRONG 0`，未改 prediction 的同答案 judge 方差净 `-3`。结论是 clean、零额外 prediction LLM token 的小正向，保留为当前 LME 候选，但还未达到 0.80 baseline target。

v78 structured guide row features 已完成 LongMemEval-S controlled full：DeepSeek judge accuracy `0.758`，低于 v73 `0.778`；avg query tokens `5891.06`，token 合格。changed-answer method surface 为 9 gain / 14 loss，说明浅层数量/时间 row feature 会提高候选显著性但不能稳定解决去重、scope 和 endpoint 选择。结论是负向；顶层 config 和源码开关已删除，只保留 formal `config_snapshot.json`。

v77 已完成 LongMemEval-S full：fresh DeepSeek judge accuracy `0.772`，低于 v73 `0.778`；avg query tokens 与 v73 相同，finalizer applied `42/500`。changed subset 对 v73 为 4 gain / 4 loss，controlled accuracy 持平。结论是 missing reason enrichment 不进入主线；顶层配置和源码分支已删除，只保留 formal `config_snapshot.json`。

v76 已完成 LongMemEval-S full：fresh DeepSeek judge accuracy `0.768`，低于 v73 `0.778`；avg query tokens `5880.232`，token 合格。controlled changed-prediction subset 对 v73 为轻微正向，但 fresh full 不支撑主线。v75/v76 结论是 profile repair 可作为低频拒答补救信号，但不能作为通用答案重写器；顶层配置已删除，只保留 formal `config_snapshot.json`。

v74 build 4K 输出上限消融已完成 LongMemEval-S full：DeepSeek judge accuracy `0.766`，低于 v73 `0.778`；avg_build_tokens 从 `80346.246` 增至 `84656.5`，evidence recall 仍为 `1.0`。结论是负向 build-side 消融，不进入主线；顶层配置已删除，只保留 formal `config_snapshot.json`。

正式结果必须同时报告 build token、record 数、query token、accuracy 和 cache 命中。

`stage1_finalizer_duration_fix_v73_cached.json`：从 v42 出发，只关闭机械 duration decimal rounding finalizer。badcase 显示该 finalizer 在 LongMemEval-S full 中唯一一次触发时，把 answer model 正确草稿 `3.5 weeks` 改成 `4 weeks`。v73 不改 retrieval/build/prompt，使用 v42 answer cache 做 query/finalizer 侧消融；LongMemEval-S full DeepSeek judge `0.778`，当前 LME 最好，但还未达到 `0.80` baseline target。

v71 temporal-order router 已完成 LongMemEval-S full：accuracy `0.770`，低于 v42 修复控制 `0.772`；seeded cache 控制后 prediction_changed `11/500`，changed subset `WRONG->CORRECT 1`、`CORRECT->WRONG 1`，整体中性。结论是 route-only 修正不足，顶层 config 和 src route 改动撤出主线，只保留 formal 快照。v70 route snippet compact 已完成 LongMemEval-S full：accuracy `0.758`，低于 v42 修复控制 `0.772`；seeded cache 控制后 prediction_changed `26/500`，changed subset `CORRECT->WRONG 13`、`WRONG->CORRECT 3`，主要损失来自 `list_count`。结论是纯 query snippet 压缩负向，顶层 config 删除，只保留 formal 快照。v69 supported-uncertain repair 已完成 LongMemEval-S full：full judge `0.760`，低于 v42 修复控制 `0.772`；实际改动 6 条中 `WRONG->CORRECT 2`、`WRONG->WRONG 4`，但 full judge 重跑受 same-answer variance 影响明显。结论是局部小正向但不足以作为主线，顶层 config 删除，只保留 formal 快照。v67/v68 preliminary supported-uncertain repair 因 full avg query tokens 略超 6K，不作为主线配置保留。v66 route-aware context budget 已完成 LongMemEval-S full：query token 明显下降但 accuracy 低于 v42，顶层 config 删除，只保留 formal 快照。v65 unit/sum mechanical finalizer 已完成 LongMemEval-S full：accuracy 低于 v42，且不是纯 finalizer 正向消融；顶层 config 和源码分支删除，只保留 formal 快照。v64 list_count-only adjacent-turn window BM25 也已验证负向，只保留 diagnostic 快照。

负向 formal/diagnostic 结果只保留在对应实验目录的 `config_snapshot.json` 中，不保留顶层 config。

## 新配置规则

- 不使用 gold answer、judge output、benchmark label、sample id、qid、row index 或 test feedback。
- 关键开关显式写入配置，便于 ablation。
- 如果只是一次负向诊断，不长期保留配置文件；结论写入 `experiments/README.md` 或对应实验记录即可。
- 正式实验必须把实际运行配置保存到 `experiments/formal/<run_id>/config_snapshot.json`。
- 任何会影响 prompt、answer parsing、finalizer 或 repair 的改动，都不能默认复用旧 answer cache 来证明等价；需要更换 cache namespace，或显式做 prediction-level 复现对比并记录结论。
