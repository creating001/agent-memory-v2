# Diagnosis for formal/stage1_route_priority_v6_locomo_nonadv_full_c57e810_cached

## Summary

v6 在 LoCoMo non-adversarial full 上是负向验证。该配置在 LME full 提升到 0.606，但在 LoCoMo valid-only DeepSeek judge accuracy 从 v4 的 0.695906 降到 0.681611。

预测阶段 clean：只使用 question text、question_time、raw dialogue、build-stage typed memory 和可见 metadata；不使用 gold、judge、category、sample id 或 feedback。

## Observations

- samples_processed: 1540
- avg_compiled_evidence_items: 33.044155844155846
- avg_build_memory_records: 136.65974025974026
- avg_active_build_memory_records: 125.21103896103897
- build_memory_cache_hits: 12411
- build_memory_cache_misses: 0
- build_memory_cache_writes: 0
- avg_memory_hits: 19.835064935064935
- avg_memory_source_hits: 22.58051948051948
- avg_context_chars: 13917.034415584416
- avg_query_tokens: 4419.401298701298
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

- accuracy_valid_only: 1049/1539 = 0.681611
- accuracy_invalid_as_wrong: 1049/1540 = 0.681169
- v4 baseline valid-only: 1071/1539 = 0.695906
- net change vs v4: -22 valid correct
- n_invalid: 1
- judge usage: prompt_tokens=497156, completion_tokens=158459, total_tokens=655615

## By Category

- category 1: 169/282 = 0.599291, v4 was 178/281 = 0.633452
- category 2: 129/321 = 0.401869, v4 was 135/321 = 0.420561
- category 3: 52/96 = 0.541667, v4 was 54/96 = 0.562500
- category 4: 699/840 = 0.832143, v4 was 704/841 = 0.837099

## By Route

- fact_lookup: 804/1017 = 0.790560, v4 was 821/1017 = 0.807276
- temporal_lookup: 144/339 = 0.424779, v4 was 146/338 = 0.431953
- list_count: 67/131 = 0.511450, v4 was 70/131 = 0.534351
- profile_preference: 33/49 = 0.673469, v4 was 32/49 = 0.653061
- current_state: 1/3 = 0.333333, v4 was 2/4 = 0.500000

## Route Diff

- actual route changes vs v4: 1/1540
- changed sample: `How long has Caroline had her current group of friends for?`
- changed route: current_state -> temporal_lookup
- judge label: correct in both v4 and v6

The LoCoMo drop is therefore not evidence that route priority itself solved or broke many LoCoMo cases. It is a full-run negative result for this configuration, and the direct LoCoMo route-priority effect is neutral.

## Evidence Recall

- overall evidence recall: 0.830078 over 1536 labeled samples, slightly below v4 0.831380
- category 2 recall: 0.856698, below v4 0.862928
- category 3 recall: 0.500000, unchanged and still a major bottleneck

## Interpretation

- LoCoMo remains bottlenecked by evidence organization, list/count coverage, temporal state, and multi-fact composition.
- The only route change is neutral, so using v6 as LoCoMo mainline is not justified.
- Profile/preference improved slightly, but not enough to offset fact_lookup, temporal_lookup, and list_count drops.

## Next Steps

- Keep `stage1_temporal_preference_v4_cached.json` as the LoCoMo mainline for now.
- For the next method, focus on build-stage memory management rather than route priority: state timeline, active/historical validity, entity-centered event/profile separation, and source-linked list aggregation.
- Any LoCoMo-specific diagnosis must remain offline; no category labels, record keys, judge output, or gold answers can enter prediction logic.
