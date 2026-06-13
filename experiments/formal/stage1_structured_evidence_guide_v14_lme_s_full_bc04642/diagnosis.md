# Diagnosis for stage1_structured_evidence_guide_v14_lme_s_full_bc04642

## Summary

The run validates pipeline shape, clean traceability, and answerer integration under the configured experiment kind.

## Observations

- samples_processed: 500
- avg_compiled_evidence_items: 35.318
- avg_build_tokens: 80346.246
- build_token_accounting: logical cold-build LLM tokens; cached build chunks count from stored usage, while cache hits only avoid repeated local API calls.
- avg_build_memory_records: 129.662
- avg_active_build_memory_records: 116.492
- build_memory_cache_hits: 3341
- build_memory_cache_misses: 0
- build_memory_cache_writes: 0
- avg_memory_hits: 8.208
- avg_memory_source_hits: 7.894
- build_memory_include_superseded: False
- build_memory_include_superseded_information_needs: ['temporal_lookup', 'list_count']
- avg_context_chars: 18064.726
- avg_query_tokens: 5338.76
- dense_protect_top_n: 32
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
- max_memory_records: 8
- route_guidance: False
- temporal_workpad: True
- temporal_text_normalization: True
- temporal_workpad_scope: route
- temporal_workpad_max_rows: 12
- temporal_workpad_max_pairs: 12
- structured_guide: True
- structured_guide_max_rows: 12
- route_overrides: {}
- enable_recommendation_profile_patterns: False
- temporal_priority_over_recent: False
- answer_max_input_tokens: 131072
- answer_max_output_tokens: 16384
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0, max_input_tokens 131072, and max_output_tokens 16384.

## Next Steps

- DeepSeek judge accuracy is 352/500 = 0.704, below v12/v13 by 5 examples.
- Positive movement: single-session-preference improves over v13 by net +3 and temporal-reasoning by net +2.
- Negative movement: knowledge-update net -4, multi-session net -4, single-session-assistant net -2 versus v13.
- Evidence recall remains 1.0, so the main issue is not raw evidence absence; the structured guide likely adds useful indexing for some profile/temporal cases but also distracts the answer model from exact raw rows in update and multi-session cases.
- Do not promote v14 as the LME mainline. If continuing this branch, prefer a smaller guide or a source-linked memory guide that excludes weakly linked records, rather than increasing prompt length or adding benchmark-shaped rules.
