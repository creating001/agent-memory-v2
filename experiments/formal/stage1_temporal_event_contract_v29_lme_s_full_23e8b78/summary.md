# stage1_temporal_event_contract_v29_lme_s_full_23e8b78

## 目的

验证 v29 temporal event contract：在 v28 的 build-stage typed memory、dense+BM25 raw retrieval、raw source expansion、structured row guide、temporal aid 和可见 `evidence_report` 不变的前提下，只在 temporal route 中显式区分：

- `mention_time`：Memory row/session date，即这条记忆被说出或记录的时间。
- `event_time`：目标事件或状态真正发生/成立的时间。

设计参考：

- Graphiti/Zep：事实边保留 `valid_at` / `invalid_at` 和 episode provenance。
- SimpleMem：build 阶段生成 lossless、时间归一化、可独立理解的 memory unit。
- xMemory：semantic / episodic 双通道和 original message 回链。
- creating001 query 结构：evidence-first temporal extraction 中“memory date 不等于 event date”的通用思想；不迁移其 benchmark/字符串 guardrail、target phrase、category、sample 规则或 finalizer。

本次改动是 query-side compiler ablation，不改 retrieval/build cache，不使用 gold answer、judge output、benchmark label、question_type、sample id、qid、row index 或 test feedback。

## 范围

- benchmark: LongMemEval-S
- subset: full
- samples: 500
- config: `configs/stage1_temporal_event_contract_v29_cached.json`
- predictions: `outputs/formal/stage1_temporal_event_contract_v29_lme_s_full_23e8b78/predictions.jsonl`
- traces: `outputs/formal/stage1_temporal_event_contract_v29_lme_s_full_23e8b78/traces.jsonl`
- judge: `experiments/formal/stage1_temporal_event_contract_v29_lme_s_full_23e8b78/deepseek_judge.json`
- offline diagnostics: `offline_comparison.json`, `evidence_recall.json`

## Git 与 Clean 状态

- prediction commit: `23e8b787d31d199e203506ec1a6a855c193715a6`
- prediction dirty: `false`
- judge/evidence diagnostic dirty: `true`，原因是预测完成后新增本实验目录中的 judge、comparison、diagnosis 文件。
- clean note: DeepSeek judge、labels 和 diagnostics 只在预测完成后离线使用，不进入 prediction pipeline。

## 结果

- DeepSeek judge accuracy: `0.762` (`381/500`)
- v28 LME accuracy: `0.766` (`383/500`)
- v29 vs v28: `-2/500`
- LME baseline target: `>=0.800`
- 当前结论: v29 没有超过 v28，不能作为 LME 主线替代；但它改善了一部分 temporal/fact case，值得作为后续 temporal compiler 诊断输入。

## Token 成本

- avg build tokens: `80346.246`
- total build tokens: `40173123`
- avg query tokens: `5807.19`
- total query tokens: `2903595`
- LME 主线预算: avg build `<=300K`，avg query `<=6K`
- 本次满足 avg token 预算，但 query 更接近 6K 上限。
- query tail: `174/500` samples > 6K，`2/500` samples > 8K。
- answer max input/output: `131072/16384`
- build cache hits/misses/writes: `3341/0/0`
- answer cache hits/misses/writes: `0/500/500`
- avg build memory records: `129.662`

## 与 v28 对比

- both correct: `361`
- v29 only: `20`
- v28 only: `22`
- both wrong: `97`

按 LongMemEval type：

| type | v28 | v29 | delta |
|---|---:|---:|---:|
| knowledge-update | 0.821 | 0.808 | -1 |
| multi-session | 0.647 | 0.639 | -1 |
| single-session-assistant | 0.929 | 0.946 | +1 |
| single-session-preference | 0.433 | 0.400 | -1 |
| single-session-user | 0.929 | 0.943 | +1 |
| temporal-reasoning | 0.774 | 0.767 | -1 |

按 question-derived information need：

| need | v28 | v29 | delta |
|---|---:|---:|---:|
| current_state | 0.636 | 0.500 | -3 |
| fact_lookup | 0.803 | 0.814 | +2 |
| list_count | 0.807 | 0.790 | -2 |
| profile_preference | 0.600 | 0.533 | -1 |
| temporal_lookup | 0.727 | 0.739 | +2 |

## 结论

v29 的核心假设只部分成立：把 `mention_time` 和 `event_time` 分开确实帮助了一些 temporal_lookup，例如 “last week / a week ago / month ago” 相关题，也修复了一些 fact slot 选择。但它同时让 current_state、list_count 和部分 insufficient-evidence case 更容易过度使用候选时间或相关事件，整体低于 v28。

下一步不应直接扩大 temporal prompt 规则。更合理的方向是做 build-side typed event/state memory：在 build 阶段由 LLM 明确抽取 `valid_from` / `valid_to` / `event_time` / `mention_time` / source_ids，并在 query 阶段把这些 typed records 作为检索和组织线索，同时仍回到 raw evidence 定案。
