# Diagnosis for stage1_structured_answer_contract_v26_locomo_nonadv_full_c21ef84

## 摘要

v26 在 LoCoMo non-adversarial full 上为 `0.7298701298701299`，低于 v18 的 `0.737012987012987`，净 `-11`。因此 v26 不能成为 unified best。

## 与 v18 差分

- both_correct: `1082`
- both_wrong: `363`
- v18_only: `53`
- v26_only: `42`
- net: `-11`

按 category：

- category 1: `177/282`，v18 `187/282`，净 `-10`
- category 2: `191/321`，v18 `190/321`，净 `+1`
- category 3: `58/96`，v18 `60/96`，净 `-2`
- category 4: `698/841`，v18 `698/841`，净 `0`

## Evidence Recall

- overall evidence_recall: `0.8893229166666666`
- category 1: `0.8936170212765957`
- category 2: `0.8909657320872274`
- category 3: `0.6739130434782609`
- category 4: `0.9108204518430439`

v26 与 v18 的 retrieval/build 基本一致，evidence recall 没有解释最终 accuracy 下降。主要问题仍在 answer-side structured contract 对 reader 的影响。

## Token 与缓存

- avg_build_tokens: `58386.00779220779`
- avg_query_tokens: `3391.3974025974026`
- build cache hits/misses/writes: `12411/0/0`
- answer cache hits/misses/writes: `11/1529/1529`
- finalizer applied: `0`

token gate 通过，成本不是失败原因。

## 方法判断

v26 对 LoCoMo category 2 只有轻微正向，但伤 category 1/3。说明当前 answer contract 在 LME multi-session / temporal 中有帮助，但迁移到 LoCoMo 对话 QA 时会干扰更直接的 single-hop/open-domain 类回答。

这也解释了为什么不能简单把旧 creating001 的 evidence-table 思路扩大：同样是 clean 的 reader discipline，在不同 benchmark 的问题分布上可能改变答案形态，导致 judge accuracy 下降。

## Clean 检查

- prediction 输入无 gold/reference/target、judge output、benchmark 标签、sample id、qid、row index。
- LoCoMo category 只在离线 labels/judge/diagnosis 中使用，未进入 route/retrieval/compiler/answer。
- finalizer 关闭 count correction，且本次没有触发任何 finalizer。
- judge 与 evidence_recall 均为离线输出。

## 下一步

当前统一主线仍是 v18；LME 单项最好是 v26。下一轮方法不应继续加重 answer JSON contract，而应设计更轻的、可选择的 reader workpad：

- 保留 LME multi-session / temporal 正向部分。
- 避免影响 LoCoMo category 1/3 的直接回答。
- 可能把 contract 从“要求输出 evidence_items”改为“prompt 内部检查，但最终 JSON 仍只输出 answer/reasoning”。
- 或按通用 route 进一步收窄，只给明确的 aggregation/duration/order 问题启用，不给所有 temporal_lookup 启用。
