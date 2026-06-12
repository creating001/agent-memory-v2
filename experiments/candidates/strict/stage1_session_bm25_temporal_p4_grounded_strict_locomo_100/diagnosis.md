# Diagnosis for stage1_session_bm25_temporal_p4_grounded_strict_locomo_100

## Summary

The run validates pipeline shape, clean traceability, and answerer integration under the configured experiment kind.

## Observations

- samples_processed: 100
- avg_compiled_evidence_items: 34.13
- avg_context_chars: 9317.68
- avg_query_tokens: 2832.96
- session_bm25_enabled: True
- session_bm25_top_k: 8
- session_anchor_top_k: 2
- session_enabled_route_signals: ['temporal', 'recent_or_current']
- session_bm25_applied_count: 41
- session_bm25_applied_rate: 0.41
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0.0 and max_tokens 128.

## Offline Results

- exact_match: 0.09
- token_f1: 0.3938473303083172
- bleu_unigram: 0.329455353419273
- evidence_recall: 0.7857142857142857
- grounded_baseline: stage1_session_bm25_temporal_p4_grounded_locomo_100 had token_f1 0.30323744092503646 and evidence_recall 0.7857142857142857.
- dense_baseline: stage1_dense_k12_concise_locomo_100 had token_f1 0.27571269917466834 and evidence_recall 0.7653061224489796.

## Diagnosis

- Strict temporal grounding is strongly positive on LoCoMo 100: it improves exact, F1, and BLEU without changing retrieval recall.
- The improvement is answer-side: the same evidence rows are used, but shorter normalized temporal answers are easier to match and inspect.
- Avg query tokens are 2832.96, still within the target budget; embedding tokens are unchanged and recorded separately.
- This should be the current LoCoMo candidate, pending real DeepSeek judge.
- Remaining risk: some temporal date arithmetic is still wrong, so a deterministic temporal verifier remains the next clean method.
- DeepSeek judge dry-run was written to /data/home_new/wujinqi/agent-memory/experiments/candidates/strict/stage1_session_bm25_temporal_p4_grounded_strict_locomo_100/deepseek_judge_dry_run.json; real judge was not run because DEEPSEEK_API_KEY was missing from the shell environment.

## Next Steps

- Run real DeepSeek judge once DEEPSEEK_API_KEY is available in the environment without writing the key to disk.
- Build a clean deterministic temporal verifier/compiler pass for relative date normalization.
- Test the strict temporal candidate beyond the first 100 LoCoMo rows before full benchmark runs.
