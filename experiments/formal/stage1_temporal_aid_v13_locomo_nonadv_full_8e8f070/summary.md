# stage1_temporal_aid_v13_locomo_nonadv_full_8e8f070

## Purpose

Stage-1 clean skeleton run: validate raw evidence storage, lexical retrieval, neighbor expansion, evidence compilation, answer generation, trace output, and experiment bookkeeping.

## Scope

- benchmark: locomo
- subset: non_adversarial_full
- experiment_kind: formal
- limit: None
- workers: 8
- input_path: /data/home_new/wujinqi/agent-memory/outputs/prepare_locomo_non_adversarial/prediction_input.jsonl
- config_path: /data/home_new/wujinqi/agent-memory/configs/stage1_temporal_aid_v13_cached.json
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0, max_input_tokens 131072, and max_output_tokens 16384.

## Git

- inside_work_tree: True
- commit: 8e8f0703522b73b4495e2e3ce776704db1c32a5d
- dirty: False
- note: None

## Metrics

- n_samples: 1540
- accuracy: None
- f1: None
- bleu: None
- avg_build_tokens: 58386.00779220779
- build_token_accounting: logical cold-build LLM tokens; cached build chunks count from stored usage, while cache hits only avoid repeated local API calls.
- avg_query_tokens: 2887.87987012987
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
- avg_context_chars: 8992.012987012988
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
- temporal_workpad: True
- temporal_text_normalization: True
- temporal_workpad_scope: route
- temporal_workpad_max_rows: 12
- temporal_workpad_max_pairs: 12
- route_overrides: {}
- enable_broad_list_patterns: False
- enable_recommendation_profile_patterns: False
- temporal_priority_over_recent: False

## Offline Judge Results

- judge: DeepSeek `deepseek-v4-flash`, offline only after prediction.
- accuracy: 1111/1540 = 0.721429
- invalid_judgments: 0
- judge_tokens: prompt 495789, completion 149711, total 645500
- retry_note: two empty-content INVALID judge responses were retried offline and replaced before final metrics; prediction artifacts were unchanged.
- evidence_recall: 1339/1536 = 0.871745, diagnostic only.
- token_gate: avg_build_tokens 58386.008 <= 100000; avg_query_tokens 2887.880 <= 6000.
- temporal_aid_prompts: 391/1540 = 0.254
- comparison_vs_v12: v13-only 85, v12-only 50, net +35.
- comparison_vs_naive_external_top40: v13-only 116, naive-only 80, net +36.

By category:

- category 1: 184/282 = 0.652
- category 2: 186/321 = 0.579
- category 3: 54/96 = 0.562
- category 4: 687/841 = 0.817

结论：v13 是当前 LoCoMo 最好结果，主要收益来自 category 2：相对 v12 净 +44，解决了多条把 row date 当 event date 的错误。category 1/3/4 有小幅回退，后续需要把 temporal aid 与更稳的 evidence table 结合，而不是继续增加日期规则。

## Outputs

- predictions: /data/home_new/wujinqi/agent-memory/outputs/formal/stage1_temporal_aid_v13_locomo_nonadv_full_8e8f070/predictions.jsonl
- traces: /data/home_new/wujinqi/agent-memory/outputs/formal/stage1_temporal_aid_v13_locomo_nonadv_full_8e8f070/traces.jsonl
- metrics: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_temporal_aid_v13_locomo_nonadv_full_8e8f070/metrics.json
- manifest: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_temporal_aid_v13_locomo_nonadv_full_8e8f070/manifest.json
- judge: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_temporal_aid_v13_locomo_nonadv_full_8e8f070/deepseek_judge.json
- evidence_recall: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_temporal_aid_v13_locomo_nonadv_full_8e8f070/evidence_recall.json

## Clean Notes

- No gold/reference/target answer, judge output, benchmark label, sample id, qid, or row index is passed into the prediction pipeline.
- Build-stage typed memory is generated only from raw dialogue and visible metadata; it is recorded separately from offline labels and judge outputs.
- Raw context remains available for fallback and diagnosis; build memory records keep source back-links when produced by the current builder.
- Accuracy is intentionally not computed by the prediction runner; any gold or judge metrics must be produced offline after prediction.
