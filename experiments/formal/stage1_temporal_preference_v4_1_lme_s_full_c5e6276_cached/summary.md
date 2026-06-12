# formal/stage1_temporal_preference_v4_1_lme_s_full_c5e6276_cached

## Purpose

Query-side v4.1 cost/compactness ablation reusing the v1 cold build cache: evaluate whether gating temporal workpad to explicit duration/order/ago questions preserves v4 accuracy while reducing query tokens.

## Scope

- benchmark: longmemeval
- subset: s_cleaned
- experiment_kind: formal
- limit: None
- workers: 8
- input_path: /data/home_new/wujinqi/agent-memory/outputs/prepare_longmemeval_s_cleaned/prediction_input.jsonl
- config_path: /data/home_new/wujinqi/agent-memory/configs/stage1_temporal_preference_v4_1_cached.json
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0.0 and max_tokens 16384.

## Git

- inside_work_tree: True
- commit: c5e6276f67c3a730b778ec0d2550fa1c6579b46c
- dirty: False
- note: None
- prediction_manifest_dirty: False
- deepseek_judge_git_dirty: True
- deepseek_judge_dirty_note: judge was launched after this experiment directory had been generated, so git status contained only the untracked generated `experiments/formal/` results; prediction code/config commit remained c5e6276f67c3a730b778ec0d2550fa1c6579b46c.

## Metrics

- n_samples: 500
- deepseek_judge_accuracy: 0.584
- deepseek_judge_correct: 292
- deepseek_judge_wrong: 208
- deepseek_judge_n_valid: 500
- deepseek_judge_usage_total_tokens: 114572
- deepseek_judge_usage_prompt_tokens: 77951
- deepseek_judge_usage_completion_tokens: 36621
- offline_evidence_recall: 0.978
- offline_evidence_recall_n: 500
- accuracy: None
- f1: None
- bleu: None
- avg_build_tokens: 0.0
- avg_query_tokens: 5468.818
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
- avg_context_chars: 20801.958
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
- temporal_workpad_scope: calculation_route
- temporal_workpad_max_rows: 6
- temporal_workpad_max_pairs: 8
- enable_broad_list_patterns: False
- enable_recommendation_profile_patterns: True

## DeepSeek Judge By Type

- knowledge-update: 55/78 = 0.7051
- multi-session: 47/133 = 0.3534
- single-session-assistant: 46/56 = 0.8214
- single-session-preference: 9/30 = 0.3000
- single-session-user: 62/70 = 0.8857
- temporal-reasoning: 73/133 = 0.5489

## Comparison

- v3 typed memory compiler: 0.558
- v4 temporal/preference query ablation: 0.596
- v4.1 compact temporal workpad: 0.584
- v4.1 vs v4: 10 improved, 16 regressed, -6 net correct
- v4.1 vs v3: 29 improved, 16 regressed, +13 net correct
- cost effect: avg query tokens dropped from v4 5760.424 to 5468.818, and workpad prompts dropped from 198 to 120.
- conclusion: compact gating saves tokens but loses accuracy; v4 remains the current LME mainline best.

## Outputs

- predictions: /data/home_new/wujinqi/agent-memory/outputs/formal/stage1_temporal_preference_v4_1_lme_s_full_c5e6276_cached/predictions.jsonl
- traces: /data/home_new/wujinqi/agent-memory/outputs/formal/stage1_temporal_preference_v4_1_lme_s_full_c5e6276_cached/traces.jsonl
- metrics: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_temporal_preference_v4_1_lme_s_full_c5e6276_cached/metrics.json
- manifest: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_temporal_preference_v4_1_lme_s_full_c5e6276_cached/manifest.json
- deepseek_judge: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_temporal_preference_v4_1_lme_s_full_c5e6276_cached/deepseek_judge.json
- deepseek_judge_partial: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_temporal_preference_v4_1_lme_s_full_c5e6276_cached/deepseek_judge.json.partial.jsonl
- offline_evidence_recall: /data/home_new/wujinqi/agent-memory/experiments/formal/stage1_temporal_preference_v4_1_lme_s_full_c5e6276_cached/evidence_recall.json

## Clean Notes

- No gold/reference/target answer, judge output, benchmark label, sample id, qid, or row index is passed into the prediction pipeline.
- Build-stage typed memory is generated only from raw dialogue and visible metadata; it is recorded separately from offline labels and judge outputs.
- Raw context remains available for fallback and diagnosis; build memory records keep source back-links when produced by the current builder.
- Accuracy is intentionally not computed by the prediction runner; any gold or judge metrics must be produced offline after prediction.
- DeepSeek judge and evidence recall were run offline after predictions were written. Judge labels, gold answers, question_type, and record_key must not be consumed by prediction, retrieval, compiler, answer, or verifier code.

## Conclusion

v4.1 is a clean but negative accuracy ablation. It is useful evidence that the full v4 workpad carries real signal beyond obvious duration/order wording. Keep v4 as best, and move the next major gain to build-stage memory management rather than further shrinking the workpad.
