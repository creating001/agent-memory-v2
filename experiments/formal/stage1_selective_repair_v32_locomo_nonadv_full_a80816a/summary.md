# stage1_selective_repair_v32_locomo_nonadv_full_a80816a

## Purpose

Stage-1 clean skeleton run: validate raw evidence storage, lexical retrieval, neighbor expansion, evidence compilation, answer generation, trace output, and experiment bookkeeping.

## Scope

- benchmark: locomo
- subset: non_adversarial_full
- experiment_kind: formal
- limit: None
- workers: 8
- input_path: /data/home_new/wujinqi/agent-memory/outputs/prepare_locomo_non_adversarial/prediction_input.jsonl
- config_path: /data/home_new/wujinqi/agent-memory/configs/stage1_selective_repair_v32_cached.json
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0, max_input_tokens 131072, and max_output_tokens 16384.

## Git

- inside_work_tree: True
- commit: a80816adac107d8cb05e177a3623e6f2385c1046
- dirty: True
- note: None

## Metrics

- n_samples: 1540
- accuracy: None
- f1: None
- bleu: None
- avg_build_tokens: 58386.00779220779
- build_token_accounting: logical cold-build LLM tokens; cached build chunks count from stored usage, while cache hits only avoid repeated local API calls.
- avg_query_tokens: 4466.223376623377
- avg_compiled_evidence_items: 40.0
- build_memory_enabled: True
- build_memory_model: Qwen/Qwen3-30B-A3B-Instruct-2507
- build_memory_temporal_fields: False
- build_memory_cache_enabled: True
- build_memory_cache_path: outputs/cache/qwen3_build_memory.sqlite
- build_memory_cache_hits: 12411
- build_memory_cache_misses: 0
- build_memory_cache_writes: 0
- avg_build_memory_records: 136.65974025974026
- avg_active_build_memory_records: 125.11233766233767
- avg_memory_hits: 19.84155844155844
- avg_memory_source_hits: 22.37922077922078
- build_memory_include_superseded: False
- build_memory_include_superseded_information_needs: ['temporal_lookup', 'list_count']
- neighbor_order: hit_priority
- drop_query_stopwords: True
- lexical_enabled: True
- dense_enabled: True
- lexical_protect_top_n: 0
- dense_protect_top_n: 32
- dense_document_text_mode: external_naive
- dense_query_text_mode: external_naive
- embedding_cache_enabled: True
- embedding_cache_path: outputs/cache/qwen3_embedding.sqlite
- embedding_cache_hits: 7422
- embedding_cache_misses: 0
- embedding_cache_writes: 0
- session_bm25_enabled: False
- session_bm25_top_k: None
- session_anchor_top_k: None
- session_max_anchor_hits: None
- session_protect_turn_hits: None
- session_enabled_route_signals: None
- session_enabled_information_needs: None
- session_enabled_query_patterns: None
- session_bm25_applied_count: 0
- session_bm25_applied_rate: 0.0
- avg_embedding_tokens: 0.0
- avg_context_chars: 11416.253896103895
- compiler_prompt_mode: external_naive
- answer_mode: openai_compatible
- answer_model: Qwen/Qwen3-30B-A3B-Instruct-2507
- answer_max_input_tokens: 131072
- answer_max_output_tokens: 16384
- answer_output_format: json_answer
- answer_cache_enabled: True
- answer_cache_path: outputs/cache/qwen3_answer_v29.sqlite
- answer_cache_namespace: stage1_temporal_event_contract_v29_qwen3_30b
- answer_cache_hits: 1540
- answer_cache_misses: 0
- answer_cache_writes: 0
- answer_finalizer_enabled: False
- answer_finalizer_mode: structured_evidence_mechanical
- answer_finalizer_enable_count_correction: False
- answer_finalizer_enable_money_sum_correction: True
- answer_finalizer_applied_count: 0
- answer_finalizer_applied_rate: 0.0
- answer_repair_enabled: True
- answer_repair_mode: openai_compatible
- answer_repair_model: Qwen/Qwen3-30B-A3B-Instruct-2507
- answer_repair_max_input_tokens: 131072
- answer_repair_max_output_tokens: 16384
- answer_repair_output_format: json_answer
- answer_repair_information_needs: ['current_state', 'fact_lookup', 'list_count', 'profile_preference', 'temporal_lookup']
- answer_repair_enable_uncertain_trigger: True
- answer_repair_enable_short_list_trigger: True
- answer_repair_enable_temporal_conflict_trigger: True
- answer_repair_max_context_chars: 14000
- answer_repair_max_row_text_chars: 700
- answer_repair_cache_enabled: True
- answer_repair_cache_path: outputs/cache/qwen3_answer_repair_v32.sqlite
- answer_repair_cache_namespace: stage1_selective_repair_v32_qwen3_30b
- answer_repair_cache_hits: 263
- answer_repair_cache_misses: 0
- answer_repair_cache_writes: 0
- answer_repair_triggered_count: 263
- answer_repair_triggered_rate: 0.17077922077922078
- answer_repair_applied_count: 11
- answer_repair_applied_rate: 0.007142857142857143
- answer_repair_total_query_tokens: 819828
- answer_repair_avg_query_tokens_when_triggered: 3117.216730038023
- answer_style: concise
- evidence_order: retrieval
- memory_order: retrieval
- memory_layout: flat
- row_text_mode: full
- max_row_text_chars: 0
- evidence_row_labels: False
- final_answer_checklist: False
- max_memory_records: 0
- route_guidance: False
- temporal_grounding: False
- temporal_hints: False
- temporal_workpad: True
- temporal_text_normalization: True
- temporal_event_contract: True
- temporal_workpad_scope: route
- temporal_workpad_max_rows: 12
- temporal_workpad_max_pairs: 12
- structured_guide: True
- structured_guide_max_rows: 12
- structured_guide_include_rows: True
- structured_guide_include_memory: False
- structured_guide_disabled_signals: ['personalized_recommendation']
- structured_answer_contract: False
- structured_answer_contract_information_needs: None
- structured_answer_contract_max_items: 10
- evidence_report_contract: True
- evidence_report_information_needs: ['current_state', 'fact_lookup', 'list_count', 'profile_preference', 'temporal_lookup']
- evidence_report_max_items: 8
- evidence_report_detail: False
- route_overrides: {}
- enable_broad_list_patterns: False
- enable_recommendation_profile_patterns: True
- temporal_priority_over_recent: False

## Outputs

- predictions: /data/home_new/wujinqi/agent-memory/outputs/formal/stage1_selective_repair_v32_locomo_nonadv_full_a80816a/predictions.jsonl
- traces: /data/home_new/wujinqi/agent-memory/outputs/formal/stage1_selective_repair_v32_locomo_nonadv_full_a80816a/traces.jsonl
- metrics: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_selective_repair_v32_locomo_nonadv_full_a80816a/metrics.json
- manifest: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_selective_repair_v32_locomo_nonadv_full_a80816a/manifest.json

## Clean Notes

- No gold/reference/target answer, judge output, benchmark label, sample id, qid, or row index is passed into the prediction pipeline.
- Build-stage typed memory is generated only from raw dialogue and visible metadata; it is recorded separately from offline labels and judge outputs.
- Raw context remains available for fallback and diagnosis; build memory records keep source back-links when produced by the current builder.
- Accuracy is intentionally not computed by the prediction runner; any gold or judge metrics must be produced offline after prediction.

## Offline Judge

- deepseek_accuracy: `0.7616883116883116`
- correct/valid/total: `1173/1540/1540`
- v29 reference: `1173/1540 = 0.7616883116883116`
- result_vs_v29: tied overall, not an improvement
- evidence_recall: `0.8912760416666666`
- judge_usage_total_tokens: `663472`

## Repair Analysis

- draft answer cache was seeded from v29 prediction traces using `scripts/seed_answer_cache_from_traces.py`; this reads prediction traces only, not labels or judge outputs.
- draft answer cache hits/misses/writes: `1540/0/0`
- repair cache hits/misses/writes: `263/0/0`
- repair_triggered: `263/1540 = 0.17077922077922078`
- repair_applied: `11/1540 = 0.007142857142857143`
- repair_applied_delta: fixed `3`, broken `1`, both_correct `2`, both_wrong `5`
- judge_comparison_vs_v29: both_correct `1143`, both_wrong `337`, gained `30`, lost `30`
- conclusion: v32 is token-safe and clean, but the selective repair policy is too conservative and does not improve full LoCoMo accuracy.

## Offline Outputs

- deepseek_judge: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_selective_repair_v32_locomo_nonadv_full_a80816a/deepseek_judge.json
- evidence_recall: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_selective_repair_v32_locomo_nonadv_full_a80816a/evidence_recall.json
- judge_comparison_vs_v29: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_selective_repair_v32_locomo_nonadv_full_a80816a/judge_comparison_vs_v29.json
- repair_applied_delta: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_selective_repair_v32_locomo_nonadv_full_a80816a/repair_applied_delta.json
- repair_applied_draft_judge: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_selective_repair_v32_locomo_nonadv_full_a80816a/repair_applied_draft_judge.json
