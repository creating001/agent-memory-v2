# stage1_structured_answer_contract_v26_locomo_nonadv_full_c21ef84

## 目的

验证 v26 structured answer contract 在 LoCoMo non-adversarial full 上的跨 benchmark 效果。v26 在 LongMemEval-S full 上相对 v18 净 +7，因此需要在 LoCoMo full 上确认是否能成为 unified best。

## 范围

- benchmark: LoCoMo
- subset: non-adversarial full
- samples: 1540
- config: `/data/home_new/wujinqi/agent-memory/configs/stage1_structured_answer_contract_v26_cached.json`
- predictions: `/data/home_new/wujinqi/agent-memory/outputs/formal/stage1_structured_answer_contract_v26_locomo_nonadv_full_c21ef84/predictions.jsonl`
- traces: `/data/home_new/wujinqi/agent-memory/outputs/formal/stage1_structured_answer_contract_v26_locomo_nonadv_full_c21ef84/traces.jsonl`

## Git

- prediction commit: `c21ef8414abb5da77972c4278c6a6edbe57aed9c`
- prediction dirty: `False`
- judge/evidence_recall: 离线诊断，不能进入 prediction pipeline。

## 指标

- DeepSeek judge accuracy: `0.7298701298701299` (`1124/1540`)
- v18 baseline accuracy: `0.737012987012987` (`1135/1540`)
- vs v18: 净 `-11`
- evidence_recall: `0.8893229166666666`
- avg_build_tokens: `58386.00779220779`
- avg_query_tokens: `3391.3974025974026`
- token gate: 通过，低于 LoCoMo 6K query / 100K build 预算
- build_cache: hits `12411`, misses `0`, writes `0`
- answer_cache: hits `11`, misses `1529`, writes `1529`
- finalizer_applied: `0/1540`

按 category：

- category 1: `177/282`，v18 为 `187/282`，净 `-10`
- category 2: `191/321`，v18 为 `190/321`，净 `+1`
- category 3: `58/96`，v18 为 `60/96`，净 `-2`
- category 4: `698/841`，v18 为 `698/841`，净 `0`

## 结论

v26 是 LME-positive，但 LoCoMo-negative，不能作为 unified best。当前统一主线仍是 v18 hybrid BM25；v26 只作为 LongMemEval-S 正向消融保留。

LoCoMo 的退化主要来自 category 1/3，category 2 只有 +1，category 4 持平。evidence recall 与 v18 基本一致，因此问题更可能在 answer-side contract 干扰，而不是 retrieval 召回。

下一步不应继续无差别扩大 structured answer contract。更合理方向是把 contract 改成更轻的 reader workpad，或只在 LME/LoCoMo 共同受益的通用信息需求上启用。

## 输出

- metrics: `/data/home_new/wujinqi/agent-memory/experiments/formal/stage1_structured_answer_contract_v26_locomo_nonadv_full_c21ef84/metrics.json`
- judge: `/data/home_new/wujinqi/agent-memory/experiments/formal/stage1_structured_answer_contract_v26_locomo_nonadv_full_c21ef84/deepseek_judge.json`
- evidence_recall: `/data/home_new/wujinqi/agent-memory/experiments/formal/stage1_structured_answer_contract_v26_locomo_nonadv_full_c21ef84/evidence_recall.json`
- manifest: `/data/home_new/wujinqi/agent-memory/experiments/formal/stage1_structured_answer_contract_v26_locomo_nonadv_full_c21ef84/manifest.json`
