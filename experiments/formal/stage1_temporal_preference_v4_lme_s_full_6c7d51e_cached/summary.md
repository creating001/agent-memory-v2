# formal/stage1_temporal_preference_v4_lme_s_full_6c7d51e_cached

## Purpose

Query-side v4 ablation reusing the v1 cold build cache: evaluate a generic temporal calculation workpad plus personalized recommendation routing on top of v3 typed memory compiler.

## Scope

- benchmark: longmemeval
- subset: s_cleaned
- experiment_kind: formal
- limit: None
- workers: 8
- input_path: /data/home_new/wujinqi/agent-memory/outputs/prepare_longmemeval_s_cleaned/prediction_input.jsonl
- config_path: /data/home_new/wujinqi/agent-memory/configs/stage1_temporal_preference_v4_cached.json
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0.0 and max_tokens 16384.

## Git

- inside_work_tree: True
- commit: 6c7d51e1a73161e0827645d258b595091f1681ef
- dirty: False
- note: None
- prediction_manifest_dirty: False
- deepseek_judge_git_dirty: True
- deepseek_judge_dirty_note: judge was launched after this experiment directory had been generated, so git status contained only the untracked generated `experiments/formal/` results; prediction code/config commit remained 6c7d51e1a73161e0827645d258b595091f1681ef.

## Metrics

- n_samples: 500
- deepseek_judge_accuracy: 0.596
- deepseek_judge_correct: 298
- deepseek_judge_wrong: 202
- deepseek_judge_n_valid: 500
- deepseek_judge_usage_total_tokens: 117190
- deepseek_judge_usage_prompt_tokens: 77891
- deepseek_judge_usage_completion_tokens: 39299
- offline_evidence_recall: 0.978
- offline_evidence_recall_n: 500
- accuracy: None
- f1: None
- bleu: None
- avg_build_tokens: 0.0
- avg_query_tokens: 5760.424
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
- avg_context_chars: 21378.516
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
- enable_broad_list_patterns: False
- enable_recommendation_profile_patterns: True

## DeepSeek Judge By Type

- knowledge-update: 57/78 = 0.7308
- multi-session: 47/133 = 0.3534
- single-session-assistant: 48/56 = 0.8571
- single-session-preference: 11/30 = 0.3667
- single-session-user: 61/70 = 0.8714
- temporal-reasoning: 74/133 = 0.5564

## Comparison

- v1 cold build: 0.528
- v2 query retrieval cleanup: 0.540
- v3 typed memory compiler: 0.558
- v4 temporal/preference query ablation: 0.596
- v4 vs v3: 34 improved, 15 regressed, +19 net correct
- v4 vs v1: 55 improved, 21 regressed, +34 net correct
- v4 vs v3 net by type: temporal-reasoning +23, single-session-preference +3, knowledge-update 0, single-session-user -1, single-session-assistant -2, multi-session -4.
- likely gain: temporal calculation workpad helps answer elapsed-time and event-order questions; recommendation routing makes some personalized recommendation questions use profile/preference evidence instead of abstaining.
- remaining issue: avg query tokens 5760.424 is close to the 6K mainline budget, and multi-session regressed; the workpad should be gated or compacted before becoming the long-term default.

## Outputs

- predictions: /data/home_new/wujinqi/agent-memory/outputs/formal/stage1_temporal_preference_v4_lme_s_full_6c7d51e_cached/predictions.jsonl
- traces: /data/home_new/wujinqi/agent-memory/outputs/formal/stage1_temporal_preference_v4_lme_s_full_6c7d51e_cached/traces.jsonl
- metrics: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_temporal_preference_v4_lme_s_full_6c7d51e_cached/metrics.json
- manifest: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_temporal_preference_v4_lme_s_full_6c7d51e_cached/manifest.json
- deepseek_judge: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_temporal_preference_v4_lme_s_full_6c7d51e_cached/deepseek_judge.json
- deepseek_judge_partial: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_temporal_preference_v4_lme_s_full_6c7d51e_cached/deepseek_judge.json.partial.jsonl
- offline_evidence_recall: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_temporal_preference_v4_lme_s_full_6c7d51e_cached/evidence_recall.json

## Clean Notes

- No gold/reference/target answer, judge output, benchmark label, sample id, qid, or row index is passed into the prediction pipeline.
- Build-stage typed memory is generated only from raw dialogue and visible metadata; it is recorded separately from offline labels and judge outputs.
- Raw context remains available for fallback and diagnosis; build memory records keep source back-links when produced by the current builder.
- Accuracy is intentionally not computed by the prediction runner; any gold or judge metrics must be produced offline after prediction.
- DeepSeek judge and evidence recall were run offline after predictions were written. Judge labels, gold answers, question_type, and record_key must not be consumed by prediction, retrieval, compiler, answer, or verifier code.

## Conclusion

v4 is a clean positive query-side ablation and is the current best LME result. It should not end the method search: the temporal workpad is useful but token-heavy and slightly hurts multi-session, so the next step should compact/gate temporal reasoning and move to stronger build-stage memory management for profile/event/state validity.
