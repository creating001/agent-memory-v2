# stage1_structured_answer_contract_v26_lme_s_full_eecb206

## 目的

验证 v26：在 v25 的 structured answer contract 基础上关闭不稳定的 count finalizer，仅保留更窄的 money-sum finalizer。v26 的 prompt、build、retrieval 和 answer cache namespace 与 v25 一致，因此这个实验隔离的是 finalizer policy，而不是重新设计 retrieval。

## 范围

- benchmark: LongMemEval-S
- subset: full
- samples: 500
- config: `/data/home_new/wujinqi/agent-memory/configs/stage1_structured_answer_contract_v26_cached.json`
- predictions: `/data/home_new/wujinqi/agent-memory/outputs/formal/stage1_structured_answer_contract_v26_lme_s_full_eecb206/predictions.jsonl`
- traces: `/data/home_new/wujinqi/agent-memory/outputs/formal/stage1_structured_answer_contract_v26_lme_s_full_eecb206/traces.jsonl`

## Git

- prediction commit: `eecb206463a5216dc8c8eb2f523a48b0048f044b`
- prediction dirty: `False`
- judge/evidence_recall: 离线诊断，读取 labels/gold 后产生，不能进入 prediction pipeline。

## 指标

- DeepSeek judge accuracy: `0.746` (`373/500`)
- v18 baseline accuracy: `0.732` (`366/500`)
- v25 accuracy: `0.732` (`366/500`)
- vs v18: 净 `+7`
- vs v25: 净 `+7`
- evidence_recall: `1.0`
- avg_build_tokens: `80346.246`
- avg_query_tokens: `5355.432`
- token gate: 通过，低于 LME 6K query / 300K build 预算
- build_cache: hits `3341`, misses `0`, writes `0`
- answer_cache: hits `500`, misses `0`, writes `0`
- finalizer_applied: `0/500`

按类型：

- knowledge-update: `57/78`，比 v18 低 7
- multi-session: `87/133`，比 v18 高 13
- single-session-assistant: `52/56`，与 v18 持平
- single-session-preference: `9/30`，比 v18 低 2
- single-session-user: `63/70`，比 v18 低 3
- temporal-reasoning: `105/133`，比 v18 高 6

## 结论

v26 是当前 LongMemEval-S full 最好结果，说明 structured answer contract 的正向信号是真实的，尤其帮助 multi-session 和 temporal reasoning。v25 的负面主要来自 count finalizer，而不是结构化契约本身。

但 v26 仍低于 LME 80% baseline target，且 knowledge-update / preference / user fact 有退化。它可以作为下一阶段主线候选，但不是最终方法。

下一步：跑 LoCoMo non-adversarial full。若 LoCoMo 也正向，v26 进入当前 unified best；若 LoCoMo 负向，需要把 contract 做得更 selective 或改成不增加 answer 负担的 reader workpad。

## 输出

- metrics: `/data/home_new/wujinqi/agent-memory/experiments/formal/stage1_structured_answer_contract_v26_lme_s_full_eecb206/metrics.json`
- judge: `/data/home_new/wujinqi/agent-memory/experiments/formal/stage1_structured_answer_contract_v26_lme_s_full_eecb206/deepseek_judge.json`
- evidence_recall: `/data/home_new/wujinqi/agent-memory/experiments/formal/stage1_structured_answer_contract_v26_lme_s_full_eecb206/evidence_recall.json`
- manifest: `/data/home_new/wujinqi/agent-memory/experiments/formal/stage1_structured_answer_contract_v26_lme_s_full_eecb206/manifest.json`
