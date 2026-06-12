# formal/stage1_route_priority_v6_lme_s_full_a387f79_cached

## Purpose

Stage-1 clean skeleton run: validate raw evidence storage, lexical retrieval, neighbor expansion, evidence compilation, answer generation, trace output, and experiment bookkeeping.

## Scope

- benchmark: longmemeval_s
- subset: full
- experiment_kind: formal
- limit: None
- workers: 8
- input_path: /data/home_new/wujinqi/agent-memory/outputs/prepare_longmemeval_s_cleaned/prediction_input.jsonl
- config_path: /data/home_new/wujinqi/agent-memory/configs/stage1_route_priority_v6_cached.json
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0.0 and max_tokens 16384.

## Git

- inside_work_tree: True
- commit: a387f79c9454b5dbe075e27dc56a92cb2a4e5a99
- dirty: False
- note: None

## Metrics

- n_samples: 500
- accuracy: None
- f1: None
- bleu: None
- avg_build_tokens: 0.0
- avg_query_tokens: 5657.696
- avg_compiled_evidence_items: 12.522
- build_memory_enabled: True
- build_memory_model: Qwen/Qwen3-30B-A3B-Instruct-2507
- build_memory_cache_enabled: True
- build_memory_cache_path: outputs/cache/qwen3_build_memory.sqlite
- build_memory_cache_hits: 3341
- build_memory_cache_misses: 0
- build_memory_cache_writes: 0
- avg_build_memory_records: 129.662
- avg_active_build_memory_records: 116.492
- avg_memory_hits: 7.756
- avg_memory_source_hits: 7.528
- neighbor_order: hit_priority
- drop_query_stopwords: True
- dense_enabled: True
- lexical_protect_top_n: 2
- embedding_cache_enabled: True
- embedding_cache_path: outputs/cache/qwen3_embedding.sqlite
- embedding_cache_hits: 247238
- embedding_cache_misses: 0
- embedding_cache_writes: 0
- session_bm25_enabled: True
- session_bm25_top_k: 8
- session_anchor_top_k: 2
- session_max_anchor_hits: 12
- session_protect_turn_hits: 4
- session_enabled_route_signals: ['temporal', 'recent_or_current']
- session_enabled_information_needs: None
- session_enabled_query_patterns: ['\\b20\\d{2}\\b', '\\b(?:january|february|march|april|june|july|august|september|october|november|december)\\b', '\\bmay\\s+20\\d{2}\\b']
- session_bm25_applied_count: 193
- session_bm25_applied_rate: 0.386
- avg_embedding_tokens: 0.0
- avg_context_chars: 21213.04
- answer_mode: openai_compatible
- answer_model: Qwen/Qwen3-30B-A3B-Instruct-2507
- answer_style: concise
- evidence_order: question_overlap
- memory_order: question_overlap
- memory_layout: typed_sections
- row_text_mode: full
- max_row_text_chars: 0
- max_memory_records: 16
- route_guidance: True
- temporal_grounding: True
- temporal_hints: True
- temporal_workpad: True
- temporal_text_normalization: False
- temporal_workpad_scope: route
- temporal_workpad_max_rows: 10
- temporal_workpad_max_pairs: 12
- enable_broad_list_patterns: False
- enable_recommendation_profile_patterns: True

## DeepSeek Judge

- accuracy: 303/500 = 0.6060
- n_valid: 500
- n_invalid: 0
- judge_model: deepseek-v4-flash
- judge_prompt_tokens: 77726
- judge_completion_tokens: 38546
- judge_total_tokens: 116272

## DeepSeek Judge By Type

- knowledge-update: 57/78 = 0.7308
- multi-session: 49/133 = 0.3684
- single-session-assistant: 47/56 = 0.8393
- single-session-preference: 9/30 = 0.3000
- single-session-user: 63/70 = 0.9000
- temporal-reasoning: 78/133 = 0.5865

## Evidence Recall

- overall: 0.978 over 500 labeled samples
- knowledge-update: 1.0000
- multi-session: 0.9624
- single-session-assistant: 1.0000
- single-session-preference: 0.9667
- single-session-user: 0.9857
- temporal-reasoning: 0.9699

## Comparison

- v4 LME accuracy: 0.5960
- v5 LME accuracy: 0.5900
- v6 LME accuracy: 0.6060
- v6 vs v4: 17 improved, 12 regressed, +5 net correct
- actual route changes vs v4: 9 samples; route-changed subset has +1 net correct and no direct route-change regression.
- by type vs v4: temporal-reasoning +4, multi-session +2, single-session-user +2, knowledge-update 0, single-session-assistant -1, single-session-preference -2.
- interpretation: explicit temporal/duration intent should outrank descriptive latest/current words. The direct route-priority effect is modest but clean; the full-run gain also includes normal answer-model variance.
- decision: v6 is the current best LME configuration and should be considered for LoCoMo validation after a short planning pass.

## Outputs

- predictions: /data/home_new/wujinqi/agent-memory/outputs/formal/stage1_route_priority_v6_lme_s_full_a387f79_cached/predictions.jsonl
- traces: /data/home_new/wujinqi/agent-memory/outputs/formal/stage1_route_priority_v6_lme_s_full_a387f79_cached/traces.jsonl
- metrics: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_route_priority_v6_lme_s_full_a387f79_cached/metrics.json
- manifest: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_route_priority_v6_lme_s_full_a387f79_cached/manifest.json
- deepseek_judge: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_route_priority_v6_lme_s_full_a387f79_cached/deepseek_judge.json
- deepseek_judge_partial: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_route_priority_v6_lme_s_full_a387f79_cached/deepseek_judge.json.partial.jsonl
- offline_evidence_recall: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_route_priority_v6_lme_s_full_a387f79_cached/evidence_recall.json

## Clean Notes

- No gold/reference/target answer, judge output, benchmark label, sample id, qid, or row index is passed into the prediction pipeline.
- Build-stage typed memory is generated only from raw dialogue and visible metadata; it is recorded separately from offline labels and judge outputs.
- Raw context remains available for fallback and diagnosis; build memory records keep source back-links when produced by the current builder.
- Accuracy is intentionally not computed by the prediction runner; any gold or judge metrics must be produced offline after prediction.
- DeepSeek judge and evidence recall were run offline after predictions were written. Judge labels, gold answers, question_type, and record_key must not be consumed by prediction, retrieval, compiler, answer, or verifier code.

## Conclusion

v6 is a clean positive LME ablation and the current best LongMemEval-S full result at 0.6060 DeepSeek judge accuracy. The targeted route change affects only 9/500 LME questions, so it should not be over-claimed as a broad memory-management solution. The next substantial method should still focus on build-stage memory state/timeline management for list/count, preference, and temporal state errors.
