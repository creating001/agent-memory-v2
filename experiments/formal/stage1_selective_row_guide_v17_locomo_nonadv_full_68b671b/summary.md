# stage1_selective_row_guide_v17_locomo_nonadv_full_68b671b

## 目的

验证 v17 selective row guide 在 LoCoMo non-adversarial full 上的跨 benchmark 影响。v17 的主要改动是启用通用 personalized recommendation route 并在该信号下关闭 row guide；LoCoMo 本轮没有触发 personalized_recommendation，因此该实验主要检查 v17 是否保持 v16 row-guide-only 的 LoCoMo 表现。

该方法不使用 gold answer、judge output、benchmark category、sample id、qid、row index 或样本级规则。

## 配置

- benchmark: LoCoMo
- subset: non-adversarial full
- n_samples: 1540
- config: `/data/home_new/wujinqi/agent-memory/configs/stage1_selective_row_guide_v17_cached.json`
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
- structured_guide_disabled_signals: `personalized_recommendation`
- enable_recommendation_profile_patterns: true
- max_memory_records: 0

## Git

- commit: `68b671be00e5882b46834c87a16f2c3481702c1b`
- dirty at prediction: true
- dirty_status: untracked v17 LME experiment directory existed during LoCoMo prediction.
- dirty_impact: previous experiment artifacts only；prediction code/config for v17 were committed at `68b671b` before this run。

## Prediction Metrics

- avg_build_tokens: 58386.008
- build_token_accounting: logical cold-build LLM tokens；cache 命中也按 stored usage 计入方法成本，cache 只减少本机重复 API 调用。
- avg_query_tokens: 3303.915
- avg_compiled_evidence_items: 40.0
- avg_context_chars: 10111.044
- avg_build_memory_records: 136.660
- avg_memory_hits: 19.842
- build_memory_cache: hits 12411, misses 0, writes 0
- structured_guide_prompts: 1540/1540
- row_index_prompts: 1540/1540
- activated_build_memory_prompts: 0/1540
- temporal_aid_prompts: 391/1540
- personalized_recommendation_prompts: 0/1540
- avg_selected_memory_records: 0.0

## Offline Judge Results

- judge: DeepSeek `deepseek-v4-flash`, prediction 完成后离线使用。
- accuracy: 1110/1540 = 0.720779
- invalid_judgments: 0
- judge_tokens: prompt 495338, completion 151705, total 647043
- evidence_recall: 1339/1536 = 0.871745, diagnostic only.
- token_gate: avg_build_tokens 58386.008 <= 100000；avg_query_tokens 3303.915 <= 6000。

By category:

- category 1: 183/282 = 0.649
- category 2: 188/321 = 0.586
- category 3: 57/96 = 0.594
- category 4: 682/841 = 0.811

Comparisons:

- vs v16 row-guide-only: v17-only 25, v16-only 39, net -14.
- vs v15 source-map-only: v17-only 106, v15-only 105, net +1.
- vs v14 full structured guide: v17-only 80, v14-only 103, net -23.
- vs v13 temporal aid: v17-only 92, v13-only 93, net -1.
- vs v12 source expansion: net +34.
- vs clean naive external top-40: net +35.

结论：v17 不是 LoCoMo 最优。它保持在 v13/v15 附近，但低于 v16 和当前 LoCoMo 最好 v14。由于 LoCoMo 没有触发 personalized_recommendation，本轮更像是 row-guide-only 的复测；answer 服务在 temperature 0 下仍出现 345 条预测字符串差异，最终以本次 judge accuracy 为准。LoCoMo 下一步应从 v14 的 typed memory source map 正收益或 hybrid retrieval/source expansion 入手，而不是把 v17 作为 LoCoMo 主线。

## Outputs

- predictions: `/data/home_new/wujinqi/agent-memory/outputs/formal/stage1_selective_row_guide_v17_locomo_nonadv_full_68b671b/predictions.jsonl`
- traces: `/data/home_new/wujinqi/agent-memory/outputs/formal/stage1_selective_row_guide_v17_locomo_nonadv_full_68b671b/traces.jsonl`
- metrics: `/data/home_new/wujinqi/agent-memory/experiments/formal/stage1_selective_row_guide_v17_locomo_nonadv_full_68b671b/metrics.json`
- judge: `/data/home_new/wujinqi/agent-memory/experiments/formal/stage1_selective_row_guide_v17_locomo_nonadv_full_68b671b/deepseek_judge.json`
- evidence_recall: `/data/home_new/wujinqi/agent-memory/experiments/formal/stage1_selective_row_guide_v17_locomo_nonadv_full_68b671b/evidence_recall.json`
- manifest: `/data/home_new/wujinqi/agent-memory/experiments/formal/stage1_selective_row_guide_v17_locomo_nonadv_full_68b671b/manifest.json`

## Clean Notes

- Prediction loader rejects gold/reference/target answers, judge outputs, benchmark labels, sample ids, qids, and hidden row indices.
- Personalized recommendation signal is derived only from question text by generic route patterns；LoCoMo 本轮未触发该信号。
- Row guide only reorganizes retrieved raw rows already visible in Memory Context.
- DeepSeek judge and evidence labels are offline-only diagnostics and must not feed prediction, retrieval, compiler, answer, verifier, or route logic.
