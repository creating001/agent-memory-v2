# stage1_temporal_aid_v13_lme_s_full_8e8f070

## Purpose

Stage-1 clean skeleton run: validate raw evidence storage, lexical retrieval, neighbor expansion, evidence compilation, answer generation, trace output, and experiment bookkeeping.

## Scope

- benchmark: longmemeval
- subset: s_full
- experiment_kind: formal
- limit: None
- workers: 8
- input_path: /data/home_new/wujinqi/agent-memory/outputs/prepare_longmemeval_s_cleaned/prediction_input.jsonl
- config_path: /data/home_new/wujinqi/agent-memory/configs/stage1_temporal_aid_v13_cached.json
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0, max_input_tokens 131072, and max_output_tokens 16384.

## Git

- inside_work_tree: True
- commit: 8e8f0703522b73b4495e2e3ce776704db1c32a5d
- dirty: True
- note: None

## Metrics

- n_samples: 500
- accuracy: None
- f1: None
- bleu: None
- avg_build_tokens: 80346.246
- build_token_accounting: logical cold-build LLM tokens; cached build chunks count from stored usage, while cache hits only avoid repeated local API calls.
- avg_query_tokens: 4614.806
- avg_compiled_evidence_items: 35.318
- build_memory_enabled: True
- build_memory_model: Qwen/Qwen3-30B-A3B-Instruct-2507
- build_memory_cache_enabled: True
- build_memory_cache_path: outputs/cache/qwen3_build_memory.sqlite
- build_memory_cache_hits: 3341
- build_memory_cache_misses: 0
- build_memory_cache_writes: 0
- avg_build_memory_records: 129.662
- avg_active_build_memory_records: 116.492
- avg_memory_hits: 8.208
- avg_memory_source_hits: 7.894
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
- embedding_cache_hits: 247238
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
- avg_context_chars: 15788.524
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
- accuracy: 357/500 = 0.714
- invalid_judgments: 0
- judge_tokens: prompt 78830, completion 40604, total 119434
- evidence_recall: 500/500 = 1.0, diagnostic only.
- token_gate: avg_build_tokens 80346.246 <= 300000; avg_query_tokens 4614.806 <= 6000.
- temporal_aid_prompts: 198/500 = 0.396
- comparison_vs_v12: v13-only 27, v12-only 27, net 0.
- comparison_vs_naive_external_top40: v13-only 31, naive-only 18, net +13.

By question type:

- knowledge-update: 60/78 = 0.769
- multi-session: 74/133 = 0.556
- single-session-assistant: 53/56 = 0.946
- single-session-preference: 10/30 = 0.333
- single-session-user: 65/70 = 0.929
- temporal-reasoning: 95/133 = 0.714

结论：v13 在 LME full 上与 v12 总分持平，仍明显高于 clean naive RAG。temporal aid 对 temporal-reasoning 净 +1、preference 净 +1，但 multi-session 和 single-session-user 有小回退；因此 v13 可作为 LoCoMo 主线，但 LME 需要继续做更稳的 evidence compiler，而不是单独依赖时间辅助。

## Outputs

- predictions: /data/home_new/wujinqi/agent-memory/outputs/formal/stage1_temporal_aid_v13_lme_s_full_8e8f070/predictions.jsonl
- traces: /data/home_new/wujinqi/agent-memory/outputs/formal/stage1_temporal_aid_v13_lme_s_full_8e8f070/traces.jsonl
- metrics: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_temporal_aid_v13_lme_s_full_8e8f070/metrics.json
- manifest: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_temporal_aid_v13_lme_s_full_8e8f070/manifest.json
- judge: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_temporal_aid_v13_lme_s_full_8e8f070/deepseek_judge.json
- evidence_recall: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_temporal_aid_v13_lme_s_full_8e8f070/evidence_recall.json

## Clean Notes

- No gold/reference/target answer, judge output, benchmark label, sample id, qid, or row index is passed into the prediction pipeline.
- Build-stage typed memory is generated only from raw dialogue and visible metadata; it is recorded separately from offline labels and judge outputs.
- Raw context remains available for fallback and diagnosis; build memory records keep source back-links when produced by the current builder.
- Accuracy is intentionally not computed by the prediction runner; any gold or judge metrics must be produced offline after prediction.
