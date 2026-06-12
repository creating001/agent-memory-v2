# formal/stage1_agent_memory_v1_lme_s_full_b8f58b3_cold

## Purpose

Stage-1 clean skeleton run: validate raw evidence storage, lexical retrieval, neighbor expansion, evidence compilation, answer generation, trace output, and experiment bookkeeping.

## Scope

- benchmark: longmemeval
- subset: s_cleaned
- experiment_kind: formal
- limit: None
- workers: 8
- input_path: /data/home_new/wujinqi/agent-memory/outputs/prepare_longmemeval_s_cleaned/prediction_input.jsonl
- config_path: /data/home_new/wujinqi/agent-memory/configs/stage1_build_memory_cached.json
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0.0 and max_tokens 16384.

## Git

- inside_work_tree: True
- commit: b8f58b36d808cdb4b6d35929ecc90322abb873d5
- dirty: False
- note: None
- prediction_manifest_dirty: False
- deepseek_judge_git_dirty: True
- deepseek_judge_dirty_note: judge was launched after this experiment directory had been generated, so git status contained only the untracked generated `experiments/formal/` results; prediction code/config commit remained b8f58b36d808cdb4b6d35929ecc90322abb873d5.

## Metrics

- n_samples: 500
- deepseek_judge_accuracy: 0.528
- deepseek_judge_correct: 264
- deepseek_judge_wrong: 236
- deepseek_judge_n_valid: 500
- deepseek_judge_usage_total_tokens: 118369
- deepseek_judge_usage_prompt_tokens: 77604
- deepseek_judge_usage_completion_tokens: 40765
- accuracy: None
- f1: None
- bleu: None
- avg_build_tokens: 80346.246
- avg_query_tokens: 5334.412
- avg_compiled_evidence_items: 13.39
- build_memory_enabled: True
- build_memory_model: Qwen/Qwen3-30B-A3B-Instruct-2507
- build_memory_cache_enabled: True
- build_memory_cache_path: outputs/cache/qwen3_build_memory.sqlite
- build_memory_cache_hits: 0
- build_memory_cache_misses: 3341
- build_memory_cache_writes: 3341
- avg_build_memory_records: 129.662
- avg_active_build_memory_records: 116.492
- avg_memory_hits: 12.082
- avg_memory_source_hits: 11.912
- neighbor_order: hit_priority
- drop_query_stopwords: False
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
- avg_context_chars: 20511.524
- answer_mode: openai_compatible
- answer_model: Qwen/Qwen3-30B-A3B-Instruct-2507
- answer_style: concise
- evidence_order: retrieval
- row_text_mode: full
- max_row_text_chars: 0
- max_memory_records: 10
- route_guidance: True
- temporal_grounding: True
- temporal_hints: False
- enable_broad_list_patterns: False

## DeepSeek Judge By Type

- knowledge-update: 53/78 = 0.6795
- multi-session: 43/133 = 0.3233
- single-session-assistant: 50/56 = 0.8929
- single-session-preference: 8/30 = 0.2667
- single-session-user: 62/70 = 0.8857
- temporal-reasoning: 48/133 = 0.3609

## Outputs

- predictions: /data/home_new/wujinqi/agent-memory/outputs/formal/stage1_agent_memory_v1_lme_s_full_b8f58b3_cold/predictions.jsonl
- traces: /data/home_new/wujinqi/agent-memory/outputs/formal/stage1_agent_memory_v1_lme_s_full_b8f58b3_cold/traces.jsonl
- metrics: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_agent_memory_v1_lme_s_full_b8f58b3_cold/metrics.json
- manifest: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_agent_memory_v1_lme_s_full_b8f58b3_cold/manifest.json
- deepseek_judge: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_agent_memory_v1_lme_s_full_b8f58b3_cold/deepseek_judge.json
- deepseek_judge_partial: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_agent_memory_v1_lme_s_full_b8f58b3_cold/deepseek_judge.json.partial.jsonl

## Clean Notes

- No gold/reference/target answer, judge output, benchmark label, sample id, qid, or row index is passed into the prediction pipeline.
- Build-stage typed memory is generated only from raw dialogue and visible metadata; it is recorded separately from offline labels and judge outputs.
- Raw context remains available for fallback and diagnosis; build memory records keep source back-links when produced by the current builder.
- Accuracy is intentionally not computed by the prediction runner; any gold or judge metrics must be produced offline after prediction.
- DeepSeek judge was run offline after all predictions were written. Judge labels, rationales, gold answers, question_type, and record_key must not be consumed by prediction, retrieval, compiler, answer, or verifier code.

## Conclusion

This cold-build typed-memory skeleton is clean and within token budgets, but the accuracy is far below the target. The main failures are multi-session, temporal-reasoning, and single-session-preference. The next iteration should target general memory management and query-time evidence organization for multi-session aggregation, temporal state/conflict handling, and profile/preference retrieval, with all changes behind explicit config switches for ablation.
