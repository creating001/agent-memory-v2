# Diagnosis for formal/stage1_naive_rag_top40_lme_s_full_3f40022

## Summary

Prompt-fixed strict clean naive RAG top-40 是新的 LongMemEval-S full baseline。该方法只使用 raw dialogue turn 的 dense retrieval top-40 和 answer LLM，不使用 build-stage typed memory、lexical fusion、session expansion、question_type、gold、judge 或 sample id。DeepSeek judge accuracy 为 0.646（323/500），高于此前 v6/v7 的 0.606，也高于 prompt 约束前 naive RAG 的 0.640。

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
- avg_context_chars: 16231.018
- avg_query_tokens: 5096.818
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

- accuracy: 323/500 = 0.646000
- previous naive RAG: 320/500 = 0.640000
- v6/v7 baseline: 303/500 = 0.606000
- net change vs previous naive RAG: +3 correct
- net change vs v6/v7: +20 correct
- n_invalid: 0
- judge usage: prompt_tokens=81206, completion_tokens=38318, total_tokens=119524

## By Type

- single-session-assistant: 55/56 = 0.982143
- single-session-user: 66/70 = 0.942857
- knowledge-update: 57/78 = 0.730769
- multi-session: 71/133 = 0.533835
- temporal-reasoning: 65/133 = 0.488722
- single-session-preference: 9/30 = 0.300000

## Evidence Recall

- overall evidence recall: 0.998000 over 500 labeled samples
- all types are 1.000000 except temporal-reasoning at 0.992481

High evidence recall with 0.646 accuracy means the bottleneck is evidence use and reasoning, not raw retrieval recall. The concise final-answer contract improves temporal and multi-session slightly, but preference remains weak.

## Interpretation

- The project baseline has shifted: future LME methods must beat 0.646, not 0.606.
- Build-stage memory must add value on top of raw-turn dense retrieval, not replace it.
- The next general method should keep dense raw evidence available and use build-stage memory for aggregation, state management, and temporal normalization where it measurably improves judge accuracy.

## Next Steps

- Run the same prompt-fixed strict naive RAG top-40 baseline on LoCoMo non-adversarial full.
- Analyze naive RAG badcases by offline question type/category after both benchmarks are recorded.
- Inspect external method code repositories before designing the next general memory method.
