# stage1_dense_protect2_locomo_20

## Purpose

Stage-1 clean skeleton run: validate raw evidence storage, lexical retrieval, neighbor expansion, evidence compilation, answer generation, trace output, and experiment bookkeeping.

## Scope

- benchmark: locomo
- subset: non-adversarial
- experiment_kind: diagnostic
- limit: 20
- input_path: /data/home_new/wujinqi/agent-memory/outputs/prepare_locomo_non_adversarial/prediction_input.jsonl
- config_path: /data/home_new/wujinqi/agent-memory/configs/stage1_vllm_dense_hybrid_protect2.json
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0.0 and max_tokens 256.

## Git

- inside_work_tree: True
- commit: 4d3c56abb82347b19c612dc13ea443b07164207b
- dirty: False
- note: None

## Metrics

- n_samples: 20
- accuracy: None
- f1: None
- bleu: None
- avg_build_tokens: 0.0
- avg_query_tokens: 1647.25
- avg_compiled_evidence_items: 19.8
- neighbor_order: hit_priority
- drop_query_stopwords: False
- dense_enabled: True
- lexical_protect_top_n: 2
- avg_embedding_tokens: 13489.55
- avg_context_chars: 5282.8
- answer_mode: openai_compatible
- answer_model: Qwen/Qwen3-30B-A3B-Instruct-2507
- offline_exact: 0.0
- offline_f1: 0.11995047751106505
- offline_bleu_unigram: 0.07782635632864467
- evidence_recall: 0.65
- avg_embedding_tokens: 13489.55

## Outputs

- predictions: /data/home_new/wujinqi/agent-memory/outputs/stage1_dense_protect2_locomo_20/predictions.jsonl
- traces: /data/home_new/wujinqi/agent-memory/outputs/stage1_dense_protect2_locomo_20/traces.jsonl
- metrics: /data/home_new/wujinqi/agent-memory/experiments/stage1_dense_protect2_locomo_20/metrics.json
- manifest: /data/home_new/wujinqi/agent-memory/experiments/stage1_dense_protect2_locomo_20/manifest.json
- offline_lexical_eval: /data/home_new/wujinqi/agent-memory/experiments/stage1_dense_protect2_locomo_20/offline_lexical_eval.json
- evidence_recall: /data/home_new/wujinqi/agent-memory/experiments/stage1_dense_protect2_locomo_20/evidence_recall.json
- deepseek_judge_dry_run: /data/home_new/wujinqi/agent-memory/experiments/stage1_dense_protect2_locomo_20/deepseek_judge_dry_run.json

## Diagnosis

- Method: dense hybrid retrieval with lexical top-2 nucleus protection, Qwen3-Embedding-0.6B, and Qwen3-30B answer model.
- Evidence recall is 13/20 overall: category 1 is weakest at 3/8, category 2 is 8/10, category 3 is 2/2.
- Several answers are semantically close but lexical metrics undercount them; true accuracy needs the offline DeepSeek judge once `DEEPSEEK_API_KEY` is available in the environment.
- Next retrieval work should target LoCoMo category 1 single-hop/profile-style misses and temporal normalization, not larger context windows.

## Clean Notes

- No gold/reference/target answer, judge output, benchmark label, sample id, qid, or row index is passed into the prediction pipeline.
- Raw evidence remains the only factual source; compiled evidence rows keep source_id links.
- Accuracy is intentionally not computed by the prediction runner; any gold or judge metrics must be produced offline after prediction.
