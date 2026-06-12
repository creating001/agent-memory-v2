# Diagnosis for formal/stage1_agent_memory_v1_lme_s_full_b8f58b3_cold

## Summary

The run validates pipeline shape, clean traceability, and answerer integration under the configured experiment kind.

DeepSeek judge accuracy is 0.528 on 500 LongMemEval-S samples. This result is clean and fully traceable, but it is not a competitive baseline. It should be used as the first formal diagnosis point for the next method iteration, not as a satisfactory method.

## Observations

- samples_processed: 500
- avg_compiled_evidence_items: 13.39
- avg_build_memory_records: 129.662
- avg_active_build_memory_records: 116.492
- build_memory_cache_hits: 0
- build_memory_cache_misses: 3341
- build_memory_cache_writes: 3341
- avg_memory_hits: 12.082
- avg_memory_source_hits: 11.912
- avg_context_chars: 20511.524
- avg_query_tokens: 5334.412
- session_bm25_enabled: True
- session_bm25_top_k: 8
- session_anchor_top_k: 2
- session_enabled_route_signals: ['temporal', 'recent_or_current']
- session_bm25_applied_count: 193
- session_bm25_applied_rate: 0.386
- embedding_cache_enabled: True
- embedding_cache_hits: 247238
- embedding_cache_misses: 0
- evidence_order: retrieval
- row_text_mode: full
- max_row_text_chars: 0
- max_memory_records: 10
- route_guidance: True
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0.0 and max_tokens 16384.
- deepseek_judge_accuracy: 0.528
- deepseek_judge_correct: 264
- deepseek_judge_wrong: 236
- deepseek_judge_usage_total_tokens: 118369
- deepseek_judge_usage_prompt_tokens: 77604
- deepseek_judge_usage_completion_tokens: 40765

## DeepSeek Judge By Type

- knowledge-update: 53/78 = 0.6795
- multi-session: 43/133 = 0.3233
- single-session-assistant: 50/56 = 0.8929
- single-session-preference: 8/30 = 0.2667
- single-session-user: 62/70 = 0.8857
- temporal-reasoning: 48/133 = 0.3609

## Diagnosis

- Single-session user and assistant questions are strong enough to show that raw retrieval plus answer generation can work when the evidence is local.
- Multi-session and temporal-reasoning are weak, which points to insufficient multi-session aggregation, temporal state handling, conflict ordering, and answer-time evidence organization.
- Single-session-preference is also weak, which suggests the build memory currently creates many records but does not yet manage stable profile/preference memory well enough for direct use.
- Build cost is within the LongMemEval budget at 80346.246 avg build tokens/sample, and query cost is within budget at 5334.412 avg query tokens/sample. The next iteration should improve memory quality and compiler organization rather than simply increasing context.

## Next Steps

- Run clean, aggregate-only diagnostics over traces to separate retrieval miss, memory hit but wrong compilation, and answer misuse. Do not turn sample entities, record keys, or judge errors into prediction rules.
- Design the next method from general agent-memory principles in `docs/method.md`: profile/event split, temporal state/conflict chain, multi-session evidence aggregation, and compiler changes that organize evidence before answer generation.
- Prefer query-side ablations first when they can reuse this cold build cache; only rerun full cold build when the build prompt, memory schema, memory management, or cache key changes.
- Keep each new method behind explicit config toggles for ablation and report DeepSeek judge accuracy as the main metric.
