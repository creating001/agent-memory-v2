# v53 规划：Scoped Evidence 两阶段回答

## 背景

v42 是当前 LongMemEval-S full 最好结果：DeepSeek judge accuracy `387/500 = 0.774`，avg build tokens `80346.246`，avg query tokens `5865.644`，仍未达到 `0.80` baseline target。

v47 证明把聚合字段塞进同一个 answer schema 并用机械 finalizer 纠错是负向：同 106 条 temporal/list 诊断从 v42 `81/106` 退到 `75/106`，主要问题是 answer model 自报 `count_increment` 不稳定、重复计数和 token 增长。v52 也证明 answer-side repair 在小子集可正向，但 full 不稳定。

重新看 v42 badcase 后，关键失败不是完全没有召回证据，而是证据使用不稳定：

- exact-date 题可能选了宽泛月份，漏掉同事件更具体日期。
- sum/count 题可能漏掉 top-12 之外的低显著 operands。
- list/order 题可能在已有 top-40 里漏掉一项。
- assistant suggestion 与 user confirmation 需要分清，不能把建议直接当事实。

因此 v53 不再扩大单次 answer prompt，也不做机械 finalizer。它把 query-time compiler 拆成两步：先从可见 Memory Context 中抽取 scoped evidence，再只基于抽取 JSON 回答。

## 方法设计

底座：v42 operation workpad。

新增配置：`configs/stage1_scoped_evidence_v53_cached.json`

新增模块：

- `scoped_evidence.enabled=true`
- `scoped_evidence.information_needs=["list_count","temporal_lookup"]`
- `scoped_evidence.max_rows=40`
- `scoped_evidence.max_row_chars=260`
- extractor 使用本地 Qwen，从 top-40 Memory Context 里抽取 `included_items`、`excluded_items`、`canonical_item`、`mention_date`、`event_time`、`value`、`calculation` 和 `missing_info`。
- answer stage 只读取 extracted evidence JSON，输出简洁 JSON answer。

v53 的目标不是让派生 memory 替代原文，而是把 already-retrieved raw evidence 做成更稳定的 answer interface。build-stage typed memory、dense+BM25 retrieval、source expansion 和 v42 compiler 仍保留，保证 build 阶段 LLM 继续参与。

## 外部方法参考

- `external/creating001-agent-memory`：重点参考其 query 侧先组织 included/excluded/canonical evidence 再回答的思路，以及区分 assistant suggestion、event time 和 mention date 的 query discipline。舍弃 target phrase、category、sample-level guardrail、benchmark 字段、gold/judge 相关逻辑。
- `external/SimpleMem`：参考 build lossless memory units、hybrid retriever 和 structured context answer 的工程组织；v53 不引入额外 query planner，避免 token 继续膨胀。
- `docs/method.md` 推荐主线：优先强化 query-time evidence compiler 和 source expansion；v53 正是对 `retrieve + evidence table + answer` 的轻量实现。

## Clean 边界

- prediction 只使用 question text、question_time、raw dialogue、build-stage memory source links、retrieved evidence rows 和 question-derived information_need。
- 不读取 gold answer、judge output、benchmark label、question_type、category、sample id、qid、真实 dataset row index 或 test feedback。
- local `Memory 1/2/...` 只是当前 prompt 内的临时证据标签，不是 benchmark row index。
- badcase 只用于离线方法设计，不把具体测试实体、答案或样本规则写进 prompt/config。

## 预期收益

- `temporal_lookup`：更稳定地区分 mention date 与 event time；同事件宽时间和具体时间同时出现时优先具体时间。
- `list_count`：先抽 distinct operands，再计算或枚举，降低漏项和重复计数。
- `sum/count/order`：让模型先显式列出 included/excluded，再回答，减少最终答案和证据不一致。

## 风险

- 两阶段 LLM 会增加 query tokens；v42 full 平均只剩约 134 token 空间，v53 大概率只能在部分 route 上使用。
- extractor 如果把错误证据写进 JSON，第二阶段 answer 没有原文兜底，可能放大 extractor 错误。
- 如果 extraction JSON 太长，answer stage 仍可能超预算。

## Gate 计划

先做诊断，不直接跑 full：

1. 使用 LongMemEval-S `temporal_aggregation_106` 诊断输入。该输入按 question-derived route/pattern 构造，覆盖 temporal/list/count/sum/order 类型，不把 gold/judge 信息传入 prediction。
2. 跑 v53 prediction，检查 answer max input/output 是否为 `131072/16384`，avg query tokens、scoped evidence 触发率、extract/answer cache 和 build token 记录是否正确。
3. 做 prompt clean scan，确认 prediction prompt 不含 gold/judge/benchmark label/sample id/qid/真实 row index。
4. 用 DeepSeek judge 离线比较 v53 与 v42 same-106 accuracy、gain/loss、changed-answer。
5. 只有在 same-set accuracy 明确净正、query token 估计不超过 6K、regression 可解释时，才考虑 LongMemEval-S full。

通过条件：

- prediction 全成功。
- DeepSeek judge accuracy 相对 v42 same set 净正向，不能只靠 same-answer judge variance。
- full avg query token 估计不超过 `6K`；超过 `8K` 只能视作 expensive diagnostic。
- scoped evidence 的 token 成本在 summary/metrics/diagnosis 中单独记录。

如果 v53 失败，删除顶层候选配置，只保留诊断目录里的 `config_snapshot.json` 和本 planning 结论。下一步转向 build-side typed temporal/entity/profile memory 的更强 management，而不是继续加长 answer prompt。

## 诊断结果

v53 已完成 LongMemEval-S `temporal_aggregation_106` 诊断，结论为失败，不进入 full。

- v42 same-106 DeepSeek judge accuracy: `81/106 = 0.764151`
- v47 same-106 DeepSeek judge accuracy: `75/106 = 0.707547`
- v53 same-106 DeepSeek judge accuracy: `63/106 = 0.594340`
- v53 vs v42 gain/loss: `5 / 23`
- answer_changed vs v42: `68`
- avg_build_tokens: `79953.094340`
- avg_query_tokens: `5113.226415`
- scoped extraction avg query tokens: `4025.603774`
- scoped answer avg query tokens: `1087.622642`
- prompt clean scan: `2` findings, both raw-dialogue `correct answer` false positives

按离线 question_type：

- temporal-reasoning: v42 `49/56` -> v53 `42/56`
- multi-session: v42 `23/40` -> v53 `15/40`
- knowledge-update: v42 `4/5` -> v53 `2/5`
- single-session-user: v42 `5/5` -> v53 `4/5`

决策：

- 不跑 LongMemEval-S full。
- 删除顶层候选配置 `configs/stage1_scoped_evidence_v53_cached.json`，只保留诊断目录里的 `config_snapshot.json`。
- 保留 `scoped_evidence` 代码作为可消融工具，但不把 extracted JSON 作为唯一 answer input。
- 下一步转向 build-side typed temporal/entity/state memory management，query 阶段用派生 memory 扩展和组织 raw evidence，而不是替代 raw evidence。
