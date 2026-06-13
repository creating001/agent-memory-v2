# formal/stage1_naive_rag_top40_external_lme_s_full_224aa42

## Purpose

Stage-1 clean skeleton run: validate raw evidence storage, lexical retrieval, neighbor expansion, evidence compilation, answer generation, trace output, and experiment bookkeeping.

## Scope

- benchmark: longmemeval
- subset: full
- experiment_kind: formal
- limit: None
- workers: 8
- input_path: /data/home_new/wujinqi/agent-memory/outputs/prepare_longmemeval_s_cleaned/prediction_input.jsonl
- config_path: /data/home_new/wujinqi/agent-memory/configs/stage1_naive_rag_top40_external.json
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0.0, max_input_tokens 131072, and max_output_tokens 16384.

## Git

- inside_work_tree: True
- commit: 224aa42c2db8960b68358324c42dd36494e68b51
- dirty: False
- note: None

## Metrics

- n_samples: 500
- accuracy: None
- f1: None
- bleu: None
- avg_build_tokens: 0.0
- avg_query_tokens: 4101.308
- avg_compiled_evidence_items: 36.758
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
- dense_document_text_mode: external_naive
- dense_query_text_mode: external_naive
- embedding_cache_enabled: True
- embedding_cache_path: outputs/cache/qwen3_embedding.sqlite
- embedding_cache_hits: 186
- embedding_cache_misses: 247052
- embedding_cache_writes: 246450
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
- avg_embedding_tokens: 116790.09
- avg_context_chars: 13869.726
- compiler_prompt_mode: external_naive
- answer_mode: openai_compatible
- answer_model: Qwen/Qwen3-30B-A3B-Instruct-2507
- answer_max_input_tokens: 131072
- answer_max_output_tokens: 16384
- answer_output_format: json_answer
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

- accuracy: 344/500 = 0.688000
- n_valid: 500
- n_invalid: 0
- judge_model: deepseek-v4-flash
- judge_prompt_tokens: 78636
- judge_completion_tokens: 39616
- judge_total_tokens: 118252

## DeepSeek Judge By Type

- knowledge-update: 56/78 = 0.717949
- multi-session: 65/133 = 0.488722
- single-session-assistant: 52/56 = 0.928571
- single-session-preference: 10/30 = 0.333333
- single-session-user: 65/70 = 0.928571
- temporal-reasoning: 96/133 = 0.721805

## Diagnostic Evidence Recall

- note: evidence recall is diagnostic only; method selection is based on judge accuracy.
- overall: 1.000000 over 500 labeled samples

## Comparison

- previous prompt-fixed naive RAG: 323/500 = 0.646000
- v6 route priority: 303/500 = 0.606000
- v7 memory validity: 303/500 = 0.606000
- external-aligned naive RAG vs previous naive RAG: net_correct=+21 (plus=64, minus=43)
- external-aligned naive RAG vs v6: net_correct=+41 (plus=78, minus=37)
- external-aligned naive RAG vs v7: net_correct=+41 (plus=80, minus=39)
- interpretation: aligning with the external clean naive RAG implementation is strongly positive on LongMemEval-S full.
- decision: future LME methods must beat 0.688 DeepSeek judge accuracy.

## Outputs

- predictions: /data/home_new/wujinqi/agent-memory/outputs/formal/stage1_naive_rag_top40_external_lme_s_full_224aa42/predictions.jsonl
- traces: /data/home_new/wujinqi/agent-memory/outputs/formal/stage1_naive_rag_top40_external_lme_s_full_224aa42/traces.jsonl
- metrics: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_naive_rag_top40_external_lme_s_full_224aa42/metrics.json
- manifest: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_naive_rag_top40_external_lme_s_full_224aa42/manifest.json
- deepseek_judge: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_naive_rag_top40_external_lme_s_full_224aa42/deepseek_judge.json
- deepseek_judge_partial: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_naive_rag_top40_external_lme_s_full_224aa42/deepseek_judge.json.partial.jsonl
- offline_evidence_recall: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_naive_rag_top40_external_lme_s_full_224aa42/evidence_recall.json

## Clean Notes

- No gold/reference/target answer, judge output, benchmark label, sample id, qid, or row index is passed into the prediction pipeline.
- Build-stage typed memory is generated only from raw dialogue and visible metadata; it is recorded separately from offline labels and judge outputs.
- Raw context remains available for fallback and diagnosis; build memory records keep source back-links when produced by the current builder.
- Accuracy is intentionally not computed by the prediction runner; any gold or judge metrics must be produced offline after prediction.
- DeepSeek judge and evidence recall were run offline after predictions were written. Judge labels, gold answers, question_type, and record_key must not be consumed by prediction, retrieval, compiler, answer, or verifier code.

## Conclusion

External-aligned strict clean naive RAG top-40 reaches 0.688 LongMemEval-S full accuracy with avg_query_tokens 4101.308 and no build tokens. This is the new LME baseline to beat. The strongest remaining weaknesses are multi-session and preference; temporal-reasoning improves substantially under the external-style date/query/prompt contract.
