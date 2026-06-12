# stage1_turn_stopwords_lme_s_20

## Purpose

Stage-1 clean skeleton run: validate raw evidence storage, lexical retrieval, neighbor expansion, evidence compilation, answer generation, trace output, and experiment bookkeeping.

## Scope

- benchmark: longmemeval
- subset: s_cleaned
- experiment_kind: focused_ablation
- limit: 20
- input_path: /data/home_new/wujinqi/agent-memory/outputs/prepare_longmemeval_s_cleaned/prediction_input.jsonl
- config_path: /data/home_new/wujinqi/agent-memory/configs/stage1_vllm_dense_k12_concise_session_bm25_temporal_p4_grounded_strict_cached_turn_stopwords.json
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0.0 and max_tokens 128.

## Git

- inside_work_tree: True
- commit: eb71e3e10c988b360da61300b450882ddb9d5082
- dirty: True
- note: None

## Metrics

- n_samples: 20
- accuracy: None
- f1: None
- bleu: None
- avg_build_tokens: 0.0
- avg_query_tokens: 4370.4
- avg_compiled_evidence_items: 14.55
- neighbor_order: hit_priority
- drop_query_stopwords: True
- dense_enabled: True
- lexical_protect_top_n: 2
- embedding_cache_enabled: True
- embedding_cache_path: outputs/cache/qwen3_embedding.sqlite
- embedding_cache_hits: 10155
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
- session_bm25_applied_count: 4
- session_bm25_applied_rate: 0.2
- avg_embedding_tokens: 0.0
- avg_context_chars: 17871.65
- answer_mode: openai_compatible
- answer_model: Qwen/Qwen3-30B-A3B-Instruct-2507
- answer_style: concise
- evidence_order: retrieval
- temporal_grounding: True
- temporal_hints: False
- enable_broad_list_patterns: False

## Outputs

- predictions: /data/home_new/wujinqi/agent-memory/outputs/stage1_turn_stopwords_lme_s_20/predictions.jsonl
- traces: /data/home_new/wujinqi/agent-memory/outputs/stage1_turn_stopwords_lme_s_20/traces.jsonl
- metrics: /data/home_new/wujinqi/agent-memory/experiments/stage1_turn_stopwords_lme_s_20/metrics.json
- manifest: /data/home_new/wujinqi/agent-memory/experiments/stage1_turn_stopwords_lme_s_20/manifest.json

## Clean Notes

- No gold/reference/target answer, judge output, benchmark label, sample id, qid, or row index is passed into the prediction pipeline.
- Raw evidence remains the only factual source; compiled evidence rows keep source_id links.
- Accuracy is intentionally not computed by the prediction runner; any gold or judge metrics must be produced offline after prediction.

## Offline Evaluation

- offline_lexical_eval: /data/home_new/wujinqi/agent-memory/experiments/stage1_turn_stopwords_lme_s_20/offline_lexical_eval.json
- evidence_recall: /data/home_new/wujinqi/agent-memory/experiments/stage1_turn_stopwords_lme_s_20/evidence_recall.json
- accuracy_exact: 0.70
- f1: 0.8928785103785104
- bleu_unigram: 0.8558333333333333
- evidence_recall: 1.0
- strict_baseline_lme_s_20_f1: 0.8912301587301588
- strict_baseline_lme_s_20_evidence_recall: 1.0

## Method Note

This ablation follows the `docs/method.md` retrieval-layer direction: keep dense retrieval, protected lexical hits, and raw evidence order, but filter generic question terms in turn-level BM25. It is clean because it only uses the question text and raw evidence text.

## Decision

Slightly positive on LongMemEval 20; expand to 100 before deciding whether it is a candidate for a larger run.
