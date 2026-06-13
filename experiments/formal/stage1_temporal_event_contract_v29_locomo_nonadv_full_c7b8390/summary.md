# stage1_temporal_event_contract_v29_locomo_nonadv_full_c7b8390

## 目的

验证 v29 temporal event contract 在 LoCoMo non-adversarial full 上是否能修复 v28 的 mention date / event time 混淆。方法保持 v28 的 build-stage typed memory、dense+BM25 raw retrieval、raw source expansion、structured row guide、temporal aid 和可见 `evidence_report` 不变，只在 temporal route 中要求 answer model 区分：

- `mention_time`：Memory row/session date。
- `event_time`：目标事件或状态发生/成立的时间。

设计参考：

- Graphiti/Zep：temporal validity (`valid_at` / `invalid_at`) 和 episode provenance。
- SimpleMem：lossless memory unit 与绝对时间归一化。
- xMemory：semantic / episodic 双通道和 original message 回链。
- creating001 query 结构：evidence-first temporal extraction 中 memory date 不等于 event date 的通用思想；不迁移 benchmark/category/sample/string guardrail、target phrase 或 finalizer。

本次是 query-side compiler ablation，不改 build/retrieval，不使用 gold answer、judge output、benchmark label、category、sample id、row index 或 test feedback 参与预测。

## 范围

- benchmark: LoCoMo
- subset: non-adversarial full
- samples: 1540
- config: `configs/stage1_temporal_event_contract_v29_cached.json`
- predictions: `outputs/formal/stage1_temporal_event_contract_v29_locomo_nonadv_full_c7b8390/predictions.jsonl`
- traces: `outputs/formal/stage1_temporal_event_contract_v29_locomo_nonadv_full_c7b8390/traces.jsonl`
- judge: `experiments/formal/stage1_temporal_event_contract_v29_locomo_nonadv_full_c7b8390/deepseek_judge.json`
- diagnostics: `offline_comparison.json`, `evidence_recall.json`

## Git 与 Dirty 状态

- prediction commit in manifest: `c7b8390ca6867aac53eaa781d7a300ac2ea94759`
- manifest dirty: `true`
- dirty reason: prediction 运行过程中用户修改了 `docs/architecture.md` 和 `docs/clean_protocol.md`；prediction code/config 没有未提交改动，运行前工作区为 clean `c7b8390`。
- clean note: labels、category、evidence、gold 和 DeepSeek judge 只在预测完成后离线诊断使用，不进入 prediction pipeline。

## 结果

- DeepSeek judge accuracy: `0.761688` (`1173/1540`)
- v28 accuracy: `0.737662` (`1136/1540`)
- v18 accuracy: `0.737013` (`1135/1540`)
- clean naive RAG accuracy: `0.698506`
- v29 vs v28: `+37/1540`
- v29 vs naive: about `+97/1540`
- LoCoMo baseline target: `>=0.780`
- 当前结论: v29 是当前 LoCoMo 最好结果，但仍未达到 baseline target。

## Token 成本

- avg build tokens: `58386.0078`
- total build tokens: `89914452`
- avg query tokens: `3932.5604`
- total query tokens: `6056143`
- LoCoMo 主线预算: avg build `<=100K`，avg query `<=6K`
- 本次满足 avg token 预算。
- query tail: `4/1540` samples > 6K，`1/1540` samples > 8K。
- answer max input/output: `131072/16384`
- build cache hits/misses/writes: `12411/0/0`
- answer cache hits/misses/writes: `11/1529/1529`
- avg build memory records: `136.6597`
- avg memory hits: `19.8416`

## 与 v28 对比

- both correct: `1099`
- v29 only: `74`
- v28 only: `37`
- both wrong: `330`
- net: `+37`

按 LoCoMo category：

| category | n | v28 | v29 | delta |
|---|---:|---:|---:|---:|
| 1 | 282 | 0.648936 | 0.659574 | +3 |
| 2 | 321 | 0.619938 | 0.732087 | +36 |
| 3 | 96 | 0.583333 | 0.593750 | +1 |
| 4 | 841 | 0.829964 | 0.826397 | -3 |

按 question-derived information need：

| need | n | v28 | v29 | delta |
|---|---:|---:|---:|---:|
| current_state | 4 | 0.750000 | 0.750000 | 0 |
| fact_lookup | 1018 | 0.783890 | 0.783890 | 0 |
| list_count | 131 | 0.587786 | 0.603053 | +2 |
| profile_preference | 49 | 0.795918 | 0.775510 | -1 |
| temporal_lookup | 338 | 0.647929 | 0.754438 | +36 |

## 结论

v29 对 LoCoMo 是明确正向，收益几乎完全来自 temporal_lookup/category 2。它修复了大量“last week / weekend before / Tuesday before / month ago”等相对时间被错误答成 Memory Date 的问题，例如：

- “meet up with friends, family, and mentors”：`2023-06-09` -> `2023-06-02 to 2023-06-08`
- “picnic”：`2023-07-06` -> `2023-06-29 to 2023-07-05`
- “mentorship program”：`2023-07-17` -> `2023-07-15 to 2023-07-16`
- “activist group”：`2023-07-20` -> `2023-07-18`

但它仍有明显不足：

- category 4 略降，profile/preference 也略降。
- 部分旧正确 temporal case 被过度归一化或误用相邻事件。
- LME full 上 v29 低于 v28，因此不能作为统一主线最终方案。

下一步应把 v29 的有效部分前移到 build-stage memory 管理：构建 typed event/state records，显式保存 `mention_time`、`event_time`、`valid_from`、`valid_to`、`event_type`、`source_ids`，并做 dedup/supersede。query-side 只使用这些 typed records 来组织候选和回链 raw evidence，而不是继续给 answer prompt 增加规则。
