# stage1_stopwords_locomo_3

## Purpose

Stage-1 clean skeleton run: validate raw evidence storage, lexical retrieval, neighbor expansion, evidence compilation, answer generation, trace output, and experiment bookkeeping.

## Scope

- benchmark: locomo
- subset: non-adversarial
- experiment_kind: diagnostic
- limit: 3
- input_path: /data/home_new/wujinqi/agent-memory/outputs/prepare_locomo_non_adversarial/prediction_input.jsonl
- config_path: /data/home_new/wujinqi/agent-memory/configs/stage1_vllm_hit_priority_stopwords.json
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0.0 and max_tokens 256.

## Git

- inside_work_tree: True
- commit: 6cfcd4a3bff1b76ccd50db50877f0469d0474ccf
- dirty: True
- note: None

## Metrics

- n_samples: 3
- accuracy: None
- f1: None
- bleu: None
- avg_build_tokens: 0.0
- avg_query_tokens: 1661.6666666666667
- avg_compiled_evidence_items: 20.0
- neighbor_order: hit_priority
- drop_query_stopwords: True
- avg_context_chars: 5394.333333333333
- answer_mode: openai_compatible
- answer_model: Qwen/Qwen3-30B-A3B-Instruct-2507
- offline_exact: 0.0
- offline_f1: 0.12190476190476192
- offline_bleu_unigram: 0.07575757575757576
- evidence_recall: 0.3333333333333333

## Outputs

- predictions: /data/home_new/wujinqi/agent-memory/outputs/stage1_stopwords_locomo_3/predictions.jsonl
- traces: /data/home_new/wujinqi/agent-memory/outputs/stage1_stopwords_locomo_3/traces.jsonl
- metrics: /data/home_new/wujinqi/agent-memory/experiments/stage1_stopwords_locomo_3/metrics.json
- manifest: /data/home_new/wujinqi/agent-memory/experiments/stage1_stopwords_locomo_3/manifest.json
- offline_lexical_eval: /data/home_new/wujinqi/agent-memory/experiments/stage1_stopwords_locomo_3/offline_lexical_eval.json
- evidence_recall: /data/home_new/wujinqi/agent-memory/experiments/stage1_stopwords_locomo_3/evidence_recall.json
- deepseek_judge_dry_run: /data/home_new/wujinqi/agent-memory/experiments/stage1_stopwords_locomo_3/deepseek_judge_dry_run.json

## Diagnosis

- Change: enable generic BM25 query stopword filtering with `neighbor_window=1` and `neighbor_order=hit_priority`.
- Compared with `stage1_hit_priority_locomo_3`, offline F1 improves from 0.07731 to 0.12190 and avg query tokens drop from 1731.33 to 1661.67.
- Evidence recall stays 1/3, so stopword filtering does not solve the remaining retrieval miss on this slice.
- The first temporal answer is still noisy, so this remains a diagnostic retrieval-normalization switch, not a mainline promotion.

## Clean Notes

- No gold/reference/target answer, judge output, benchmark label, sample id, qid, or row index is passed into the prediction pipeline.
- Raw evidence remains the only factual source; compiled evidence rows keep source_id links.
- Accuracy is intentionally not computed by the prediction runner; any gold or judge metrics must be produced offline after prediction.
