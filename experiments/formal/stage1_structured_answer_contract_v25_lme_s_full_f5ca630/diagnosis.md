# Diagnosis for stage1_structured_answer_contract_v25_lme_s_full_f5ca630

## 摘要

v25 的总体 accuracy 为 `0.732`，与 v18 持平。它没有降低 evidence recall，token 也在预算内，但收益和退化明显分布不均。

核心发现：structured answer contract 本身可能帮助 multi-session / temporal 的证据组织；count finalizer 不可靠，不能继续扩展。

## 差分

相对 v18：

- both_correct: `336`
- both_wrong: `104`
- v25_only: `30`
- v18_only: `30`
- net: `0`

按类型变化：

- multi-session: `+6`
- temporal-reasoning: `+6`
- knowledge-update: `-8`
- single-session-user: `-2`
- single-session-assistant: `-1`
- single-session-preference: `-1`

这说明 structured contract 的正向集中在需要枚举、聚合、时间选择的题；但它也会让 knowledge-update/current fact 类问题更容易过度解释或选错更新状态。

## Finalizer 诊断

`answer_finalizer_applied_count=11`，全部是 `structured_evidence_count_consistency`。

结果：

- finalizer applied 后 judge correct: `2`
- finalizer applied 后 judge wrong: `9`

典型错误模式：

- 问题实际要求数量求和，例如鱼数、页数、天数、购买数量；finalizer 把 evidence_items 的条目数当最终答案。
- 重复提及或阶段性状态被当成 distinct item，导致把原本正确答案改错。
- 对“how many times”这类题，证据 item 数和事件发生次数不是同一个量。

结论：count finalizer 不满足当前主线的可靠性要求。它虽是 clean 的，因为只读 question 和模型结构化输出，但泛化性不够，会把通用 count 题误修。

## Token 与缓存

- avg_build_tokens: `80346.246`
- avg_query_tokens: `5355.432`
- build cache hits/misses/writes: `3341/0/0`
- answer cache hits/misses/writes: `0/500/500`
- avg_context_chars: `18132.274`
- answer max input/output: `131072 / 16384`

build token 仍按逻辑冷启动成本记录；cache hit 只表示本地没有重复请求。

## Clean 检查

- prediction input 不包含 gold/reference/judge/category/question_type/sample id/qid/row index。
- structured contract 只由 question-derived route (`list_count`, `temporal_lookup`) 触发。
- finalizer 只读 answer model 的 raw structured JSON，不读取 labels/gold/judge。
- DeepSeek judge 和 evidence recall 是离线输出，不能进入 prediction。

## 下一步

不跑 v25 LoCoMo full。先跑 v26 LME full：保留 structured answer contract，关闭 count finalizer，只保留 money-sum finalizer，并复用 v25 answer cache。若 v26 相对 v18 有正向或至少保留 multi/temporal 收益且减少 KU 退化，再考虑 LoCoMo full；否则需要重新设计 answer contract，让它更像 reader workpad，而不是强制结构化输出。
