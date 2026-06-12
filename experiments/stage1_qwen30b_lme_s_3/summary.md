# stage1_qwen30b_lme_s_3

## Purpose

Stage-1 clean skeleton run: validate raw evidence storage, lexical retrieval, neighbor expansion, evidence compilation, answer generation, trace output, and experiment bookkeeping.

## Scope

- benchmark: longmemeval
- subset: s_cleaned
- experiment_kind: diagnostic
- limit: 3
- input_path: /data/home_new/wujinqi/agent-memory/outputs/prepare_longmemeval_s_cleaned/prediction_input.jsonl
- config_path: /data/home_new/wujinqi/agent-memory/configs/stage1_vllm_answer.json
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0.0 and max_tokens 256.

## Git

- inside_work_tree: True
- commit: 7262de64500092804a0b5b5f76d16341aa5ed763
- dirty: True
- note: None

## Metrics

- n_samples: 3
- accuracy: None
- f1: None
- bleu: None
- avg_build_tokens: 0.0
- avg_query_tokens: 2798.6666666666665
- avg_compiled_evidence_items: 10.0
- avg_context_chars: 10923.0
- answer_mode: openai_compatible
- answer_model: Qwen/Qwen3-30B-A3B-Instruct-2507
- offline_exact: 0.0
- offline_f1: 0.11111111111111112
- offline_bleu_unigram: 0.06666666666666667
- evidence_recall: 0.3333333333333333

## Outputs

- predictions: /data/home_new/wujinqi/agent-memory/outputs/stage1_qwen30b_lme_s_3/predictions.jsonl
- traces: /data/home_new/wujinqi/agent-memory/outputs/stage1_qwen30b_lme_s_3/traces.jsonl
- metrics: /data/home_new/wujinqi/agent-memory/experiments/stage1_qwen30b_lme_s_3/metrics.json
- manifest: /data/home_new/wujinqi/agent-memory/experiments/stage1_qwen30b_lme_s_3/manifest.json
- offline_lexical_eval: /data/home_new/wujinqi/agent-memory/experiments/stage1_qwen30b_lme_s_3/offline_lexical_eval.json
- evidence_recall: /data/home_new/wujinqi/agent-memory/experiments/stage1_qwen30b_lme_s_3/evidence_recall.json
- deepseek_judge_dry_run: /data/home_new/wujinqi/agent-memory/experiments/stage1_qwen30b_lme_s_3/deepseek_judge_dry_run.json

## Diagnosis

- BM25 plus neighbor expansion retrieves at least one labeled answer session for 1/3 examples.
- The answer model returns unavailable for two of three samples, so immediate gain should come from recall and context construction before answer prompt complexity.
- This run is diagnostic only; the sample size is too small for benchmark claims.

## Clean Notes

- No gold/reference/target answer, judge output, benchmark label, sample id, qid, or row index is passed into the prediction pipeline.
- Raw evidence remains the only factual source; compiled evidence rows keep source_id links.
- Accuracy is intentionally not computed by the prediction runner; any gold or judge metrics must be produced offline after prediction.
