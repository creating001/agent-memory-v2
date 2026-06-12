# stage1_hit_priority_locomo_3

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
- commit: 2bb002e0944bba23e314079c1bcec194d07efb2d
- dirty: True
- note: None

## Metrics

- n_samples: 3
- accuracy: None
- f1: None
- bleu: None
- avg_build_tokens: 0.0
- avg_query_tokens: 1731.3333333333333
- avg_compiled_evidence_items: 20.0
- neighbor_order: hit_priority
- avg_context_chars: 5646.666666666667
- answer_mode: openai_compatible
- answer_model: Qwen/Qwen3-30B-A3B-Instruct-2507
- offline_exact: 0.0
- offline_f1: 0.07731481481481482
- offline_bleu_unigram: 0.0424192665571976
- evidence_recall: 0.3333333333333333

## Outputs

- predictions: /data/home_new/wujinqi/agent-memory/outputs/stage1_hit_priority_locomo_3/predictions.jsonl
- traces: /data/home_new/wujinqi/agent-memory/outputs/stage1_hit_priority_locomo_3/traces.jsonl
- metrics: /data/home_new/wujinqi/agent-memory/experiments/stage1_hit_priority_locomo_3/metrics.json
- manifest: /data/home_new/wujinqi/agent-memory/experiments/stage1_hit_priority_locomo_3/manifest.json
- offline_lexical_eval: /data/home_new/wujinqi/agent-memory/experiments/stage1_hit_priority_locomo_3/offline_lexical_eval.json
- evidence_recall: /data/home_new/wujinqi/agent-memory/experiments/stage1_hit_priority_locomo_3/evidence_recall.json
- deepseek_judge_dry_run: /data/home_new/wujinqi/agent-memory/experiments/stage1_hit_priority_locomo_3/deepseek_judge_dry_run.json

## Diagnosis

- Change: `neighbor_order=hit_priority`, preserving top retrieved evidence before adding neighbors.
- Compared with `stage1_qwen30b_locomo_3`, evidence recall improves from 0/3 to 1/3 and offline F1 improves from 0.00647 to 0.07731.
- The first question now compiles `D1:3` first and answers `7 May 2023`; remaining misses indicate BM25 recall still needs session/entity expansion.
- This is clean because ordering uses only retrieval hits and raw neighboring turns, not labels or evidence annotations.

## Clean Notes

- No gold/reference/target answer, judge output, benchmark label, sample id, qid, or row index is passed into the prediction pipeline.
- Raw evidence remains the only factual source; compiled evidence rows keep source_id links.
- Accuracy is intentionally not computed by the prediction runner; any gold or judge metrics must be produced offline after prediction.
