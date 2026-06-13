# Diagnosis for formal/stage1_memory_validity_v7_locomo_nonadv_full_b10bfdf_cached

## Summary

v7 在 LoCoMo non-adversarial full 上是负向验证。该配置复用 v7 build-memory validity cache，开启 temporal/list 的 superseded memory retrieval，但 DeepSeek judge accuracy 只有 0.681818（1050/1540），低于 v4 的 0.695906（1071/1539），只比 v6 多 1 个正确。

预测阶段 clean：只使用 question text、question_time、raw dialogue、build-stage typed memory 和可见 metadata；不使用 gold、judge、category、sample id 或 feedback。

## Observations

- samples_processed: 1540
- avg_compiled_evidence_items: 33.044155844155846
- avg_build_memory_records: 136.65974025974026
- avg_active_build_memory_records: 125.21103896103897
- build_memory_cache_hits: 12411
- build_memory_cache_misses: 0
- build_memory_cache_writes: 0
- avg_memory_hits: 19.84155844155844
- avg_memory_source_hits: 22.381168831168832
- build_memory_include_superseded: False
- build_memory_include_superseded_information_needs: ['temporal_lookup', 'list_count']
- avg_context_chars: 14577.615584415584
- avg_query_tokens: 4715.416883116883
- session_bm25_enabled: True
- session_bm25_top_k: 8
- session_anchor_top_k: 2
- session_enabled_route_signals: ['temporal', 'recent_or_current']
- session_bm25_applied_count: 522
- session_bm25_applied_rate: 0.33896103896103896
- embedding_cache_enabled: True
- embedding_cache_hits: 927698
- embedding_cache_misses: 0
- evidence_order: question_overlap
- memory_order: question_overlap
- memory_layout: typed_sections
- row_text_mode: full
- max_row_text_chars: 0
- evidence_row_labels: False
- final_answer_checklist: False
- max_memory_records: 16
- route_guidance: True
- temporal_workpad: True
- temporal_text_normalization: False
- temporal_workpad_scope: route
- temporal_workpad_max_rows: 10
- temporal_workpad_max_pairs: 12
- route_overrides: {}
- enable_recommendation_profile_patterns: True
- temporal_priority_over_recent: False
- answer_max_input_tokens: 131072
- answer_max_output_tokens: 16384
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0.0, max_input_tokens 131072, and max_output_tokens 16384.

## Offline Judge

- accuracy_valid_only: 1050/1540 = 0.681818
- accuracy_invalid_as_wrong: 1050/1540 = 0.681818
- v4 baseline valid-only: 1071/1539 = 0.695906
- net change vs v4: -21 correct
- net change vs v6: +1 correct
- n_invalid: 0
- judge usage: prompt_tokens=497751, completion_tokens=157496, total_tokens=655247

## By Category

- category 1: 169/282 = 0.599291
- category 2: 130/321 = 0.404984
- category 3: 53/96 = 0.552083
- category 4: 698/841 = 0.829964

Compared with v4, category 4 loses the most absolute correct answers, and category 2 remains weak. Category 3 is slightly better than v6 but still far from target.

## By Route

- fact_lookup: 797/1018 = 0.782908
- temporal_lookup: 148/338 = 0.437870
- list_count: 71/131 = 0.541985
- profile_preference: 32/49 = 0.653061
- current_state: 2/4 = 0.500000

`list_count` and `temporal_lookup` do not become strong despite superseded memory retrieval. This is evidence that the current build-memory validity records are not enough; the answer stage still needs better evidence selection or a stronger retrieval baseline.

## Evidence Recall

- overall evidence recall: 0.830729 over 1536 labeled samples
- category 1 recall: 0.734043
- category 2 recall: 0.856698
- category 3 recall: 0.500000
- category 4 recall: 0.889417

Recall is nearly unchanged from v4/v6, while accuracy stays low. The bottleneck is not only whether labeled evidence appears in context; it is also evidence ranking, noise control, and answer-time use of retrieved turns.

## Interpretation

- v7 should not be treated as a LoCoMo mainline method. It is below v4 and essentially tied with v6.
- The current branch spends complexity on build-stage typed memory but does not beat a simpler LoCoMo configuration.
- Before designing another build-memory method, the project needs a strong, strict clean naive RAG baseline on both LongMemEval-S full and LoCoMo non-adversarial full.

## Next Steps

- Run `configs/stage1_naive_rag_top40_dense.json` on LongMemEval-S full and LoCoMo non-adversarial full.
- Use DeepSeek judge accuracy as the primary metric; keep F1/BLEU/exact out of method decisions unless needed for auxiliary diagnosis.
- Only after the naive RAG baseline is established, inspect badcases and external code repositories before proposing the next general memory/retrieval improvement.
