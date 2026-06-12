# stage1_compiler_overlap_locomo_20

## Purpose

Stage-1 clean skeleton run: validate raw evidence storage, lexical retrieval, neighbor expansion, evidence compilation, answer generation, trace output, and experiment bookkeeping.

## Scope

- benchmark: locomo
- subset: non_adversarial
- experiment_kind: focused_ablation
- limit: 20
- input_path: /data/home_new/wujinqi/agent-memory/outputs/prepare_locomo_non_adversarial/prediction_input.jsonl
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
- avg_query_tokens: 2914.1
- avg_compiled_evidence_items: 34.65
- neighbor_order: hit_priority
- drop_query_stopwords: False
- dense_enabled: True
- lexical_protect_top_n: 2
- embedding_cache_enabled: True
- embedding_cache_path: outputs/cache/qwen3_embedding.sqlite
- embedding_cache_hits: 7961
- embedding_cache_misses: 439
- embedding_cache_writes: 439
- session_bm25_enabled: True
- session_bm25_top_k: 8
- session_anchor_top_k: 2
- session_max_anchor_hits: 12
- session_protect_turn_hits: 4
- session_enabled_route_signals: ['temporal', 'recent_or_current']
- session_enabled_information_needs: None
- session_enabled_query_patterns: ['\\b20\\d{2}\\b', '\\b(?:january|february|march|april|june|july|august|september|october|november|december)\\b', '\\bmay\\s+20\\d{2}\\b']
- session_bm25_applied_count: 11
- session_bm25_applied_rate: 0.55
- avg_embedding_tokens: 684.5
- avg_context_chars: 9378.0
- answer_mode: openai_compatible
- answer_model: Qwen/Qwen3-30B-A3B-Instruct-2507
- answer_style: concise
- evidence_order: question_overlap
- temporal_grounding: True
- temporal_hints: False
- enable_broad_list_patterns: False

## Outputs

- predictions: /data/home_new/wujinqi/agent-memory/outputs/stage1_compiler_overlap_locomo_20/predictions.jsonl
- traces: /data/home_new/wujinqi/agent-memory/outputs/stage1_compiler_overlap_locomo_20/traces.jsonl
- metrics: /data/home_new/wujinqi/agent-memory/experiments/stage1_compiler_overlap_locomo_20/metrics.json
- manifest: /data/home_new/wujinqi/agent-memory/experiments/stage1_compiler_overlap_locomo_20/manifest.json

## Clean Notes

- No gold/reference/target answer, judge output, benchmark label, sample id, qid, or row index is passed into the prediction pipeline.
- Raw evidence remains the only factual source; compiled evidence rows keep source_id links.
- Accuracy is intentionally not computed by the prediction runner; any gold or judge metrics must be produced offline after prediction.

## Offline Evaluation

- offline_lexical_eval: /data/home_new/wujinqi/agent-memory/experiments/stage1_compiler_overlap_locomo_20/offline_lexical_eval.json
- evidence_recall: /data/home_new/wujinqi/agent-memory/experiments/stage1_compiler_overlap_locomo_20/evidence_recall.json
- accuracy_exact: 0.10
- f1: 0.34033473389355745
- bleu_unigram: 0.29509615384615384
- evidence_recall: 0.75
- strict_baseline_locomo_20_f1: 0.40334126984126983
- strict_baseline_locomo_20_evidence_recall: 0.80

## Method Note

This ablation follows the `docs/method.md` recommendation to improve query-time evidence organization without replacing raw evidence. The adopted part is a generic question-overlap ordering for compiled evidence rows. The discarded part is using it as a mainline strategy: on this sample it reduced both lexical answer quality and evidence recall, likely because raw retrieval order and session-neighbor structure carry useful context that simple token overlap disrupts.

## Decision

Negative ablation. Keep `compiler.evidence_order=question_overlap` gated and disabled by default; do not expand to full LoCoMo until a structure-preserving variant is designed.
