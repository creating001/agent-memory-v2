# Diagnosis for stage1_compiler_overlap_lme_s_20

## Summary

The run validates pipeline shape, clean traceability, and answerer integration under the configured experiment kind.

## Observations

- samples_processed: 20
- avg_compiled_evidence_items: 15.5
- avg_context_chars: 17521.4
- avg_query_tokens: 4365.55
- session_bm25_enabled: True
- session_bm25_top_k: 8
- session_anchor_top_k: 2
- session_enabled_route_signals: ['temporal', 'recent_or_current']
- session_bm25_applied_count: 4
- session_bm25_applied_rate: 0.2
- embedding_cache_enabled: True
- embedding_cache_hits: 10155
- embedding_cache_misses: 0
- evidence_order: question_overlap
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0.0 and max_tokens 128.

## Next Steps

- Treat this as a negative compiler-ordering diagnostic, not a candidate mainline result.
- Preserve retrieval order on LongMemEval; evidence recall was already 1.0, so the failure is likely answer-stage use of reorganized context rather than retrieval miss.
- Keep each new method behind explicit config toggles for ablation.

## Offline Result

- f1: 0.8312118437118438
- strict_baseline_f1: 0.8912301587301588
- evidence_recall: 1.0
- strict_baseline_evidence_recall: 1.0
- conclusion: question-overlap global row ordering harms LongMemEval 20 under the current strict candidate.
