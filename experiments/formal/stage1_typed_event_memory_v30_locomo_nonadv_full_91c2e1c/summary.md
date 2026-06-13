# stage1_typed_event_memory_v30_locomo_nonadv_full_91c2e1c

## Purpose

Stage-1 clean skeleton run: validate raw evidence storage, lexical retrieval, neighbor expansion, evidence compilation, answer generation, trace output, and experiment bookkeeping.

## Scope

- benchmark: locomo
- subset: non_adversarial_full
- experiment_kind: formal
- limit: None
- workers: 8
- input_path: /data/home_new/wujinqi/agent-memory/outputs/prepare_locomo_non_adversarial/prediction_input.jsonl
- config_path: /data/home_new/wujinqi/agent-memory/configs/stage1_typed_event_memory_v30_cached.json
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0, max_input_tokens 131072, and max_output_tokens 16384.

## Git

- inside_work_tree: True
- commit: 91c2e1c2b73dde4f8372ac20400725d205582263
- dirty: True
- note: None

## Metrics

- n_samples: 1540
- DeepSeek judge accuracy: 0.755685510071475
- DeepSeek judge correct/valid/total: 1163/1539/1540
- DeepSeek judge invalid: 1
- comparison_vs_v29: -10 correct overall; excluding exact-same-answer judge flips, changed-answer delta is about -7.
- conclusion: v30 is a negative LoCoMo full result and should not replace v29 as the current LoCoMo mainline.
- f1: None
- bleu: None
- avg_build_tokens: 61047.40909090909
- build_token_accounting: logical cold-build LLM tokens; cached build chunks count from stored usage, while cache hits only avoid repeated local API calls.
- avg_query_tokens: 4047.9045454545453
- avg_compiled_evidence_items: 40.0
- build_memory_enabled: True
- build_memory_model: Qwen/Qwen3-30B-A3B-Instruct-2507
- build_memory_temporal_fields: True
- build_memory_cache_enabled: True
- build_memory_cache_path: outputs/cache/qwen3_build_memory.sqlite
- build_memory_cache_hits: 11784
- build_memory_cache_misses: 627
- build_memory_cache_writes: 627
- avg_build_memory_records: 94.45454545454545
- avg_active_build_memory_records: 89.79935064935064
- avg_memory_hits: 19.822727272727274
- avg_memory_source_hits: 21.43896103896104
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
- avg_context_chars: 11771.485064935065
- compiler_prompt_mode: external_naive
- answer_mode: openai_compatible
- answer_model: Qwen/Qwen3-30B-A3B-Instruct-2507
- answer_max_input_tokens: 131072
- answer_max_output_tokens: 16384
- answer_output_format: json_answer
- answer_cache_enabled: True
- answer_cache_path: outputs/cache/qwen3_answer_v30.sqlite
- answer_cache_namespace: stage1_typed_event_memory_v30_qwen3_30b
- answer_cache_hits: 11
- answer_cache_misses: 1529
- answer_cache_writes: 1529
- answer_finalizer_enabled: False
- answer_finalizer_mode: structured_evidence_mechanical
- answer_finalizer_enable_count_correction: False
- answer_finalizer_enable_money_sum_correction: True
- answer_finalizer_applied_count: 0
- answer_finalizer_applied_rate: 0.0
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
- route_overrides: {'temporal_lookup': {'max_memory_records': 8, 'structured_guide_include_memory': True}, 'current_state': {'max_memory_records': 6, 'structured_guide_include_memory': True}}
- enable_broad_list_patterns: False
- enable_recommendation_profile_patterns: True
- temporal_priority_over_recent: False
- evidence_recall: 0.8802083333333334
- evidence_recall_vs_v29: 0.8802083333333334 vs 0.8893229166666666
- delta_vs_v29: both_correct=1106, both_wrong_or_invalid=310, gained=57, lost=67
- delta_by_route: fact_lookup gained=33/lost=34; temporal_lookup gained=15/lost=21; list_count gained=6/lost=9; profile_preference gained=3/lost=3.

## Outputs

- predictions: /data/home_new/wujinqi/agent-memory/outputs/formal/stage1_typed_event_memory_v30_locomo_nonadv_full_91c2e1c/predictions.jsonl
- traces: /data/home_new/wujinqi/agent-memory/outputs/formal/stage1_typed_event_memory_v30_locomo_nonadv_full_91c2e1c/traces.jsonl
- metrics: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_typed_event_memory_v30_locomo_nonadv_full_91c2e1c/metrics.json
- manifest: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_typed_event_memory_v30_locomo_nonadv_full_91c2e1c/manifest.json
- deepseek_judge: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_typed_event_memory_v30_locomo_nonadv_full_91c2e1c/deepseek_judge.json
- evidence_recall: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_typed_event_memory_v30_locomo_nonadv_full_91c2e1c/evidence_recall.json
- offline_comparison: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_typed_event_memory_v30_locomo_nonadv_full_91c2e1c/offline_comparison.json

## Accuracy Diagnosis

v30 把 build memory 的 validity 管理限制到 `state/profile/preference/relationship`，避免一次性 `event/fact/plan` 被误当成持续状态。这个设计更干净，也通过字段门禁，但 LoCoMo full 没有提升：v30 为 `0.755686`，低于 v29 的 `0.761688`。

差异里有一部分来自 judge 抖动：932 条 v29/v30 答案完全相同，其中 15 条 judge 标签翻转。只看答案发生变化的样本，v30 是 `+51/-58`，净少约 7 条正确。更关键的是 evidence recall 从 v29 的 `0.889323` 降到 `0.880208`，avg memory source hits 从 `22.381` 降到 `21.439`。这说明 v30 typed memory 记录减少后，source activation 覆盖略降，且 answer/compiler 没有稳定利用新增 temporal fields。

因此 v30 结论是负向 ablation：保留 stateful validity 修正作为代码能力，但当前 config 不作为主线。下一步不应继续盲跑 v30 LongMemEval full，而应设计一个更稳的 v31：恢复/提升 source activation 覆盖，同时只把 typed temporal fields 作为 compiler 辅助，不让它降低 raw evidence 召回。

## Clean Notes

- No gold/reference/target answer, judge output, benchmark label, sample id, qid, or row index is passed into the prediction pipeline.
- Build-stage typed memory is generated only from raw dialogue and visible metadata; it is recorded separately from offline labels and judge outputs.
- Raw context remains available for fallback and diagnosis; build memory records keep source back-links when produced by the current builder.
- Accuracy was computed only after prediction by the offline DeepSeek judge. Judge labels, gold answers, benchmark labels, evidence ids, and sample ids were used only for this offline summary/diagnosis and must not be read by prediction modules.
