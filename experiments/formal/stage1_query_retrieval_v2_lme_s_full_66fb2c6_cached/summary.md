# formal/stage1_query_retrieval_v2_lme_s_full_66fb2c6_cached

## Purpose

Stage-1 clean skeleton run: validate raw evidence storage, lexical retrieval, neighbor expansion, evidence compilation, answer generation, trace output, and experiment bookkeeping.

## Scope

- benchmark: longmemeval
- subset: s_cleaned
- experiment_kind: formal
- limit: None
- workers: 8
- input_path: /data/home_new/wujinqi/agent-memory/outputs/prepare_longmemeval_s_cleaned/prediction_input.jsonl
- config_path: /data/home_new/wujinqi/agent-memory/configs/stage1_query_retrieval_v2_cached.json
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0.0 and max_tokens 16384.

## Git

- inside_work_tree: True
- commit: 66fb2c6cc159abe5c713fc8dad483a883e0691c2
- dirty: False
- note: None
- prediction_manifest_dirty: False
- deepseek_judge_git_dirty: True
- deepseek_judge_dirty_note: judge was launched after this experiment directory had been generated, so git status contained only the untracked generated `experiments/formal/` results; prediction code/config commit remained 66fb2c6cc159abe5c713fc8dad483a883e0691c2.

## Metrics

- n_samples: 500
- deepseek_judge_accuracy: 0.54
- deepseek_judge_correct: 270
- deepseek_judge_wrong: 230
- deepseek_judge_n_valid: 500
- deepseek_judge_usage_total_tokens: 117677
- deepseek_judge_usage_prompt_tokens: 77890
- deepseek_judge_usage_completion_tokens: 39787
- accuracy: None
- f1: None
- bleu: None
- avg_build_tokens: 0.0
- avg_query_tokens: 5133.492
- avg_compiled_evidence_items: 12.49
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
- avg_context_chars: 19925.042
- answer_mode: openai_compatible
- answer_model: Qwen/Qwen3-30B-A3B-Instruct-2507
- answer_style: concise
- evidence_order: question_overlap
- row_text_mode: full
- max_row_text_chars: 0
- max_memory_records: 10
- route_guidance: True
- temporal_grounding: True
- temporal_hints: True
- enable_broad_list_patterns: False

## DeepSeek Judge By Type

- knowledge-update: 51/78 = 0.6538
- multi-session: 50/133 = 0.3759
- single-session-assistant: 48/56 = 0.8571
- single-session-preference: 7/30 = 0.2333
- single-session-user: 63/70 = 0.9000
- temporal-reasoning: 51/133 = 0.3835

## Comparison To Cold Build V1

- overall: 0.528 -> 0.540
- improved samples: 34
- regressed samples: 28
- net: +6 correct
- likely gain: less noisy multi-session/temporal retrieval and evidence ordering
- likely loss: preference and some knowledge-update answers need better memory state/profile handling, not only lexical cleanup

## Outputs

- predictions: /data/home_new/wujinqi/agent-memory/outputs/formal/stage1_query_retrieval_v2_lme_s_full_66fb2c6_cached/predictions.jsonl
- traces: /data/home_new/wujinqi/agent-memory/outputs/formal/stage1_query_retrieval_v2_lme_s_full_66fb2c6_cached/traces.jsonl
- metrics: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_query_retrieval_v2_lme_s_full_66fb2c6_cached/metrics.json
- manifest: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_query_retrieval_v2_lme_s_full_66fb2c6_cached/manifest.json
- deepseek_judge: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_query_retrieval_v2_lme_s_full_66fb2c6_cached/deepseek_judge.json
- deepseek_judge_partial: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_query_retrieval_v2_lme_s_full_66fb2c6_cached/deepseek_judge.json.partial.jsonl

## Clean Notes

- No gold/reference/target answer, judge output, benchmark label, sample id, qid, or row index is passed into the prediction pipeline.
- Build-stage typed memory is generated only from raw dialogue and visible metadata; it is recorded separately from offline labels and judge outputs.
- Raw context remains available for fallback and diagnosis; build memory records keep source back-links when produced by the current builder.
- Accuracy is intentionally not computed by the prediction runner; any gold or judge metrics must be produced offline after prediction.
- DeepSeek judge was run offline after all predictions were written. Judge labels, rationales, gold answers, question_type, and record_key must not be consumed by prediction, retrieval, compiler, answer, or verifier code.

## Conclusion

This query-side cleanup is clean, cheap, and slightly positive, but it is not enough to reach the target. It should be kept as an ablation data point. The next method should address general memory management: profile/event separation, temporal conflict/state chains, and multi-session evidence aggregation over raw source turns.
