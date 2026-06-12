# Diagnosis for stage1_route_guidance_lme_s_100

## Summary

The run validates pipeline shape, clean traceability, and answerer integration under the configured experiment kind.

## Observations

- samples_processed: 100
- avg_compiled_evidence_items: 13.93
- avg_context_chars: 17827.56
- avg_query_tokens: 4405.71
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
- row_text_mode: full
- max_row_text_chars: 0
- route_guidance: True
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0.0 and max_tokens 128.

## Next Steps

- Run full LongMemEval-S and LoCoMo non-adversarial with DeepSeek judge accuracy.
- Do not use offline exact/F1/BLEU for method selection.
- Keep route guidance behind an explicit config toggle until full-scope judge results are available.
