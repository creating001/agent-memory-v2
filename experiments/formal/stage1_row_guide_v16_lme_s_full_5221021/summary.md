# stage1_row_guide_v16_lme_s_full_5221021

## 目的

验证 v16 row-level evidence guide 在 LongMemEval-S full 上的效果。v16 基于 v13：保留 raw dense top-40、build-stage typed memory source expansion 和 temporal aid；只增加 retrieved raw rows 的紧凑 row overview，关闭 activated build-memory source map，并把 `max_memory_records` 设为 0。

该实验用于归因 v14/v15：v14 = row overview + memory source map，v15 = memory source map only，v16 = row overview only。

## 配置

- benchmark: LongMemEval-S
- subset: full
- n_samples: 500
- config: `/data/home_new/wujinqi/agent-memory/configs/stage1_row_guide_v16_cached.json`
- prediction workers: 8
- judge workers: 16
- answer model: Qwen/Qwen3-30B-A3B-Instruct-2507
- answer base_url: `http://127.0.0.1:8000/v1`
- answer max input/output: 131072 / 16384
- dense raw-turn retrieval: top-40, external_naive text format
- lexical retrieval: disabled
- temporal aid: enabled
- structured_guide_include_rows: true
- structured_guide_include_memory: false
- max_memory_records: 0

## Git

- commit: `52210214bc3b908b3dc765fb20c3f7a66b614a84`
- dirty at prediction: false

## Prediction Metrics

- avg_build_tokens: 80346.246
- build_token_accounting: logical cold-build LLM tokens；cache 命中也按 stored usage 计入方法成本，cache 只减少本机重复 API 调用。
- avg_query_tokens: 5029.098
- avg_compiled_evidence_items: 35.318
- avg_context_chars: 17142.120
- avg_build_memory_records: 129.662
- avg_memory_hits: 8.208
- build_memory_cache: hits 3341, misses 0, writes 0
- structured_guide_prompts: 500/500
- row_index_prompts: 500/500
- activated_build_memory_prompts: 0/500
- temporal_aid_prompts: 198/500
- avg_selected_memory_records: 0.0

## Offline Judge Results

- judge: DeepSeek `deepseek-v4-flash`, prediction 完成后离线使用。
- accuracy: 354/500 = 0.708
- invalid_judgments: 0
- judge_tokens: prompt 78231, completion 38531, total 116762
- evidence_recall: 500/500 = 1.000, diagnostic only.
- token_gate: avg_build_tokens 80346.246 <= 300000；avg_query_tokens 5029.098 <= 6000。

By question type:

- knowledge-update: 60/78 = 0.769
- multi-session: 71/133 = 0.534
- single-session-assistant: 52/56 = 0.929
- single-session-preference: 8/30 = 0.267
- single-session-user: 66/70 = 0.943
- temporal-reasoning: 97/133 = 0.729

Comparisons:

- vs v15 source-map-only: v16-only 46, v15-only 35, net +11.
- vs v14 full structured guide: v16-only 32, v14-only 30, net +2.
- vs v13 temporal aid: v16-only 29, v13-only 32, net -3.
- vs v12 source expansion: v16-only 33, v12-only 36, net -3.
- vs clean naive external top-40: v16-only 39, naive-only 29, net +10.

结论：v16 明显优于 v15，略优于 v14，但仍低于 LME 主线 v12/v13。row overview 比 typed-memory source map 更稳；但 preference 类严重退化，说明 row-level guide 不应无条件进入所有信息需求。

## Outputs

- predictions: `/data/home_new/wujinqi/agent-memory/outputs/formal/stage1_row_guide_v16_lme_s_full_5221021/predictions.jsonl`
- traces: `/data/home_new/wujinqi/agent-memory/outputs/formal/stage1_row_guide_v16_lme_s_full_5221021/traces.jsonl`
- metrics: `/data/home_new/wujinqi/agent-memory/experiments/formal/stage1_row_guide_v16_lme_s_full_5221021/metrics.json`
- judge: `/data/home_new/wujinqi/agent-memory/experiments/formal/stage1_row_guide_v16_lme_s_full_5221021/deepseek_judge.json`
- evidence_recall: `/data/home_new/wujinqi/agent-memory/experiments/formal/stage1_row_guide_v16_lme_s_full_5221021/evidence_recall.json`
- manifest: `/data/home_new/wujinqi/agent-memory/experiments/formal/stage1_row_guide_v16_lme_s_full_5221021/manifest.json`

## Clean Notes

- Prediction loader rejects gold/reference/target answers, judge outputs, benchmark labels, sample ids, qids, and row indices.
- Row guide only uses retrieved raw rows, visible timestamps/roles, question terms, and relative-time text available at prediction time.
- DeepSeek judge and evidence labels are offline-only diagnostics and must not feed prediction, retrieval, compiler, answer, verifier, or route logic.
