# v32 Selective Repair Planning

## 目标

v31 证明“无差别加长 evidence_report prompt”会提升部分 evidence use，但整体低于 v29：source coverage 没回退，主要失败点是 answer/compiler 过度保守、列表缩窄和 temporal 相邻时间误选。因此 v32 回到 v29 作为主线底座，只新增 query-side selective verifier/repair。

核心目标：

- 保持 v29 build memory、retrieval、compiler 和 draft answer prompt 不变。
- 不重新 build memory，不增加 build token。
- 只在运行时高风险样本触发第二次 LLM 读取，其他样本保持 v29 答案。
- 所有触发条件只来自 question、route、retrieved Memory Context、draft answer 和 draft JSON。
- 正式指标仍以 DeepSeek judge accuracy 为主，同时检查 avg query tokens 不超过 6K。

## 外部方法借鉴

- creating001-agent-memory：借鉴 evidence-first 二阶段读取、include/exclude 证据表和 temporal 证据核验思路；舍弃 target phrase guardrail、benchmark 化 route、finalizer 和任何基于测试反馈的规则。
- SimpleMem：借鉴 reflection retrieval / hybrid evidence use 的思想，即只在初始证据使用不稳定时做补充推理；舍弃其 benchmark/category adapter。
- DeepResearch / IterResearch 类方法：借鉴 “draft -> reflect completeness -> revise/keep” 的闭环，但 v32 不做多轮检索扩张，只做一次 answer-side verifier，控制 token。
- Memento / failure-aware reflection：借鉴 failure mode 作为通用运行时风险信号；不把 judge 结果或样本级经验写入预测流程。
- `docs/method.md`：对应 `retrieve + evidence table + verifier` 路线，重点记录 verifier 改对/改错比例、触发率和 token 成本。

## Badcase 启发

离线分析只在 prediction 后读取 judge/label，用于方法设计，不进入预测代码。v31 与 v29 对照显示：

- v31 修对的主要是 v29 `unknown`、拒答、短答案、证据存在但 draft 没用好的样本。
- v31 改错的主要是 v29 已经可接受的宽列表答案被缩窄、temporal 相邻日期误选、profile/fact 过度保守。
- 所以 v32 不采用 v31 的全局 detailed prompt，而是只对高风险 draft 做二次 verifier。

基于 v29 draft 的 clean 运行时触发器做离线体检：

- 触发率约 `424/1540 = 27.5%`，在 token 预算可控范围内。
- 如果粗略用 v31 作为触发样本替代答案，离线投影约 `1183/1540 = 0.7682`，比 v29 `1173/1540` 高 `+10`，但仍需真实 v32 repair prompt 验证。
- 该投影只用于决定是否值得跑 v32；预测代码不读取 judge、gold、category、sample id 或样本级规则。

## 方法设计

新增 `answer.repair`，默认关闭。启用后流程为：

1. v29 原流程生成 draft answer 和 draft JSON。
2. 根据通用运行时信号判断是否触发 repair：
   - draft answer/JSON 表示 unknown、insufficient、missing。
   - collection/list 问题返回过短答案。
   - temporal route 中 answer_type 与时间问题不匹配，或 evidence_report 里出现多个 support event_time/value。
3. 触发时构造 repair prompt，包含 question、question_time、information_need、trigger reasons、draft answer、draft JSON、retrieved Memory Context。
4. repair LLM 输出 `decision=keep|revise` 和 final answer。
5. 无论 keep 还是 revise，repair response token 都计入 query token；trace 保留 draft、repair response、final answer、触发原因、cache delta。

## 配置

`configs/stage1_selective_repair_v32_cached.json`：

- build_memory 复用 v29 namespace: `stage1_agent_memory_v1_qwen3_30b_cold`
- draft answer 复用 v29 cache: `outputs/cache/qwen3_answer_v29.sqlite`
- repair cache: `outputs/cache/qwen3_answer_repair_v32.sqlite`
- answer / repair model: `Qwen/Qwen3-30B-A3B-Instruct-2507`
- answer / repair max input/output: `131072/16384`
- repair context cap: `max_context_chars=14000`, `max_row_text_chars=700`
- finalizer 关闭，避免把 verifier 和机械修正混在一个 ablation。

## Gate

先跑 no-label diagnostic：

- 输入使用 route-stratified prediction input，不读取 labels/gold/judge/category/sample id。
- 检查 repair trace 是否存在、触发率是否接近预期、avg query tokens 是否小于 6K。
- 检查 build cache logical token 统计是否正常，answer max input/output 是否仍为 `131072/16384`。
- 如果 gate 通过，跑 LoCoMo non-adversarial full；只有 LoCoMo 有正向且 token 合格，再跑 LongMemEval-S full。

## 2026-06-14 Gate 结果

第一版触发器过宽，20 条 no-label probe 中触发 `8/20`，avg query tokens `6117.55` 超过 6K，且 8 次 repair 全部 keep。该失败 gate 已删除，不作为保留实验记录。

随后收窄 `short_collection_answer`：

- 不再把任意 `what/which` 问句视为集合问题。
- 明确数字 count answer 不再因 short trigger 触发。
- 只保留真正复数/集合名词问题，或 `has/have/had + collection action` 形态。

通过 gate：`v32_selective_repair_probe_7cde029`

- samples: `20/20`
- avg build tokens: `63181.8`
- avg query tokens: `5017.3`
- build cache: hits `128`, misses `0`, writes `0`
- draft answer cache: hits `20`, misses `0`, writes `0`
- repair triggered: `1/20 = 0.05`
- repair applied: `0/20`
- repair query tokens: total `3596`, avg when triggered `3596.0`
- answer max input/output: `131072/16384`
- repair max input/output: `131072/16384`
- dirty: 仅用户编辑的 `docs/architecture.md` 与 `docs/clean_protocol.md`，以及本次诊断输出。

用 v29 full traces 做离线风险体检，新触发器预计触发 `258/1540 = 16.75%`。若粗略用 v31 答案替换触发样本，投影 `1186/1540 = 0.7701`，相对 v29 净 `+13`。该投影只用于判断 v32 值得跑 full；预测阶段不读取 judge、gold、category、sample id 或样本级规则。

结论：v32 通过 no-label/token gate，可以跑 LoCoMo non-adversarial full。若 LoCoMo full accuracy 正向并且 avg query tokens <= 6K，再补 LongMemEval-S full。

## 2026-06-14 LoCoMo full 结果

严格 draft-cache 对照版 run：`stage1_selective_repair_v32_locomo_nonadv_full_a80816a`

- commit: `a80816a`
- dirty: 用户编辑的 `docs/architecture.md`、`docs/clean_protocol.md`，以及本次实验输出目录
- DeepSeek judge accuracy: `0.7616883116883116`
- correct/valid/total: `1173/1540/1540`
- v29 reference: `1173/1540 = 0.7616883116883116`
- avg build tokens: `58386.00779220779`
- avg query tokens: `4466.223376623377`
- evidence recall: `0.8912760416666666`
- repair triggered: `263/1540 = 0.17077922077922078`
- repair applied: `11/1540 = 0.007142857142857143`
- repair-applied delta: fixed `3`, broken `1`, both_correct `2`, both_wrong `5`
- draft answer cache hits/misses/writes: `1540/0/0`
- repair cache hits/misses/writes: `263/0/0`

结论：v32 token 合格、clean、可追溯，但 LoCoMo full 与 v29 持平，不是性能提升。不要跑 v32 LongMemEval-S full。下一步需要设计更强的 v33：优先考虑 query-side evidence expansion / gap-aware verifier，或 build-side memory management 改进，而不是继续扩大同 context repair 的触发率。
