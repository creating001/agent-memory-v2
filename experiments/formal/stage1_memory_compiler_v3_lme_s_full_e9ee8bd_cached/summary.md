# formal/stage1_memory_compiler_v3_lme_s_full_e9ee8bd_cached

## Purpose

Stage-1 clean skeleton run: validate raw evidence storage, lexical retrieval, neighbor expansion, evidence compilation, answer generation, trace output, and experiment bookkeeping.

## Scope

- benchmark: longmemeval
- subset: s_cleaned
- experiment_kind: formal
- limit: None
- workers: 8
- input_path: /data/home_new/wujinqi/agent-memory/outputs/prepare_longmemeval_s_cleaned/prediction_input.jsonl
- config_path: /data/home_new/wujinqi/agent-memory/configs/stage1_memory_compiler_v3_cached.json
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0.0 and max_tokens 16384.

## Git

- inside_work_tree: True
- commit: e9ee8bd117c39b222ff7c7dc4be6d69271690621
- dirty: False
- note: None
- prediction_manifest_dirty: False
- deepseek_judge_git_dirty: True
- deepseek_judge_dirty_note: judge was launched after this experiment directory had been generated, so git status contained only the untracked generated `experiments/formal/` results; prediction code/config commit remained e9ee8bd117c39b222ff7c7dc4be6d69271690621.

## Metrics

- n_samples: 500
- deepseek_judge_accuracy: 0.558
- deepseek_judge_correct: 279
- deepseek_judge_wrong: 221
- deepseek_judge_n_valid: 500
- deepseek_judge_usage_total_tokens: 116961
- deepseek_judge_usage_prompt_tokens: 77559
- deepseek_judge_usage_completion_tokens: 39402
- accuracy: None
- f1: None
- bleu: None
- avg_build_tokens: 0.0
- avg_query_tokens: 5274.212
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
- avg_context_chars: 20335.074
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
- enable_broad_list_patterns: False

## DeepSeek Judge By Type

- knowledge-update: 57/78 = 0.7308
- multi-session: 51/133 = 0.3835
- single-session-assistant: 50/56 = 0.8929
- single-session-preference: 8/30 = 0.2667
- single-session-user: 62/70 = 0.8857
- temporal-reasoning: 51/133 = 0.3835

## Comparison

- v1 cold build: 0.528
- v2 query retrieval cleanup: 0.540
- v3 typed memory compiler: 0.558
- v3 vs v2: 23 improved, 14 regressed, +9 net correct
- v3 vs v1: 37 improved, 22 regressed, +15 net correct
- likely gain: typed memory sections and memory ordering help knowledge-update and some multi-session questions.
- remaining gap: temporal and multi-session are still below 40%; single-session-preference remains very weak.

## Outputs

- predictions: /data/home_new/wujinqi/agent-memory/outputs/formal/stage1_memory_compiler_v3_lme_s_full_e9ee8bd_cached/predictions.jsonl
- traces: /data/home_new/wujinqi/agent-memory/outputs/formal/stage1_memory_compiler_v3_lme_s_full_e9ee8bd_cached/traces.jsonl
- metrics: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_memory_compiler_v3_lme_s_full_e9ee8bd_cached/metrics.json
- manifest: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_memory_compiler_v3_lme_s_full_e9ee8bd_cached/manifest.json
- deepseek_judge: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_memory_compiler_v3_lme_s_full_e9ee8bd_cached/deepseek_judge.json
- deepseek_judge_partial: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_memory_compiler_v3_lme_s_full_e9ee8bd_cached/deepseek_judge.json.partial.jsonl

## Clean Notes

- No gold/reference/target answer, judge output, benchmark label, sample id, qid, or row index is passed into the prediction pipeline.
- Build-stage typed memory is generated only from raw dialogue and visible metadata; it is recorded separately from offline labels and judge outputs.
- Raw context remains available for fallback and diagnosis; build memory records keep source back-links when produced by the current builder.
- Accuracy is intentionally not computed by the prediction runner; any gold or judge metrics must be produced offline after prediction.
- DeepSeek judge was run offline after all predictions were written. Judge labels, rationales, gold answers, question_type, and record_key must not be consumed by prediction, retrieval, compiler, answer, or verifier code.

## Conclusion

The typed memory compiler is a clean positive ablation and should be kept as the current query-side best. It is still far from the target, so the next main improvement should move beyond formatting into stronger memory management: profile/event separation, temporal validity/conflict chains, and multi-session aggregation grounded back to raw source turns.
