# stage1_cached_strict_lme_s_100_warm

## Purpose

Stage-1 clean skeleton run: validate raw evidence storage, lexical retrieval, neighbor expansion, evidence compilation, answer generation, trace output, and experiment bookkeeping.

## Scope

- benchmark: longmemeval
- subset: s_cleaned
- experiment_kind: cache_diagnostic
- limit: 100
- input_path: /data/home_new/wujinqi/agent-memory/outputs/prepare_longmemeval_s_cleaned/prediction_input.jsonl
- config_path: /data/home_new/wujinqi/agent-memory/configs/stage1_vllm_dense_k12_concise_session_bm25_temporal_p4_grounded_strict_cached.json
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0.0 and max_tokens 128.

## Git

- inside_work_tree: True
- commit: a455ddab6358cd81a212aa213c8b8a462ed35ece
- dirty: True
- note: None

## Metrics

- n_samples: 100
- accuracy: None
- f1: None
- bleu: None
- avg_build_tokens: 0.0
- avg_query_tokens: 4371.14
- avg_compiled_evidence_items: 13.93
- neighbor_order: hit_priority
- drop_query_stopwords: False
- dense_enabled: True
- lexical_protect_top_n: 2
- embedding_cache_enabled: True
- embedding_cache_path: outputs/cache/qwen3_embedding.sqlite
- embedding_cache_hits: 49918
- embedding_cache_misses: 0
- embedding_cache_writes: 0
- session_bm25_enabled: True
- session_bm25_top_k: 8
- session_anchor_top_k: 2
- session_max_anchor_hits: 12
- session_protect_turn_hits: 4
- session_enabled_route_signals: ['temporal', 'recent_or_current']
- session_enabled_information_needs: None
- session_enabled_query_patterns: ['\\b20\\d{2}\\b', '\\b(?:january|february|march|april|june|july|august|september|october|november|december)\\b', '\\bmay\\s+20\\d{2}\\b']
- session_bm25_applied_count: 36
- session_bm25_applied_rate: 0.36
- avg_embedding_tokens: 0.0
- avg_context_chars: 17652.75
- answer_mode: openai_compatible
- answer_model: Qwen/Qwen3-30B-A3B-Instruct-2507
- answer_style: concise
- temporal_grounding: True
- temporal_hints: False
- enable_broad_list_patterns: False

## Outputs

- predictions: /data/home_new/wujinqi/agent-memory/outputs/stage1_cached_strict_lme_s_100_warm/predictions.jsonl
- traces: /data/home_new/wujinqi/agent-memory/outputs/stage1_cached_strict_lme_s_100_warm/traces.jsonl
- metrics: /data/home_new/wujinqi/agent-memory/experiments/stage1_cached_strict_lme_s_100_warm/metrics.json
- manifest: /data/home_new/wujinqi/agent-memory/experiments/stage1_cached_strict_lme_s_100_warm/manifest.json

## Offline Evaluation

- offline_lexical_eval: /data/home_new/wujinqi/agent-memory/experiments/stage1_cached_strict_lme_s_100_warm/offline_lexical_eval.json
- evidence_recall: /data/home_new/wujinqi/agent-memory/experiments/stage1_cached_strict_lme_s_100_warm/evidence_recall.json
- exact_match: 0.52
- token_f1: 0.6352964073078624
- bleu_unigram: 0.6107978429885426
- evidence_recall: 0.99 over 100 evidence-labeled rows
- cache_phase: warm cache validation
- cache_effect: 49918 hits, 0 misses, 0 writes, avg embedding service tokens 0.0.
- uncached_reference: stage1_session_bm25_temporal_p4_grounded_strict_lme_s_100

## Clean Notes

- No gold/reference/target answer, judge output, benchmark label, sample id, qid, or row index is passed into the prediction pipeline.
- Raw evidence remains the only factual source; compiled evidence rows keep source_id links.
- Accuracy is intentionally not computed by the prediction runner; any gold or judge metrics must be produced offline after prediction.
