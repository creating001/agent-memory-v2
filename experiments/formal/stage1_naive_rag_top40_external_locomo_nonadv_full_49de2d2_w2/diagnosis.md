# Diagnosis for formal/stage1_naive_rag_top40_external_locomo_nonadv_full_49de2d2_w2

## Summary

External-aligned strict clean naive RAG top-40 is a small positive LoCoMo baseline. This run follows the read-only external implementation details that are clean and general: Date+role+text document embeddings, Current Date+Question query embeddings, top-40 dense retrieval, external-style memory context, and JSON answer extraction. DeepSeek judge accuracy is 0.698506（1075/1539 valid），slightly above v4's 0.695906.

## Observations

- samples_processed: 1540
- avg_compiled_evidence_items: 40.0
- avg_build_memory_records: 0.0
- avg_active_build_memory_records: 0.0
- build_memory_cache_hits: 0
- build_memory_cache_misses: 0
- build_memory_cache_writes: 0
- avg_memory_hits: 0.0
- avg_memory_source_hits: 0.0
- build_memory_include_superseded: False
- build_memory_include_superseded_information_needs: None
- avg_context_chars: 8214.93051948052
- avg_query_tokens: 2650.6435064935067
- session_bm25_enabled: False
- session_bm25_top_k: None
- session_anchor_top_k: None
- session_enabled_route_signals: None
- session_bm25_applied_count: 0
- session_bm25_applied_rate: 0.0
- embedding_cache_enabled: True
- embedding_cache_hits: 1540
- embedding_cache_misses: 5882
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

- accuracy_valid_only: 1075/1539 = 0.698506
- accuracy_invalid_as_wrong: 1075/1540 = 0.698052
- previous v4 best: 1071/1539 = 0.695906
- net change vs v4: +4 correct
- net change vs v7: +25 correct
- n_invalid: 1
- judge usage: prompt_tokens=496353, completion_tokens=159077, total_tokens=655430

## By Category

- category 1: 183/282 = 0.648936
- category 2: 152/321 = 0.473520
- category 3: 58/96 = 0.604167
- category 4: 682/840 = 0.811905, invalid 1

## By Route

- fact_lookup: 788/1017 = 0.774828, invalid 1
- temporal_lookup: 181/338 = 0.535503
- list_count: 69/131 = 0.526718
- profile_preference: 34/49 = 0.693878
- current_state: 3/4 = 0.750000

## Diagnostic Note

Accuracy is the decision metric. Evidence recall is only used here as a diagnostic. The earlier pure dense-only run scored 0.555 because it did not faithfully reproduce the clean external naive RAG implementation; it has been deleted and should not be treated as a formal baseline.

## Interpretation

- Correctly aligned naive RAG is already competitive on LoCoMo and slightly beats v4.
- The gain is small, so the next method must be planned carefully and validated full-run.
- The strongest general direction is not replacing raw dense retrieval, but adding build-stage memory management or hybrid candidate generation that improves answer accuracy on top of this baseline.

## Next Steps

- Treat 0.698506 as the LoCoMo baseline to beat.
- Run the same external-aligned naive RAG on LongMemEval-S full if exact cross-benchmark comparability is needed.
- Before the next new method, analyze accuracy badcases and inspect external method code repositories for the mechanism being borrowed.
