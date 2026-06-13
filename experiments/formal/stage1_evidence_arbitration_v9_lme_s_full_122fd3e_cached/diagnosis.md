# Diagnosis for formal/stage1_evidence_arbitration_v9_lme_s_full_122fd3e_cached

## Summary

The run validates pipeline shape, clean traceability, and answerer integration under the configured experiment kind.

## Observations

- samples_processed: 500
- avg_compiled_evidence_items: 26.642
- avg_build_memory_records: 129.662
- avg_active_build_memory_records: 116.492
- build_memory_cache_hits: 3341
- build_memory_cache_misses: 0
- build_memory_cache_writes: 0
- avg_memory_hits: 8.208
- avg_memory_source_hits: 7.894
- build_memory_include_superseded: False
- build_memory_include_superseded_information_needs: ['temporal_lookup', 'list_count']
- avg_context_chars: 22383.794
- avg_query_tokens: 6744.762
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
- row_text_mode: role_query_snippet
- max_row_text_chars: 700
- evidence_row_labels: True
- final_answer_checklist: True
- max_memory_records: 16
- route_guidance: True
- temporal_workpad: True
- temporal_text_normalization: False
- temporal_workpad_scope: route
- temporal_workpad_max_rows: 10
- temporal_workpad_max_pairs: 12
- enable_recommendation_profile_patterns: True
- temporal_priority_over_recent: False
- answer_max_input_tokens: 131072
- answer_max_output_tokens: 16384
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0.0, max_input_tokens 131072, and max_output_tokens 16384.

## Next Steps

- Use offline lexical, judge, and evidence-recall scripts to diagnose quality after prediction is complete.
- Compare typed build memory on/off before adding more expensive answer-time reasoning.
- Keep each new method behind explicit config toggles for ablation.

## Offline Diagnosis

- judge_accuracy: 291/500 = 0.582
- evidence_recall: 0.996
- avg_query_tokens: 6744.762，超过 6K 目标；该结果不能作为主线。
- n_samples_over_8k_total_tokens: 88
- max_completion_tokens: 16384，说明 checklist/证据扩展诱发了长输出风险。
- v9 vs v7: net_correct=-12；multi-session 有收益，但总体负向。
- clean note: judge 和 evidence recall 是离线结果，不得进入 prediction pipeline。
