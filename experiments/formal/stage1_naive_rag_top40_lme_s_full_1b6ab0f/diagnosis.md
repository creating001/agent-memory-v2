# Diagnosis for formal/stage1_naive_rag_top40_lme_s_full_1b6ab0f

## Summary

Strict clean naive RAG top-40 是新的 LongMemEval-S full 强 baseline。该方法只使用 raw dialogue turn 的 dense retrieval top-40 和 answer LLM，不使用 build-stage typed memory、lexical fusion、session expansion、question_type、gold、judge 或 sample id。DeepSeek judge accuracy 为 0.640（320/500），高于此前 v6/v7 的 0.606。

## Observations

- samples_processed: 500
- avg_compiled_evidence_items: 35.218
- avg_build_memory_records: 0.0
- avg_active_build_memory_records: 0.0
- build_memory_cache_hits: 0
- build_memory_cache_misses: 0
- build_memory_cache_writes: 0
- avg_memory_hits: 0.0
- avg_memory_source_hits: 0.0
- build_memory_include_superseded: False
- build_memory_include_superseded_information_needs: None
- avg_context_chars: 16108.018
- avg_query_tokens: 5071.432
- session_bm25_enabled: False
- session_bm25_top_k: None
- session_anchor_top_k: None
- session_enabled_route_signals: None
- session_bm25_applied_count: 0
- session_bm25_applied_rate: 0.0
- embedding_cache_enabled: True
- embedding_cache_hits: 247238
- embedding_cache_misses: 0
- evidence_order: retrieval
- memory_order: retrieval
- memory_layout: flat
- row_text_mode: full
- max_row_text_chars: 0
- evidence_row_labels: False
- final_answer_checklist: False
- max_memory_records: 0
- route_guidance: False
- temporal_workpad: False
- temporal_text_normalization: False
- temporal_workpad_scope: route
- temporal_workpad_max_rows: 10
- temporal_workpad_max_pairs: 12
- route_overrides: {}
- enable_recommendation_profile_patterns: False
- temporal_priority_over_recent: False
- answer_max_input_tokens: 131072
- answer_max_output_tokens: 16384
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0.0, max_input_tokens 131072, and max_output_tokens 16384.

## Offline Judge

- accuracy: 320/500 = 0.640000
- v6/v7 baseline: 303/500 = 0.606000
- net change vs v6/v7: +17 correct
- n_invalid: 0
- judge usage: prompt_tokens=81431, completion_tokens=37631, total_tokens=119062

## By Type

- single-session-assistant: 55/56 = 0.982143
- single-session-user: 67/70 = 0.957143
- knowledge-update: 57/78 = 0.730769
- multi-session: 69/133 = 0.518797
- temporal-reasoning: 61/133 = 0.458647
- single-session-preference: 11/30 = 0.366667

## Evidence Recall

- overall evidence recall: 0.998000 over 500 labeled samples
- all types are 1.000000 except temporal-reasoning at 0.992481

High evidence recall with only 0.640 accuracy means the main bottleneck is answer-time evidence use and reasoning, not raw retrieval recall. Temporal-reasoning and preference are the clearest weaknesses.

## Interpretation

- The previous build-memory branch was below a simple dense raw-turn baseline, so future methods must treat 0.640 as the LME floor.
- Build-stage memory is still a project requirement, but it must add value on top of naive RAG rather than replace or obscure the raw-turn signal.
- The next general method should preserve dense raw-turn top-k access and add memory management/reranking/aggregation only where it improves answer accuracy under the same token budget.

## Next Steps

- Run the same strict naive RAG top-40 baseline on LoCoMo non-adversarial full.
- Analyze naive RAG badcases by question-derived information need and benchmark type only offline.
- Inspect external method code repositories before proposing the next general memory method.
