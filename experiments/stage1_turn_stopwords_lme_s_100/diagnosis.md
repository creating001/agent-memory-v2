# Diagnosis for stage1_turn_stopwords_lme_s_100

## Summary

The run validates pipeline shape, clean traceability, and answerer integration under the configured experiment kind.

## Observations

- samples_processed: 100
- avg_compiled_evidence_items: 14.28
- avg_context_chars: 17725.63
- avg_query_tokens: 4411.25
- session_bm25_enabled: True
- session_bm25_top_k: 8
- session_anchor_top_k: 2
- session_enabled_route_signals: ['temporal', 'recent_or_current']
- session_bm25_applied_count: 36
- session_bm25_applied_rate: 0.36
- embedding_cache_enabled: True
- embedding_cache_hits: 49918
- embedding_cache_misses: 0
- evidence_order: retrieval
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0.0 and max_tokens 128.

## Next Steps

- Preserve this as an LME-positive retrieval diagnostic.
- Do not enable globally because LoCoMo 100 regresses.
- Test a clean route plus memory-shape gate if further stopword filtering is explored.

## Offline Result

- f1: 0.6534165060896154
- strict_baseline_f1: 0.6352964073078624
- evidence_recall: 1.0
- strict_baseline_evidence_recall: 0.99
- route_slice_note: list_count +0.073896 F1 and temporal_lookup +0.042300 F1, but fact_lookup -0.021490 F1 versus strict on this 100-sample slice.
- conclusion: LongMemEval-positive but not universal.
