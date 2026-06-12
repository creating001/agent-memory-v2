# stage1_dense_k12_concise_locomo_20

## Purpose

Stage-1 clean skeleton run: validate raw evidence storage, lexical retrieval, neighbor expansion, evidence compilation, answer generation, trace output, and experiment bookkeeping.

## Scope

- benchmark: locomo
- subset: non-adversarial
- experiment_kind: diagnostic
- limit: 20
- input_path: /data/home_new/wujinqi/agent-memory/outputs/prepare_locomo_non_adversarial/prediction_input.jsonl
- config_path: /data/home_new/wujinqi/agent-memory/configs/stage1_vllm_dense_protect2_k12_concise.json
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
- avg_query_tokens: 2795.35
- avg_compiled_evidence_items: 34.55
- neighbor_order: hit_priority
- drop_query_stopwords: False
- dense_enabled: True
- lexical_protect_top_n: 2
- avg_embedding_tokens: 13489.55
- avg_context_chars: 9038.65
- answer_mode: openai_compatible
- answer_model: Qwen/Qwen3-30B-A3B-Instruct-2507
- answer_style: concise
- offline_exact: 0.05
- offline_f1: 0.1859956416132887
- offline_bleu_unigram: 0.1407515401265401
- evidence_recall: 0.7

## Outputs

- predictions: /data/home_new/wujinqi/agent-memory/outputs/stage1_dense_k12_concise_locomo_20/predictions.jsonl
- traces: /data/home_new/wujinqi/agent-memory/outputs/stage1_dense_k12_concise_locomo_20/traces.jsonl
- metrics: /data/home_new/wujinqi/agent-memory/experiments/stage1_dense_k12_concise_locomo_20/metrics.json
- manifest: /data/home_new/wujinqi/agent-memory/experiments/stage1_dense_k12_concise_locomo_20/manifest.json
- offline_lexical_eval: /data/home_new/wujinqi/agent-memory/experiments/stage1_dense_k12_concise_locomo_20/offline_lexical_eval.json
- evidence_recall: /data/home_new/wujinqi/agent-memory/experiments/stage1_dense_k12_concise_locomo_20/evidence_recall.json
- deepseek_judge_dry_run: /data/home_new/wujinqi/agent-memory/experiments/stage1_dense_k12_concise_locomo_20/deepseek_judge_dry_run.json

## Diagnosis

- Method: dense hybrid protect2 k12 with concise answer prompt.
- Compared with `stage1_dense_protect2_k12_locomo_20`, exact improves from 0.0 to 0.05 and F1 from 0.13776 to 0.18600; evidence recall remains 0.70.
- Temporal grounding remains weak: the first sample answers 8 May instead of deriving 7 May from "yesterday" relative to 8 May.
- LoCoMo next step should add temporal normalization/verifier and profile/entity retrieval, not only concise answer style.

## Clean Notes

- No gold/reference/target answer, judge output, benchmark label, sample id, qid, or row index is passed into the prediction pipeline.
- Raw evidence remains the only factual source; compiled evidence rows keep source_id links.
- Accuracy is intentionally not computed by the prediction runner; any gold or judge metrics must be produced offline after prediction.
