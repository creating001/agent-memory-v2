# v41 规划：问题文本 LLM 操作路由

## 背景

当前 LongMemEval-S full 最好结果仍是 v36：DeepSeek judge accuracy `0.772`，avg query tokens `5715.468`，离 `0.80` baseline target 还差 14 条。v37-v40 都是在 v36 上尝试让 reader 或 typed memory 更“详细”，但 full 结果连续负向，说明问题不只是 evidence 数量，而是 answer 前对问题操作、证据边界和时间/列表语义的组织不稳。

v40 相比 v36 净 `-15`，主要损失在 temporal/list/fact。典型 badcase 包括：
- count/list 边界错：把每周健身课数从 5 答成 4，把两个月内珠宝/毕业典礼/自行车服务等集合边界弄错。
- temporal/order 错：把新地毯家具时间从 1 week 答成 21 days，把最近家庭旅行误判成旧旅行。
- 细节不足：医生访问数回答成裸数字，缺少题目要求的支撑细节。

因此 v41 不继续堆 reader-side 规则，也不重跑 build。先做一个小而可消融的 query-side 改动：用 LLM 只基于 question text 和可见 question_time 生成通用操作分析，再映射到现有 information_need。

## 外部方法参考

代码参考：
- `external/creating001-agent-memory/src/agent_memory/prompts/router.py`：借鉴 question-only task / operation / answer slot 的抽象输出；舍弃任何 benchmark 字段、样本标识和样本级规则。
- `external/creating001-agent-memory/src/agent_memory/baseline/evidence_finalizer.py`：借鉴“先结构化 evidence，再做有限机械修正”的思想；v41 暂不新增 finalizer，避免把负向 v40 问题扩大。

方法卡参考：
- xMemory：decoupling before aggregation，先判断问题需要什么证据结构，再聚合 raw source；v41 只实现轻量 query intent，不引入重构建。
- SimpleMem：Intent-Aware Retrieval Planning；v41 采用问题意图规划，但只输出通用 operation，所有 token 计入 query。
- Mnemis：list/count/all 类问题需要结构覆盖，不能只靠相似度 top-k；v41 将 count/list/set_relation 优先路由到 list_count。
- Graphiti/Zep：时间状态和当前状态要区分；v41 将 recency/current 与 duration/order/date_time 分开路由。

## 方法设计

新增模块：`src/memory/question_analysis.py`。

输入：
- question text
- visible question_time

输出：
- `task`: `single_fact | multi_evidence | preference_advice | temporal | recency_state`
- `operation`: `none | count | sum | compare | list | set_relation | duration | order | date_time | preference | recency`
- `temporal_subtype`
- `answer_slot`
- `target_phrases`
- `temporal_hints`
- `confidence`

路由映射：
- `count/sum/list/set_relation/compare` -> `list_count`
- `duration/order/date_time` 或 temporal task -> `temporal_lookup`
- `recency_state/recency` -> `current_state`
- `preference_advice/preference` -> `profile_preference`
- 其他 -> `fact_lookup`

clean 边界：
- analyzer 不读 memory、gold、offline judge、hidden benchmark metadata、row identifiers 或 test feedback。
- analyzer 只做通用操作分类，不输出答案。
- analyzer token usage 计入 query tokens；cache 命中仍按 cached usage 计入逻辑方法成本。
- v41 不使用 v40 的 detailed evidence prompt，不基于 full 结果手写样本级规则。

## 预期收益与风险

预期收益：
- 修复“how many ... in a time scope”被当成纯 temporal 的路由错配。
- 修复 order/date/current-state 之间的混淆。
- 让 list/count 检索使用已有 list_count retrieval_multiplier 和 compiler 结构。

主要风险：
- 额外 LLM analyzer 可能把 LME avg query tokens 从 v36 的 `5715.468` 推过 `6000`。
- analyzer 分类错误会比启发式 route 更稳定但也可能更系统性地错。
- 如果 gate 只显示 token 合格但 route_changed 很少，full 价值不足。

## Gate 计划

先跑 LongMemEval-S route-stratified 20 条 diagnostic，不直接跑 full。

通过条件：
- prediction 20/20 成功。
- answer LLM max input/output 为 `131072/16384`。
- avg query tokens <= `6000`；如果 > `6000`，不作为主线 full，只能标 expensive/diagnostic。
- question_analysis avg query tokens、route_changed_count、cache hits/misses/writes 都记录在 metrics。
- prompt clean scan 不出现 hidden benchmark metadata 泄漏到 compiled prompt。
- build tokens 按 logical cold-build token 记录，即 cache hit 也统计 cached usage。

如果 gate 通过，再考虑 LongMemEval-S full；只有 LME full 不负向并且 token 合格，才考虑 LoCoMo non-adversarial full。
