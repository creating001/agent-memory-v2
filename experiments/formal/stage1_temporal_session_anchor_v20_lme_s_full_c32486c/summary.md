# stage1_temporal_session_anchor_v20_lme_s_full_c32486c

## 目的

验证一个 raw-evidence-only 的 temporal/session anchor 方法：在 v18 hybrid BM25+dense retrieval 上，只对通用 `temporal_lookup` route 启用 session-level BM25，再把少量 session 内 anchor turns 折回 raw Memory Context。目标是借鉴 HippoRAG/xMemory 的 passage/session 信号回流，不再把 build-memory 摘要放进 prompt。

## 方法

- 原始配置：`configs/stage1_temporal_session_anchor_v20_cached.json`；负向后已从主配置入口删除，当前保留本目录 `config_snapshot.json`
- prediction commit：`c32486cf82fce8f02ef73bb22b60beeb28aa5e87`
- prediction dirty：`false`
- answer max input/output：`131072 / 16384`
- session_bm25：只对 `temporal_lookup` 开启，`top_k=4`，`anchor_top_k=1`，`max_anchor_hits=4`，`protect_turn_hits=32`
- clean note：session route 来自 question text 的 information_need，不使用 gold、judge、benchmark label、sample id、qid、row index 或 test feedback。

## 指标

- benchmark/subset：LongMemEval-S full，500 条。
- DeepSeek judge accuracy：`361/500 = 0.722`
- invalid judge：`0`
- evidence recall：`1.000`
- avg_build_tokens：`80346.246`
- avg_query_tokens：`5101.412`
- session_bm25 applied：`161/500`
- avg session anchor hits：`1.288`
- avg final session anchor hits：`0.760`
- avg context chars：`17502.464`
- judge token usage：prompt `78258`，completion `39397`，total `117655`

## 对比结论

- vs v18：净 `-5`，v20-only `17`，v18-only `22`。
- vs v17：净 `0`。
- vs v14：净 `+9`。
- vs v13：净 `+4`。
- vs clean naive RAG：净 `+17`。

v20 不是 LME 新主线：总分低于 v18。但它把 temporal-reasoning 从 v18 的 `99/133` 提到 `101/133`，且 query token 略低。这说明 raw session anchors 对 temporal 有局部价值，但替换尾部 evidence 会伤 multi-session 和 single-session-user。

## 输出路径

- predictions：`outputs/formal/stage1_temporal_session_anchor_v20_lme_s_full_c32486c/predictions.jsonl`
- traces：`outputs/formal/stage1_temporal_session_anchor_v20_lme_s_full_c32486c/traces.jsonl`
- metrics：`experiments/formal/stage1_temporal_session_anchor_v20_lme_s_full_c32486c/metrics.json`
- judge：`experiments/formal/stage1_temporal_session_anchor_v20_lme_s_full_c32486c/deepseek_judge.json`
- evidence recall：`experiments/formal/stage1_temporal_session_anchor_v20_lme_s_full_c32486c/evidence_recall.json`
- manifest：`experiments/formal/stage1_temporal_session_anchor_v20_lme_s_full_c32486c/manifest.json`

## 下一步

LoCoMo non-adversarial full 已完成，结果为 `0.727273`，低于 v18 和 v14；因此 v20 不作为主线。v20 配置不长期保留在 `configs/`，两个正式实验目录保留 config snapshot 和诊断记录。
