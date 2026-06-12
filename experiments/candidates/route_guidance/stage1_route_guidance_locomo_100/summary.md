# stage1_route_guidance_locomo_100

## Purpose

Stage-1 clean skeleton run: validate raw evidence storage, lexical retrieval, neighbor expansion, evidence compilation, answer generation, trace output, and experiment bookkeeping.

## Scope

- benchmark: locomo
- subset: non_adversarial
- experiment_kind: focused_ablation
- limit: 100
- input_path: /data/home_new/wujinqi/agent-memory/outputs/prepare_locomo_non_adversarial/prediction_input.jsonl
- config_path: /data/home_new/wujinqi/agent-memory/configs/stage1_vllm_dense_k12_concise_session_bm25_temporal_p4_grounded_strict_cached_guidance.json
- answer: OpenAI-compatible answerer using Qwen/Qwen3-30B-A3B-Instruct-2507 at http://127.0.0.1:8000/v1 with temperature 0.0 and max_tokens 128.

## Git

- inside_work_tree: True
- commit: d30c0a995fcd7bad56e0ed77c95ab053c6a7c8c1
- dirty: True
- note: None

## Metrics

- n_samples: 100
- accuracy: None
- f1: None
- bleu: None
- avg_build_tokens: 0.0
- avg_query_tokens: 2867.35
- avg_compiled_evidence_items: 34.14
- neighbor_order: hit_priority
- drop_query_stopwords: False
- dense_enabled: True
- lexical_protect_top_n: 2
- embedding_cache_enabled: True
- embedding_cache_path: outputs/cache/qwen3_embedding.sqlite
- embedding_cache_hits: 42000
- embedding_cache_misses: 0
- embedding_cache_writes: 0
- session_bm25_enabled: True
- session_bm25_top_k: 8
- session_anchor_top_k: 2
- session_max_anchor_hits: 12
- session_protect_turn_hits: 4
- session_enabled_route_signals: ['temporal', 'recent_or_current']
- session_enabled_information_needs: None
- session_enabled_query_patterns: ['\\b20\\d{2}\\b', '\\b(?:january|february|march|april|june|july|august|september|october|november|december)\\b', '\\bmay\\s+20\\d{2}\\b']
- session_bm25_applied_count: 41
- session_bm25_applied_rate: 0.41
- avg_embedding_tokens: 0.0
- avg_context_chars: 9497.6
- answer_mode: openai_compatible
- answer_model: Qwen/Qwen3-30B-A3B-Instruct-2507
- answer_style: concise
- evidence_order: retrieval
- row_text_mode: full
- max_row_text_chars: 0
- route_guidance: True
- temporal_grounding: True
- temporal_hints: False
- enable_broad_list_patterns: False

## Outputs

- predictions: /data/home_new/wujinqi/agent-memory/outputs/stage1_route_guidance_locomo_100/predictions.jsonl
- traces: /data/home_new/wujinqi/agent-memory/outputs/stage1_route_guidance_locomo_100/traces.jsonl
- metrics: /data/home_new/wujinqi/agent-memory/experiments/candidates/route_guidance/stage1_route_guidance_locomo_100/metrics.json
- manifest: /data/home_new/wujinqi/agent-memory/experiments/candidates/route_guidance/stage1_route_guidance_locomo_100/manifest.json

## Clean Notes

- No gold/reference/target answer, judge output, benchmark label, sample id, qid, or row index is passed into the prediction pipeline.
- Raw evidence remains the only factual source; compiled evidence rows keep source_id links.
- Accuracy is intentionally not computed by the prediction runner; any gold or judge metrics must be produced offline after prediction.

## Judge Evaluation

- deepseek_judge: /data/home_new/wujinqi/agent-memory/experiments/candidates/route_guidance/stage1_route_guidance_locomo_100/deepseek_judge.json
- judge_model: deepseek-v4-flash
- judge_accuracy: 0.51
- n_judgments: 100

## Evaluation Note

- This is a 100-row diagnostic, not a formal full LoCoMo result.
- Primary method selection should use DeepSeek judge accuracy on full benchmark scope.
- Offline exact/F1/BLEU are diagnostic only and should not drive method selection.

## Method Note

Route guidance adds generic information-need instructions derived from the question-only router, without benchmark labels, sample ids, gold answers, or judge output. It is a clean answer-stage procedural prompt.

## Decision

Positive diagnostic by judge accuracy on LoCoMo 100, but still not formal. Next step is full LoCoMo non-adversarial and full LongMemEval-S judge evaluation.
