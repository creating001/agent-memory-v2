# stage1_concise_lme_s_20

## Purpose

Stage-1 clean skeleton run: validate raw evidence storage, lexical retrieval, neighbor expansion, evidence compilation, answer generation, trace output, and experiment bookkeeping.

## Scope

- benchmark: longmemeval
- subset: s_cleaned
- experiment_kind: diagnostic
- limit: 20
- input_path: /data/home_new/wujinqi/agent-memory/outputs/prepare_longmemeval_s_cleaned/prediction_input.jsonl
- config_path: /data/home_new/wujinqi/agent-memory/configs/stage1_vllm_answer_concise.json
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0.0 and max_tokens 128.

## Git

- inside_work_tree: True
- commit: d32987dbb9e2075fcd5268c98a75c5352dde7fae
- dirty: True
- note: None

## Metrics

- n_samples: 20
- accuracy: None
- f1: None
- bleu: None
- avg_build_tokens: 0.0
- avg_query_tokens: 2841.85
- avg_compiled_evidence_items: 9.85
- neighbor_order: hit_priority
- drop_query_stopwords: False
- dense_enabled: False
- lexical_protect_top_n: None
- avg_embedding_tokens: 0.0
- avg_context_chars: 11278.6
- answer_mode: openai_compatible
- answer_model: Qwen/Qwen3-30B-A3B-Instruct-2507
- answer_style: concise
- offline_exact: 0.5
- offline_f1: 0.7513194444444445
- offline_bleu_unigram: 0.6910081585081584
- evidence_recall: 1.0

## Outputs

- predictions: /data/home_new/wujinqi/agent-memory/outputs/stage1_concise_lme_s_20/predictions.jsonl
- traces: /data/home_new/wujinqi/agent-memory/outputs/stage1_concise_lme_s_20/traces.jsonl
- metrics: /data/home_new/wujinqi/agent-memory/experiments/stage1_concise_lme_s_20/metrics.json
- manifest: /data/home_new/wujinqi/agent-memory/experiments/stage1_concise_lme_s_20/manifest.json
- offline_lexical_eval: /data/home_new/wujinqi/agent-memory/experiments/stage1_concise_lme_s_20/offline_lexical_eval.json
- evidence_recall: /data/home_new/wujinqi/agent-memory/experiments/stage1_concise_lme_s_20/evidence_recall.json
- deepseek_judge_dry_run: /data/home_new/wujinqi/agent-memory/experiments/stage1_concise_lme_s_20/deepseek_judge_dry_run.json

## Diagnosis

- Method: hit-priority BM25 with concise answer prompt and Qwen3-30B answer model.
- Compared with `stage1_hit_priority_lme_s_20`, exact improves from 0.05 to 0.50, F1 from 0.37087 to 0.75132, and evidence recall stays 20/20.
- Avg query tokens are essentially unchanged: 2833.6 to 2841.85.
- This is the current LongMemEval-S mainline candidate for larger-slice testing; remaining failures include answer grounding issues such as yoga class confusion.

## Clean Notes

- No gold/reference/target answer, judge output, benchmark label, sample id, qid, or row index is passed into the prediction pipeline.
- Raw evidence remains the only factual source; compiled evidence rows keep source_id links.
- Accuracy is intentionally not computed by the prediction runner; any gold or judge metrics must be produced offline after prediction.
