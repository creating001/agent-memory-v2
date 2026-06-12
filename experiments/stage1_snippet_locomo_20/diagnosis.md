# Diagnosis for stage1_snippet_locomo_20

## Summary

The run validates pipeline shape, clean traceability, and answerer integration under the configured experiment kind.

## Observations

- samples_processed: 20
- avg_compiled_evidence_items: 34.65
- avg_context_chars: 9482.15
- avg_query_tokens: 2876.05
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
- row_text_mode: query_snippet
- max_row_text_chars: 700
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0.0 and max_tokens 128.

## Next Steps

- Treat snippet mode as negative for compact LoCoMo-style evidence.
- Do not expand to LoCoMo 100 unless a stricter long-row-only gate is added from prediction-visible signals.
- Keep each new method behind explicit config toggles for ablation.

## Offline Result

- f1: 0.38334126984126987
- strict_baseline_f1: 0.40334126984126983
- evidence_recall: 0.80
- strict_baseline_evidence_recall: 0.80
- conclusion: prompt snippet mode disrupts answer use without recall gains on LoCoMo 20.
