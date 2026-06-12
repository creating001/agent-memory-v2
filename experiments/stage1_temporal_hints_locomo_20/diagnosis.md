# Diagnosis for stage1_temporal_hints_locomo_20

## Summary

The run validates pipeline shape, clean traceability, and answerer integration under the configured experiment kind.

## Observations

- samples_processed: 20
- avg_compiled_evidence_items: 34.55
- avg_context_chars: 9456.2
- avg_query_tokens: 2870.05
- session_bm25_enabled: True
- session_bm25_top_k: 8
- session_anchor_top_k: 2
- session_enabled_route_signals: ['temporal', 'recent_or_current']
- session_bm25_applied_count: 11
- session_bm25_applied_rate: 0.55
- embedding_cache_enabled: False
- embedding_cache_hits: 0
- embedding_cache_misses: 0
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0.0 and max_tokens 128.

## Offline Results

- exact_match: 0.15
- token_f1: 0.38334126984126987
- bleu_unigram: 0.3421428571428572
- evidence_recall: 0.8
- baseline: stage1_session_bm25_temporal_p4_grounded_strict_locomo_20 had exact_match 0.15, token_f1 0.40334126984126983, and evidence_recall 0.8.

## Diagnosis

- Deterministic temporal hints are negative on this 20-row LoCoMo probe.
- Evidence recall is unchanged, so the loss is answer-side: the extra hint block appears to distract or over-constrain the answer model.
- The hints remain behind compiler.temporal_hints for future controlled ablation, but must stay disabled in the current strict candidate.
- This result argues for a true post-answer verifier/normalizer rather than adding more prompt context.

## Next Steps

- Keep compiler.temporal_hints disabled by default.
- Explore deterministic post-processing/verifier only after it can prove support from evidence rows.
