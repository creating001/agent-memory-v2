# stage1_structured_evidence_guide_v14_locomo_nonadv_full_f48cf10

## 目的

验证 v14 structured evidence guide 在 LoCoMo non-adversarial full 上的全量效果。v14 基于 v13 temporal aid，额外把已检索 raw rows 和 build-stage typed memory 的 source links 组织成 compact guide，帮助 answer model 看清 raw evidence 与 typed memory 的对应关系。

该 guide 不是独立事实来源，只索引当前 prompt 中已经出现的 Memory Context 和 activated build memory；不读取 gold、judge、benchmark category/question_type、sample id、qid 或样本级规则。

## 配置

- benchmark: LoCoMo
- subset: non-adversarial full
- n_samples: 1540
- config: `/data/home_new/wujinqi/agent-memory/configs/stage1_structured_evidence_guide_v14_cached.json`
- prediction workers: 8
- judge workers: 16
- answer model: Qwen/Qwen3-30B-A3B-Instruct-2507
- answer base_url: `http://127.0.0.1:8000/v1`
- answer max input/output: 131072 / 16384
- embedding model: Qwen/Qwen3-Embedding-0.6B
- dense raw-turn retrieval: top-40, external_naive text format
- lexical retrieval: disabled
- temporal aid: enabled
- structured guide: enabled, max_rows 12
- max_memory_records in guide: 8

## Git

- commit: `f48cf10cc935c653869da446ed9b4f32231b318c`
- dirty at prediction: false

## Prediction Metrics

- avg_build_tokens: 58386.008
- build_token_accounting: logical cold-build LLM tokens；cache 命中也按 stored usage 计入方法成本，cache 只减少本机重复 API 调用。
- avg_query_tokens: 3818.198
- avg_compiled_evidence_items: 40.0
- avg_context_chars: 11952.301
- avg_build_memory_records: 136.660
- avg_active_build_memory_records: 125.211
- avg_memory_hits: 19.842
- avg_memory_source_hits: 22.381
- build_memory_cache: hits 12411, misses 0, writes 0
- embedding_cache: hits 7422, misses 0, writes 0
- structured_guide_prompts: 1540/1540
- temporal_aid_prompts: 391/1540
- prompts_with_memory_records: 1540/1540

## Offline Judge Results

- judge: DeepSeek `deepseek-v4-flash`, prediction 完成后离线使用。
- accuracy: 1133/1540 = 0.735714
- invalid_judgments: 0
- judge_tokens: prompt 496315, completion 155818, total 652133
- retry_note: one empty-content INVALID judge response was retried offline and replaced before final metrics; prediction artifacts were unchanged.
- evidence_recall: 1339/1536 = 0.871745, diagnostic only.
- token_gate: avg_build_tokens 58386.008 <= 100000；avg_query_tokens 3818.198 <= 6000。

By category:

- category 1: 182/282 = 0.645
- category 2: 195/321 = 0.607
- category 3: 60/96 = 0.625
- category 4: 696/841 = 0.828

Comparisons:

- vs v13 temporal aid: v14-only 123, v13-only 101, net +22.
- vs v12 source expansion: v14-only 147, v12-only 90, net +57.
- vs clean naive external top-40: v14-only 168, naive-only 110, net +58.

结论：v14 是当前 LoCoMo 最好结果，主要提升来自 category 2/3/4；category 1 小幅下降。structured guide 对 LoCoMo 有明确正收益，但同一配置在 LongMemEval-S full 上从 v13 的 0.714 降到 0.704，因此不能作为统一主线直接推广。下一步应保留 source-linked guide 的优点，同时减少对 LME 的上下文噪声。

## Outputs

- predictions: `/data/home_new/wujinqi/agent-memory/outputs/formal/stage1_structured_evidence_guide_v14_locomo_nonadv_full_f48cf10/predictions.jsonl`
- traces: `/data/home_new/wujinqi/agent-memory/outputs/formal/stage1_structured_evidence_guide_v14_locomo_nonadv_full_f48cf10/traces.jsonl`
- metrics: `/data/home_new/wujinqi/agent-memory/experiments/formal/stage1_structured_evidence_guide_v14_locomo_nonadv_full_f48cf10/metrics.json`
- judge: `/data/home_new/wujinqi/agent-memory/experiments/formal/stage1_structured_evidence_guide_v14_locomo_nonadv_full_f48cf10/deepseek_judge.json`
- evidence_recall: `/data/home_new/wujinqi/agent-memory/experiments/formal/stage1_structured_evidence_guide_v14_locomo_nonadv_full_f48cf10/evidence_recall.json`
- manifest: `/data/home_new/wujinqi/agent-memory/experiments/formal/stage1_structured_evidence_guide_v14_locomo_nonadv_full_f48cf10/manifest.json`

## Clean Notes

- Prediction loader rejects gold/reference/target answers, judge outputs, benchmark labels, sample ids, qids, and row indices.
- Build-stage typed memory is generated only from raw dialogue and visible metadata.
- Structured guide only reorganizes retrieved raw rows and activated memory source links already available at query time.
- DeepSeek judge and evidence labels are offline-only diagnostics and must not feed prediction, retrieval, compiler, answer, verifier, or route logic.
