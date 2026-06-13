# Diagnosis for stage1_temporal_aid_v13_lme_s_full_8e8f070

## Summary

v13 在 LongMemEval-S full 上达到 357/500 = 0.714 DeepSeek judge accuracy，与 v12 持平，并保持高于 clean naive RAG 0.688。token gate 通过：avg_build_tokens 80346.246，avg_query_tokens 4614.806。

Temporal Aid 只做通用日历换算，把 retrieved raw rows 中的相对时间表达按该 row timestamp 归一化；它不使用 question_type、gold、judge、sample id 或样本实体规则。LME 上该改动没有总分收益，但 temporal-reasoning 小幅正向。

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
- avg_context_chars: 15788.524
- avg_query_tokens: 4614.806
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
- max_memory_records: 0
- route_guidance: False
- temporal_workpad: True
- temporal_text_normalization: True
- temporal_workpad_scope: route
- temporal_workpad_max_rows: 12
- temporal_workpad_max_pairs: 12
- route_overrides: {}
- enable_recommendation_profile_patterns: False
- temporal_priority_over_recent: False
- answer_max_input_tokens: 131072
- answer_max_output_tokens: 16384
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0, max_input_tokens 131072, and max_output_tokens 16384.

## Judge Diagnosis

- accuracy: 357/500 = 0.714
- evidence_recall: 500/500 = 1.0
- temporal_aid_prompts: 198/500 = 0.396
- vs_v12: v13-only 27, v12-only 27, net 0
- vs_naive_external_top40: v13-only 31, naive-only 18, net +13
- positive_delta_vs_v12: temporal-reasoning net +1; single-session-preference net +1; single-session-assistant net +1
- negative_delta_vs_v12: single-session-user net -2; multi-session net -1
- main_risk: LME 的剩余瓶颈仍是证据选择和答案聚合，单纯日期辅助不能解决 multi-session/profile 类错误。
- dirty_note: prediction manifest dirty True 的原因是已有 LoCoMo v13 experiment artifacts 未跟踪；没有未提交代码 diff 参与 prediction。

## Next Steps

- LME 下一步应做 general memory-aware evidence table：保留 v12/v13 raw source expansion，同时让 compiler 更稳定地区分 profile/preference、assistant/user source 和 conflict chains。
- 不扩大 top-k；当前 evidence recall 已经是 1.0，继续堆 context 性价比低。
- 任何改动必须继续保持 question-text/runtime-metadata only，不使用 benchmark label 或样本级反馈。
