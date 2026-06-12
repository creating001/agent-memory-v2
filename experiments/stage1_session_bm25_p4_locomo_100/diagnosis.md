# Diagnosis for stage1_session_bm25_p4_locomo_100

## Summary

The run validates pipeline shape, clean traceability, and answerer integration under the configured experiment kind.

## Observations

- samples_processed: 100
- avg_compiled_evidence_items: 35.99
- avg_context_chars: 9465.53
- avg_query_tokens: 2924.36
- session_bm25_enabled: True
- session_bm25_top_k: 8
- session_anchor_top_k: 2
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0.0 and max_tokens 128.

## Offline Results

- exact_match: 0.03
- token_f1: 0.26673298976993887
- bleu_unigram: 0.20502075656566504
- evidence_recall: 0.7244897959183674
- by_type_recall: category 1 = 0.46875, category 2 = 0.918918918918919, category 3 = 0.5454545454545454, category 4 = 0.8888888888888888
- baseline: stage1_dense_k12_concise_locomo_100 had token_f1 0.27571269917466834 and evidence_recall 0.7653061224489796.

## Diagnosis

- Ungated p4 improves category 2 recall but hurts category 1 and category 3 enough to reduce total evidence recall and F1.
- The failure mode is context crowding: session anchors inserted after protected turn hits push out lower-ranked but relevant direct evidence on non-temporal/profile-style questions.
- This run should remain a diagnostic ablation, not a default config.
- DeepSeek judge was not run because DEEPSEEK_API_KEY was missing from the shell environment.

## Next Steps

- Gate session anchors by clean question-text/route signals before larger runs.
- Preserve this run as the negative control for session-anchor insertion strategy.
