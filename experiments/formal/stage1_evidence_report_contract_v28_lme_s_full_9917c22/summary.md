# stage1_evidence_report_contract_v28_lme_s_full_9917c22

## 目的

验证 v28 visible evidence report contract：在 v18 的 build-stage typed memory、dense+BM25 raw retrieval、raw source expansion、structured row guide 和 temporal aid 不变的前提下，让 answer model 在最终答案前输出一个紧凑的 `evidence_report`，显式列出 support / exclude / missing 证据，再给 `answer`。

设计参考：
- LongMemEval 官方 `con` reader：先抽取相关信息，再推理作答。
- creating001 query 结构：evidence-first extraction 对 list/count/temporal 有帮助；但不迁移其 benchmark/字符串 guardrail、target phrase、finalizer 等不够 general 的部分。
- SimpleMem / Hindsight / MemMachine：raw evidence 仍是事实源，typed/view/report 只帮助组织上下文和读证。

本次改动是 query-side compiler/reader ablation，不改 retrieval/build，不使用 gold answer、judge output、benchmark label、question_type、sample id、qid、row index 或 test feedback。

## 范围

- benchmark: LongMemEval-S
- subset: full
- samples: 500
- config: `configs/stage1_evidence_report_contract_v28_cached.json`
- prediction output: `outputs/formal/stage1_evidence_report_contract_v28_lme_s_full_9917c22/predictions.jsonl`
- traces: `outputs/formal/stage1_evidence_report_contract_v28_lme_s_full_9917c22/traces.jsonl`
- judge: `experiments/formal/stage1_evidence_report_contract_v28_lme_s_full_9917c22/deepseek_judge.json`
- diagnosis: `experiments/formal/stage1_evidence_report_contract_v28_lme_s_full_9917c22/offline_comparison.json`

## Git 与 Clean 状态

- prediction commit: `9917c229064fe7ff2e27ba07460eef549fc18352`
- prediction dirty: `false`
- judge/evidence diagnostic commit: `9917c229064fe7ff2e27ba07460eef549fc18352`
- judge/evidence diagnostic dirty: `true`，原因是预测后新增本实验目录中的 judge、diagnosis、comparison 文件。
- clean note: DeepSeek judge、labels 和 source/evidence diagnostic 只在预测完成后离线运行，不进入 retrieval、compiler、answer 或 verifier。

## 结果

- DeepSeek judge accuracy: `0.766` (`383/500`)
- LME baseline target: `>=0.800`
- 当前结论: v28 是目前 LME 最好结果，但仍未达到 baseline target。
- v18 accuracy: `0.732` (`366/500`)
- v26 accuracy: `0.746` (`373/500`)
- v27 accuracy: `0.742` (`371/500`)
- v28 vs v26: `+10/500`
- v28 vs v18: `+17/500`

## Token 成本

- avg build tokens: `80346.246`
- total build tokens: `40173123`
- avg query tokens: `5736.928`
- total query tokens: `2868464`
- LME 主线预算: avg build `<=300K`，avg query `<=6K`
- 本次满足 avg token 预算。
- query tail: `147/500` samples > 6K，`3/500` samples > 8K；主线约束按 avg 口径，但后续需要继续压长尾。
- answer max input/output: `131072/16384`
- build cache hits/misses/writes: `3341/0/0`
- answer cache hits/misses/writes: `500/0/0`；这是重跑正式记录时命中 v28 cache，logical query tokens 仍按缓存 usage 计入。

## 分类型 Accuracy

| type | v18 | v26 | v27 | v28 |
|---|---:|---:|---:|---:|
| knowledge-update | 0.821 | 0.731 | 0.808 | 0.821 |
| multi-session | 0.556 | 0.654 | 0.571 | 0.647 |
| single-session-assistant | 0.929 | 0.929 | 0.964 | 0.929 |
| single-session-preference | 0.367 | 0.300 | 0.500 | 0.433 |
| single-session-user | 0.943 | 0.900 | 0.871 | 0.929 |
| temporal-reasoning | 0.744 | 0.789 | 0.767 | 0.774 |

## 按 Information Need

| need | v28 accuracy |
|---|---:|
| current_state | 0.636 |
| fact_lookup | 0.803 |
| list_count | 0.807 |
| profile_preference | 0.600 |
| temporal_lookup | 0.727 |

## 结论

v28 证明“可见 evidence report”比私有 workpad 更有效：它保住了 v26 对 list/count 的候选收集收益，同时改善了 fact lookup、current state、preference 和部分 abstention/false-premise 错误。相对 v26，v28 的 changed-answer 净收益是 `+10`；同答案 judge 差异只有 `2` 条，不足以解释提升。

但 v28 仍低于 0.80 baseline target，主要缺口还在 temporal_lookup 和 multi-session 的复杂聚合/时间窗口题。下一步应继续改 source-aware context organization 或 build-stage typed memory 管理，而不是只堆 reader 规则。

由于 v28 是当前 LME 最好结果且仍满足 avg token 预算，下一步需要跑 LoCoMo non-adversarial full 验证泛化；如果 LoCoMo 不提升，则不能把 v28 作为统一主线。
