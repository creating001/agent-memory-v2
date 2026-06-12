# Diagnosis for stage1_session_bm25_p4_locomo_20

## Summary

The run validates pipeline shape, clean traceability, and answerer integration under the configured experiment kind.

## Observations

- samples_processed: 20
- avg_compiled_evidence_items: 36.0
- avg_context_chars: 9473.35
- avg_query_tokens: 2921.35
- session_bm25_enabled: True
- session_bm25_top_k: 8
- session_anchor_top_k: 2
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0.0 and max_tokens 128.

## Offline Results

- exact_match: 0.05
- token_f1: 0.21710618741423696
- bleu_unigram: 0.1627922077922078
- evidence_recall: 0.75
- baseline: stage1_dense_k12_concise_locomo_20 had token_f1 0.1859956416132887 and evidence_recall 0.7.

## Diagnosis

- Protecting four turn-level hits improves the 20-row probe versus the p2 insertion setting.
- The improvement was not stable on 100 rows, where ungated anchors hurt non-temporal categories; use this result only as a small-sample stepping stone.
- DeepSeek judge was not run because DEEPSEEK_API_KEY was missing from the shell environment.

## Next Steps

- Validate p4 on a larger sample and add clean gating if category-specific crowding appears.
