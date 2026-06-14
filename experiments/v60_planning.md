# v60 规划：Dialogue + Temporal Reader Contract

## 背景

当前 LongMemEval-S full 最好是 v42：DeepSeek judge `387/500 = 0.774`，avg build tokens `80346.246`，avg query tokens `5865.644`。v59 provenance alignment + source-anchor 在 `weak_route_87` 上失败：`55/87`，低于 v42 same87 `59/87`，并且 avg query tokens `6065.920` 超过 6K 软预算。

v59 badcase 说明，继续调整 source ordering / source anchor 不是主矛盾。很多 loss 的 top evidence row 与 v42 相同，错误来自 answer reader 对已召回证据的使用不稳：相邻 turns 不能合并、assistant acknowledgement 被过度忽略、current-state 新旧事实选择不稳、temporal order 把 row mention time 当作 event start time。

## 外部代码依据

- `creating001-agent-memory`：参考 clean naive RAG 的 evidence-first query 组织和 query-time context 编排；不迁移 target phrase、category、sample 规则或不 clean guardrail。
- LongMemEval 官方 `run_generation.py`：参考 turn/round 级上下文给模型直接读原始对话；`has_answer`、`answer_session_ids`、`question_type` 只作负面边界。
- LoCoMo `rag_utils.py`：参考 dialogue-level RAG prompt 要求从 conversation 精确作答；不使用 category / answer choices。
- LD-Agent：参考长期对话中 topic continuity、recency 和 persona/event 管理，但本轮不引入 summary/profile 作为事实源。
- MemoryOS：参考 short/mid/long-term 分层和 prompt 中 timestamp 检查；本轮只采用“读证据时检查时间语义”的轻量策略。
- agentmemory：参考混合搜索和 token budget 管理；本轮不改 retrieval，只新增可消融 reader discipline。

## 方法设计

在 v42 基础上新增两个 compiler 开关：

- `dialogue_inference_contract`：允许同一 session 的相邻 turns 在同一连续 exchange 中共同补全省略 slot；assistant row 只有在直接回答、确认、重复或澄清用户事件/请求时可支持答案；禁止跨 session 或无关 topic 拼凑。
- `temporal_order_contract`：对 order/comparison 问题先规范化 event/state time；`past N months/weeks`、`since N ago`、`started N ago` 表示相对 row Date 往前的起点，而不是 row Date 本身。

route override：

- `fact_lookup` / `profile_preference`：只启用 dialogue inference。
- `current_state`：启用 dialogue inference + current-state update contract。
- `temporal_lookup`：启用 dialogue inference + temporal order contract。
- `list_count`：保持 v42，不启用新 contract，避免 v59/v57 那类 list/count regression。

本轮不改 build memory、不改 retrieval、不增加 LLM call、不把 typed memory 直接放回 answer prompt、不启用 v59 source-anchor。`max_memory_records=0` 保持 v42 口径。

## Clean 检查

- 只使用 question text、question_time、retrieved raw Memory Context 和 build-time memory cache 的非泄漏结果。
- 不使用 gold answer、judge output、benchmark hidden label、sample id、row index、test feedback 或样本级规则。
- 新规则是通用对话阅读纪律，不包含具体测试实体、具体答案或具体样本。
- route 来自现有 question-derived information need，不读取 LongMemEval `question_type` 或 LoCoMo `category`。

## 成本预期

build 侧完全复用 v42 方法，正式记录中的 `avg_build_tokens` 仍按新环境 cold build 的逻辑 token 统计，cache hit 只减少本机重复调用。

query 侧只增加短 prompt rules，预期 full avg query tokens 仍接近 v42，目标 `<= 6000`，硬线 `<= 8000`。answer LLM 固定为 max input `131072`、max output `16384`。

## 实验门禁

1. 单元测试和 `json.tool` / diff check 通过。
2. 先跑 LongMemEval-S question-derived `weak_route_87` 诊断，对比 v42 same87：
   - DeepSeek judge accuracy 不低于 v42 same87。
   - 重点看 current_state、profile_preference、temporal_lookup；list_count 不能被误伤。
   - avg query tokens 目标 `<= 6000`，若略超需有明确正向收益，否则停止。
3. 若诊断通过，再考虑 LongMemEval-S full；如果弱路由负向，则删除顶层 config，仅保留诊断快照。

## 预期风险

- 新规则可能让模型把同 session 但不同 topic 的 assistant suggestion 当成用户确认，导致 over-answer。
- temporal order contract 可能改变本来正确的 approximate answer 表达。
- 对 profile/preference 的 dialogue inference 可能增加泛化回答，需要 badcase 检查确认。

## 诊断结果

run: `v60_dialogue_temporal_lme_weakroute_fb0376b`

- commit: `fb0376bbe4918d456b29756110512faf5271ff4f`
- dirty: true，仅用户修改的 `docs/architecture.md` 和 `docs/clean_protocol.md` 未提交；prediction 代码/config 已在 commit 中。
- benchmark/subset: LongMemEval-S `weak_route_87` diagnostic。
- prediction: `87/87` 输出成功。
- answer max input/output: `131072 / 16384`
- avg_build_tokens: `80991.86206896552`
- avg_query_tokens: `6202.19540229885`
- build cache hits/misses/writes: `585 / 0 / 0`
- build memory avg records: `130.98850574712642`
- answer cache hits/misses/writes: `0 / 87 / 87`
- DeepSeek judge accuracy: `58/87 = 0.6666666666666666`
- v42 same87 accuracy: `59/87 = 0.6781609195402298`
- gain/loss: `6 / 7`
- answer_changed: `29/87`
- same-answer judge disagreement: `1`

按 information_need：

- `current_state`: v42 `12/22` -> v60 `13/22`，gain/loss `2/1`
- `list_count`: v42 `15/20` -> v60 `14/20`，gain/loss `1/2`
- `profile_preference`: v42 `10/15` -> v60 `9/15`，gain/loss `0/1`
- `temporal_lookup`: v42 `22/30` -> v60 `22/30`，gain/loss `3/3`

结论：v60 未通过门禁。它保留了 current_state 的小正向，并修复了少数 temporal/count case，但引入 list/profile 回退，temporal 整体持平，同时 avg query tokens 超过 6K 软目标。因此不跑 LongMemEval-S full，不跑 LoCoMo full；顶层 config 删除，只保留诊断快照。

主要 badcase 形态：

- 正向：能回答一些相邻证据补全或当前状态更新问题，例如 recent family trip、Airbnb booking duration、writing total。
- 负向：over-answer 了 recommendation/profile 问题，错把更早状态当当前状态，count/list 把旧/近似候选重新纳入。
- 有 1 条 same-answer judge variance，不影响总体负向结论。

输出：

- prediction: `outputs/diagnostic/v60_dialogue_temporal_lme_weakroute_fb0376b/predictions.jsonl`
- trace: `outputs/diagnostic/v60_dialogue_temporal_lme_weakroute_fb0376b/traces.jsonl`
- metrics: `experiments/diagnostic/v60_dialogue_temporal_lme_weakroute_fb0376b/metrics.json`
- judge: `experiments/diagnostic/v60_dialogue_temporal_lme_weakroute_fb0376b/deepseek_judge.json`
- comparison: `experiments/diagnostic/v60_dialogue_temporal_lme_weakroute_fb0376b/judge_comparison_vs_v42_same87.json`
