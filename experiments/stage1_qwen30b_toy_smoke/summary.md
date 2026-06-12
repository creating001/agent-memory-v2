# stage1_qwen30b_toy_smoke

## Purpose

Stage-1 clean skeleton run: validate raw evidence storage, lexical retrieval, neighbor expansion, evidence compilation, answer generation, trace output, and experiment bookkeeping.

## Scope

- benchmark: toy
- subset: smoke
- experiment_kind: diagnostic
- limit: 1
- input_path: /data/home_new/wujinqi/agent-memory/data/examples/toy_memory.jsonl
- config_path: /data/home_new/wujinqi/agent-memory/configs/stage1_vllm_answer.json
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0.0 and max_tokens 256.

## Git

- inside_work_tree: True
- commit: 7262de64500092804a0b5b5f76d16341aa5ed763
- dirty: True
- note: None

## Metrics

- n_samples: 1
- accuracy: None
- f1: None
- bleu: None
- avg_build_tokens: 0.0
- avg_query_tokens: 314.0
- avg_compiled_evidence_items: 3.0
- avg_context_chars: 867.0
- answer_mode: openai_compatible
- answer_model: Qwen/Qwen3-30B-A3B-Instruct-2507

## Outputs

- predictions: /data/home_new/wujinqi/agent-memory/outputs/stage1_qwen30b_toy_smoke/predictions.jsonl
- traces: /data/home_new/wujinqi/agent-memory/outputs/stage1_qwen30b_toy_smoke/traces.jsonl
- metrics: /data/home_new/wujinqi/agent-memory/experiments/stage1_qwen30b_toy_smoke/metrics.json
- manifest: /data/home_new/wujinqi/agent-memory/experiments/stage1_qwen30b_toy_smoke/manifest.json

## Clean Notes

- No gold/reference/target answer, judge output, benchmark label, sample id, qid, or row index is passed into the prediction pipeline.
- Raw evidence remains the only factual source; compiled evidence rows keep source_id links.
- Accuracy is intentionally not computed by the prediction runner; any gold or judge metrics must be produced offline after prediction.
