# stage1_row_memory_bundle_v37_lme_s_full_7f1fea6

## 目的

验证 v37 row-linked build memory bundle 是否能在 LongMemEval-S full 上提升 v36。v37 的设计初衷是让 build-stage LLM typed memory 参与 answer context，但只展示 source_id 已经出现在当前 raw evidence rows 中的 memory records，避免 summary/profile 成为独立事实源。

结论：v37 是负向消融，不作为主线方法继续推进。

## 范围

- benchmark: `longmemeval_s`
- subset: `full`
- samples: `500`
- experiment_kind: `formal`
- workers: `8`
- input_path: `/data/home_new/wujinqi/agent-memory/outputs/prepare_longmemeval_s_cleaned/prediction_input.jsonl`
- config_path: `/data/home_new/wujinqi/agent-memory/configs/stage1_row_memory_bundle_v37_cached.json`
- answer model: `Qwen/Qwen3-30B-A3B-Instruct-2507`
- answer base_url: `http://127.0.0.1:8000/v1`
- answer temperature: `0`
- answer max input/output: `131072/16384`

## Git

- prediction commit: `7f1fea62934d33252a01f0fe2000abdb483b2be8`
- dirty: `True`
- dirty_note: 预测代码和 v37 config 在 commit `7f1fea6`；dirty 主要来自用户修改的 `docs/architecture.md`、`docs/clean_protocol.md`，以及预测后新增的本实验输出记录。

## 指标

- DeepSeek judge accuracy: `0.744`
- DeepSeek judge correct/valid/samples: `372/500/500`
- DeepSeek judge invalid: `0`
- current LME best v36: `0.772`, `386/500`
- delta_vs_v36: `-14` correct
- v28: `0.766`, `383/500`
- delta_vs_v28: `-11` correct
- target_status: 距 `0.80` baseline target 还差 `28` correct
- f1/bleu/exact: 不作为方法选择依据
- avg_build_tokens: `80346.246`
- total_build_tokens: `40173123`
- build_token_accounting: logical cold-build LLM tokens；cache hit 只减少本机重复 API 调用，不把方法成本记为 0。
- avg_query_tokens: `5790.57`
- total_query_tokens: `2895285`
- DeepSeek judge total_tokens: `121391`
- avg_compiled_evidence_items: `32.348`
- avg_compiled_memory_records: `7.478`
- avg_context_chars: `18698.966`
- avg_build_memory_records: `129.662`
- avg_active_build_memory_records: `116.456`
- avg_memory_hits: `8.236`
- avg_memory_source_hits: `7.924`
- build cache hits/misses/writes: `3341/0/0`
- embedding cache hits/misses/writes: `247238/0/0`
- answer cache hits/misses/writes: `20/480/480`
- answer finalizer applied: `1`
- answer output format: `json_answer`

## 方法配置摘要

- base: v36 top40 retrieval/evidence budget + v35 answer format guard。
- build memory: enabled，本地 Qwen 从 raw dialogue 构建 typed memory。
- compiler memory_record_source: `evidence_rows`
- structured_guide_include_memory: route-scoped enabled
- max_memory_records route budget: current_state `6`, fact_lookup `6`, list_count `10`, profile_preference `6`, temporal_lookup `8`
- retrieval: lexical + dense hybrid
- retrieval top_k / dense_top_k / max_top_k: `40/40/40`
- dense protect top_n: `32`
- compiler evidence_report_contract: `True`
- temporal_workpad: `True`
- temporal_text_normalization: `True`
- answer repair/verifier: `False`

## 离线诊断

Evidence recall:

- evidence_recall: `1.0`
- n_with_evidence_labels: `500`
- by question_type: 全部 `1.0`

这里的 LME evidence label 是 `answer_session_ids` 级别，只能说明目标 session 进入了 context。v37 失败不是显著的 session recall 问题，而是 context organization / reader 使用证据的问题。

v37 vs v36 judge comparison:

- v36 correct: `386`
- v37 correct: `372`
- gained: `29`
- lost: `43`
- both_correct: `343`
- both_wrong: `85`
- answer_changed: `170`
- changed-answer net: `-11`
- same-answer judge flip net: `-3`

按 information_need 的净变化:

- fact_lookup: `+3` correct
- profile_preference: `+1` correct
- current_state: `-4` correct
- list_count: `-6` correct
- temporal_lookup: `-8` correct

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

## 决策

v37 不跑 LoCoMo full，不升级为主线。row-linked typed memory bundle 虽然通用且 clean，但直接进入 answer prompt 后让 LME reader 更容易受派生 memory 和更窄 raw evidence budget 干扰。它确实修复了一些 temporal/list/profile 个案，但整体 regressions 更多，尤其是 temporal_lookup、list_count 和 current_state。

下一步不应继续“把更多 typed memory 放进 answer prompt”。更合理的方向是让 build memory 参与 retrieval、ranking、source expansion 或冲突管理，并让最终 prompt 更少、更准地展示 raw evidence。

## 输出路径

- predictions: `/data/home_new/wujinqi/agent-memory/outputs/formal/stage1_row_memory_bundle_v37_lme_s_full_7f1fea6/predictions.jsonl`
- traces: `/data/home_new/wujinqi/agent-memory/outputs/formal/stage1_row_memory_bundle_v37_lme_s_full_7f1fea6/traces.jsonl`
- metrics: `/data/home_new/wujinqi/agent-memory/experiments/formal/stage1_row_memory_bundle_v37_lme_s_full_7f1fea6/metrics.json`
- judge: `/data/home_new/wujinqi/agent-memory/experiments/formal/stage1_row_memory_bundle_v37_lme_s_full_7f1fea6/deepseek_judge.json`
- evidence_recall: `/data/home_new/wujinqi/agent-memory/experiments/formal/stage1_row_memory_bundle_v37_lme_s_full_7f1fea6/evidence_recall.json`
- comparison_vs_v36: `/data/home_new/wujinqi/agent-memory/experiments/formal/stage1_row_memory_bundle_v37_lme_s_full_7f1fea6/judge_comparison_vs_v36.json`
- comparison_vs_v28: `/data/home_new/wujinqi/agent-memory/experiments/formal/stage1_row_memory_bundle_v37_lme_s_full_7f1fea6/judge_comparison_vs_v28.json`
- manifest: `/data/home_new/wujinqi/agent-memory/experiments/formal/stage1_row_memory_bundle_v37_lme_s_full_7f1fea6/manifest.json`
- config_snapshot: `/data/home_new/wujinqi/agent-memory/experiments/formal/stage1_row_memory_bundle_v37_lme_s_full_7f1fea6/config_snapshot.json`

## Clean Notes

- Prediction pipeline 未读取 gold/reference answer、judge output、benchmark label、sample id、qid、row index、category 或 question_type。
- Build-stage typed memory 只由 raw dialogue 和可见元数据构建。
- `memory_record_source=evidence_rows` 只使用当前样本 raw turns、build-stage typed records、retrieved raw evidence rows 和 question-text route。
- DeepSeek judge、evidence recall、question_type 分组和 v36/v28 comparison 都是 prediction 完成后的离线诊断，不能被 prediction/retrieval/compiler/answer/verifier 读取。
- v37 没有加入样本级规则，也没有加入 benchmark-specific entity 或测试答案。
