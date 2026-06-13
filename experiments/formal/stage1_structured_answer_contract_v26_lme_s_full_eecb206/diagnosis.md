# Diagnosis for stage1_structured_answer_contract_v26_lme_s_full_eecb206

## 摘要

v26 在 LongMemEval-S full 上达到 `0.746`，相对 v18 / v25 都净增 7 条，是当前 LME 最好结果。

关键解释：structured answer contract 帮助 answer model 在 multi-session 和 temporal 题中显式整理 evidence_items / calculation；关闭 count finalizer 后，v25 的误修正被消除。

## 与 v18 差分

- both_correct: `341`
- both_wrong: `102`
- v18_only: `25`
- v26_only: `32`
- net: `+7`

按类型：

- multi-session: `87/133`，v18 为 `74/133`，净 `+13`
- temporal-reasoning: `105/133`，v18 为 `99/133`，净 `+6`
- knowledge-update: `57/78`，v18 为 `64/78`，净 `-7`
- single-session-user: `63/70`，v18 为 `66/70`，净 `-3`
- single-session-preference: `9/30`，v18 为 `11/30`，净 `-2`
- single-session-assistant: `52/56`，v18 为 `52/56`，净 `0`

## 与 v25 差分

- v26_only: `11`
- v25_only: `4`
- net: `+7`

v25 的 count finalizer 是主要负向来源。v26 复用同一批 answer cache，finalizer applied 为 `0/500`，说明 v26 的提升来自去掉错误后处理，而不是重新生成答案。

## 方法判断

正向点：

- 对 multi-session/list/temporal 的 reader-side evidence organization 有帮助。
- 不增加 build token，不改 retrieval，不引入 benchmark label 或 sample 规则。
- query token 从 v18 的 `5117.622` 增到 `5355.432`，仍在 6K 预算内。

问题：

- KU / user fact / preference 退化明显，说明当前 contract 对“最新状态、单事实、偏好迁移”仍有干扰。
- evidence_recall 已经是 `1.0`，继续改 retrieval 不是当前 LME 主要瓶颈；下一步应更关注 answer contract 对不同信息需求的副作用。
- LME 仍未达到 80% baseline target。

## 外部方法借鉴与取舍

- 借鉴旧 `creating001/agent-memory` 的 evidence table 和 answer detail discipline，但不迁移其 benchmark 词表、样本规则、query expansion 实体表或 structured finalizer 里的宽泛规则。
- 借鉴 xMemory 的 decouple-to-aggregate，把候选证据先结构化后聚合，但不引入重型 group/component 层。
- 借鉴 SimpleMem 的 temporal normalization 和 structured memory 思路，但 raw Memory Context 仍是最终事实来源。
- 借鉴 Hindsight 的 evidence separation：模型需区分 included / excluded 证据，但 judge/gold 不参与预测。

## Clean 检查

- prediction 输入无 gold/reference/target、judge output、benchmark 标签、sample id、qid、row index。
- route 只来自 question text 和 question_time。
- structured contract 只由 `information_need` 触发，该字段由 question-derived router 生成。
- DeepSeek judge 和 evidence_recall 离线运行，不能被 prediction 模块读取。

## 下一步

跑 LoCoMo non-adversarial full。判定：

- 若 LoCoMo 相对 v18 也正向，v26 成为当前 unified best，并更新 `experiments/README.md`。
- 若 LoCoMo 负向，则 v26 只保留为 LME-positive 消融；下一步需要更 selective 的 contract，可能只用于 multi-session / temporal 的 reader workpad，并减少对 KU/current-state 的干扰。
