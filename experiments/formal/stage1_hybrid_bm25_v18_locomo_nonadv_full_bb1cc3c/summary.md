# stage1_hybrid_bm25_v18_locomo_nonadv_full_bb1cc3c

## 目的

用与 LongMemEval-S v18 完全相同的通用 hybrid BM25+dense retrieval 配置，验证该方法在 LoCoMo non-adversarial full 上是否也能提升 DeepSeek judge accuracy，并检查 build/query token 是否仍在预算内。

## 方法

- 配置：`configs/stage1_hybrid_bm25_v18_cached.json`
- prediction commit：`bb1cc3c19a335c57d11bcbd180168e3e8576a1b7`
- prediction dirty：`false`
- answer model：Qwen/Qwen3-30B-A3B-Instruct-2507，本地 vLLM `http://127.0.0.1:8000/v1`
- answer max input/output：`131072 / 16384`
- runner workers：`8`

v18 在 v17 selective row guide 上加入 raw-turn BM25 lexical retrieval，与 dense retrieval 和 build-memory source expansion 做通用融合；最终事实来源仍是 raw evidence rows，不使用 gold、judge、benchmark category、sample id、qid、row index 或 test feedback。

## 指标

- benchmark/subset：LoCoMo non-adversarial full，1540 条。
- DeepSeek judge accuracy：`1135/1540 = 0.737013`
- invalid judge：`0`
- evidence recall：`0.889323`，有 evidence labels 的样本数 `1536`
- avg_build_tokens：`58386.008`
- avg_query_tokens：`3270.569`
- build cache：hits `12411`，misses `0`，writes `0`
- avg build memory records：`136.660`
- avg active memory records：`125.211`
- avg compiled evidence items：`40.000`
- avg context chars：`9956.962`
- judge token usage：prompt `495397`，completion `156487`，total `651884`

## 分 category accuracy

| category | correct / total | accuracy |
|---|---:|---:|
| 1 | 187 / 282 | 0.663121 |
| 2 | 190 / 321 | 0.591900 |
| 3 | 60 / 96 | 0.625000 |
| 4 | 698 / 841 | 0.829964 |

## 对比结论

- vs v14：净 `+2`，v18-only `112`，v14-only `110`。
- vs v17：净 `+25`。
- vs v16：净 `+11`。
- vs v13：净 `+24`。
- vs v12：净 `+59`。
- vs clean naive RAG：净 `+60`。

v18 成为当前 LoCoMo non-adversarial full 最好结果，但相对 v14 只高 2 条；category 2 比 v14 少 5 条，category 1 和 4 补回。结论是 v18 可以作为统一主线，但下一步需要重点做 v18/v14 互补错例分析，不能把这 2 条净提升过度解读。

## 输出路径

- predictions：`outputs/formal/stage1_hybrid_bm25_v18_locomo_nonadv_full_bb1cc3c/predictions.jsonl`
- traces：`outputs/formal/stage1_hybrid_bm25_v18_locomo_nonadv_full_bb1cc3c/traces.jsonl`
- metrics：`experiments/formal/stage1_hybrid_bm25_v18_locomo_nonadv_full_bb1cc3c/metrics.json`
- judge：`experiments/formal/stage1_hybrid_bm25_v18_locomo_nonadv_full_bb1cc3c/deepseek_judge.json`
- evidence recall：`experiments/formal/stage1_hybrid_bm25_v18_locomo_nonadv_full_bb1cc3c/evidence_recall.json`
- manifest：`experiments/formal/stage1_hybrid_bm25_v18_locomo_nonadv_full_bb1cc3c/manifest.json`

## 下一步

v18 同时刷新 LME 和 LoCoMo 当前最好结果，下一阶段应该围绕通用 memory management 做更强方法：保留 v18 hybrid retrieval，同时分析 v14 的 source-linked organization 在 LoCoMo category 2 上的优势，设计 clean 的 selective source-linked guide 或多视图 compiler。
