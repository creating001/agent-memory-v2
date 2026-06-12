# Diagnosis for stage1_session_bm25_temporal_p4_grounded_locomo_100

## Summary

The run validates pipeline shape, clean traceability, and answerer integration under the configured experiment kind.

## Observations

- samples_processed: 100
- avg_compiled_evidence_items: 34.13
- avg_context_chars: 9260.68
- avg_query_tokens: 2830.58
- session_bm25_enabled: True
- session_bm25_top_k: 8
- session_anchor_top_k: 2
- session_enabled_route_signals: ['temporal', 'recent_or_current']
- session_bm25_applied_count: 41
- session_bm25_applied_rate: 0.41
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0.0 and max_tokens 128.

## Offline Results

- exact_match: 0.03
- token_f1: 0.30323744092503646
- bleu_unigram: 0.23508689750504044
- evidence_recall: 0.7857142857142857
- baseline: stage1_session_bm25_temporal_p4_locomo_100 had token_f1 0.28101885421163425 and evidence_recall 0.7857142857142857.
- dense_baseline: stage1_dense_k12_concise_locomo_100 had token_f1 0.27571269917466834 and evidence_recall 0.7653061224489796.

## Diagnosis

- Temporal grounding is positive on LoCoMo 100 for lexical overlap: F1 improves by about 0.022 over gated session BM25 without changing retrieval recall.
- The improvement comes from answer-side normalization of relative time expressions, not from extra evidence.
- Exact-match drops from 0.04 to 0.03, so exact lexical matching is not reliable for this benchmark; judge evaluation is still needed.
- Avg query tokens increase from 2776.52 to 2830.58, still well under the 6K target budget.
- Qualitative inspection shows some remaining temporal reasoning mistakes, so a verifier should check date arithmetic against row timestamps rather than only prompting the answer model.
- DeepSeek judge dry-run was written to /data/home_new/wujinqi/agent-memory/experiments/stage1_session_bm25_temporal_p4_grounded_locomo_100/deepseek_judge_dry_run.json; real judge was not run because DEEPSEEK_API_KEY was missing from the shell environment.

## Next Steps

- Add a clean temporal verifier/compiler pass that normalizes relative expressions deterministically from source timestamps.
- Run real DeepSeek judge once DEEPSEEK_API_KEY is available in the environment without writing the key to disk.
- Keep gated session BM25 plus temporal grounding as the current LoCoMo 100 candidate.
