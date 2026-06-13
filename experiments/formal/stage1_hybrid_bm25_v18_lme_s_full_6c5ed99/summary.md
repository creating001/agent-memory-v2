# stage1_hybrid_bm25_v18_lme_s_full_6c5ed99

## 目的

验证一个通用、clean 的 hybrid retrieval 改动：在 v17 selective row guide 的基础上加入 raw-turn BM25 lexical 检索，与 dense top-40 和 build-memory source expansion 融合；不增加 evidence slots，不引入 benchmark 标签、sample id、gold、judge 或样本级规则。

## 方法

- 配置：`configs/stage1_hybrid_bm25_v18_cached.json`
- 基线来源：v17 selective row guide。
- 改动：启用 `lexical_enabled=true`、`drop_query_stopwords=true`、`dense_protect_top_n=32`、`lexical_protect_top_n=0`。
- build 阶段：仍由 Qwen/Qwen3-30B-A3B-Instruct-2507 从 raw dialogue 构建 typed memory，cache 命中也按 cached usage 计入逻辑 cold-build token。
- query 阶段：dense raw-turn、lexical BM25、build-memory source hits 做通用融合，最终给 answer model 的事实来源仍是 raw evidence rows。

## 外部方法借鉴与取舍

- 借鉴 xMemory / SimpleMem / Graphiti 中常见的 dense + BM25 / hybrid retrieval / RRF 思路。
- 借鉴 Hindsight 的 temporal/semantic/entity 多路 memory 检索方向，但本轮只采用轻量 lexical supplement。
- 暂不引入 LLM query planner、reflection、heavy graph DB 或 benchmark-specific route；原因是 token/复杂度成本高，且当前优先验证通用检索增强是否稳定正向。

## Clean 与 Git

- prediction commit：`6c5ed99a9339cc4a7cda944b98aa20ac51dc04bb`
- prediction dirty：`false`
- offline judge/evidence 分析 dirty：`true`，原因是本实验目录在评估时尚未提交；不影响 prediction clean 性。
- clean note：prediction pipeline 不读取 gold/reference/target、judge 输出、benchmark question_type/category、sample id/qid/row index 或 test feedback。

## 指标

- benchmark/subset：LongMemEval-S full，500 条。
- DeepSeek judge accuracy：`366/500 = 0.732`
- invalid judge：`0`
- evidence recall：`1.000`
- avg_build_tokens：`80346.246`
- avg_query_tokens：`5117.622`
- answer max input/output：`131072 / 16384`
- build cache：hits `3341`，misses `0`，writes `0`
- avg build memory records：`129.662`
- avg active memory records：`116.492`
- avg compiled evidence items：`34.058`
- avg context chars：`17551.224`
- judge token usage：prompt `78333`，completion `36910`，total `115243`

## 对比结论

- vs v17：净 `+5`，v18-only `23`，v17-only `18`。
- vs v16：净 `+12`。
- vs v14：净 `+14`。
- vs v13/v12：净 `+9`。
- vs clean naive RAG：净 `+22`。

v18 是当前 LongMemEval-S full 最好结果。主要增益来自 temporal-reasoning 与 knowledge-update，同时 multi-session 与 preference 没有出现大幅崩坏；query token 增加约 `+95`/sample，仍低于 6K 预算。

## 输出路径

- predictions：`outputs/formal/stage1_hybrid_bm25_v18_lme_s_full_6c5ed99/predictions.jsonl`
- traces：`outputs/formal/stage1_hybrid_bm25_v18_lme_s_full_6c5ed99/traces.jsonl`
- metrics：`experiments/formal/stage1_hybrid_bm25_v18_lme_s_full_6c5ed99/metrics.json`
- judge：`experiments/formal/stage1_hybrid_bm25_v18_lme_s_full_6c5ed99/deepseek_judge.json`
- evidence recall：`experiments/formal/stage1_hybrid_bm25_v18_lme_s_full_6c5ed99/evidence_recall.json`
- manifest：`experiments/formal/stage1_hybrid_bm25_v18_lme_s_full_6c5ed99/manifest.json`

## 下一步

由于 v18 在 LME 全量上准确率正向、token 未超标、方法 general，下一步用同一配置跑 LoCoMo non-adversarial full。若 LoCoMo 也正向，可以把 v18 提升为统一主线；若 LoCoMo 负向，则保留为 LME 主线，并继续分析 v14 source-linked organization 与 v18 hybrid retrieval 的可组合方式。
