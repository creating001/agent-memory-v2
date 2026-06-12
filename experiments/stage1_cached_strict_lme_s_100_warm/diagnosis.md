# Diagnosis for stage1_cached_strict_lme_s_100_warm

## Summary

The run validates pipeline shape, clean traceability, and answerer integration under the configured experiment kind.

## Observations

- samples_processed: 100
- avg_compiled_evidence_items: 13.93
- avg_context_chars: 17652.75
- avg_query_tokens: 4371.14
- session_bm25_enabled: True
- session_bm25_top_k: 8
- session_anchor_top_k: 2
- session_enabled_route_signals: ['temporal', 'recent_or_current']
- session_bm25_applied_count: 36
- session_bm25_applied_rate: 0.36
- embedding_cache_enabled: True
- embedding_cache_hits: 49918
- embedding_cache_misses: 0
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0.0 and max_tokens 128.

## Offline Results

- exact_match: 0.52
- token_f1: 0.6352964073078624
- bleu_unigram: 0.6107978429885426
- evidence_recall: 0.99

## Diagnosis

- Warm cache preserves the uncached LME 100 quality exactly while reducing embedding service tokens to 0.0 for repeated diagnostics.
- This makes the dense strict candidate practical for iterative LME 100 debugging after the initial cache population pass.
- The cache remains a clean engineering layer: it keys visible text and model namespace, and it does not read gold answers, labels, sample ids, or judge outputs.

## Next Steps

- Use the cached config for larger LME diagnostics and record cache phase in every experiment.
- Continue method work on answer verification; cache only reduces service cost.
