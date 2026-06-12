# Diagnosis for stage1_snippet_lme_s_100

## Summary

The run validates pipeline shape, clean traceability, and answerer integration under the configured experiment kind.

## Observations

- samples_processed: 100
- avg_compiled_evidence_items: 27.69
- avg_context_chars: 17214.21
- avg_query_tokens: 4839.38
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
- row_text_mode: query_snippet
- max_row_text_chars: 700
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0.0 and max_tokens 128.

## Next Steps

- Treat query snippet mode as negative at 100-sample scale.
- If revisited, add a separate row-count cap or long-row-only gate from prediction-visible metadata.
- Keep each new method behind explicit config toggles for ablation.

## Offline Result

- f1: 0.6239503755618308
- strict_baseline_f1: 0.6352964073078624
- evidence_recall: 0.99
- strict_baseline_evidence_recall: 0.99
- avg_query_tokens: 4839.38
- strict_baseline_avg_query_tokens: 4371.14
- conclusion: snippet mode is recall-neutral but answer-negative and more expensive on LME 100.
