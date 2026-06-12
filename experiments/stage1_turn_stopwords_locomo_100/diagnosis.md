# Diagnosis for stage1_turn_stopwords_locomo_100

## Summary

The run validates pipeline shape, clean traceability, and answerer integration under the configured experiment kind.

## Observations

- samples_processed: 100
- avg_compiled_evidence_items: 33.56
- avg_context_chars: 9131.45
- avg_query_tokens: 2780.32
- session_bm25_enabled: True
- session_bm25_top_k: 8
- session_anchor_top_k: 2
- session_enabled_route_signals: ['temporal', 'recent_or_current']
- session_bm25_applied_count: 41
- session_bm25_applied_rate: 0.41
- embedding_cache_enabled: True
- embedding_cache_hits: 41920
- embedding_cache_misses: 80
- evidence_order: retrieval
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0.0 and max_tokens 128.

## Next Steps

- Treat global turn-level stopword filtering as negative for LoCoMo despite evidence-recall gain.
- Explore route- or memory-shape-aware gating only if it can be justified from prediction-visible signals.
- Keep each new method behind explicit config toggles for ablation.

## Offline Result

- f1: 0.375049236387644
- strict_baseline_f1: 0.3938473303083172
- evidence_recall: 0.8061224489795918
- strict_baseline_evidence_recall: 0.7857142857142857
- route_slice_note: fact_lookup -0.004662 F1, list_count -0.500000 F1, temporal_lookup -0.022584 F1 versus strict on this 100-sample slice.
- conclusion: recall-positive but answer-negative; not a global mainline setting.
