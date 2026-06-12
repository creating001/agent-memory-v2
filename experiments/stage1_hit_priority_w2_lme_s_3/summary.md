# stage1_hit_priority_w2_lme_s_3

## Purpose

Stage-1 clean skeleton run: validate raw evidence storage, lexical retrieval, neighbor expansion, evidence compilation, answer generation, trace output, and experiment bookkeeping.

## Scope

- benchmark: longmemeval
- subset: s_cleaned
- experiment_kind: diagnostic
- limit: 3
- input_path: /data/home_new/wujinqi/agent-memory/outputs/prepare_longmemeval_s_cleaned/prediction_input.jsonl
- config_path: /data/home_new/wujinqi/agent-memory/configs/stage1_vllm_hit_priority_w2.json
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0.0 and max_tokens 256.

## Git

- inside_work_tree: True
- commit: 3611e5a346b9a8941683c41eb7ef18cda12f9110
- dirty: True
- note: None

## Metrics

- n_samples: 3
- accuracy: None
- f1: None
- bleu: None
- avg_build_tokens: 0.0
- avg_query_tokens: 3240.6666666666665
- avg_compiled_evidence_items: 11.0
- neighbor_order: hit_priority
- avg_context_chars: 12947.0
- answer_mode: openai_compatible
- answer_model: Qwen/Qwen3-30B-A3B-Instruct-2507
- offline_exact: 0.0
- offline_f1: 0.3844155844155845
- offline_bleu_unigram: 0.25
- evidence_recall: 1.0

## Outputs

- predictions: /data/home_new/wujinqi/agent-memory/outputs/stage1_hit_priority_w2_lme_s_3/predictions.jsonl
- traces: /data/home_new/wujinqi/agent-memory/outputs/stage1_hit_priority_w2_lme_s_3/traces.jsonl
- metrics: /data/home_new/wujinqi/agent-memory/experiments/stage1_hit_priority_w2_lme_s_3/metrics.json
- manifest: /data/home_new/wujinqi/agent-memory/experiments/stage1_hit_priority_w2_lme_s_3/manifest.json
- offline_lexical_eval: /data/home_new/wujinqi/agent-memory/experiments/stage1_hit_priority_w2_lme_s_3/offline_lexical_eval.json
- evidence_recall: /data/home_new/wujinqi/agent-memory/experiments/stage1_hit_priority_w2_lme_s_3/evidence_recall.json
- deepseek_judge_dry_run: /data/home_new/wujinqi/agent-memory/experiments/stage1_hit_priority_w2_lme_s_3/deepseek_judge_dry_run.json

## Diagnosis

- Change: increase source expansion from `neighbor_window=1` to `neighbor_window=2` while keeping `neighbor_order=hit_priority`.
- Compared with `stage1_hit_priority_lme_s_3`, evidence recall remains 3/3 and offline F1 is unchanged, while avg query tokens increase from 2807.0 to 3240.67.
- This fixed wider window is not justified as a LongMemEval mainline change on the current diagnostic.
- Next step should target adaptive expansion or improved retrieval views before raising context size.

## Clean Notes

- No gold/reference/target answer, judge output, benchmark label, sample id, qid, or row index is passed into the prediction pipeline.
- Raw evidence remains the only factual source; compiled evidence rows keep source_id links.
- Accuracy is intentionally not computed by the prediction runner; any gold or judge metrics must be produced offline after prediction.
