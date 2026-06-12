# Diagnosis for stage1_session_bm25_temporal_p4_grounded_strict_lme_s_20

## Summary

The run validates pipeline shape, clean traceability, and answerer integration under the configured experiment kind.

## Observations

- samples_processed: 20
- avg_compiled_evidence_items: 14.75
- avg_context_chars: 17520.25
- avg_query_tokens: 4299.8
- session_bm25_enabled: True
- session_bm25_top_k: 8
- session_anchor_top_k: 2
- session_enabled_route_signals: ['temporal', 'recent_or_current']
- session_bm25_applied_count: 4
- session_bm25_applied_rate: 0.2
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0.0 and max_tokens 128.

## Offline Results

- exact_match: 0.7
- token_f1: 0.8912301587301588
- bleu_unigram: 0.854469696969697
- evidence_recall: 1.0
- baseline: stage1_concise_lme_s_20 had exact_match 0.5, token_f1 0.7513194444444445, and evidence_recall 1.0.

## Diagnosis

- The strict candidate is positive on the 20-row LME probe, but this is an expensive dense diagnostic.
- Query tokens remain within budget at avg_query_tokens 4299.8.
- Avg embedding tokens are 104198.55 per sample, so caching or a cheaper retrieval mode is required before full-scale LME runs.
- DeepSeek judge was not run because DEEPSEEK_API_KEY was missing from the shell environment.

## Next Steps

- Validate on LME 100 and then design a lower-cost/cached retrieval variant.
