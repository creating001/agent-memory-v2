# stage1_source_map_guide_v15_locomo_nonadv_full_cc7f4c8

## 目的

验证 v15 compact source-map guide 在 LoCoMo non-adversarial full 上的效果。v15 删除 v14 的 row overview，只保留 activated build memory 到当前 Memory Context 的 source map，测试是否能保留 v14 的 LoCoMo 提升并降低噪声。

## 配置

- benchmark: LoCoMo
- subset: non-adversarial full
- n_samples: 1540
- config: `/data/home_new/wujinqi/agent-memory/configs/stage1_source_map_guide_v15_cached.json`
- prediction workers: 8
- judge workers: 16
- answer model: Qwen/Qwen3-30B-A3B-Instruct-2507
- answer base_url: `http://127.0.0.1:8000/v1`
- answer max input/output: 131072 / 16384
- dense raw-turn retrieval: top-40, external_naive text format
- lexical retrieval: disabled
- temporal aid: enabled
- structured_guide_include_rows: false
- structured_guide_include_memory: true
- max_memory_records: 4

## Git

- commit: `cc7f4c897eeaf426da3179cc1819202603ed8682`
- dirty at prediction: true
- dirty_status: `M docs/clean_protocol.md`; untracked LME v15 experiment directory existed during LoCoMo prediction.
- dirty_impact: docs-only diff and previous experiment artifacts；prediction code/config for v15 were committed at `cc7f4c8` before this run。

## Prediction Metrics

- avg_build_tokens: 58386.008
- build_token_accounting: logical cold-build LLM tokens；cache 命中也按 stored usage 计入方法成本，cache 只减少本机重复 API 调用。
- avg_query_tokens: 3205.268
- avg_compiled_evidence_items: 40.0
- avg_context_chars: 10201.027
- avg_build_memory_records: 136.660
- avg_active_build_memory_records: 125.211
- avg_memory_hits: 19.842
- avg_memory_source_hits: 22.381
- build_memory_cache: hits 12411, misses 0, writes 0
- embedding_cache: hits 7422, misses 0, writes 0
- structured_guide_prompts: 1540/1540
- row_index_prompts: 0/1540
- activated_build_memory_prompts: 1540/1540
- temporal_aid_prompts: 391/1540
- avg_selected_memory_records: 3.985

## Offline Judge Results

- judge: DeepSeek `deepseek-v4-flash`, prediction 完成后离线使用。
- accuracy: 1109/1540 = 0.720130
- invalid_judgments: 0
- judge_tokens: prompt 496575, completion 148952, total 645527
- retry_note: two empty-content INVALID judge responses were retried offline and replaced before final metrics; prediction artifacts were unchanged.
- evidence_recall: 1339/1536 = 0.871745, diagnostic only.
- token_gate: avg_build_tokens 58386.008 <= 100000；avg_query_tokens 3205.268 <= 6000。

By category:

- category 1: 182/282 = 0.645
- category 2: 169/321 = 0.526
- category 3: 57/96 = 0.594
- category 4: 701/841 = 0.833

Comparisons:

- vs v14 structured guide: v15-only 69, v14-only 93, net -24.
- vs v13 temporal aid: v15-only 92, v13-only 94, net -2.
- vs v12 source expansion: v15-only 119, v12-only 86, net +33.
- vs clean naive external top-40: v15-only 136, naive-only 102, net +34.

结论：v15 不如 v14，也略低于 v13；它仍明显高于 v12/naive，但这主要继承了 v13 temporal aid 和 source expansion 的收益。删掉 row overview 后 category 2 从 v14 的 195/321 降到 169/321，说明 v14 的 LoCoMo 提升依赖更宽的 evidence organization，而不是 source-map-only。

## Outputs

- predictions: `/data/home_new/wujinqi/agent-memory/outputs/formal/stage1_source_map_guide_v15_locomo_nonadv_full_cc7f4c8/predictions.jsonl`
- traces: `/data/home_new/wujinqi/agent-memory/outputs/formal/stage1_source_map_guide_v15_locomo_nonadv_full_cc7f4c8/traces.jsonl`
- metrics: `/data/home_new/wujinqi/agent-memory/experiments/formal/stage1_source_map_guide_v15_locomo_nonadv_full_cc7f4c8/metrics.json`
- judge: `/data/home_new/wujinqi/agent-memory/experiments/formal/stage1_source_map_guide_v15_locomo_nonadv_full_cc7f4c8/deepseek_judge.json`
- evidence_recall: `/data/home_new/wujinqi/agent-memory/experiments/formal/stage1_source_map_guide_v15_locomo_nonadv_full_cc7f4c8/evidence_recall.json`
- manifest: `/data/home_new/wujinqi/agent-memory/experiments/formal/stage1_source_map_guide_v15_locomo_nonadv_full_cc7f4c8/manifest.json`

## Clean Notes

- Prediction loader rejects gold/reference/target answers, judge outputs, benchmark labels, sample ids, qids, and row indices.
- Source-map guide only reorganizes retrieved raw rows and activated memory source links already available at query time.
- DeepSeek judge and evidence labels are offline-only diagnostics and must not feed prediction, retrieval, compiler, answer, verifier, or route logic.
