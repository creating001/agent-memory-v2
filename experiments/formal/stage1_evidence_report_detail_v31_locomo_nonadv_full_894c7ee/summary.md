# stage1_evidence_report_detail_v31_locomo_nonadv_full_894c7ee

## Purpose

Stage-1 clean skeleton run: validate raw evidence storage, lexical retrieval, neighbor expansion, evidence compilation, answer generation, trace output, and experiment bookkeeping.

## Scope

- benchmark: locomo
- subset: non_adversarial_full
- experiment_kind: formal
- limit: None
- workers: 8
- input_path: /data/home_new/wujinqi/agent-memory/outputs/prepare_locomo_non_adversarial/prediction_input.jsonl
- config_path: /data/home_new/wujinqi/agent-memory/configs/stage1_evidence_report_detail_v31_cached.json
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0, max_input_tokens 131072, and max_output_tokens 16384.

## Git

- inside_work_tree: True
- commit: 894c7ee1b6203681d8d5c59d5b79eb12fbd1073e
- dirty: True
- note: None

## Metrics

- n_samples: 1540
- DeepSeek judge accuracy: 0.7551948051948052
- DeepSeek judge correct/valid/total: 1163/1540/1540
- comparison_vs_v29: -10 correct overall
- conclusion: v31 is a negative LoCoMo full result and should not replace v29 as the current LoCoMo mainline.
- f1: None
- bleu: None
- avg_build_tokens: 58386.00779220779
- build_token_accounting: logical cold-build LLM tokens; cached build chunks count from stored usage, while cache hits only avoid repeated local API calls.
- avg_query_tokens: 4275.424025974026
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
- avg_context_chars: 12893.451298701299
- compiler_prompt_mode: external_naive
- answer_mode: openai_compatible
- answer_model: Qwen/Qwen3-30B-A3B-Instruct-2507
- answer_max_input_tokens: 131072
- answer_max_output_tokens: 16384
- answer_output_format: json_answer
- answer_cache_enabled: True
- answer_cache_path: outputs/cache/qwen3_answer_v31.sqlite
- answer_cache_namespace: stage1_evidence_report_detail_v31_qwen3_30b
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
- evidence_report_max_items: 12
- evidence_report_detail: True
- evidence_recall: 0.8912760416666666
- evidence_recall_vs_v29: 0.8912760416666666 vs 0.8893229166666666
- delta_vs_v29: both_correct=1118, both_wrong=322, gained=45, lost=55
- delta_by_route: fact_lookup gained=30/lost=25; temporal_lookup gained=6/lost=16; list_count gained=8/lost=10; profile_preference gained=1/lost=4.
- route_overrides: {}
- enable_broad_list_patterns: False
- enable_recommendation_profile_patterns: True
- temporal_priority_over_recent: False

## Outputs

- predictions: /data/home_new/wujinqi/agent-memory/outputs/formal/stage1_evidence_report_detail_v31_locomo_nonadv_full_894c7ee/predictions.jsonl
- traces: /data/home_new/wujinqi/agent-memory/outputs/formal/stage1_evidence_report_detail_v31_locomo_nonadv_full_894c7ee/traces.jsonl
- metrics: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_evidence_report_detail_v31_locomo_nonadv_full_894c7ee/metrics.json
- manifest: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_evidence_report_detail_v31_locomo_nonadv_full_894c7ee/manifest.json
- deepseek_judge: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_evidence_report_detail_v31_locomo_nonadv_full_894c7ee/deepseek_judge.json
- evidence_recall: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_evidence_report_detail_v31_locomo_nonadv_full_894c7ee/evidence_recall.json
- offline_comparison: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_evidence_report_detail_v31_locomo_nonadv_full_894c7ee/offline_comparison.json

## Accuracy Diagnosis

v31 保留了 v29 的 build memory/source activation，并把 evidence recall 从 `0.889323` 提到 `0.891276`，说明 retrieval/source 覆盖没有问题。失败点在 answer/compiler：detailed evidence_report 让模型更谨慎，修复了一些 `unknown`、lower-bound 和 assistant-suggestion 相关错误，但引入更多 temporal/list/profile 回退。

相对 v29：

- gained: `45`
- lost: `55`
- fact_lookup: `+30/-25`
- temporal_lookup: `+6/-16`
- list_count: `+8/-10`
- profile_preference: `+1/-4`

同答案 judge 翻转仍存在：`same_WRONG_to_CORRECT=10`，`same_CORRECT_to_WRONG=7`。只看答案变化，v31 为 `+35/-48`，净少 13 条；整体净少 10 条。因此 v31 不是 judge 噪声导致的假负向，而是方法本身保守化/错选时间证据带来的真实回退。

结论：v31 是有信息的负向 ablation。不要跑 LongMemEval full。下一步应回到 v29 主线，避免继续堆 prompt 规则；应优先设计更稳的 query mechanism，例如轻量二阶段 verifier/repair 只在 answer 可能 unknown、list partial 或 temporal conflict 时触发，并严格控制 token。

## Clean Notes

- No gold/reference/target answer, judge output, benchmark label, sample id, qid, or row index is passed into the prediction pipeline.
- Build-stage typed memory is generated only from raw dialogue and visible metadata; it is recorded separately from offline labels and judge outputs.
- Raw context remains available for fallback and diagnosis; build memory records keep source back-links when produced by the current builder.
- Accuracy was computed only after prediction by the offline DeepSeek judge. Judge labels, gold answers, benchmark labels, evidence ids, and sample ids were used only for this offline summary/diagnosis and must not be read by prediction modules.
