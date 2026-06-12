# stage1_qwen30b_locomo_3

## Purpose

Stage-1 clean skeleton run: validate raw evidence storage, lexical retrieval, neighbor expansion, evidence compilation, answer generation, trace output, and experiment bookkeeping.

## Scope

- benchmark: locomo
- subset: non-adversarial
- experiment_kind: diagnostic
- limit: 3
- input_path: /data/home_new/wujinqi/agent-memory/outputs/prepare_locomo_non_adversarial/prediction_input.jsonl
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
- avg_query_tokens: 1787.3333333333333
- avg_compiled_evidence_items: 20.0
- avg_context_chars: 5871.666666666667
- answer_mode: openai_compatible
- answer_model: Qwen/Qwen3-30B-A3B-Instruct-2507
- offline_exact: 0.0
- offline_f1: 0.006472491909385113
- offline_bleu_unigram: 0.0033333333333333335
- evidence_recall: 0.0

## Outputs

- predictions: /data/home_new/wujinqi/agent-memory/outputs/stage1_qwen30b_locomo_3/predictions.jsonl
- traces: /data/home_new/wujinqi/agent-memory/outputs/stage1_qwen30b_locomo_3/traces.jsonl
- metrics: /data/home_new/wujinqi/agent-memory/experiments/stage1_qwen30b_locomo_3/metrics.json
- manifest: /data/home_new/wujinqi/agent-memory/experiments/stage1_qwen30b_locomo_3/manifest.json
- offline_lexical_eval: /data/home_new/wujinqi/agent-memory/experiments/stage1_qwen30b_locomo_3/offline_lexical_eval.json
- evidence_recall: /data/home_new/wujinqi/agent-memory/experiments/stage1_qwen30b_locomo_3/evidence_recall.json
- deepseek_judge_dry_run: /data/home_new/wujinqi/agent-memory/experiments/stage1_qwen30b_locomo_3/deepseek_judge_dry_run.json

## Diagnosis

- BM25 plus neighbor expansion misses all labeled evidence turns in the first three non-adversarial LoCoMo examples.
- The output quality is dominated by retrieval failure, not by answerer integration.
- This run is diagnostic only; the sample size is too small for benchmark claims.

## Clean Notes

- No gold/reference/target answer, judge output, benchmark label, sample id, qid, or row index is passed into the prediction pipeline.
- Raw evidence remains the only factual source; compiled evidence rows keep source_id links.
- Accuracy is intentionally not computed by the prediction runner; any gold or judge metrics must be produced offline after prediction.
