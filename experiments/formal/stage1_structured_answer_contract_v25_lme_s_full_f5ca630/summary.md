# stage1_structured_answer_contract_v25_lme_s_full_f5ca630

## 目的

验证 v25 query-side answer/compiler 消融：在 v18 的 build-stage typed memory source expansion、raw-turn dense+BM25 hybrid retrieval、selective row guide 不变的前提下，只增加 `list_count` / `temporal_lookup` 的 structured answer contract，并启用机械 finalizer。

设计参考：

- 旧 `creating001/agent-memory` 的 evidence table / structured evidence finalizer。
- xMemory 的 decouple-to-aggregate。
- SimpleMem 的 temporal normalization / structured memory。
- Hindsight 的 evidence separation。

取舍：不迁移旧项目的 benchmark 词表、样本规则、query expansion 实体表或 judge/test feedback；不增加第二次 answer LLM 调用。

## 范围

- benchmark: LongMemEval-S
- subset: full
- samples: 500
- config: `/data/home_new/wujinqi/agent-memory/configs/stage1_structured_answer_contract_v25_cached.json`
- predictions: `/data/home_new/wujinqi/agent-memory/outputs/formal/stage1_structured_answer_contract_v25_lme_s_full_f5ca630/predictions.jsonl`
- traces: `/data/home_new/wujinqi/agent-memory/outputs/formal/stage1_structured_answer_contract_v25_lme_s_full_f5ca630/traces.jsonl`

## Git

- prediction commit: `f5ca630f097feaeeeaef49a1dd9c218ef04644c6`
- prediction dirty: `False`
- note: 后续 judge / evidence_recall 属于离线诊断，会读取 labels/gold；这些输出不能进入 prediction pipeline。

## 指标

- DeepSeek judge accuracy: `0.732` (`366/500`)
- v18 baseline accuracy: `0.732`
- vs v18: 净 `0`
- evidence_recall: `1.0`
- avg_build_tokens: `80346.246`
- avg_query_tokens: `5355.432`
- token gate: 通过，低于 LME 6K query / 300K build 预算
- build_cache: hits `3341`, misses `0`, writes `0`
- answer_cache: hits `0`, misses `500`, writes `500`
- finalizer_applied: `11/500`

按类型：

- knowledge-update: `56/78`，比 v18 `64/78` 低 8
- multi-session: `80/133`，比 v18 `74/133` 高 6
- single-session-assistant: `51/56`，比 v18 `52/56` 低 1
- single-session-preference: `10/30`，比 v18 `11/30` 低 1
- single-session-user: `64/70`，比 v18 `66/70` 低 2
- temporal-reasoning: `105/133`，比 v18 `99/133` 高 6

## 结论

v25 与 v18 总分打平，但不是可直接升级的主线。structured answer contract 对 multi-session 和 temporal 有明显正向信号，但 knowledge-update / user / preference 退化抵消了收益。

更关键的是，count finalizer 明显不稳：11 次触发里只有 2 条最终 judge correct，9 条 wrong。错误模式是把“需要求和的数量、页数、天数、鱼数、购买件数”误当成“证据项个数”，这不是可靠通用机制。

因此 v25 不跑 LoCoMo full，不作为主线。下一步做 v26：保留 structured answer contract，关闭 count finalizer，只保留更窄的 money-sum finalizer，并复用 v25 answer cache 做 full LME 消融。

## 输出

- metrics: `/data/home_new/wujinqi/agent-memory/experiments/formal/stage1_structured_answer_contract_v25_lme_s_full_f5ca630/metrics.json`
- judge: `/data/home_new/wujinqi/agent-memory/experiments/formal/stage1_structured_answer_contract_v25_lme_s_full_f5ca630/deepseek_judge.json`
- evidence_recall: `/data/home_new/wujinqi/agent-memory/experiments/formal/stage1_structured_answer_contract_v25_lme_s_full_f5ca630/evidence_recall.json`
- manifest: `/data/home_new/wujinqi/agent-memory/experiments/formal/stage1_structured_answer_contract_v25_lme_s_full_f5ca630/manifest.json`
