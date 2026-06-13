# stage1_temporal_session_anchor_v20_locomo_nonadv_full_4e4a939

## 目的

验证 v20 raw temporal/session anchor 是否能补上 v18 在 LoCoMo category 2 / temporal 类问题上相对 v14 的短板。方法保持 raw evidence-first：session BM25 只用于找到 raw session 内 anchor turns，不暴露 build-memory 摘要。

## 方法

- 配置快照：`experiments/formal/stage1_temporal_session_anchor_v20_locomo_nonadv_full_4e4a939/config_snapshot.json`
- prediction commit：`4e4a939cbb5f9e605eeeb54c4a6861a4f169e758`
- prediction dirty：`false`
- answer max input/output：`131072 / 16384`
- session_bm25：只对 `temporal_lookup` 开启，`top_k=4`，`anchor_top_k=1`，`max_anchor_hits=4`，`protect_turn_hits=32`
- clean note：只使用 question-derived route、raw dialogue、build memory source expansion 和 retrieved raw rows；不使用 gold、judge、benchmark category、sample id、qid、row index 或 test feedback。

## 指标

- benchmark/subset：LoCoMo non-adversarial full，1540 条。
- DeepSeek judge accuracy：`1120/1540 = 0.727273`
- invalid judge：`0`
- evidence recall：`0.889974`
- avg_build_tokens：`58386.008`
- avg_query_tokens：`3269.849`
- session_bm25 applied：`338/1540`
- avg session anchor hits：`0.878`
- avg final session anchor hits：`0.490`
- judge token usage：prompt `495516`，completion `152889`，total `648405`

## 分 category accuracy

| category | correct / total | accuracy |
|---|---:|---:|
| 1 | 177 / 282 | 0.627660 |
| 2 | 185 / 321 | 0.576324 |
| 3 | 58 / 96 | 0.604167 |
| 4 | 700 / 841 | 0.832342 |

## 对比结论

- vs v18：净 `-15`，v20-only `29`，v18-only `44`。
- vs v14：净 `-13`。
- vs v16：净 `-4`。
- vs v17：净 `+10`。
- vs v13：净 `+9`。
- vs clean naive RAG：净 `+45`。

v20 未补上 LoCoMo category 2，反而从 v18 的 `190/321` 降到 `185/321`。它只在 category 4 有小幅高于 v18，但不足以抵消 category 1/2/3 的退化。

## 输出路径

- predictions：`outputs/formal/stage1_temporal_session_anchor_v20_locomo_nonadv_full_4e4a939/predictions.jsonl`
- traces：`outputs/formal/stage1_temporal_session_anchor_v20_locomo_nonadv_full_4e4a939/traces.jsonl`
- metrics：`experiments/formal/stage1_temporal_session_anchor_v20_locomo_nonadv_full_4e4a939/metrics.json`
- judge：`experiments/formal/stage1_temporal_session_anchor_v20_locomo_nonadv_full_4e4a939/deepseek_judge.json`
- evidence recall：`experiments/formal/stage1_temporal_session_anchor_v20_locomo_nonadv_full_4e4a939/evidence_recall.json`
- manifest：`experiments/formal/stage1_temporal_session_anchor_v20_locomo_nonadv_full_4e4a939/manifest.json`

## 决策

v20 不作为主线，且配置不长期保留在 `configs/`。当前统一主线仍是 v18 hybrid BM25。v20 的教训是：raw session anchors 虽然比 v19 的 build-memory guide 更 clean、更可控，但简单插入 anchor turns 仍会扰乱原本有效的 top-40 evidence。
