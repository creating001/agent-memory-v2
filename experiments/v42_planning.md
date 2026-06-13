# v42 规划：Evidence Report + Operation Workpad

## 背景

v41 question-only router 的 gate 没有带来 accuracy 诊断收益：同一 LongMemEval-S route-stratified 20 条上，v36=`14/20`、v41=`14/20`，但 v41 增加了 `331.05` avg query tokens。因此继续堆 query router 不划算。

v36 full 的 badcase 更像是 evidence aggregation 问题：
- count/quantity：`59/114` wrong 带 count_or_quantity tag。
- temporal：`57/114` wrong 带 temporal tag。
- large_context：`70/114` wrong 带 large_context tag。

两个代表性错案：
- “How many items of clothing do I need to pick up or return from a store?” gold=3，v36 evidence_report 漏掉 dry cleaning blazer pickup。
- “How many projects have I led or am currently leading?” gold=2，v36 evidence_report 把 completed project 排除掉，因为它不是 current；这违反了问题里 “have led or am currently leading” 的 inclusive scope。

这些错案说明：证据在 context 中时，reader 仍可能没有稳定执行“先确定操作语义、再聚合所有 in-scope candidates”。v42 只尝试加强这个通用操作纪律，不新增 retrieval、不新增 LLM call、不扩大 top-k。

## 外部方法参考

- `creating001-agent-memory`：参考 evidence-first answer organization 和 include/exclude/missing 的通用结构；不迁移 benchmark 字段、target-phrase 样本规则或 finalizer。
- SimpleMem：参考 Intent-Aware Retrieval Planning 中“先理解 query operation，再组织 evidence”的思想；v42 不引入额外 planning LLM，只用 prompt 内部 workpad。
- Mnemis：list/count/all 类问题需要覆盖完整集合而不是早停在相似证据；v42 用 operation workpad 提醒 reader 检查所有 in-scope candidates。
- xMemory：decoupling before aggregation；v42 不做新 build，只在 answer 前强化 aggregation 语义。

## 方法设计

底座：v36 `stage1_lme_token_safe_format_guard_v36_cached`。

代码改动：
- 允许 `compiler.operation_workpad=true` 在 `evidence_report_contract=true` 时同时生效。
- `Private Operation Discipline` 仍不改变输出 schema，只是 answer model 内部 checklist。
- 对 list/count/sum/comparison 加一条通用 inclusive alternatives 语义：
  - 如果问题使用 `or`、`have done or currently doing`、`past or current` 这类 inclusive alternatives，要包括满足任一请求条件的候选；不能仅因为某项不是 current 就排除 past item。

配置改动：
- `configs/stage1_operation_workpad_v42_cached.json`
- `operation_workpad=true`
- `operation_workpad_information_needs=["list_count","temporal_lookup"]`
- answer cache 使用独立 namespace `stage1_operation_workpad_v42_qwen3_30b`

不改变：
- build memory
- retrieval top-k
- dense/BM25 fusion
- evidence_report schema
- answer max input/output `131072/16384`
- finalizer 策略

## Clean 边界

- 只读取 question text、question_time、retrieved raw Memory Context 和 build-time typed memory source signals。
- 不使用 hidden benchmark metadata、reference solutions、offline evaluator output、row identifiers、test feedback 或样本级规则。
- 规则是通用自然语言操作语义，不包含具体测试实体、答案、record key 或 benchmark-specific route。
- DeepSeek judge 只用于预测完成后的离线比较，不进入 prediction pipeline。

## 风险

- v40 已证明“更详细 reader 规则”可能伤害整体 accuracy；v42 必须保持规则短、route-scoped、可关闭。
- prompt 增加会推高 query tokens；v36 LME avg query `5715.468`，v42 gate 必须确认仍 <= `6000`。
- 如果根因是 retrieval miss 或 evidence order，operation workpad 不会解决。

## Gate 计划

先跑 LongMemEval-S route-stratified 20 条 diagnostic：

- input：`outputs/diagnostic/v35_lme_route_stratified_probe/prediction_input.jsonl`
- config：`configs/stage1_operation_workpad_v42_cached.json`
- workers：`4`

通过条件：
- 20/20 prediction 成功。
- answer max input/output = `131072/16384`。
- avg query tokens <= `6000`，max query tokens < `8000`。
- operation_workpad 只出现在 `list_count` / `temporal_lookup` prompts。
- 同子集 DeepSeek judge 相对 v36 有净收益，或至少修复关键 count/list badcase 且无明显新增错；否则不跑 full。

## Gate 结果

Run：`v42_operation_workpad_lme_probe_df25f6a`

- commit：`df25f6a8198af35ff7498f3d4ca505b1f8014bd2`
- dirty：True，仅用户修改的 `docs/architecture.md` 和 `docs/clean_protocol.md` 未提交。
- prediction：20/20 成功。
- answer max input/output：`131072/16384`。
- avg_build_tokens：`81690.45`。
- avg_query_tokens：`5660.25`。
- max_query_tokens：`6908`。
- weighted LME full avg query estimate：`5668.1925`。
- operation_workpad 生效范围：`list_count 4/4`，`temporal_lookup 4/4`；其他 route `0/12`。
- prompt clean scan：无 hidden metadata 命中；`category` 仅来自原始对话普通词。
- 同子集 DeepSeek judge：v36=`14/20`，v42=`15/20`，delta=`+1`。
- answer_changed：`6/20`；gained `1`、lost `0`。
- 关键 gained case：Costa Rica 5-day trip shirt count，从 insufficient 改为 `7`。

结论：v42 满足 token gate，有净正向诊断信号，且无同子集 judge regression。下一步跑 LongMemEval-S full；若 full 不负向且 token 合格，再考虑 LoCoMo non-adversarial full。
