# Diagnosis for stage1_turn_stopwords_lme_s_20

## Summary

The run validates pipeline shape, clean traceability, and answerer integration under the configured experiment kind.

## Observations

- samples_processed: 20
- avg_compiled_evidence_items: 14.55
- avg_context_chars: 17871.65
- avg_query_tokens: 4370.4
- session_bm25_enabled: True
- session_bm25_top_k: 8
- session_anchor_top_k: 2
- session_enabled_route_signals: ['temporal', 'recent_or_current']
- session_bm25_applied_count: 4
- session_bm25_applied_rate: 0.2
- embedding_cache_enabled: True
- embedding_cache_hits: 10155
- embedding_cache_misses: 0
- evidence_order: retrieval
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0.0 and max_tokens 128.

## Next Steps

- Compare against the 100-sample LongMemEval run before promoting this config.
- Inspect route-level deltas because stopword filtering may improve temporal/list questions while hurting simple fact lookup.
- Keep each new method behind explicit config toggles for ablation.

## Offline Result

- f1: 0.8928785103785104
- strict_baseline_f1: 0.8912301587301588
- evidence_recall: 1.0
- strict_baseline_evidence_recall: 1.0
- conclusion: small positive on LongMemEval 20, not sufficient alone for mainline.
