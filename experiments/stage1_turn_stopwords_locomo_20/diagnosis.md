# Diagnosis for stage1_turn_stopwords_locomo_20

## Summary

The run validates pipeline shape, clean traceability, and answerer integration under the configured experiment kind.

## Observations

- samples_processed: 20
- avg_compiled_evidence_items: 34.4
- avg_context_chars: 9316.75
- avg_query_tokens: 2837.3
- session_bm25_enabled: True
- session_bm25_top_k: 8
- session_anchor_top_k: 2
- session_enabled_route_signals: ['temporal', 'recent_or_current']
- session_bm25_applied_count: 11
- session_bm25_applied_rate: 0.55
- embedding_cache_enabled: True
- embedding_cache_hits: 8400
- embedding_cache_misses: 0
- evidence_order: retrieval
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0.0 and max_tokens 128.

## Next Steps

- Compare against the 100-sample LoCoMo run before promoting this config.
- If the larger run regresses, consider route- or memory-shape-aware gating rather than global turn-level stopword filtering.
- Keep each new method behind explicit config toggles for ablation.

## Offline Result

- f1: 0.41195912859070755
- strict_baseline_f1: 0.40334126984126983
- evidence_recall: 0.80
- strict_baseline_evidence_recall: 0.80
- conclusion: small positive on LoCoMo 20, not sufficient for mainline.
