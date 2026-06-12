# stage1_adapter_smoke

## Purpose

Stage-1 clean skeleton smoke run: validate raw evidence storage, lexical retrieval, neighbor expansion, evidence compilation, trace output, and experiment bookkeeping.

## Scope

- benchmark: generic
- subset: smoke
- experiment_kind: smoke
- input_path: /data/home_new/wujinqi/agent-memory/outputs/stage1_prepare_toy/prediction_input.jsonl
- config_path: /data/home_new/wujinqi/agent-memory/configs/stage1_clean_skeleton.json

## Git

- inside_work_tree: True
- commit: None
- dirty: True
- note: None

## Metrics

- n_samples: 1
- accuracy: None
- f1: None
- bleu: None
- avg_build_tokens: 0.0
- avg_query_tokens: 0.0
- avg_compiled_evidence_items: 3.0
- avg_context_chars: 867.0

## Outputs

- predictions: /data/home_new/wujinqi/agent-memory/outputs/stage1_adapter_smoke/predictions.jsonl
- traces: /data/home_new/wujinqi/agent-memory/outputs/stage1_adapter_smoke/traces.jsonl
- metrics: /data/home_new/wujinqi/agent-memory/experiments/stage1_adapter_smoke/metrics.json
- manifest: /data/home_new/wujinqi/agent-memory/experiments/stage1_adapter_smoke/manifest.json
- offline_lexical_eval: /data/home_new/wujinqi/agent-memory/experiments/stage1_adapter_smoke/offline_lexical_eval.json
- deepseek_judge_dry_run: /data/home_new/wujinqi/agent-memory/experiments/stage1_adapter_smoke/deepseek_judge_dry_run.json

## Clean Notes

- No gold/reference/target answer, judge output, benchmark label, sample id, qid, or row index is passed into the prediction pipeline.
- Raw evidence remains the only factual source; compiled evidence rows keep source_id links.
- This runner uses a null answerer, so accuracy is intentionally not reported.
- Offline lexical eval and DeepSeek judge dry-run read labels only after prediction and are not consumed by prediction modules.
