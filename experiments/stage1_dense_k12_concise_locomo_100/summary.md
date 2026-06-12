# stage1_dense_k12_concise_locomo_100

## Purpose

Stage-1 clean skeleton run: validate raw evidence storage, lexical retrieval, neighbor expansion, evidence compilation, answer generation, trace output, and experiment bookkeeping.

## Scope

- benchmark: locomo
- subset: non-adversarial
- experiment_kind: diagnostic
- limit: 100
- input_path: /data/home_new/wujinqi/agent-memory/outputs/prepare_locomo_non_adversarial/prediction_input.jsonl
- config_path: /data/home_new/wujinqi/agent-memory/configs/stage1_vllm_dense_protect2_k12_concise.json
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0.0 and max_tokens 128.

## Git

- inside_work_tree: True
- commit: b8ca07a73fc7d2fac87584b9644ecb88fde6bc72
- dirty: False
- note: None

## Metrics

- n_samples: 100
- accuracy: None
- f1: None
- bleu: None
- avg_build_tokens: 0.0
- avg_query_tokens: 2758.74
- avg_compiled_evidence_items: 34.14
- neighbor_order: hit_priority
- drop_query_stopwords: False
- dense_enabled: True
- lexical_protect_top_n: 2
- avg_embedding_tokens: 13489.47
- avg_context_chars: 8893.15
- answer_mode: openai_compatible
- answer_model: Qwen/Qwen3-30B-A3B-Instruct-2507
- answer_style: concise
- offline_exact: 0.04
- offline_f1: 0.27571269917466834
- offline_bleu_unigram: 0.21255678202477424
- evidence_recall: 0.7653061224489796
- avg_embedding_tokens: 13489.47

## Outputs

- predictions: /data/home_new/wujinqi/agent-memory/outputs/stage1_dense_k12_concise_locomo_100/predictions.jsonl
- traces: /data/home_new/wujinqi/agent-memory/outputs/stage1_dense_k12_concise_locomo_100/traces.jsonl
- metrics: /data/home_new/wujinqi/agent-memory/experiments/stage1_dense_k12_concise_locomo_100/metrics.json
- manifest: /data/home_new/wujinqi/agent-memory/experiments/stage1_dense_k12_concise_locomo_100/manifest.json
- offline_lexical_eval: /data/home_new/wujinqi/agent-memory/experiments/stage1_dense_k12_concise_locomo_100/offline_lexical_eval.json
- evidence_recall: /data/home_new/wujinqi/agent-memory/experiments/stage1_dense_k12_concise_locomo_100/evidence_recall.json
- deepseek_judge_dry_run: /data/home_new/wujinqi/agent-memory/experiments/stage1_dense_k12_concise_locomo_100/deepseek_judge_dry_run.json

## Diagnosis

- Method: dense hybrid protect2 k12 with concise answer prompt and Qwen3-30B answer model.
- On 100 LoCoMo non-adversarial examples, evidence recall is 0.76531 and lexical F1 is 0.27571.
- Category 1 recall is weakest at 0.625, category 3 recall is 0.63636, while category 2 and 4 are stronger.
- Temporal/date questions still fail because relative dates like "yesterday" and "last Saturday" are not normalized against dialogue timestamps.
- Real judge accuracy is needed; current DeepSeek artifact is dry-run because `DEEPSEEK_API_KEY` is not exported in the environment.

## Clean Notes

- No gold/reference/target answer, judge output, benchmark label, sample id, qid, or row index is passed into the prediction pipeline.
- Raw evidence remains the only factual source; compiled evidence rows keep source_id links.
- Accuracy is intentionally not computed by the prediction runner; any gold or judge metrics must be produced offline after prediction.
