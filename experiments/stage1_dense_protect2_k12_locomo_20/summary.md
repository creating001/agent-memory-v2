# stage1_dense_protect2_k12_locomo_20

## Purpose

Stage-1 clean skeleton run: validate raw evidence storage, lexical retrieval, neighbor expansion, evidence compilation, answer generation, trace output, and experiment bookkeeping.

## Scope

- benchmark: locomo
- subset: non-adversarial
- experiment_kind: diagnostic
- limit: 20
- input_path: /data/home_new/wujinqi/agent-memory/outputs/prepare_locomo_non_adversarial/prediction_input.jsonl
- config_path: /data/home_new/wujinqi/agent-memory/configs/stage1_vllm_dense_protect2_k12.json
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0.0 and max_tokens 256.

## Git

- inside_work_tree: True
- commit: 21c327ff8cf8968de2201f77104f20c46e332ed6
- dirty: True
- note: None

## Metrics

- n_samples: 20
- accuracy: None
- f1: None
- bleu: None
- avg_build_tokens: 0.0
- avg_query_tokens: 2796.55
- avg_compiled_evidence_items: 34.55
- neighbor_order: hit_priority
- drop_query_stopwords: False
- dense_enabled: True
- lexical_protect_top_n: 2
- avg_embedding_tokens: 13489.55
- avg_context_chars: 8944.85
- answer_mode: openai_compatible
- answer_model: Qwen/Qwen3-30B-A3B-Instruct-2507
- offline_exact: 0.0
- offline_f1: 0.13776068080452944
- offline_bleu_unigram: 0.08851153985817861
- evidence_recall: 0.7
- avg_embedding_tokens: 13489.55

## Outputs

- predictions: /data/home_new/wujinqi/agent-memory/outputs/stage1_dense_protect2_k12_locomo_20/predictions.jsonl
- traces: /data/home_new/wujinqi/agent-memory/outputs/stage1_dense_protect2_k12_locomo_20/traces.jsonl
- metrics: /data/home_new/wujinqi/agent-memory/experiments/stage1_dense_protect2_k12_locomo_20/metrics.json
- manifest: /data/home_new/wujinqi/agent-memory/experiments/stage1_dense_protect2_k12_locomo_20/manifest.json
- offline_lexical_eval: /data/home_new/wujinqi/agent-memory/experiments/stage1_dense_protect2_k12_locomo_20/offline_lexical_eval.json
- evidence_recall: /data/home_new/wujinqi/agent-memory/experiments/stage1_dense_protect2_k12_locomo_20/evidence_recall.json
- deepseek_judge_dry_run: /data/home_new/wujinqi/agent-memory/experiments/stage1_dense_protect2_k12_locomo_20/deepseek_judge_dry_run.json

## Diagnosis

- Method: dense hybrid protect2 with `top_k=12`, `dense.top_k=12`, and compiler budget 36 rows / 18000 chars.
- Compared with `stage1_dense_protect2_locomo_20`, evidence recall improves from 0.65 to 0.70 and offline F1 improves from 0.11995 to 0.13776.
- Avg query tokens rise from 1647.25 to 2796.55, still within the 6K budget but not a strong enough tradeoff by itself.
- Remaining misses are mostly profile/entity/temporal questions where relevant facts are not reached by turn-level dense/BM25, or where the answer is derivable from alternate evidence not listed in labels.
- Next step should add typed profile/entity/session views or a verifier, rather than only increasing top-k further.

## Clean Notes

- No gold/reference/target answer, judge output, benchmark label, sample id, qid, or row index is passed into the prediction pipeline.
- Raw evidence remains the only factual source; compiled evidence rows keep source_id links.
- Accuracy is intentionally not computed by the prediction runner; any gold or judge metrics must be produced offline after prediction.
