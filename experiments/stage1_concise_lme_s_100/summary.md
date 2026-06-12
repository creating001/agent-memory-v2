# stage1_concise_lme_s_100

## Purpose

Stage-1 clean skeleton run: validate raw evidence storage, lexical retrieval, neighbor expansion, evidence compilation, answer generation, trace output, and experiment bookkeeping.

## Scope

- benchmark: longmemeval
- subset: s_cleaned
- experiment_kind: diagnostic
- limit: 100
- input_path: /data/home_new/wujinqi/agent-memory/outputs/prepare_longmemeval_s_cleaned/prediction_input.jsonl
- config_path: /data/home_new/wujinqi/agent-memory/configs/stage1_vllm_answer_concise.json
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0.0 and max_tokens 128.

## Git

- inside_work_tree: True
- commit: c73b385023255068e597e894810727e2351ffb53
- dirty: False
- note: None

## Metrics

- n_samples: 100
- accuracy: None
- f1: None
- bleu: None
- avg_build_tokens: 0.0
- avg_query_tokens: 2880.17
- avg_compiled_evidence_items: 9.41
- neighbor_order: hit_priority
- drop_query_stopwords: False
- dense_enabled: False
- lexical_protect_top_n: None
- avg_embedding_tokens: 0.0
- avg_context_chars: 11406.68
- answer_mode: openai_compatible
- answer_model: Qwen/Qwen3-30B-A3B-Instruct-2507
- answer_style: concise
- offline_exact: 0.4
- offline_f1: 0.5320425887579914
- offline_bleu_unigram: 0.4974012812169807
- evidence_recall: 0.95

## Outputs

- predictions: /data/home_new/wujinqi/agent-memory/outputs/stage1_concise_lme_s_100/predictions.jsonl
- traces: /data/home_new/wujinqi/agent-memory/outputs/stage1_concise_lme_s_100/traces.jsonl
- metrics: /data/home_new/wujinqi/agent-memory/experiments/stage1_concise_lme_s_100/metrics.json
- manifest: /data/home_new/wujinqi/agent-memory/experiments/stage1_concise_lme_s_100/manifest.json
- offline_lexical_eval: /data/home_new/wujinqi/agent-memory/experiments/stage1_concise_lme_s_100/offline_lexical_eval.json
- evidence_recall: /data/home_new/wujinqi/agent-memory/experiments/stage1_concise_lme_s_100/evidence_recall.json
- deepseek_judge_dry_run: /data/home_new/wujinqi/agent-memory/experiments/stage1_concise_lme_s_100/deepseek_judge_dry_run.json

## Diagnosis

- Method: hit-priority BM25 with concise answer prompt and Qwen3-30B answer model.
- Overall lexical exact is 0.40 and F1 is 0.53204 on 100 LongMemEval-S examples.
- Single-session-user exact is 0.55714 with evidence recall 0.97143; multi-session exact is 0.03333 with evidence recall 0.90.
- The next LongMemEval priority is multi-session retrieval/compilation and answer synthesis, not single-session short-answer formatting.
- Real DeepSeek judge accuracy is still blocked because `DEEPSEEK_API_KEY` is not exported in the environment.

## Clean Notes

- No gold/reference/target answer, judge output, benchmark label, sample id, qid, or row index is passed into the prediction pipeline.
- Raw evidence remains the only factual source; compiled evidence rows keep source_id links.
- Accuracy is intentionally not computed by the prediction runner; any gold or judge metrics must be produced offline after prediction.
