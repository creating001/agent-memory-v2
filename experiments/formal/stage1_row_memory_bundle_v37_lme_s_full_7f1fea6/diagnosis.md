# Diagnosis for stage1_row_memory_bundle_v37_lme_s_full_7f1fea6

## 结论

v37 是 LongMemEval-S full 负向消融：

- DeepSeek judge accuracy: `0.744`
- correct/valid/samples: `372/500/500`
- current best v36: `0.772`, `386/500`
- delta_vs_v36: `-14` correct
- avg_build_tokens: `80346.246`
- avg_query_tokens: `5790.57`
- answer max input/output: `131072/16384`

该结果通过平均 query token 约束，但 accuracy 明显低于 v36 和 v28。v37 不能作为后续主线基础，也不应继续跑 LoCoMo full。

## 主要观察

- samples_processed: `500`
- avg_compiled_evidence_items: `32.348`
- avg_compiled_memory_records: `7.478`
- avg_context_chars: `18698.966`
- build_memory_enabled: `True`
- build_memory_model: `Qwen/Qwen3-30B-A3B-Instruct-2507`
- build_memory_cache_hits/misses/writes: `3341/0/0`
- avg_build_memory_records: `129.662`
- avg_active_build_memory_records: `116.456`
- retrieval top_k/dense_top_k/max_top_k: `40/40/40`
- dense_protect_top_n: `32`
- compiler memory_record_source: `evidence_rows`
- compiler evidence_report_contract: `True`
- structured_guide_include_memory: route-scoped enabled
- temporal_workpad: `True`
- temporal_text_normalization: `True`
- answer_output_format: `json_answer`
- answer_cache_hits/misses/writes: `20/480/480`
- answer_finalizer_applied_count: `1`
- answer_repair_enabled: `False`

## v36 对比

Offline judge comparison against `stage1_lme_token_safe_format_guard_v36_lme_s_full_4af3244`:

- both_correct: `343`
- both_wrong: `85`
- gained: `29`
- lost: `43`
- net: `-14`
- answer_changed: `170/500`
- gained_answer_changed: `29`
- lost_answer_changed: `40`
- changed-answer net: `-11`
- same-answer judge flip net: `-3`

分 question_type:

- knowledge-update: gained `2`, lost `9`
- multi-session: gained `13`, lost `14`
- single-session-assistant: gained `1`, lost `1`
- single-session-preference: gained `4`, lost `5`
- single-session-user: gained `1`, lost `2`
- temporal-reasoning: gained `8`, lost `12`

分 information_need:

- current_state: gained `0`, lost `4`
- fact_lookup: gained `13`, lost `10`
- list_count: gained `5`, lost `11`
- profile_preference: gained `1`, lost `0`
- temporal_lookup: gained `10`, lost `18`

解释：v37 有真实修复，不是全盘失效；但它修复 fact_lookup/profile 个案的收益不足以抵消 temporal/list/current_state 回退。由于 lost 中 `40/43` 是答案实际改变导致，主要问题不是 judge 抖动，而是 answer context 改变后 reader 选择了错误事实、漏算或过度拒答。

## 剩余错误

v37 wrong total: `128`。

按 question_type:

- multi-session: `48`
- temporal-reasoning: `32`
- knowledge-update: `22`
- single-session-preference: `19`
- single-session-user: `5`
- single-session-assistant: `2`

按 information_need:

- temporal_lookup: `49`
- fact_lookup: `33`
- list_count: `29`
- current_state: `11`
- profile_preference: `6`

代表性 regression:

- `0ae3182c3a2b012937a96b9d`: 游戏总时长，v36 `140 hours` 正确，v37 `125 hours`，说明 list/count 聚合漏项。
- `5aa4f411bcf1044886c38e54`: 当前鱼缸数量，v36 `3 tanks` 正确，v37 `2 tanks`，说明 current-state 聚合漏了仍在范围内的旧事实。
- `16ae1aaf11135cd4037557ed`: Jamaican dish，v36 `Grilled Snapper with Mango Salsa` 正确，v37 选择了相邻错误菜名。
- `25cafcb56c382cbde1cfcb13`: MCU/Star Wars watch duration，v36 `3.5` 正确，v37 `4 weeks`，说明 temporal calculation 受错误边界影响。

代表性 gains:

- `0bf314d56525b110034655c0`: social media follower 增长，v36 `Twitter`，v37 `TikTok` 正确。
- `e638d9fede2e6278ca0c1061`: 美国露营天数，v36 `3`，v37 `8` 正确。
- `1db38df3ec49cf8d8220ddc4`: grandma 年龄差，v36 拒答，v37 `43` 正确。
- `2152374e46762b936b18b5c5`: two weeks ago gardening activity，v36 答泛化活动，v37 `Planted 12 new tomato saplings` 正确。

## Evidence Recall

- evidence_recall: `1.0`
- n_with_evidence_labels: `500`
- by question_type: 全部 `1.0`

LME 的 evidence label 是 answer_session_ids 级别，因此 recall 只能证明目标 session 进入 context。v37 的失败更像 answer prompt 中的派生 memory 和 raw rows 互相竞争，导致模型在已有 session 里选错、漏算或过度压缩答案。

## 方法判断

v37 借鉴 SimpleMem/EverOS/xMemory/Mnemis 的 source-linked typed memory 思路，clean 边界成立，但当前落地方式把 typed memory 作为 Structured Evidence Guide 的显式 prompt 内容，造成两个问题：

- typed memory 把局部事实显著化后，reader 更倾向选择这些紧凑片段，忽略 raw rows 中的边界和反证。
- 为控制 token，v37 降低了 raw evidence char budget，可能让一些 list/count/temporal 题丢失支持行附近的上下文。

因此，后续应避免继续增加 answer prompt 里的 typed memory。更有希望的方向是把 typed memory 用于 query-time source selection、reranking、conflict-chain construction 或 candidate aggregation，然后把更少、更准的 raw evidence 交给 answer model。

## Clean 检查

- Prediction 输入未暴露 gold answer、judge、benchmark label、sample id、row index、question_type 或 category。
- v37 route/retrieval/compiler/answer 没有根据 LME label 或样本 ID 做分支。
- `memory_record_source=evidence_rows` 只依赖 raw evidence rows 与 build memory source_ids 的交集。
- Evidence recall、judge comparison 和 badcase 分组只在预测完成后离线读取 labels/judge。
- Dirty state 来自用户修改的 docs 和预测后新增实验记录，不影响 prediction code/config。

## 决策

记录 v37 为关键负向结果。顶层 `configs/` 中不长期保留 v37 config，正式复现使用本实验目录的 `config_snapshot.json`。

下一轮方法设计要求：

- 不基于 v37 full 继续堆小 prompt 或规则。
- 先结合 v36/v37 regression、外部代码和方法卡设计更 general 的 build/query memory organization。
- 优先考虑 “derived memory as retrieval/ranking/control signal, raw evidence as final prompt”。
- 任何 full run 前先做 no-label route-stratified token/trace gate。

## 输出路径

- predictions: `/data/home_new/wujinqi/agent-memory/outputs/formal/stage1_row_memory_bundle_v37_lme_s_full_7f1fea6/predictions.jsonl`
- traces: `/data/home_new/wujinqi/agent-memory/outputs/formal/stage1_row_memory_bundle_v37_lme_s_full_7f1fea6/traces.jsonl`
- judge: `/data/home_new/wujinqi/agent-memory/experiments/formal/stage1_row_memory_bundle_v37_lme_s_full_7f1fea6/deepseek_judge.json`
- evidence_recall: `/data/home_new/wujinqi/agent-memory/experiments/formal/stage1_row_memory_bundle_v37_lme_s_full_7f1fea6/evidence_recall.json`
- comparison_vs_v36: `/data/home_new/wujinqi/agent-memory/experiments/formal/stage1_row_memory_bundle_v37_lme_s_full_7f1fea6/judge_comparison_vs_v36.json`
- comparison_vs_v28: `/data/home_new/wujinqi/agent-memory/experiments/formal/stage1_row_memory_bundle_v37_lme_s_full_7f1fea6/judge_comparison_vs_v28.json`
- metrics: `/data/home_new/wujinqi/agent-memory/experiments/formal/stage1_row_memory_bundle_v37_lme_s_full_7f1fea6/metrics.json`
- manifest: `/data/home_new/wujinqi/agent-memory/experiments/formal/stage1_row_memory_bundle_v37_lme_s_full_7f1fea6/manifest.json`
