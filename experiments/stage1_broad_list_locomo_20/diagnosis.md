# Diagnosis for stage1_broad_list_locomo_20

## Summary

The run validates pipeline shape, clean traceability, and answerer integration under the configured experiment kind.

## Observations

- samples_processed: 20
- avg_compiled_evidence_items: 34.8
- avg_context_chars: 9527.65
- avg_query_tokens: 2890.1
- session_bm25_enabled: True
- session_bm25_top_k: 8
- session_anchor_top_k: 2
- session_enabled_route_signals: ['temporal', 'recent_or_current', 'list_or_count']
- session_bm25_applied_count: 13
- session_bm25_applied_rate: 0.65
- embedding_cache_enabled: False
- embedding_cache_hits: 0
- embedding_cache_misses: 0
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0.0 and max_tokens 128.

## Offline Results

- exact_match: 0.15
- token_f1: 0.3763968253968254
- bleu_unigram: 0.3375
- evidence_recall: 0.8
- baseline: stage1_session_bm25_temporal_p4_grounded_strict_locomo_20 had token_f1 0.40334126984126983 and evidence_recall 0.8.

## Diagnosis

- Broad list routing is negative on the 20-row LoCoMo probe.
- It increases session-BM25 application from 11 to 13 rows but does not improve evidence recall and lowers answer overlap.
- The likely failure mode is context crowding from extra session anchors on broad non-temporal questions.
- The route option remains explicit behind route.enable_broad_list_patterns and is disabled by default.

## Next Steps

- Do not promote broad list routing to the main candidate.
- Prefer a more precise list compiler/verifier over broad route expansion.
