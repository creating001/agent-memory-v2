# stage1_dense_protect2_lme_s_3

## Purpose

Stage-1 clean skeleton run: validate raw evidence storage, lexical retrieval, neighbor expansion, evidence compilation, answer generation, trace output, and experiment bookkeeping.

## Scope

- benchmark: longmemeval
- subset: s_cleaned
- experiment_kind: diagnostic
- limit: 3
- input_path: /data/home_new/wujinqi/agent-memory/outputs/prepare_longmemeval_s_cleaned/prediction_input.jsonl
- config_path: /data/home_new/wujinqi/agent-memory/configs/stage1_vllm_dense_hybrid_protect2.json
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0.0 and max_tokens 256.

## Git

- inside_work_tree: True
- commit: c78479d33bb155df3eb7742900b493baddaeccc0
- dirty: True
- note: None

## Metrics

- n_samples: 3
- accuracy: None
- f1: None
- bleu: None
- avg_build_tokens: 0.0
- avg_query_tokens: 2870.3333333333335
- avg_compiled_evidence_items: 9.666666666666666
- neighbor_order: hit_priority
- drop_query_stopwords: False
- dense_enabled: True
- lexical_protect_top_n: 2
- avg_embedding_tokens: 103881.66666666667
- avg_context_chars: 11778.0
- answer_mode: openai_compatible
- answer_model: Qwen/Qwen3-30B-A3B-Instruct-2507
- offline_exact: 0.0
- offline_f1: 0.3844155844155845
- offline_bleu_unigram: 0.25
- evidence_recall: 1.0
- avg_embedding_tokens: 103881.66666666667

## Outputs

- predictions: /data/home_new/wujinqi/agent-memory/outputs/stage1_dense_protect2_lme_s_3/predictions.jsonl
- traces: /data/home_new/wujinqi/agent-memory/outputs/stage1_dense_protect2_lme_s_3/traces.jsonl
- metrics: /data/home_new/wujinqi/agent-memory/experiments/stage1_dense_protect2_lme_s_3/metrics.json
- manifest: /data/home_new/wujinqi/agent-memory/experiments/stage1_dense_protect2_lme_s_3/manifest.json
- offline_lexical_eval: /data/home_new/wujinqi/agent-memory/experiments/stage1_dense_protect2_lme_s_3/offline_lexical_eval.json
- evidence_recall: /data/home_new/wujinqi/agent-memory/experiments/stage1_dense_protect2_lme_s_3/evidence_recall.json
- deepseek_judge_dry_run: /data/home_new/wujinqi/agent-memory/experiments/stage1_dense_protect2_lme_s_3/deepseek_judge_dry_run.json

## Diagnosis

- Change: dense hybrid plus `lexical_protect_top_n=2`, preserving BM25 top nuclei before fused dense candidates.
- Compared with equal RRF, offline F1 recovers from 0.32381 to 0.38442 while evidence recall stays 3/3.
- Compared with hit-priority BM25, answer quality is unchanged but embedding cost is high.
- Dense should be gated or cached before any full LongMemEval run.

## Clean Notes

- No gold/reference/target answer, judge output, benchmark label, sample id, qid, or row index is passed into the prediction pipeline.
- Raw evidence remains the only factual source; compiled evidence rows keep source_id links.
- Accuracy is intentionally not computed by the prediction runner; any gold or judge metrics must be produced offline after prediction.
