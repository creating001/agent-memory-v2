# Diagnosis for formal/stage1_route_priority_v6_lme_s_full_a387f79_cached

## Summary

v6 在 v4 基础上只调整 question-text route priority：明确的 when / duration / days / weeks / months / years 等 temporal intent 先于 latest / current / now 等 recent-current 描述词触发。这个改动不读取 gold、judge、question_type、record_key、qid 或样本反馈。

LongMemEval-S full 离线 DeepSeek judge 结果为 303/500 = 0.6060，超过 v4 的 0.5960，是当前 LME 最好结果。

## Observations

- samples_processed: 500
- avg_compiled_evidence_items: 12.522
- avg_build_memory_records: 129.662
- avg_active_build_memory_records: 116.492
- build_memory_cache_hits: 3341
- build_memory_cache_misses: 0
- build_memory_cache_writes: 0
- avg_memory_hits: 7.756
- avg_memory_source_hits: 7.528
- avg_context_chars: 21213.04
- avg_query_tokens: 5657.696
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
- memory_order: question_overlap
- memory_layout: typed_sections
- row_text_mode: full
- max_row_text_chars: 0
- max_memory_records: 16
- route_guidance: True
- temporal_workpad: True
- temporal_text_normalization: False
- temporal_workpad_scope: route
- temporal_workpad_max_rows: 10
- temporal_workpad_max_pairs: 12
- enable_recommendation_profile_patterns: True
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0.0 and max_tokens 16384.

## Offline Judge

- accuracy: 303/500 = 0.6060
- v4 baseline: 298/500 = 0.5960
- net change vs v4: +5 correct
- changed judgments vs v4: 17 improved, 12 regressed
- judge usage: prompt_tokens=77726, completion_tokens=38546, total_tokens=116272

## By Type

- knowledge-update: 57/78 = 0.7308, net 0 vs v4
- multi-session: 49/133 = 0.3684, net +2 vs v4
- single-session-assistant: 47/56 = 0.8393, net -1 vs v4
- single-session-preference: 9/30 = 0.3000, net -2 vs v4
- single-session-user: 63/70 = 0.9000, net +2 vs v4
- temporal-reasoning: 78/133 = 0.5865, net +4 vs v4

## Route Diff

- actual route changes vs v4: 9/500
- route-changed subset: 3 stayed correct, 1 changed from wrong to correct, 5 stayed wrong, 0 changed from correct to wrong
- direct route-priority net on changed subset: +1 correct
- fixed direct example: a duration question containing `latest thriller novel` now routes temporal_lookup instead of current_state.

Full-run judge net is +5, larger than the direct route-change subset. Because answer generation is live vLLM inference with parallel workers, some unchanged-route samples can still differ between runs. Treat v6 as a positive full-run result, but do not over-attribute all +5 to route priority alone.

## Evidence Recall

- overall evidence recall: 0.978 over 500 samples
- temporal-reasoning recall: 0.9699
- multi-session recall: 0.9624
- single-session-preference recall: 0.9667

The remaining errors are not primarily evidence-missing errors. The system often retrieves the right session but still fails to count, choose among competing facts, or express preferences/state at the right abstraction level.

## Interpretation

- The route priority change is general: explicit temporal intent should determine route even when the described entity contains words like latest/current.
- The improvement is strongest on temporal-reasoning and multi-session, which matches the intended failure mode.
- Preference remains weak and regresses vs v4; this is not solved by route priority. It points back to build-stage profile/preference management and answer compiler stability.
- List/count remains weak despite high evidence recall; this needs better memory organization or a count/list compiler strategy, not just wider retrieval.

## Next Steps

- Validate v6 on LoCoMo non-adversarial full because it is now the best LME clean configuration and LoCoMo impact surface is tiny but relevant.
- In parallel, design the next substantive method as build-stage memory state/timeline management: active vs historical state, profile/preference vs one-time event, source-linked temporal validity, and list/count aggregation support.
- Keep v5 as negative ablation; do not re-enable temporal_text_normalization by default.
