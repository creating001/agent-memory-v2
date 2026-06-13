# Diagnosis for formal/stage1_naive_rag_top40_external_lme_s_full_224aa42

## Summary

External-aligned strict clean naive RAG top-40 is the new LongMemEval-S full baseline. It follows the read-only external implementation details that are clean and general: Date+role+text document embeddings, Current Date+Question query embeddings, top-40 dense retrieval, external-style memory context, and JSON answer extraction. DeepSeek judge accuracy is 0.688（344/500）, beating the previous prompt-fixed naive RAG at 0.646 and the typed-memory v6/v7 line at 0.606.

## Observations

- samples_processed: 500
- avg_compiled_evidence_items: 36.758
- avg_build_memory_records: 0.0
- avg_active_build_memory_records: 0.0
- build_memory_cache_hits: 0
- build_memory_cache_misses: 0
- build_memory_cache_writes: 0
- avg_memory_hits: 0.0
- avg_memory_source_hits: 0.0
- build_memory_include_superseded: False
- build_memory_include_superseded_information_needs: None
- avg_context_chars: 13869.726
- avg_query_tokens: 4101.308
- session_bm25_enabled: False
- session_bm25_top_k: None
- session_anchor_top_k: None
- session_enabled_route_signals: None
- session_bm25_applied_count: 0
- session_bm25_applied_rate: 0.0
- embedding_cache_enabled: True
- embedding_cache_hits: 186
- embedding_cache_misses: 247052
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

- accuracy: 344/500 = 0.688000
- previous prompt-fixed naive RAG: 323/500 = 0.646000
- v6/v7 baseline: 303/500 = 0.606000
- net change vs previous naive RAG: +21 correct
- net change vs v6/v7: +41 correct
- n_invalid: 0
- judge usage: prompt_tokens=78636, completion_tokens=39616, total_tokens=118252

## By Type

- temporal-reasoning: 96/133 = 0.721805
- single-session-assistant: 52/56 = 0.928571
- single-session-user: 65/70 = 0.928571
- knowledge-update: 56/78 = 0.717949
- multi-session: 65/133 = 0.488722
- single-session-preference: 10/30 = 0.333333

## Diagnostic Note

Accuracy is the decision metric. Evidence recall is only diagnostic; here it is 1.000000 and shows that remaining LME errors are answer/reasoning/memory-use failures rather than missing labeled evidence.

## Interpretation

- Faithfully reproducing clean naive RAG details is a major positive correction.
- Date-aware document/query text and JSON answer extraction especially improve temporal-reasoning.
- Build-stage memory must now add value above 0.688 by helping multi-session aggregation and preference/profile stability, not by replacing raw evidence retrieval.

## Next Steps

- Treat 0.688 as the LME baseline to beat.
- Analyze remaining wrong cases in multi-session and single-session-preference before designing the next method.
- Inspect external method code repositories before borrowing any memory-management mechanism.
