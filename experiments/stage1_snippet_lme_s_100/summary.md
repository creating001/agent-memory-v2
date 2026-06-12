# stage1_snippet_lme_s_100

## Purpose

Stage-1 clean skeleton run: validate raw evidence storage, lexical retrieval, neighbor expansion, evidence compilation, answer generation, trace output, and experiment bookkeeping.

## Scope

- benchmark: longmemeval
- subset: s_cleaned
- experiment_kind: focused_ablation
- limit: 100
- input_path: /data/home_new/wujinqi/agent-memory/outputs/prepare_longmemeval_s_cleaned/prediction_input.jsonl
- config_path: /data/home_new/wujinqi/agent-memory/configs/stage1_vllm_dense_k12_concise_session_bm25_temporal_p4_grounded_strict_cached_snippet.json
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0.0 and max_tokens 128.

## Git

- inside_work_tree: True
- commit: 6c99677ef6ccf28dc5bf81feaad257fb6055f3c9
- dirty: True
- note: None

## Metrics

- n_samples: 100
- accuracy: None
- f1: None
- bleu: None
- avg_build_tokens: 0.0
- avg_query_tokens: 4839.38
- avg_compiled_evidence_items: 27.69
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
- avg_context_chars: 17214.21
- answer_mode: openai_compatible
- answer_model: Qwen/Qwen3-30B-A3B-Instruct-2507
- answer_style: concise
- evidence_order: retrieval
- row_text_mode: query_snippet
- max_row_text_chars: 700
- temporal_grounding: True
- temporal_hints: False
- enable_broad_list_patterns: False

## Outputs

- predictions: /data/home_new/wujinqi/agent-memory/outputs/stage1_snippet_lme_s_100/predictions.jsonl
- traces: /data/home_new/wujinqi/agent-memory/outputs/stage1_snippet_lme_s_100/traces.jsonl
- metrics: /data/home_new/wujinqi/agent-memory/experiments/stage1_snippet_lme_s_100/metrics.json
- manifest: /data/home_new/wujinqi/agent-memory/experiments/stage1_snippet_lme_s_100/manifest.json

## Clean Notes

- No gold/reference/target answer, judge output, benchmark label, sample id, qid, or row index is passed into the prediction pipeline.
- Raw evidence remains the only factual source; compiled evidence rows keep source_id links.
- Accuracy is intentionally not computed by the prediction runner; any gold or judge metrics must be produced offline after prediction.

## Offline Evaluation

- offline_lexical_eval: /data/home_new/wujinqi/agent-memory/experiments/stage1_snippet_lme_s_100/offline_lexical_eval.json
- evidence_recall: /data/home_new/wujinqi/agent-memory/experiments/stage1_snippet_lme_s_100/evidence_recall.json
- accuracy_exact: 0.50
- f1: 0.6239503755618308
- bleu_unigram: 0.5969883191790187
- evidence_recall: 0.99
- strict_baseline_lme_s_100_f1: 0.6352964073078624
- strict_baseline_lme_s_100_evidence_recall: 0.99

## Method Note

The 100-sample result reverses the positive 20-sample signal. Snippet mode lets many more rows enter the prompt, increasing query tokens and lowering LongMemEval answer quality despite unchanged evidence recall. The useful lesson is that compression must control both row length and row count, and should not replace raw retrieval order with more prompt material by default.

## Decision

Negative on LME 100. Keep `compiler.row_text_mode=query_snippet` as a diagnostic-only option disabled by default.
