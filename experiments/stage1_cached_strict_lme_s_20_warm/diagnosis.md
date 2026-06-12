# Diagnosis for stage1_cached_strict_lme_s_20_warm

## Summary

The run validates pipeline shape, clean traceability, and answerer integration under the configured experiment kind.

## Observations

- samples_processed: 20
- avg_compiled_evidence_items: 14.75
- avg_context_chars: 17520.25
- avg_query_tokens: 4299.35
- session_bm25_enabled: True
- session_bm25_top_k: 8
- session_anchor_top_k: 2
- session_enabled_route_signals: ['temporal', 'recent_or_current']
- session_bm25_applied_count: 4
- session_bm25_applied_rate: 0.2
- embedding_cache_enabled: True
- embedding_cache_hits: 10155
- embedding_cache_misses: 0
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0.0 and max_tokens 128.

## Offline Results

- exact_match: 0.7
- token_f1: 0.9045634920634921
- bleu_unigram: 0.8628030303030304
- evidence_recall: 1.0

## Diagnosis

- Warm cache run confirms the SQLite embedding cache removes repeated embedding service calls for this input: avg_embedding_tokens is 0.0 with 10155 hits and no misses.
- Predictions and offline metrics match the cold cache run, so cache does not change method behavior.
- This makes expensive dense LME diagnostics more sustainable after an initial cache population pass, while preserving clean prediction inputs.

## Next Steps

- Re-run larger LME diagnostics with a warm cache and record cache phase explicitly.
- Add deterministic temporal verification next; cache only solves cost, not remaining answer errors.
