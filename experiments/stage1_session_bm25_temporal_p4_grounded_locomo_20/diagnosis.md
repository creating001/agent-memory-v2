# Diagnosis for stage1_session_bm25_temporal_p4_grounded_locomo_20

## Summary

The run validates pipeline shape, clean traceability, and answerer integration under the configured experiment kind.

## Observations

- samples_processed: 20
- avg_compiled_evidence_items: 34.55
- avg_context_chars: 9405.45
- avg_query_tokens: 2877.2
- session_bm25_enabled: True
- session_bm25_top_k: 8
- session_anchor_top_k: 2
- session_enabled_route_signals: ['temporal', 'recent_or_current']
- session_bm25_applied_count: 11
- session_bm25_applied_rate: 0.55
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0.0 and max_tokens 128.

## Offline Results

- exact_match: 0.05
- token_f1: 0.26112725406688253
- bleu_unigram: 0.21380378880378878
- evidence_recall: 0.8
- baseline: stage1_session_bm25_temporal_p4_locomo_20 had token_f1 0.20788680056327116 and evidence_recall 0.8.

## Diagnosis

- Temporal grounding improved the 20-row probe substantially without changing evidence recall, indicating an answer/compiler bottleneck.
- The prompt reduces relative-time answers, but qualitative inspection still shows some date arithmetic mistakes.
- DeepSeek judge was not run because DEEPSEEK_API_KEY was missing from the shell environment.

## Next Steps

- Validate on 100 rows and consider a deterministic temporal verifier instead of relying only on prompt wording.
