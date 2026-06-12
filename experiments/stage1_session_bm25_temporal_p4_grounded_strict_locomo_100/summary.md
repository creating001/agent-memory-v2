# stage1_session_bm25_temporal_p4_grounded_strict_locomo_100

## Purpose

Stage-1 clean skeleton run: validate raw evidence storage, lexical retrieval, neighbor expansion, evidence compilation, answer generation, trace output, and experiment bookkeeping.

## Scope

- benchmark: locomo
- subset: non_adversarial
- experiment_kind: focused_ablation
- limit: 100
- input_path: /data/home_new/wujinqi/agent-memory/outputs/prepare_locomo_non_adversarial/prediction_input.jsonl
- config_path: /data/home_new/wujinqi/agent-memory/configs/stage1_vllm_dense_k12_concise_session_bm25_temporal_p4_grounded_strict.json
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0.0 and max_tokens 128.

## Git

- inside_work_tree: True
- commit: 4011022ca76405a1c1405772384c7551fd93191f
- dirty: True
- note: None

## Metrics

- n_samples: 100
- accuracy: None
- f1: None
- bleu: None
- avg_build_tokens: 0.0
- avg_query_tokens: 2832.96
- avg_compiled_evidence_items: 34.13
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
- session_bm25_applied_count: 41
- session_bm25_applied_rate: 0.41
- avg_embedding_tokens: 13489.47
- avg_context_chars: 9317.68
- answer_mode: openai_compatible
- answer_model: Qwen/Qwen3-30B-A3B-Instruct-2507
- answer_style: concise
- temporal_grounding: True

## Outputs

- predictions: /data/home_new/wujinqi/agent-memory/outputs/stage1_session_bm25_temporal_p4_grounded_strict_locomo_100/predictions.jsonl
- traces: /data/home_new/wujinqi/agent-memory/outputs/stage1_session_bm25_temporal_p4_grounded_strict_locomo_100/traces.jsonl
- metrics: /data/home_new/wujinqi/agent-memory/experiments/stage1_session_bm25_temporal_p4_grounded_strict_locomo_100/metrics.json
- manifest: /data/home_new/wujinqi/agent-memory/experiments/stage1_session_bm25_temporal_p4_grounded_strict_locomo_100/manifest.json

## Offline Evaluation

- offline_lexical_eval: /data/home_new/wujinqi/agent-memory/experiments/stage1_session_bm25_temporal_p4_grounded_strict_locomo_100/offline_lexical_eval.json
- evidence_recall: /data/home_new/wujinqi/agent-memory/experiments/stage1_session_bm25_temporal_p4_grounded_strict_locomo_100/evidence_recall.json
- judge_dry_run: /data/home_new/wujinqi/agent-memory/experiments/stage1_session_bm25_temporal_p4_grounded_strict_locomo_100/deepseek_judge_dry_run.json
- exact_match: 0.09
- token_f1: 0.3938473303083172
- bleu_unigram: 0.329455353419273
- evidence_recall: 0.7857142857142857 over 98 evidence-labeled rows
- baseline_reference: stage1_session_bm25_temporal_p4_grounded_locomo_100
- baseline_token_f1: 0.30323744092503646
- baseline_evidence_recall: 0.7857142857142857
- dense_baseline_reference: stage1_dense_k12_concise_locomo_100
- dense_baseline_token_f1: 0.27571269917466834
- dense_baseline_evidence_recall: 0.7653061224489796
- judge_status: dry-run only; DEEPSEEK_API_KEY was not set in the shell environment.

## Clean Notes

- No gold/reference/target answer, judge output, benchmark label, sample id, qid, or row index is passed into the prediction pipeline.
- Raw evidence remains the only factual source; compiled evidence rows keep source_id links.
- Accuracy is intentionally not computed by the prediction runner; any gold or judge metrics must be produced offline after prediction.
