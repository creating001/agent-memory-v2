# stage1_compiler_overlap_lme_s_20

## Purpose

Stage-1 clean skeleton run: validate raw evidence storage, lexical retrieval, neighbor expansion, evidence compilation, answer generation, trace output, and experiment bookkeeping.

## Scope

- benchmark: longmemeval
- subset: s_cleaned
- experiment_kind: focused_ablation
- limit: 20
- input_path: /data/home_new/wujinqi/agent-memory/outputs/prepare_longmemeval_s_cleaned/prediction_input.jsonl
- config_path: /data/home_new/wujinqi/agent-memory/configs/stage1_vllm_dense_k12_concise_session_bm25_temporal_p4_grounded_strict_cached_overlap.json
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0.0 and max_tokens 128.

## Git

- inside_work_tree: True
- commit: 96dd707ac2a13f41b5ca2ef0f51494bce858e6fc
- dirty: True
- note: None

## Metrics

- n_samples: 20
- accuracy: None
- f1: None
- bleu: None
- avg_build_tokens: 0.0
- avg_query_tokens: 4365.55
- avg_compiled_evidence_items: 15.5
- neighbor_order: hit_priority
- drop_query_stopwords: False
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
- avg_context_chars: 17521.4
- answer_mode: openai_compatible
- answer_model: Qwen/Qwen3-30B-A3B-Instruct-2507
- answer_style: concise
- evidence_order: question_overlap
- temporal_grounding: True
- temporal_hints: False
- enable_broad_list_patterns: False

## Outputs

- predictions: /data/home_new/wujinqi/agent-memory/outputs/stage1_compiler_overlap_lme_s_20/predictions.jsonl
- traces: /data/home_new/wujinqi/agent-memory/outputs/stage1_compiler_overlap_lme_s_20/traces.jsonl
- metrics: /data/home_new/wujinqi/agent-memory/experiments/stage1_compiler_overlap_lme_s_20/metrics.json
- manifest: /data/home_new/wujinqi/agent-memory/experiments/stage1_compiler_overlap_lme_s_20/manifest.json

## Clean Notes

- No gold/reference/target answer, judge output, benchmark label, sample id, qid, or row index is passed into the prediction pipeline.
- Raw evidence remains the only factual source; compiled evidence rows keep source_id links.
- Accuracy is intentionally not computed by the prediction runner; any gold or judge metrics must be produced offline after prediction.

## Offline Evaluation

- offline_lexical_eval: /data/home_new/wujinqi/agent-memory/experiments/stage1_compiler_overlap_lme_s_20/offline_lexical_eval.json
- evidence_recall: /data/home_new/wujinqi/agent-memory/experiments/stage1_compiler_overlap_lme_s_20/evidence_recall.json
- accuracy_exact: 0.65
- f1: 0.8312118437118438
- bleu_unigram: 0.7941666666666667
- evidence_recall: 1.0
- strict_baseline_lme_s_20_f1: 0.8912301587301588
- strict_baseline_lme_s_20_evidence_recall: 1.0

## Method Note

This ablation follows the `docs/method.md` query-time compiler direction: organize evidence using only the question, route, retrieval metadata, raw text, and timestamps. The adopted part is generic question-overlap ordering. The discarded part is making overlap the primary evidence order, because it lowered LongMemEval lexical quality even when evidence recall stayed perfect.

## Decision

Negative ablation. Keep `compiler.evidence_order=question_overlap` gated and disabled by default; the next compiler attempt should preserve retrieval order while adding evidence annotations or sections.
