# Diagnosis: stage1_evidence_report_contract_v28_locomo_nonadv_full_ee13e22

## 结果判断

v28 在 LoCoMo non-adversarial full 上没有形成有效突破。

- v28: 0.7376623377，1136 / 1540
- v18: 0.7370129870，1135 / 1540
- v26: 0.7298701299，1124 / 1540
- target: 0.78

相对 v18，v28 只有 +1 个正确样本；相对 v26，v28 +12 个正确样本。该结果说明 `evidence_report_contract` 对 LoCoMo 的收益有限，不能作为下一阶段的主线完成目标。

## 分类表现

v28 by category:

- category 1: 0.6489361702
- category 2: 0.6199376947
- category 3: 0.5833333333
- category 4: 0.8299643282

v28 by information_need:

- current_state: 0.75
- fact_lookup: 0.7838899804
- list_count: 0.5877862595
- profile_preference: 0.7959183673
- temporal_lookup: 0.6479289941

主要变化：

- 相比 v18，temporal_lookup 从 0.6272189349 到 0.6479289941，有明显但不够大的提升。
- profile_preference 从 0.7551020408 到 0.7959183673，有小幅提升。
- fact_lookup 从 0.7907662083 降到 0.7838899804，抵消了 temporal/profile 收益。
- category 3 从 0.625 降到 0.5833333333，是明显退化点。
- category 4 与 v18 完全持平，说明证据报告没有改善大量基础事实问题。

## 与 v18 的差异

v18 vs v28:

- both_correct: 1044
- both_wrong: 313
- v18_only: 91
- v28_only: 92
- same normalized answer: 569
- same normalized answer but judge differs: 8

差异几乎完全对冲。v28 新答对了一些时间题和偏好题，但也错掉了 v18 能答对的直接事实、开放列表和反事实/隐含推理题。

典型收益：

- `When did Melanie go to the museum?`: v18 输出 2023-07-06，v28 输出 2023-07-05，v28 正确。
- `When did Melanie make a plate in pottery class?`: v18 输出 2023-08-25，v28 输出 2023-08-24，v28 正确。
- `What pets does Melanie have?`: v18 漏掉一只猫，v28 输出 dog Luna + cats Oliver and Bailey，v28 正确。

典型退化：

- `When did Caroline meet up with her friends, family, and mentors?`: v18 能输出 week before 9 June，v28 回到会话日期 2023-06-09。
- `What activities does Melanie partake in?`: v28 过度收窄，漏掉 painting，v18 更接近 judge 口径。
- `Would Caroline still want to pursue counseling...`: v28 过度保守答 unknown，v18 给出合理推断。

## Evidence recall 诊断

- overall evidence_recall: 0.8893229167
- category 1: 0.8936170213
- category 2: 0.8909657321
- category 3: 0.6739130435
- category 4: 0.9108204518

category 3 的 source/evidence recall 明显低，说明这类问题不是只靠 answer prompt 能修好，需要改 retrieval / context organization / memory view。category 1/2/4 recall 较高但 accuracy 仍有大量错误，说明已有证据进入上下文后，answer 侧还存在时间解释、列表边界、隐含推理和证据筛选问题。

## Token 与成本

- avg_build_tokens: 58386.0078，低于 LoCoMo 100K build 预算
- avg_query_tokens: 3864.5370，低于 LoCoMo 6K query 预算
- answer max_input_tokens: 131072
- answer max_output_tokens: 16384
- answer cache hits/misses/writes: 1539 / 1 / 1
- build cache hits/misses/writes: 12411 / 0 / 0

正式报告中的 build token 是该方法冷启动构建 memory 的逻辑成本；cache 命中只表示本次复现实验没有重复调用 build LLM，不表示方法不消耗 build token。

## Clean 检查

- Prediction input 只包含 `question`、`sessions`，LongMemEval 另有 `question_time`；LoCoMo 的 `evidence` 字段只在 labels 文件里。
- `gold_answer`、`question_type`、`category`、`source_sample_id`、`evidence` 均没有进入 prediction pipeline。
- DeepSeek judge 和 evidence recall 均为 prediction 完成后的离线诊断。
- 本次改动没有引入样本级规则、benchmark 专门规则或 judge feedback。

## 下一步

下一阶段不应继续只堆 answer prompt。更值得投入的方向：

1. 设计 source-aware episode / turn-pair context 组织，让检索命中的事实带上必要前后文，但控制 query token 不超 6K。
2. 针对 LoCoMo category 3 的低 evidence recall，分析 badcase 中缺失证据的 source 分布，判断是 lexical/dense 检索漏召回，还是 build memory 压缩丢失隐含条件。
3. 保留 v28 对 temporal/profile 的正收益，但降低 evidence report 的过度保守倾向，尤其是反事实、would/if 问题不能简单输出 unknown。
4. 继续参考外部实现，重点看 high-performing query 侧如何组织 raw episode、邻近 turn、时间线和候选证据，而不是迁移任何 sample-level 或 benchmark-specific 逻辑。
