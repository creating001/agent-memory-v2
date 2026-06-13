# Diagnosis for stage1_temporal_aid_frontload_v22_lme_s_full_2143e43

## 诊断结论

v22 不值得继续放大。它没有改变 retrieval 或 build，只改变 Temporal Aid 的位置和通用 duration mention 抽取；但 LME full 从 v18 的 `0.732` 降到 `0.720`。

## 与 v18 对比

- fixed_vs_v18: `21`
- hurt_vs_v18: `27`
- net_correct_delta: `-6`

fixed by type：

| type | count |
|---|---:|
| knowledge-update | 3 |
| multi-session | 7 |
| single-session-assistant | 3 |
| single-session-preference | 2 |
| single-session-user | 1 |
| temporal-reasoning | 5 |

hurt by type：

| type | count |
|---|---:|
| knowledge-update | 6 |
| multi-session | 8 |
| single-session-assistant | 2 |
| single-session-preference | 1 |
| single-session-user | 3 |
| temporal-reasoning | 7 |

## 失败模式

- evidence recall 仍为 `1.0`，说明退化不是 evidence label 覆盖率下降导致。
- retrieval 结构与 v18 相同，avg compiled evidence items 仍为 `34.058`。
- avg query tokens 从 v18 的 `5117.622` 变为 `5134.496`，仍在 6K 预算内，但没有换来 accuracy 收益。
- Temporal Aid 前置 198/198 成功，duration mentions 出现在 145 个 prompt 中，说明实现生效。
- temporal-reasoning 从 v18 的 `99/133` 降到 `97/133`，multi-session 从 `74/133` 降到 `73/133`，knowledge-update 从 `64/78` 降到 `61/78`。

推断：Temporal Aid 和 duration mentions 作为辅助索引本身是 clean/general 的，但放在 context 前会改变模型注意力分配；对需要完整事件链、更新链和精确实体的题，额外候选时长可能造成过早计算或错误聚焦。该类 regex temporal aid 不应继续加复杂度。

## Clean 检查

- prediction loader 未读取 gold/reference/target、judge output、benchmark label、sample id、qid 或 row index。
- duration mention 提取只读取 raw row text 和 row timestamp，属于通用文本时间归一化。
- DeepSeek judge 和 evidence recall 均在预测完成后离线运行，输出不得被 route、retrieval、compiler、answer 或 verifier 读取。
- manifest 记录 commit `2143e43aa0e3cc3b9fe2fbca8a6a544eb03899c5`，prediction dirty 为 `false`。

## 后续建议

- 不继续运行 LoCoMo full，避免在 LME 明确负向的 temporal aid 上浪费成本。
- v18 仍是当前 unified best。
- 下一步应分析 v18/v14 互补样本，优先探索 source-preserving evidence selection、typed memory conflict/update chains、profile/event 分层检索，而不是继续增加 prompt 里的计算提示。
