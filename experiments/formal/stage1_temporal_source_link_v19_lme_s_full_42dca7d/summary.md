# stage1_temporal_source_link_v19_lme_s_full_42dca7d

## 目的

验证一个从 v18/v14 互补诊断得出的 query-side 方法：保持 v18 hybrid BM25+dense retrieval，只对通用 `temporal_lookup` route 打开 build-memory source map，希望补足 v14 在 LoCoMo temporal/source-linked organization 上的优势，同时避免恢复全量 memory guide 的噪声。

## 方法

- 代码/config commit：`42dca7d1e775b59c89293fd738d4102895ad0fab`
- prediction dirty：`false`
- 配置快照：`experiments/formal/stage1_temporal_source_link_v19_lme_s_full_42dca7d/config_snapshot.json`
- 基线：v18 hybrid BM25。
- 改动：compiler 支持按 question-derived `information_need` 覆盖 `max_memory_records` 和 structured guide memory 开关；v19 只对 `temporal_lookup` 设置 `max_memory_records=6`、`structured_guide_include_memory=true`。
- clean note：route 来自问题文本，不使用 gold、judge、benchmark question_type/category、sample id、qid、row index 或 test feedback。

## 指标

- benchmark/subset：LongMemEval-S full，500 条。
- DeepSeek judge accuracy：`357/500 = 0.714`
- invalid judge：`0`
- evidence recall：`1.000`
- avg_build_tokens：`80346.246`
- avg_query_tokens：`5203.986`
- answer max input/output：`131072 / 16384`
- activated build memory prompts：`154/500`，全部来自 `temporal_lookup`
- avg selected memory records：`1.612`，max `6`
- judge token usage：prompt `78341`，completion `36861`，total `115202`

## 对比结论

- vs v18：净 `-9`，v19-only `17`，v18-only `26`。
- vs v17：净 `-4`。
- vs v14：净 `+5`。
- vs v13：净 `0`。
- vs clean naive RAG：净 `+13`。

v19 明显低于 v18，且 query token 更高；虽然高于 v14/naive，但没有成为主线价值。结论是：即使只在 temporal route 打开 source-linked memory guide，LME 仍会被额外 memory index 噪声伤到。

## 输出路径

- predictions：`outputs/formal/stage1_temporal_source_link_v19_lme_s_full_42dca7d/predictions.jsonl`
- traces：`outputs/formal/stage1_temporal_source_link_v19_lme_s_full_42dca7d/traces.jsonl`
- metrics：`experiments/formal/stage1_temporal_source_link_v19_lme_s_full_42dca7d/metrics.json`
- judge：`experiments/formal/stage1_temporal_source_link_v19_lme_s_full_42dca7d/deepseek_judge.json`
- evidence recall：`experiments/formal/stage1_temporal_source_link_v19_lme_s_full_42dca7d/evidence_recall.json`
- manifest：`experiments/formal/stage1_temporal_source_link_v19_lme_s_full_42dca7d/manifest.json`

## 决策

不跑 LoCoMo full。原因：v19 已在 LME full 上比当前主线 v18 低 9 条，且方法增加 query token；继续跑 LoCoMo 即使可能局部提升，也不适合作为统一主线。v19 配置不长期保留在 `configs/`，实验目录保留完整 config snapshot 和诊断记录。
