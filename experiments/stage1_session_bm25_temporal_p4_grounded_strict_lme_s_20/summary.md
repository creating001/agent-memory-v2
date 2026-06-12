# stage1_session_bm25_temporal_p4_grounded_strict_lme_s_20

## Purpose

Stage-1 clean skeleton run: validate raw evidence storage, lexical retrieval, neighbor expansion, evidence compilation, answer generation, trace output, and experiment bookkeeping.

## Scope

- benchmark: longmemeval
- subset: s_cleaned
- experiment_kind: diagnostic
- limit: 20
- input_path: /data/home_new/wujinqi/agent-memory/outputs/prepare_longmemeval_s_cleaned/prediction_input.jsonl
- config_path: /data/home_new/wujinqi/agent-memory/configs/stage1_vllm_dense_k12_concise_session_bm25_temporal_p4_grounded_strict.json
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0.0 and max_tokens 128.

## Git

- inside_work_tree: True
- commit: 70c673a16d6327a985251c49d314e9b7a1b7863d
- dirty: False
- note: None

## Metrics

- n_samples: 20
- accuracy: None
- f1: None
- bleu: None
- avg_build_tokens: 0.0
- avg_query_tokens: 4299.8
- avg_compiled_evidence_items: 14.75
- neighbor_order: hit_priority
- drop_query_stopwords: False
- dense_enabled: True
- lexical_protect_top_n: 2
- session_bm25_enabled: True
- session_bm25_top_k: 8
- session_anchor_top_k: 2
- session_max_anchor_hits: 12
- session_protect_turn_hits: 4
- session_enabled_route_signals: ['temporal', 'recent_or_current']
- session_enabled_information_needs: None
- session_enabled_query_patterns: ['\\b20\\d{2}\\b', '\\b(?:january|february|march|april|june|july|august|september|october|november|december)\\b', '\\bmay\\s+20\\d{2}\\b']
- session_bm25_applied_count: 4
- session_bm25_applied_rate: 0.2
- avg_embedding_tokens: 104198.55
- avg_context_chars: 17520.25
- answer_mode: openai_compatible
- answer_model: Qwen/Qwen3-30B-A3B-Instruct-2507
- answer_style: concise
- temporal_grounding: True

## Outputs

- predictions: /data/home_new/wujinqi/agent-memory/outputs/stage1_session_bm25_temporal_p4_grounded_strict_lme_s_20/predictions.jsonl
- traces: /data/home_new/wujinqi/agent-memory/outputs/stage1_session_bm25_temporal_p4_grounded_strict_lme_s_20/traces.jsonl
- metrics: /data/home_new/wujinqi/agent-memory/experiments/stage1_session_bm25_temporal_p4_grounded_strict_lme_s_20/metrics.json
- manifest: /data/home_new/wujinqi/agent-memory/experiments/stage1_session_bm25_temporal_p4_grounded_strict_lme_s_20/manifest.json

## Offline Evaluation

- offline_lexical_eval: /data/home_new/wujinqi/agent-memory/experiments/stage1_session_bm25_temporal_p4_grounded_strict_lme_s_20/offline_lexical_eval.json
- evidence_recall: /data/home_new/wujinqi/agent-memory/experiments/stage1_session_bm25_temporal_p4_grounded_strict_lme_s_20/evidence_recall.json
- exact_match: 0.7
- token_f1: 0.8912301587301588
- bleu_unigram: 0.854469696969697
- evidence_recall: 1.0 over 20 evidence-labeled rows
- baseline_reference: stage1_concise_lme_s_20
- baseline_exact_match: 0.5
- baseline_token_f1: 0.7513194444444445
- baseline_evidence_recall: 1.0
- cost_note: expensive diagnostic; avg_embedding_tokens is 104198.55 per sample.
- judge_status: not run; DEEPSEEK_API_KEY was not set in the shell environment.

## Clean Notes

- No gold/reference/target answer, judge output, benchmark label, sample id, qid, or row index is passed into the prediction pipeline.
- Raw evidence remains the only factual source; compiled evidence rows keep source_id links.
- Accuracy is intentionally not computed by the prediction runner; any gold or judge metrics must be produced offline after prediction.
