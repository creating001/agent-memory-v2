# Diagnosis for stage1_session_bm25_locomo_20

## Summary

The run validates pipeline shape, clean traceability, and answerer integration under the configured experiment kind.

## Observations

- samples_processed: 20
- avg_compiled_evidence_items: 36.0
- avg_context_chars: 9470.65
- avg_query_tokens: 2922.75
- session_bm25_enabled: True
- session_bm25_top_k: 8
- session_anchor_top_k: 2
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0.0 and max_tokens 128.

## Offline Results

- exact_match: 0.05
- token_f1: 0.21554077784960138
- bleu_unigram: 0.15745851370851374
- evidence_recall: 0.7
- baseline: stage1_dense_k12_concise_locomo_20 had token_f1 0.1859956416132887 and evidence_recall 0.7.

## Diagnosis

- The first session-BM25 insertion improved lexical answer overlap but did not improve aggregate evidence recall on the 20-row probe.
- Per-example inspection showed gains on temporal category 2 questions and losses where early session anchors crowded out direct turn-level evidence.
- This motivated the p4 and gated temporal follow-up ablations.
- DeepSeek judge was not run because DEEPSEEK_API_KEY was missing from the shell environment.

## Next Steps

- Increase protected turn hits and test route-gated session anchors.
