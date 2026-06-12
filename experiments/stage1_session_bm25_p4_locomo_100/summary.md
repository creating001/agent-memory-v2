# stage1_session_bm25_p4_locomo_100

## Purpose

Stage-1 clean skeleton run: validate raw evidence storage, lexical retrieval, neighbor expansion, evidence compilation, answer generation, trace output, and experiment bookkeeping.

## Scope

- benchmark: locomo
- subset: non_adversarial
- experiment_kind: focused_ablation
- limit: 100
- input_path: /data/home_new/wujinqi/agent-memory/outputs/prepare_locomo_non_adversarial/prediction_input.jsonl
- config_path: /data/home_new/wujinqi/agent-memory/configs/stage1_vllm_dense_k12_concise_session_bm25_p4.json
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0.0 and max_tokens 128.

## Git

- inside_work_tree: True
- commit: db0d97069bddc90a12ad40d12743f2ddc3253c3f
- dirty: True
- note: None

## Metrics

- n_samples: 100
- accuracy: None
- f1: None
- bleu: None
- avg_build_tokens: 0.0
- avg_query_tokens: 2924.36
- avg_compiled_evidence_items: 35.99
- neighbor_order: hit_priority
- drop_query_stopwords: False
- dense_enabled: True
- lexical_protect_top_n: 2
- session_bm25_enabled: True
- session_bm25_top_k: 8
- session_anchor_top_k: 2
- session_max_anchor_hits: 12
- session_protect_turn_hits: 4
- avg_embedding_tokens: 13489.47
- avg_context_chars: 9465.53
- answer_mode: openai_compatible
- answer_model: Qwen/Qwen3-30B-A3B-Instruct-2507
- answer_style: concise
- temporal_grounding: False

## Outputs

- predictions: /data/home_new/wujinqi/agent-memory/outputs/stage1_session_bm25_p4_locomo_100/predictions.jsonl
- traces: /data/home_new/wujinqi/agent-memory/outputs/stage1_session_bm25_p4_locomo_100/traces.jsonl
- metrics: /data/home_new/wujinqi/agent-memory/experiments/stage1_session_bm25_p4_locomo_100/metrics.json
- manifest: /data/home_new/wujinqi/agent-memory/experiments/stage1_session_bm25_p4_locomo_100/manifest.json

## Offline Evaluation

- offline_lexical_eval: /data/home_new/wujinqi/agent-memory/experiments/stage1_session_bm25_p4_locomo_100/offline_lexical_eval.json
- evidence_recall: /data/home_new/wujinqi/agent-memory/experiments/stage1_session_bm25_p4_locomo_100/evidence_recall.json
- exact_match: 0.03
- token_f1: 0.26673298976993887
- bleu_unigram: 0.20502075656566504
- evidence_recall: 0.7244897959183674 over 98 evidence-labeled rows
- baseline_reference: stage1_dense_k12_concise_locomo_100
- baseline_token_f1: 0.27571269917466834
- baseline_evidence_recall: 0.7653061224489796
- judge_status: not run; DEEPSEEK_API_KEY was not set in the shell environment.

## Clean Notes

- No gold/reference/target answer, judge output, benchmark label, sample id, qid, or row index is passed into the prediction pipeline.
- Raw evidence remains the only factual source; compiled evidence rows keep source_id links.
- Accuracy is intentionally not computed by the prediction runner; any gold or judge metrics must be produced offline after prediction.
