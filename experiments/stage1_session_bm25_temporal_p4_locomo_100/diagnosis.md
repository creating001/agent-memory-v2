# Diagnosis for stage1_session_bm25_temporal_p4_locomo_100

## Summary

The run validates pipeline shape, clean traceability, and answerer integration under the configured experiment kind.

## Observations

- samples_processed: 100
- avg_compiled_evidence_items: 34.13
- avg_context_chars: 8985.68
- avg_query_tokens: 2776.52
- session_bm25_enabled: True
- session_bm25_top_k: 8
- session_anchor_top_k: 2
- session_enabled_route_signals: ['temporal', 'recent_or_current']
- session_bm25_applied_count: 41
- session_bm25_applied_rate: 0.41
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0.0 and max_tokens 128.

## Offline Results

- exact_match: 0.04
- token_f1: 0.28101885421163425
- bleu_unigram: 0.2170953470950295
- evidence_recall: 0.7857142857142857
- by_type_recall: category 1 = 0.625, category 2 = 0.918918918918919, category 3 = 0.6363636363636364, category 4 = 0.8888888888888888
- baseline: stage1_dense_k12_concise_locomo_100 had token_f1 0.27571269917466834 and evidence_recall 0.7653061224489796.

## Diagnosis

- Gated session BM25 is positive on LoCoMo 100: it keeps category 1/3/4 recall at baseline and improves category 2 recall from 0.8648648648648649 to 0.918918918918919.
- Ungated p4 was negative on LoCoMo 100 because session anchors crowded out non-temporal category 1/3 evidence; the route/query gating fixes that failure mode.
- The gain is still retrieval-side and modest. Exact-match remains 0.04, so answer normalization, temporal reasoning, and source-grounded verification remain the next bottlenecks.
- Query tokens remain within budget at avg_query_tokens 2776.52; embedding tokens are unchanged and recorded separately.
- DeepSeek judge dry-run was written to /data/home_new/wujinqi/agent-memory/experiments/stage1_session_bm25_temporal_p4_locomo_100/deepseek_judge_dry_run.json; real judge was not run because DEEPSEEK_API_KEY was missing from the shell environment.

## Next Steps

- Promote gated session BM25 as the current LoCoMo retrieval candidate and avoid ungated session anchors as a default.
- Add a source-grounded verifier or evidence sufficiency pass for temporal answers before spending more query tokens.
- Add embedding/document caching before larger LoCoMo or LongMemEval runs to reduce repeated dense build cost.
