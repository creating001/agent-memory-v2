# formal/stage1_temporal_text_v5_lme_s_full_e875d29_cached

## Purpose

Stage-1 clean skeleton run: validate raw evidence storage, lexical retrieval, neighbor expansion, evidence compilation, answer generation, trace output, and experiment bookkeeping.

## Scope

- benchmark: longmemeval_s
- subset: full
- experiment_kind: formal
- limit: None
- workers: 8
- input_path: /data/home_new/wujinqi/agent-memory/outputs/prepare_longmemeval_s_cleaned/prediction_input.jsonl
- config_path: /data/home_new/wujinqi/agent-memory/configs/stage1_temporal_text_v5_cached.json
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0.0 and max_tokens 16384.

## Git

- inside_work_tree: True
- commit: e875d298db3bc52190de2eae28e79da8fbc9093b
- dirty: False
- note: None

## Metrics

- n_samples: 500
- accuracy: None
- f1: None
- bleu: None
- avg_build_tokens: 0.0
- avg_query_tokens: 5683.876
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
- avg_context_chars: 21313.04
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
- temporal_text_normalization: True
- temporal_workpad_scope: route
- temporal_workpad_max_rows: 10
- temporal_workpad_max_pairs: 12
- enable_broad_list_patterns: False
- enable_recommendation_profile_patterns: True

## DeepSeek Judge

- accuracy: 295/500 = 0.5900
- n_valid: 500
- n_invalid: 0
- judge_model: deepseek-v4-flash
- judge_prompt_tokens: 77934
- judge_completion_tokens: 36249
- judge_total_tokens: 114183

## DeepSeek Judge By Type

- knowledge-update: 56/78 = 0.7179
- multi-session: 47/133 = 0.3534
- single-session-assistant: 48/56 = 0.8571
- single-session-preference: 8/30 = 0.2667
- single-session-user: 62/70 = 0.8857
- temporal-reasoning: 74/133 = 0.5564

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
- v5 vs v4: 12 improved, 15 regressed, -3 net correct
- net by type: knowledge-update -1, multi-session 0, single-session-assistant 0, single-session-preference -3, single-session-user +1, temporal-reasoning 0
- interpretation: adding relative-time mentions to the temporal workpad did not improve LongMemEval-S; temporal-reasoning had equal wins and losses, while preference questions regressed.
- decision: keep v5 as a clean negative ablation, not the mainline default.

## Outputs

- predictions: /data/home_new/wujinqi/agent-memory/outputs/formal/stage1_temporal_text_v5_lme_s_full_e875d29_cached/predictions.jsonl
- traces: /data/home_new/wujinqi/agent-memory/outputs/formal/stage1_temporal_text_v5_lme_s_full_e875d29_cached/traces.jsonl
- metrics: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_temporal_text_v5_lme_s_full_e875d29_cached/metrics.json
- manifest: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_temporal_text_v5_lme_s_full_e875d29_cached/manifest.json
- deepseek_judge: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_temporal_text_v5_lme_s_full_e875d29_cached/deepseek_judge.json
- deepseek_judge_partial: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_temporal_text_v5_lme_s_full_e875d29_cached/deepseek_judge.json.partial.jsonl
- offline_evidence_recall: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_temporal_text_v5_lme_s_full_e875d29_cached/evidence_recall.json

## Clean Notes

- No gold/reference/target answer, judge output, benchmark label, sample id, qid, or row index is passed into the prediction pipeline.
- Build-stage typed memory is generated only from raw dialogue and visible metadata; it is recorded separately from offline labels and judge outputs.
- Raw context remains available for fallback and diagnosis; build memory records keep source back-links when produced by the current builder.
- Accuracy is intentionally not computed by the prediction runner; any gold or judge metrics must be produced offline after prediction.
- DeepSeek judge and evidence recall were run offline after predictions were written. Judge labels, gold answers, question_type, and record_key must not be consumed by prediction, retrieval, compiler, answer, or verifier code.

## Conclusion

v5 is a clean but negative LME ablation. The method is general and source-only at prediction time, but LME accuracy drops from v4 0.5960 to 0.5900, so the current best LME method remains v4. The next method should focus on build-stage memory management and temporal/state validity instead of adding more answer-time hints.
