# stage1_turn_stopwords_locomo_100

## Purpose

Stage-1 clean skeleton run: validate raw evidence storage, lexical retrieval, neighbor expansion, evidence compilation, answer generation, trace output, and experiment bookkeeping.

## Scope

- benchmark: locomo
- subset: non_adversarial
- experiment_kind: focused_ablation
- limit: 100
- input_path: /data/home_new/wujinqi/agent-memory/outputs/prepare_locomo_non_adversarial/prediction_input.jsonl
- config_path: /data/home_new/wujinqi/agent-memory/configs/stage1_vllm_dense_k12_concise_session_bm25_temporal_p4_grounded_strict_cached_turn_stopwords.json
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0.0 and max_tokens 128.

## Git

- inside_work_tree: True
- commit: eb71e3e10c988b360da61300b450882ddb9d5082
- dirty: True
- note: None

## Metrics

- n_samples: 100
- accuracy: None
- f1: None
- bleu: None
- avg_build_tokens: 0.0
- avg_query_tokens: 2780.32
- avg_compiled_evidence_items: 33.56
- neighbor_order: hit_priority
- drop_query_stopwords: True
- dense_enabled: True
- lexical_protect_top_n: 2
- embedding_cache_enabled: True
- embedding_cache_path: outputs/cache/qwen3_embedding.sqlite
- embedding_cache_hits: 41920
- embedding_cache_misses: 80
- embedding_cache_writes: 80
- session_bm25_enabled: True
- session_bm25_top_k: 8
- session_anchor_top_k: 2
- session_max_anchor_hits: 12
- session_protect_turn_hits: 4
- session_enabled_route_signals: ['temporal', 'recent_or_current']
- session_enabled_information_needs: None
- session_enabled_query_patterns: ['\\b20\\d{2}\\b', '\\b(?:january|february|march|april|june|july|august|september|october|november|december)\\b', '\\bmay\\s+20\\d{2}\\b']
- session_bm25_applied_count: 41
- session_bm25_applied_rate: 0.41
- avg_embedding_tokens: 8.36
- avg_context_chars: 9131.45
- answer_mode: openai_compatible
- answer_model: Qwen/Qwen3-30B-A3B-Instruct-2507
- answer_style: concise
- evidence_order: retrieval
- temporal_grounding: True
- temporal_hints: False
- enable_broad_list_patterns: False

## Outputs

- predictions: /data/home_new/wujinqi/agent-memory/outputs/stage1_turn_stopwords_locomo_100/predictions.jsonl
- traces: /data/home_new/wujinqi/agent-memory/outputs/stage1_turn_stopwords_locomo_100/traces.jsonl
- metrics: /data/home_new/wujinqi/agent-memory/experiments/stage1_turn_stopwords_locomo_100/metrics.json
- manifest: /data/home_new/wujinqi/agent-memory/experiments/stage1_turn_stopwords_locomo_100/manifest.json

## Clean Notes

- No gold/reference/target answer, judge output, benchmark label, sample id, qid, or row index is passed into the prediction pipeline.
- Raw evidence remains the only factual source; compiled evidence rows keep source_id links.
- Accuracy is intentionally not computed by the prediction runner; any gold or judge metrics must be produced offline after prediction.

## Offline Evaluation

- offline_lexical_eval: /data/home_new/wujinqi/agent-memory/experiments/stage1_turn_stopwords_locomo_100/offline_lexical_eval.json
- evidence_recall: /data/home_new/wujinqi/agent-memory/experiments/stage1_turn_stopwords_locomo_100/evidence_recall.json
- accuracy_exact: 0.08
- f1: 0.375049236387644
- bleu_unigram: 0.3112171251745873
- evidence_recall: 0.8061224489795918
- strict_baseline_locomo_100_f1: 0.3938473303083172
- strict_baseline_locomo_100_evidence_recall: 0.7857142857142857

## Method Note

Turn-level stopword filtering improves LoCoMo evidence recall on 100 samples but lowers lexical answer quality. This suggests the retrieved context changes in a way that includes more labeled evidence yet makes the answer model less stable. The method remains clean, but it is not a LoCoMo mainline candidate as a global setting.

## Decision

Negative for LoCoMo 100 answer quality. Keep `retrieval.drop_query_stopwords=true` gated in this config; do not enable globally.
