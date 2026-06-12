# Diagnosis for stage1_route_guidance_locomo_100

## Summary

The run validates pipeline shape, clean traceability, and answerer integration under the configured experiment kind.

## Observations

- samples_processed: 100
- avg_compiled_evidence_items: 34.14
- avg_context_chars: 9497.6
- avg_query_tokens: 2867.35
- session_bm25_enabled: True
- session_bm25_top_k: 8
- session_anchor_top_k: 2
- session_enabled_route_signals: ['temporal', 'recent_or_current']
- session_bm25_applied_count: 41
- session_bm25_applied_rate: 0.41
- embedding_cache_enabled: True
- embedding_cache_hits: 42000
- embedding_cache_misses: 0
- evidence_order: retrieval
- row_text_mode: full
- max_row_text_chars: 0
- route_guidance: True
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0.0 and max_tokens 128.

## Next Steps

- Run full LoCoMo non-adversarial and LongMemEval-S with DeepSeek judge accuracy.
- Do not use this first-100 diagnostic as a formal result.
- Keep route guidance behind an explicit config toggle until full-scope results are available.

## Judge Result

- judge_accuracy: 0.51
- n_judgments: 100
- conclusion: positive diagnostic only; requires full benchmark confirmation.
