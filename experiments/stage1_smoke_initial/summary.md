# stage1_smoke_initial

## Purpose

Stage-1 clean skeleton smoke run: validate raw evidence storage, lexical retrieval, neighbor expansion, evidence compilation, trace output, and experiment bookkeeping.

## Scope

- benchmark: toy
- subset: smoke
- experiment_kind: smoke
- input_path: /data/home_new/wujinqi/agent-memory/data/examples/toy_memory.jsonl
- config_path: /data/home_new/wujinqi/agent-memory/configs/stage1_clean_skeleton.json

## Git

- inside_work_tree: False
- commit: None
- dirty: None
- note: not_a_git_repository

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

- predictions: /data/home_new/wujinqi/agent-memory/outputs/stage1_smoke_initial/predictions.jsonl
- traces: /data/home_new/wujinqi/agent-memory/outputs/stage1_smoke_initial/traces.jsonl
- metrics: /data/home_new/wujinqi/agent-memory/experiments/stage1_smoke_initial/metrics.json
- manifest: /data/home_new/wujinqi/agent-memory/experiments/stage1_smoke_initial/manifest.json

## Clean Notes

- No gold/reference/target answer, judge output, benchmark label, sample id, qid, or row index is passed into the prediction pipeline.
- Raw evidence remains the only factual source; compiled evidence rows keep source_id links.
- This runner uses a null answerer, so accuracy is intentionally not reported.
