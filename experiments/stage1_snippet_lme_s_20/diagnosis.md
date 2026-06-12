# Diagnosis for stage1_snippet_lme_s_20

## Summary

The run validates pipeline shape, clean traceability, and answerer integration under the configured experiment kind.

## Observations

- samples_processed: 20
- avg_compiled_evidence_items: 26.65
- avg_context_chars: 16420.95
- avg_query_tokens: 4571.4
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
- row_text_mode: query_snippet
- max_row_text_chars: 700
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0.0 and max_tokens 128.

## Next Steps

- Compare against the 100-sample LME run before considering any promotion.
- Track query tokens because row snippets can admit many more evidence rows and increase prompt overhead.
- Keep each new method behind explicit config toggles for ablation.

## Offline Result

- f1: 0.9045634920634921
- strict_baseline_f1: 0.8912301587301588
- evidence_recall: 1.0
- strict_baseline_evidence_recall: 1.0
- conclusion: positive on LME 20, but not sufficient alone.
