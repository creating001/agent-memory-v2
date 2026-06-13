# stage1_row_guide_v16_locomo_nonadv_full_5221021

## 目的

验证 v16 row-level evidence guide 在 LoCoMo non-adversarial full 上的效果，并对 v14/v15 做归因。v16 只保留 retrieved raw rows 的 row overview，关闭 activated build-memory source map。

## 配置

- benchmark: LoCoMo
- subset: non-adversarial full
- n_samples: 1540
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
- dirty at prediction: true
- dirty_status: untracked LME v16 experiment directory existed during LoCoMo prediction.
- dirty_impact: previous experiment artifacts only；prediction code/config for v16 were committed at `5221021` before this run。

## Prediction Metrics

- avg_build_tokens: 58386.008
- build_token_accounting: logical cold-build LLM tokens；cache 命中也按 stored usage 计入方法成本，cache 只减少本机重复 API 调用。
- avg_query_tokens: 3303.977
- avg_compiled_evidence_items: 40.0
- avg_context_chars: 10638.899
- avg_build_memory_records: 136.660
- avg_memory_hits: 19.842
- build_memory_cache: hits 12411, misses 0, writes 0
- structured_guide_prompts: 1540/1540
- row_index_prompts: 1540/1540
- activated_build_memory_prompts: 0/1540
- temporal_aid_prompts: 391/1540
- avg_selected_memory_records: 0.0

## Offline Judge Results

- judge: DeepSeek `deepseek-v4-flash`, prediction 完成后离线使用。
- accuracy: 1124/1540 = 0.729870
- invalid_judgments: 0
- judge_tokens: prompt 495435, completion 150565, total 646000
- evidence_recall: 1339/1536 = 0.871745, diagnostic only.
- token_gate: avg_build_tokens 58386.008 <= 100000；avg_query_tokens 3303.977 <= 6000。

By category:

- category 1: 188/282 = 0.667
- category 2: 186/321 = 0.579
- category 3: 59/96 = 0.615
- category 4: 691/841 = 0.822

Comparisons:

- vs v15 source-map-only: v16-only 113, v15-only 98, net +15.
- vs v14 full structured guide: v16-only 91, v14-only 100, net -9.
- vs v13 temporal aid: v16-only 96, v13-only 83, net +13.
- vs v12 source expansion: v16-only 132, v12-only 84, net +48.
- vs clean naive external top-40: v16-only 139, naive-only 90, net +49.

结论：v16 高于 v13/v15/v12/naive，但低于 v14。row guide 是 v14 LoCoMo 收益的主要来源之一；typed memory source map 也有额外 LoCoMo 正收益，但它会伤 LME。因此下一步应做 clean selective compiler，而不是全量开关。

## Outputs

- predictions: `/data/home_new/wujinqi/agent-memory/outputs/formal/stage1_row_guide_v16_locomo_nonadv_full_5221021/predictions.jsonl`
- traces: `/data/home_new/wujinqi/agent-memory/outputs/formal/stage1_row_guide_v16_locomo_nonadv_full_5221021/traces.jsonl`
- metrics: `/data/home_new/wujinqi/agent-memory/experiments/formal/stage1_row_guide_v16_locomo_nonadv_full_5221021/metrics.json`
- judge: `/data/home_new/wujinqi/agent-memory/experiments/formal/stage1_row_guide_v16_locomo_nonadv_full_5221021/deepseek_judge.json`
- evidence_recall: `/data/home_new/wujinqi/agent-memory/experiments/formal/stage1_row_guide_v16_locomo_nonadv_full_5221021/evidence_recall.json`
- manifest: `/data/home_new/wujinqi/agent-memory/experiments/formal/stage1_row_guide_v16_locomo_nonadv_full_5221021/manifest.json`

## Clean Notes

- Prediction loader rejects gold/reference/target answers, judge outputs, benchmark labels, sample ids, qids, and hidden row indices.
- Row guide only reorganizes retrieved raw rows already visible in Memory Context.
- DeepSeek judge and evidence labels are offline-only diagnostics and must not feed prediction, retrieval, compiler, answer, verifier, or route logic.
