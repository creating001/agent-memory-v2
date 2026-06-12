# Diagnosis for stage1_session_bm25_temporal_p4_grounded_strict_lme_s_100

## Summary

The run validates pipeline shape, clean traceability, and answerer integration under the configured experiment kind.

## Observations

- samples_processed: 100
- avg_compiled_evidence_items: 13.93
- avg_context_chars: 17652.75
- avg_query_tokens: 4371.14
- session_bm25_enabled: True
- session_bm25_top_k: 8
- session_anchor_top_k: 2
- session_enabled_route_signals: ['temporal', 'recent_or_current']
- session_bm25_applied_count: 36
- session_bm25_applied_rate: 0.36
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0.0 and max_tokens 128.

## Offline Results

- exact_match: 0.52
- token_f1: 0.6352964073078624
- bleu_unigram: 0.6107978429885426
- evidence_recall: 0.99
- baseline: stage1_concise_lme_s_100 had exact_match 0.4, token_f1 0.5320425887579914, and evidence_recall 0.95.

## Diagnosis

- The strict candidate is positive on LongMemEval-S 100 as an expensive diagnostic: exact, F1, BLEU, and evidence recall all improve.
- Query tokens remain inside the 6K budget at avg_query_tokens 4371.14.
- The cost problem is dense embedding: avg_embedding_tokens is 104483.7 per sample, so this should not become the default LME setting without caching or a cheaper retrieval variant.
- This result suggests the method is not LoCoMo-only; the same clean multi-view retrieval plus strict temporal answer compiler helps LME too.
- DeepSeek judge dry-run was written to /data/home_new/wujinqi/agent-memory/experiments/stage1_session_bm25_temporal_p4_grounded_strict_lme_s_100/deepseek_judge_dry_run.json; real judge was not run because DEEPSEEK_API_KEY was missing from the shell environment.

## Next Steps

- Add embedding/document caching before full LME runs.
- Build a cheaper LME ablation that keeps strict temporal compiler but disables dense retrieval or uses cached dense vectors.
- Run real DeepSeek judge once DEEPSEEK_API_KEY is available in the environment without writing the key to disk.
