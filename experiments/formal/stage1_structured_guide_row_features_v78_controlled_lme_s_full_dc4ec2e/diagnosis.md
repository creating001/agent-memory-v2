# Diagnosis for stage1_structured_guide_row_features_v78_controlled_lme_s_full_dc4ec2e

## 判断

v78 row feature guide 没有解决 v73 的 reader/aggregation 问题。controlled run 将未变 prompt 的答案固定到 v73 cache 后，结果仍从 `389/500` 降到 `379/500`。因此负向不是单纯 cache miss 或 Qwen 全量重采样造成。

## 对比 v73

- both_correct: `367`
- both_wrong: `99`
- gained: `12`
- lost: `22`
- same-answer judge variance: gain/loss `3` / `8`
- changed-answer method surface: gain/loss `9` / `14`

## By Information Need

| group | C->C | C->W | W->C | W->W |
|---|---:|---:|---:|---:|
| current_state | 12 | 1 | 0 | 9 |
| fact_lookup | 148 | 2 | 2 | 31 |
| list_count | 89 | 7 | 2 | 21 |
| profile_preference | 8 | 2 | 0 | 5 |
| temporal_lookup | 110 | 10 | 8 | 33 |

## Changed-Answer Surface

| group | C->C | C->W | W->C | W->W |
|---|---:|---:|---:|---:|
| list_count | 7 | 5 | 1 | 4 |
| temporal_lookup | 19 | 9 | 8 | 13 |

## 失败原因

1. row feature guide 对真正改变答案的 66 条样本是净负：`9` gain / `14` loss。它有时帮助 temporal/count 看到数量或时间短语，但更常见的是提高了无关数字、相邻时间短语或候选行的显著性。
2. `list_count` changed subset 只有 `1` gain / `5` loss，说明“把数量显示出来”不足以解决 distinct item / duplicate / scope 管理，反而会让 Qwen 更容易受局部数字牵引。
3. `temporal_lookup` changed subset `8` gain / `9` loss，接近中性但仍负。时间短特征对部分 relative-time 问题有帮助，但不能稳定解决 endpoint/event-role 选择。
4. evidence recall 仍为 `1.0`，瓶颈不是目标 session 是否召回，而是 answer 阶段如何在 raw rows 里管理候选集合、去重和端点角色。

## 取舍

保留结论：候选组织方向仍重要，但不能用浅层 row feature salience 解决。下一步如果继续做 candidate organization，应显式形成 source-preserving candidate set / endpoint chain，并在 compiler 中弱提示，而不是只追加 row-level quantities/time phrases。

舍弃内容：v78 顶层 config 和源码开关不应保留在主线。正式追溯依赖本目录 config snapshot 和 git commit。

## Clean 复核

- Prediction input 不包含 gold answer、judge output、benchmark label、question_type、category、sample id、qid 或 row index。
- row features 只来自 question-derived route、raw retrieved row text、visible row timestamp。
- cache seed 只读取 v73 prediction traces；prompt-keyed cache 不会让旧答案命中已变更 prompt。
- DeepSeek judge、labels、question_type 只在 prediction 完成后用于离线评估和诊断。
