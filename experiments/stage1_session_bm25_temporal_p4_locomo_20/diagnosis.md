# Diagnosis for stage1_session_bm25_temporal_p4_locomo_20

## Summary

The run validates pipeline shape, clean traceability, and answerer integration under the configured experiment kind.

## Observations

- samples_processed: 20
- avg_compiled_evidence_items: 34.55
- avg_context_chars: 9130.45
- avg_query_tokens: 2817.25
- session_bm25_enabled: True
- session_bm25_top_k: 8
- session_anchor_top_k: 2
- session_enabled_route_signals: ['temporal', 'recent_or_current']
- session_bm25_applied_count: 11
- session_bm25_applied_rate: 0.55
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0.0 and max_tokens 128.

## Offline Results

- exact_match: 0.05
- token_f1: 0.20788680056327116
- bleu_unigram: 0.1551047774689079
- evidence_recall: 0.8
- baseline: stage1_dense_k12_concise_locomo_20 had token_f1 0.1859956416132887 and evidence_recall 0.7.

## Diagnosis

- Gating improves the 20-row probe more cleanly than ungated p4: evidence_recall rises to 0.8 while avg_query_tokens stays near baseline at 2817.25.
- The diagnostic supports using session anchors only for temporal/recent/date-like question text, not as a blanket retrieval expansion.
- DeepSeek judge was not run because DEEPSEEK_API_KEY was missing from the shell environment.

## Next Steps

- Validate the gated setting on 100 rows before considering it as a default retrieval candidate.
- Diagnose remaining evidence misses and answer errors separately; this ablation only changes retrieval ordering.
