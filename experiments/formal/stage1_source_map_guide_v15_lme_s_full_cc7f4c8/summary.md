# stage1_source_map_guide_v15_lme_s_full_cc7f4c8

## 目的

验证 v15 compact source-map guide 在 LongMemEval-S full 上的效果。v15 基于 v13/v14：保留 raw dense top-40、build-stage typed memory source expansion、temporal aid；但关闭 v14 的宽泛 `row_index` overview，只保留能回链到当前 Memory Context 的 activated build memory source map，并把 `max_memory_records` 从 8 收紧到 4。

设计动机：v14 在 LoCoMo 正向但 LME 回退，怀疑 row overview 和过多 secondary memory 带来噪声。v15 只保留高置信 source map，测试是否能降低 LME 噪声。

## 配置

- benchmark: LongMemEval-S
- subset: full
- n_samples: 500
- config: `/data/home_new/wujinqi/agent-memory/configs/stage1_source_map_guide_v15_cached.json`
- prediction workers: 8
- judge workers: 16
- answer model: Qwen/Qwen3-30B-A3B-Instruct-2507
- answer base_url: `http://127.0.0.1:8000/v1`
- answer max input/output: 131072 / 16384
- dense raw-turn retrieval: top-40, external_naive text format
- lexical retrieval: disabled
- temporal aid: enabled
- structured guide: enabled
- structured_guide_include_rows: false
- structured_guide_include_memory: true
- max_memory_records: 4

## Git

- commit: `cc7f4c897eeaf426da3179cc1819202603ed8682`
- dirty at prediction: true
- dirty_status: `M docs/clean_protocol.md`
- dirty_impact: docs-only checklist deletion outside prediction/eval code and config；本次结果仍记录 dirty，不视为 clean git snapshot。

## Prediction Metrics

- avg_build_tokens: 80346.246
- build_token_accounting: logical cold-build LLM tokens；cache 命中也按 stored usage 计入方法成本，cache 只减少本机重复 API 调用。
- avg_query_tokens: 4865.988
- avg_compiled_evidence_items: 35.318
- avg_context_chars: 16750.102
- avg_build_memory_records: 129.662
- avg_active_build_memory_records: 116.492
- avg_memory_hits: 8.208
- avg_memory_source_hits: 7.894
- build_memory_cache: hits 3341, misses 0, writes 0
- embedding_cache: hits 247238, misses 0, writes 0
- structured_guide_prompts: 464/500
- row_index_prompts: 0/500
- activated_build_memory_prompts: 464/500
- temporal_aid_prompts: 198/500
- avg_selected_memory_records: 3.440

## Offline Judge Results

- judge: DeepSeek `deepseek-v4-flash`, prediction 完成后离线使用。
- accuracy: 343/500 = 0.686
- invalid_judgments: 0
- judge_tokens: prompt 78329, completion 36848, total 115177
- evidence_recall: 500/500 = 1.000, diagnostic only.
- token_gate: avg_build_tokens 80346.246 <= 300000；avg_query_tokens 4865.988 <= 6000。

By question type:

- knowledge-update: 55/78 = 0.705
- multi-session: 68/133 = 0.511
- single-session-assistant: 53/56 = 0.946
- single-session-preference: 12/30 = 0.400
- single-session-user: 64/70 = 0.914
- temporal-reasoning: 91/133 = 0.684

Comparisons:

- vs v14 structured guide: v15-only 24, v14-only 33, net -9.
- vs v13 temporal aid: v15-only 34, v13-only 48, net -14.
- vs v12 source expansion: v15-only 36, v12-only 50, net -14.
- vs clean naive external top-40: v15-only 45, naive-only 46, net -1.

结论：v15 没有解决 LME 回退，反而低于 v14/v13/v12，并略低于 clean naive。source-map-only 对 assistant 类有小幅正向，但 temporal/multi-session/knowledge-update 退化更大。该配置不进入 LME 主线。

## Outputs

- predictions: `/data/home_new/wujinqi/agent-memory/outputs/formal/stage1_source_map_guide_v15_lme_s_full_cc7f4c8/predictions.jsonl`
- traces: `/data/home_new/wujinqi/agent-memory/outputs/formal/stage1_source_map_guide_v15_lme_s_full_cc7f4c8/traces.jsonl`
- metrics: `/data/home_new/wujinqi/agent-memory/experiments/formal/stage1_source_map_guide_v15_lme_s_full_cc7f4c8/metrics.json`
- judge: `/data/home_new/wujinqi/agent-memory/experiments/formal/stage1_source_map_guide_v15_lme_s_full_cc7f4c8/deepseek_judge.json`
- evidence_recall: `/data/home_new/wujinqi/agent-memory/experiments/formal/stage1_source_map_guide_v15_lme_s_full_cc7f4c8/evidence_recall.json`
- manifest: `/data/home_new/wujinqi/agent-memory/experiments/formal/stage1_source_map_guide_v15_lme_s_full_cc7f4c8/manifest.json`

## Clean Notes

- Prediction loader rejects gold/reference/target answers, judge outputs, benchmark labels, sample ids, qids, and row indices.
- Source-map guide only uses question text, retrieved raw rows, build-stage memory records, and source_ids visible at prediction time.
- DeepSeek judge and evidence labels are offline-only diagnostics and must not feed prediction, retrieval, compiler, answer, verifier, or route logic.
