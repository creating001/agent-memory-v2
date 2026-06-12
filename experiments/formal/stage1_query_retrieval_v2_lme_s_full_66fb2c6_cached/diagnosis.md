# Diagnosis for formal/stage1_query_retrieval_v2_lme_s_full_66fb2c6_cached

## Summary

The run validates pipeline shape, clean traceability, and answerer integration under the configured experiment kind.

DeepSeek judge accuracy is 0.540 on 500 LongMemEval-S samples. Compared with the cold-build v1 run, this query-side cleanup changes 34 samples from wrong to correct and 28 from correct to wrong, for a small net gain of 6.

## Observations

- samples_processed: 500
- avg_compiled_evidence_items: 12.49
- avg_build_memory_records: 129.662
- avg_active_build_memory_records: 116.492
- build_memory_cache_hits: 3341
- build_memory_cache_misses: 0
- build_memory_cache_writes: 0
- avg_memory_hits: 7.756
- avg_memory_source_hits: 7.528
- avg_context_chars: 19925.042
- avg_query_tokens: 5133.492
- session_bm25_enabled: True
- session_bm25_top_k: 8
- session_anchor_top_k: 2
- session_enabled_route_signals: ['temporal', 'recent_or_current']
- session_bm25_applied_count: 193
- session_bm25_applied_rate: 0.386
- embedding_cache_enabled: True
- embedding_cache_hits: 247238
- embedding_cache_misses: 0
- evidence_order: question_overlap
- row_text_mode: full
- max_row_text_chars: 0
- max_memory_records: 10
- route_guidance: True
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0.0 and max_tokens 16384.
- deepseek_judge_accuracy: 0.54
- deepseek_judge_correct: 270
- deepseek_judge_wrong: 230
- deepseek_judge_usage_total_tokens: 117677
- deepseek_judge_usage_prompt_tokens: 77890
- deepseek_judge_usage_completion_tokens: 39787

## DeepSeek Judge By Type

- knowledge-update: 51/78 = 0.6538
- multi-session: 50/133 = 0.3759
- single-session-assistant: 48/56 = 0.8571
- single-session-preference: 7/30 = 0.2333
- single-session-user: 63/70 = 0.9000
- temporal-reasoning: 51/133 = 0.3835

## Diagnosis

- The query-side cleanup improves multi-session and temporal-reasoning slightly, which supports the hypothesis that noisy lexical terms and retrieval ordering were hurting some hard cases.
- The regression in knowledge-update, single-session-assistant, and preference shows that stopword filtering plus question-overlap ordering is not a robust main method by itself.
- The remaining main gaps are general memory-state problems: current vs historical fact, stable preference vs one-time event, and aggregating related evidence across sessions without losing raw source context.
- Build cache was fully reused: 3341 hits, 0 misses, 0 writes, 0 avg build tokens. Query cost stayed within budget at 5133.492 avg query tokens.

## Next Steps

- Keep this run as a positive but insufficient query-side ablation.
- Design the next method around profile/event separation and temporal conflict chains, borrowing from LangMem, Memobase, Hindsight, SimpleMem, and Graphiti/Zep while keeping raw turns as final evidence.
- Prefer using the existing cold build cache only if the next change is query/compiler side. If build memory schema or extraction prompt changes, rerun full cold build and report build tokens.
- Do not convert any sample-level changed/regressed cases into prediction rules.
