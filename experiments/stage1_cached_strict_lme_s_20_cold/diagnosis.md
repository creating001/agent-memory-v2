# Diagnosis for stage1_cached_strict_lme_s_20_cold

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
- embedding_cache_hits: 192
- embedding_cache_misses: 9963
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0.0 and max_tokens 128.

## Offline Results

- exact_match: 0.7
- token_f1: 0.9045634920634921
- bleu_unigram: 0.8628030303030304
- evidence_recall: 1.0

## Diagnosis

- Cold cache run populated outputs/cache/qwen3_embedding.sqlite with 9945 unique embedding vectors.
- It still paid most embedding service cost, as expected for first use: avg_embedding_tokens 102223.6.
- Quality matches the warm cache run, so cache storage does not change retrieval or answer behavior.
- This is a clean engineering optimization because keys are derived from model namespace, input_type, and raw visible text only.

## Next Steps

- Use the warm cache run to confirm service-token reduction.
- For formal cached runs, record whether the cache is cold, warm, or partially warm.
