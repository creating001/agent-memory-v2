# Diagnosis for stage1_compiler_overlap_locomo_20

## Summary

The run validates pipeline shape, clean traceability, and answerer integration under the configured experiment kind.

## Observations

- samples_processed: 20
- avg_compiled_evidence_items: 34.65
- avg_context_chars: 9378.0
- avg_query_tokens: 2914.1
- session_bm25_enabled: True
- session_bm25_top_k: 8
- session_anchor_top_k: 2
- session_enabled_route_signals: ['temporal', 'recent_or_current']
- session_bm25_applied_count: 11
- session_bm25_applied_rate: 0.55
- embedding_cache_enabled: True
- embedding_cache_hits: 7961
- embedding_cache_misses: 439
- evidence_order: question_overlap
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0.0 and max_tokens 128.

## Next Steps

- Treat this as a negative compiler-ordering diagnostic, not a candidate mainline result.
- Preserve retrieval/session-neighbor order in the next compiler design, and add organization through sectioning or annotations rather than global row reordering.
- Keep each new method behind explicit config toggles for ablation.

## Offline Result

- f1: 0.34033473389355745
- strict_baseline_f1: 0.40334126984126983
- evidence_recall: 0.75
- strict_baseline_evidence_recall: 0.80
- conclusion: question-overlap global row ordering harms LoCoMo 20 under the current strict candidate.
