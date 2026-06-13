# stage1_source_expansion_v12_locomo_nonadv_full_3235553

## Purpose

Stage-1 clean skeleton run: validate raw evidence storage, lexical retrieval, neighbor expansion, evidence compilation, answer generation, trace output, and experiment bookkeeping.

## Scope

- benchmark: locomo
- subset: non_adversarial_full
- experiment_kind: formal
- limit: None
- workers: 8
- input_path: /data/home_new/wujinqi/agent-memory/outputs/prepare_locomo_non_adversarial/prediction_input.jsonl
- config_path: /data/home_new/wujinqi/agent-memory/configs/stage1_source_expansion_v12_cached.json
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0, max_input_tokens 131072, and max_output_tokens 16384.

## Git

- inside_work_tree: True
- commit: 32355535de2170dee39eb06cf02122d41efb483e
- dirty: True
- note: None

## Metrics

- n_samples: 1540
- accuracy: None
- f1: None
- bleu: None
- avg_build_tokens: 58386.00779220779
- build_token_accounting: logical cold-build LLM tokens; cached build chunks count from stored usage, while cache hits only avoid repeated local API calls.
- avg_query_tokens: 2729.4474025974027
- avg_compiled_evidence_items: 40.0
- build_memory_enabled: True
- build_memory_model: Qwen/Qwen3-30B-A3B-Instruct-2507
- build_memory_cache_enabled: True
- build_memory_cache_path: outputs/cache/qwen3_build_memory.sqlite
- build_memory_cache_hits: 12411
- build_memory_cache_misses: 0
- build_memory_cache_writes: 0
- avg_build_memory_records: 136.65974025974026
- avg_active_build_memory_records: 125.21103896103897
- avg_memory_hits: 19.84155844155844
- avg_memory_source_hits: 22.381168831168832
- build_memory_include_superseded: False
- build_memory_include_superseded_information_needs: ['temporal_lookup', 'list_count']
- neighbor_order: hit_priority
- drop_query_stopwords: False
- lexical_enabled: False
- dense_enabled: True
- lexical_protect_top_n: 0
- dense_protect_top_n: 32
- dense_document_text_mode: external_naive
- dense_query_text_mode: external_naive
- embedding_cache_enabled: True
- embedding_cache_path: outputs/cache/qwen3_embedding.sqlite
- embedding_cache_hits: 7422
- embedding_cache_misses: 0
- embedding_cache_writes: 0
- session_bm25_enabled: False
- session_bm25_top_k: None
- session_anchor_top_k: None
- session_max_anchor_hits: None
- session_protect_turn_hits: None
- session_enabled_route_signals: None
- session_enabled_information_needs: None
- session_enabled_query_patterns: None
- session_bm25_applied_count: 0
- session_bm25_applied_rate: 0.0
- avg_embedding_tokens: 0.0
- avg_context_chars: 8583.171428571428
- compiler_prompt_mode: external_naive
- answer_mode: openai_compatible
- answer_model: Qwen/Qwen3-30B-A3B-Instruct-2507
- answer_max_input_tokens: 131072
- answer_max_output_tokens: 16384
- answer_output_format: json_answer
- answer_style: concise
- evidence_order: retrieval
- memory_order: retrieval
- memory_layout: flat
- row_text_mode: full
- max_row_text_chars: 0
- evidence_row_labels: False
- final_answer_checklist: False
- max_memory_records: 0
- route_guidance: False
- temporal_grounding: False
- temporal_hints: False
- temporal_workpad: False
- temporal_text_normalization: False
- temporal_workpad_scope: route
- temporal_workpad_max_rows: 10
- temporal_workpad_max_pairs: 12
- route_overrides: {}
- enable_broad_list_patterns: False
- enable_recommendation_profile_patterns: False
- temporal_priority_over_recent: False

## Offline Judge Results

- judge: DeepSeek `deepseek-v4-flash`, offline only after prediction.
- accuracy: 1076/1540 = 0.698701
- invalid_judgments: 0
- judge_tokens: prompt 496369, completion 156274, total 652643
- evidence_recall: 1339/1536 = 0.871745, diagnostic only.
- token_gate: avg_build_tokens 58386.008 <= 100000; avg_query_tokens 2729.447 <= 6000.
- comparison_vs_naive_external_top40: v12-only 76, naive-only 75, net +1.

By category:

- category 1: 186/282 = 0.660
- category 2: 142/321 = 0.442
- category 3: 59/96 = 0.615
- category 4: 689/841 = 0.819

结论：v12 在 LoCoMo full 上基本与 clean naive RAG 持平，没有形成有效突破。category 2 相比 naive 净亏 10 个，是当前主要负向来源；category 4 净增 7 个，说明 source expansion 对 fact-like 问题有帮助，但对时间/跨事件关系类问题还不稳定。

## Outputs

- predictions: /data/home_new/wujinqi/agent-memory/outputs/formal/stage1_source_expansion_v12_locomo_nonadv_full_3235553/predictions.jsonl
- traces: /data/home_new/wujinqi/agent-memory/outputs/formal/stage1_source_expansion_v12_locomo_nonadv_full_3235553/traces.jsonl
- metrics: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_source_expansion_v12_locomo_nonadv_full_3235553/metrics.json
- manifest: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_source_expansion_v12_locomo_nonadv_full_3235553/manifest.json
- judge: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_source_expansion_v12_locomo_nonadv_full_3235553/deepseek_judge.json
- evidence_recall: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_source_expansion_v12_locomo_nonadv_full_3235553/evidence_recall.json

## Clean Notes

- No gold/reference/target answer, judge output, benchmark label, sample id, qid, or row index is passed into the prediction pipeline.
- Build-stage typed memory is generated only from raw dialogue and visible metadata; it is recorded separately from offline labels and judge outputs.
- Raw context remains available for fallback and diagnosis; build memory records keep source back-links when produced by the current builder.
- Accuracy is intentionally not computed by the prediction runner; any gold or judge metrics must be produced offline after prediction.
