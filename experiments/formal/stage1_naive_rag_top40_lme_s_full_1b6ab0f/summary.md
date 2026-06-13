# formal/stage1_naive_rag_top40_lme_s_full_1b6ab0f

## Purpose

Stage-1 clean skeleton run: validate raw evidence storage, lexical retrieval, neighbor expansion, evidence compilation, answer generation, trace output, and experiment bookkeeping.

## Scope

- benchmark: longmemeval
- subset: full
- experiment_kind: formal
- limit: None
- workers: 8
- input_path: /data/home_new/wujinqi/agent-memory/outputs/prepare_longmemeval_s_cleaned/prediction_input.jsonl
- config_path: /data/home_new/wujinqi/agent-memory/configs/stage1_naive_rag_top40_dense.json
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0.0, max_input_tokens 131072, and max_output_tokens 16384.

## Git

- inside_work_tree: True
- commit: 1b6ab0f741fe5ef3ec0d07b2fdd6b8b6e4a3e39b
- dirty: False
- note: None

## Metrics

- n_samples: 500
- accuracy: None
- f1: None
- bleu: None
- avg_build_tokens: 0.0
- avg_query_tokens: 5071.432
- avg_compiled_evidence_items: 35.218
- build_memory_enabled: False
- build_memory_model: None
- build_memory_cache_enabled: False
- build_memory_cache_path: None
- build_memory_cache_hits: 0
- build_memory_cache_misses: 0
- build_memory_cache_writes: 0
- avg_build_memory_records: 0.0
- avg_active_build_memory_records: 0.0
- avg_memory_hits: 0.0
- avg_memory_source_hits: 0.0
- build_memory_include_superseded: False
- build_memory_include_superseded_information_needs: None
- neighbor_order: hit_priority
- drop_query_stopwords: False
- lexical_enabled: False
- dense_enabled: True
- lexical_protect_top_n: 0
- embedding_cache_enabled: True
- embedding_cache_path: outputs/cache/qwen3_embedding.sqlite
- embedding_cache_hits: 247238
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
- avg_context_chars: 16108.018
- compiler_prompt_mode: raw_context_only
- answer_mode: openai_compatible
- answer_model: Qwen/Qwen3-30B-A3B-Instruct-2507
- answer_max_input_tokens: 131072
- answer_max_output_tokens: 16384
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
- temporal_workpad: False
- temporal_text_normalization: False
- temporal_workpad_scope: route
- temporal_workpad_max_rows: 10
- temporal_workpad_max_pairs: 12
- route_overrides: {}
- enable_broad_list_patterns: False
- enable_recommendation_profile_patterns: False
- temporal_priority_over_recent: False

## DeepSeek Judge

- accuracy: 320/500 = 0.640000
- n_valid: 500
- n_invalid: 0
- judge_model: deepseek-v4-flash
- judge_prompt_tokens: 81431
- judge_completion_tokens: 37631
- judge_total_tokens: 119062

## DeepSeek Judge By Type

- knowledge-update: 57/78 = 0.730769
- multi-session: 69/133 = 0.518797
- single-session-assistant: 55/56 = 0.982143
- single-session-preference: 11/30 = 0.366667
- single-session-user: 67/70 = 0.957143
- temporal-reasoning: 61/133 = 0.458647

## Evidence Recall

- overall: 0.998000 over 500 labeled samples
- knowledge-update: 1.000000
- multi-session: 1.000000
- single-session-assistant: 1.000000
- single-session-preference: 1.000000
- single-session-user: 1.000000
- temporal-reasoning: 0.992481

## Comparison

- v6 route priority: 303/500 = 0.606000
- v7 memory validity: 303/500 = 0.606000
- naive RAG vs v6/v7: net_correct=+17 (plus=66, minus=49)
- naive RAG vs v11: net_correct=+23 (plus=73, minus=50)
- interpretation: strict clean dense-only naive RAG is the new LongMemEval-S full baseline and beats the typed build-memory branch.
- decision: future LME methods must beat 0.640 DeepSeek judge accuracy, not the previous 0.606 line.

## Outputs

- predictions: /data/home_new/wujinqi/agent-memory/outputs/formal/stage1_naive_rag_top40_lme_s_full_1b6ab0f/predictions.jsonl
- traces: /data/home_new/wujinqi/agent-memory/outputs/formal/stage1_naive_rag_top40_lme_s_full_1b6ab0f/traces.jsonl
- metrics: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_naive_rag_top40_lme_s_full_1b6ab0f/metrics.json
- manifest: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_naive_rag_top40_lme_s_full_1b6ab0f/manifest.json
- deepseek_judge: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_naive_rag_top40_lme_s_full_1b6ab0f/deepseek_judge.json
- deepseek_judge_partial: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_naive_rag_top40_lme_s_full_1b6ab0f/deepseek_judge.json.partial.jsonl
- offline_evidence_recall: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_naive_rag_top40_lme_s_full_1b6ab0f/evidence_recall.json

## Clean Notes

- No gold/reference/target answer, judge output, benchmark label, sample id, qid, or row index is passed into the prediction pipeline.
- Build-stage typed memory is generated only from raw dialogue and visible metadata; it is recorded separately from offline labels and judge outputs.
- Raw context remains available for fallback and diagnosis; build memory records keep source back-links when produced by the current builder.
- Accuracy is intentionally not computed by the prediction runner; any gold or judge metrics must be produced offline after prediction.
- DeepSeek judge and evidence recall were run offline after predictions were written. Judge labels, gold answers, question_type, and record_key must not be consumed by prediction, retrieval, compiler, answer, or verifier code.

## Conclusion

Strict clean naive RAG top-40 reaches 0.640 LongMemEval-S full accuracy with avg_query_tokens 5071.432 and no build tokens. This corrects the baseline: the previous typed build-memory branch was weaker than a simple raw-turn dense retriever. The next method should preserve this strong retrieval floor while improving temporal reasoning, preference, and multi-session aggregation without using benchmark labels or sample-level rules.
